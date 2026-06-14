#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/screen_capture.py'
#   Autoconnect, grab the screen framebuffer with capture(), decode it (BGR565),
#   and save a PNG. Requires Pillow (and numpy for the fast decode path):
#       pip install -e ".[plotting]"
#       python examples/screen_capture.py
#       python examples/screen_capture.py --byte-order big   # compare byte order
#
#   NOTE (tinySA cross-reference): the NanoVNA panel is BGR565; the tinySA used
#   RGB565 (red/blue swapped). decode_capture handles the NanoVNA ordering.
#
#   OPEN ITEM: per-pixel byte order (little vs big) is still being confirmed on
#   hardware -- pass --byte-order big to compare. decode_capture defaults little.
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Capture the NanoVNA screen to PNG.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--out", default="example_screen_capture_demo.png")
    ap.add_argument("--byte-order", choices=["little", "big"], default="little",
                    help="BGR565 per-pixel byte order (default little; see notes)")
    ap.add_argument("--show", action="store_true", help="display the image too")
    args = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print('Pillow not installed: pip install -e ".[plotting]"')
        return 1

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
    print("device connected")

    try:
        print(nvna.get_info())

        # device's own resolution -> image size (don't hardcode 800x480)
        res = bytes(nvna.resolution()).decode("utf-8", errors="replace").strip()
        try:
            width, height = (int(x) for x in res.split(","))
        except Exception:
            width, height = nvna.get_screen_size()   # model default
        print(f"resolution: {width}x{height}")

        # capture() reads exactly width*height*2 bytes via the binary path
        raw = nvna.capture(width, height)
        expected = width * height * 2
        print(f"captured {len(raw)} bytes (expected {expected})")
        if len(raw) < expected:
            print("WARNING: short capture -- image will be incomplete. Re-run; if "
                  "it persists, the transfer is timing out (raise the timeout).")
    finally:
        nvna.disconnect()

    # decode via the LIBRARY (single source of the BGR565 logic)
    try:
        pixels = nvna.decode_capture(raw, width, height, byte_order=args.byte_order)
    except ValueError as e:
        print(f"decode failed: {e}")
        return 1

    img = Image.new("RGB", (width, height))
    img.putdata(pixels)
    img.save(args.out)
    print(f"saved {args.out}")
    if args.show:
        img.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
