# nvnapython/tests/fakes.py
#
# Test doubles for the nvnapython mock tests.
#
# Import it in tests as:
#     from tests.fakes import FakePort
#
# (Matches the project's testpaths = ["tests"] layout. If you ever run tests as
#  an installed package, add a tests/__init__.py so the import resolves either
#  way.)

class FakePort:
    """Minimal pyserial-Serial stand-in, PRELOADED with the raw bytes the
    device would emit.

    Construct it with the exact frame a real NanoVNA returns -- echoed command,
    payload, then the doubled trailing-space prompt -- and the library's read
    path (get_serial_return / nanoVNA_serial) consumes it through the normal
    in_waiting / read() interface, exactly as against hardware:

        # real F V2 framing: '<cmd>\\r\\n<payload>\\r\\nch> \\r\\nch> '
        port = FakePort(b"version\\r\\n0.3.0\\r\\nch> \\r\\nch> ")

    The framing is supplied BY THE TEST (these byte strings are verbatim
    captures from tests/readme_capture.md), so this class stays framing-agnostic
    -- it just dispenses whatever bytes it was given and logs what was written.

    Attributes the test suite relies on:
        _buf        : the readable byte buffer (tests set/read it directly)
        written     : list of bytes objects the library wrote, in order
        _reset_in   : count of reset_input_buffer() calls
        _reset_out  : count of reset_output_buffer() calls
    """

    def __init__(self, payload=b""):
        self.is_open = True
        self.timeout = 1
        self.port = "FAKE"
        self._buf = bytearray(payload)   # bytes waiting to be read by the library
        self.written = []                # log of everything the library wrote
        self._reset_in = 0
        self._reset_out = 0

    # ---- pyserial-compatible API --------------------------------------

    @property
    def in_waiting(self):
        return len(self._buf)

    def read(self, size=1):
        # _buf may be assigned directly as bytes by a test, so slice + reassign
        # rather than mutating in place (bytes has no item deletion).
        out = bytes(self._buf[:size])
        self._buf = self._buf[size:]
        return out

    def read_until(self, expected=b"\n", size=None):
        idx = bytes(self._buf).find(expected)
        if idx == -1:
            out = bytes(self._buf)
            self._buf = self._buf[:0]
            return out
        end = idx + len(expected)
        out = bytes(self._buf[:end])
        self._buf = self._buf[end:]
        return out

    def readline(self):
        return self.read_until(b"\n")

    def write(self, data):
        self.written.append(bytes(data))
        return len(data)

    def reset_input_buffer(self):
        self._reset_in += 1

    def reset_output_buffer(self):
        self._reset_out += 1

    def flush(self):
        pass

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False