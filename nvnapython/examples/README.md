# nvnapython examples

Standalone, single-file examples for the `nvnapython` library. Each file runs on
its own — copy one out, point it at your NanoVNA, and go. They bootstrap `src/`
onto the path, so you can run them straight from the repo without installing:

```
python examples/hello_world.py
python examples/hello_world.py --port COM6      # explicit port instead of autoconnect
```

Most take `--port`, `--start`, `--stop`, `--points`; run any with `-h` to see its
options. Every example releases the serial port in a `finally` block, so a failed
run won't leave the port locked for the next one.

## Dependencies

| Example | Needs |
|---|---|
| hello_world, using_autoconnect, using_command_func, basic_scan, identify_and_select_model, solt_calibration, robust_acquisition_loop | library only (pyserial) |
| save_scan_csv, save_raw_to_csv, two_port_s21 | numpy |
| plotting_scan, plotting_waterfall_static, plotting_waterfall_realtime, screen_capture | the `[plotting]` extra (numpy, matplotlib, Pillow): `pip install -e ".[plotting]"` |

## Start here

- **hello_world.py** — the smallest example: connect, print device info, disconnect.
- **using_autoconnect.py** — what `autoconnect()` returns and how `found` vs `connected` differ (device seen vs port actually opened).
- **identify_and_select_model.py** — read the device's identity and select the matching model envelope so the library's range checks use the right bounds for your unit.

## Measuring

- **basic_scan.py** — connect, run a small S11 scan, parse the real/imag pairs. The minimal measurement example.
- **two_port_s21.py** — S21 (port 1 → port 2 transmission); reports insertion loss/gain. Connect your device-under-test between both ports.
- **solt_calibration.py** — interactive Short-Open-Load-Thru calibration: prompts you to attach each standard, runs the cal steps, optionally saves to a preset. This is what makes measurements trustworthy.
- **robust_acquisition_loop.py** — a repeated-scan loop that validates each reply and retries/skips bad reads instead of crashing. Copy this pattern for any long-running collection.

## Saving & plotting

- **save_raw_to_csv.py** — scan S11, save raw frequency/real/imaginary to CSV.
- **save_scan_csv.py** — same, plus derived magnitude (dB) and phase (deg) columns.
- **plotting_scan.py** — 4-panel S11 plot: real/imag, |S11| dB, phase, and a complex-plane (Smith-style) scatter.
- **plotting_waterfall_static.py** — collect N scans, then render magnitude/phase waterfalls and save the data to CSV.
- **plotting_waterfall_realtime.py** — live waterfall: a background thread acquires while matplotlib animates the latest trace plus rolling history. Close the window to stop.
- **screen_capture.py** — grab the device framebuffer, decode it (BGR565), and save a PNG.

## Notes

- The examples assume a NanoVNA-F V2 by default (sweep points up to 201, 50 kHz–3 GHz). If you have a different model, see `identify_and_select_model.py` for selecting its envelope, or override bounds with the `set_*` methods.
- `solt_calibration.py` changes device calibration state (that's its job) and can save to a preset slot. The others are read-only except where noted.
- Each example inlines its own small parser rather than sharing a helper module, so any single file is complete on its own and safe to copy out.
