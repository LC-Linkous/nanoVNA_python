# nvnapython/tests/conftest.py
#
# Shared pytest fixtures for the nvnapython test suite.
#
# There are two no-hardware seams (mirroring the tsapython suite):
#
#   * `recorder` / `nvna` -> replace nanoVNA_serial, capturing the exact command
#                            string each library method builds. Use these for
#                            command-construction tests.
#   * `fake_port`         -> a stand-in serial port (tests/fakes.FakePort) that
#                            returns canned bytes, for exercising the real
#                            get_serial_return / clean_return parsing logic.
#
# Plus the hardware seam:
#
#   * `device`            -> a real connected NanoVNA, session-scoped. Hardware
#                            tests (@pytest.mark.hardware) self-skip when no
#                            device is detected.
#
#   python -m pytest                    # everything; hardware self-skips if unplugged
#   python -m pytest -m "not hardware"  # explicitly skip device tests
#   python -m pytest -m hardware        # device tests only
#
# Run from the nvnapython/ project directory (the one with pyproject.toml).

import os
import sys
import pytest

# Make 'src' importable when running pytest from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# NanoVNA / tinySA shared USB VID:PID for the serial interface (STM32 VCP).
_NANOVNA_VID = 0x0483
_NANOVNA_PID = 0x5740


# ---------------------------------------------------------------------------
# Hardware-detection gate
# ---------------------------------------------------------------------------

def _device_present() -> bool:
    """Cheap check (no port open) for a NanoVNA-looking serial device.

    NOTE: intentionally NOT cached. During hardware bring-up you plug/unplug
    the device between runs; a session-global cache would latch the first
    result and make a freshly-connected device keep self-skipping until the
    process restarts. Set NVNA_FORCE_HARDWARE=1 to force-run hardware tests
    regardless of detection (useful when a model reports an unexpected PID).
    """
    if os.environ.get("NVNA_FORCE_HARDWARE") == "1":
        return True
    try:
        from serial.tools import list_ports
        return any(
            p.vid == _NANOVNA_VID and p.pid == _NANOVNA_PID
            for p in list_ports.comports()
        )
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Auto-skip hardware-marked tests when no device is detected."""
    if _device_present():
        return
    skip_hw = pytest.mark.skip(reason="no NanoVNA detected on any serial port")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hw)


# ---------------------------------------------------------------------------
# Command-construction seam (mock; no hardware)
# ---------------------------------------------------------------------------

class SerialRecorder:
    """Drop-in replacement for nanoVNA.nanoVNA_serial.

    Records every writebyte string it is handed and returns a canned reply
    (default empty bytearray, matching the device's "no data" responses).
    Set .next_return to control what a given call hands back.
    """

    def __init__(self):
        self.calls = []                  # list of writebyte strings, in order
        self.next_return = bytearray(b"")

    def __call__(self, writebyte, printBool=False, pts=None):
        self.calls.append(writebyte)
        return self.next_return

    # convenience accessors -------------------------------------------------
    @property
    def last(self):
        """The most recent command string sent, or None if nothing was sent."""
        return self.calls[-1] if self.calls else None

    @property
    def count(self):
        return len(self.calls)


@pytest.fixture
def recorder():
    """A bare SerialRecorder, in case a test wants to wire it up manually."""
    return SerialRecorder()


@pytest.fixture
def nvna(recorder):
    """A nanoVNA instance whose serial layer is replaced by the recorder.

    A fresh nanoVNA() is already seeded to the F V2 default model by __init__
    (via _apply_model in core.py), so this fixture does NOT set bounds manually.
    Seeding them here would risk drifting from the real attribute names in
    core.py (e.g. the real names are minVNADeviceFreq/maxVNADeviceFreq, not
    minDeviceFreq/maxDeviceFreq). Tests that need a different model call
    dev.select_existing_device(...) themselves. Use this for command-construction
    tests:

        def test_frequencies(nvna):
            nvna.frequencies()
            assert nvna._recorder.last == 'frequencies\\r\\n'
    """
    from nvnapython.core import nanoVNA

    dev = nanoVNA()                      # already seeded to F V2 by __init__
    dev.nanoVNA_serial = recorder
    dev._recorder = recorder             # handy backref for assertions
    return dev


# ---------------------------------------------------------------------------
# Parsing seam (mock; no hardware)
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_port():
    """A FakePort (tests/fakes.FakePort) for driving the real parsing helpers."""
    from tests.fakes import FakePort
    return FakePort()


@pytest.fixture
def parsing_nvna(fake_port):
    """A nanoVNA with the REAL nanoVNA_serial/clean_return logic intact, but
    `ser` swapped for a FakePort. Preload the port with raw device bytes
    (FakePort(b"...") or by setting fake_port._buf) and call the library method
    as usual; the real read loop + cleaner run against the canned bytes.
    """
    from nvnapython.core import nanoVNA

    dev = nanoVNA()
    dev.ser = fake_port
    return dev


# ---------------------------------------------------------------------------
# Hardware seam (real device; ONE shared connection for the whole session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def device():
    """Session-wide connection to a real NanoVNA, shared by ALL hardware modules.

    Why session scope: opening/closing the port once per hardware MODULE made the
    STM32 virtual COM port re-enumerate between modules, and on Windows that race
    sometimes left a later module unable to grab the port -- so it would hit the
    skip below and the whole module would skip mid-run (e.g. test_hardware_probe
    skipping while test_hardware_boundaries ran). Connecting once for the session
    and reusing the handle removes the race: every hardware module binds to the
    same already-open device.

    The per-module `device` fixtures in the individual test_hardware_*.py files
    should be REMOVED so they fall through to this one. (If a module still
    defines its own, that local fixture shadows this and the race returns.)

    Skips cleanly (does not error) if no device is detected at collection time
    or if the connection itself fails (port busy, unplugged, permissions).
    """
    from nvnapython.core import nanoVNA

    dev = nanoVNA()
    dev.set_verbose(False)               # probes do their own printing; keep quiet
    dev.set_error_byte_return(True)      # explicit b'ERROR' so probes see rejects

    found_bool, connected_bool = dev.autoconnect()
    if not connected_bool:
        pytest.skip("NanoVNA detected but could not connect (port busy or permissions?)")

    yield dev

    # Union of the cleanup the old per-module fixtures did, each step independent
    # and tolerant so one failure can't leave the port held open. Runs ONCE, at
    # the end of the whole session.
    try:
        dev.command("recall 0")          # restore the startup preset
    except Exception:
        pass
    try:
        dev.resume()                     # un-pause if a probe paused the sweep
    except Exception:
        pass
    try:
        dev.disconnect()                 # always release the port
    except Exception:
        pass
