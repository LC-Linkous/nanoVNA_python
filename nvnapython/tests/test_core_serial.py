#! /usr/bin/python3
"""
Core / serial-layer tests.

These cover core.py: the parts the per-mixin command tests don't touch --
the serial read loop (get_serial_return), the write/read round trip
(nanoVNA_serial), connect / autoconnect / disconnect, and the library-side
override setters/getters. No hardware required: we drive the real logic with
the FakePort seam (and a chunking subclass for the read loop) and a couple of
tiny fakes for the pyserial entry points.

The read-loop tests pin the exact framing bugs the overhaul fixed:
  * the device prompt is 'ch> ' WITH A TRAILING SPACE, often DOUBLED
    ('ch> \\r\\nch> '); the loop must stop on it instead of timing out.
  * USB CDC delivers the reply in CHUNKS with gaps; in_waiting briefly reading
    0 does not mean the reply is done, so the loop must keep waiting until the
    prompt actually arrives.
"""

import time
import pytest

from nvnapython import nanoVNA
from tests.conftest import FakePort


# ---------------------------------------------------------------------------
# A FakePort that hands its payload out in fixed-size CHUNKS, returning 0 from
# in_waiting between chunks for `gap_polls` polls. This exercises the real
# chunked-read / gap-tolerant path in get_serial_return that the plain
# FakePort (which dispenses everything at once) cannot.
# ---------------------------------------------------------------------------

class ChunkedFakePort(FakePort):
    def __init__(self, payload=b"", chunk=4, gap_polls=1):
        super().__init__(payload)
        self._chunk = chunk
        self._gap_polls = gap_polls
        self._since_gap = 0

    @property
    def in_waiting(self):
        # Simulate the gap between USB packets: every time we'd hand out a
        # chunk, first report 0 for gap_polls reads so the loop has to wait.
        if not self._buf:
            return 0
        if self._since_gap < self._gap_polls:
            self._since_gap += 1
            return 0
        self._since_gap = 0
        return min(self._chunk, len(self._buf))


# ---------------------------------------------------------------------------
# get_serial_return: stop-on-prompt, chunk reassembly, timeout
# ---------------------------------------------------------------------------

def test_get_serial_return_stops_on_doubled_space_prompt():
    # Real F V2 tail: 'ch> \r\nch> ' (trailing space, doubled). The loop must
    # detect the prompt via rstrip() and stop -- NOT fall through to timeout.
    dev = nanoVNA()
    dev.ser = FakePort(b"version\r\n0.3.0\r\nch> \r\nch> ")
    t0 = time.time()
    out = dev.get_serial_return()
    # returned fast (well under the 5s default timeout) because the prompt matched
    assert time.time() - t0 < 1.0
    assert bytes(out).rstrip().endswith(b"ch>")
    assert b"0.3.0" in out


def test_get_serial_return_reassembles_chunks():
    # The reply arrives a few bytes at a time with gaps in between; the loop
    # must accumulate across the gaps and only stop at the prompt.
    dev = nanoVNA()
    dev.set_serial_poll_interval(0.001)
    payload = b"info\r\nModel: NanoVNA-F_V2\r\nch> \r\nch> "
    dev.ser = ChunkedFakePort(payload, chunk=5, gap_polls=1)
    out = dev.get_serial_return()
    # The loop stops the instant rstrip() ends with the prompt, which can be
    # before the final trailing-space chunk lands -- so the result may end at
    # 'ch>' rather than 'ch> '. The contract is: nothing dropped from the
    # MIDDLE, and the read ends at the prompt.
    assert bytes(out).rstrip().endswith(b"ch>")
    assert b"NanoVNA-F_V2" in out          # nothing dropped across the gaps
    assert out.startswith(b"info\r\n")     # nothing dropped from the front
    # the cleaner still recovers the exact payload from this chunked read
    assert bytes(dev.clean_return(out)) == b"Model: NanoVNA-F_V2"


def test_get_serial_return_times_out_without_prompt():
    # No prompt ever arrives (e.g. the port dropped after reset). The loop must
    # bail at the wall-clock deadline instead of hanging forever, returning
    # whatever it accumulated.
    dev = nanoVNA()
    dev.set_serial_timeout(0.05)
    dev.set_serial_poll_interval(0.01)
    dev.ser = FakePort(b"partial reply, no prompt")
    t0 = time.time()
    out = dev.get_serial_return()
    elapsed = time.time() - t0
    assert 0.05 <= elapsed < 1.0          # waited ~timeout, not forever
    assert bytes(out) == b"partial reply, no prompt"


# ---------------------------------------------------------------------------
# nanoVNA_serial: full write -> read -> clean round trip on the real helpers
# ---------------------------------------------------------------------------

def test_nanoVNA_serial_round_trip_cleans_payload():
    dev = nanoVNA()
    dev.ser = FakePort(b"version\r\n0.3.0\r\nch> \r\nch> ")
    out = dev.nanoVNA_serial("version\r\n")
    # the command was written to the port verbatim (as bytes)
    assert dev.ser.written == [b"version\r\n"]
    # both buffers were flushed before the write
    assert dev.ser._reset_in == 1 and dev.ser._reset_out == 1
    # and the return is the cleaned payload, not the raw frame
    assert bytes(out) == b"0.3.0"


