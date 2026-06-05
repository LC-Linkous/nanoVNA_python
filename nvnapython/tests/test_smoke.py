#! /usr/bin/python3
"""
Smoke tests for nvnapython. Requires NO hardware.
Confirms the package imports, instantiates, exposes its core methods, and that
the library-side settings don't raise.

Run with: pytest tests/test_smoke.py
"""

import pytest


def test_import():
    """The package imports and exposes nanoVNA."""
    from nvnapython import nanoVNA  # noqa: F401


def test_create_instance():
    """A nanoVNA instance can be constructed without hardware."""
    from nvnapython import nanoVNA
    assert nanoVNA() is not None


# Device-agnostic methods that every build must expose. If the refactor ever
# drops or renames one of these, this test fails loudly.
REQUIRED_METHODS = [
    "autoconnect", "disconnect",
    "info", "version", "SN",
    "set_verbose", "set_error_byte_return",
    "scan", "data", "frequencies",
    "cal", "marker", "trace",
    "pause", "resume",
]


@pytest.mark.parametrize("method_name", REQUIRED_METHODS)
def test_required_method_exists(nvna, method_name):
    """Each core method is present and callable on the composed class."""
    assert callable(getattr(nvna, method_name, None)), \
        f"missing required method: {method_name}"


def test_verbose_setting_does_not_raise(nvna):
    nvna.set_verbose(True)
    nvna.set_verbose(False)


def test_error_byte_setting_does_not_raise(nvna):
    nvna.set_error_byte_return(True)
    nvna.set_error_byte_return(False)


def test_select_existing_device_known_model(nvna):
    """Known preset returns True and sets bounds; unknown returns False."""
    assert nvna.select_existing_device("NANOVNA_F_V2") is True
    assert nvna.select_existing_device("NOT_A_REAL_MODEL") is False
