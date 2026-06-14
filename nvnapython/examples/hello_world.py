#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/hello_world.py'
#   The smallest nvnapython example: connect, print device info, disconnect.
#   Standalone single file -- run straight from the repo without installing:
#       python examples/hello_world.py
#       python examples/hello_world.py --port COM6      # explicit port
#
#   disconnect() is in a finally block so the COM port is always released, even
#   if something raises (a leaked handle is the usual cause of the next run
#   failing with "no device connected" on Windows).
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

# Make 'src' importable when running straight from the repo without installing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Minimal NanoVNA connect + info example.")
    ap.add_argument("--port", default=None,
                    help="serial port (e.g. COM6 or /dev/ttyACM0). Omit to autoconnect.")
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(True)              # detailed messages
    nvna.set_error_byte_return(True)    # explicit b'ERROR' on a rejected command

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    try:
        print("device connected")
        print(nvna.info())
    finally:
        nvna.disconnect()              # always release the port
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
