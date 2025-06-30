#! /usr/bin/python3

##-------------------------------------------------------------------------------\
#   nanoVNA_python
#   './examples/using_command_func.py'
#   The command func can be used for commands or functionalities that exist on the 
#   nanoVNA series of devices but arent included in the library yet. There is NO
#   built in error checking for this process. 
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------\


# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA 


# create a new tinySA object    
nvna = nanoVNA()

# set the return message preferences 
nvna.set_verbose(True) #detailed messages
nvna.set_error_byte_return(True) #get explicit b'ERROR' if error thrown


# attempt to autoconnect
found_bool, connected_bool = nvna.autoconnect()

# if port closed, then return error message
if connected_bool == False:
    print("ERROR: could not connect to port")
else: # if port found and connected, then complete task(s) and disconnect

    # scan
    data_bytes = nvna.command("scan 150000 250000000 200 2")

    print(data_bytes)

    nvna.resume() #resume 

    nvna.disconnect()

