#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/test_hardware_boundaries.py'
#
#   BOUNDARY DISCOVERY PROBES -- settle the stale range claims.
#
#   The library was first written ~a year before official docs existed, so
#   several bounds are educated guesses that a firmware update may have changed.
#   These probes ask the DEVICE directly and PRINT verbatim answers so the
#   constants + validators can be set from ground truth instead of guesses.
#
#   What this settles (each prints a [REPORT] line + a [CONCLUSION]):
#     B1. scan point range: exact min and max the device accepts, and whether
#         the top is inclusive (does 201 return 201 pairs, 202 error?).
#     B2. marker index bound: does the device key the index on the CURRENT
#         sweep point count or on a fixed model max? (Set two different sweep
#         sizes and see where marker index starts erroring.)
#     B3. data {n} indices: which of 0..6 (and is 7+?) return data vs error.
#     B4. recall slot range: highest accepted id (read-only; restores slot 0).
#     B5. save slot range: SAFE round-trip -- recall a slot to capture its
#         active fingerprint, save active back to the SAME slot (identical
#         data, no content change), confirm the id is accepted. Never writes a
#         slot that wasn't first recalled successfully. Uses the library's
#         fire-and-forget save() so it does not hang on firmware that emits no
#         prompt after a flash write (F V3 0.5.8 vs F V2 0.3.0, which prompts).
#     B6. cal actions: is 'in' accepted on this firmware? (help omits it.)
#     B7. cwfreq units: set a value, read back the active point, infer Hz vs kHz.
#
#   Run with output visible:
#       pytest -m hardware tests/test_hardware_boundaries.py -s -v
#
#   SAFETY: B5 is the only path that issues 'save'. It ONLY saves a slot whose
#   prior contents it just loaded via recall, so the write is byte-identical to
#   what was already there. If a recall fails/empties, that slot is SKIPPED, not
#   written. No clearconfig/reset is ever sent.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import pytest

pytestmark = pytest.mark.hardware


def _decode(b):
    if not b:
        return ""
    try:
        return bytes(b).decode("utf-8", errors="replace").strip()
    except Exception:
        return repr(b)


def _is_error(b):
    s = _decode(b).lower()
    return (b == bytearray(b"ERROR")) or ("not recognised" in s) or \
           ("not recognized" in s) or ("error" in s) or ("usage" in s) or \
           ("exceeds" in s) or ("invalid" in s)


def _count_lines(b):
    return len([ln for ln in _decode(b).split("\n") if ln.strip()])


# ===========================================================================
# B1. scan point range -- exact accepted min/max and inclusivity.
# ===========================================================================

@pytest.mark.parametrize("pts", [2, 5, 10, 11, 12, 50, 101, 200, 201, 202, 256, 401])
def test_b1_scan_point_acceptance(device, pts):
    device.pause()
    raw = device.command(f"scan 1000000 2000000 {pts} 2")
    err = _is_error(raw)
    n = _count_lines(raw)
    print(f"\n  [REPORT] B1 scan pts={pts}: error={err}, lines_returned={n}, "
          f"sample={_decode(raw)[:50]!r}")
    device.resume()
    # informational: we want the full accept/reject + count map, not a pass/fail


def test_b1_conclusion(device):
    print("\n  [CONCLUSION] B1: read the accept/reject map above. The lowest pts "
          "with error=False is the MIN; the highest is the MAX; if max pts "
          "returns exactly max pairs and max+1 errors, the top is INCLUSIVE. "
          "Set constants.MODELS[...]['max_points'] and ['point_end_inclusive'] "
          "to match, and update min if it's not the assumed 11.")


# ===========================================================================
# B2. marker index bound -- keyed on CURRENT sweep points or model max?
#     Set a SMALL sweep (e.g. 11 pts) and a LARGER one (e.g. 101 pts); probe
#     where marker index starts erroring in each. If the error boundary MOVES
#     with the sweep size, the device keys on current points (so the library
#     should bound on the live sweep, not maxPoints).
# ===========================================================================

@pytest.mark.parametrize("sweep_pts,probe_idx", [
    (11, [0, 10, 11, 20]),
    (101, [0, 100, 101, 200]),
])
def test_b2_marker_index_vs_sweep_size(device, sweep_pts, probe_idx):
    device.pause()
    # set a sweep of known size
    device.command(f"scan 1000000 2000000 {sweep_pts} 2")
    print(f"\n  [REPORT] B2 sweep set to {sweep_pts} points")
    for idx in probe_idx:
        raw = device.command(f"marker 1 {idx}")
        # read back where the marker actually landed
        pos = _decode(device.command("marker 1"))
        print(f"           marker 1 {idx}: error={_is_error(raw)}, "
              f"readback={pos[:40]!r}")
    device.resume()


def test_b2_conclusion(device):
    print("\n  [CONCLUSION] B2: if the highest non-error index tracks the sweep "
          "size (10 for an 11-pt sweep, 100 for 101), the device keys marker "
          "index on the CURRENT sweep point count -> marker() should bound on "
          "the live sweep length, NOT self.maxPoints. If it's fixed regardless "
          "of sweep size, keep a model-max bound.")


# ===========================================================================
# B3. data {n} indices -- which return data, which error, and is 7+ rejected.
# ===========================================================================

@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5, 6, 7, 8])
def test_b3_data_indices(device, n):
    device.pause()
    raw = device.command(f"data {n}")
    print(f"\n  [REPORT] B3 data {n}: error={_is_error(raw)}, "
          f"lines={_count_lines(raw)}, first={_decode(raw)[:40]!r}")
    device.resume()


def test_b3_conclusion(device):
    print("\n  [CONCLUSION] B3: the contiguous run starting at 0 with error=False "
          "is the valid data() range. If 7+ errors, the library's [0-6] is "
          "correct; if 7 works, extend DATA_VALUES and data()'s accepted list.")


