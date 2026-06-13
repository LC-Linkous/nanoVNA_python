#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/test_hardware.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Hardware-backed pytest tests. These REQUIRE a serial-connected NanoVNA device and are
#   skipped by default. Run them explicitly with:
#
#       pytest -m hardware
#
#   Run everything EXCEPT these with:
#
#       pytest -m "not hardware"   (or just `pytest`, which skips on no-connect)
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import pytest

pytestmark = pytest.mark.hardware


def test_info_nonempty(device):
    """A connected device returns non-empty info text."""
    info = device.info()
    assert info  # non-empty bytearray


def test_version_nonempty(device):
    """A connected device returns non-empty version text."""
    version = device.version()
    assert version


def test_scan_s11_returns_pairs(device):
    """
    A small S11 scan (outmask=2) returns whitespace-separated real/imag pairs,
    one pair per line. This is the substantive behavioral check for the NanoVNA
    data contract: scan output is TEXT pairs, not dBm scalars.
    """
    start = int(1e9)    # 1 GHz
    stop = int(2e9)     # 2 GHz
    pts = 51            # small, well under maxPoints

    device.pause()

    data_bytes = device.get_scan_s11(start, stop, pts)   # outmask 2
    assert data_bytes, "no S11 data returned"

    lines = [ln for ln in data_bytes.decode("utf-8").split("\n") if ln.strip()]
    assert len(lines) > 0, "no parseable lines in S11 data"

    # each non-empty line should hold at least a real/imag pair
    first = lines[0].split()
    assert len(first) >= 2, f"expected >=2 values per line, got: {lines[0]!r}"
    # values must be float-parseable
    float(first[0])
    float(first[1])

    device.resume()


def test_frequencies_after_scan(device):
    """frequencies() returns the freq list used by the last sweep."""
    device.pause()
    device.get_scan_s11(int(1e9), int(2e9), 51)
    freqs = device.frequencies()
    assert freqs, "no frequency data returned"
    freq_lines = [ln for ln in freqs.decode("utf-8").split("\n") if ln.strip()]
    assert len(freq_lines) > 0
    # first frequency should be int-parseable and near the start
    int(freq_lines[0].split()[0])
    device.resume()
