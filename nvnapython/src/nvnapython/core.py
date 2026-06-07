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
        try:
            self.ser = serial.Serial(port=port, timeout=timeout)
            return True
        except Exception as err:
            self.ser = None
            self.print_message("ERROR: cannot open port at " + str(port))
            self.print_message(err)
            # On Windows a PermissionError or a FileNotFoundError on a port that
            # DID enumerate almost always means the port is already open in
            # another process (another script/REPL still holding it, a serial
            # monitor, or a prior run that did not disconnect). Point at that.
            if isinstance(err, (PermissionError, FileNotFoundError)):
                self.print_message(
                    "HINT: the port was detected but could not be opened. It is "
                    "likely held by another process (another Python session, a "
                    "serial monitor, or a previous run that did not disconnect). "
                    "Close other programs using the port, or unplug/replug the "
                    "device, then try again.")
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

        if printBool == True:
            print(msgbytes)  # overrides verbose for debug

        return msgbytes

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
                # the full reply is done once the prompt is at the end
                if buffer.endswith(prompt):
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

    def clean_return(self, data):
        # removes 1) the echoed command up to and including the first '\r\n',
        # and 2) the trailing 'ch>' prompt.
        first_newline_index = data.find(b'\r\n')
        if first_newline_index != -1:
            # skip past the first '\r\n'
            data = data[first_newline_index + 2:]
        if data.endswith(b'ch>'):
            # remove the trailing prompt (4 bytes: the '\n' before it + 'ch>')
            data = data[:-4]
        return data

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
