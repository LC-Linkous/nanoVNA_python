#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/markers_traces.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class MarkersTracesMixin:
    def marker(self, ID=None, val=None, idx=None):
        # sets or dumps marker info.
        # usage:
        #   marker                       -> dump all active markers
        #   marker {ID}                  -> dump that marker's position
        #   marker {ID} on|off|peak      -> action on marker ID
        #   marker {ID} {index}          -> move marker ID to a point index
        # ID is 1..4. The frequency/index must be within the sweep range.
        # example return: ''
        #
        # FIXED (vs original): every set/action branch built the command as
        # str(val) + +'\r\n' -- the doubled '+' made a unary-plus on the '\r\n'
        # string, raising TypeError on EVERY marker set. All marker setting was
        # broken. Rewritten below with normal concatenation.

        accepted_IDs = [1, 2, 3, 4]
        accepted_vals = ["on", "off", "peak"]

        # no args -> dump all marker info
        if (ID is None) and (val is None) and (idx is None):
            writebyte = 'marker\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("returning active marker information")
            return msgbytes

        # ID must be a valid marker number
        try:
            id_int = int(ID)
        except (TypeError, ValueError):
            self.print_message("ERROR: marker() ID must be an integer 1..4")
            return self.error_byte_return()

        if id_int not in accepted_IDs:
            self.print_message("ERROR: marker() ID must be an integer 1..4")
            return self.error_byte_return()

        # ID only -> dump that marker
        if (val is None) and (idx is None):
            writebyte = 'marker ' + str(id_int) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("returning marker " + str(id_int) + " information")
            return msgbytes

        # ID + index (no action) -> set marker position by point index
        if (val is None) and (idx is not None):
            try:
                idx_int = int(idx)
            except (TypeError, ValueError):
                self.print_message("ERROR: marker() index must be an integer")
                return self.error_byte_return()
            # README: idx is a point between 0 and the device's point limit
            # (commonly 0..201). Bound against maxPoints to catch obvious errors.
            if not (0 <= idx_int <= self.maxPoints):
                self.print_message("ERROR: marker() index must be 0.." + str(self.maxPoints))
                return self.error_byte_return()
            writebyte = 'marker ' + str(id_int) + ' ' + str(idx_int) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("setting marker " + str(id_int) +
                               " to point " + str(idx_int))
            return msgbytes

        # ID + action
        if str(val) in accepted_vals:
            writebyte = 'marker ' + str(id_int) + ' ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            if str(val) == "on":
                self.print_message("turning marker " + str(id_int) + " on")
            elif str(val) == "off":
                self.print_message("turning marker " + str(id_int) + " off")
            else:  # peak
                self.print_message("setting marker " + str(id_int) + " to peak")
            return msgbytes

        self.print_message("ERROR: marker() actions are on|off|peak")
        return self.error_byte_return()

    def get_all_marker_positions(self):
        # alias for marker()
        return self.marker(None, None, None)

    def get_marker_position(self, ID):
        # alias for marker()
        return self.marker(ID, None, None)

    def set_marker_position(self, ID, idx):
        # alias for marker()
        return self.marker(ID, None, idx)

    def marker_peak(self, ID):
        # alias for marker()
        return self.marker(ID, 'peak', None)

    def marker_on(self, ID):
        # alias for marker()
        return self.marker(ID, 'on', None)

    def marker_off(self, ID):
        # alias for marker()
        return self.marker(ID, 'off', None)

    def trace(self, ID=None, trace_format=None, val=None):
        # set trace format and attributes, or dump trace info.
        # usage:
        #   trace                                  -> dump all active traces
        #   trace {ID}                             -> dump that trace
        #   trace {ID} {format}                    -> apply format to trace
        #   trace {ID} {format} {value|channel}    -> format with a value
        # ID is 1..4 or "all".
        # formats: off|logmag|linear|phase|smith|swr|polar|delay|refpos|channel
        # example return: b''

        # no args -> dump all trace info
        if (ID is None) and (trace_format is None) and (val is None):
            writebyte = 'trace\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("returning the attributes of active traces")
            return msgbytes

        accepted_ID_vals = [0, 1, 2, 3, "all"]
        if ID not in accepted_ID_vals:
            self.print_message("ERROR: trace() ID must be an integer 0..3 or 'all'")
            return self.error_byte_return()

        # ID only -> dump that trace
        if (trace_format is None) and (val is None):
            writebyte = 'trace ' + str(ID) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("returning the attributes of trace " + str(ID))
            return msgbytes

        accepted_format_vals = ['off', 'logmag', 'linear', 'phase', 'smith',
                                'swr', 'polar', 'delay', 'refpos', 'channel']

        if str(trace_format) not in accepted_format_vals:
            self.print_message("ERROR: trace() unrecognized argument " + str(trace_format))
            return self.error_byte_return()

        if val is None:
            writebyte = 'trace ' + str(ID) + ' ' + str(trace_format) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("applying format " + str(trace_format) +
                               " to trace " + str(ID))
            return msgbytes

        # format + value/channel
        writebyte = 'trace ' + str(ID) + ' ' + str(trace_format) + ' ' + str(val) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("applying " + str(trace_format) + " " + str(val) +
                           " to trace " + str(ID))
        return msgbytes

    def get_all_trace_attr(self):
        # alias for trace()
        return self.trace()

    def get_trace_attr(self, ID):
        # alias for trace()
        return self.trace(ID)

    def trace_off(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="off")

    def set_trace_logmag(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="logmag")

    def set_trace_linear(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="linear")

    def set_trace_phase(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="phase")

    def set_trace_smith(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="smith")

    def set_trace_polar(self, ID):
        # alias for trace()
        return self.trace(ID=ID, trace_format="polar")

    def set_trace_swr(self, ID, val):
        # alias for trace()
        return self.trace(ID=ID, trace_format="swr", val=val)

    def set_trace_refposition(self, ID, val):
        # alias for trace()
        return self.trace(ID=ID, trace_format="refpos", val=val)

    def set_trace_delay(self, ID, val):
        # alias for trace()
        return self.trace(ID=ID, trace_format="delay", val=val)

    def set_trace_channel(self, ID, val):
        # alias for trace()
        if isinstance(val, int):
            msgbytes = self.trace(ID=ID, trace_format="channel", val=val)
        else:
            self.print_message("ERROR: trace() channel value must be an integer")
            msgbytes = self.error_byte_return()
        return msgbytes
