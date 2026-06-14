#! /usr/bin/python3
"""
diagnose_continuous.py -- find the right fix for the continuous-read failure.

BACKGROUND
----------
Back-to-back commands (the realtime-waterfall loop, rapid scan() calls) sometimes
come back truncated or empty. The README's realtime example already worked around
this with a hand-tuned `time.sleep(0.15)  # prevent overwhelming the device`. The
same root cause produced the intermittent empty 'help' dump under pytest.

Suspected mechanism (confirmed against the hardware captures in readme_capture.md):
  * the REAL device prompt tail is doubled with trailing spaces: 'ch> \\r\\nch> '
  * get_serial_return() stops on the FIRST 'ch>', so it returns BEFORE the second
    prompt (and its trailing bytes) have been read -- those bytes stay in the OS
    input buffer
  * nanoVNA_serial() does reset_input_buffer() right before the NEXT write; when
    commands come fast, that flush discards bytes that are still part of the
    PREVIOUS reply's tail OR the next reply's echo, so the next read sees a
    truncated frame or no prompt at all (-> full-timeout empty return)

WHAT THIS DOES
--------------
Runs a tight loop of scan()-style reads FOUR ways on the SAME connected device,
WITHOUT editing core.py (each variant is monkeypatched on for its run, then
restored). For each variant it reports how many reads came back:
    clean      -- parses to the expected pair count
    truncated  -- got SOME data but the wrong line count
    empty      -- got nothing (the buffer race / timeout)
plus min/median/max per-read time.

VARIANTS
  baseline : current get_serial_return + current nanoVNA_serial (the shipped code)
  A_double : get_serial_return reads until it has seen the prompt TWICE (consume
             the whole doubled tail) -- nothing left in the buffer
  B_noflush: nanoVNA_serial does NOT reset_input_buffer() before writing
  C_drain  : nanoVNA_serial does a short POST-read drain instead of a pre-write
             flush (read reply, then sip any immediate trailing bytes)

It also runs a SINGLE-SHOT control for each variant (one scan with a gap before
it) to make sure a variant that helps continuous reads doesn't BREAK the simple
case (e.g. B_noflush could let stale bytes leak into a lone read).

SAFETY: read-only. scan() with an outmask does not write device state. The loop
pauses the sweep first and resumes after. No save/clearconfig/reset.

USAGE
-----
    python diagnose_continuous.py                      # autoconnect, defaults
    python diagnose_continuous.py --port COM5
    python diagnose_continuous.py --pts 101 --reps 30  # more points / more reads
    python diagnose_continuous.py --gap 0.0            # zero inter-read delay (stress)
    python diagnose_continuous.py --gap 0.15           # the README's worked-around delay

"""

import sys
import os
import time
import types
import argparse
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "src"), os.path.join(HERE, "..", "src"),
             os.path.join(HERE, ".."), HERE):
    if os.path.isdir(os.path.join(cand, "nvnapython")):
        sys.path.insert(0, cand)
        break

from nvnapython import nanoVNA  # noqa: E402


# ---------------------------------------------------------------------------
# Candidate get_serial_return / nanoVNA_serial implementations.
#
# Each takes `self` (a nanoVNA) so we can bind it as a method via types.MethodType.
# They mirror the real signatures exactly.
# ---------------------------------------------------------------------------

def _gsr_baseline(self):
    """Verbatim copy of the shipped get_serial_return (break on FIRST prompt)."""
    prompt = b'ch>'
    buffer = bytes()
    deadline = time.time() + self.serialTimeout
    while True:
        waiting = self.ser.in_waiting
        if waiting > 0:
            buffer += self.ser.read(waiting)
            if buffer.rstrip().endswith(prompt):
                break
            deadline = time.time() + self.serialTimeout
        else:
            if time.time() > deadline:
                self.print_message("WARNING: serial read timed out waiting for prompt")
                break
            time.sleep(self.serialPollInterval)
    return bytearray(buffer)