# ===========================================================================
# B4. recall slot range -- highest accepted id (read-only; restore slot 0).
# ===========================================================================

@pytest.mark.parametrize("slot", [0, 1, 2, 3, 4, 5, 6, 7, 8])
def test_b4_recall_slots(device, slot):
    raw = device.command(f"recall {slot}")
    print(f"\n  [REPORT] B4 recall {slot}: error={_is_error(raw)}, "
          f"resp={_decode(raw)[:60]!r}")
    device.command("recall 0")   # restore startup preset after each probe


def test_b4_conclusion(device):
    print("\n  [CONCLUSION] B4: highest slot with error=False is the recall max. "
          "Compare to constants num_cal_slots/num_preset_slots and to recall()'s "
          "hardcoded 0..6.")


# ===========================================================================
# B5. save slot range -- SAFE round-trip restore.
#     For each candidate slot: recall it (load its stored state into active).
#     If that succeeds, immediately save the SAME slot -> writes back the exact
#     state we just loaded (no net change), proving the id is writable. If the
#     recall failed, SKIP the save for that slot (never write an unknown slot).
# ===========================================================================

@pytest.mark.parametrize("slot", [0, 1, 2, 3, 4, 5, 6])
def test_b5_save_slots_safe_roundtrip(device, slot):
    # 1) load the slot's current contents into active state
    rec = device.command(f"recall {slot}")
    rec_ok = not _is_error(rec)
    if not rec_ok:
        print(f"\n  [REPORT] B5 slot {slot}: recall ERRORED "
              f"({_decode(rec)[:40]!r}) -> SKIP save (won't write unknown slot)")
        device.command("recall 0")
        return

    # capture an active-state fingerprint BEFORE the save
    before = _decode(device.command("sweep"))

    # 2) save active state back to the SAME slot -> byte-identical rewrite.
    #
    # FIRMWARE NOTE: we go through device.save() -- the library's fire-and-forget
    # path -- NOT a raw command("save N"). 'save' writes to flash, and the two
    # firmwares behave differently afterward:
    #   * NanoVNA-F V2 (0.3.0): emits the 'ch> ' prompt normally (~0.56s).
    #   * NanoVNA-F V3 (0.5.8): emits NO prompt at all (echo only), so a
    #     prompt-waiting read (raw command) hangs for the full serial timeout and
    #     the NEXT command collides with the still-busy device and blocks the
    #     port. This is what made this probe hang on the V3 while passing on V2.
    # device.save() does not wait for a prompt, so it is safe on both. We also
    # settle briefly before the follow-up recall so the V3's post-flash-write
    # window can clear before we talk to the device again.
    import time
    save_resp = device.save(slot)
    sav_ok = not _is_error(save_resp)
    time.sleep(0.8)   # let a slow/no-prompt flash write settle before next read

    # 3) re-load and re-fingerprint to confirm nothing changed
    device.command(f"recall {slot}")
    after = _decode(device.command("sweep"))

    print(f"\n  [REPORT] B5 slot {slot}: recall_ok={rec_ok}, save_ok={sav_ok}, "
          f"fingerprint_unchanged={before == after}")
    print(f"           before={before!r} after={after!r}")

    device.command("recall 0")   # leave device on startup preset


def test_b5_conclusion(device):
    print("\n  [CONCLUSION] B5: slots with save_ok=True are valid save targets. "
          "The highest is the save max. If it exceeds the library's hardcoded "
          "0..4, widen save(); reconcile against num_preset_slots. "
          "fingerprint_unchanged=True confirms the probe was non-destructive. "
          "NOTE: on firmware that does not prompt after a flash write (e.g. F V3 "
          "0.5.8), save() returns empty rather than an ack, so save_ok just means "
          "'sent without an error reply' -- fingerprint_unchanged is the real "
          "confirmation the write round-tripped.")


# ===========================================================================
# B6. cal 'in' -- accepted on this firmware? (help omits it.)
# ===========================================================================

def test_b6_cal_in(device):
    raw = device.command("cal in")
    err = _is_error(raw)
    print(f"\n  [REPORT] B6 'cal in': error={err}, resp={_decode(raw)[:60]!r}")
    print(f"  [CONCLUSION] B6: cal 'in' is "
          f"{'NOT accepted -> drop from CAL_ACTIONS' if err else 'accepted -> keep, mark unlisted'}")
    # leave cal state alone; do not send done/reset


# ===========================================================================
# B7. cwfreq units -- set a value, read back the active point, infer Hz vs kHz.
# ===========================================================================

def test_b7_cwfreq_units(device):
    before = _decode(device.command("sweep"))
    print(f"\n  [REPORT] B7 sweep before: {before!r}")

    device.command("cwfreq 100000")
    usage = _decode(device.command("cwfreq"))          # bare -> usage w/ unit label
    mk = _decode(device.command("marker"))             # active point freq
    sweep_after = _decode(device.command("sweep"))
    print(f"  [REPORT] B7 cwfreq usage label: {usage!r}")
    print(f"  [REPORT] B7 marker after cwfreq 100000: {mk!r}")
    print(f"  [REPORT] B7 sweep after: {sweep_after!r}")
    print("  [CONCLUSION] B7: if the active/marker freq ~= 100000, the unit is "
          "Hz; if ~= 100000000 (100 MHz), the unit is kHz. Document the TRUE "
          "unit in cwfreq() and stop passing through unconverted.")

    # restore prior sweep if parseable
    parts = before.split()
    if len(parts) >= 3 and all(p.lstrip("-").isdigit() for p in parts[:3]):
        device.command(f"sweep {parts[0]} {parts[1]} {parts[2]}")