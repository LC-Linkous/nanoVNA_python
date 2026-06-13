#! /usr/bin/python3
"""
diagnose_help.py -- pin down WHY device.command("help") sometimes returns empty.

Runs against a connected NanoVNA. For the 'help' command (the largest text
reply the device produces, ~1414 bytes) it captures, at each stage:

  1. the RAW bytes get_serial_return() collected, BEFORE clean_return
  2. what clean_return() then produces
  3. the timing of the read loop (did it hit the wall-clock timeout?)

and repeats the whole thing N times, because the failure is suspected to be an
intermittent USB-CDC timing race on the largest reply. A few small/fast replies
(version, sweep) are captured alongside as a control: if those are always fine
and only 'help' is flaky, that confirms it's size/timing, not a broken command.

This is a DIAGNOSTIC, not a test. It is read-only: 'help', 'version', and
'sweep' (no-arg) do not change device state or write storage.

USAGE
-----
    python diagnose_help.py                  # auto-detect port, 5 help reads
    python diagnose_help.py --port COM5      # explicit port
    python diagnose_help.py --reps 10        # more repetitions to catch flakiness
    python diagnose_help.py --raw-timeout 5  # widen the read timeout for the probe

WHAT TO SEND BACK
-----------------
The whole printed block. The decisive lines are, for each 'help' rep:
    raw_len=...  timed_out=...  cleaned_len=...
plus the raw_repr_head / raw_repr_tail on any rep where cleaned_len == 0.
That tells us whether the bytes never arrived (read-loop fix) or arrived and
were eaten by clean_return (cleaner fix).
"""

import sys
import os
import time
import argparse

# make src/ importable when run from the project root or tests/
HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (
    os.path.join(HERE, "src"),
    os.path.join(HERE, "..", "src"),
    os.path.join(HERE, ".."),
    HERE,
):
    if os.path.isdir(os.path.join(cand, "nvnapython")):
        sys.path.insert(0, cand)
        break

from nvnapython import nanoVNA  # noqa: E402


def _send_and_capture(dev, cmd, raw_timeout=None):
    """Mirror nanoVNA_serial's write path, but capture the RAW read separately
    from the cleaned result so we can see which stage drops the payload.

    Returns a dict with raw bytes, cleaned bytes, elapsed time, and whether the
    read loop appears to have hit its timeout.
    """
    # optionally widen the read timeout just for this probe, then restore
    saved_timeout = dev.get_serial_timeout()
    if raw_timeout is not None:
        dev.set_serial_timeout(float(raw_timeout))

    try:
        dev.ser.reset_input_buffer()
        dev.ser.reset_output_buffer()
        dev.ser.write(bytes(cmd + "\r\n", "utf-8"))

        t0 = time.time()
        raw = dev.get_serial_return()          # BEFORE clean_return
        elapsed = time.time() - t0

        cleaned = dev.clean_return(bytearray(raw))
    finally:
        dev.set_serial_timeout(saved_timeout)

    # Heuristic: if we spent ~>= the timeout AND the buffer doesn't end in the
    # prompt, the loop almost certainly bailed on the wall-clock deadline.
    rstripped = bytes(raw).rstrip()
    ends_with_prompt = rstripped.endswith(b"ch>")
    timed_out = (elapsed >= dev.get_serial_timeout() * 0.95) and not ends_with_prompt

    return {
        "cmd": cmd,
        "raw": bytes(raw),
        "cleaned": bytes(cleaned),
        "elapsed": elapsed,
        "ends_with_prompt": ends_with_prompt,
        "timed_out": timed_out,
    }


