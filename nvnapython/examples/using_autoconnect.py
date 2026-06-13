#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/using_autoconnect.py'
#   Demonstrates autoconnect(): scan the serial ports for a NanoVNA-class device,
#   connect to the first match, report what was found, and disconnect.
#
#   autoconnect() returns (found, connected): found = a matching USB VID:PID was
#   seen; connected = the port actually opened. They can differ (found but busy).
#       python examples/using_autoconnect.py
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def main():
    argparse.ArgumentParser(description="NanoVNA autoconnect demo.").parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(True)              # so you can see which port it checks
    nvna.set_error_byte_return(True)

    found, connected = nvna.autoconnect()

    if not found:
        print("no NanoVNA-class device (USB VID:PID 0483:5740) was found on any port.")
        print("If yours enumerates differently, connect() to the port explicitly.")
        return 1
    if not connected:
        print("a device was FOUND but could NOT be opened (port busy or permissions?).")
        print("Close other programs using the port; on Linux check dialout group.")
        return 1

    try:
        print("device connected")
        print(nvna.get_info())
    finally:
        nvna.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
