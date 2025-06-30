#!/usr/bin/python3
##-------------------------------------------------------------------------------
#   nanoVNA_python
#   './examples/plotting_s11_waterfall.py'
#   A waterfall plot example for S11 data using matplotlib.
#   The waterfall plot is shown after data is collected and exported
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------

# import nanoVNA library
# (NOTE: check library path relative to script path)
from src.nanoVNA_python import nanoVNA

# imports FOR THE EXAMPLE
import csv
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

def convert_s11_data_to_arrays(start, stop, pts, data):
    """
    Convert S11 data to frequency and S11 arrays.
    Assumes data contains pairs of values (real/imag).
    """
    # Create frequency array
    freq_arr = np.linspace(start, stop, pts)
    
    # Handle error data replacement
    data1 = bytearray(data.replace(b"-:.0", b"-10.0"))
    
    # Parse data into pairs of values
    lines = data1.decode('utf-8').split('\n')
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
    magnitude_db = 20 * np.log10(np.sqrt(real_arr**2 + imag_arr**2))
    phase_deg = np.degrees(np.arctan2(imag_arr, real_arr))
    
    # Adjust frequency array to match actual data length
    actual_pts = len(real_arr)
    if actual_pts != pts:
        freq_arr = np.linspace(start, stop, actual_pts)
    
    return freq_arr, real_arr, imag_arr, magnitude_db, phase_deg

def collect_s11_waterfall_data(nvna, start, stop, pts, outmask, num_scans, scan_interval):
    """
    Collect multiple S11 scans for waterfall plot
    """
    waterfall_real = []      # 2D array for real components
    waterfall_imag = []      # 2D array for imaginary components  
    waterfall_magnitude = [] # 2D array for magnitude in dB
    waterfall_phase = []     # 2D array for phase in degrees
    timestamps = []
    freq_arr = None
    
    print(f"Collecting {num_scans} S11 scans with {scan_interval}s intervals...")
    
    for i in range(num_scans):
        print(f"Scan {i+1}/{num_scans}")
        
        # Perform scan
        data_bytes = nvna.scan(start, stop, pts, outmask)
        
        # Convert to arrays
        if freq_arr is None:
            freq_arr, real_arr, imag_arr, mag_arr, phase_arr = convert_s11_data_to_arrays(start, stop, pts, data_bytes)
        else:
            _, real_arr, imag_arr, mag_arr, phase_arr = convert_s11_data_to_arrays(start, stop, pts, data_bytes)
        
        # Store data and timestamp
        waterfall_real.append(real_arr)
        waterfall_imag.append(imag_arr)
        waterfall_magnitude.append(mag_arr)
        waterfall_phase.append(phase_arr)
        timestamps.append(datetime.now())
        
        # Wait before next scan (except for last scan)
        if i < num_scans - 1:
            time.sleep(scan_interval)
    
    return (freq_arr, 
            np.array(waterfall_real), 
            np.array(waterfall_imag),
            np.array(waterfall_magnitude), 
            np.array(waterfall_phase), 
            timestamps)

