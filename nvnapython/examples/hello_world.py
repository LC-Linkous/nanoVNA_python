#! /usr/bin/python3

##-------------------------------------------------------------------------------\
#   nanoVNA_python
#   './examples/hello_world.py'
#   This is a minimal example of how to use the nvnapython library.
#   Install the package first (from the repo root: pip install -e .),
#   then this script can import it from anywhere.
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------\

# import nanoVNA library
# (installed package: pip install -e . from the repo root)
from nvnapython import nanoVNA 

#import for EXAMPLE
import matplotlib.pyplot as plt

# create a new nanoVNA object    
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


