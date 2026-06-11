#! /usr/bin/python3
"""
Phantom-command guard.

The device 'help' dump (captured from real NanoVNA-F V2 firmware via
test_hardware_audit.py) is the authoritative list of commands the device
accepts. This test scans the library's command mixins for every device command
string they BUILD and asserts each one is in that authoritative list -- so a
command the device doesn't actually have (a "phantom", like 'port' and 'restart'
were) fails here at commit time instead of silently shipping.

If you intentionally add a command that IS on the device but not yet in the
captured list, update DEVICE_COMMANDS below (and ideally re-capture the help
dump on hardware to confirm).

This test requires NO hardware -- it reads the source statically.
"""

import os
import re
import pytest


# Authoritative command set, transcribed from the device 'help' dump captured
# on NanoVNA-F V2 firmware (see test_hardware_audit.py::test_capture_help_reference).
DEVICE_COMMANDS = {
    "help", "reset", "cwfreq", "saveconfig", "clearconfig", "data",
    "frequencies", "scan", "sweep", "touchcal", "touchtest", "pause", "resume",
    "cal", "save", "recall", "trace", "marker", "edelay", "pwm", "beep", "lcd",
    "capture", "version", "info", "SN", "resolution", "LCD_ID",
}


def _library_command_tokens():
    """
    Statically scan the _commands mixins for the first token of every
    'writebyte = ...' command string the library builds.
    """
    here = os.path.dirname(__file__)
    cmd_dir = os.path.join(here, "..", "src", "nvnapython", "_commands")
    cmd_dir = os.path.abspath(cmd_dir)

    tokens = set()
    pattern = re.compile(r"writebyte\s*=\s*['\"]([A-Za-z_][A-Za-z0-9_]*)")
    for fn in os.listdir(cmd_dir):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(cmd_dir, fn), encoding="utf-8") as f:
            text = f.read()
        for m in pattern.finditer(text):
            tokens.add(m.group(1))
    return tokens


def test_no_phantom_commands():
    """Every device command the library builds must exist on the device."""
    built = _library_command_tokens()
    phantoms = built - DEVICE_COMMANDS
    assert not phantoms, (
        "library builds command(s) the device does not recognise "
        f"(phantoms): {sorted(phantoms)}. Either the command is wrong/removed, "
        "or it is a real-but-unlisted command that should be added to "
        "DEVICE_COMMANDS after confirming on hardware."
    )


def test_library_covers_core_commands():
    """
    Sanity check the static scanner actually found commands (guards against the
    regex silently matching nothing and the phantom test passing vacuously).
    """
    built = _library_command_tokens()
    # a few we know the library builds
    for expected in ("scan", "cal", "marker", "trace", "info"):
        assert expected in built, f"scanner missed '{expected}' -- regex may be broken"
