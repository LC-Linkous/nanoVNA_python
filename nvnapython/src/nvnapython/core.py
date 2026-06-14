#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './src/nvnapython/core.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   NOTE: this library shares its architecture with the tinySA_python (tsapython) library.
#   The tinySA library was written first; the NanoVNA device specifics were adapted from it.
#   The two devices look similar and share a serial/console framing ('ch>' prompt), but they
#   are different instruments made by different people, with different command sets.
#
#   references:
#       https://github.com/ttrftech/NanoVNA  (console command lineage)
#       NanoVNA-F / NanoVNA-H firmware console help output
#
#   The per-command methods live in mixin classes under ./_commands/ and are composed onto the
#   nanoVNA class below. core.py holds shared state, serial management, and reusable helpers.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import serial
import serial.tools.list_ports  # COM search method wants full path
import re
import time  # noqa: F401  (used by binary read helper)

from .constants import (
    MODELS,
    DEFAULT_MODEL,
    SERIAL_TIMEOUT_S,
    SERIAL_POLL_INTERVAL_S,
)

from ._commands.acquisition import AcquisitionMixin
from ._commands.calibration import CalibrationMixin
from ._commands.markers_traces import MarkersTracesMixin
from ._commands.display_ui import DisplayUIMixin
from ._commands.presets_config import PresetsConfigMixin
from ._commands.system_info import SystemInfoMixin


class nanoVNA(
    AcquisitionMixin,
    CalibrationMixin,
    MarkersTracesMixin,
    DisplayUIMixin,
    PresetsConfigMixin,
    SystemInfoMixin,
):
    def __init__(self, parent=None):
        # serial port
        self.ser = None

        # message feedback
        self.verboseEnabled = False
        self.returnErrorByte = False

        # serial read tuning (see constants.py for the meaning of each)
        self.serialTimeout = SERIAL_TIMEOUT_S
        self.serialPollInterval = SERIAL_POLL_INTERVAL_S

        # VARS BELOW HERE are seeded from the per-model envelope in constants.py.
        # select_existing_device() swaps in a different model's values; the
        # set_* override methods below tweak individual bounds for debug / clones.

        # seed library-side device bounds from the default model
        self._apply_model(MODELS[DEFAULT_MODEL])
        self.deviceModel = DEFAULT_MODEL

######################################################################
# Error and information printout
# set/get_verbose()  - set how detailed the error printouts are
# print_message()  - deal with the bool in one place
######################################################################

    def set_verbose(self, verbose=False):
        self.verboseEnabled = verbose

    def get_verbose(self):
        return self.verboseEnabled

    def print_message(self, msg):
        if self.verboseEnabled == True:
            print(msg)

######################################################################
# Explicit error return
# set_error_byte_return()  - set if explicit b'ERROR' is returned
# get_error_byte_return()  - get the return mode True/False
# error_byte_return()  - return 'ERROR' message or empty.
######################################################################

    def set_error_byte_return(self, errByte=False):
        self.returnErrorByte = errByte

    def get_error_byte_return(self):
        return self.returnErrorByte

    def error_byte_return(self):
        if self.returnErrorByte == True:
            return bytearray(b'ERROR')
        else:
            return bytearray(b'')  # the default

