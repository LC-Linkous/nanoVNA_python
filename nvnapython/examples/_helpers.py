#! /usr/bin/python3
"""
examples/_helpers.py

Small shared helpers for the nvnapython examples. Kept deliberately tiny and
dependency-free (stdlib only) so the examples stay copy-paste friendly.

The README notes that convert_s11_data_to_arrays was historically duplicated
per-example on purpose. This module is the "one shared copy" alternative; an
example that wants to stay self-contained can still inline the function.

All parsing here matches the REAL NanoVNA-F V2 framing confirmed on hardware:
  * scan/data payloads are whitespace-separated values, one record per line;
  * scan lines carry a TRAILING SPACE before the newline (the 'frequencies'
    command's lines do not) -- str.split() handles both transparently;
  * lines are CR/LF terminated.

NOTE: screen-capture BGR565 color decoding is NOT here -- it now lives in the
library itself (nanoVNA.decode_capture), so there is one source of that logic.
The screen_capture.py example calls nvna.decode_capture directly.
"""


def _decode(raw):
    """bytes/bytearray/str -> str, tolerant of None."""
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw).decode("utf-8", errors="replace")
    return str(raw)


def _records(raw):
    """Yield the non-empty whitespace-split records of a scan/data payload."""
    for line in _decode(raw).replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        yield line.split()


def convert_s11_data_to_arrays(raw):
    """
    Parse a 2-column (real, imag) payload -- e.g. `data 0` (S11) or
    `scan ... 2` (outmask 2) -- into two parallel lists (reals, imags).

    Lines that don't hold at least two float-parseable values are skipped, so a
    stray framing line won't crash the parse.
    """
    reals, imags = [], []
    for parts in _records(raw):
        if len(parts) < 2:
            continue
        try:
            re_, im_ = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        reals.append(re_)
        imags.append(im_)
    return reals, imags


def convert_frequencies_to_array(raw):
    """
    Parse a `frequencies` (or `scan ... 1`) payload into a list of ints (Hz).
    """
    freqs = []
    for parts in _records(raw):
        try:
            freqs.append(int(parts[0]))
        except (ValueError, IndexError):
            continue
    return freqs


def convert_scan_outmask7_to_arrays(raw):
    """
    Parse outmask-7 scan output (freq, s11_re, s11_im, s21_re, s21_im) into
    (freqs, s11_reals, s11_imags, s21_reals, s21_imags).

    Confirmed shape on hardware: 5 whitespace-separated values per line.
    """
    freqs = []
    s11r, s11i, s21r, s21i = [], [], [], []
    for parts in _records(raw):
        if len(parts) < 5:
            continue
        try:
            f = int(parts[0])
            a, b, c, d = (float(x) for x in parts[1:5])
        except ValueError:
            continue
        freqs.append(f)
        s11r.append(a); s11i.append(b)
        s21r.append(c); s21i.append(d)
    return freqs, s11r, s11i, s21r, s21i


def complex_to_db(reals, imags):
    """
    Convert (real, imag) reflection/transmission samples to magnitude in dB:
        20 * log10(|re + j*im|).
    Uses math only (no numpy) so the helper stays dependency-free. A magnitude
    of exactly 0 is reported as -inf-safe floor (-200 dB) rather than crashing.
    """
    import math
    out = []
    for re_, im_ in zip(reals, imags):
        mag = math.hypot(re_, im_)
        out.append(20.0 * math.log10(mag) if mag > 0 else -200.0)
    return out
