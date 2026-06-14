#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/identify_and_select_model.py'
#   Connect, read the device's identity (info / version / serial / resolution),
#   and select the matching MODEL ENVELOPE so the library's range checks use the
#   right bounds for your unit. select_existing_device() sets LIBRARY bounds only;
#   it does not change anything on the device.
#       python examples/identify_and_select_model.py
#       python examples/identify_and_select_model.py --model NANOVNA_H4
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def _txt(raw):
    return bytes(raw).decode("utf-8", errors="replace").strip() if raw else ""


def main():
    ap = argparse.ArgumentParser(description="Identify a NanoVNA and select its model envelope.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--model", default=None,
                    help="model preset to select (e.g. NANOVNA_F_V2, NANOVNA_H4). "
                         "Omit to keep the default and just report.")
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(False)             # quiet; we print what we want below
    nvna.set_error_byte_return(True)

    # Show the known presets BEFORE connecting -- this needs no device.
    print("known model presets:", ", ".join(nvna.list_known_models()))
    print("default model after construction:", nvna.get_device_model())
    print()

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    try:
        # read what the DEVICE reports about itself
        print("== device identity (read from hardware) ==")
        print("info:      ", _txt(nvna.info()))
        print("version:   ", _txt(nvna.version()))
        print("serial(SN):", _txt(nvna.SN()))
        print("resolution:", _txt(nvna.resolution()))
        print()

        # optionally select a model envelope to match this unit
        if args.model:
            ok = nvna.select_existing_device(args.model)
            if not ok:
                print(f"'{args.model}' is not a known preset; bounds unchanged. "
                      f"Known: {', '.join(nvna.list_known_models())}")
            else:
                print(f"selected model envelope: {args.model}")

        # report the LIBRARY bounds now in effect (these gate error checking)
        w, h = nvna.get_screen_size()
        print("\n== library bounds now in effect ==")
        print("model:        ", nvna.get_device_model())
        print("max points:   ", nvna.get_max_points())
        print("freq range:   ",
              f"{nvna.get_min_device_freq():.0f} .. {nvna.get_max_device_freq():.0f} Hz")
        print("screen size:  ", f"{w}x{h}")
        print("\nTip: if the resolution read from the device above doesn't match the "
              "screen size here, select the right --model (or override with "
              "set_screen_size / set_max_points / set_min_device_freq).")
    finally:
        nvna.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