######################################################################
# Set Device Params
#   Library specific functions. These set the boundaries & features for
#   error checking in the library
#
# WARNING: these DO NOT change the settings on the DEVICE. just the library.
######################################################################

    def _apply_model(self, model_dict):
        # Internal: copy a per-model envelope (from constants.MODELS) into the
        # instance attributes the validation code reads. Kept in one place so
        # __init__ and select_existing_device stay in sync.
        self.maxPoints = model_dict["max_points"]
        self.pointEndInclusive = model_dict["point_end_inclusive"]
        self.minVNADeviceFreq = model_dict["min_freq_hz"]
        self.maxVNADeviceFreq = model_dict["max_freq_hz"]
        self.screenWidth = model_dict["screen_width"]
        self.screenHeight = model_dict["screen_height"]
        self.numMarkers = model_dict["num_markers"]
        self.numTraces = model_dict["num_traces"]
        self.numCalSlots = model_dict["num_cal_slots"]
        self.numPresetSlots = model_dict["num_preset_slots"]

    def select_existing_device(self, nanoVNAModel):
        # Seed the library-side error-checking bounds from a known model preset
        # in constants.MODELS (e.g. "NANOVNA_F_V2", "NANOVNA_H4").
        # This sets the LIBRARY bounds ONLY; it does not talk to the device.
        # To add a model, add an entry to constants.MODELS -- no code change here.
        model = str(nanoVNAModel).upper()

        if model in MODELS:
            self._apply_model(MODELS[model])
            self.deviceModel = model
            self.print_message("device bounds set for " + model)
            return True

        self.print_message("ERROR: '" + str(nanoVNAModel) +
                            "' is not a known preset. Known models: " +
                            ", ".join(sorted(MODELS.keys())) + ". bounds unchanged.")
        return False

    def get_device_model(self):
        # returns the currently selected model preset name
        return self.deviceModel

    def list_known_models(self):
        # returns the list of model names available in constants.MODELS
        return sorted(MODELS.keys())

    def load_custom_config(self, configFile):
        # TODO: for loading modified or other devices working on the same firmware
        pass

######################################################################
# Direct overrides
#   These are used during DEBUG or when device state/model is already known.
#   Not recommended unless you are sure of the device state and which
#   settings each device has.
# WARNING: these DO NOT change the settings on the DEVICE. just the library.
######################################################################

    # error check boundaries
    def set_min_device_freq(self, f):
        self.minVNADeviceFreq = float(f)

    def get_min_device_freq(self):
        return self.minVNADeviceFreq

    def set_max_device_freq(self, f):
        self.maxVNADeviceFreq = float(f)

    def get_max_device_freq(self):
        # NOTE: original library had a typo here (get_max_devicefreq).
        return self.maxVNADeviceFreq

    def set_max_points(self, n):
        self.maxPoints = int(n)

    def get_max_points(self):
        return self.maxPoints

    def set_screen_size(self, width, height):
        self.screenWidth = int(width)
        self.screenHeight = int(height)

    def get_screen_size(self):
        return self.screenWidth, self.screenHeight

    # serial read tuning
    def set_serial_timeout(self, seconds):
        # max idle seconds to wait for the 'ch>' prompt during a read
        self.serialTimeout = float(seconds)

    def get_serial_timeout(self):
        return self.serialTimeout

    def set_serial_poll_interval(self, seconds):
        # sleep between in_waiting checks while awaiting the next chunk
        self.serialPollInterval = float(seconds)

    def get_serial_poll_interval(self):
        return self.serialPollInterval

