#! /usr/bin/python3
"""
Shared pytest fixtures for the nvnapython test suite.

These tests run WITHOUT hardware. The nanoVNA class talks to the device only
through `self.ser` (a pyserial Serial object) and the single method
`nanoVNA_serial()`. We exploit those two seams:

  * `recorder`   -> replaces nanoVNA_serial, capturing the exact command string
                    each library method builds. Use for command-construction tests.
  * `fake_port`  -> a stand-in serial port that returns canned bytes, letting us
                    test the real get_serial_return / clean_return parsing logic
                    against captured device output.

Neither touches real hardware.
"""

import sys
import os
import pytest

# Make 'src' importable when running `pytest` from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA  # noqa: E402


# ---------------------------------------------------------------------------
# Command-construction seam
# ---------------------------------------------------------------------------

class SerialRecorder:
    """
    Drop-in replacement for nanoVNA.nanoVNA_serial.

    Records every writebyte string it is handed and returns a canned reply
    (default empty bytearray, matching the device's "no data" responses).
    Set .next_return to control what a given call hands back.
    """

    def __init__(self):
        self.calls = []            # list of writebyte strings, in order
        self.next_return = bytearray(b"")

    def __call__(self, writebyte, printBool=False, pts=None):
        self.calls.append(writebyte)
        return self.next_return

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
    """
    A nanoVNA instance whose serial layer is replaced by the recorder.

    Device-parameter defaults are seeded (as select_existing_device would do)
    so that range-checking methods have sane bounds to validate against.
    Use this for command-construction tests:

        def test_scan(nvna):
            nvna.scan(1_000_000, 2_000_000, 101, 2)
            assert nvna._recorder.last == 'scan 1000000 2000000 101 2\\r\\n'
    """
    dev = nanoVNA()
    # Seed library-side device bounds (NanoVNA-F V2 defaults).
    dev.maxPoints = 201
    dev.minVNADeviceFreq = 50e3
    dev.maxVNADeviceFreq = 3e9
    dev.screenWidth = 800
    dev.screenHeight = 480

    dev.nanoVNA_serial = recorder
    dev._recorder = recorder          # handy backref for assertions
    return dev


# ---------------------------------------------------------------------------
# Parsing seam
# ---------------------------------------------------------------------------

class FakePort:
    """
    Minimal stand-in for serial.Serial, used to drive the real parsing helpers
    (get_serial_return) with canned bytes.

    Feed it the raw bytes the device would emit; it dispenses them through the
    in_waiting / read() interface the library expects.
    """

    def __init__(self, payload=b""):
        self._buf = bytes(payload)
        self.written = []           # bytes written by the library
        self._reset_in = 0
        self._reset_out = 0

    @property
    def in_waiting(self):
        return len(self._buf)

    def read(self, n):
        chunk, self._buf = self._buf[:n], self._buf[n:]
        return chunk

    def write(self, data):
        self.written.append(data)
        return len(data)

    def reset_input_buffer(self):
        self._reset_in += 1

    def reset_output_buffer(self):
        self._reset_out += 1

    def close(self):
        pass


@pytest.fixture
def parsing_nvna():
    """
    A nanoVNA instance with the REAL nanoVNA_serial/clean_return logic intact,
    but `ser` swapped for a FakePort. Load a payload per-test:

        def test_clean(parsing_nvna):
            parsing_nvna.ser._buf = b'info\\r\\nModel: NanoVNA\\r\\nch>'
            out = parsing_nvna.get_serial_return()
            ...
    """
    dev = nanoVNA()
    dev.ser = FakePort()
    return dev
