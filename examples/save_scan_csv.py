#!/usr/bin/python3
##-------------------------------------------------------------------------------
#   nanoVNA_python
#   './examples/save_s11_scan_csv.py'
#   A short example to save S11 scan data to CSV
#   Modified to handle S11 data with real/imaginary pairs
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------

# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA
# imports FOR THE EXAMPLE
import csv
import numpy as np

def convert_s11_data_to_arrays(start, stop, pts, data):
    # Convert the raw device S11 data to frequency and S11 arrays.
    # given the format of the data, this is assuming the data 
    # contains PAIRS of values (real/imag or mag/phase).


    # Create frequency array
    freq_arr = np.linspace(start, stop, pts)
    
    # Parse data into pairs of values
    lines = data.decode('utf-8').split('\n')
    real_parts = []
    imag_parts = []
    
    for line in lines:
        if line.strip():  # Skip empty lines
            values = line.split()
            if len(values) >= 2:
                try:
                    real_val = float(values[0])
                    imag_val = float(values[1])
                    
                    # Skip zero pairs (padding data)
                    if real_val != 0.0 or imag_val != 0.0:
                        real_parts.append(real_val)
                        imag_parts.append(imag_val)
                except ValueError:
                    continue  # Skip malformed lines
    
    # Convert to numpy arrays
    real_arr = np.array(real_parts)
    imag_arr = np.array(imag_parts)
    
    # Calculate derived values
    # If data is real/imaginary components:
    magnitude_db = 20 * np.log10(np.sqrt(real_arr**2 + imag_arr**2))
    phase_deg = np.degrees(np.arctan2(imag_arr, real_arr))
    
    # Adjust frequency array to match actual data length
    actual_pts = len(real_arr)
    if actual_pts != pts:
        freq_arr = np.linspace(start, stop, actual_pts)
    
    return freq_arr, real_arr, imag_arr, magnitude_db, phase_deg


# create a new nanoVNA object    
nvna = nanoVNA()
# set the return message preferences
nvna.set_verbose(True) # detailed messages
nvna.set_error_byte_return(True) # get explicit b'ERROR' if error thrown

# attempt to autoconnect
found_bool, connected_bool = nvna.autoconnect()

# if port closed, then return error message
if connected_bool == False:
    print("ERROR: could not connect to port")
else: # if port found and connected, then complete task(s) and disconnect
    # set scan values
    start = int(1e9)  # 1 GHz
    stop = int(3e9)   # 3 GHz
    pts = 200         # sample points
    outmask = 2       # get measured data (y axis)
    
    # scan
    data_bytes = nvna.scan(start, stop, pts, outmask)
    print(data_bytes)
    
    nvna.resume() # resume so screen isn't still frozen
    nvna.disconnect()
    
    # processing after disconnect (just for this example)
    # convert data to arrays
    freq_arr, real_arr, imag_arr, magnitude_db, phase_deg = convert_s11_data_to_arrays(start, stop, pts, data_bytes)
    
    # Save the S11 data to CSV
    filename = "s11_scan_sample.csv"
    
    # Write out to csv with all S11 parameters
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header row
        writer.writerow(['Frequency_Hz', 'S11_Real', 'S11_Imaginary', 'S11_Magnitude_dB', 'S11_Phase_deg'])
        
        # Write data rows
        for i in range(len(freq_arr)):
            writer.writerow([
                f'{freq_arr[i]:.0f}',
                f'{real_arr[i]:.6f}',
                f'{imag_arr[i]:.6f}',
                f'{magnitude_db[i]:.3f}',
                f'{phase_deg[i]:.2f}'
            ])
    
    print(f"S11 data saved to {filename}")
    print(f"CSV contains {len(freq_arr)} frequency/S11 parameter sets")
    print(f"Frequency range: {freq_arr[0]/1e9:.3f} - {freq_arr[-1]/1e9:.3f} GHz")
    print(f"S11 Magnitude range: {np.min(magnitude_db):.2f} to {np.max(magnitude_db):.2f} dB")
    print(f"S11 Phase range: {np.min(phase_deg):.1f} to {np.max(phase_deg):.1f} degrees")