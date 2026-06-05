#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/presets_config.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class PresetsConfigMixin:
    def recall(self, val=0):
        # loads a previously stored preset, where 0 is the startup preset.
        # usage: recall [0-6]
        # example return: ''

        accepted_vals = [0, 1, 2, 3, 4, 5, 6]
        if val in accepted_vals:
            writebyte = 'recall ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("recall() set to value " + str(val))
        else:
            self.print_message("ERROR: recall() takes vals [0 - 6]")
            msgbytes = self.error_byte_return()
        return msgbytes

    def save(self, val=1):
        # saves the current settings to a preset, where 0 is the startup preset.
        # usage: save [0-4]
        # example return: ''

        accepted_vals = [0, 1, 2, 3, 4]
        if val in accepted_vals:
            writebyte = 'save ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("saving to preset " + str(val))
        else:
            self.print_message("ERROR: save() takes vals [0 - 4] as integers")
            msgbytes = self.error_byte_return()
        return msgbytes

    def save_config(self):
        # saves the device configuration data
        # usage: saveconfig
        # example return: bytearray(b'Config saved.\r')

        writebyte = 'saveconfig\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("save_config() called")
        return msgbytes

    def clear_config(self):
        # resets the configuration data to factory defaults. requires password.
        # usage: clearconfig 1234
        # example return: bytearray(b'Config and all cal data cleared.\r\n
        #   Do reset manually to take effect. Then do touch cal and save.\r')

        writebyte = 'clearconfig 1234\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("clear_config() with password. Config and all cal data cleared. "
                           "Reset manually to take effect.")
        return msgbytes

    def clear_and_reset(self):
        # full clear and reset process.
        # NOTE: reset() disconnects the serial immediately, so it may raise a
        # SerialException or return nothing usable. We clear first, then reset,
        # and tolerate the disconnect rather than depending on a clean return.
        # Returns the reset response if one comes back before the port drops,
        # otherwise None. Callers should NOT block waiting on this return.
        self.clear_config()
        try:
            return self.reset()
        except Exception as err:  # serial drops on reset; expected
            self.print_message("reset() disconnected the serial (expected): " + str(err))
            return None

    def reset(self):
        # reset the device. NOTE: will disconnect and fully reset.
        # usage: reset
        # example return: raises SerialException on real hardware (port drops)

        writebyte = 'reset\r\n'
        self.print_message("sending reset signal. Serial will disconnect...")
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        return msgbytes

    def reset_device(self):
        # alias for reset()
        return self.reset()

    def restart(self, val=0):
        # restarts the device after the specified number of seconds.
        # usage: restart {seconds}
        # example return: empty bytearray
        #
        # NOTE (per README): this has not worked on the NanoVNA-F V2 in testing,
        # but appears to work on some devices. 0 seconds cancels a pending restart.
        try:
            seconds = int(val)
        except (TypeError, ValueError):
            self.print_message("ERROR: restart() takes an integer number of seconds (0 to cancel)")
            return self.error_byte_return()

        if seconds < 0:
            self.print_message("ERROR: restart() takes vals 0 or greater")
            return self.error_byte_return()

        writebyte = 'restart ' + str(seconds) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        if seconds == 0:
            self.print_message("restart cancelled.")
        else:
            self.print_message("restarting the device in " + str(seconds) + " seconds.")
        return msgbytes

    def restart_device(self, val):
        # alias for restart()
        return self.restart(val)

    def cancel_restart(self):
        # alias for restart() - sends 'restart 0' to cancel a pending restart
        return self.restart(0)
