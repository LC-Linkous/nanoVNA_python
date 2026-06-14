#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/save_raw_to_csv.py'
#   Scan S11 and save the RAW data (frequency, real, imaginary) to CSV -- no
#   derived magnitude/phase, just the measured complex samples. Requires numpy.
#       python examples/save_raw_to_csv.py
#       python examples/save_raw_to_csv.py --start 1e9 --stop 3e9 --points 200
#
##-------------------------------------------------------------------------------\

import sys
import os
import csv
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def convert_s11_data_to_arrays(start, stop, pts, data):
    # Parse raw S11 bytes into frequency/real/imaginary arrays. Genuine zero
    # samples are KEPT (dropping a deep null misaligns the frequency axis).
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
    actual = len(real_arr)
    freq_arr = np.linspace(start, stop, actual if actual else 1)
    return freq_arr, real_arr, imag_arr


def main():
    ap = argparse.ArgumentParser(description="Save RAW NanoVNA S11 scan to CSV.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=3e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=200, help="points (<=201 on F V2)")
    ap.add_argument("--out", default="s11_raw_data.csv", help="output CSV path")
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
        print("Connected to NanoVNA - collecting S11 data...")
        nvna.pause()
        data_bytes = nvna.get_scan_s11(start, stop, pts)   # outmask 2
        nvna.resume()
        print(f"Received {len(data_bytes)} bytes of S11 data")
    finally:
        nvna.disconnect()

    if not data_bytes or bytes(data_bytes).strip() in (b"", b"ERROR"):
        print(f"no scan data returned (got {bytes(data_bytes)!r}). Check the range "
              "and that points <= the model max.")
        return 1

    freq_arr, real_arr, imag_arr = convert_s11_data_to_arrays(start, stop, pts, data_bytes)

    if len(real_arr) == 0:
        print("scan returned no parseable pairs; nothing to save.")
        return 1

    with open(args.out, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Frequency_Hz", "S11_Real", "S11_Imaginary"])
        for freq, real, imag in zip(freq_arr, real_arr, imag_arr):
            writer.writerow([f"{freq:.0f}", f"{real:.6f}", f"{imag:.6f}"])

    print(f"RAW S11 data saved to {args.out}")
    print(f"Total: {len(freq_arr)} data points saved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
