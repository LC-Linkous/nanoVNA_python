# nvnapython

**An Unofficial Python API for the NanoVNA Device Series**

[![PyPI version](https://badge.fury.io/py/nvnapython.svg)](https://badge.fury.io/py/nvnapython)
[![Python versions](https://img.shields.io/pypi/pyversions/nvnapython.svg)](https://pypi.org/project/nvnapython/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/nvnapython.svg)](https://pypi.org/project/nvnapython/)
[![Downloads](https://static.pepy.tech/badge/nvnapython)](https://pepy.tech/project/nvnapython)
[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20685801.svg)](https://doi.org/10.5281/zenodo.20685801)

A non-GUI Python API for the NanoVNA series of vector network analyzer devices. This library provides programmatic control over NanoVNA devices for automated S-parameter measurements, data collection, and analysis.

This repository uses official resources and documentation but is **NOT** endorsed by any official NanoVNA product, owner, or company. Refer to official resources and support for product information. This library is developed and tested against the NanoVNA-F V2 and NanoVNA-F V3; other models are supported by selecting their envelope, but knock-off or custom devices may not be compatible and have not been tested.


## Features

- **Device Discovery** — automatic detection and serial connection to NanoVNA devices
- **Frequency Sweeps** — collect S11 / S21 sweep data across specified frequency ranges
- **Per-Model Envelopes** — sweep-point, frequency, and slot bounds for the F V2, F V3, H4, and a generic fallback
- **Screen Capture** — read the device framebuffer and decode it to an image
- **Calibration** — drive an interactive SOLT (Short-Open-Load-Thru) calibration
- **Data Export** — easy integration with `matplotlib` and `numpy`
- **Error Handling** — input checking against the selected model and verbose output options
- **Device Control** — full programmatic control of NanoVNA settings and measurements

## Installation

```bash
pip install nvnapython
```

The library itself depends only on `pyserial`. The plotting and screen-capture examples need an optional extra:

```bash
pip install "nvnapython[plotting]"
```

Python 3.10+ is required.

## Quick Start

```python
from nvnapython import nanoVNA

nvna = nanoVNA()
found, connected = nvna.autoconnect()
if connected:
    print(nvna.info())
    nvna.disconnect()
```

To collect an S11 sweep:

```python
from nvnapython import nanoVNA

nvna = nanoVNA()
found, connected = nvna.autoconnect()
if connected:
    nvna.pause()
    s11 = nvna.get_scan_s11(int(1e9), int(3e9), 200)   # 1-3 GHz, 200 points
    nvna.resume()
    nvna.disconnect()
    print(s11)
```

## Selecting a Device Model

A fresh `nanoVNA()` is seeded with the NanoVNA-F V2 envelope. If you have a different model, select its envelope so the library's range checks match your hardware:

```python
nvna.select_existing_device("NANOVNA_F_V3")   # 50 kHz - 6 GHz, up to 801 points
print(nvna.list_known_models())                # F V2, F V3, H4, GENERIC
```

## Examples

The [main GitHub repository](https://github.com/LC-Linkous/nanoVNA_python) provides runnable examples, grouped by what they demonstrate.

**Getting started / device control**

- `hello_world.py` — connect, read device info, disconnect
- `using_autoconnect.py` — detect and connect to a NanoVNA by USB ID
- `identify_and_select_model.py` — read the device identity and select the matching model envelope
- `using_command_func.py` — send raw device commands for functionality not yet wrapped by the library

**Acquisition**

- `basic_scan.py` — run a single S11 sweep over a frequency range
- `two_port_s21.py` — collect S21 (transmission) data
- `robust_acquisition_loop.py` — a resilient repeated-acquisition loop

**Plotting scan data**

- `plotting_scan.py` — plot a single sweep (magnitude, phase, and a Smith-style complex plot)
- `plotting_waterfall_static.py` — collect several sweeps and render a static waterfall plot
- `plotting_waterfall_realtime.py` — a live, continuously updating waterfall plot

**Calibration**

- `solt_calibration.py` — interactively run a SOLT (Short-Open-Load-Thru) calibration

**Screen capture**

- `screen_capture.py` — read the device framebuffer and save it as an image

**Exporting data**

- `save_raw_to_csv.py` — run a scan and write frequency/real/imaginary to a CSV file
- `save_scan_csv.py` — as above, with derived magnitude (dB) and phase (deg) columns

> Most plotting and capture examples require the optional plotting dependencies:
> `pip install "nvnapython[plotting]"`

## Documentation

For comprehensive documentation, the full command reference, advanced examples, and troubleshooting:

- **Library GitHub repository**: [https://github.com/LC-Linkous/nanoVNA_python/](https://github.com/LC-Linkous/nanoVNA_python/)
- **Official NanoVNA documentation**: [https://nanovna.com/](https://nanovna.com/) (not associated with this library)

## Contributing

This is an unofficial community project. Contributions welcome!

- Report bugs and request features on [GitHub](https://github.com/LC-Linkous/nanoVNA_python)
- For device information and OFFICIAL resources, see [https://nanovna.com/](https://nanovna.com/)
  - Please do **NOT** request features or report bugs to the official NanoVNA community or makers! This is an unofficial project and they do not maintain it.

## Citing

If you use this library in your work, citation details are in the repository's `CITATION.cff`. <!-- A Zenodo DOI will be added on release; update this section and the DOI badge above when it is assigned. -->

## License

GPL-2.0 — this package and the repo code is unofficial software with no warranty, offered AS-IS. Use at your own risk.

The licensing of this software does NOT take priority over the official releases and the decisions of the official NanoVNA team or device makers. This licensing does NOT take priority for any of their products, including the devices that can be used with this software.

## Acknowledgments

- The NanoVNA device creators and community, who have created an awesome line of devices
- Official NanoVNA documentation and resources, especially [nanovna.com](https://nanovna.com/)
- All contributors to this library, including those who have contributed code and reached out with questions

---

**Disclaimer**: This software is unofficial and not supported by the NanoVNA team or device makers. For official software and support, visit [nanovna.com](https://nanovna.com/). The NanoVNA makers do not offer tech support for this software, do not maintain it, and have no responsibility for any of the contents.