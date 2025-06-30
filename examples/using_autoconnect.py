#! /usr/bin/python3

##-------------------------------------------------------------------------------\
#   nanoVNA_python
#   './examples/using_autoconnect.py'
#   This is an example of using the autoconnect feature. 
#   The detected device info is returned and the serial disconnected
#
#   Last update: June 18, 2025
##-------------------------------------------------------------------------------\

# import nanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA 

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

    msg = nvna.get_info() 
    print(msg)
    

    nvna.disconnect()
else:
    print("ERROR: could not connect to port")