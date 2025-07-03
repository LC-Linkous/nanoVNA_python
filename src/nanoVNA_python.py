#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python 
#   './nanoVNA_python.py'
#   UNOFFICIAL Python API based on the tinySA official documentation at https://www.tinysa.org/wiki/
#
#  # NOTE: the tinySA_python library was created first, and then the NanoVNA device modifications added
#   references:
#       https://tinysa.org/wiki/pmwiki.php?n=TinySA4.ConsoleCommands  (NOTE: backwards compatibility not tested!)
#       http://athome.kaashoek.com/tinySA/python/tinySA.py  (existing library with some examples)
#      
#
#
#   Author(s): Lauren Linkous
#   Last update: July 2, 2025
##--------------------------------------------------------------------------------------------------\

import serial
import serial.tools.list_ports # COM search method wants full path
import numpy as np
import re

try:
    from src.device_config.device_config import deviceConfig
except:
    from device_config.device_config import deviceConfig

class nanoVNA():
    def __init__(self, parent=None):
        # serial port
        self.ser = None

        # user device class (to account for custom settings) 
        self.dev = deviceConfig #TODO, finish this class and integrate

        # message feedback
        self.verboseEnabled = False
        self.returnErrorByte = False

        # VARS BELOW HERE will be largely replaced with device class config calls
        # # this will allow for user settings and device presets

        #select device vars - hardcoding for NanoVNA-F V2
        # device params
        self.maxPoints = 200 # UP TO 201, but everything kicks back with 201
        # device ranges for err checking
        self.minVNADeviceFreq = 50e3  #50 kHz
        self.maxVNADeviceFreq = 5e9 #3 GHz for testing
        # screen 
        self.screenWidth = 800
        self.screenHeight = 480

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
            return bytearray(b'') # the default

######################################################################
# Set Device Params
#   Library specific functions. These set the boundaries & features for
#   error checking in the library 
#    
# WARNING: these DO NOT change the settings on the DEVICE. just the library.
######################################################################

    def select_existing_device(self, nanoVNAModel):
        # uses pre-set config files. 
        # nanoVNAModel var must be one of the following:
        # []
        try:
            noErrors = self.dev.select_preset_model(nanoVNAModel)
            if noErrors == False:
                print("ERROR: device configuration unable to be set. This feature is under development")
                return

            # set variables from device configs.
            # these are placeholders for now
            # device params
            self.maxPoints = 450
            # device ranges for err checking
            self.minVNADeviceFreq = 100e3  #100 kHz
            self.maxVNADeviceFreq = 3e9 #3 GHz for testing
            # screen 
            self.screenWidth = 480
            self.screenHeight = 320

        except:
            print("ERROR: device configuration unable to be set. This feature is under development")

    def load_custom_config(self, configFile):
        # TODO: for loading modified or other devices working on the same firmware
        pass


######################################################################
# Direct overrides
#   These are used during DEBUG or when device state/model is already known
#   Not recommended unless you are sure of the device state
#   and which settings each device has
# WARNING: these DO NOT change the settings on the DEVICE. just the library.
######################################################################
    
    # error check boundaries
    ## signal analyzer specific
    def set_min_device_freq(self, f):
        self.minVNADeviceFreq = float(f)
    
    def get_min_device_freq(self):
        return self.minVNADeviceFreq 
    
    def set_max_device_freq(self, f):
        self.maxVNADeviceFreq = float(f)

    def get_max_devicefreq(self):
        return self.maxVNADeviceFreq

