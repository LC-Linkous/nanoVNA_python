#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/two_port_s21.py'
#   Measure S21 (the port-1 -> port-2 transmission path) and report insertion
#   loss/gain. Connect your device-under-test BETWEEN port 1 and port 2.
#   Uses scan outmask 4 (S21) via get_scan_s21(). Requires numpy.
#       python examples/two_port_s21.py
#       python examples/two_port_s21.py --start 1e6 --stop 900e6 --points 201
#
#   NOTE: meaningful S21 needs a calibration that includes the THRU step
#   (see solt_calibration.py); otherwise the magnitude is uncalibrated.
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def convert_s21_data_to_arrays(start, stop, pts, data):
    # S21 has the same on-wire shape as S11: real/imag pairs, one per line,
    # scan lines trailing-spaced. Keep zero samples (real data; dropping them
    # misaligns the frequency axis).
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
        mag_db = 20.0 * np.log10(np.where(mag > 0, mag, 1e-12))
    mag_db = np.where(mag > 0, mag_db, -240.0)
    phase_deg = np.degrees(np.arctan2(imag_arr, real_arr))
    actual = len(real_arr)
    freq_arr = np.linspace(start, stop, actual if actual else 1)
    return freq_arr, real_arr, imag_arr, mag_db, phase_deg


def main():
    ap = argparse.ArgumentParser(description="Two-port S21 (transmission) measurement.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e6, help="start Hz")
    ap.add_argument("--stop", type=float, default=900e6, help="stop Hz")
    ap.add_argument("--points", type=int, default=201, help="points (<=201 on F V2)")
    ap.add_argument("--save", default=None,
                    help="optional: save an S21 magnitude plot to this path "
                         "(requires matplotlib)")
    args = ap.parse_args()

    try:
        import numpy as np
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
        print("Connect your DUT between PORT 1 and PORT 2 for an S21 measurement.")
        nvna.pause()
        data_bytes = nvna.get_scan_s21(start, stop, pts)   # outmask 4 = S21
        nvna.resume()
    finally:
        nvna.disconnect()

    if not data_bytes or bytes(data_bytes).strip() in (b"", b"ERROR"):
        print(f"no S21 data returned (got {bytes(data_bytes)!r}). Check the range "
              "and that points <= the model max.")
        return 1

    freq, real_arr, imag_arr, mag_db, phase_deg = \
        convert_s21_data_to_arrays(start, stop, pts, data_bytes)

    if len(real_arr) == 0:
        print("S21 scan returned no parseable pairs.")
        return 1

    # report insertion loss/gain summary
    peak_i = int(np.argmax(mag_db))
    min_i = int(np.argmin(mag_db))
    print(f"\nS21 over {freq[0]/1e6:.3f}-{freq[-1]/1e6:.3f} MHz, {len(freq)} points")
    print(f"  max |S21|: {mag_db[peak_i]:+.2f} dB at {freq[peak_i]/1e6:.3f} MHz")
    print(f"  min |S21|: {mag_db[min_i]:+.2f} dB at {freq[min_i]/1e6:.3f} MHz")
    print(f"  mean |S21|: {mag_db.mean():+.2f} dB")
    print("  (negative dB = loss; ~0 dB = thru/low-loss; positive dB = gain)")

    if args.save:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print('matplotlib not installed; skipping plot. pip install -e ".[plotting]"')
            return 0
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(freq / 1e6, mag_db, "b-", linewidth=1.5)
        ax.set_xlabel("Frequency (MHz)"); ax.set_ylabel("|S21| (dB)")
        ax.set_title("S21 transmission"); ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.save, dpi=120)
        print(f"saved {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
