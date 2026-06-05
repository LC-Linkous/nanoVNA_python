#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   'src/nvnapython/_commands/display_ui.py'
#   UNOFFICIAL Python API for the NanoVNA series of vector network analyzers.
#
#   Part of the nvnapython package. This module is a mixin for the nanoVNA class in core.py;
#   it is not intended to be instantiated on its own.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

class DisplayUIMixin:
    def beep(self, val):
        # turn the beep on or off
        # usage: beep [on|off]
        # example return: bytearray(b'')

        accepted_vals = ['on', 'off']
        if str(val) in accepted_vals:
            writebyte = 'beep ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("beep() called to turn beep " + str(val))
        else:
            self.print_message("ERROR: beep() takes vals [on|off]")
            msgbytes = self.error_byte_return()
        return msgbytes

    def beep_on(self):
        # alias for beep()
        return self.beep(val='on')

    def beep_off(self):
        # alias for beep()
        return self.beep(val='off')

    def beep_time(self, val):
        # beep on, wait val seconds, beep off.
        # NOTE: this BLOCKS for val seconds (uses time.sleep).
        try:
            seconds = float(val)
        except (TypeError, ValueError):
            self.print_message("ERROR: beep_time() takes a numerical value in seconds")
            return self.error_byte_return()

        import time
        self.beep(val='on')
        time.sleep(seconds)
        return self.beep(val='off')

    def capture(self):
        # requests a screen dump in binary format.
        # 800x480 for NanoVNA-F V2 / V3.
        # usage: capture
        # example return: bytearray(b'\x00 ...\x00\x00\x00')

        writebyte = 'capture\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("capture() called for screen data")
        return msgbytes

    def capture_screen(self):
        # alias for capture()
        return self.capture()

    def lcd(self, X, Y, W, H, COL):
        # draws a rectangle on the active area of the screen.
        # usage: lcd X Y W H COL
        #   X, Y - top-left coordinate (>= 0, screen coords)
        #   W, H - width and height in pixels
        #   COL  - 16-bit RGB565 color as a 4-digit hex string (e.g. 'F800'),
        #          with or without a leading 0x.
        # example return: b''
        #
        # FIXED (vs original): required X>0 and Y>0, rejecting the valid top
        # corner (0,0); now allows X,Y >= 0. Color check now uses is_rgb565_hex
        # to accept an optional 0x prefix rather than a bare len()==4 test.

        if not (isinstance(X, int) and isinstance(Y, int)
                and isinstance(W, int) and isinstance(H, int)):
            self.print_message("ERROR: lcd() X, Y, W, and H must be integers")
            return self.error_byte_return()

        if X < 0 or Y < 0:
            self.print_message("ERROR: lcd() X and Y are screen coords and must be >= 0")
            return self.error_byte_return()

        if not self.is_rgb565_hex(COL):
            self.print_message("ERROR: lcd() COL must be a 4-digit RGB565 hex string "
                               "(e.g. 'F800' or '0xF800')")
            return self.error_byte_return()

        writebyte = ('lcd ' + str(X) + ' ' + str(Y) + ' ' + str(W) + ' ' +
                     str(H) + ' ' + str(COL) + '\r\n')
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("drawing a rectangle on the screen")
        return msgbytes

    def draw_rect(self, X, Y, W, H, COL):
        # alias for lcd()
        return self.lcd(X, Y, W, H, COL)

    def LCD_ID(self):
        # returns the LCD controller ID
        # usage: LCD_ID
        # example return: bytearray(b'...\r')

        writebyte = 'LCD_ID\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("returning LCD_ID value")
        return msgbytes

    def get_LCD_ID(self):
        # alias for LCD_ID()
        return self.LCD_ID()

    def pwm(self, val):
        # adjusts the screen PWM (brightness).
        # usage: pwm {0.0-1.0}
        # example return: ''

        try:
            f = float(val)
        except (TypeError, ValueError):
            self.print_message("ERROR: pwm() values must be floats 0.0-1.0")
            return self.error_byte_return()

        if 0.0 <= f <= 1.0:
            writebyte = 'pwm ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("adjusting pwm value to " + str(val))
        else:
            self.print_message("ERROR: pwm() values must be floats 0.0-1.0")
            msgbytes = self.error_byte_return()
        return msgbytes

    def set_screen_brightness(self, val):
        # alias for pwm()
        return self.pwm(val)

    def resolution(self):
        # gets the LCD screen resolution
        # usage: resolution
        # example return: bytearray(b'800,480\r')

        writebyte = 'resolution\r\n'
        self.print_message("getting the screen resolution in pixels")
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        return msgbytes

    def get_resolution(self):
        # alias for resolution()
        return self.resolution()

    def lcd_resolution(self):
        # alias for resolution()
        return self.resolution()

    def touch_cal(self):
        # starts the touch calibration. Requires physical screen interaction.
        # usage: touchcal
        # example return: bytearray(b'')

        writebyte = 'touchcal\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("starting touchcal")
        return msgbytes

    def start_touch_cal(self):
        # alias for touch_cal()
        return self.touch_cal()

    def touch_test(self):
        # starts the touch test
        # usage: touchtest
        # example return: bytearray(b'')

        writebyte = 'touchtest\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
        self.print_message("starting the touch_test()")
        return msgbytes

    def start_touch_test(self):
        # alias for touch_test()
        return self.touch_test()