def test_nanoVNA_serial_printbool_echoes(capsys):
    dev = nanoVNA()
    dev.ser = FakePort(b"version\r\n0.3.0\r\nch> \r\nch> ")
    dev.nanoVNA_serial("version\r\n", printBool=True)
    captured = capsys.readouterr()
    assert "0.3.0" in captured.out


# ---------------------------------------------------------------------------
# connect / disconnect
# ---------------------------------------------------------------------------

def test_connect_success(monkeypatch):
    # Patch serial.Serial so connect() opens a fake port and reports True.
    import nvnapython.core as core

    class _OkSerial:
        def __init__(self, port, timeout):
            self.port = port
            self.timeout = timeout

    monkeypatch.setattr(core.serial, "Serial", _OkSerial)
    dev = nanoVNA()
    assert dev.connect("COM_TEST") is True
    assert dev.ser is not None


def test_connect_failure_clears_handle(monkeypatch):
    # A failed open must return False and leave ser as None (no half-open state).
    import nvnapython.core as core

    def _boom(port, timeout):
        raise OSError("device not functioning")

    monkeypatch.setattr(core.serial, "Serial", _boom)
    dev = nanoVNA()
    assert dev.connect("COM_BUSY") is False
    assert dev.ser is None


def test_disconnect_swallows_close_error():
    # disconnect() must never raise, even if the underlying close() throws, and
    # must still clear the handle so the port isn't left logically held.
    dev = nanoVNA()

    class _BadClose:
        def close(self):
            raise OSError("already gone")

    dev.ser = _BadClose()
    dev.disconnect()              # must not raise
    assert dev.ser is None


# ---------------------------------------------------------------------------
# autoconnect: VID/PID matching against a fake comports() listing
# ---------------------------------------------------------------------------

class _PortInfo:
    def __init__(self, device, vid, pid):
        self.device = device
        self.vid = vid
        self.pid = pid


def test_autoconnect_matches_stm32_vid_pid(monkeypatch):
    import nvnapython.core as core
    ports = [
        _PortInfo("COM1", None, None),          # skipped: vid is None
        _PortInfo("COM2", 0x1234, 0x5678),      # skipped: not in accepted list
        _PortInfo("COM3", 0x0483, 0x5740),      # match: STM32 VCP
    ]
    monkeypatch.setattr(core.serial.tools.list_ports, "comports", lambda: ports)
    captured = {}

    def _fake_connect(self, port, timeout=1):
        captured["port"] = port
        return True

    monkeypatch.setattr(nanoVNA, "connect", _fake_connect)
    dev = nanoVNA()
    found, connected = dev.autoconnect()
    assert (found, connected) == (True, True)
    assert captured["port"] == "COM3"           # picked the matching port


def test_autoconnect_no_match_returns_false_false(monkeypatch):
    import nvnapython.core as core
    ports = [
        _PortInfo("COM1", None, None),
        _PortInfo("COM2", 0x1234, 0x5678),
    ]
    monkeypatch.setattr(core.serial.tools.list_ports, "comports", lambda: ports)
    dev = nanoVNA()
    assert dev.autoconnect() == (False, False)


# ---------------------------------------------------------------------------
# Library-side override setters / getters (DEBUG bounds; do not touch device)
# ---------------------------------------------------------------------------

def test_freq_overrides_roundtrip():
    dev = nanoVNA()
    dev.set_min_device_freq(20_000)
    dev.set_max_device_freq(6e9)
    assert dev.get_min_device_freq() == 20_000.0
    assert dev.get_max_device_freq() == 6e9


def test_max_points_override_affects_scan_bound():
    # Lowering maxPoints must immediately tighten the scan() validation, since
    # scan reads self.maxPoints. This is the live link between an override and
    # the command guard.
    dev = nanoVNA()
    dev.nanoVNA_serial = lambda *a, **k: bytearray(b"")  # stub the wire
    dev.set_max_points(50)
    assert dev.get_max_points() == 50
    sent = {"n": 0}
    orig = dev.nanoVNA_serial

    def _count(*a, **k):
        sent["n"] += 1
        return bytearray(b"")
    dev.nanoVNA_serial = _count
    dev.scan(1_000_000, 2_000_000, 51, 2)   # 51 > new max 50 -> rejected
    assert sent["n"] == 0


def test_serial_tuning_overrides_roundtrip():
    dev = nanoVNA()
    dev.set_serial_timeout(2.5)
    dev.set_serial_poll_interval(0.2)
    assert dev.get_serial_timeout() == 2.5
    assert dev.get_serial_poll_interval() == 0.2


def test_screen_size_override_roundtrip():
    dev = nanoVNA()
    dev.set_screen_size(480, 320)
    assert dev.get_screen_size() == (480, 320)


def test_verbose_getter_roundtrip():
    dev = nanoVNA()
    dev.set_verbose(True)
    assert dev.get_verbose() is True
    dev.set_verbose(False)
    assert dev.get_verbose() is False


def test_error_byte_getter_roundtrip():
    dev = nanoVNA()
    dev.set_error_byte_return(True)
    assert dev.get_error_byte_return() is True


def test_print_message_respects_verbose(capsys):
    dev = nanoVNA()
    dev.set_verbose(False)
    dev.print_message("hidden")
    assert capsys.readouterr().out == ""
    dev.set_verbose(True)
    dev.print_message("shown")
    assert "shown" in capsys.readouterr().out


def test_load_custom_config_is_noop():
    # Documented TODO stub: must exist and not raise.
    dev = nanoVNA()
    assert dev.load_custom_config("anything.cfg") is None
