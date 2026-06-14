#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/robust_acquisition_loop.py'
#   A repeated-scan loop that validates each reply and RETRIES an empty/malformed
#   read, then SKIPS one that keeps failing -- instead of crashing on the first bad
#   read. Copy this pattern for any long-running collection (logging, monitoring).
#       python examples/robust_acquisition_loop.py
#       python examples/robust_acquisition_loop.py --iterations 50 --retries 2
#
#   pause() once up front, resume() once at the end; clean teardown via finally.
#   Requires only the library (a tiny stdlib parser, no numpy).
#
##-------------------------------------------------------------------------------\

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def parse_s11_pairs(data, expected):
    """Return a list of (real, imag) tuples, or None if the reply doesn't look
    like a valid scan of `expected` points. This is the validation gate: a
    raced/truncated/empty read fails it and the caller retries."""
    if not data:
        return None
    text = bytes(data).decode("utf-8", errors="replace")
    if text.strip() in ("", "ERROR"):
        return None
    pairs = []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        vals = line.split()
        if len(vals) < 2:
            continue
        try:
            pairs.append((float(vals[0]), float(vals[1])))
        except ValueError:
            continue
    # a correct scan yields exactly `expected` pairs; anything else is suspect
    if len(pairs) != expected:
        return None
    return pairs


def acquire_one(nvna, start, stop, pts, retries):
    """Do a single validated scan with up to `retries` retries. Returns the
    list of pairs, or None if every attempt failed."""
    for attempt in range(retries + 1):
        raw = nvna.get_scan_s11(start, stop, pts)   # outmask 2
        pairs = parse_s11_pairs(raw, pts)
        if pairs is not None:
            return pairs
        # brief settle before retrying; a bad read is usually transient
        time.sleep(0.1)
    return None


def main():
    ap = argparse.ArgumentParser(description="Robust repeated S11 acquisition loop.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=2e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=101, help="points (<=201 on F V2)")
    ap.add_argument("--iterations", type=int, default=20, help="how many scans to attempt")
    ap.add_argument("--retries", type=int, default=2, help="retries per scan before skipping")
    ap.add_argument("--interval", type=float, default=0.0,
                    help="delay between scans in seconds (0 = as fast as possible)")
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(False)             # quiet -- we print our own per-scan status
    nvna.set_error_byte_return(True)

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    start, stop, pts = int(args.start), int(args.stop), args.points
    got = 0
    skipped = 0

    try:
        # pause ONCE up front; resume ONCE at the end (in finally).
        nvna.pause()
        print(f"acquiring {args.iterations} scans of {pts} points "
              f"({start/1e9:.3f}-{stop/1e9:.3f} GHz)...")

        for i in range(1, args.iterations + 1):
            pairs = acquire_one(nvna, start, stop, pts, args.retries)
            if pairs is None:
                skipped += 1
                print(f"  [{i:3d}] SKIPPED after {args.retries + 1} attempts "
                      f"(empty/malformed reply)")
            else:
                got += 1
                # trivial example processing: peak |S11| sample
                # (kept dependency-free; real code would vectorize with numpy)
                mags = [(r * r + im * im) ** 0.5 for r, im in pairs]
                peak = max(mags)
                print(f"  [{i:3d}] ok  {len(pairs)} pts  peak|S11|={peak:.4f}")
            if args.interval:
                time.sleep(args.interval)

    finally:
        # resume the sweep and release the port no matter what happened
        try:
            nvna.resume()
        finally:
            nvna.disconnect()

    total = got + skipped
    print(f"\ndone: {got}/{total} scans usable, {skipped} skipped.")
    if skipped:
        print("  Skips are handled gracefully (retried then skipped) rather than "
              "crashing the loop -- copy this validate/retry/skip pattern for any "
              "long-running collection.")
    return 0 if got else 1


if __name__ == "__main__":
    raise SystemExit(main())
