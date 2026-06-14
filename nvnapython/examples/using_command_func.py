#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/using_command_func.py'
#   command() is a passthrough: it sends an arbitrary command string straight to
#   the device and returns the cleaned reply, with NO library-side error checking.
#   Use it for device features the library doesn't wrap yet, or to experiment.
#       python examples/using_command_func.py
#       python examples/using_command_func.py --cmd "info"
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="NanoVNA raw command() passthrough demo.")
    ap.add_argument("--port", default=None,
                    help="serial port. Omit to autoconnect.")
    ap.add_argument("--cmd", default="scan 150000 250000000 200 2",
                    help="raw command string to send (no error checking)")
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
        # a scan pauses the sweep on the device; resume() afterward so the
        # screen isn't left frozen. (Harmless for non-scan commands.)
        raw = nvna.command(args.cmd)
        print(f"sent: {args.cmd!r}")
        print(f"got {len(raw)} bytes:")
        print(raw)
        nvna.resume()
    finally:
        nvna.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