def _report(rec, show_full_raw=False):
    raw = rec["raw"]
    cleaned = rec["cleaned"]
    print(f"    raw_len={len(raw)}  cleaned_len={len(cleaned)}  "
          f"elapsed={rec['elapsed']:.3f}s  "
          f"ends_with_prompt={rec['ends_with_prompt']}  "
          f"timed_out={rec['timed_out']}")
    # Always show head+tail so we can see framing; show full raw only on request
    # or when something looks wrong (empty cleaned, or no prompt at the end).
    suspicious = (len(cleaned) == 0) or (not rec["ends_with_prompt"])
    if show_full_raw or suspicious:
        head = raw[:120]
        tail = raw[-120:]
        print(f"      raw_repr_head={head!r}")
        print(f"      raw_repr_tail={tail!r}")
        # how many times does the prompt token appear in the raw buffer?
        print(f"      raw.count(b'ch>')={raw.count(b'ch>')}  "
              f"raw.count(b'\\r\\n')={raw.count(chr(13).encode()+chr(10).encode())}")
        if len(cleaned) == 0:
            print("      >>> cleaned is EMPTY: payload was dropped. If raw_len is "
                  "large, clean_return ate it; if raw_len is tiny, the read loop "
                  "bailed before the payload arrived.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None,
                    help="serial port (e.g. COM5 or /dev/ttyACM0). "
                         "Omitted = autoconnect.")
    ap.add_argument("--reps", type=int, default=5,
                    help="how many times to read 'help' (catch intermittency)")
    ap.add_argument("--raw-timeout", type=float, default=None,
                    help="override serial read timeout (s) during the probe; "
                         "widen this to test the timing hypothesis")
    args = ap.parse_args()

    dev = nanoVNA()
    dev.set_verbose(False)
    dev.set_error_byte_return(True)

    if args.port:
        ok = dev.connect(args.port)
    else:
        _found, ok = dev.autoconnect()
    if not ok:
        print("ERROR: could not open the serial port. Pass --port explicitly, "
              "or check permissions (Linux: sudo chmod a+rw /dev/ttyACM0).")
        sys.exit(1)

    print("Connected.")
    print(f"serial timeout    = {dev.get_serial_timeout()}s")
    print(f"poll interval     = {dev.get_serial_poll_interval()}s")
    if args.raw_timeout is not None:
        print(f"probe read timeout= {args.raw_timeout}s (override)")
    print()

    # --- control replies: small/fast, should always be clean ---------------
    print("== CONTROL (small replies; expect these always clean) ==")
    for cmd in ("version", "sweep"):
        rec = _send_and_capture(dev, cmd, raw_timeout=args.raw_timeout)
        print(f"  [{cmd}]")
        _report(rec, show_full_raw=True)
    print()

    # --- the suspect: 'help', repeated -------------------------------------
    print(f"== HELP (largest reply; reading {args.reps}x to catch flakiness) ==")
    empties = 0
    for i in range(1, args.reps + 1):
        rec = _send_and_capture(dev, "help", raw_timeout=args.raw_timeout)
        print(f"  [help #{i}]")
        _report(rec)
        if len(rec["cleaned"]) == 0:
            empties += 1
        time.sleep(0.1)   # small gap between reps
    print()

    # --- verdict -----------------------------------------------------------
    print("== SUMMARY ==")
    print(f"  help reads: {args.reps}, empty cleaned results: {empties}")
    if empties == 0:
        print("  -> 'help' was clean on every read here. If it fails under the "
              "full pytest run, the difference is timing/contention (e.g. a "
              "prior test left bytes in the buffer, or back-to-back commands "
              "with no settle). Try widening serialTimeout or adding a small "
              "settle before large reads.")
    elif empties == args.reps:
        print("  -> 'help' was empty EVERY time. Not a race: a consistent "
              "read-loop or clean_return issue on the large reply. The raw_len "
              "on the reps above says which stage.")
    else:
        print("  -> 'help' was INTERMITTENT (some empty, some not). This is the "
              "USB-CDC timing race on the largest reply: get_serial_return's "
              "prompt check can trip on an early chunk before the whole 1414-byte "
              "dump lands. The raw_len/timed_out columns on the empty reps "
              "confirm which.")

    dev.disconnect()
    print("\nDone")


if __name__ == "__main__":
    main()