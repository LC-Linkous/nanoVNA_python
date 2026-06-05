#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/calibration.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class CalibrationMixin:
    def cal(self, val=0):
        # Work through the SOLT calibration process.
        # Several steps require physical interaction with the device (attaching
        # the load/open/short/thru standards).
        # usage: cal [load|open|short|thru|done|reset|on|off]
        # example return: bytearray(b'')

        # 'in' is documented but has no button on the NanoVNA-F V2 (may be a
        # later feature); it is accepted here and passed through to the device.
        accepted_vals = ['load', 'open', 'short', 'thru', 'done', 'reset', 'on', 'off', 'in']
        if str(val) in accepted_vals:
            writebyte = 'cal ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            if val == 'on' or val == 'off':
                self.print_message("calibration is now " + str(val))
            elif str(val) == 'reset':
                self.print_message("calibration has been reset")
            elif str(val) == 'done':
                self.print_message("finished calibration signal sent")
            else:
                self.print_message("calibration action: " + str(val))
        else:
            self.print_message("ERROR: cal() takes string args "
                               "load|open|short|thru|done|reset|on|off|in")
            msgbytes = self.error_byte_return()
        return msgbytes

    def cal_load(self):
        # alias for cal()
        return self.cal('load')

    def cal_open(self):
        # alias for cal()
        return self.cal('open')

    def cal_short(self):
        # alias for cal()
        return self.cal('short')

    def cal_thru(self):
        # alias for cal()
        return self.cal('thru')

    def cal_done(self):
        # alias for cal()
        return self.cal('done')

    def cal_reset(self):
        # alias for cal()
        return self.cal('reset')

    def cal_on(self):
        # alias for cal()
        return self.cal('on')

    def cal_off(self):
        # alias for cal()
        # FIXED (vs original): previously sent 'of' (typo) instead of 'off'.
        return self.cal('off')

    def cal_in(self):
        # alias for cal()
        # NOTE: documented but a no-op on the NanoVNA-F V2 (no button).
        return self.cal('in')

    def edelay(self, val=None):
        # gets or sets the electrical delay.
        # usage: edelay [{delay}]
        # example return: bytearray(b'0\r')

        if val is None:
            writebyte = 'edelay\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("getting the current edelay")
            return msgbytes

        if isinstance(val, (int, float)):
            writebyte = 'edelay ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("setting the edelay value to " + str(val))
            return msgbytes

        self.print_message("ERROR: the edelay value must be an int or float")
        return self.error_byte_return()

    def get_edelay(self):
        # alias for edelay()
        return self.edelay()

    def set_edelay(self, val):
        # alias for edelay()
        return self.edelay(val)