def plot_s11_waterfall(freq_arr, waterfall_real, waterfall_imag, waterfall_magnitude, waterfall_phase, timestamps, start, stop):
    """
    Create comprehensive S11 waterfall plots
    """
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Create time array for y-axis
    time_arr = np.arange(len(timestamps))
    freq_mesh, time_mesh = np.meshgrid(freq_arr, time_arr)
    
    # Plot 1: S11 Magnitude waterfall
    im1 = ax1.pcolormesh(freq_mesh/1e9, time_mesh, waterfall_magnitude, 
                        shading='nearest', cmap='viridis')
    ax1.set_xlabel('Frequency (GHz)')
    ax1.set_ylabel('Scan Number')
    ax1.set_title(f'S11 Magnitude Waterfall: {start/1e9:.1f} - {stop/1e9:.1f} GHz')
    cbar1 = plt.colorbar(im1, ax=ax1)
    cbar1.set_label('S11 Magnitude (dB)')
    
    # Plot 2: S11 Phase waterfall
    im2 = ax2.pcolormesh(freq_mesh/1e9, time_mesh, waterfall_phase, 
                        shading='nearest', cmap='plasma')
    ax2.set_xlabel('Frequency (GHz)')
    ax2.set_ylabel('Scan Number')
    ax2.set_title('S11 Phase Waterfall')
    cbar2 = plt.colorbar(im2, ax=ax2)
    cbar2.set_label('S11 Phase (degrees)')
    
    # Plot 3: Latest S11 Magnitude scan
    ax3.plot(freq_arr/1e9, waterfall_magnitude[-1], 'b-', linewidth=1.5)
    ax3.set_xlabel('Frequency (GHz)')
    ax3.set_ylabel('S11 Magnitude (dB)')
    ax3.set_title('Latest S11 Magnitude Scan')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Latest S11 Phase scan
    ax4.plot(freq_arr/1e9, waterfall_phase[-1], 'r-', linewidth=1.5)
    ax4.set_xlabel('Frequency (GHz)')
    ax4.set_ylabel('S11 Phase (degrees)')
    ax4.set_title('Latest S11 Phase Scan')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

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
    try:
        # set scan values
        start = int(1e9)  # 1 GHz
        stop = int(3e9)   # 3 GHz
        pts = 200         # sample points
        outmask = 2       # get measured data (y axis)
        
        # waterfall parameters
        num_scans = 20        # number of scans to collect
        scan_interval = 1.0   # seconds between scans
        
        # collect waterfall data
        (freq_arr, waterfall_real, waterfall_imag, 
         waterfall_magnitude, waterfall_phase, timestamps) = collect_s11_waterfall_data(
            nvna, start, stop, pts, outmask, num_scans, scan_interval)
        
        print("S11 data collection complete!")
        
        # resume and disconnect
        nvna.resume() # resume so screen isn't still frozen
        nvna.disconnect()
        
        # processing after disconnect
        print("Creating S11 waterfall plots...")
        
        # create waterfall plot
        fig = plot_s11_waterfall(freq_arr, waterfall_real, waterfall_imag, 
                                waterfall_magnitude, waterfall_phase, timestamps, start, stop)
        
        # Save data to CSV
        filename = "s11_waterfall_sample.csv"
        
        # Create CSV with comprehensive S11 data
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            header = ['Scan_Number', 'Timestamp']
            for freq in freq_arr:
                header.extend([f'{freq:.0f}_Real', f'{freq:.0f}_Imag', 
                              f'{freq:.0f}_Mag_dB', f'{freq:.0f}_Phase_deg'])
            writer.writerow(header)
            
            # Write data rows
            for i in range(len(timestamps)):
                row = [i+1, timestamps[i].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]
                for j in range(len(freq_arr)):
                    row.extend([
                        f'{waterfall_real[i][j]:.6f}',
                        f'{waterfall_imag[i][j]:.6f}',
                        f'{waterfall_magnitude[i][j]:.3f}',
                        f'{waterfall_phase[i][j]:.2f}'
                    ])
                writer.writerow(row)
        
        print(f"S11 waterfall data saved to {filename}")
        print(f"CSV contains {len(timestamps)} scans with {len(freq_arr)} frequency points each")
        print(f"Each frequency point includes: Real, Imaginary, Magnitude (dB), Phase (deg)")
        
        # Statistics
        print(f"\nScan Statistics:")
        print(f"Frequency range: {freq_arr[0]/1e9:.3f} - {freq_arr[-1]/1e9:.3f} GHz")
        print(f"S11 Magnitude range: {np.min(waterfall_magnitude):.2f} to {np.max(waterfall_magnitude):.2f} dB")
        print(f"S11 Phase range: {np.min(waterfall_phase):.1f} to {np.max(waterfall_phase):.1f} degrees")
        
        # show plot
        plt.show()

    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        nvna.resume()
        nvna.disconnect()
    except Exception as e:
        print(f"Error occurred: {e}")
        nvna.resume()
        nvna.disconnect()