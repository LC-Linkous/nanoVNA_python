#!/usr/bin/python3
##-------------------------------------------------------------------------------
#   nanoVNA_python
#   './examples/plotting_scan.py'
#   A short example using matplotlib to plot requested SCAN data
#   Modified to handle S11 data with real/imaginary or magnitude/phase pairs
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------

# import NanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA
# imports FOR THE EXAMPLE
import numpy as np
import matplotlib.pyplot as plt

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



# create a new tinySA object    
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
    pts = 200         # sample points. MAX 201
    outmask = 2       # get measured data (y axis)
    
    # scan
    data_bytes = nvna.scan(start, stop, pts, outmask)
    print("Raw data received:")
    print(data_bytes)
    
    nvna.resume() # resume so screen isn't still frozen
    nvna.disconnect()
    
    # processing after disconnect
    # This is typical for the examples, but does not need to be done
    # if you are sitll using the device or collecting data.


    # convert data to arrays
    freq_arr, real_arr, imag_arr, magnitude_db, phase_deg = convert_s11_data_to_arrays(start, stop, pts, data_bytes)
    
    # Create subplots for comprehensive S11 visualization
    # this is different from the tinySA plots, which only showed the frequency data overlapped
    # because we are collecting more data with each sweep. 
    # Data has been sorted into 4 plots
     # The Antenna used in data collection is a 2.4 GHz monopole

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Real and Imaginary parts
    ax1.plot(freq_arr/1e9, real_arr, 'b-', label='Real', linewidth=1.5)
    ax1.plot(freq_arr/1e9, imag_arr, 'r-', label='Imaginary', linewidth=1.5)
    ax1.set_xlabel("Frequency (GHz)")
    ax1.set_ylabel("S11 Components")
    ax1.set_title("S11 Real and Imaginary Components")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Magnitude in dB
    ax2.plot(freq_arr/1e9, magnitude_db, 'g-', linewidth=1.5)
    ax2.set_xlabel("Frequency (GHz)")
    ax2.set_ylabel("S11 Magnitude (dB)")
    ax2.set_title("S1 Magnitude Response")
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Phase
    ax3.plot(freq_arr/1e9, phase_deg, 'm-', linewidth=1.5)
    ax3.set_xlabel("Frequency (GHz)")
    ax3.set_ylabel("S11 Phase (degrees)")
    ax3.set_title("S11 Phase Response")
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Smith Chart representation (simplified)
    ax4.scatter(real_arr, imag_arr, c=freq_arr/1e9, cmap='viridis', s=20)
    ax4.set_xlabel("Real Part")
    ax4.set_ylabel("Imaginary Part")
    ax4.set_title("S11 Complex Plane (Simplified Smith Chart)")
    ax4.grid(True, alpha=0.3)
    ax4.axis('equal')
    
    # Add colorbar for frequency reference
    cbar = plt.colorbar(ax4.collections[0], ax=ax4)
    cbar.set_label('Frequency (GHz)')
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print(f"\nData Summary:")
    print(f"Number of valid data points: {len(real_arr)}")
    print(f"Frequency range: {freq_arr[0]/1e9:.3f} - {freq_arr[-1]/1e9:.3f} GHz")
    print(f"S_{11} Magnitude range: {np.min(magnitude_db):.2f} to {np.max(magnitude_db):.2f} dB")
    print(f"S_{11} Phase range: {np.min(phase_deg):.1f} to {np.max(phase_deg):.1f} degrees")