#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/save_scan_csv.py'
#   Scan S11 and save a CSV with frequency, real, imaginary, magnitude (dB), and
#   phase (deg) per point. Requires numpy.
#       python examples/save_scan_csv.py
#       python examples/save_scan_csv.py --start 1e9 --stop 3e9 --points 200
#
##-------------------------------------------------------------------------------\

import sys
import os
import csv
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def convert_s11_data_to_arrays(start, stop, pts, data):
    # Parse raw S11 bytes (whitespace-separated real/imag pairs, one per line,
    # possibly trailing-spaced) into freq/real/imag arrays plus derived
    # magnitude(dB) and phase(deg). Genuine zero samples are KEPT -- dropping a
    # deep null would shift every later point onto the wrong frequency.
    import numpy as np

    text = bytes(data).decode("utf-8", errors="replace") if data else ""
    real_parts, imag_parts = [], []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        vals = line.split()
        if len(vals) < 2:
            continue
        try:
            real_parts.append(float(vals[0]))
            imag_parts.append(float(vals[1]))
        except ValueError:
            continue

    real_arr = np.array(real_parts)
    imag_arr = np.array(imag_parts)
    mag = np.hypot(real_arr, imag_arr)
    with np.errstate(divide="ignore"):
        magnitude_db = 20.0 * np.log10(np.where(mag > 0, mag, 1e-12))
    magnitude_db = np.where(mag > 0, magnitude_db, -240.0)
    phase_deg = np.degrees(np.arctan2(imag_arr, real_arr))

    actual = len(real_arr)
    freq_arr = np.linspace(start, stop, actual if actual else 1)
    return freq_arr, real_arr, imag_arr, magnitude_db, phase_deg


def main():
    ap = argparse.ArgumentParser(description="Save NanoVNA S11 scan to CSV.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=3e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=200, help="points (<=201 on F V2)")
    ap.add_argument("--out", default="s11_scan_sample.csv", help="output CSV path")
    args = ap.parse_args()

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        print("numpy not installed: pip install numpy")
        return 1

    nvna = nanoVNA()
    nvna.set_verbose(True)
    nvna.set_error_byte_return(True)

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    try:
        start, stop, pts = int(args.start), int(args.stop), args.points
        nvna.pause()
        data_bytes = nvna.get_scan_s11(start, stop, pts)   # outmask 2
        nvna.resume()
    finally:
        nvna.disconnect()

    if not data_bytes or bytes(data_bytes).strip() in (b"", b"ERROR"):
        print(f"no scan data returned (got {bytes(data_bytes)!r}). Check the range "
              "and that points <= the model max.")
        return 1

    freq_arr, real_arr, imag_arr, magnitude_db, phase_deg = \
        convert_s11_data_to_arrays(start, stop, pts, data_bytes)

    if len(real_arr) == 0:
        print("scan returned no parseable pairs; nothing to save.")
        return 1

    with open(args.out, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Frequency_Hz", "S11_Real", "S11_Imaginary",
                         "S11_Magnitude_dB", "S11_Phase_deg"])
        for i in range(len(freq_arr)):
            writer.writerow([
                f"{freq_arr[i]:.0f}",
                f"{real_arr[i]:.6f}",
                f"{imag_arr[i]:.6f}",
                f"{magnitude_db[i]:.3f}",
                f"{phase_deg[i]:.2f}",
            ])

    print(f"S11 data saved to {args.out}")
    print(f"  {len(freq_arr)} points over "
          f"{freq_arr[0]/1e9:.3f} - {freq_arr[-1]/1e9:.3f} GHz")
    print(f"  |S11| range: {magnitude_db.min():.2f} to {magnitude_db.max():.2f} dB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