######################################################################
# Serial management and message processing
######################################################################

    def autoconnect(self, timeout=1):
        # attempt to autoconnect to a detected port.
        # returns: found_bool, connected_bool
        #
        # NOTE: NanoVNA and tinySA devices both commonly enumerate under the
        # STM32 virtual COM VID:PID 0483:5740, so VID/PID ALONE cannot tell them
        # apart. Some NanoVNA variants enumerate differently; the set below is a
        # starting list. If your device isn't detected, connect() to the port
        # explicitly, or add its VID/PID here.
        accepted_vid_pid = [
            (0x0483, 0x5740),   # STM32 VCP (NanoVNA-H, NanoVNA-F, tinySA, ...)
        ]

        ports = serial.tools.list_ports.comports()
        for port_info in ports:
            port = port_info.device
            self.print_message(f"Checking port: {port}")
            vid = port_info.vid
            pid = port_info.pid

            if vid is None:
                continue
            if (vid, pid) in accepted_vid_pid:
                self.print_message(f"NanoVNA-class device identified at port: {port}")
                connected_bool = self.connect(port, timeout)
                return True, connected_bool

        return False, False  # no device found, not connected

    def connect(self, port, timeout=1):
        # attempt connection to provided port.
        # returns: True if successful, False otherwise
        # Single explicit attempt: open the port, succeed or fail, report.
        try:
            self.ser = serial.Serial(port=port, timeout=timeout)
            return True
        except Exception as err:
            self.ser = None
            self.print_message("ERROR: cannot open port at " + str(port))
            self.print_message(err)
            return False

    def disconnect(self):
        # Close the serial port and release the handle.
        # Tolerant of being called when never connected or already closed, so
        # cleanup paths (e.g. test teardown, error handlers) can always call it
        # without risking an exception that leaves the port held open.
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception as err:
                self.print_message("WARNING: error while closing serial: " + str(err))
            finally:
                self.ser = None

    def nanoVNA_serial(self, writebyte, printBool=False, pts=None):
        # write out to serial, get message back, clean up, return.
        #
        # The pts argument is accepted for signature-compatibility with the
        # tsapython binary path and for future binary-frame reads. NanoVNA
        # scan/data responses are TEXT (whitespace-separated values terminated
        # by the 'ch>' prompt), so the text path is used regardless for now.

        # clear INPUT buffer
        self.ser.reset_input_buffer()
        # clear OUTPUT buffer
        self.ser.reset_output_buffer()

        self.ser.write(bytes(writebyte, 'utf-8'))
        msgbytes = self.get_serial_return()
        msgbytes = self.clean_return(msgbytes)

        # Post-read straggler drain: belt-and-suspenders companion to the
        # doubled-prompt handling in get_serial_return. On fast back-to-back
        # commands, any residual tail bytes (e.g. the trailing space/newline
        # after the second 'ch>') that arrive just after the read could
        # otherwise sit in the buffer and be raced by the NEXT command. We sip
        # them here so each call leaves the input buffer clean. This is cheap and
        # bounded; if nothing is waiting it does effectively nothing.
        try:
            if self.ser.in_waiting:
                self.ser.read(self.ser.in_waiting)
        except Exception:
            pass

        if printBool == True:
            print(msgbytes)  # overrides verbose for debug

        return msgbytes

    def nanoVNA_serial_no_wait(self, writebyte, settle_s=0.6):
        # Write a command but do NOT wait for a 'ch>' prompt.
        #
        # WHY THIS EXISTS: a few commands write to FLASH (notably 'save', and on
        # some firmware 'saveconfig'). During the flash write the NanoVNA-F V2/V3
        # firmware stops servicing the serial interface and NEVER sends the 'ch>'
        # prompt back for that command -- confirmed on hardware: 'save 0' returns
        # only its echo ('save 0\r\n') and no prompt, even after 30 s. Routing
        # 'save' through the normal nanoVNA_serial (which waits for the prompt)
        # therefore always hits the full serial timeout, and the next command can
        # collide with the still-recovering device and block the port on Windows.
        #
        # So for these commands we write, wait a fixed settle for the flash write
        # to finish, drain any bytes the device did emit (the echo, and possibly a
        # late prompt on firmware that does recover), and return WITHOUT awaiting a
        # prompt. The command still executes on the device; we simply don't depend
        # on an acknowledgement that may never come.
        #
        # NOTE: because the device does not acknowledge, the return here is only
        # whatever bytes happened to arrive within the settle window -- it is NOT a
        # reliable success signal. To confirm a save persisted, power-cycle and
        # 'recall' the slot.
        import time
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(bytes(writebyte, 'utf-8'))

        time.sleep(settle_s)
        collected = bytearray()
        try:
            if self.ser.in_waiting:
                collected += self.ser.read(self.ser.in_waiting)
        except Exception:
            pass
        # one more brief drain pass in case a tail arrives just after
        try:
            time.sleep(self.serialPollInterval)
            if self.ser.in_waiting:
                collected += self.ser.read(self.ser.in_waiting)
        except Exception:
            pass
        return self.clean_return(bytearray(collected))

    def get_serial_return(self):
        # Read the device reply, accumulating until the 'ch>' prompt arrives.
        #
        # The device terminates every reply with the prompt 'ch>'. USB CDC
        # delivers data in chunks with gaps between them, so 'in_waiting'
        # momentarily reading 0 does NOT mean the reply is complete -- it just
        # means the next chunk hasn't landed yet. We therefore loop until the
        # accumulated buffer ENDS WITH the prompt, with a wall-clock timeout so a
        # missing prompt (or a disconnect, e.g. after reset) cannot hang forever.
        #
        # DOUBLED-PROMPT TAIL (firmware-dependent): current NanoVNA-F V2 firmware
        # emits the prompt TWICE at the end of every reply -- 'ch> \r\nch> ' (see
        # tests/readme_capture.md, captured verbatim). If we stop the instant the
        # FIRST 'ch>' appears, the bytes of the SECOND prompt are still arriving
        # and get left in the OS input buffer. For SLOW replies (a 1.4s scan)
        # that tail lands harmlessly before the next command. But for FAST,
        # instant-returning commands fired back to back (version, sweep, data,
        # the help dump), the next nanoVNA_serial's reset_input_buffer() races
        # those leftover bytes -- producing the intermittent empty/truncated
        # reads seen on the help probe and in rapid command loops.
        #
        # FIX (confirmed on hardware via diagnose_fastcmd.py): once the prompt is
        # seen, do a SHORT bounded settle to absorb a possible second/doubled
        # prompt, then return. This consumes the whole tail on doubled-prompt
        # firmware WITHOUT requiring two prompts -- so single-prompt firmware (or
        # a future change) still returns promptly via the settle timeout instead
        # of hanging. The companion post-read drain in nanoVNA_serial mops up any
        # straggler bytes that arrive after the settle window.
        #
        # buffer reading lineage:
        #   https://groups.io/g/nanovna-users (screen capture / serial read threads)

        import time
        prompt = b'ch>'
        buffer = bytes()
        deadline = time.time() + self.serialTimeout

        while True:
            waiting = self.ser.in_waiting
            if waiting > 0:
                buffer += self.ser.read(waiting)
                # The full reply is done once the prompt is at the end. The
                # device emits the prompt as 'ch> ' WITH A TRAILING SPACE (and
                # sometimes a trailing '\r\n'), so a bare buffer.endswith(b'ch>')
                # never matches. Strip trailing whitespace before testing.
                if buffer.rstrip().endswith(prompt):
                    # Prompt seen. This firmware usually sends a SECOND prompt
                    # right behind it; give that tail a brief, bounded chance to
                    # arrive and consume it, so nothing is left in the buffer for
                    # the next command to race. We do NOT require a second prompt
                    # -- if none comes within the settle window, we return what we
                    # have (handles single-prompt firmware without a long stall).
                    settle_deadline = time.time() + max(self.serialPollInterval * 5,
                                                        0.05)
                    while time.time() < settle_deadline:
                        if self.ser.in_waiting:
                            buffer += self.ser.read(self.ser.in_waiting)
                            # if a full second prompt has now landed, we're done
                            if buffer.count(prompt) >= 2:
                                break
                        else:
                            time.sleep(self.serialPollInterval)
                    break
                # reset the deadline whenever we make progress
                deadline = time.time() + self.serialTimeout
            else:
                # no data right now; the device may still be sending. Wait a
                # beat and re-check rather than busy-spinning or bailing early.
                if time.time() > deadline:
                    self.print_message("WARNING: serial read timed out waiting for prompt")
                    break
                time.sleep(self.serialPollInterval)

        return bytearray(buffer)

    def get_binary_return(self, expected_bytes, timeout_s=None, start_timeout_s=None):
        # Read a fixed-length BINARY reply (e.g. the 'capture' framebuffer) off
        # the port, WITHOUT the text 'ch>'-prompt framing.
        #
        # WHY THIS IS SEPARATE FROM get_serial_return: binary frames have no line
        # framing and CAN contain the bytes 'ch>' or '>' mid-payload (they're
        # just pixel values). Scanning for the prompt -- the way the text read
        # does -- can therefore cut a binary frame short at a coincidental byte
        # run, or (with the prompt-settle) stop before the whole frame has
        # streamed in. The reliable completion signal for a binary frame is its
        # KNOWN LENGTH, so we read until expected_bytes have arrived.
        #
        # NO IDLE GIVEUP DURING THE STREAM: the framebuffer streams over USB CDC
        # in many small chunks (measured: an 800x480x2 = 768000-byte frame
        # arrives in ~474 chunks over ~2.5s). We must NOT treat a brief idle
        # WITHIN the transfer as end-of-data, or the frame truncates. Stop
        # conditions are: (a) we have expected_bytes, (b) NO data ever started
        # arriving within start_timeout_s (device not streaming -- fail fast
        # instead of waiting the full cap), or (c) a generous absolute timeout
        # (a stalled/dead transfer mid-stream). Returns exactly expected_bytes on
        # success, or a SHORT bytearray (with a warning) otherwise.
        import time
        if timeout_s is None:
            # generous absolute cap that scales with the configured serial
            # timeout. At the default serialTimeout (5s) this is ~30s; the real
            # transfer is a couple of seconds, so it only fires on a stalled or
            # dead transfer mid-stream.
            timeout_s = self.serialTimeout * 6
        if start_timeout_s is None:
            # how long to wait for the FIRST byte before giving up. If the device
            # didn't begin streaming, there's no point waiting out the full cap.
            start_timeout_s = self.serialTimeout

        buffer = bytearray()
        start = time.time()
        while len(buffer) < expected_bytes:
            waiting = self.ser.in_waiting
            if waiting:
                buffer += self.ser.read(waiting)
            else:
                elapsed = time.time() - start
                if len(buffer) == 0 and elapsed > start_timeout_s:
                    self.print_message(
                        "WARNING: binary read got no data within " +
                        str(start_timeout_s) + "s (device not streaming?)")
                    break
                if elapsed > timeout_s:
                    self.print_message(
                        "WARNING: binary read timed out with " + str(len(buffer)) +
                        "/" + str(expected_bytes) + " bytes after " +
                        str(timeout_s) + "s")
                    break
                time.sleep(self.serialPollInterval)

        # The device appends a 'ch> ' prompt after the frame; if we over-read
        # into it, trim back to exactly the image bytes.
        if len(buffer) >= expected_bytes:
            return bytearray(buffer[:expected_bytes])
        return buffer   # short read; caller decides how to handle

    def clean_return(self, data):
        # Normalize the raw device reply into just the payload.
        #
        # The device frames every reply as:
        #     <echoed command>\r\n<payload>\r\nch> \r\nch>
        # i.e. the command is echoed first, then the payload, then the console
        # prompt 'ch>' -- which on this firmware appears WITH A TRAILING SPACE
        # and often TWICE ('ch> \r\nch> '). The old logic stripped only a single
        # bare 'ch>' at the very end, so the real trailing prompt block survived.
        #
        # 1) strip the echoed command: up to and including the first '\r\n'.
        # 2) strip the trailing prompt block: remove any run of trailing 'ch>'
        #    prompts (with surrounding whitespace), then the '\r\n' that
        #    separated the payload from that block.
        first_newline_index = data.find(b'\r\n')
        if first_newline_index != -1:
            data = data[first_newline_index + 2:]

        # drop a trailing run of 'ch>' prompts and their surrounding whitespace
        head = data
        while True:
            stripped = head.rstrip()
            if stripped.endswith(b'ch>'):
                head = stripped[:-3]
                continue
            break

        # drop the single '\r\n' that separated the payload from the prompt block
        if head.endswith(b'\r\n'):
            head = head[:-2]
        return head

######################################################################
# Reusable format checking functions
######################################################################

    def is_rgb24(self, hexStr):
        # check if the string matches the pattern 0xRRGGBB
        pattern = r"^0x[0-9A-Fa-f]{6}$"
        return bool(re.match(pattern, hexStr))

    def is_rgb565_hex(self, hexStr):
        # NanoVNA lcd() colors are 16-bit (RGB565) given as a 4-digit hex
        # string, e.g. 'F800' (red) or '07E0' (green). Accept with or without
        # an optional 0x prefix.
        pattern = r"^(0x)?[0-9A-Fa-f]{4}$"
        return bool(re.match(pattern, str(hexStr)))