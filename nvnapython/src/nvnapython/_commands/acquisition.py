#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/acquisition.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class AcquisitionMixin:
    def cwfreq(self, val):
        # Set the continuous wave (CW) frequency.
        # usage: cwfreq {freq(Hz)}
        # example return: bytearray(b'')
        #
        # FIXED (vs original): the command string was 'cwfreq'+str(val) with no
        # space ('cwfreq150000000'), and the isinstance(int) gate rejected
        # float-like input after already int()-ing it. Now: accept int/float,
        # build 'cwfreq {val}' with a space.
        if isinstance(val, (int, float)):
            writebyte = 'cwfreq ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("setting CW frequency to " + str(val))
        else:
            self.print_message("ERROR: cwfreq() requires an int or float value in Hz")
            msgbytes = self.error_byte_return()
        return msgbytes

    def set_cwfreq(self, val):
        # alias for cwfreq()
        return self.cwfreq(val)

    def data(self, val=0):
        # dumps the trace / calibration data.
        # usage: data [0-6]
        #   0 = S11, 1 = S21,
        #   2 = load cal, 3 = open cal, 4 = short cal, 5 = thru cal, 6 = isolation cal
        # example return: bytearray(b'1.0 0.0\r\n0.998 -0.01\r\n...')

        accepted_vals = [0, 1, 2, 3, 4, 5, 6]
        if val in accepted_vals:
            writebyte = 'data ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            messages = {
                0: "returning S11 data",
                1: "returning S21 data",
                2: "returning load calibration data",
                3: "returning open calibration data",
                4: "returning short calibration data",
                5: "returning thru calibration data",
                6: "returning isolation calibration data",
            }
            self.print_message(messages[val])
        else:
            self.print_message("ERROR: data() takes integer vals [0-6]")
            msgbytes = self.error_byte_return()
        return msgbytes

    def get_s11_data(self):
        # alias for data()
        return self.data(val=0)

    def get_s21_data(self):
        # alias for data()
        return self.data(val=1)

    def get_load_cal_data(self):
        # alias for data()
        return self.data(val=2)

    def get_open_cal_data(self):
        # alias for data()
        return self.data(val=3)

    def get_short_cal_data(self):
        # alias for data()
        return self.data(val=4)

    def get_thru_cal_data(self):
        # alias for data()
        return self.data(val=5)

    def get_isolation_cal_data(self):
        # alias for data()
        return self.data(val=6)

    def frequencies(self):
        # gets the frequencies used by the last sweep
        # usage: frequencies
        # example return: bytearray(b'1000000000\r\n...\r\n3000000000\r')

        writebyte = 'frequencies\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("getting frequencies from the last sweep")
        return msgbytes

    def get_last_freqs(self):
        # alias for frequencies()
        return self.frequencies()

    def pause(self):
        # pauses the sweeping
        # usage: pause
        # example return: ''

        writebyte = 'pause\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("pausing NanoVNA device")
        return msgbytes

    def port(self, val):
        # selects the active measurement port.
        # usage: port {1:S11 2:S21}
        # example return: ''
        #
        # Documented in the device 'help' output (port {1:S11 2:S21}).
        # 1 selects S11 (port 1), 2 selects S21 (port 2).
        accepted_vals = [1, 2]
        if val in accepted_vals:
            writebyte = 'port ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("selecting port " + str(val) +
                               (" (S11)" if val == 1 else " (S21)"))
        else:
            self.print_message("ERROR: port() takes 1 (S11) or 2 (S21)")
            msgbytes = self.error_byte_return()
        return msgbytes

    def set_port_s11(self):
        # alias for port()
        return self.port(1)

    def set_port_s21(self):
        # alias for port()
        return self.port(2)

    def resume(self):
        # resumes the sweeping
        # usage: resume
        # example return: ''

        writebyte = 'resume\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("resuming sweep")
        return msgbytes

    def scan(self, start, stop, pts=None, outmask=None):
        # Scan with start, stop, points, and outmask.
        # usage: scan {start(Hz)} {stop(Hz)} [points] [outmask]
        #   start  - required, freq in Hz
        #   stop   - required, freq in Hz
        #   points - optional, integer number of sample points
        #   outmask - optional, controls returned data (bitmask):
        #     0 = no printout
        #     1 = frequency values
        #     2 = S11 of sweep points
        #     3 = frequency + S11
        #     4 = S21 of sweep points
        #     5 = frequency + S21
        #     6 = S11 + S21
        #     7 = frequency + S11 + S21

        # start/stop must be int-able
        try:
            int(start)
            int(stop)
        except (TypeError, ValueError):
            self.print_message("ERROR: scan() requires start and stop frequencies as integers")
            return self.error_byte_return()

        # start must be LESS than stop
        if int(start) >= int(stop):
            self.print_message("ERROR: scan() requires start frequency less than stop frequency")
            return self.error_byte_return()

        # sweep with NO point/output args
        if (pts is None) and (outmask is None):
            writebyte = 'scan ' + str(start) + ' ' + str(stop) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("scanning frequencies. no output.")
            return msgbytes

        # pts and outmask path
        try:
            if int(pts) <= 0:
                self.print_message("ERROR: scan() requires more than 0 points to return data")
                return self.error_byte_return()
            # bound against the device point limit (library-side check).
            # README: device reports "range 51 -201" with the upper end NOT
            # inclusive, so maxPoints (201) itself is rejected -> use >=.
            if int(pts) >= self.maxPoints:
                self.print_message("ERROR: scan() pts must be less than device maxPoints (" +
                                   str(self.maxPoints) + ", upper end not inclusive)")
                return self.error_byte_return()
            if int(outmask) not in [0, 1, 2, 3, 4, 5, 6, 7]:
                self.print_message("ERROR: scan() outmask options are integers 0-7")
                return self.error_byte_return()
        except (TypeError, ValueError):
            self.print_message("ERROR: scan() invalid input. check parameters; see documentation")
            return self.error_byte_return()

        writebyte = ('scan ' + str(start) + ' ' + str(stop) + ' ' +
                     str(pts) + ' ' + str(outmask) + '\r\n')
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        outmask_messages = {
            0: "scanning. no output.",
            1: "scanning. returning frequency values.",
            2: "scanning. returning S11 values.",
            3: "scanning. returning frequency and S11 values.",
            4: "scanning. returning S21 values.",
            5: "scanning. returning frequency and S21 values.",
            6: "scanning. returning S11 and S21 values.",
            7: "scanning. returning frequency, S11, and S21 values.",
        }
        self.print_message(outmask_messages[int(outmask)])
        return msgbytes

    def scan_range(self, start, stop):
        # alias for scan() - sweep only, no data returned
        return self.scan(start, stop, None, None)

    def get_scan_frequencies(self, start, stop, pts):
        # alias for scan() - outmask 1
        return self.scan(start, stop, pts, 1)

    def get_scan_s11(self, start, stop, pts):
        # alias for scan() - outmask 2
        return self.scan(start, stop, pts, 2)

    def get_scan_freqs_s11(self, start, stop, pts):
        # alias for scan() - outmask 3
        return self.scan(start, stop, pts, 3)

    def get_scan_s21(self, start, stop, pts):
        # alias for scan() - outmask 4
        return self.scan(start, stop, pts, 4)

    def get_scan_freqs_s21(self, start, stop, pts):
        # alias for scan() - outmask 5
        return self.scan(start, stop, pts, 5)

    def get_scan_s11_s21(self, start, stop, pts):
        # alias for scan() - outmask 6
        return self.scan(start, stop, pts, 6)

    def get_scan_freqs_s11_s21(self, start, stop, pts):
        # alias for scan() - outmask 7
        return self.scan(start, stop, pts, 7)

    def config_sweep(self, argName=None, val=None):
        # split call for SWEEP. Sets sweep boundaries.
        # Sweep without arguments lists the current sweep settings.
        # usage:
        #   sweep [(start|stop|center|span|cw {frequency}) |
        #          ({start(Hz)} {stop(Hz)} [points])]
        # example return: b''

        accepted_table_args = ["start", "stop", "center", "span", "cw"]

        if (argName is None) and (val is None):
            writebyte = 'sweep\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("returning current sweep settings")
        elif argName in accepted_table_args:
            if val is None:
                self.print_message("ERROR: sweep " + str(argName) + " needs a value")
                msgbytes = self.error_byte_return()
            else:
                writebyte = 'sweep ' + str(argName) + ' ' + str(val) + '\r\n'
                self.print_message("sweep " + str(argName) + " is " + str(val))
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        else:
            self.print_message("ERROR: " + str(argName) + " invalid argument for sweep")
            msgbytes = self.error_byte_return()

        return msgbytes

    def get_sweep_params(self):
        # alias for config_sweep()
        return self.config_sweep()

    def set_sweep_start(self, val):
        # alias for config_sweep()
        return self.config_sweep("start", val)

    def set_sweep_stop(self, val):
        # alias for config_sweep()
        return self.config_sweep("stop", val)

    def set_sweep_center(self, val):
        # alias for config_sweep()
        return self.config_sweep("center", val)

    def set_sweep_span(self, val):
        # alias for config_sweep()
        return self.config_sweep("span", val)

    def set_sweep_cw(self, val):
        # alias for config_sweep()
        return self.config_sweep("cw", val)

    def run_sweep(self, start=None, stop=None, pts=250):
        # split call for SWEEP. Executes a sweep over start..stop with points.
        # usage: sweep {start(Hz)} {stop(Hz)} [points]
        #
        # FIXED (vs original): the command string appended a stray '1' after
        # points ("sweep ... "+str(pts)+"1\r\n"), turning e.g. 250 into 2501.
        if (start is None) or (stop is None):
            self.print_message("ERROR: sweep start and stop need non-empty values")
            msgbytes = self.error_byte_return()
        elif int(start) >= int(stop):
            self.print_message("ERROR: sweep start must be less than sweep stop value")
            msgbytes = self.error_byte_return()
        else:
            self.print_message("sweeping...")
            writebyte = 'sweep ' + str(start) + ' ' + str(stop) + ' ' + str(pts) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)

        return msgbytes

    def preform_sweep(self, start=None, stop=None, pts=250):
        # alias for run_sweep().
        # The README prose names this 'preform_sweep' while its alias list names
        # 'run_sweep'; both are provided so either documented name works.
        return self.run_sweep(start, stop, pts)
