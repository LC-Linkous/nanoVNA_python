# nanoVNA_python

<!-- Badges. Note on the DOI: replace the Zenodo badge + link below once the
     Zenodo deposit is created and a DOI is assigned. -->

[![PyPI version](https://badge.fury.io/py/nvnapython.svg)](https://badge.fury.io/py/nvnapython)
[![Python versions](https://img.shields.io/pypi/pyversions/nvnapython.svg)](https://pypi.org/project/nvnapython/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/nvnapython.svg)](https://pypi.org/project/nvnapython/)
[![Downloads](https://static.pepy.tech/badge/nvnapython)](https://pepy.tech/project/nvnapython)
[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
<!-- [![DOI](https://zenodo.org/badge/DOI/REPLACE_WITH_DOI.svg)](https://doi.org/REPLACE_WITH_DOI) -->


<!-- Zenodo archive with DOI: add link once the deposit is created. -->

## AN UNOFFICIAL Python API for the NanoVNA Device Series

A non-GUI Python API for the NanoVNA series of vector network analyzers. 

This repository uses official resources and documentation but is NOT endorsed by the official NanoVNA product or company. See the [references](#references) section for further reading. See the [official NanoVNA resources](https://nanovna.com/) and the [active user group](https://groups.io/g/nanovna-users/) for device features.

This library covers most of the documented commands for the NanoVNA device series. The documentation (after the examples) is sorted by the serial command for the device, with usage examples provided. While some error checking exists in both the device and the library, it is not exhaustive. It is strongly advised to read the official documentation before scripting with your NanoVNA device. Operating the device experimentally or without referencing the official documents runs the risk of **damaging your device or connected equipment**.


There also exists several officially recognized resources:
* [NanoVNA-App](https://nanovna.com/?page_id=141), download available on official page
    * With development at [https://github.com/OneOfEleven/NanoVNA-App](https://github.com/OneOfEleven/NanoVNA-App)   
* [NanoVNA-Saver](https://nanovna.com/?page_id=90)
    * With releases and download at [https://github.com/NanoVNA-Saver/nanovna-saver/releases](https://github.com/NanoVNA-Saver/nanovna-saver/releases)
* [NanoVNA-Web-Client / WebApp](https://nanovna.com/?page_id=26)
    * Works from https://cho45.stfuawsc.com/NanoVNA/ using the latest version of chrome browser, and as an Android .apk


This README provides example code for connecting to the device, scanning and plotting data, saving to CSV, capturing the screen, and running calibrations. Examples are not exhaustive. Refer to the [List of NanoVNA Commands and their Library Commands](#list-of-nanovna-commands-and-their-library-commands) for the tested commands. Alias functions are provided for convenience but are not exhaustive.

If you are interested in developing the PyPI package or making a custom local version, see [Library Development](#library-development) towards the end of this README.

The primary GitHub: [https://github.com/LC-Linkous/nanoVNA_python](https://github.com/LC-Linkous/nanoVNA_python)

The PyPI page: [https://pypi.org/project/nvnapython/](https://pypi.org/project/nvnapython/)



## Table of Contents
* [The NanoVNA Series of Devices](#the-nanovna-series-of-devices)
* [Library Usage](#library-usage)
    * [PyPI Install](#pypi-install)
    * [Local Install Using UV](#local-install-using-uv)
* [Requirements](#requirements)
* [Structure](#structure)
* [Running Tests](#running-tests)
* [Error Handling](#error-handling)
* [Example Implementations](#example-implementations)
    * [Finding the Serial Port](#finding-the-serial-port)
        * [Autoconnection with the nanoVNA_python Library](#autoconnection-with-the-nanovna_python-library)
        * [Manually Finding a Port on Windows](#manually-finding-a-port-on-windows)
        * [Manually Finding a Port on Linux](#manually-finding-a-port-on-linux)
    * [Serial Message Return Format](#serial-message-return-format)
    * [Connecting and Disconnecting the Device](#connecting-and-disconnecting-the-device)
    * [Toggle Error Messages](#toggle-error-messages)
    * [Device and Library Help](#device-and-library-help)
    * [Selecting a Device Model](#selecting-a-device-model)
    * [Getting Data from the Active Screen](#getting-data-from-the-active-screen)
    * [Saving Screen Images](#saving-screen-images)
    * [Plotting Data with Matplotlib](#plotting-data-with-matplotlib)
    * [Saving SCAN Data to CSV](#saving-scan-data-to-csv)
    * [Accessing the NanoVNA Directly](#accessing-the-nanovna-directly)
* [List of NanoVNA Commands and their Library Commands](#list-of-nanovna-commands-and-their-library-commands)
* [Additional Library Functions for Advanced Use](#additional-library-functions-for-advanced-use)
* [Library Development](#library-development)
* [Notes for Beginners](#notes-for-beginners)
    * [Vocab Check](#vocab-check)
    * [VNA vs. SA vs. LNA vs. SNA vs. SDR vs Signal Generator](#vna-vs-sa-vs-lna-vs-sna-vs-sdr-vs-signal-generator)
    * [Calibration Setup](#calibration-setup)
    * [Some General NanoVNA Notes](#some-general-nanovna-notes)
* [FAQs](#faqs)
* [References](#references)
* [Licensing](#licensing)


## The NanoVNA Series of Devices

The [NanoVNA line of devices](https://nanovna.com/?page_id=21) are a series of portable and pretty user-friendly vector network analyzer devices. There are several devices with different frequency ranges, so refer to [official documentation](https://nanovna.com/?page_id=21) to select one for your needs. There are also some very convincing knock-off devices, so ensure that you are purchasing an actual device from a [reputable vendor](https://nanovna.com/?page_id=121). 

This device is often compared to the [tinySA series of devices][https://tinysa.org/](https://tinysa.org/). The NanoVNA series is a handheld vector network analyzer (VNA), which measures the S-parameters (loosely: a type of response of a device or antenna) over at different frequencies, while a spectrum analyzer measures the amplitude of RF signals at different frequencies. There's a lot of overlap with the use of both devices, but the measurements are very different. A signal generator (one of the features of the tinySA) is exactly what it sounds like - it generates a signal at a specific frequency or frequencies at a specified power level.

Official documentation can be found at [https://nanovna.com/](https://nanovna.com/?page_id=21). The official Wiki is going to be more up to date than this repo with new versions and features, and they also have links to GUI-based software. Several community projects also exist on GitHub.

There is also a very active NanoVNA community at [https://groups.io/g/nanovna-users/](https://groups.io/g/nanovna-users/) exploring the device capabilities and its many features. 

The end of this README will have some references and links to supporting material, but it is STRONGLY suggested to do some basic research and become familiar with your device before attempting to script or write code for it. 



## Library Usage

This library is available via PyPI, local install, or by using the class directly. We recommend one of the install options.

Several usage examples are provided in the [Example Implementations](#example-implementations) section, including working with the hardware and plotting results with matplotlib. Runnable versions of all of them live in the `examples/` directory (see the [examples README](examples/README.md)).


### PyPI Install

The `nvnapython` package (from PyPI at [https://pypi.org/project/nvnapython/](https://pypi.org/project/nvnapython/)) can be installed with:

```python

pip install nvnapython

```

The GitHub repository is named `nanoVNA_python` to differentiate the working version (with extended documentation and runnable examples) from the installable package.


### Local Install Using UV

Developing a project, or running something custom? You can pull the code from GitHub and build + install the package locally.

(You can also use your favorite package manager. This is set up for UV, but the information for other setups is in the `nvnapython` directory.)

```python
# install UV
pip install uv

# navigate to the nvnapython directory
cd .\nvnapython

# build the package
# a 'dist' directory should be created in nvnapython
uv build

# install the package locally
pip install dist/nvnapython-<version>-py3-none-any.whl

```


## Requirements

The core library depends only on [pyserial](https://pypi.org/project/pyserial/) for device communication. The plotting and screen-capture examples additionally need numpy, matplotlib, and Pillow, which are grouped under the optional `[plotting]` extra:

```python
# core library only
pip install nvnapython

# with the plotting/imaging example dependencies
pip install "nvnapython[plotting]"
```

For users on Linux systems, `pyQt5` is used with `matplotlib` to draw the figures. `pyQT5` needs to be installed on Linux systems to follow the examples included in this README, but is not needed on all Windows machines. Install both if you have doubts; they're small packages and commonly used.


Python 3.9+ is recommended. The examples are written for a NanoVNA-F V2 by default but take `--start`, `--stop`, and `--points` arguments for other ranges.


## Structure

The `nvnapython` library, as it is available on PyPI, is structured as follows:

```
nvnapython/
├── .python-version
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── nvnapython/
│       ├── __init__.py
│       ├── core.py
│       ├── constants.py
│       ├── _bounds.py
│       ├── py.typed
│       └── _commands/
│           ├── __init__.py
│           ├── acquisition.py
│           ├── calibration.py
│           ├── display_ui.py
│           ├── markers_traces.py
│           ├── presets_config.py
│           └── system_info.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── fakes.py
    ├── test_smoke.py
    ├── test_acquisition.py
    ├── test_calibration.py
    ├── test_display_ui.py
    ├── test_markers_traces.py
    ├── test_presets_config.py
    ├── test_system_info.py
    ├── test_parsing.py
    ├── test_core_serial.py
    ├── test_bounds_helper.py
    ├── test_boundary_safety.py
    ├── test_command_coverage.py
    ├── test_edge_cases.py
    ├── test_hardware_captures.py
    ├── test_hardware.py
    ├── test_hardware_audit.py
    ├── test_hardware_boundaries.py
    ├── test_hardware_probe.py
    ├── test_hardware_capture_probe.py
    ├── readme_capture.md
    ├── collect_readme_data.py
    └── run_all_tests.py
```

The public API is `from nvnapython import nanoVNA`, which exposes the full `nanoVNA` class. The per-command methods live in mixin modules under `_commands/` and are composed onto the `nanoVNA` class in `core.py`, which holds the shared state, serial handling, model envelope, and helper methods. `constants.py` holds the per-model envelopes (frequency range, max points, screen size, slot counts) and `_bounds.py` the range-checking helpers.

This library is also part of the `nanoVNA_python` repository, which includes more extensive documentation, runnable examples, and the working development. The GitHub repository is structured as follows:

```
nanoVNA_python/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .python-version
├── examples/
│   ├── README.md
│   ├── hello_world.py
│   ├── using_autoconnect.py
│   ├── using_command_func.py
│   ├── identify_and_select_model.py
│   ├── basic_scan.py
│   ├── two_port_s21.py
│   ├── solt_calibration.py
│   ├── robust_acquisition_loop.py
│   ├── plotting_scan.py
│   ├── plotting_waterfall_static.py
│   ├── plotting_waterfall_realtime.py
│   ├── save_raw_to_csv.py
│   ├── save_scan_csv.py
│   └── screen_capture.py
├── src/
│   └── nvnapython/
│       ├── __init__.py
│       ├── core.py
│       ├── constants.py
│       ├── _bounds.py
│       ├── py.typed
│       └── _commands/
│           ├── __init__.py
│           ├── acquisition.py
│           ├── calibration.py
│           ├── display_ui.py
│           ├── markers_traces.py
│           ├── presets_config.py
│           └── system_info.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── fakes.py
    ├── readme_capture.md
    ├── collect_readme_data.py
    ├── run_all_tests.py
    ├── (test_*.py — see the package layout above)
    └── (diagnose_*.py — manual hardware diagnostics)
```


## Running Tests

This is primarily for development or advanced troubleshooting. These tests are for the API.

The test suite uses [pytest](https://docs.pytest.org/). Tests must be run from the `nvnapython` project directory (the one containing `pyproject.toml`), since the pytest configuration and the `hardware` marker are defined in `pyproject.toml`. Running from a different directory will produce an `Unknown pytest.mark.hardware` warning.

Install the test dependencies first:
```bash
pip install -e ".[test]"
# or, using pip directly:
pip install pytest pytest-cov
```

Run the suite (hardware tests self-skip when no device is connected):
```bash
python -m pytest
```

> **Note:** use `python -m pytest`, not `uv run pytest`. Running through `uv` here can create a stray virtual environment inside the project directory and tangle the test environment.

The suite is split into hardware-free tests and tests that need a connected NanoVNA. The hardware tests are marked with `@pytest.mark.hardware` and are skipped automatically when no device is detected:
```bash
# run ONLY the hardware-free tests (explicitly skip device tests)
python -m pytest -m "not hardware"

# run ONLY the hardware tests (requires a connected NanoVNA)
python -m pytest -m hardware
```

Hardware detection is intentionally NOT cached, so you can plug/unplug the device between runs without restarting the process. If a connected device is being skipped (e.g. a model reporting an unexpected USB PID), force the hardware tests with:
```bash
# Windows PowerShell
$env:NVNA_FORCE_HARDWARE = "1"; python -m pytest -m hardware

# Linux / macOS
NVNA_FORCE_HARDWARE=1 python -m pytest -m hardware
```

To see coverage while testing:
```bash
python -m pytest --cov=nvnapython --cov-report=term-missing
```

### Capturing real device responses

`tests/collect_readme_data.py` is a helper (not a pytest test) that connects to a real device, sends a set of read-only commands, and writes their verbatim responses to `tests/readme_capture.md`. The parsing tests (`test_parsing.py`, `test_hardware_captures.py`) then replay those exact device bytes through the library's real `clean_return`/parsing logic — proving the library handles true hardware output, not an idealized synthetic version. These run without a device, since the bytes are frozen in the capture file:
```bash
# auto-detect the serial port
python tests/collect_readme_data.py

# or specify the port explicitly
python tests/collect_readme_data.py --port COM22     # Windows
python tests/collect_readme_data.py --port /dev/ttyACM0   # Linux
```

### Manual hardware diagnostics

The `tests/diagnose_*.py` scripts are manual tools (not pytest tests) used during hardware bring-up to isolate timing and framing behavior — e.g. `diagnose_fastcmd.py` reproduced the rapid-command serial race, and the capture diagnostics measured the framebuffer transfer. They require a connected device and print their findings rather than asserting.

These are experimental in nature and have limitations. They are not designed to be exhaustive diagnostic tools, and are left in this repo for future development usage.


## Error Handling

Some error handling has been implemented for the individual functions in this library, but not for much of the device configuration. Most functions have a list of acceptable formats for input, which is included in the documentation. 

Two library-side toggles control how much the library reports:

* `set_verbose(True/False)` — when on, the library prints detailed status/diagnostic messages (which port it checks, what a method did, warnings). When off, it stays quiet.
* `set_error_byte_return(True/False)` — when on, a command the library rejects (bad argument, out-of-range value) returns an explicit `b'ERROR'`. When off, a rejected command returns the default empty `b''`.

The library validates many arguments before sending them (sweep point counts, frequency ranges, marker indices, slot numbers) against the selected model's envelope. Validation is not exhaustive, and the device performs its own checks too, so always consult the official documentation for valid ranges.


## Example Implementations

Runnable, standalone versions of every example below are in the `examples/` directory; each is a single file you can copy out and run. See [examples/README.md](examples/README.md) for the full list organized by task. The snippets here are illustrative.

All examples release the serial port in a `finally` block, so a failed run does not leave the port locked for the next run — a leaked handle is the usual cause of a `PermissionError` / "device not functioning" on the next attempt on Windows.

This library was developed on Windows and has been lightly tested on Linux. The main difference (so far) has been in the permissions for first access of the serial port, but there may be smaller bugs in format that have not been detected yet. 


### Finding the Serial Port

To start, a serial connection between the NanoVNA and user PC device must be created. There are several ways to list available serial ports. The library supports some rudimentary autodetection, but if that does not work instructions in this section also support manual detection. 


#### Autoconnection with the nanoVNA_python Library

`autoconnect()` scans the serial ports for a device matching the NanoVNA USB VID:PID (`0x0483:0x5740`) and connects to the first match. It returns **two booleans**, `(found, connected)`: `found` means a matching device was seen on some port; `connected` means the port was actually opened. These can differ a device can be found but fail to connect (port busy, held by another program, permissions).


If multiple devices have the same VID, then the first one found is used. If you are connecting multiple devices to a user PC, then it is suggested to connect them manually (for now). The NanoVNA and tinySA devices have the same VID and hardware identification for the serial ports.


```python
# import the library (installed package)
from nvnapython import nanoVNA

# create a new nanoVNA object
nvna = nanoVNA()

# set the return-message preferences
nvna.set_verbose(True)            # detailed messages
nvna.set_error_byte_return(True)  # explicit b'ERROR' on a rejected command

# attempt to autoconnect
found, connected = nvna.autoconnect()

if connected:
    print("device connected")
    print(nvna.info())
    nvna.disconnect()
else:
    print("ERROR: could not connect to port")
```

#### Manually Finding a Port on Windows

If autoconnect does not find your device (for example, a model with a different USB descriptor), you can find the COM port manually and pass it to `connect()`. 

1)  Open _Device Manager_, scroll down to _Ports (COM & LPT)_, and expand the menu. There should be a _COM#_ port listing "USB Serial Device(COM #)". If your NanoVNA is set up to work with Serial, this will be it. Note the `COMx` 

2) Then you can use the code below to confirm connection.This uses the pyserial library requirement already installed for this library.


```python
from nvnapython import nanoVNA
nvna = nanoVNA()
nvna.connect("COM22")     # use the COM number you found
```

If a device does not connect, use the code below to list all ports.

```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

for port, desc, hwid in ports:
    print(f"Port: {port}, Description: {desc}, Hardware ID: {hwid}")
```

Example output for this method (on Windows) is as follows:

```python

Port: COM4, Description: Standard Serial over Bluetooth link (COM4), Hardware ID: BTHENUM\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0000\7&D0D1EE&0&000000000000_00000000
Port: COM3, Description: Standard Serial over Bluetooth link (COM3), Hardware ID: BTHENUM\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0002\7&D0D1EE&0&B8B3DC31CBA8_C00000000
Port: COM22, Description: USB Serial Device (COM10), Hardware ID: USB VID:PID=0483:5740 SER=400 LOCATION=1-3

```

"COM22" is the port location of the NanoVNA that is used in the examples in this README.


#### Manually Finding a Port on Linux

On Linux the device usually appears as `/dev/ttyACM0` (or a higher number). List candidates with:

```bash
ls /dev/ttyACM*
# or inspect USB devices
dmesg | grep -i tty
```

Then connect explicitly. You may need to be in the `dialout` group (or use `sudo`) to access the port.

Ports can also be found from within your IDE:
```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

for port, desc, hwid in ports:
    print(f"Port: {port}, Description: {desc}, Hardware ID: {hwid}")

```

This method identified the `/dev/ttyACM0`. Now, when attempting to use the autoconnection feature, the following error was initially returned:

```python
[Errno 13] could not open port /dev/ttyACM0: [Errno 13] Permission denied: '/dev/ttyACM0'

```

This was due to not having permission to access the port. In this case, this error was solved by opening a terminal and executing `sudo chmod a+rw /dev/ttyACM0`. Should this issue be persistent, other solutions related to user groups and access will need to be investigated.  


Confirm connection to the nanoVNA with:

```python
from nvnapython import nanoVNA
nvna = nanoVNA()
nvna.connect("/dev/ttyACM0")
```


### Serial Message Return Format

This libary has iterated over several message return formats on the backend while interfacing with the device. All front-end commands remain the same.

The original message format:
```python
bytearray(b'info\r\nModel:        NanoVNA-F_V2\r\nFrequency:    50k ~ 3GHz\r\nBuild time:   Mar  2 2021 - 09:40:50 CST\r\nch> \r\n')
```

Cleaned version:

```python
bytearray(b'Model:        NanoVNA-F_V2\r\nFrequency:    50k ~ 3GHz\r\nBuild time:   Mar  2 2021 - 09:40:50 CST\r')
```

The device frames every reply by echoing the command, sending the payload (whitespace-separated values, one record per line, CR/LF terminated), and ending with the console prompt. On the NanoVNA-F V2 firmware tested here, the prompt is emitted as `ch> ` (with a trailing space) and is **doubled** at the end of each reply — the tail is `...\r\nch> \r\nch> `. The library's read logic consumes that whole prompt tail so leftover bytes don't corrupt the next command, and `clean_return()` strips the echoed-command line and the trailing prompt, leaving just the payload.

Two framing details worth knowing if you parse raw output yourself:

* `scan` output lines (outmask 2 and similar) carry a **trailing space** before the newline; the `frequencies` command's lines do **not**. `str.split()` handles both transparently.
* Binary replies (the `capture` framebuffer) are NOT line-framed and can contain bytes that happen to equal `ch>` or `>` — so binary reads are handled by byte count, not by scanning for the prompt (see [Saving Screen Images](#saving-screen-images)).

### Connecting and Disconnecting the Device
 
 This example shows the process for initializing, opening the serial port, getting device info, and disconnecting.

```python
from nvnapython import nanoVNA

nvna = nanoVNA()
nvna.set_verbose(True)
nvna.set_error_byte_return(True)

found, connected = nvna.autoconnect()      # or: nvna.connect("COM22")
if connected:
    print("device connected")
    # ... do work ...
    nvna.disconnect()                       # always release the port
else:
    print("ERROR: could not connect to port")
```


Example output for this method is as follows:

```python

bytearray(b'Model:        NanoVNA-F_V2\r\nFrequency:    50k ~ 3GHz\r\nBuild time:   Mar  2 2021 - 09:40:50 CST\r')

```


### Toggle Error Messages

Currently, the following can be used to turn on or off returned error messages.

1) the 'verbose' option. When enabled, detailed messages are printed out. 

2) the 'errorByte' option. When enabled, if there is an error with the command or configuration, `b'ERROR'` is returned instead of the default `b''`. 

```python
# detailed status messages ON
nvna.set_verbose(True)
# detailed status messages OFF
nvna.set_verbose(False)

# when a command is rejected, return an explicit b'ERROR'
nvna.set_error_byte_return(True)
# when a command is rejected, return the default b''
nvna.set_error_byte_return(False)
```

### Device and Library Help

The `help` return can be accessed via the `help()` function call.

```python
nvna.help()
```

Or access the command list via the `help` command through the passthrough, and the library exposes method-level docstrings for each wrapped command:

```python
# the device's built-in command list
print(nvna.command("help"))

# Python help for a library method
help(nvna.scan)
```

The `help` command returns bytearray in the format `bytearray(b'commands:......')`

### Selecting a Device Model

When using the library, the `nanoVNA()` class is seeded with the NanoVNA-F V2 envelope by default. 

If you have a different model, select its envelope so the library's range checks (sweep points, frequency range, screen size, slot counts) match your hardware. `select_existing_device()` changes **library-side bounds only**; it does not change anything on the device.

The shipped presets:

| Preset | Frequency range | Max points | Screen | Cal/preset slots |
|---|---|---|---|---|
| `NANOVNA_F_V2` (default) | 50 kHz – 3 GHz | 201 | 800×480 | 7 |
| `NANOVNA_F_V3` | 50 kHz – 6 GHz | 801 | 800×480 | 7 |
| `NANOVNA_H4` | 10 kHz – 1.5 GHz | 101 | 320×480 | 5 |
| `NANOVNA_GENERIC` | 10 kHz – 1.5 GHz | 101 | 320×240 | 5 |

```python
from nvnapython import nanoVNA
nvna = nanoVNA()

# see the available presets
print(nvna.list_known_models())          # NANOVNA_F_V2, NANOVNA_F_V3, NANOVNA_H4, NANOVNA_GENERIC

# select the one matching your unit (e.g. a NanoVNA-F V3)
nvna.select_existing_device("NANOVNA_F_V3")
print(nvna.get_device_model())

# the bounds now in effect
print(nvna.get_max_points())                                  # 801
print(nvna.get_min_device_freq(), nvna.get_max_device_freq()) # 50000.0  6000000000.0
print(nvna.get_screen_size())                                 # (800, 480)
```

Individual bounds can also be overridden directly with `set_max_points`, `set_min_device_freq` / `set_max_device_freq`, and `set_screen_size`. See `examples/identify_and_select_model.py` for a full read-identity-then-select walkthrough.

A note on the F V3 frequency ceiling: the device's firmware `info` banner reports `50k ~ 6.3GHz`, but the hardware only returns valid samples up to **6 GHz** — scanning above that yields all-zero data. The preset's `max_freq_hz` is set to the real 6 GHz limit accordingly. The library's bounds are a guardrail, not a hard wall: `command()` sends a raw command string with no validation, so you can always bypass the envelope when you know what you're doing.

### Getting Data from the Active Screen

See other sections for the following examples:
* [Saving Screen Images](#saving-screen-images)
* [Plotting Data with Matplotlib](#plotting-data-with-matplotlib)

The most straight forward way to get data from an active screen is with the `data` command. This will pull data from an active screen. It will not adjust the range or number of points before a read. If the range needs to be adjusted prior to a read, use `scan` instead.

S-parameter data for the most recent sweep is read with the `data` command: `data 0` returns S11, `data 1` returns S21, and `data 2`–`6` return the calibration tables. The matching frequency axis comes from `frequencies`.

```python
nvna.pause()                       # freeze the sweep so the read is stable
s11 = nvna.get_s11_data()          # data 0  -> real/imag pairs
freqs = nvna.frequencies()         # matching frequency axis (Hz)
nvna.resume()
```

### Analysis of the Returned Data from the NanoVNA

This first example shows how to get measured data on the screen (using `data`) or to specify the read range and then measure with `scan`. Data returned will always be in a bytearray, but it will need to be converted in order to work with it.


```python
# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA 
import time
import serial

# create a new tinySA object    
nvna = nanoVNA()

# set the return message preferences 
nvna.set_verbose(True) #detailed messages
nvna.set_error_byte_return(True) #get explicit b'ERROR' if error thrown


# attempt to autoconnect
found_bool, connected_bool = nvna.autoconnect()

# if port closed, then return error message
if connected_bool == False:
    print("ERROR: could not connect to port")
else: # if port found and connected, then complete task(s) and disconnect

    # set up some parameters for the scan
    # NanoVNA takes freq in Hz, as ints
    start = int(1e9) # 1 GHz, as an int. 
    stop = int(3e9)  # 3 GHz, as an int.
    pts = 200

    # SCAN can change range and number of pts
    # get the frequency valuess (the Y Axis of the screen)
    freq = nvna.get_scan_frequencies(start, stop, pts)
    print(freq)
    # get the S11 data
    s11 = nvna.get_scan_s11(start, stop, pts)
    print(s11)
    # get the S21 data
    s21 = nvna.get_scan_s21(start, stop, pts)
    print(s21)

    # DATA gets the data on the screen
    # get the S11 data
    s11 = nvna.get_s11_data()
    print(s11)
    # get the S21 data
    s21 = nvna.get_s21_data()
    print(s21)

    nvna.resume() #resume 

    nvna.disconnect()


```

The requested frequencies are in the following format:
```python
bytearray(b'1000000 \r\n1020000 \r\n1040000 \r\n1060000 \r\n1080000 \r\n1100000 \r\n1120000 \r\n1140000 \r\n1160000 \r\n1180000 \r\n1200000 \r\n1220000 \r\n1240000 \r\n1260000 \r\n1280000 \r\n1300000 \r\n1320000 \r\n1340000 \r\n1360000 \r\n1380000 \r\n1400000 \r\n1420000 \r\n1440000 \r\n1460000 \r\n1480000 \r\n1500000 \r\n1520000 \r\n1540000 \r\n1560000 \r\n1580000 \r\n1600000 \r\n1620000 \r\n1640000 \r\n1660000 \r\n1680000 \r\n1700000 \r\n1720000 \r\n1740000 \r\n1760000 \r\n1780000 \r\n1800000 \r\n1820000 \r\n1840000 \r\n1860000 \r\n1880000 \r\n1900000 \r\n1920000 \r\n1940000 \r\n1960000 \r\n1980000 \r\n2000000 \r\n2020000 \r\n2040000 \r\n2060000 \r\n2080000 \r\n2100000 \r\n2120000 \r\n2140000 \r\n2160000 \r\n2180000 \r\n2200000 \r\n2220000 \r\n2240000 \r\n2260000 \r\n2280000 \r\n2300000 \r\n2320000 \r\n2340000 \r\n2360000 \r\n2380000 \r\n2400000 \r\n2420000 \r\n2440000 \r\n2460000 \r\n2480000 \r\n2500000 \r\n2520000 \r\n2540000 \r\n2560000 \r\n2580000 \r\n2600000 \r\n2620000 \r\n2640000 \r\n2660000 \r\n2680000 \r\n2700000 \r\n2720000 \r\n2740000 \r\n2760000 \r\n2780000 \r\n2800000 \r\n2820000 \r\n2840000 \r\n2860000 \r\n2880000 \r\n2900000 \r\n2920000 \r\n2940000 \r\n2960000 \r\n2980000 \r\n3000000 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r\n0 \r')
```
These frequencies represent where in the frequency range the measurements have been taken, and are returned in `kHz`. That is, the last reading before the padding 0-s start is '3000000'. This value is actually '3000000e3', or 3 GHz, not 3 MHz. 


Returned S11 and S21 data are in the format:
```python
bytearray(b'0.414528 0.623509 \r\n0.512547 0.542835 \r\n0.552637 0.489537 \r\n0.602180 0.444314 \r\n0.674851 0.374883 \r\n0.721209 0.316875 \r\n0.770192 0.216239 \r\n0.790564 0.140702 \r\n0.804490 0.037844 \r\n0.802676 -0.086580 \r\n0.784412 -0.188284 \r\n0.757563 -0.260674 \r\n0.718249 -0.342237 \r\n0.664428 -0.416341 \r\n0.617326 -0.480844 \r\n0.568474 -0.533208 \r\n0.492809 -0.581321 \r\n0.460760 -0.616593 \r\n0.384558 -0.668559 \r\n0.314043 -0.682421 \r\n0.245858 -0.719574 \r\n0.194356 -0.714597 \r\n0.118920 -0.738018 \r\n0.066108 -0.737820 \r\n0.010847 -0.744120 \r\n-0.045027 -0.754767 \r\n-0.101323 -0.761777 \r\n-0.172184 -0.763956 \r\n-0.248799 -0.752455 \r\n-0.322770 -0.734302 \r\n-0.386569 -0.712150 \r\n-0.465589 -0.678363 \r\n-0.538067 -0.640787 \r\n-0.614912 -0.575165 \r\n-0.675761 -0.518579 \r\n-0.719431 -0.459212 \r\n-0.762334 -0.381576 \r\n-0.804731 -0.287837 \r\n-0.828170 -0.205799 \r\n-0.847075 -0.126603 \r\n-0.857135 -0.029673 \r\n-0.849052 0.066982 \r\n-0.834792 0.182195 \r\n-0.805081 0.263328 \r\n-0.756838 0.355655 \r\n-0.699059 0.442736 \r\n-0.627638 0.513114 \r\n-0.526945 0.592252 \r\n-0.424149 0.632364 \r\n-0.313906 0.655601 \r\n-0.181712 0.653672 \r\n-0.125724 0.615638 \r\n-0.053355 0.591899 \r\n0.009786 0.579131 \r\n0.073450 0.570709 \r\n0.166064 0.538408 \r\n0.250542 0.481270 \r\n0.324851 0.387106 \r\n0.371485 0.280715 \r\n0.392284 0.164942 \r\n0.372584 0.048407 \r\n0.321884 -0.054561 \r\n0.248533 -0.125397 \r\n0.153565 -0.178265 \r\n0.061536 -0.194453 \r\n-0.013059 -0.182995 \r\n-0.085104 -0.155251 \r\n-0.138454 -0.125033 \r\n-0.184962 -0.078549 \r\n-0.225650 -0.029733 \r\n-0.239032 0.054426 \r\n-0.229694 0.126419 \r\n-0.195660 0.184412 \r\n-0.150762 0.222993 \r\n-0.089336 0.251350 \r\n-0.039771 0.261744 \r\n0.009027 0.261116 \r\n0.065524 0.260008 \r\n0.110400 0.234943 \r\n0.140959 0.225260 \r\n0.193066 0.202232 \r\n0.260522 0.159201 \r\n0.309473 0.106962 \r\n0.343722 0.029135 \r\n0.362852 -0.053262 \r\n0.367468 -0.136931 \r\n0.371292 -0.227675 \r\n0.363786 -0.314572 \r\n0.318734 -0.411707 \r\n0.260611 -0.519830 \r\n0.184881 -0.579277 \r\n0.113375 -0.670024 \r\n-0.006515 -0.709672 \r\n-0.088562 -0.746757 \r\n-0.209147 -0.763733 \r\n-0.318236 -0.751811 \r\n-0.424684 -0.736606 \r\n-0.525702 -0.713903 \r\n-0.608816 -0.662751 \r\n-0.673664 -0.612937 \r\n-0.737695 -0.554410 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r\n0.000000 0.000000 \r')
```

The last value before the padding is ` -0.737695 -0.554410`. The first number is the `real` part of the signal, and the second number is the `imaginary` part of the signal. All signals are returned in two parts for each measurement. 


### Saving Screen Images

`capture()` reads the screen framebuffer (RGB565, 2 bytes per pixel) and `decode_capture()` turns it into a list of `(r, g, b)` pixels you can hand to Pillow. The capture path reads the binary frame by its known byte count (width × height × 2), strips the leading command echo and the trailing prompt, and leaves the buffer clean for the next command. This avoids the truncation/wrap and color-scramble that a text-style prompt-framed read produces on a binary payload.

```python
from PIL import Image
from nvnapython import nanoVNA

nvna = nanoVNA()
nvna.autoconnect()

width, height = nvna.get_screen_size()        # e.g. 800x480 on the F V2
raw = nvna.capture(width, height)             # exactly width*height*2 image bytes
nvna.disconnect()

pixels = nvna.decode_capture(raw, width, height)
img = Image.new("RGB", (width, height))
img.putdata(pixels)
img.save("screen.png")
```

A complete version with command-line options is `examples/screen_capture.py`. Note: if the device is interrupted mid-capture it can become briefly unresponsive (Windows may report "a device attached to the system is not functioning") — power-cycle the NanoVNA to recover, and avoid hammering captures back-to-back.

### Plotting Data with Matplotlib

The plotting examples scan S11 (or S21) over a band and plot magnitude (dB), phase, and a complex-plane (Smith-style) scatter, or build a waterfall over repeated scans. They require the `[plotting]` extra. See `examples/plotting_scan.py`, `examples/plotting_waterfall_static.py`, and `examples/plotting_waterfall_realtime.py`.

A note on speed for the realtime waterfall: the update rate is bounded by how fast the device can produce a sweep, not by the example code. A 150-point S11 sweep takes on the order of 1–2 seconds on the F V2 (a VNA makes a complex magnitude-and-phase measurement at every point), so the plot updates every couple of seconds. Lower `--points` for a faster refresh at the cost of frequency resolution.

```python
import numpy as np
from nvnapython import nanoVNA

nvna = nanoVNA()
nvna.autoconnect()
nvna.pause()
raw = nvna.get_scan_s11(int(1e9), int(3e9), 200)   # outmask 2
nvna.resume()
nvna.disconnect()

# parse real/imag pairs (keep genuine zero samples so the freq axis stays aligned)
text = bytes(raw).decode("utf-8", errors="replace")
reals, imags = [], []
for line in text.replace("\r\n", "\n").split("\n"):
    parts = line.split()
    if len(parts) >= 2:
        try:
            reals.append(float(parts[0])); imags.append(float(parts[1]))
        except ValueError:
            continue
mag = np.hypot(reals, imags)
mag_db = 20 * np.log10(np.where(mag > 0, mag, 1e-12))
```

### Saving SCAN Data to CSV

`examples/save_raw_to_csv.py` saves frequency / real / imaginary, and `examples/save_scan_csv.py` adds derived magnitude (dB) and phase (deg) columns.

```python
import csv, numpy as np
from nvnapython import nanoVNA

nvna = nanoVNA()
nvna.autoconnect()
nvna.pause()
raw = nvna.get_scan_s11(int(1e9), int(3e9), 200)
nvna.resume()
nvna.disconnect()

# ... parse into freq/real/imag arrays (see example) ...
with open("s11.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Frequency_Hz", "S11_Real", "S11_Imaginary"])
    # w.writerow([...]) per point
```

### Accessing the NanoVNA Directly

`command()` is a passthrough: it sends an arbitrary command string straight to the device and returns the cleaned reply, with **no** library-side error checking. Use it for device features the library does not wrap yet, or to experiment.

```python
# send a raw command exactly as the device expects it
raw = nvna.command("scan 150000 250000000 200 2")
print(raw)
nvna.resume()
```


## List of NanoVNA Commands and their Library Commands

The library wraps the documented NanoVNA serial commands. Each device command and its library method(s) are listed below. Alias methods (e.g. `get_*`) are provided for readability and are not exhaustive. Argument validation is performed against the selected model envelope where applicable.

> **Note:** the exact command set and argument ranges vary by model and firmware. The mappings below were confirmed against the NanoVNA-F V2 (firmware 0.3.0). Always cross-check with your device's `help` output and official documentation.


UPDATING TABLE BC FORMAT is GROSS







## Additional Library Functions for Advanced Use

### `command`

```python
# send any command string directly to the device, no validation, cleaned reply returned
raw = nvna.command("info")
```

`command()` bypasses all library-side argument checking. It is the right tool for commands not yet wrapped, for experimentation, and for reproducing exact device behavior — but you are responsible for a valid command string.

Other library-side helpers (no device traffic): `set_verbose` / `get_verbose`, `set_error_byte_return` / `get_error_byte_return`, `set_serial_timeout` / `get_serial_timeout`, `set_serial_poll_interval` / `get_serial_poll_interval`, the model/bounds setters and getters listed under [Selecting a Device Model](#selecting-a-device-model), and `decode_capture` / `capture_to_pixels` for image decoding.


## Library Development

The package layout, optional-dependency split (`plotting`, `test`), and the `hardware` pytest marker are defined in `pyproject.toml`. To work on the library:

```bash
# clone, then from the nvnapython project directory:
pip install -e ".[plotting,test]"
python -m pytest                 # hardware tests self-skip without a device
```

The per-command methods live in mixin modules under `src/nvnapython/_commands/` and are composed onto the `nanoVNA` class in `core.py`. Adding a command usually means adding a method to the appropriate mixin and a command-construction test (assert the exact command string on the happy path; assert nothing is sent on the validation-error path). Parsing changes should be checked against the frozen captures in `tests/readme_capture.md` via the parsing tests.

A `docs` site for the library may be added later for stable releases.


## Notes for Beginners

### Vocab Check

* **VNA (Vector Network Analyzer):** measures both magnitude and phase of how an RF network reflects (S11) and transmits (S21) signals across a frequency range.
* **S-parameters:** scattering parameters describing a network's ports. S11 is the reflection at port 1 (return loss); S21 is the transmission from port 1 to port 2 (insertion loss/gain).
* **Sweep:** stepping the source across a frequency range and measuring at each point.
* **Calibration standards:** known Short, Open, Load, and Thru references used to remove the test setup's own errors from measurements (see [Calibration Setup](#calibration-setup)).
* **Smith chart:** a polar plot of complex reflection coefficient, the standard way to visualize S11.

### VNA vs. SA vs. LNA vs. SNA vs. SDR vs Signal Generator

* **VNA** — vector network analyzer: measures S-parameters (magnitude **and** phase) of a network. This is what the NanoVNA is.
* **SA** — spectrum analyzer: measures signal power vs frequency (magnitude only). The tinySA is an SA.
* **SNA** — scalar network analyzer: like a VNA but magnitude only (no phase).
* **LNA** — low-noise amplifier: a component, not an instrument; amplifies weak signals with minimal added noise.
* **SDR** — software-defined radio: a receiver/transmitter whose processing is done in software.
* **Signal generator** — produces a defined output signal; some SAs (like the tinySA) include one.

### Calibration Setup

A NanoVNA measures the network *plus* its own cables/connectors. Calibration removes the setup's contribution. The common procedure is **SOLT** — Short, Open, Load, Thru — where you attach each known standard in turn and the device computes the correction. `examples/solt_calibration.py` walks through it interactively. Calibrate over the same sweep range you intend to measure, and re-calibrate if you change cables or range. Meaningful S21 measurements require a calibration that includes the Thru step.

### Some General NanoVNA Notes

* The device performs a live sweep continuously; `pause()` before reading data for a stable result, and `resume()` afterward so the screen isn't left frozen.
* The `reset` command can drop the USB connection mid-read; handle it accordingly.
* An interrupted binary capture can leave the device briefly unresponsive — power-cycle to recover.
* Different models have different frequency ranges, point counts, and slot counts; select the right model envelope so the library's checks match your hardware.


## FAQs

### How should I be using this?

For scripting and automating measurements with a NanoVNA from Python — repeated scans, logging to CSV, screen capture, calibration, and integrating measurements into larger workflows. Start with the `examples/` directory. Read the official device documentation before driving the hardware experimentally.

### Will this be made into a REAL Python library I can import into my project?

It is already available on PyPI as `nvnapython` (`pip install nvnapython`) and importable as `from nvnapython import nanoVNA`.

### How often is this library updated?

As development continues and as device behavior is confirmed on hardware. The GitHub repository tracks the working version. Stable versions are released to PyPI. Zenodo get periodic updates for research purposes.


## References

UPDATE FOR NEW DOCS and website updates


## Licensing

This project is licensed under the GNU General Public License v2.0. See the [LICENSE](LICENSE) file for details.