#! /usr/bin/python3
"""
Command-construction tests for the DisplayUIMixin.

Mocked-serial `nvna` fixture; no hardware. Covers fixed-string screen commands,
beep, lcd (with the X/Y>=0 and RGB565 color fixes), pwm bounds, and touch.
"""

import pytest


# --- fixed-string commands ------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("capture", "capture\r\n"),
    ("capture_screen", "capture\r\n"),
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
