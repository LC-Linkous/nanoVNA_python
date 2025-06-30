#! /usr/bin/python3

##-------------------------------------------------------------------------------\
#   nanoVNA_python
#   './examples/hello_world.py'
#   This is an example of how to use the current nanoVNApython library. 
#   Note how this file is OUTSIDE the ./src folder, which contains the 
#   nanoVNA_python.py library file
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------\

# import tinySA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA 

#import for EXAMPLE
import matplotlib.pyplot as plt

# create a new tinySA object    
nvna = nanoVNA()

# set the return message preferences 
nvna.set_verbose(True) #detailed messages
nvna.set_error_byte_return(True) #get explicit b'ERROR' if error thrown


# attempt to autoconnect
found_bool, connected_bool = nvna.autoconnect()

# if port found and connected, then complete task(s) and disconnect
if connected_bool == True: 
    print("device connected")

    # print the device info
    msg = nvna.info() 
    print(msg)

    # disconnect because we don't need the serial connection anymore
    nvna.disconnect()
else:
    print("ERROR: could not connect to port")


