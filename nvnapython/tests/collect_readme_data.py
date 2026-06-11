#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/collect_readme_data.py'
#
#   ONE-PASS README DATA COLLECTOR (run with a NanoVNA connected).
#
#   This is NOT a pytest test -- it's a manual data-gathering utility, like the
#   tsapython collect_samples.py. It exercises the device with safe, read-only /
#   non-destructive commands and captures the REAL return bytes plus the device's
#   own 'help' usage strings, then writes a paste-ready markdown file organized to
#   match the README's per-command reference format (Description / Original Usage /
#   Example Return / Notes).
#
#   The point: replace the README's guessed/older example returns with verbatim
#   captures from real hardware, and fill in the device's authoritative usage
#   strings -- all in a single device session so you don't re-run on the bench.
#
#   SAFETY: only read-only / non-destructive commands are sent. It does NOT call
#   save, saveconfig, clearconfig, reset, cal (write steps), lcd, pwm, beep, or
#   anything that changes device state or writes storage. recall is read-only-ish
#   (loads a stored preset) and is intentionally SKIPPED to avoid changing the
#   active state; the help usage string for it is captured instead.
#
#   USAGE:
#       python tests/collect_readme_data.py
#       python tests/collect_readme_data.py --out readme_capture.md
#
#   Then open the generated markdown and copy the per-command blocks into the
#   README's reference section as desired.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import sys
import os
import argparse
import datetime

# make 'src' importable when run from the repo's nvnapython/ dir or tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from nvnapython import nanoVNA  # noqa: E402


# Safe, read-only / non-destructive captures.
# (label, command string to send verbatim, note)
# We send via command() passthrough so we capture EXACTLY what the device emits,
# including any framing, with no library-side filtering.
SAFE_CAPTURES = [
    ("info",          "info",                         "device SW/HW info"),
    ("version",       "version",                      "firmware version string"),
    ("SN",            "SN",                            "unique serial number"),
    ("resolution",    "resolution",                   "LCD resolution"),
    ("LCD_ID",        "LCD_ID",                        "LCD controller id"),
    ("help",          "help",                          "full command list + usage"),
    ("cal_status",    "cal",                           "calibration status (no arg)"),
    ("edelay_get",    "edelay",                        "current electrical delay"),
    ("cwfreq_status", "cwfreq",                        "cwfreq with no arg"),
    ("sweep_status",  "sweep",                         "current sweep settings (no arg)"),
    ("marker_status", "marker",                        "active marker info (no arg)"),
    ("trace_status",  "trace",                         "active trace attributes (no arg)"),
    # data tables: S11/S21 + cal tables (read-only)
    ("data_0_s11",    "data 0",                        "S11"),
    ("data_1_s21",    "data 1",                        "S21"),
    ("data_2_load",   "data 2",                        "cal load"),
    ("data_3_open",   "data 3",                        "cal open"),
    ("data_4_short",  "data 4",                        "cal short"),
    ("data_5_thru",   "data 5",                        "cal thru"),
    ("data_6_isoln",  "data 6",                        "cal isolation"),
    # a small scan + the frequencies it used (read-only, then resume)
    ("scan_freqs",    "scan 1000000 2000000 11 1",     "scan outmask 1 -> frequencies"),
    ("scan_s11",      "scan 1000000 2000000 11 2",     "scan outmask 2 -> S11 pairs"),
    ("scan_s11_s21",  "scan 1000000 2000000 11 6",     "scan outmask 6 -> S11+S21"),
    ("scan_all",      "scan 1000000 2000000 11 7",     "scan outmask 7 -> freq+S11+S21"),
    ("frequencies",   "frequencies",                   "freqs from last sweep"),
    # the documented edge case: too many points
    ("scan_overmax",  "scan 1000000 2000000 999 2",    "over-max points (error string)"),
]


def trunc(b, n=400):
    """Truncate long captures for readability, keeping head and tail."""
    if b is None:
        return "None"
    raw = bytes(b)
    if len(raw) <= n:
        return repr(raw)
    head = repr(raw[: n // 2])
    tail = repr(raw[-n // 2:])
    return f"{head[:-1]} ... {tail[1:]}  (total {len(raw)} bytes)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None,
                    help="serial port (e.g. COM6 or /dev/ttyACM0). Omitted = autoconnect.")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(__file__), "readme_capture.md"))
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(True)
    nvna.set_error_byte_return(True)

    # connect ---------------------------------------------------------------
    if args.port:
        ok = nvna.connect(args.port)
    else:
        _found, ok = nvna.autoconnect()
    if not ok:
        print("ERROR: could not open the serial port. Pass --port explicitly, "
              "close other programs using the port, or replug the device.")
        sys.exit(1)

    print(f"Connected. Capturing {len(SAFE_CAPTURES)} commands...\n")

    # pause so scans are stable, capture, then resume at the end
    nvna.pause()

    records = []
    for i, (label, cmd, note) in enumerate(SAFE_CAPTURES, start=1):
        print(f"[{i}/{len(SAFE_CAPTURES)}] {label}: {cmd!r}")
        try:
            raw = nvna.command(cmd)
        except Exception as e:  # noqa: BLE001
            raw = None
            print(f"   capture error: {e!r}")
        records.append((label, cmd, note, raw))

    nvna.resume()
    nvna.disconnect()

    # write markdown --------------------------------------------------------
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    model = nvna.get_device_model()
    lines = []
    lines.append(f"# NanoVNA README capture\n\n")
    lines.append(f"Generated: {ts}  \n")
    lines.append(f"Library model preset: `{model}`  \n")
    lines.append("Captured verbatim via `command()` passthrough (raw device "
                 "bytes, no library filtering). Paste the Example Return blocks "
                 "into the README's per-command reference as desired.\n\n")
    lines.append("---\n\n")

    for label, cmd, note, raw in records:
        lines.append(f"## `{cmd}`  ({note})\n\n")
        lines.append(f"* **sent:** `{cmd}`\n")
        lines.append(f"* **raw return:**\n\n")
        lines.append(f"  ```\n  {trunc(raw)}\n  ```\n\n")

    # pull the help usage table out into its own clearly labeled block, since
    # it is the authoritative per-command 'Original Usage' source for the README.
    help_rec = next((r for r in records if r[0] == "help"), None)
    if help_rec and help_rec[3]:
        lines.append("---\n\n")
        lines.append("## Authoritative `help` usage strings (for 'Original Usage' fields)\n\n")
        lines.append("```\n")
        try:
            lines.append(bytes(help_rec[3]).decode("utf-8", errors="replace"))
        except Exception:
            lines.append(repr(help_rec[3]))
        lines.append("\n```\n")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"\nWrote {args.out}")
    print("Open it and copy the capture blocks into the README reference section.")


if __name__ == "__main__":
    main()
