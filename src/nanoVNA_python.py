#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python 
#   './nanoVNA_python.py'
#   UNOFFICIAL Python API based on the tinySA official documentation at https://www.tinysa.org/wiki/
#
#   references:
#       https://tinysa.org/wiki/pmwiki.php?n=TinySA4.ConsoleCommands  (NOTE: backwards compat not tested!)
#       http://athome.kaashoek.com/tinySA/python/tinySA.py  (existing library with some examples)
#       # NOTE: the tinySA_python library was created first, and then the nanoVNA device modifications added
#
#
#
#   Author(s): Lauren Linkous
#   Last update: June 29, 2025
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

        #select device vars - hardcoding for the Ultra for now
        # device params
        self.maxPoints = 450
        # device ranges for err checking
        self.minVNADeviceFreq = 100e3  #100 kHz
        self.maxVNADeviceFreq = 3e9 #3 GHz for testing
        # screen 
        self.screenWidth = 480
        self.screenHeight = 320


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
                print("ERROR: device configuration unable to be set.This feature is underdevelopment")
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
            print("ERROR: device configuration unable to be set.This feature is underdevelopment")

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

            # check if it's a tinySA OR nanoVNA. 
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

    def convert_frequency(self, txtstr):
        # this takes the user input (as text) and converts it. 
        #  From documentation:
        #       Frequencies can be specified using an integer optionally postfixed with a the letter 
        #       'k' for kilo 'M' for Mega or 'G' for Giga. E.g. 0.1M (100kHz), 500k (0.5MHz) or 12000000 (12MHz)
        # However the abbreviation makes error checking with numerics more difficult. so convert everything to Hz.
        #  e notation is fine
        pass


    def is_rgb24(self, hexStr):
        # check if the string matches the pattern 0xRRGGBB
        pattern = r"^0x[0-9A-Fa-f]{6}$"
        return bool(re.match(pattern, hexStr))


