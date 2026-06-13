#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/test_hardware_capture_probe.py'
#
#   HARDWARE PROBE: the 'capture' screen-buffer format.
#
#   The README TODO flags this as UNVERIFIED on this firmware:
#       "Verify capture returns the expected 800x480x2 byte BGR565 buffer and
#        the example image decode is correct on this firmware."
#
#   This probe settles three things, printing what the device actually returns:
#     1. How many bytes 'capture' yields, vs the expected 800*480*2 = 768000
#        for a 16-bit-per-pixel 800x480 panel.
#     2. Whether the byte count matches the device's OWN reported resolution
#        (read live via resolution()), so the check is self-consistent rather
#        than hardcoded to 800x480.
#     3. A BGR565-vs-RGB565 sanity read: decode the first few pixels both ways
#        and print them, so the byte-order note (NanoVNA = BGR565, tinySA =
#        RGB565) can be eyeballed against a known screen region.
#
#   IMPORTANT: 'capture' returns BINARY, not text. The current text-oriented
#   nanoVNA_serial / clean_return path is NOT appropriate for it (a binary frame
#   has no 'ch>' line framing and may contain 0x63('c')/0x68('h')/0x3e('>')
#   bytes mid-image). This probe therefore reads the raw bytes directly off the
#   serial port AFTER issuing 'capture', bypassing clean_return, and reports the
#   true length. If the count is right but the library's capture() (which goes
#   through the text path) returns something shorter, that is the evidence that
#   capture() needs a dedicated binary read path.
#
#   Run with output visible:
#       pytest -m hardware tests/test_hardware_capture_probe.py -s -v
#
#   SAFETY: read-only. 'capture' does not change device state or write storage.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import time
import pytest

pytestmark = pytest.mark.hardware


def _read_raw_binary(dev, settle_s=0.4, idle_giveup_s=1.0):
    """
    Issue 'capture' and read the raw bytes off the port directly, WITHOUT the
    text 'ch>'-prompt framing logic (which is wrong for binary). We read until
    the stream goes idle for idle_giveup_s, then return everything collected.

    This is probe-only scaffolding; the library's real binary capture path, if
    added, would frame this more precisely (e.g. by expected byte count).
    """
    ser = dev.ser
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b"capture\r\n")

    buf = bytearray()
    last_data = time.time()
    # give the device a moment to start streaming the framebuffer
    time.sleep(settle_s)
    while True:
        waiting = ser.in_waiting
        if waiting:
            buf += ser.read(waiting)
            last_data = time.time()
        else:
            if time.time() - last_data > idle_giveup_s:
                break
            time.sleep(0.01)
    return bytes(buf)


def _strip_trailing_prompt(buf):
    """
    The binary framebuffer is usually followed by the text 'ch> \\r\\nch> '
    prompt. Strip a trailing prompt run so the reported image-byte count isn't
    inflated by the console tail. Only strips from the END.
    """
    tail = buf
    # remove trailing whitespace + 'ch>' runs
    while True:
        stripped = tail.rstrip()
        if stripped.endswith(b"ch>"):
            tail = stripped[:-3]
            continue
        break
    if tail.endswith(b"\r\n"):
        tail = tail[:-2]
    return tail


def test_probe_capture_byte_count(device):
    # device's own reported resolution -> expected byte count at 2 bytes/pixel
    res = device.resolution()
    res_txt = bytes(res).decode("utf-8", errors="replace").strip()
    print(f"\n  [REPORT] device resolution(): {res_txt!r}")
    expected = None
    try:
        w, h = (int(x) for x in res_txt.split(","))
        expected = w * h * 2
        print(f"  [REPORT] expected capture bytes (w*h*2): {w}x{h}x2 = {expected}")
    except Exception:
        print("  [REPORT] could not parse resolution; will report raw count only")

    raw = _read_raw_binary(device)
    img = _strip_trailing_prompt(raw)
    print(f"  [REPORT] raw bytes read: {len(raw)}  | after prompt-strip: {len(img)}")
    if expected is not None:
        delta = len(img) - expected
        print(f"  [REPORT] delta vs expected: {delta:+d} "
              f"({'MATCH' if delta == 0 else 'MISMATCH -- investigate framing'})")

    # First pixels decoded both byte-orders, for the BGR565/RGB565 eyeball.
    if len(img) >= 6:
        def rgb565(hi, lo, swap):
            v = (lo << 8) | hi if swap else (hi << 8) | lo
            r = (v >> 11) & 0x1F
            g = (v >> 5) & 0x3F
            b = v & 0x1F
            return (r << 3, g << 2, b << 3)
        print("  [REPORT] first 3 px as (hi<<8|lo):  ",
              [rgb565(img[i], img[i + 1], False) for i in range(0, 6, 2)])
        print("  [REPORT] first 3 px as (lo<<8|hi):  ",
              [rgb565(img[i], img[i + 1], True) for i in range(0, 6, 2)])
        print("  [REPORT] NanoVNA is documented BGR565 (tinySA was RGB565); "
              "compare against a known screen color to confirm byte order.")

    # Informational probe: only fail if we got effectively nothing back, which
    # would mean the read approach itself is wrong (not a format question).
    assert len(img) > 1000, \
        f"capture returned only {len(img)} bytes -- read path likely wrong"


def test_probe_library_capture_vs_raw(device):
    """
    Contrast: the library's capture() goes through the TEXT path
    (nanoVNA_serial -> clean_return), which is not binary-safe. Report how many
    bytes it returns next to the raw read, as direct evidence for whether
    capture() needs a dedicated binary read path.
    """
    via_lib = device.capture()
    lib_len = len(via_lib) if via_lib else 0
    raw = _strip_trailing_prompt(_read_raw_binary(device))
    print(f"\n  [REPORT] capture() via text path: {lib_len} bytes")
    print(f"  [REPORT] raw binary read:          {len(raw)} bytes")
    if lib_len < len(raw):
        print("  [REPORT] CONCLUSION: text-path capture() is SHORT -- it stops at "
              "the first 'ch>'-looking byte run in the image. capture() needs a "
              "binary read path keyed on expected byte count, not prompt framing.")
    else:
        print("  [REPORT] CONCLUSION: text path returned >= raw; re-examine assumptions.")
    # informational only
