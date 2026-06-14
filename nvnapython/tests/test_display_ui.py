#! /usr/bin/python3
"""
Command-construction tests for the DisplayUIMixin.

Mocked-serial `nvna` fixture; no hardware. Covers fixed-string screen commands,
beep, lcd (with the X/Y>=0 and RGB565 color fixes), pwm bounds, and touch.
"""

import pytest


# --- fixed-string commands ------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("LCD_ID", "LCD_ID\r\n"),
    ("get_LCD_ID", "LCD_ID\r\n"),
    ("resolution", "resolution\r\n"),
    ("get_resolution", "resolution\r\n"),
    ("lcd_resolution", "resolution\r\n"),
    ("touch_cal", "touchcal\r\n"),
    ("start_touch_cal", "touchcal\r\n"),
    ("touch_test", "touchtest\r\n"),
    ("start_touch_test", "touchtest\r\n"),
])
def test_fixed_string_commands(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


# --- capture: BINARY path (length-driven read, not the text command path) ---
# capture() deliberately bypasses nanoVNA_serial/clean_return: it writes
# 'capture\r\n' directly and reads exactly width*height*2 bytes via
# get_binary_return. So it is NOT a recorder command -- it is exercised with a
# FakePort preloaded with a fake framebuffer.

ECHO = b"capture\r\n"   # the command echo the device sends before the image


def test_capture_reads_full_binary_frame():
    from nvnapython.core import nanoVNA
    from tests.fakes import FakePort

    dev = nanoVNA()
    # use a tiny screen so the expected frame is small and explicit
    dev.set_screen_size(4, 2)                 # 4*2*2 = 16 image bytes
    frame = bytes(range(16))                  # the "framebuffer"
    # real stream = echo + image + trailing prompt; capture() must strip echo
    # and prompt and return exactly the image, correctly aligned.
    dev.ser = FakePort(ECHO + frame + b"ch> \r\nch> ")

    raw = dev.capture()                       # width/height default to 4x2
    assert len(raw) == 16                     # exactly the image
    assert bytes(raw) == frame                # content intact AND aligned (echo
    #                                           stripped -> not shifted by 9 bytes)


def test_capture_writes_capture_command():
    from nvnapython.core import nanoVNA
    from tests.fakes import FakePort

    dev = nanoVNA()
    dev.set_screen_size(2, 2)                 # 8 bytes
    dev.ser = FakePort(ECHO + bytes(8) + b"ch> ")
    dev.capture()
    # the command actually written to the port is 'capture\r\n'
    assert dev.ser.written and dev.ser.written[-1] == b"capture\r\n"


def test_capture_strips_echo_no_shift():
    # explicit regression test for the 9-byte echo misalignment: a frame of
    # known increasing bytes must come back starting at byte 0, not at the echo.
    from nvnapython.core import nanoVNA
    from tests.fakes import FakePort

    dev = nanoVNA()
    dev.set_screen_size(8, 1)                 # 16 image bytes
    frame = bytes(range(100, 116))            # distinctive, non-zero
    dev.ser = FakePort(ECHO + frame + b"ch> \r\nch> ")
    raw = dev.capture()
    assert bytes(raw) == frame                # first image byte is 100, not echo
    assert raw[0] == 100                       # would be ord('c')=99 if shifted


def test_capture_short_read_returns_what_it_got():
    from nvnapython.core import nanoVNA
    from tests.fakes import FakePort

    dev = nanoVNA()
    dev.set_serial_timeout(0.05)              # bail fast in these no-data waits
    dev.set_serial_poll_interval(0.005)
    dev.set_screen_size(100, 100)             # expects 20000 bytes
    # echo present so the echo-read succeeds, then only 4 image bytes arrive
    dev.ser = FakePort(ECHO + b"\x01\x02\x03\x04")
    raw = dev.capture()
    assert len(raw) == 4                      # returns what it got, no hang/crash


# --- beep: on/off ---------------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("beep_on", "beep on\r\n"),
    ("beep_off", "beep off\r\n"),
])
def test_beep_aliases(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


def test_beep_invalid(nvna):
    nvna.beep("loud")
    assert nvna._recorder.count == 0


# --- lcd / draw_rect ------------------------------------------------------

def test_lcd_valid(nvna):
    nvna.lcd(10, 20, 100, 50, "F800")
    assert nvna._recorder.last == "lcd 10 20 100 50 F800\r\n"


def test_lcd_origin_allowed(nvna):
    # FIXED: original required X>0 and Y>0, rejecting the valid (0,0) corner.
    nvna.lcd(0, 0, 100, 50, "07E0")
    assert nvna._recorder.last == "lcd 0 0 100 50 07E0\r\n"


def test_lcd_color_with_0x_prefix(nvna):
    # FIXED: original len(COL)==4 check rejected an explicit 0x prefix.
    nvna.lcd(10, 20, 100, 50, "0xF800")
    assert nvna._recorder.last == "lcd 10 20 100 50 0xF800\r\n"


def test_draw_rect_alias(nvna):
    nvna.draw_rect(5, 5, 10, 10, "FFFF")
    assert nvna._recorder.last == "lcd 5 5 10 10 FFFF\r\n"


@pytest.mark.parametrize("X,Y,W,H,COL", [
    (-1, 20, 100, 50, "F800"),     # negative X
    (10, -1, 100, 50, "F800"),     # negative Y
    (1.5, 20, 100, 50, "F800"),    # non-int coord
    (10, 20, 100, 50, "F80"),      # bad color (3 hex digits)
    (10, 20, 100, 50, "GGGG"),     # bad color (non-hex)
])
def test_lcd_invalid(nvna, X, Y, W, H, COL):
    nvna.lcd(X, Y, W, H, COL)
    assert nvna._recorder.count == 0


# --- pwm: 0.0..1.0 --------------------------------------------------------

@pytest.mark.parametrize("val,expected", [
    (0.0, "pwm 0.0\r\n"),
    (1.0, "pwm 1.0\r\n"),
    (0.5, "pwm 0.5\r\n"),
])
def test_pwm_valid(nvna, val, expected):
    nvna.pwm(val)
    assert nvna._recorder.last == expected


def test_set_screen_brightness_alias(nvna):
    nvna.set_screen_brightness(0.75)
    assert nvna._recorder.last == "pwm 0.75\r\n"


@pytest.mark.parametrize("val", [-0.1, 1.1, "bright"])
def test_pwm_invalid(nvna, val):
    nvna.pwm(val)
    assert nvna._recorder.count == 0


def test_beep_time_invalid(nvna):
    # non-numeric duration -> error path, no beep sent.
    nvna.beep_time("a while")
    assert nvna._recorder.count == 0


def test_beep_time_valid(nvna, monkeypatch):
    # numeric duration -> beep on, sleep (patched to no-op), beep off.
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)
    nvna.beep_time(0.01)
    assert nvna._recorder.calls[0] == "beep on\r\n"
    assert nvna._recorder.calls[-1] == "beep off\r\n"