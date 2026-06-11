#! /usr/bin/python3
"""
examples/basic_scan.py

Minimal end-to-end example: connect, identify the device, run a small S11 scan,
parse the real/imag pairs, and disconnect cleanly.

Dependency-free (stdlib + pyserial only). Run with a NanoVNA connected:

    python examples/basic_scan.py
    python examples/basic_scan.py --port COM6        # explicit port
    python examples/basic_scan.py --start 1e6 --stop 2e6 --points 101

The disconnect lives in a finally block so the COM port is always released,
even if the scan raises -- a leaked handle is the usual cause of the next run
skipping with "no device connected" / PermissionError on Windows.
"""

import sys
import os
import argparse

# Make 'src' importable when running straight from the repo without installing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA                       # noqa: E402
from _helpers import convert_s11_data_to_arrays      # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Basic NanoVNA S11 scan example.")
    ap.add_argument("--port", default=None,
                    help="serial port (e.g. COM6 or /dev/ttyACM0). Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start frequency in Hz")
    ap.add_argument("--stop", type=float, default=2e9, help="stop frequency in Hz")
    ap.add_argument("--points", type=int, default=101, help="sweep points (11..201 on F V2)")
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(True)
    nvna.set_error_byte_return(True)

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    try:
        print("info:", nvna.info())
        print("version:", nvna.version())

        # pause the live sweep so the scan result is stable, then scan S11.
        nvna.pause()
        raw = nvna.get_scan_s11(int(args.start), int(args.stop), args.points)  # outmask 2
        nvna.resume()

        reals, imags = convert_s11_data_to_arrays(raw)
        print(f"got {len(reals)} S11 samples over "
              f"{args.start:.0f}..{args.stop:.0f} Hz")
        if reals:
            print(f"first sample: {reals[0]:+.6f} {imags[0]:+.6f}j")
            print(f"last sample:  {reals[-1]:+.6f} {imags[-1]:+.6f}j")
    finally:
        nvna.disconnect()       # always release the port
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
