#!/usr/bin/python3
##-------------------------------------------------------------------------------
#   nanoVNA_python
#   './examples/plotting_scan.py'
#   Scan and save data to .csv file. Records the data with the frequency based
#   on the range of the scan()
#
#   Last update: June 30, 2025
##-------------------------------------------------------------------------------

# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA
# imports FOR THE EXAMPLE
import csv
import numpy as np

def convert_s11_data_to_arrays(start, stop, pts, data):
    # Convert the raw data so that the frequency, real, and imaginary are all stored.

    # Create frequency array
    freq_arr = np.linspace(start, stop, pts)
    
    # Parse data into pairs of values (real/imaginary)
    lines = data.decode('utf-8').split('\n')
    real_parts = []
    imag_parts = []
    
    for line in lines:
        if line.strip():
            values = line.split()
            if len(values) >= 2:
                try:
                    real_val = float(values[0])
                    imag_val = float(values[1])
                    real_parts.append(real_val)
                    imag_parts.append(imag_val)
                except ValueError:
                    continue
    
    # Convert to numpy arrays
    real_arr = np.array(real_parts)
    imag_arr = np.array(imag_parts)
    
    # Adjust frequency array to match actual data length
    actual_pts = len(real_arr)
    if actual_pts != pts:
        freq_arr = np.linspace(start, stop, actual_pts)
    
    return freq_arr, real_arr, imag_arr

# create a new nanoVNA object    
nvna = nanoVNA()
# set the return message preferences
nvna.set_verbose(True) #detailed messages
nvna.set_error_byte_return(True) #get explicit b'ERROR' if error thrown

# attempt to autoconnect
found_bool, connected_bool = nvna.autoconnect()

# if port closed, then return error message
if connected_bool == False:
    print("ERROR: could not connect to port")
else: 
    # if port found and connected, then complete task(s) and disconnect
    # the S11 (return loss) data is the default collection for this tutorial
    print("Connected to nanoVNA - collecting S11 data...")
    
    # set scan values
    start = int(1e9)  # 1 GHz
    stop = int(3e9)   # 3 GHz
    pts = 200         # sample points
    outmask = 2       # get measured data 
    
    # scan for S11 data
    data_bytes = nvna.scan(start, stop, pts, outmask)
    print(f"Received {len(data_bytes)} bytes of S11 data")

    nvna.resume() #resume so screen isn't still frozen

    # disconnect because in this example we're done reading from device
    nvna.disconnect()
    
    # processing after disconnect
    # convert data to 3 arrays: frequency, real, imaginary
    freq_arr, real_arr, imag_arr = convert_s11_data_to_arrays(start, stop, pts, data_bytes)
    
    # Save the RAW data to CSV
    filename = "s11_raw_data.csv"
       
    # Write out to csv: frequency, real, imaginary
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header row
        writer.writerow(['Frequency_Hz', 'S11_Real', 'S11_Imaginary'])

        # Write data rows (frequency, real, imaginary triplets)
        for freq, real, imag in zip(freq_arr, real_arr, imag_arr):
            writer.writerow([f'{freq:.0f}', f'{real:.6f}', f'{imag:.6f}'])

    print(f"RAW S11 data saved to {filename}")
    print(f"Total: {len(freq_arr)} data points saved")
   