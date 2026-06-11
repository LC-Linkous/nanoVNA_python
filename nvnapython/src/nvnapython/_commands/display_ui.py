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

    def decode_capture(self, data_bytes, width=None, height=None,
                       byte_order="little"):
        # Decode a raw NanoVNA screen-capture buffer (BGR565) into a flat list
        # of (r, g, b) tuples, row-major, length width*height.
        #
        # The NanoVNA panel is BGR565: within each 16-bit pixel, bits 15-11 are
        # BLUE, bits 10-5 GREEN, bits 4-0 RED. (This is the documented swap from
        # the tinySA's RGB565 -- red and blue are exchanged.)
        #
        # byte_order selects how the two bytes of each pixel combine into the
        # 16-bit value:
        #   "little" -> value = lo | (hi << 8) using struct '<H' (the order the
        #               original example used; the library default)
        #   "big"    -> value = (hi << 8) | lo
        # The true on-wire order is being confirmed on hardware (see
        # tests/test_hardware_capture_probe.py, which reports BOTH decodes).
        # Exposed as a parameter so flipping the default is a one-line change
        # once settled, with no caller rewrite.
        #
        # width/height default to the library's seeded screen size for the
        # selected model (self.screenWidth/Height), so a correctly-sized buffer
        # needs no explicit dimensions.
        #
        # Returns a list of (r, g, b) ints 0-255. Raises ValueError if the
        # buffer is too short for width*height pixels (no silent padding -- a
        # short buffer means the capture read was truncated and the caller
        # should know).
        if width is None:
            width = self.screenWidth
        if height is None:
            height = self.screenHeight

        buf = bytes(data_bytes) if data_bytes is not None else b""
        num_pixels = width * height
        needed = num_pixels * 2
        if len(buf) < needed:
            raise ValueError(
                "capture buffer too short: have " + str(len(buf)) +
                " bytes, need " + str(needed) + " for " + str(width) + "x" +
                str(height) + " (the binary read was likely truncated; see "
                "decode_capture / capture notes)")
        if len(buf) > needed:
            buf = buf[:needed]  # trailing console prompt etc.; keep image bytes

        fmt_char = "<" if byte_order == "little" else ">"
        try:
            import struct
            values = struct.unpack(fmt_char + str(num_pixels) + "H", buf)
        except Exception:
            # pure-Python fallback if struct is somehow unavailable.
            # For each pixel the two bytes are buf[2i], buf[2i+1]. Little-endian
            # means the FIRST byte is the low byte (value = b0 | b1<<8); big-
            # endian means the first byte is the high byte (value = b0<<8 | b1).
            values = []
            for i in range(num_pixels):
                b0, b1 = buf[2 * i], buf[2 * i + 1]
                values.append((b0 | (b1 << 8)) if byte_order == "little"
                              else ((b0 << 8) | b1))

        pixels = []
        for v in values:
            blue = ((v & 0xF800) >> 11) * 255 // 31
            green = ((v & 0x07E0) >> 5) * 255 // 63
            red = (v & 0x001F) * 255 // 31
            pixels.append((red, green, blue))
        return pixels

    def capture_to_pixels(self, width=None, height=None, byte_order="little"):
        # Convenience: issue capture() and decode in one call. NOTE: capture()
        # currently uses the TEXT serial path, which can truncate the binary
        # framebuffer at a 'ch>'-looking byte run; if decode_capture raises on a
        # short buffer, read the raw bytes off the port directly (see the
        # screen_capture example) until a binary capture path lands.
        raw = self.capture()
        return self.decode_capture(raw, width, height, byte_order)

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