######################################################################
# Serial command config, input error checking
######################################################################

  
    def capture(self):
        # requests a screen dump to be sent in binary format 
        # of 320x240 pixels of each 2 bytes
        # usage: capture
        # example return: bytearray(b'\x00 ...\x00\x00\x00')
        writebyte = 'capture\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("capture() called for screen data")   
        return msgbytes
    
    def capture_screen(self):
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


    def data(self, val=0):
        # dumps the trace data. 
        # usage: data [0-2]
        # example return: bytearray(b'-8.671875e+01\r\n... -8.337500e+01\r\n-8.237500e+01\r')
        
        #explicitly allowed vals
        accepted_vals = [0,1,2]
        #check input
        if val in accepted_vals:
            writebyte = 'data '+str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)  
            if val == 0:
                self.print_message("returning temp value data") 
            elif val == 1:
                self.print_message("returning stored trace data") 
            elif val == 2:
                self.print_message("returning measurement data") 
        else:
            self.print_message("ERROR: data() takes vals [0-2]")
            msgbytes = self.error_byte_return()
        return msgbytes
    

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
    

    # TODO
    def info(self):
        # displays various SW and HW information
        # usage: info
        # example return: bytearray(b'tinySA ...\r')

        writebyte = 'info\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("returning device info()")
        return msgbytes 
    
    def get_info(self):
        # alias for info()
        return self.info()


    def marker(self, ID, val):
        # sets or dumps marker info.
        # where id=1..4 index=0..num_points-1
        # Marker levels will use the selected unit.
        # Marker peak will:
        # 1) activate the marker (if not done already), 
        # 2) position the marker on the strongest signal, and
        # 3) display the marker info.
        # The frequency must be within the selected sweep range
        # usage: marker {id} on|off|peak|{freq}|{index}
        # example return: ''

        #explicitly allowed vals
        accepted_vals =  ["on", "off", "peak"]
        #check input
        if ID == None: 
            self.print_message("ERROR: marker() takes ID=Int|0..4")
            msgbytes = self.error_byte_return()
            return msgbytes

        if (str(val) in accepted_vals):
            writebyte = 'marker ' + str(ID) + ' ' +str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)     
            self.print_message("marker set to " + str(val))      
        elif (isinstance(val, (int, float))): # or (isinstance(val, float)):  
            writebyte = 'marker ' + str(ID) + ' ' +str(val)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)     
            self.print_message("marker set to " + str(val)) 
        else:
            self.print_message("ERROR: marker() takes ID=Int|0..4, and frequency or index in Int or Float")
            msgbytes = self.error_byte_return()
        return msgbytes

    def pause(self):
        # pauses the sweeping in either input or output mode
        # usage: pause
        # example return: ''

        writebyte = 'pause\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("pausing NanoVNA device")
        return msgbytes 

    def recall(self, val=0):
        # loads a previously stored preset,where 0 is the startup preset 
        # usage: recall [0-4]
        # example return: ''

        #explicitly allowed vals
        accepted_vals =  [0,1,2,3,4]
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

    def scan(self, start, stop, pts=250, outmask=None):
        # Performs a scan and optionally outputs the measured data.
        # usage: scan {start(Hz)} {stop(Hz)} [points] [outmask]
            # where the outmask is a binary OR of:
            # 1=frequencies, 2=measured data,
            # 4=stored data and max points is device dependent

        if (0<=start) and (start < stop) and (pts <= self.maxPoints):
            if outmask == None:
                writebyte = 'scan '+str(start)+' '+str(stop)+' '+str(pts)+'\r\n'
            else: 
                 writebyte = 'scan '+str(start)+' '+str(stop)+' '+str(pts)+ ' '+str(outmask)+'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)
            self.print_message("scanning...")           
        else:
            self.print_message("ERROR: scan takes START STOP PTS OUTMASK as args. Check doc for format and limits")
            msgbytes = self.error_byte_return()
        return msgbytes
    
 
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
    
    def run_sweep(self, startVal=None, stopVal=None, pts=250):
            # split call for SWEEP
            # Execute sweep.
            # The frequencies specified should be 
            # within the permissible range. The sweep commands 
            # apply both to input and output modes        
            # usage: 
            # sweep [(start|stop|center|span|cw {frequency}) | 
            #   ({start(Hz)} {stop(Hz)} [0..290])]
            # # example return:  
        if (startVal==None) or (stopVal==None):
            self.print_message("ERROR: sweep start and stop need non-empty values")
            msgbytes = self.error_byte_return()
        elif (int(startVal) >= int(stopVal)):
            self.print_message("ERROR: sweep start must be less than sweep stop value")
            msgbytes = self.error_byte_return()
        else:
            #do stuff, error checking needed
            self.print_message("sweeping...")
            writebyte = 'sweep '+str(startVal)+' '+str(stopVal)+' '+str(pts)+'1\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False)

        return msgbytes 


    def touch_cal(self):
        # starts the touch calibration
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

    def trace_select(self, ID):
        # split call for TRACE. select an available trace
        if (isinstance(ID, int)) and ID >=0:
            writebyte = 'trace '+ str(ID) +'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("selecting trace")
        else:
            self.print_message("ERROR: trace numbers must be integers greater than 0. see device documentation for max")
            msgbytes = self.error_byte_return()
        return msgbytes
    
    def trace_units(self, val):
        # split call for TRACE. set the units for the traces
        # explicitly allowed vals
        accepted_vals =  ["dBm", "dBmV", "dBuV", "V", "W", "Vpp", "RAW"]

        if (str(val) in accepted_vals):
            writebyte = 'trace '+ str(val) +'\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("setting trace units to " + str(val))
        else:
            self.print_message("ERROR: trace vals can be 'dBm'|'dBmV'|'dBuV'|'RAW'|'V'|'Vpp'|'W'")
            msgbytes = self.error_byte_return()
        return msgbytes

    def trace_scale(self, val="auto"):
        # split call for TRACE. scales a trace/traces.
        writebyte = 'trace scale' + str(val) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("scaling trace")
        return msgbytes

    def trace_reflevel(self, val="auto"):
        # split call for TRACE. sets the reference level of a trace
        writebyte = 'trace reflevel' + str(val) + '\r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("setting reference level of trace")
        return msgbytes

    def trace_value(self, ID):
        # split call for TRACE. gets values of trace

        writebyte = 'trace' + str(ID) + 'value \r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("getting raw trace values")
        return msgbytes

    def trace_toggle(self, ID, val="on"):
        # split call for TRACE. toggle trace ON or OFF
        # full description: displays all or one trace information
        # or sets trace related information
        # usage: 
        # trace [ {0..2} | 
        # dBm|dBmV|dBuV|V|W |store|clear|subtract | (scale|
        # reflevel) auto|{level}
        # example return: 

        accepted_vals = ["on", "off"]

        if (isinstance(ID,int)) and (str(val) in accepted_vals):
            writebyte = 'trace' + str(ID) + ' ' +str(val)+ '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("toggling trace " +str(val))
        else:
            self.print_message("ERROR: trace ID is an Int, val='on'|'off'")
            msgbytes = self.error_byte_return()

        return msgbytes

    def trace_subtract(self, ID1, ID2):
        # split call for TRACE. subtracts a trace/traces. 
        # subtract ID1 FROM ID2

        if (isinstance(ID1,int)) and (isinstance(ID2,int)):
            writebyte = 'trace' + str(ID1) + ' subtract ' +str(ID2)+ '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("subtracting traces")
        else:
            self.print_message("ERROR: trace IDs must be Ints")
            msgbytes = self.error_byte_return()

        return msgbytes

    def trace_copy(self, ID1, ID2):
        # split call for TRACE. copies a trace/traces. 

        if (isinstance(ID1,int)) and (isinstance(ID2,int)):
            writebyte = 'trace' + str(ID1) + ' subtract ' +str(ID2)+ '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("copying traces")
        else:
            self.print_message("ERROR: trace IDs must be Ints")
            msgbytes = self.error_byte_return()

        return msgbytes

    def trace_freeze(self, ID):
        # split call for TRACE. freezes a trace

        if (isinstance(ID,int)):
            writebyte = 'trace' + str(ID) + ' freeze\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("freezing trace")
        else:
            self.print_message("ERROR: trace ID must be Ints")
            msgbytes = self.error_byte_return()

        return msgbytes


    def trace_clear(self, val):
        # split call for TRACE. clears a trace/traces. doesnt seem to take inputs
        # full description: displays all or one trace information
        # or sets trace related information
        # usage: 
        # trace [ {0..2} | 
        # dBm|dBmV|dBuV|V|W |store|clear|subtract | (scale|
        # reflevel) auto|{level}
        # example return: 

        writebyte = 'trace ' + str(val) + 'clear \r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("clearing trace(s)")
        return msgbytes



    def trace_freeze(self, ID):
        # split call for TRACE. sets the reference level of a trace
        # full description: displays all or one trace information
        # or sets trace related information
        # usage: 
        # trace [ {0..2} | 
        # dBm|dBmV|dBuV|V|W |store|clear|subtract | (scale|
        # reflevel) auto|{level}
        # example return: 

        writebyte = 'trace' + str(ID) + 'freeze \r\n'
        msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
        self.print_message("freezing trace")
        return msgbytes



    def trace_action(self, ID, val):
        # split call for TRACE. toggle trace ON or OFF
        # full description: displays all or one trace information
        # or sets trace related information
        # usage: 
        # trace [ {0..2} | 
        # dBm|dBmV|dBuV|V|W |store|clear|subtract | (scale|
        # reflevel) auto|{level}
        # example return: 

        accepted_vals = ["copy","freeze","subtract","view","value"]

        if (isinstance(ID,int)) and (str(val) in accepted_vals):
            writebyte = 'trace' + str(ID) + ' ' +str(val)+ '\r\n'
            msgbytes = self.nanoVNA_serial(writebyte, printBool=False) 
            self.print_message("setting trace action")
        else:
            self.print_message("ERROR: trace vals can be 'copy'|'freeze'|'subtract'|'view'|'value' and ID is an Int")
            msgbytes = self.error_byte_return()

        return msgbytes


    def version(self):
        # TODO
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
    # unit testing. not recomended to write program from here

    # create a new tinySA object    
    nvna = nanoVNA()
    # attempt to connect to previously discovered serial port
    #success = nvna.connect(port='COM10')

    # attempt to autoconnect
    found_bool, connected_bool = nvna.autoconnect()

    """
bytearray(b'trace {0|1|2|3|all} [logmag|phase|smith|linear|delay|swr|off] [src]\r')
    """


    # if port open, then complete task(s) and disconnect
    if connected_bool == True: # or  if success == True:
        print("device connected")
        nvna.set_verbose(True) #detailed messages
        nvna.set_error_byte_return(True) #get explicit b'ERROR'

        for cmd in ['marker auto 7' ]:
            print("##########################################################################")
            try:
                print("calling:: " + str(cmd) )
                msg = nvna.command(cmd)
                print(msg)
            except:
                print("No command " + str(cmd))


        # msg = nvna.nanoVNA_help()
        # print(msg)

        # msg = nvna.get_device_id() 
        # print(msg)
        

        nvna.disconnect()
    else:
        print("ERROR: could not connect to port")



