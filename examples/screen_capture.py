#! /usr/bin/python3

##-------------------------------------------------------------------------------\
#   tinySA_python
#   './examples/screen_capture.py'
#   This is an example of using the autoconnect feature. 
#   The detected device info is returned and the serial disconnected
#
#   Last update: June 30, 2025
##-------------------------------------------------------------------------------\

# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA 

# imports FOR THE EXAMPLE
import numpy as np
from PIL import Image
import struct

def convert_data_to_image(data_bytes, width, height):
    # calculate the expected data size
    expected_size = width * height * 2  # 16 bits per pixel (BGR565), 2 bytes per pixel
    
    # error checking
    if len(data_bytes) < expected_size:
        print(f"Data size is too small. Expected {expected_size} bytes, got {len(data_bytes)} bytes.")
        if len(data_bytes) == expected_size - 1:
            print("Data size is 1 byte smaller than expected. Adding 1 byte of padding.")
            data_bytes.append(0)
        else:
            return
    elif len(data_bytes) > expected_size:
        data_bytes = data_bytes[:expected_size]
        print("Data is larger than the expected size. truncating. check data.")
    
    num_pixels = width * height
    
    # Unpack as little-endian 16-bit values
    x = struct.unpack(f"<{num_pixels}H", data_bytes)
    arr = np.array(x, dtype=np.uint32)
    

    # Convert RGB565 to RGBA
    # The NanoVNA uses BGR565 format.
    # This is a difference from the tinySA_python library which used RGB565. This is pulled out
    # into variables to make it clearer where/what the switch is.
    blue = ((arr & 0xF800) >> 11) * 255 // 31    # Blue in high bits (15-11)
    green = ((arr & 0x07E0) >> 5) * 255 // 63    # Green in middle bits (10-5)
    red = (arr & 0x001F) * 255 // 31             # Red in low bits (4-0)
    
    # Combine into RGBA format (Alpha = 255 for opaque)
    arr_rgba = 0xFF000000 + (red << 16) + (green << 8) + blue
    
    # reshape array to match the image dimensions
    arr_rgba = arr_rgba.reshape((height, width))
    
    # create and save the image
    img = Image.frombuffer('RGBA', (width, height), arr_rgba.tobytes(), 'raw', 'RGBA', 0, 1)
    img.save("capture_example.png")
    img.show()

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

    
    msg = nvna.get_info() 
    print(msg)
    
    # get the trace data
    data_bytes = nvna.capture() 
    print(data_bytes)
    nvna.disconnect()

    # processing after disconnect (just for this example)
    # test with 800x480 resolution for NanoVNA-F V2
    convert_data_to_image(data_bytes, 800, 480) 

else:
    print("ERROR: could not connect to port")


