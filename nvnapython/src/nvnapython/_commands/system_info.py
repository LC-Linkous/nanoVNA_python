#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/system_info.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class SystemInfoMixin:
    def command(self, val):
        # passthrough: send an arbitrary command string to the device.
        # NO error checking is performed on the argument.
        # usage: command("scan 150000 250000000 200 2")

        writebyte = str(val) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("command() called with ::" + str(val))
        return msgbytes

    def info(self):
        # displays various SW and HW information
        # usage: info
        # example return: bytearray(b'Model: NanoVNA-F_V2\r\nFrequency: 50k ~ 3GHz\r\n...')

        writebyte = 'info\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("returning device info()")
        return msgbytes

    def get_info(self):
        # alias for info()
        return self.info()

    def SN(self):
        # get the unique serial number of the device
        # usage: SN
        # example return: bytearray(b'##############\r')

        writebyte = 'SN\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("returning the unique serial number of the device")
        return msgbytes

    def get_SN(self):
        # alias for SN()
        return self.SN()

    def version(self):
        # displays the version text
        # usage: version
        # example return: bytearray(b'...\r')

        writebyte = 'version\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("getting device version information")
        return msgbytes

    def get_version(self):
        # alias for version()
        return self.version()

######################################################################
# Device and library help
######################################################################

    def help(self, val=0):
        # val controls which help is returned:
        #   1            -> library_help() (this library's command list)
        #   anything else -> nanoVNA_help() (the device's command list)
        if val == 1:
            msgbytes = self.library_help()
        else:
            msgbytes = self.nanoVNA_help()
        return msgbytes

    def library_help(self):
        # placeholder for an in-library command summary.
        self.print_message("Returning command options for this library")
        self.print_message("IN PROGRESS.")
        return b''

    def nanoVNA_help(self):
        # dumps a list of the available device commands
        # usage: help
        # example return: bytearray(b'There are all commands\r\nhelp: ...\r')

        writebyte = 'help\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("Returning command options for NanoVNA device")
        return msgbytes

    def NanoVNA_Help(self):
        # alias for nanoVNA_help() - matches the name used in the README.
        return self.nanoVNA_help()
