#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/screen_capture.py'
#   Autoconnect, grab the screen framebuffer, decode it (BGR565), and save a PNG.
#   Requires the [plotting] extra for Pillow (numpy optional):
#       pip install -e ".[plotting]"
#
#   This keeps the original example's intent but:
#     * uses the installed package import (from nvnapython import nanoVNA),
#     * decodes color via the LIBRARY now (nvna.decode_capture), so the BGR565
#       logic lives in one place instead of being copy-pasted per example,
#     * reads the raw binary directly off the port instead of the text path,
#       because 'capture' is BINARY and the text path can truncate it at a
#       'ch>'-looking byte run (the original's 1-byte padding hack was treating
#       that symptom),
#     * never mutates an immutable bytes object (the original .append(0) would
#       AttributeError if capture() returned bytes).
#
#   NOTE (intentional tinySA cross-reference): the NanoVNA panel is BGR565,
#   whereas the tinySA used RGB565 -- red and blue are SWAPPED. decode_capture
#   handles the swap; if you port a tinySA decoder you must account for it.
#
#   OPEN ITEM: the per-pixel byte order (little- vs big-endian) is being
#   confirmed on hardware -- see tests/test_hardware_capture_probe.py, which
#   prints both decodes. decode_capture defaults to little-endian (matching the
#   original example); pass byte_order="big" to compare.
##-------------------------------------------------------------------------------\

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def read_capture_raw(nvna, settle_s=0.4, idle_giveup_s=1.0):
    # Issue 'capture' and read raw bytes off the port, bypassing the text prompt
    # framing (which is wrong for binary). Read until the stream goes idle, then
    # strip a trailing console-prompt run if the device appended one.
    ser = nvna.ser
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b"capture\r\n")

    buf = bytearray()
    last = time.time()
    time.sleep(settle_s)
    while True:
        waiting = ser.in_waiting
        if waiting:
            buf += ser.read(waiting)
            last = time.time()
        elif time.time() - last > idle_giveup_s:
            break
        else:
            time.sleep(0.01)

    tail = bytes(buf)
    while True:
        s = tail.rstrip()
        if s.endswith(b"ch>"):
            tail = s[:-3]
            continue
        break
    if tail.endswith(b"\r\n"):
        tail = tail[:-2]
    return tail


def main():
    ap = argparse.ArgumentParser(description="Capture the NanoVNA screen to PNG.")
    ap.add_argument("--port", default=None)
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

    found_bool, connected_bool = nvna.autoconnect() if not args.port \
        else (True, nvna.connect(args.port))
    if not connected_bool:
        print("ERROR: could not connect to port")
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

        raw = read_capture_raw(nvna)
        expected = width * height * 2
        print(f"captured {len(raw)} bytes (expected {expected})")
    finally:
        nvna.disconnect()

    # decode via the LIBRARY (single source of the BGR565 logic)
    try:
        pixels = nvna.decode_capture(raw, width, height, byte_order=args.byte_order)
    except ValueError as e:
        print(f"decode failed: {e}")
        print("The binary read was likely truncated. Re-run; if it persists, the "
              "device may need a dedicated binary capture path in the library.")
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
