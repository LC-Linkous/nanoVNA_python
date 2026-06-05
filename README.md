# nanoVNA_python (nvnapython)

# UNDER CONSTUCTION 

An **UNOFFICIAL** Python API for the NanoVNA series of vector network analyzers.

This library shares its architecture with the
[tinySA_python (tsapython)](https://github.com/LC-Linkous/tinySA_python) library:
shared serial/console state lives in `core.py`, and per-command methods are
organized into mixin classes under `_commands/`, composed onto the `nanoVNA`
class.

> **Note:** This is a work in progress and is **not** ready for a release.

## Install (local / editable)

```bash
pip install -e .
# with plotting extras (numpy, matplotlib, pillow):
pip install -e ".[plotting]"
# with test extras:
pip install -e ".[test]"
```

## Quick start

```python
from nvnapython import nanoVNA

nvna = nanoVNA()
nvna.set_verbose(True)
nvna.set_error_byte_return(True)

found, connected = nvna.autoconnect()
if connected:
    print(nvna.info())
    data = nvna.get_scan_s11(int(1e9), int(2e9), 101)  # S11, outmask 2
    nvna.resume()
    nvna.disconnect()
```

## Testing

```bash
pytest                  # all hardware-free tests
pytest -m "not hardware" # explicit: skip hardware
pytest -m hardware       # requires a connected NanoVNA
```