######################################################################
# Serial management and message processing
######################################################################

    def autoconnect(self, timeout=1):
        # attempt to autoconnect to a detected port. 
        # returns: found_bool, connected_bool
        # True if successful, False otherwise

        # List all available serial ports
        ports = serial.tools.list_ports.comports()
        # loop through the ports and print out info
        for port_info in ports:

            # print out which port we're trying
            port = port_info.device 
            self.print_message(f"Checking port: {port}")
            vid = port_info.vid
            pid = port_info.pid

            # check if it's a tinySA OR NanoVNA. 
            # They aren't differentiated against right now:
            if (vid==None):
                pass 
            elif (hex(vid) == '0x483') and (hex(pid)=='0x5740'):
                self.print_message(f"NanoVNA device identified at port: {port}")
                connected_bool = self.connect(port, timeout)

                return True, connected_bool

        return False, False # no device found, not connected

    def connect(self, port, timeout=1):
        # attempt connection to provided port. 
        # returns: True if successful, False otherwise

        try:
            self.ser = serial.Serial(port=port, timeout=timeout)
            return True
        except Exception as err:
            self.print_message("ERROR: cannot open port at " + str(port))
            self.print_message(err)
            return False

    def disconnect(self):
        # closes the serial port
        self.ser.close()

    def nanoVNA_serial(self, writebyte, printBool=False, pts=None):
        # write out to serial, get message back, clean up, return
        
        # clear INPUT buffer
        self.ser.reset_input_buffer()
        # clear OUTPUT buffer
        self.ser.reset_output_buffer()

        self.ser.write(bytes(writebyte, 'utf-8'))
        msgbytes = self.get_serial_return()
        msgbytes = self.clean_return(msgbytes)

        if printBool == True:
            print(msgbytes) #overrides verbose for debug

        return msgbytes

    
    def get_serial_return(self):
        # while there's a buffer, read in the returned message
        # original buffer reading from: https://groups.io/g/tinysa/topic/nanoVNA_screen_capture_using/82218670

        buffer = bytes()
        while True:
            if self.ser.in_waiting > 0:
                buffer += self.ser.read(self.ser.in_waiting)
                try:
                    # split the stream to take a chunk at a time
                    # get up to '>' of the prompt
                    complete = buffer[:buffer.index(b'>')+1]  
                    # leave the rest in buffer
                    buffer = buffer[buffer.index(b'ch>')+1:]  
                except ValueError:
                    # this is an acceptable err, so can skip it and keep looping
                    continue 
                except Exception as err:
                    # otherwise, something else is wrong
                    self.print_message("ERROR: exception thrown while reading serial")
                    self.print_message(err)
                    return None
                break
            
        return bytearray(complete)

    def read_until_end_marker(self, end_marker=b'}', timeout=10.0):
        # scan and scan raw might return early with nanoVNA_serial
        # so this is written to 
        import time
        
        buffer = bytes()
        start_time = time.time()
        
        while True:
            if self.ser.in_waiting > 0:
                buffer += self.ser.read(self.ser.in_waiting)
                
                # Check if we have the end marker
                if end_marker in buffer:
                    # Find the position after the end marker
                    end_pos = buffer.find(end_marker) + len(end_marker)
                    complete = buffer[:end_pos]
                    # Keep any remaining data for next read
                    self.remaining_buffer = buffer[end_pos:]
                    return bytearray(complete)
            
            # Timeout check
            if time.time() - start_time > timeout:
                self.print_message(f"WARNING: Timeout waiting for end marker {end_marker}")
                break
            
            time.sleep(0.01)
        
        return bytearray(buffer)

    def clean_return(self, data):
        # takes in a bytearray and removes 1) the text up to the first '\r\n' (includes the command), an 2) the ending 'ch>'
        # Find the first occurrence of \r\n (carriage return + newline)
        first_newline_index = data.find(b'\r\n')
        if first_newline_index != -1:
            # Slice the bytearray to remove everything before and including the first '\r\n'
            data = data[first_newline_index + 2:]  # Skip past '\r\n'
        # Check if the message ends with 'ch>'
        if data.endswith(b'ch>'):
            # Remove 'ch>' from the end
            data = data[:-4]  # Remove the last 4 bytes ('ch>')
        return data

######################################################################
# Reusable format checking functions
######################################################################

    def is_rgb24(self, hexStr):
        # check if the string matches the pattern 0xRRGGBB
        pattern = r"^0x[0-9A-Fa-f]{6}$"
        return bool(re.match(pattern, hexStr))

