#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_bounds.py'
#
#   OPTIONAL bounds helpers -- a staging ground for moving range checks off
#   hardcoded literals and onto the per-model envelope (constants.MODELS), once
#   the hardware boundary probes (tests/test_hardware_boundaries.py) confirm the
#   true ranges on the current firmware.
#
#   These are PURE functions: they take the relevant envelope value(s) and the
#   candidate, and return (ok, message). They do NOT talk to the device and do
#   NOT change any existing behavior on their own -- a mixin method has to call
#   them. They are written so the eventual switch from "hardcoded" to "envelope
#   sourced" is a small, well-tested edit rather than a scattered rewrite.
#
#   WHY THIS EXISTS (design intent):
#     * constants.MODELS already carries num_cal_slots / num_preset_slots /
#       num_markers / num_traces / max_points, but the command methods don't
#       read them yet -- they re-encode the numbers as literals, which has
#       already drifted (save() caps 0..4 while the F V2 envelope says 7).
#     * Until the probes settle the real numbers, flipping the methods to these
#       helpers would just relocate a guess. So this module is the prepared,
#       tested target; wire it in per-method after B2/B4/B5 confirm the data.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\


def check_slot(val, num_slots, name="slot"):
    """
    Validate a 0-based slot id against an envelope count.

    Accepts integer val in 0..num_slots-1. Returns (ok: bool, msg: str).
    Use for save()/recall() once num_preset_slots / num_cal_slots are confirmed.

    Example:
        ok, msg = check_slot(val, self.numPresetSlots, "save")
    """
    if not isinstance(val, int) or isinstance(val, bool):
        return False, f"{name} id must be an integer 0..{num_slots - 1}"
    if 0 <= val < num_slots:
        return True, ""
    return False, f"{name} id must be 0..{num_slots - 1}"


def check_point_count(pts, max_points, end_inclusive, min_points=1):
    """
    Validate a sweep/scan point count against the envelope.

    end_inclusive True  -> max_points itself is a valid count (pts <= max).
    end_inclusive False -> max_points is the exclusive top (pts < max).
    Returns (ok, msg). min_points lets a model set a real floor (e.g. 11 on the
    F V2) once B1 confirms it; defaults to 1 to preserve today's behavior.
    """
    try:
        n = int(pts)
    except (TypeError, ValueError):
        return False, "points must be an integer"
    if n < min_points:
        return False, f"points must be >= {min_points}"
    over = (n > max_points) if end_inclusive else (n >= max_points)
    if over:
        bound = ("<=" if end_inclusive else "<") + str(max_points)
        return False, f"points must be {bound} for this model"
    return True, ""


def check_marker_index(idx, sweep_points, source="sweep"):
    """
    Validate a marker point index.

    The OPEN QUESTION (B2 probe) is whether the device keys this on the CURRENT
    sweep point count or a fixed model max. This helper takes whichever value
    the caller decides is authoritative as `sweep_points`, so flipping the
    SOURCE (live sweep length vs self.maxPoints) is a one-line change at the
    call site, not a rewrite here. Index is 0-based: valid 0..sweep_points-1.

    `source` is only used in the message for clarity ("current sweep" vs
    "model max").
    """
    try:
        i = int(idx)
    except (TypeError, ValueError):
        return False, "marker index must be an integer"
    if 0 <= i < sweep_points:
        return True, ""
    return False, f"marker index must be 0..{sweep_points - 1} ({source})"


def check_in_set(val, allowed, name="value"):
    """
    Generic membership check against an envelope-or-constant set (e.g. data
    indices, outmask values, cal actions). Returns (ok, msg).
    """
    if val in allowed:
        return True, ""
    return False, f"{name} must be one of {sorted(allowed, key=str)}"
