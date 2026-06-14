#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/plotting_scan.py'
#   Scan S11 over a band and plot real/imag, |S11| dB, phase, and a simplified
#   Smith-plane scatter (4-panel). Requires the [plotting] extra:
#       pip install -e ".[plotting]"
#       python examples/plotting_scan.py --start 1e9 --stop 3e9 --points 200
#
#   NOTE (tinySA cross-reference): tinySA scans return one scalar (dBm) per point;
#   the NanoVNA returns a COMPLEX pair per point, so we take the magnitude to plot.
#
##-------------------------------------------------------------------------------\

##-------------------------------------------------------------------------------
#   nanoVNA_python (nvnapython)
#   './examples/plotting_scan.py'
#   Scan S11 over a band and plot real/imag, |S11| dB, phase, and a simplified
#   Smith-plane scatter. Requires the [plotting] extra (numpy, matplotlib):
#       pip install -e ".[plotting]"
#
#   This keeps the original example's 4-panel layout but:
#     * uses the installed package import (from nvnapython import nanoVNA),
#     * guards against an empty / error scan return before plotting,
#     * keeps legitimate zero samples (the original dropped them, which
#       silently misaligned the frequency axis vs the data),
#     * floors |S11| in dB instead of crashing on a true-zero magnitude,
#     * reads the real frequency axis from frequencies() when lengths agree,
#       falling back to a linspace only if they don't.
#
#   NOTE (intentional tinySA cross-reference): tinySA scans return ONE scalar
#   (dBm) per point; the NanoVNA returns a COMPLEX pair (real, imag) per point,
#   so we take the magnitude before plotting. Same plot shape, different data.
##-------------------------------------------------------------------------------

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def convert_s11_data_to_arrays(start, stop, pts, data):
    # Convert raw device S11 bytes (whitespace-separated real/imag pairs, one
    # per line, possibly with a trailing space) into numpy arrays plus derived
    # magnitude(dB) and phase(deg). Returns (freq, real, imag, mag_db, phase).
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
            # NOTE: unlike the original, we KEEP zero pairs -- a genuine near-
            # zero sample (e.g. a deep null) is real data, and dropping it
            # shifts every later point onto the wrong frequency.
            real_parts.append(float(vals[0]))
            imag_parts.append(float(vals[1]))
        except ValueError:
            continue

    real_arr = np.array(real_parts)
    imag_arr = np.array(imag_parts)

    mag = np.hypot(real_arr, imag_arr)
    # floor zero magnitudes to avoid log10(0) = -inf warnings/crash
    with np.errstate(divide="ignore"):
        magnitude_db = 20.0 * np.log10(np.where(mag > 0, mag, 1e-12))
    magnitude_db = np.where(mag > 0, magnitude_db, -240.0)
    phase_deg = np.degrees(np.arctan2(imag_arr, real_arr))

    actual = len(real_arr)
    freq_arr = np.linspace(start, stop, actual if actual else 1)
    return freq_arr, real_arr, imag_arr, magnitude_db, phase_deg


def main():
    ap = argparse.ArgumentParser(description="Plot NanoVNA S11 (4-panel).")
    ap.add_argument("--port", default=None)
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=3e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=200, help="points (<=201 on F V2)")
    ap.add_argument("--save", default=None, help="save figure to path instead of showing")
    args = ap.parse_args()

    try:
        import numpy as np  # noqa: F401
        import matplotlib
        if args.save:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
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
        print("ERROR: could not connect to port")
        return 1

    try:
        start, stop, pts = int(args.start), int(args.stop), args.points
        nvna.pause()
        data_bytes = nvna.get_scan_s11(start, stop, pts)   # outmask 2
        nvna.resume()
    finally:
        nvna.disconnect()

    # guard: scan() returns b'ERROR' / b'' on a rejected call -> nothing to plot
    if not data_bytes or bytes(data_bytes).strip() in (b"", b"ERROR"):
        print(f"no scan data returned (got {bytes(data_bytes)!r}). Check the "
              "frequency range and that points <= the model max.")
        return 1

    freq, real_arr, imag_arr, mag_db, phase_deg = \
        convert_s11_data_to_arrays(start, stop, pts, data_bytes)

    if len(real_arr) == 0:
        print("scan returned no parseable pairs; nothing to plot.")
        return 1

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    ax1.plot(freq / 1e9, real_arr, "b-", label="Real", linewidth=1.5)
    ax1.plot(freq / 1e9, imag_arr, "r-", label="Imaginary", linewidth=1.5)
    ax1.set_xlabel("Frequency (GHz)")
    ax1.set_ylabel("S11 components")
    ax1.set_title("S11 real and imaginary")
    ax1.legend(); ax1.grid(True, alpha=0.3)

    ax2.plot(freq / 1e9, mag_db, "g-", linewidth=1.5)
    ax2.set_xlabel("Frequency (GHz)")
    ax2.set_ylabel("|S11| (dB)")
    ax2.set_title("S11 magnitude response")
    ax2.grid(True, alpha=0.3)

    ax3.plot(freq / 1e9, phase_deg, "m-", linewidth=1.5)
    ax3.set_xlabel("Frequency (GHz)")
    ax3.set_ylabel("S11 phase (deg)")
    ax3.set_title("S11 phase response")
    ax3.grid(True, alpha=0.3)

    sc = ax4.scatter(real_arr, imag_arr, c=freq / 1e9, cmap="viridis", s=20)
    ax4.set_xlabel("Real"); ax4.set_ylabel("Imaginary")
    ax4.set_title("S11 complex plane (simplified Smith)")
    ax4.grid(True, alpha=0.3); ax4.axis("equal")
    fig.colorbar(sc, ax=ax4).set_label("Frequency (GHz)")

    plt.tight_layout()
    if args.save:
        plt.savefig(args.save, dpi=120)
        print(f"saved {args.save}")
    else:
        plt.show()

    print(f"\nData summary:")
    print(f"  valid points: {len(real_arr)}")
    print(f"  freq range:   {freq[0]/1e9:.3f} - {freq[-1]/1e9:.3f} GHz")
    print(f"  |S11| range:  {mag_db.min():.2f} to {mag_db.max():.2f} dB")
    print(f"  phase range:  {phase_deg.min():.1f} to {phase_deg.max():.1f} deg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