def _gsr_double(self):
    """Variant A: read until the prompt has been seen TWICE, so the whole
    doubled 'ch> \\r\\nch> ' tail is consumed and nothing is left in the buffer.
    Falls back to a single-prompt + short settle if a model emits only one."""
    prompt = b'ch>'
    buffer = bytes()
    deadline = time.time() + self.serialTimeout
    while True:
        waiting = self.ser.in_waiting
        if waiting > 0:
            buffer += self.ser.read(waiting)
            if buffer.count(prompt) >= 2:
                # seen both prompts; give the trailing space/newline a beat to land
                time.sleep(self.serialPollInterval)
                if self.ser.in_waiting:
                    buffer += self.ser.read(self.ser.in_waiting)
                break
            deadline = time.time() + self.serialTimeout
        else:
            if time.time() > deadline:
                # timed out waiting for the second prompt: accept a single one
                if buffer.rstrip().endswith(prompt):
                    pass
                else:
                    self.print_message("WARNING: serial read timed out waiting for prompt")
                break
            time.sleep(self.serialPollInterval)
    return bytearray(buffer)


def _serial_noflush(self, writebyte, printBool=False, pts=None):
    """Variant B: nanoVNA_serial WITHOUT the pre-write reset_input_buffer().
    (Still clears the output buffer.) Tests whether the pre-write input flush is
    the thing eating in-flight bytes."""
    self.ser.reset_output_buffer()
    self.ser.write(bytes(writebyte, 'utf-8'))
    msgbytes = self.get_serial_return()
    msgbytes = self.clean_return(msgbytes)
    if printBool:
        print(msgbytes)
    return msgbytes


def _serial_postdrain(self, writebyte, printBool=False, pts=None):
    """Variant C: no pre-write input flush; instead, after the read, sip any
    immediately-trailing bytes so the buffer is clean for next time. Keeps the
    output-buffer reset."""
    self.ser.reset_output_buffer()
    self.ser.write(bytes(writebyte, 'utf-8'))
    msgbytes = self.get_serial_return()
    msgbytes = self.clean_return(msgbytes)
    # post-read drain: consume any residual tail bytes (e.g. the second prompt's
    # trailing space/newline) so they can't leak into the next read.
    try:
        time.sleep(self.serialPollInterval)
        if self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
    except Exception:
        pass
    if printBool:
        print(msgbytes)
    return msgbytes


# ---------------------------------------------------------------------------
# Variant wiring: (label, get_serial_return_impl_or_None, serial_impl_or_None)
# None means "keep the shipped method".
# ---------------------------------------------------------------------------

VARIANTS = [
    ("baseline",  None,        None),
    ("A_double",  _gsr_double, None),
    ("B_noflush", None,        _serial_noflush),
    ("C_drain",   None,        _serial_postdrain),
    # A+C combined is often the real answer (consume doubled prompt AND drain),
    # so test it too:
    ("A+C",       _gsr_double, _serial_postdrain),
]


def _expected_pairs(start, stop, pts):
    # scan outmask 2 returns one S11 "re im" pair per sweep point.
    return pts


def _classify(raw, expected):
    """Return 'clean' | 'truncated' | 'empty' for a scan outmask-2 reply."""
    if not raw:
        return "empty"
    text = bytes(raw).decode("utf-8", errors="replace")
    lines = [ln for ln in text.split("\n") if ln.strip()]
    # each line should be a re/im pair
    pair_lines = 0
    for ln in lines:
        parts = ln.split()
        if len(parts) >= 2:
            try:
                float(parts[0]); float(parts[1])
                pair_lines += 1
            except ValueError:
                pass
    if pair_lines == expected:
        return "clean"
    if pair_lines == 0:
        return "empty"
    return "truncated"


def _bind(dev, gsr_impl, serial_impl):
    """Apply a variant's method overrides; return a restore() callable."""
    orig_gsr = dev.get_serial_return
    orig_serial = dev.nanoVNA_serial
    if gsr_impl is not None:
        dev.get_serial_return = types.MethodType(gsr_impl, dev)
    if serial_impl is not None:
        dev.nanoVNA_serial = types.MethodType(serial_impl, dev)

    def restore():
        dev.get_serial_return = orig_gsr
        dev.nanoVNA_serial = orig_serial
    return restore