######################################################################
# Serial command config, input error checking
######################################################################

    def beep(self, val):
        # turn the beep on or off
        # usage: beep [on|off]
        # example return: bytearray(b'')
        #explicitly allowed vals
        accepted_vals = ['on','off']
        #check input
        if str(val) in accepted_vals:
            writebyte = 'beep '+str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)  
            self.print_message("beep() called to turn beep " + str(val)) 
        else:
            self.print_message("ERROR: beep() takes vals [on|off]")
            msgbytes = self.error_byte_return()
        return msgbytes

    def beep_on(self):
        return self.beep(val='on')
    def beep_off(self):
        return self.beep(val='off')
    def beep_time(self, val):
        try:
            import time
            self.beep(val='on')
            time.sleep(float(val))
            return self.beep(val='off')
        except:
            self.print_message("ERROR: beep_time() takes a numerical value in seconds")
            msgbytes = self.error_byte_return()
        return msgbytes

    def cal(self, val=0):
        # Work through the calibration process. 
        # Requires physical interaction with the device
        # usage: cal [load|open|short|thru|done|reset|on|off|in]
        # example return: bytearray(b'')
        
        #explicitly allowed vals
        accepted_vals = ['load','open','short','thru','done','reset','on','off']
        #check input
        if str(val) in accepted_vals:
            writebyte = 'cal '+str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)  
            if val == 'on' or val == 'off':
                self.print_message("calibration is now " + str(val)) 
            elif str(val) == 'reset':
                self.print_message("calibration has been reset") 
            elif str(val) == "done":
                self.print_message("finished calibration signal sent") 
            else:
                self.print_message("calibration action: " + str(val)) 
        else:
            self.print_message("ERROR: cal() takes string args load|open|short|thru|done|reset|on|off")
            msgbytes = self.error_byte_return()
        return msgbytes
    def cal_load(self):
        return self.cal('load')
    def cal_open(self):
        return self.cal('open')
    def cal_short(self):
        return self.cal('short')
    def cal_thru(self):
        return self.cal('thru')
    def cal_done(self):
        return self.cal('done')
    def cal_reset(self):
        return self.cal('reset')
    def cal_on(self):
        return self.cal('on')
    def cal_off(self):
        return self.cal('of')

    def capture(self):
        # requests a screen dump to be sent in binary format 
        # 800*480 for NanoVNA-F V2 and V3 
        # usage: capture
        # example return: bytearray(b'\x00 ...\x00\x00\x00')
        writebyte = 'capture\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("capture() called for screen data")   
        return msgbytes
    
    def capture_screen(self):
        # alias function for capture
        return self.capture()

    def clear_config(self):
        # resets the configuration data to factory defaults. requires password
        # NOTE: does take other commands to fully clear all
        # usage: clearconfig 1234
        # example return: bytearray(b'Config and all cal data cleared.
        # \r\nDo reset manually to take effect. 
        # Then do touch cal and save.\r')
        writebyte = 'clearconfig 1234\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("clear_config() with password. Config and all cal data cleared. \
                          Reset manually to take effect.")
        return msgbytes
    
    def clear_and_reset(self):
        # alias function for full clear and reset process
        self.clear_config()
        self.reset()

    def command(self, val):
        # if the command isn't already a function,
        #  use existing func setup to send command
        writebyte = str(val) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("command() called with ::" + str(val))
        return msgbytes   

    def cwfreq(self, val):
        # Set the continuous wave (CW) frequency
        # usage: cwfreq {freq in Hz}
        # example return: bytearray(b'')
        
        try:
            int(val)
        except:
            self.print_message("ERROR: cwfreq requires an Int value")
            return self.error_byte_return()
        if (isinstance(val,int)):
            writebyte = 'cwfreq' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("setting CW frequency to " +str(val))
            return msgbytes
        
    def set_cwfreq(self, val):
        # alias for cwfreq
        return self.cwfreq(val)

    def data(self, val=0):
        # dumps the trace data. 
        # usage: data [0-6]
        # example return: bytearray(b'-8.671875e+01\r\n... -8.337500e+01\r\n-8.237500e+01\r')
        
        #explicitly allowed vals
        accepted_vals = [0,1,2,3,4,5,6]
        #check input
        if val in accepted_vals:
            writebyte = 'data '+str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)  
            if val == 0:
                self.print_message("returning S11 data") 
            elif val == 1:
                self.print_message("returning S21 data") 
            elif val == 2:
                self.print_message("returning load calibration data") 
            elif val == 3:
                self.print_message("returning open calibration data") 
            elif val == 4:
                self.print_message("returning short calibration data") 
            elif val == 5:
                self.print_message("returning thru calibration data") 
            elif val == 6:
                self.print_message("returning isolation calibration data") 
        else:
            self.print_message("ERROR: data() takes Integer vals [0-6]")
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

    def edelay(self, val=None):
        # gets the frequencies used by the last sweep
        # usage: frequencies
        # example return: bytearray(b'1500000000\r\n... \r\n3000000000\r')

        if val == None:
            writebyte = 'edelay\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("getting the current edelay")
        else:
            try:
                float(val)
            except:
                self.print_message("ERROR: the edelay value must be an Integer or Float")
                msgbytes = self.error_byte_return()
                return msgbytes

            writebyte = 'edelay ' + str(val) + '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("setting the edlay value to " + str(val))
            return msgbytes

    def get_edelay(self):
        # alias for edelay()
        return self.edelay()
    def set_edelay(self, val):
        # alias for edelay()
        return self.edelay(val)

    def frequencies(self):
        # gets the frequencies used by the last sweep
        # usage: frequencies
        # example return: bytearray(b'1500000000\r\n... \r\n3000000000\r')

        writebyte = 'frequencies\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("getting frequencies from the last sweep")
        return msgbytes

    def get_last_freqs(self):
        # get frequencies of last sweep
        return self.frequencies()
    

    def info(self):
        # displays various SW and HW information
        # usage: info
        # example return: bytearray(b'Model:        NanoVNA-F_V2\r\nFrequency:   
        #  50k ~ 3GHz\r\nBuild time:   Mar  2 2021 - 09:40:50 CST\r')

        writebyte = 'info\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("returning device info()")
        return msgbytes 
    
    def get_info(self):
        # alias for info()
        return self.info()

    def lcd(self, X, Y, W, H, COL):
        # displays various SW and HW information
        # usage: info
        # example return: bytearray(b'tinySA ...\r')

        # check that X & Y are larger than 0 & ints.
        if (isinstance(X, (int))) and (isinstance(Y, (int))) and (isinstance(W, (int))) and (isinstance(H, (int))) :
            if X > 0 and Y > 0:
                if len(COL) == 4: # might be a color. Try it. 
                    writebyte = 'lcd ' + str(X) + ' ' + str(Y) + ' ' + str(W) + ' ' + str(H) + ' ' + str(COL) + '\r\n'
                    msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                    self.print_message("drawing a rectangle on the screen")
                else:
                    self.print_message("ERROR: COl must be a 4 digit hex value as String between 0000 and FFFF")
                    msgbytes = self.error_byte_return()
            else:
                # X and Y need to be positive (screen coords)
                self.print_message("ERROR: X and Y are screen coords. The must be positive Ints")
                msgbytes = self.error_byte_return()
        else:
            # X,Y,W,H must be ints
            self.print_message("ERROR: X, Y, W, and H must be Integers")
            msgbytes = self.error_byte_return()

        return msgbytes

    def draw_rect(self, X,Y,W,H,COL):
        # alias for lcd()
        return self.lcd(X,Y,W,H,COL)

    def LCD_ID(self):
        # displays various SW and HW information
        # usage: info
        # example return: bytearray(b'tinySA ...\r')

        writebyte = 'LCD_ID\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("returning LCD_ID value")
        return msgbytes 
    
    def get_LCD_ID(self):
        # alias for LCD_ID()
        return self.LCD_ID()

    def marker(self, ID=None, val=None, idx=None):
        # sets or dumps marker info.
        # Usage:
        # * `marker [n] [on|off|{index}]`
        # * `marker [n] [off|{index}]`
        # * `marker [n] peak`
        # The frequency must be within the selected sweep range
        # usage: marker [ID=Int|1..4] [val=None|"on"|"off"|"peak"] [idx=None|Int]
        # example return: ''

        #explicitly allowed vals (hardcoded for readability)
        accepted_IDs = [1,2,3,4]
        accepted_vals =  ["on", "off", "peak"]
        #check input
        if (ID == None) and (val == None) and (idx == None): 
            writebyte = 'marker\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("returning active marker information")
            return msgbytes

        try:
            # ID first, then action, then follow up
            if int(ID) in accepted_IDs:
                if (val == None):
                    if idx == None:
                        # return current marker location
                        writebyte = 'marker ' + str(ID) +'\r\n'
                        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                        self.print_message("returning active marker information")

                    else: # setting marker position to an int idx 
                        writebyte = 'marker ' + str(ID) + ' ' + str(idx) + +'\r\n'
                        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                        self.print_message("setting marker to point " + str(idx) + " (max 201)")
                else:
                    # action being taken
                    if str(val) == "on":
                        writebyte = 'marker ' + str(ID) + ' ' + str(val) + +'\r\n'
                        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                        self.print_message("turning marker on")

                    if str(val) == "off":
                        writebyte = 'marker ' + str(ID) + ' ' + str(val) + +'\r\n'
                        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                        self.print_message("turning marker off")

                    elif str(val) == "peak":
                        writebyte = 'marker ' + str(ID) + ' ' + str(val) + +'\r\n'
                        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                        self.print_message("setting marker to highest value")

                    else: # unrecognized val
                        self.print_message("ERROR: marker has actions on|off|peak")
                        msgbytes = self.error_byte_return()

            else:
                # not a valid marker ID value
                self.print_message("ERROR: marker() takes no args, ID Int args, ID and action args. refer to documentation for details")
                msgbytes = self.error_byte_return()
      
        except:
            self.print_message("ERROR: marker() takes no args, ID Int args, ID and action args. refer to documentation for details")
            msgbytes = self.error_byte_return()

        return msgbytes 
    
    def get_all_marker_positions(self):
        #alias function for marker()
        return self.marker(None, None, None)
    def get_marker_position(self, ID):
        #alias function for marker()
        return self.marker(ID, None, None)
    def set_marker_position(self, ID, idx):
         #alias function for marker()
        return self.marker(ID, None, idx)
    def marker_peak(self,ID):
        #alias function for marker()
        return self.marker(ID,'peak', None)
    def marker_on(self,ID):
        #alias function for marker()
        return self.marker(ID,'on', None)
    def marker_off(self,ID):
        #alias function for marker()
        return self.marker(ID,'off', None)

    def pause(self):
        # pauses the sweeping in either input or output mode
        # usage: pause
        # example return: ''

        writebyte = 'pause\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("pausing NanoVNA device")
        return msgbytes 

    def pwm(self, val):
        # Adjusts the PWM of the screen. 
        # This is screen brightness in this application.
        # usage: pwm {0.0-1.0}
        # example return: ''

        try:
            float(val)
            if 0.0 <= float(val) <=1.0:
                writebyte = 'pwm ' + str(val) +'\r\n'
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                self.print_message("adjusting pwm value")
            else:
                self.print_message("ERROR: pwm values must be float vals 0.0-1.0")
                msgbytes = self.error_byte_return()
        except:
            self.print_message("ERROR: pwm values must be float vals 0.0-1.0")
            msgbytes = self.error_byte_return()
        return msgbytes 

    def set_screen_brightness(self, val):
        # alias function for pwm
        return self.pwm(val)

    def recall(self, val=0):
        # loads a previously stored preset,where 0 is the startup preset 
        # usage: recall [0-4]
        # example return: ''

        #explicitly allowed vals
        accepted_vals =  [0,1,2,3,4,5,6]
        #check input
        if (val in accepted_vals):
            writebyte = 'recall '+str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("recall() set to value " + str(val))           
        else:
            self.print_message("ERROR: recall() takes vals [0 - 4]")
            msgbytes = self.error_byte_return()
        return msgbytes

    def reset(self):
        # reset the device. NOTE: will disconnect and fully reset
        # usage: reset
        # example return: throws error. raise SerialException

        writebyte = 'reset\r\n'
        self.print_message("sending reset signal. Serial will disconnect...")
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        return msgbytes 
    
    def reset_device(self):
        # alias function for reset()
        return self.reset()

    def resolution(self):
        # get the resolution of the LCD screen
        # usage: resolution
        # example return: bytearray(b'800,480\r')

        writebyte = 'resolution\r\n'
        self.print_message("getting the screen resolution in pixels")
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        return msgbytes 
    
    def get_resolution(self):
        # alias function for resolution()
        return self.resolution() 
    def lcd_resolution(self):
        # alias function for resolution()
        return self.resolution() 

    def resume(self):
        # resumes the sweeping in either input or output mode
        # usage: resume
        # example return: ''

        writebyte = 'resume\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("resuming sweep")
        return msgbytes 

    def save(self, val=1):
        # saves the current setting to a preset, where 0 is the startup preset
        # usage: save [0-4]
        # example return: ''

        #explicitly allowed vals
        accepted_vals =  [0,1,2,3,4]
        #check input
        if (val in accepted_vals):
            writebyte = 'save '+str(val)+'\r\n'
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

    def scan(self, start, stop, pts=None, outmask=None):
        # Scan with start, stop, point, and outmask values
        # usage: scan {start(Hz)} {stop(Hz)} [points] [outmask]
        # {start} - required. Freq in Hz.
        # {stop} - required. Freq in Hz
        # points - required. integer number of sample points
        # outmask - optional, control what data is returned.
        #  * 0 = no printout
        #  * 1 = frequency vals
        #  * 2 = S11 of sweep points
        #  * 3 = frequency values & S11 of sweep pts
        #  * 4 = S21 of sweep pts
        #  * 5 = frequency values and & S21 data of sweep pts
        #  * 6 = S11 and S21 data of sweep points
        #  * 7 = frequency values, S11 and S21 data of sweep points

        # error check that start and stop are ints
        try:
            int(start)
            int(stop)
        except:
            self.print_message("ERROR: Scan(). Device requires start and stop frequencies be integers")
            msgbytes = self.error_byte_return()
            return msgbytes
        
        #start must be LESS than stop
        if int(start) >= int(stop):
            self.print_message("ERROR: Scan(). Device requires start frequency be less than stop frequency")
            msgbytes = self.error_byte_return()
            return msgbytes            
            # NOTE: device can handle having too many points for a range, there's an error message

        # sweep with NO output
        if (pts == None) and (outmask == None): 
                writebyte = 'scan ' + str(start) + ' ' + str(stop) +'\r\n'
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                self.print_message("scanning frequencies. no output.")
                return msgbytes

        try:
            # try/except format in case non-numeric information used
            if int(pts)>0: 
                if int(outmask) in [0,1,2,3,4,5,6,7]:
                    writebyte = 'scan ' + str(start) + ' ' + str(stop) + ' ' + str(pts) + ' ' + str(outmask) + '\r\n'
                    msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                
                    if outmask == 0: # no data returned
                        self.print_message("scanning. no output.")
                    elif outmask == 1:
                        self.print_message("scanning. returning frequency values.")
                    elif outmask == 2:
                        self.print_message("scanning. returning S11 values")
                    elif outmask == 3:
                        self.print_message("scanning. returning frequency and S11 values.")
                    elif outmask == 4:
                        self.print_message("scanning. returning S21 values.")
                    elif outmask == 5:
                        self.print_message("scanning. returning frequency and S21 values.")
                    elif outmask == 6:
                        self.print_message("scanning. returning S11 and S21 values.")
                    elif outmask == 7:
                        self.print_message("scanning. returning frequency, S11, and S21 values.")
                else:
                    # not a known value for outmask
                    self.print_message("ERROR: Scan(). outmask options are integers 0-7")
                    msgbytes = self.error_byte_return()
            else:
                # points too low
                self.print_message("ERROR: Scan(). More than 0 points must be used to return data in a scan")
                msgbytes = self.error_byte_return()

        except:
            self.print_message("ERROR: Scan(). Invalid input. Check input parameters. refer to documentation for details")
            msgbytes = self.error_byte_return()

        return msgbytes 

    
    def scan_range(self, start, stop):
        #alias function for scan()
        return self.scan(start, stop, None, None)
    
    def get_scan_frequencies(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 1)
    
    def get_scan_s11(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 2)
    
    def get_scan_freqs_s11(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 3)
    
    def get_scan_s21(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 4)
    
    def get_scan_freqs_s21(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 5)
    
    def get_scan_s11_s21(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 6)
    
    def get_scan_freqs_s11_s21(self, start, stop, pts):
        #alias function for scan()
        return self.scan(start, stop, pts, 7)    

    def SN(self):
        # get the unique serial number of the NanoVNA
        # usage: SN
        # example return: bytearray(b'##############\r')
        writebyte = 'SN\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("returning the unique serial number of the device")
        return msgbytes 
    
    def get_SN(self):
        # alias for SN()
        return self.SN()

    def config_sweep(self, argName=None, val=None): 
            # split call for SWEEP
            # Set sweep boundaries.
            # Sweep without arguments lists the current sweep 
            # settings. The frequencies specified should be 
            # within the permissible range. The sweep commands 
            # apply both to input and output modes        
            # usage: 
            # sweep [(start|stop|center|span|cw {frequency}) | 
            #   ({start(Hz)} {stop(Hz)} [0..290])]
            # EXAMPLES:
            # sweep start {frequency}: sets the start frequency of the sweep.
            # sweep stop {frequency}: sets the stop frequency of the sweep.
            # sweep center {frequency}: sets the center frequency of the sweep.
            # sweep span {frequency}: sets the span of the sweep.
            # sweep cw {frequency}: sets the continuous wave frequency (zero span sweep). 
            # # example return:  b'' 

        # explicitly allowed vals
        accepted_table_args = ["start", "stop", "center", 
                               "span", "cw"]

        if (argName==None) and (val==None):
            # do sweep
            writebyte = 'sweep\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)

        elif (argName in accepted_table_args): 
            if val == None:
                #error
                self.print_message("ERROR: sweep " + str(argName) + " needs a value")
                msgbytes = self.error_byte_return()
            else:
                #do stuff, error checking needed
                writebyte = 'sweep ' + str(argName)+ ' ' + str(val)+ '\r\n'
                self.print_message("sweep " +str(argName) + " is " + str(val))
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False)

        else: #not in table of accepted args, so doesn't matter what val is
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
            # split call for SWEEP
            # Execute sweep.
            # The frequencies specified should be 
            # within the permissible range. The sweep commands 
            # apply both to input and output modes        
            # usage: 
            # sweep [(start|stop|center|span|cw {frequency}) | 
            #   ({start(Hz)} {stop(Hz)} [0..290])]
            # # example return:  
        if (start==None) or (stop==None):
            self.print_message("ERROR: sweep start and stop need non-empty values")
            msgbytes = self.error_byte_return()
        elif (int(start) >= int(stop)):
            self.print_message("ERROR: sweep start must be less than sweep stop value")
            msgbytes = self.error_byte_return()
        else:
            #do stuff, error checking needed
            self.print_message("sweeping...")
            writebyte = 'sweep '+str(start)+' '+str(stop)+' '+str(pts)+'1\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)

        return msgbytes 

    def touch_cal(self):
        # starts the touch calibration. 
        # Physical interaction with the device screen is required.
        # usage: touchcal
        # example return: bytearray(b'')
        writebyte = 'touchcal\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("starting touchcal")
        return msgbytes
    
    def start_touch_cal(self):
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
        return self.touch_test()

    # The TRACE functions are split to handle the broad functionality of this call

    def trace(self, ID=None, trace_format=None, val=None):
        # set trace format and attributes
        # usage: trace [0|1|2|3|all] [off|logmag|linear|phase|smith|swr|polar|delay|refpos|channel] [value]
        #       trace {ID} {format/action} {value/channel}
        #  ID - required. the trace ID, starts at 0
        # trace_format - optional, trace format/action.
        #        With no args this is applied to the ID channel
        # val - optional, either a value or a channel related to the action
        # example return: b''

        # if all args are 'None', return the active trace info
        if (ID==None) and (trace_format==None) and (val==None):
            writebyte = 'trace\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("returning the attributes of active traces")
            return msgbytes 
    
        # error check that ID is an int or "all"
        # and if the only val is ID, return that info
        accepted_ID_vals = [1,2,3,4, "all"]
        if ID in accepted_ID_vals:
            if (trace_format==None) and (val==None):
                writebyte = 'trace '+str(ID)+'\r\n'
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                self.print_message("returning the attributes of trace " + str(ID))
                return msgbytes 
               
        else:
            self.print_message("ERROR: trace() ID must be an integer or 'all'")
            msgbytes = self.error_byte_return()
            return msgbytes
        
        #start must be LESS than stop
        accepted_format_vals = ['off','logmag','linear','phase',
                                'smith','swr','polar',
                                'delay','refpos','channel']

        if str(trace_format) in accepted_format_vals:
            if val == None:
                # these arguments/formats are applied to the channel 
                # specified by the ID value
                writebyte = 'trace '+ str(ID) +' '+ str(trace_format)+'\r\n'
                msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                self.print_message("applying format to trace " + str(ID))
                return msgbytes 

            else:
                # try because it's possible to have non-working inputs to val
                try:
                    writebyte = 'trace '+ str(ID) +' '+ str(trace_format)+' '+ str(val)+'\r\n'
                    msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
                    self.print_message("returning the attributes of active traces")
                    return msgbytes 
                except:
                    self.print_message("ERROR: trace() ID must be an integer")
                    msgbytes = self.error_byte_return()
                    return msgbytes
        
        else:
            self.print_message("ERROR: trace() unrecognized argument " + str(trace_format))
            msgbytes = self.error_byte_return()
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
            self.print_message("ERROR: trace() ID must be an integer")
            msgbytes = self.error_byte_return()
        return msgbytes
   
    def version(self):
        # displays the version text
        # usage: version
        # example return: tinySA4_v1.4-143-g864bb27\r\nHW Version:V0.4.5.1.1
       
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

    def help(self):
        # dumps a list of the available commands
        # usage: help
        # example return: bytearray(b'There are all commands\r\nhelp:                lists all the registered commands\r\nreset:               usage: reset\r\ncwfreq:        
        # usage: cwfreq {frequency(Hz)}\r\nsaveconfig:          usage: saveconfig\r\nclearconfig:         usage: clearconfig {protection key}\r\ndata:  
        # usage: data [array]\r\nfrequencies:         usage: frequencies\r\nport:                usage: port {1:S11 2:S21}\r\nscan:
        # usage: scan {start(Hz)} [stop] [points] [outmask]\r\nsweep:               usage: sweep {start(Hz)} [stop] [points]\r\ntouchcal:            usage: touchcal\r\ntouchtest:           usage: touchtest\r\npause:               usage: pause\r\nresume:              usage: resume\r\ncal:
        # usage: cal [load|open|short|thru|done|reset|on|off|in]\r\nsave:                usage: save {id}\r\nrecall:              usage: recall {id}\r\ntrace:               usage: trace {id}\r\nmarker:              usage: marker [n] [off|{index}]\r\nedelay:              usage: edelay {id}\r\npwm:       
        # usage: pwm {0.0-1.0}\r\nbeep:                usage: beep on/off\r\nlcd:                 usage: lcd X Y WIDTH HEIGHT FFFF\r\ncapture:      
        # usage: capture\r\nversion:             usage: Show NanoVNA version\r\ninfo:                usage: NanoVNA-F info\r\nSN:                  usage: NanoVNA-F ID\r\nresolution:          usage: LCD resolution\r\nLCD_ID:              usage: LCD ID\r')

        writebyte = 'help\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("Returning command options for NanoVNA device")
        return msgbytes

######################################################################
# Unit testing
######################################################################

if __name__ == "__main__":
    # unit testing. not recommended to write program from here

    # create a new tinySA object    
    nvna = nanoVNA()
    # attempt to connect to previously discovered serial port
    #success = nvna.connect(port='COM10')

    # attempt to autoconnect
    found_bool, connected_bool = nvna.autoconnect()

    # if port open, then complete task(s) and disconnect
    if connected_bool == True: # or  if success == True:
        print("device connected")
        nvna.set_verbose(True) #detailed messages
        nvna.set_error_byte_return(True) #get explicit b'ERROR'

        msg = nvna.help()
        print(msg)

        msg = nvna.get_info() 
        print(msg)
        

        nvna.disconnect()
    else:
        print("ERROR: could not connect to port")




