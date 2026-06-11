#! /usr/bin/python3
"""
No-hardware verification of the boundary-probe SAFETY logic and the model
envelope's internal consistency.

The hardware boundary probes (test_hardware_boundaries.py) can WRITE to a preset
slot (the B5 save round-trip). That write is only safe because the probe never
saves a slot it didn't first successfully recall. This file proves that decision
rule with a scripted fake port -- so the safety property is regression-locked
WITHOUT needing the bench.

It also pins consistency invariants on constants.MODELS so a future edit (adding
a model, bumping a firmware envelope) can't silently produce a malformed entry.
"""

import pytest

from nvnapython import nanoVNA
from nvnapython.constants import MODELS, DEFAULT_MODEL, DATA_VALUES, SCAN_OUTMASK_VALUES


# ---------------------------------------------------------------------------
# A scripted serial port that mimics recall/save/sweep framing and tracks which
# slots actually received a 'save'. Lets us replay the B5 decision rule offline.
# ---------------------------------------------------------------------------

class ScriptedSlotPort:
    def __init__(self, recallable_slots):
        self.recallable = set(recallable_slots) | {0}   # slot 0 always loadable
        self.saved = []            # slots a 'save' was written to (the audit)
        self._buf = b""
        self.written = []

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass

    def write(self, data):
        cmd = data.decode().strip()
        self.written.append(cmd)
        if cmd.startswith("save "):
            slot = int(cmd.split()[1])
            self.saved.append(slot)
            body = b""             # device accepts the save
        elif cmd.startswith("recall "):
            slot = int(cmd.split()[1])
            body = b"" if slot in self.recallable else b"error: empty slot"
        elif cmd == "sweep":
            body = b"50000 3000000000 101"
        else:
            body = b""
        self._buf = cmd.encode() + b"\r\n" + body + b"\r\nch> \r\nch> "
        return len(data)

    @property
    def in_waiting(self):
        return len(self._buf)

    def read(self, n):
        chunk, self._buf = self._buf[:n], self._buf[n:]
        return chunk

    def close(self):
        pass


def _is_error(b):
    s = bytes(b).decode(errors="replace").lower()
    return ("error" in s) or ("usage" in s) or (b == bytearray(b"ERROR"))


def _run_b5_rule(dev, slots):
    """The EXACT decision rule the B5 probe uses: only save a slot whose recall
    succeeded; skip otherwise."""
    for slot in slots:
        rec = dev.command(f"recall {slot}")
        if _is_error(rec):
            continue                       # SKIP -- never write an unknown slot
        dev.command(f"save {slot}")        # safe: rewrites what we just loaded


def test_b5_never_saves_unrecallable_slot():
    # slots 0..4 recallable; 5,6 error on recall -> must never be saved.
    dev = nanoVNA()
    dev.set_error_byte_return(True)
    dev.ser = ScriptedSlotPort(recallable_slots=[1, 2, 3, 4])
    _run_b5_rule(dev, range(0, 7))
    assert dev.ser.saved == [0, 1, 2, 3, 4]
    assert 5 not in dev.ser.saved and 6 not in dev.ser.saved


def test_b5_saves_nothing_when_all_recalls_fail():
    # if every slot errors on recall (e.g. a fresh device), nothing is written.
    dev = nanoVNA()
    dev.set_error_byte_return(True)
    port = ScriptedSlotPort(recallable_slots=[])   # only slot 0 loadable
    dev.ser = port
    _run_b5_rule(dev, range(1, 7))                 # deliberately skip slot 0
    assert port.saved == []                        # zero writes


def test_b5_every_save_was_preceded_by_its_recall():
    # stronger invariant: for each save, a recall of the SAME slot came first.
    dev = nanoVNA()
    dev.set_error_byte_return(True)
    port = ScriptedSlotPort(recallable_slots=[1, 2, 3, 4])
    dev.ser = port
    _run_b5_rule(dev, range(0, 7))
    # walk the written log; every 'save N' must have a 'recall N' before it
    seen_recall = set()
    for cmd in port.written:
        if cmd.startswith("recall "):
            seen_recall.add(cmd.split()[1])
        elif cmd.startswith("save "):
            slot = cmd.split()[1]
            assert slot in seen_recall, f"save {slot} had no preceding recall"


# ---------------------------------------------------------------------------
# constants.MODELS internal-consistency invariants.
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "min_freq_hz", "max_freq_hz", "max_points", "point_end_inclusive",
    "screen_width", "screen_height", "num_markers", "num_traces",
    "num_cal_slots", "num_preset_slots",
}


def test_default_model_exists():
    assert DEFAULT_MODEL in MODELS


@pytest.mark.parametrize("name", list(MODELS.keys()))
def test_model_has_all_required_keys(name):
    # every model must carry the full key set so core._apply_model can consume
    # any entry uniformly (a missing key would KeyError at runtime).
    missing = REQUIRED_KEYS - set(MODELS[name].keys())
    extra = set(MODELS[name].keys()) - REQUIRED_KEYS
    assert not missing, f"{name} missing keys: {missing}"
    assert not extra, f"{name} has unexpected keys: {extra}"


@pytest.mark.parametrize("name", list(MODELS.keys()))
def test_model_values_are_sane(name):
    m = MODELS[name]
    assert m["min_freq_hz"] < m["max_freq_hz"], f"{name}: min freq >= max freq"
    assert m["max_points"] > 0
    assert isinstance(m["point_end_inclusive"], bool)
    assert m["screen_width"] > 0 and m["screen_height"] > 0
    for k in ("num_markers", "num_traces", "num_cal_slots", "num_preset_slots"):
        assert m[k] > 0, f"{name}: {k} must be positive"


def test_outmask_and_data_value_sets_are_contiguous():
    # sanity on the shared validation tuples
    assert SCAN_OUTMASK_VALUES == tuple(range(0, 8))
    assert DATA_VALUES == tuple(range(0, 7))


# ---------------------------------------------------------------------------
# Cross-check: does the LIBRARY's current hardcoded save/recall range match
# the envelope's slot counts? This test DOCUMENTS the current mismatch so the
# eventual "read from envelope" refactor flips it deliberately.
# ---------------------------------------------------------------------------

def test_documents_save_range_vs_envelope_mismatch():
    # F V2 envelope says 7 preset slots, but save() hardcodes 0..4 (5 slots).
    # This intentional mismatch is the thing the refactor will resolve.
    dev = nanoVNA()                                   # default F V2
    envelope_presets = MODELS[DEFAULT_MODEL]["num_preset_slots"]
    assert envelope_presets == 7

    dev.set_error_byte_return(True)
    calls = []
    dev.nanoVNA_serial = lambda *a, **k: calls.append(a[0]) or bytearray(b"")
    # the highest slot save() currently accepts:
    dev.save(4)
    assert calls == ["save 4\r\n"]
    calls.clear()
    dev.save(5)                                       # within envelope, rejected now
    assert calls == [], ("save(5) unexpectedly accepted -- if you've wired save() "
                         "to the envelope, update this test to reflect the new range")