def _run_loop(dev, start, stop, pts, reps, gap):
    """Tight continuous loop. Returns (counts dict, timings list)."""
    counts = {"clean": 0, "truncated": 0, "empty": 0}
    timings = []
    expected = _expected_pairs(start, stop, pts)
    for _ in range(reps):
        t0 = time.time()
        raw = dev.get_scan_s11(start, stop, pts)   # scan outmask 2
        timings.append(time.time() - t0)
        counts[_classify(raw, expected)] += 1
        if gap:
            time.sleep(gap)
    return counts, timings


def _single_shot(dev, start, stop, pts):
    """One read after a clear settle -- the simple-case control."""
    time.sleep(0.3)
    try:
        dev.ser.reset_input_buffer()
    except Exception:
        pass
    expected = _expected_pairs(start, stop, pts)
    raw = dev.get_scan_s11(start, stop, pts)
    return _classify(raw, expected)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None)
    ap.add_argument("--pts", type=int, default=101)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--gap", type=float, default=0.0,
                    help="inter-read delay in seconds (0 = max stress)")
    ap.add_argument("--start", type=int, default=1_000_000)
    ap.add_argument("--stop", type=int, default=100_000_000)
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
    print(f"model={dev.get_device_model()}  pts={args.pts}  reps={args.reps}  "
          f"gap={args.gap}s  range={args.start}..{args.stop}")
    print(f"serialTimeout={dev.get_serial_timeout()}s  "
          f"pollInterval={dev.get_serial_poll_interval()}s")
    print("(scan outmask 2 -> expect %d S11 pairs per read)\n" % args.pts)

    # pause the live sweep so our scans aren't fighting the UI sweep
    try:
        dev.pause()
    except Exception:
        pass

    results = []   # (label, loop_counts, timings, single_shot_result)
    for label, gsr_impl, serial_impl in VARIANTS:
        restore = _bind(dev, gsr_impl, serial_impl)
        try:
            # let the port settle between variants so one variant's tail doesn't
            # bias the next variant's first read
            time.sleep(0.4)
            try:
                dev.ser.reset_input_buffer()
            except Exception:
                pass

            counts, timings = _run_loop(dev, args.start, args.stop, args.pts,
                                        args.reps, args.gap)
            single = _single_shot(dev, args.start, args.stop, args.pts)
        finally:
            restore()
        results.append((label, counts, timings, single))

        med = statistics.median(timings) if timings else 0.0
        print(f"  [{label:9s}] loop: clean={counts['clean']:2d} "
              f"truncated={counts['truncated']:2d} empty={counts['empty']:2d}  "
              f"| single_shot={single:9s} "
              f"| t med={med:.3f}s max={max(timings):.3f}s")

    try:
        dev.resume()
    except Exception:
        pass
    dev.disconnect()

    # --- verdict ----------------------------------------------------------
    print("\n== SUMMARY ==")
    print(f"  {'variant':10s}  {'clean':>5s} {'trunc':>5s} {'empty':>5s}  {'single':>9s}")
    for label, counts, timings, single in results:
        print(f"  {label:10s}  {counts['clean']:5d} {counts['truncated']:5d} "
              f"{counts['empty']:5d}  {single:>9s}")
    print()
    print("  Pick the variant where loop clean == reps AND single_shot == 'clean',")
    print("  at the smallest --gap you can. If baseline already does that at this")
    print("  --gap, re-run with --gap 0.0 to expose the race; the fix is whichever")
    print("  variant still reads clean when baseline starts truncating/emptying.")
    print("\n  Watch especially: does B_noflush help the loop but BREAK single_shot")
    print("  (stale bytes leaking)? If so, the pre-write flush is needed for the")
    print("  simple case and the right fix is A_double or A+C, not removing it.")

    print("\nDone.")


if __name__ == "__main__":
    main()