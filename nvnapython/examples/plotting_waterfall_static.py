#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/plotting_waterfall_static.py'
#   Collect a series of S11 scans, then render a static waterfall (magnitude +
#   phase over scan number) and save the data to CSV. Requires the [plotting]
#   extra (numpy + matplotlib):
#       pip install -e ".[plotting]"
#       python examples/plotting_waterfall_static.py --scans 30 --interval 0.5
#
##-------------------------------------------------------------------------------\

import sys
import os
import csv
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def convert_s11_data_to_arrays(start, stop, pts, data):
    # Parse raw S11 bytes into freq/real/imag plus magnitude(dB)/phase(deg).
    # Genuine zero samples are KEPT -- the original example skipped them, which
    # silently misaligned the frequency axis vs the data on any deep null.
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


def collect_waterfall(nvna, start, stop, pts, num_scans, interval):
    import numpy as np
    import time

    w_real, w_imag, w_mag, w_phase, timestamps = [], [], [], [], []
    freq_arr = None
    print(f"Collecting {num_scans} S11 scans with {interval}s intervals...")
    for i in range(num_scans):
        print(f"  scan {i + 1}/{num_scans}")
        data_bytes = nvna.get_scan_s11(start, stop, pts)   # outmask 2
        f, real_arr, imag_arr, mag_arr, phase_arr = \
            convert_s11_data_to_arrays(start, stop, pts, data_bytes)
        if freq_arr is None:
            freq_arr = f
        w_real.append(real_arr)
        w_imag.append(imag_arr)
        w_mag.append(mag_arr)
        w_phase.append(phase_arr)
        timestamps.append(datetime.now())
        if i < num_scans - 1:
            time.sleep(interval)

    return (freq_arr, np.array(w_real), np.array(w_imag),
            np.array(w_mag), np.array(w_phase), timestamps)


def plot_waterfall(freq_arr, w_mag, w_phase, start, stop):
    import numpy as np
    import matplotlib.pyplot as plt

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    time_arr = np.arange(w_mag.shape[0])
    freq_mesh, time_mesh = np.meshgrid(freq_arr, time_arr)

    im1 = ax1.pcolormesh(freq_mesh / 1e9, time_mesh, w_mag,
                         shading="nearest", cmap="viridis")
    ax1.set_xlabel("Frequency (GHz)"); ax1.set_ylabel("Scan number")
    ax1.set_title(f"S11 magnitude waterfall: {start/1e9:.1f}-{stop/1e9:.1f} GHz")
    plt.colorbar(im1, ax=ax1).set_label("|S11| (dB)")

    im2 = ax2.pcolormesh(freq_mesh / 1e9, time_mesh, w_phase,
                         shading="nearest", cmap="plasma")
    ax2.set_xlabel("Frequency (GHz)"); ax2.set_ylabel("Scan number")
    ax2.set_title("S11 phase waterfall")
    plt.colorbar(im2, ax=ax2).set_label("Phase (deg)")

    ax3.plot(freq_arr / 1e9, w_mag[-1], "b-", linewidth=1.5)
    ax3.set_xlabel("Frequency (GHz)"); ax3.set_ylabel("|S11| (dB)")
    ax3.set_title("Latest magnitude scan"); ax3.grid(True, alpha=0.3)

    ax4.plot(freq_arr / 1e9, w_phase[-1], "r-", linewidth=1.5)
    ax4.set_xlabel("Frequency (GHz)"); ax4.set_ylabel("Phase (deg)")
    ax4.set_title("Latest phase scan"); ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def main():
    ap = argparse.ArgumentParser(description="Static S11 waterfall.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=3e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=200, help="points (<=201 on F V2)")
    ap.add_argument("--scans", type=int, default=20, help="number of scans to collect")
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between scans")
    ap.add_argument("--csv", default="s11_waterfall_sample.csv", help="output CSV path")
    ap.add_argument("--save", default=None, help="save figure to path instead of showing")
    args = ap.parse_args()

    try:
        import numpy as np
        import matplotlib
        if args.save:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: F401
    except ImportError:
        print('plotting extra not installed: pip install -e ".[plotting]"')
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
        (freq_arr, w_real, w_imag, w_mag, w_phase, timestamps) = \
            collect_waterfall(nvna, start, stop, pts, args.scans, args.interval)
        nvna.resume()
        print("collection complete")
    finally:
        nvna.disconnect()

    if freq_arr is None or len(freq_arr) == 0:
        print("no usable scan data collected; nothing to plot.")
        return 1

    # write CSV
    with open(args.csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Scan_Number", "Timestamp"]
        for freq in freq_arr:
            header += [f"{freq:.0f}_Real", f"{freq:.0f}_Imag",
                       f"{freq:.0f}_Mag_dB", f"{freq:.0f}_Phase_deg"]
        writer.writerow(header)
        for i in range(len(timestamps)):
            row = [i + 1, timestamps[i].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]]
            for j in range(len(freq_arr)):
                row += [f"{w_real[i][j]:.6f}", f"{w_imag[i][j]:.6f}",
                        f"{w_mag[i][j]:.3f}", f"{w_phase[i][j]:.2f}"]
            writer.writerow(row)
    print(f"data saved to {args.csv} "
          f"({len(timestamps)} scans x {len(freq_arr)} points)")

    import numpy as np
    print(f"frequency range: {freq_arr[0]/1e9:.3f}-{freq_arr[-1]/1e9:.3f} GHz")
    print(f"|S11| range: {np.min(w_mag):.2f} to {np.max(w_mag):.2f} dB")

    fig = plot_waterfall(freq_arr, w_mag, w_phase, start, stop)
    if args.save:
        fig.savefig(args.save, dpi=120)
        print(f"saved {args.save}")
    else:
        import matplotlib.pyplot as plt
        plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
