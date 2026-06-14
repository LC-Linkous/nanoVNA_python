#! /usr/bin/python3
"""
diagnose_fastcmd.py -- reproduce the buffer race with FAST commands.

WHY THIS, NOT diagnose_continuous.py
------------------------------------
diagnose_continuous.py showed scan() reads 100% clean even at gap=0 -- because a
101-point scan takes ~1.4s (real sweep time), so the device fully finishes each
reply (including the doubled 'ch> \\r\\nch> ' tail) long before the next command
arrives. There is no race when the command is slow.

The failures we actually saw -- the intermittent empty 'help' under pytest, the
probe session emptying out -- were FAST commands fired back to back: version,
sweep, data, recall, cal, port. Those return in milliseconds, so command N+1 can
arrive while the device is STILL emitting N's doubled-prompt tail. THAT is when
the shipped get_serial_return (which stops on the FIRST 'ch>') leaves bytes in
the buffer, and the next nanoVNA_serial's reset_input_buffer() races/eats them.

This diagnostic hammers fast, instant-returning commands in a tight loop and
classifies every reply, comparing the same variants as before. This is the
workload that should actually separate them.

VARIANTS (identical to diagnose_continuous.py)
  baseline : shipped code (break on first 'ch>', pre-write input flush)
  A_double : get_serial_return reads until it has seen the prompt TWICE
  B_noflush: nanoVNA_serial without the pre-write reset_input_buffer()
  C_drain  : no pre-write flush; short POST-read drain instead
  A+C      : A_double + C_drain together

WHAT EACH READ EXPECTS
  We use commands whose cleaned reply has a known, checkable shape:
    version    -> a non-empty single token (e.g. '0.3.0')
    SN         -> a non-empty token
    sweep      -> 3 integers: 'start stop points'
    resolution -> 'W,H'
    data 0     -> many 're im' pair lines (S11)
  A reply is 'bad' if it's empty OR doesn't match the expected shape (which is
  what a raced/truncated read looks like). 'good' otherwise.

SAFETY: read-only. All commands here are queries; none write device state,
none save/clear/reset. 'recall 0' is included as an OPTIONAL stressor (loads the
startup preset; non-destructive) and is OFF by default -- enable with --hard.

USAGE
-----
    python diagnose_fastcmd.py                 # autoconnect, gap=0 (max stress)
    python diagnose_fastcmd.py --port COM5
    python diagnose_fastcmd.py --reps 200      # more iterations to catch rare races
    python diagnose_fastcmd.py --gap 0.01      # add a small delay
    python diagnose_fastcmd.py --hard          # include recall 0 in the rotation

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
# Variant implementations (same as diagnose_continuous.py)
# ---------------------------------------------------------------------------

def _gsr_baseline(self):
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
    prompt = b'ch>'
    buffer = bytes()
    deadline = time.time() + self.serialTimeout
    while True:
        waiting = self.ser.in_waiting
        if waiting > 0:
            buffer += self.ser.read(waiting)
            if buffer.count(prompt) >= 2:
                time.sleep(self.serialPollInterval)
                if self.ser.in_waiting:
                    buffer += self.ser.read(self.ser.in_waiting)
                break
            deadline = time.time() + self.serialTimeout
        else:
            if time.time() > deadline:
                self.print_message("WARNING: serial read timed out waiting for prompt")
                break
            time.sleep(self.serialPollInterval)
    return bytearray(buffer)


def _serial_noflush(self, writebyte, printBool=False, pts=None):
    self.ser.reset_output_buffer()
    self.ser.write(bytes(writebyte, 'utf-8'))
    msgbytes = self.get_serial_return()
    msgbytes = self.clean_return(msgbytes)
    if printBool:
        print(msgbytes)
    return msgbytes


def _serial_postdrain(self, writebyte, printBool=False, pts=None):
    self.ser.reset_output_buffer()
    self.ser.write(bytes(writebyte, 'utf-8'))
    msgbytes = self.get_serial_return()
    msgbytes = self.clean_return(msgbytes)
    try:
        time.sleep(self.serialPollInterval)
        if self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
    except Exception:
        pass
    if printBool:
        print(msgbytes)
    return msgbytes


VARIANTS = [
    ("baseline",  None,        None),
    ("A_double",  _gsr_double, None),
    ("B_noflush", None,        _serial_noflush),
    ("C_drain",   None,        _serial_postdrain),
    ("A+C",       _gsr_double, _serial_postdrain),
]


# ---------------------------------------------------------------------------
# Per-command expected-shape validators. Each returns True if the CLEANED reply
# looks like a correct response to that command, False if empty/raced/wrong.
# ---------------------------------------------------------------------------

def _txt(raw):
    return bytes(raw).decode("utf-8", errors="replace").strip()


def _ok_version(raw):
    t = _txt(raw)
    return len(t) > 0 and "ch>" not in t and "\n" not in t  # single non-empty line


def _ok_sn(raw):
    t = _txt(raw)
    return len(t) > 0 and "ch>" not in t


def _ok_sweep(raw):
    # 'start stop points' -> 3 integers
    parts = _txt(raw).split()
    if len(parts) != 3:
        return False
    try:
        int(parts[0]); int(parts[1]); int(parts[2])
        return True
    except ValueError:
        return False


def _ok_resolution(raw):
    # 'W,H'
    t = _txt(raw)
    if "," not in t:
        return False
    a, _, b = t.partition(",")
    try:
        int(a); int(b.strip())
        return True
    except ValueError:
        return False


def _ok_data0(raw):
    # many 're im' pair lines
    lines = [ln for ln in _txt(raw).split("\n") if ln.strip()]
    if not lines:
        return False
    good = 0
    for ln in lines:
        p = ln.split()
        if len(p) >= 2:
            try:
                float(p[0]); float(p[1]); good += 1
            except ValueError:
                pass
    return good >= 2   # data 0 returns the full S11 table; >=2 pairs = real data


# (label, command_string, validator). Fast, instant-returning queries.
FAST_COMMANDS = [
    ("version",    "version",    _ok_version),
    ("sweep",      "sweep",      _ok_sweep),
    ("resolution", "resolution", _ok_resolution),
    ("SN",         "SN",         _ok_sn),
    ("data0",      "data 0",     _ok_data0),
]

# optional extra stressor rotation (still read-only); recall 0 = startup preset
HARD_EXTRA = [
    ("recall0",    "recall 0",   lambda raw: True),   # accept any reply; it's a stressor
]


def _bind(dev, gsr_impl, serial_impl):
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


def _run_fast_loop(dev, rotation, reps, gap):
    """Fire the rotation of fast commands `reps` times. Returns (good, bad,
    per-command bad counts, timings)."""
    good = 0
    bad = 0
    per_cmd_bad = {label: 0 for label, _, _ in rotation}
    timings = []
    for _ in range(reps):
        for label, cmd, validator in rotation:
            t0 = time.time()
            raw = dev.command(cmd)
            timings.append(time.time() - t0)
            if validator(raw):
                good += 1
            else:
                bad += 1
                per_cmd_bad[label] += 1
            if gap:
                time.sleep(gap)
    return good, bad, per_cmd_bad, timings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None)
    ap.add_argument("--reps", type=int, default=100,
                    help="how many times to run the full fast-command rotation")
    ap.add_argument("--gap", type=float, default=0.0,
                    help="delay between commands (0 = max stress)")
    ap.add_argument("--hard", action="store_true",
                    help="add 'recall 0' to the rotation as an extra stressor")
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

    rotation = list(FAST_COMMANDS) + (HARD_EXTRA if args.hard else [])
    cmds_per_rep = len(rotation)
    total_per_variant = args.reps * cmds_per_rep

    print("Connected.")
    print(f"model={dev.get_device_model()}  reps={args.reps}  "
          f"commands/rep={cmds_per_rep}  gap={args.gap}s  hard={args.hard}")
    print(f"serialTimeout={dev.get_serial_timeout()}s  "
          f"pollInterval={dev.get_serial_poll_interval()}s")
    print(f"each variant issues {total_per_variant} fast commands\n")

    # pause the live sweep so the UI sweep isn't contending on the wire
    try:
        dev.pause()
    except Exception:
        pass

    results = []
    for label, gsr_impl, serial_impl in VARIANTS:
        restore = _bind(dev, gsr_impl, serial_impl)
        try:
            time.sleep(0.4)
            try:
                dev.ser.reset_input_buffer()
            except Exception:
                pass
            good, bad, per_cmd_bad, timings = _run_fast_loop(
                dev, rotation, args.reps, args.gap)
        finally:
            restore()
        results.append((label, good, bad, per_cmd_bad, timings))

        med = statistics.median(timings) if timings else 0.0
        worst = max(per_cmd_bad, key=per_cmd_bad.get) if per_cmd_bad else "-"
        worst_n = per_cmd_bad.get(worst, 0)
        print(f"  [{label:9s}] good={good:4d} bad={bad:4d}  "
              f"(worst: {worst}={worst_n})  t med={med:.3f}s max={max(timings):.3f}s")

    try:
        dev.resume()
    except Exception:
        pass
    dev.disconnect()

    print("\n== SUMMARY ==")
    print(f"  total fast commands per variant: {total_per_variant}")
    print(f"  {'variant':10s}  {'good':>5s} {'bad':>5s}   per-command bad breakdown")
    for label, good, bad, per_cmd_bad, timings in results:
        brk = " ".join(f"{k}={v}" for k, v in per_cmd_bad.items() if v)
        print(f"  {label:10s}  {good:5d} {bad:5d}   {brk if brk else '(none)'}")
    print()
    print("  If baseline shows bad>0 and A_double / A+C show bad==0, the doubled-")
    print("  prompt early-break is the cause and consuming both prompts is the fix.")
    print("  If B_noflush is clean here but you suspect single reads, remember the")
    print("  flush exists to clear stale bytes -- prefer A_double/A+C over removing it.")
    print("  If EVERY variant is bad==0 even at gap=0, the fast-command race isn't")
    print("  reproducing on this firmware/host; the help/probe failures were then")
    print("  ordering/contention specific, not a get_serial_return defect.")
    print("\nDone.")


if __name__ == "__main__":
    main()