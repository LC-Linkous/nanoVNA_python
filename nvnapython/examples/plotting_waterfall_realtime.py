#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/plotting_waterfall_realtime.py'
#   Live S11 waterfall: a background thread acquires scans while matplotlib
#   animates the latest trace plus a rolling history. Close the window to stop.
#   Requires the [plotting] extra (numpy + matplotlib):
#       pip install -e ".[plotting]"
#       python examples/plotting_waterfall_realtime.py --start 1e9 --stop 3e9
#
#   NOTE: the background thread sleeps ~0.15s between scans -- that paces the
#   on-screen animation and keeps the UI responsive; tune it for your point count.
#
##-------------------------------------------------------------------------------\

import sys
import os
import time
import argparse
import threading
import queue
from collections import deque
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


class LiveS11Plotter:
    def __init__(self, nvna, start, stop, pts, max_history=30):
        self.nvna = nvna
        self.start = start
        self.stop = stop
        self.pts = pts
        self.max_history = max_history

        self.freq_arr = None
        self.magnitude_history = deque(maxlen=max_history)
        self.real_history = deque(maxlen=max_history)
        self.imag_history = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)

        self.data_queue = queue.Queue()
        self.running = False
        self.data_thread = None

        self.current_magnitude = None
        self.current_phase = None
        self.current_real = None
        self.current_imag = None

    def data_acquisition_thread(self):
        # background thread for continuous data acquisition
        while self.running:
            try:
                data_bytes = self.nvna.get_scan_s11(self.start, self.stop, self.pts)
                freq_arr, real_arr, imag_arr, mag_arr, phase_arr = \
                    convert_s11_data_to_arrays(self.start, self.stop, self.pts, data_bytes)
                self.data_queue.put({
                    "freq": freq_arr, "real": real_arr, "imag": imag_arr,
                    "magnitude": mag_arr, "phase": phase_arr,
                    "timestamp": datetime.now(),
                })
                # ~0.15s paces the animation / keeps the UI responsive; tune for
                # your point count and refresh rate (see module docstring).
                time.sleep(0.1)
            except Exception as e:
                print(f"data acquisition error: {e}")
                break

    def start_acquisition(self):
        self.running = True
        self.data_thread = threading.Thread(target=self.data_acquisition_thread, daemon=True)
        self.data_thread.start()

    def stop_acquisition(self):
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=2.0)

    def update_plots(self, frame, axes, fig):
        import numpy as np
        ax1, ax2, ax3, ax4 = axes

        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
            except queue.Empty:
                break
            if self.freq_arr is None:
                self.freq_arr = data["freq"]
            self.current_magnitude = data["magnitude"]
            self.current_phase = data["phase"]
            self.current_real = data["real"]
            self.current_imag = data["imag"]
            self.magnitude_history.append(data["magnitude"])
            self.real_history.append(data["real"])
            self.imag_history.append(data["imag"])
            self.timestamps.append(data["timestamp"])

        for ax in axes:
            ax.clear()

        if self.freq_arr is not None and self.current_magnitude is not None:
            ax1.plot(self.freq_arr / 1e9, self.current_magnitude, "b-", linewidth=1.5)
            ax1.set_xlabel("Frequency (GHz)"); ax1.set_ylabel("|S11| (dB)")
            ax1.set_title("Live S11 magnitude"); ax1.grid(True, alpha=0.3)

            ax2.plot(self.freq_arr / 1e9, self.current_phase, "r-", linewidth=1.5)
            ax2.set_xlabel("Frequency (GHz)"); ax2.set_ylabel("Phase (deg)")
            ax2.set_title("Live S11 phase"); ax2.grid(True, alpha=0.3)

            if len(self.magnitude_history) > 1:
                # all history rows share the freq axis length (same pts); guard
                # against a ragged row from a truncated scan by trimming to min.
                rows = list(self.magnitude_history)
                width = min(len(r) for r in rows)
                if width > 0:
                    mat = np.array([r[:width] for r in rows])
                    fa = self.freq_arr[:width]
                    time_arr = np.arange(mat.shape[0])
                    fm, tm = np.meshgrid(fa, time_arr)
                    ax3.pcolormesh(fm / 1e9, tm, mat, shading="nearest", cmap="viridis")
                    ax3.set_xlabel("Frequency (GHz)"); ax3.set_ylabel("scans ago")
                    ax3.set_title("S11 magnitude history")

            ax4.scatter(self.current_real, self.current_imag,
                        c=self.freq_arr / 1e9, cmap="plasma", s=10, alpha=0.7)
            ax4.set_xlabel("Real"); ax4.set_ylabel("Imaginary")
            ax4.set_title("S11 complex plane"); ax4.grid(True, alpha=0.3)
            ax4.axis("equal")

        if self.timestamps:
            fig.suptitle(f"Live S11 - {self.timestamps[-1].strftime('%H:%M:%S')}",
                         fontsize=14)


def main():
    ap = argparse.ArgumentParser(description="Realtime S11 waterfall.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=1e9, help="start Hz")
    ap.add_argument("--stop", type=float, default=3e9, help="stop Hz")
    ap.add_argument("--points", type=int, default=150, help="points (<=201 on F V2)")
    args = ap.parse_args()

    try:
        import numpy as np  # noqa: F401
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
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

    plotter = None
    try:
        print("Starting live S11 measurement... close the plot window to stop.")
        start, stop, pts = int(args.start), int(args.stop), args.points
        nvna.pause()

        plotter = LiveS11Plotter(nvna, start, stop, pts, max_history=30)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        plt.subplots_adjust(hspace=0.3, wspace=0.3)
        axes = (ax1, ax2, ax3, ax4)

        plotter.start_acquisition()
        _ani = animation.FuncAnimation(
            fig, plotter.update_plots, fargs=(axes, fig),
            interval=200, blit=False, cache_frame_data=False)
        plt.show()   # blocks until the window is closed
    except KeyboardInterrupt:
        print("\nmeasurement interrupted by user")
    finally:
        if plotter is not None:
            plotter.stop_acquisition()
        try:
            nvna.resume()
        finally:
            nvna.disconnect()
        print("live measurement stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
