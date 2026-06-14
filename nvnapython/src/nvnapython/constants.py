#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/constants.py'
#
#   Single source of truth for the NanoVNA operating envelopes used by the
#   library's error checking: per-model frequency ranges, sweep-point limits,
#   screen dimensions, and the counts for markers / traces / cal+preset slots.
#
#   EVERYTHING that is a per-model "limit" lives here so that:
#       1. there is exactly one place to edit as hardware / firmware / new models
#          appear (contributors can add a model without touching library logic),
#       2. the validation code (core.py, the command mixins) and the test suite
#          import the SAME numbers and therefore cannot silently drift apart.
#
#   WARNING: these describe the LIBRARY's checking envelope, not live device
#   state. Editing them changes what the library will accept / reject; it does
#   NOT change anything on the device.
#
#   A NOTE ON CLONES: there are many devices sold as "NanoVNA". Even within one
#   name (e.g. "F V2") vendors report different sweep-point counts and cal-slot
#   counts. The entries below use values from official / first-party docs
#   (Chelegance user guides, Hugen listings). If your unit differs, add a new
#   MODELS entry or override the bounds at runtime via the nanoVNA.set_* methods
#   (set_max_points, set_min_device_freq, etc.).
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\


# ---- library-wide defaults (NOT model specific) ----------------------------
# Serial read tuning. serialTimeout bounds *idle* time waiting for the 'ch>'
# prompt (the timer resets on each chunk received), so a long transfer will not
# time out but a missing prompt / disconnect cannot hang forever.
SERIAL_TIMEOUT_S = 5.0
SERIAL_POLL_INTERVAL_S = 0.01

# scan() outmask: bitwise OR of 1=frequency, 2=S11, 4=S21 -> valid 0..7
SCAN_OUTMASK_VALUES = (0, 1, 2, 3, 4, 5, 6, 7)

# data {n}: 0=S11, 1=S21, 2..6 = the SOLT/isolation cal tables
DATA_VALUES = (0, 1, 2, 3, 4, 5, 6)

# cal sub-commands accepted by the device console
CAL_ACTIONS = ("load", "open", "short", "thru", "done", "reset", "on", "off", "in")

# trace display formats accepted by the device console
TRACE_FORMATS = ("off", "logmag", "linear", "phase", "smith",
                 "swr", "polar", "delay", "refpos", "channel")

# marker actions
MARKER_ACTIONS = ("on", "off", "peak")


# ---- per-model operating envelopes -----------------------------------------
# Each model dict carries ONLY the values the library validates against. Keep
# the keys identical across models so core.py can consume any entry uniformly.
#
#   min_freq_hz / max_freq_hz : accepted sweep/measurement frequency bounds
#   max_points                : sweep-point ceiling (see point_end_inclusive)
#   point_end_inclusive       : True  -> max_points itself is a valid count
#                               False -> max_points is the exclusive upper end
#                                        (the device reports e.g. "range 11-201"
#                                        with the top end not selectable)
#   screen_width / screen_height : LCD pixel dimensions (for touch/lcd bounds)
#   num_markers / num_traces  : how many markers / traces the UI exposes
#   num_cal_slots             : calibration storage groups (recall range)
#   num_preset_slots          : save/recall preset count
#
# Sources:
#   NanoVNA-F V2 : Chelegance "Nano VNA-F V2 User Guide Rev 2.0" (50kHz-3GHz,
#                  sweep points 201 / 11-201 configurable, 4 traces, 4 markers,
#                  calibration storage 7, 800x480 IPS).
#   NanoVNA-F V3 : Chelegance NanoVNA-F V3 docs + on-hardware confirmation
#                  (50kHz floor per docs; 6 GHz hardware ceiling -- the firmware
#                  'info' banner says 6.3 GHz but returns all-zero samples above
#                  ~6 GHz; sweep points 51-801 confirmed via the scan command,
#                  menu range 101-801; 800x480, 4 traces, 4 markers, 7 cal slots).
#   NanoVNA-H4   : Hugen / GigaParts / R&L listings (10kHz-1.5GHz firmware floor,
#                  101 fixed scan points, 320x480 3.95" TFT, 4 traces, 4 markers,
#                  5 setting saves).
#   GENERIC      : conservative fallback for unknown clones -- widest commonly
#                  safe bounds; prefer adding a real model entry over relying on
#                  this.

MODELS = {
    "NANOVNA_F_V2": {
        "min_freq_hz": 50e3,        # 50 kHz
        "max_freq_hz": 3e9,         # 3 GHz
        "max_points": 201,          # 11-201 configurable per the user guide
        "point_end_inclusive": True,
        "screen_width": 800,
        "screen_height": 480,
        "num_markers": 4,
        "num_traces": 4,
        "num_cal_slots": 7,
        "num_preset_slots": 7,
    },
    "NANOVNA_F_V3": {
        "min_freq_hz": 50e3,        # 50 kHz (per the docs; the device is
                                    #         permissive below this, so a 50 kHz
                                    #         floor never wrongly rejects a
                                    #         documented-range scan)
        "max_freq_hz": 6e9,         # 6 GHz HARDWARE ceiling. The firmware 'info'
                                    #       banner reports 6.3 GHz, but the device
                                    #       returns all-zero samples above ~6 GHz
                                    #       (confirmed on hardware + Chelegance
                                    #       docs); 6 GHz is the real measurable max.
        "max_points": 801,          # 51..801 confirmed on hardware via scan
                                    #        (menu range is 101-801; the scan
                                    #        command accepts down to 51)
        "point_end_inclusive": True,
        "screen_width": 800,
        "screen_height": 480,
        "num_markers": 4,
        "num_traces": 4,
        "num_cal_slots": 7,
        "num_preset_slots": 7,
    },
    "NANOVNA_H4": {
        "min_freq_hz": 10e3,        # 10 kHz (firmware-permissive floor)
        "max_freq_hz": 1.5e9,       # 1.5 GHz
        "max_points": 101,          # fixed 101 on the H4
        "point_end_inclusive": True,
        "screen_width": 320,
        "screen_height": 480,
        "num_markers": 4,
        "num_traces": 4,
        "num_cal_slots": 5,
        "num_preset_slots": 5,
    },
    "NANOVNA_GENERIC": {
        "min_freq_hz": 10e3,        # 10 kHz
        "max_freq_hz": 1.5e9,       # 1.5 GHz (conservative; many base units)
        "max_points": 101,          # conservative; the classic NanoVNA limit
        "point_end_inclusive": True,
        "screen_width": 320,
        "screen_height": 240,
        "num_markers": 4,
        "num_traces": 4,
        "num_cal_slots": 5,
        "num_preset_slots": 5,
    },
}

# The model used when none is explicitly selected. The library ships seeded for
# the NanoVNA-F V2 (the model this package was developed and tested against).
DEFAULT_MODEL = "NANOVNA_F_V2"