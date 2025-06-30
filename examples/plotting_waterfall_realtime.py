#!/usr/bin/python3
##-------------------------------------------------------------------------------
#   nanoVNA_python
#   './examples/plotting_waterfall_realtime.py'
#   A waterfall plot example for S11 data using matplotlib.
#   The waterfall plot is shown after data is collected and exported
#
#   Last update: June 29, 2025
##-------------------------------------------------------------------------------

# import nanoVNA library
from src.nanoVNA_python import nanoVNA

# imports FOR THE EXAMPLE
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
from datetime import datetime
import threading
import queue

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
        if line.strip():
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
                    continue
    
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

class LiveS11Plotter:
    def __init__(self, nvna, start, stop, pts, outmask, max_history=50):
        self.nvna = nvna
        self.start = start
        self.stop = stop
        self.pts = pts
        self.outmask = outmask
        self.max_history = max_history
        
        # Data storage
        self.freq_arr = None
        self.magnitude_history = deque(maxlen=max_history)
        self.phase_history = deque(maxlen=max_history)
        self.real_history = deque(maxlen=max_history)
        self.imag_history = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        
        # Threading for data acquisition
        self.data_queue = queue.Queue()
        self.running = False
        self.data_thread = None
        
        # Current data for single-trace plots
        self.current_magnitude = None
        self.current_phase = None
        self.current_real = None
        self.current_imag = None
        
    def data_acquisition_thread(self):
        #background thread for continuous data acquisition
        while self.running:
            try:
                # Get scan data
                data_bytes = self.nvna.scan(self.start, self.stop, self.pts, self.outmask)
                
                # Convert to arrays
                freq_arr, real_arr, imag_arr, mag_arr, phase_arr = convert_s11_data_to_arrays(
                    self.start, self.stop, self.pts, data_bytes)
                
                # Put data in queue for main thread
                self.data_queue.put({
                    'freq': freq_arr,
                    'real': real_arr,
                    'imag': imag_arr,
                    'magnitude': mag_arr,
                    'phase': phase_arr,
                    'timestamp': datetime.now()
                })
                
                time.sleep(0.15)  # Small delay to prevent overwhelming the device
                        # this might need to be tuned based on the device and how many points are taken
                
            except Exception as e:
                print(f"Data acquisition error: {e}")
                break
    
    def start_acquisition(self):
        # start the thread
        self.running = True
        self.data_thread = threading.Thread(target=self.data_acquisition_thread)
        self.data_thread.daemon = True
        self.data_thread.start()
    
    def stop_acquisition(self):
       # stop the thread
        self.running = False
        if self.data_thread:
            self.data_thread.join()
    
    def update_plots(self, frame):
        
        # Get all available data from queue
        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                
                # Store frequency array (first time only)
                if self.freq_arr is None:
                    self.freq_arr = data['freq']
                
                # Update current data
                self.current_magnitude = data['magnitude']
                self.current_phase = data['phase']
                self.current_real = data['real']
                self.current_imag = data['imag']
                
                # Add to history
                self.magnitude_history.append(data['magnitude'])
                self.phase_history.append(data['phase'])
                self.real_history.append(data['real'])
                self.imag_history.append(data['imag'])
                self.timestamps.append(data['timestamp'])
                
            except queue.Empty:
                break
        
        # Clear all plots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.clear()
        
        if self.freq_arr is not None and self.current_magnitude is not None:
            # Plot 1: Current S11 Magnitude
            ax1.plot(self.freq_arr/1e9, self.current_magnitude, 'b-', linewidth=1.5)
            ax1.set_xlabel('Frequency (GHz)')
            ax1.set_ylabel('S11 Magnitude (dB)')
            ax1.set_title('Live S11 Magnitude')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Current S11 Phase
            ax2.plot(self.freq_arr/1e9, self.current_phase, 'r-', linewidth=1.5)
            ax2.set_xlabel('Frequency (GHz)')
            ax2.set_ylabel('S11 Phase (degrees)')
            ax2.set_title('Live S11 Phase')
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: S11 Magnitude Waterfall (recent history)
            if len(self.magnitude_history) > 1:
                waterfall_mag = np.array(list(self.magnitude_history))
                time_arr = np.arange(len(waterfall_mag))
                freq_mesh, time_mesh = np.meshgrid(self.freq_arr, time_arr)
                
                im = ax3.pcolormesh(freq_mesh/1e9, time_mesh, waterfall_mag, 
                                   shading='nearest', cmap='viridis')
                ax3.set_xlabel('Frequency (GHz)')
                ax3.set_ylabel('Time (scans ago)')
                ax3.set_title('S11 Magnitude History')
            
            # Plot 4: Complex plane (Smith chart style)
            ax4.scatter(self.current_real, self.current_imag, 
                       c=self.freq_arr/1e9, cmap='plasma', s=10, alpha=0.7)
            ax4.set_xlabel('Real Part')
            ax4.set_ylabel('Imaginary Part')
            ax4.set_title('S11 Complex Plane')
            ax4.grid(True, alpha=0.3)
            ax4.axis('equal')
        
        # Add timestamp
        if self.timestamps:
            fig.suptitle(f'Live S11 Measurement - {self.timestamps[-1].strftime("%H:%M:%S")}', 
                        fontsize=14)

# Main execution
if __name__ == "__main__":
    # create a new nanoVNA object    
    nvna = nanoVNA()
    # set the return message preferences
    nvna.set_verbose(True)
    nvna.set_error_byte_return(True)

    # attempt to autoconnect
    found_bool, connected_bool = nvna.autoconnect()

    if not connected_bool:
        print("ERROR: could not connect to port")
    else:
        try:
            print("Starting live S11 measurement...")
            print("Close the plot window to stop measurement")
            
            # Scan parameters
            start = int(1e9)  # 1 GHz
            stop = int(3e9)   # 3 GHz
            pts = 150         # Reduced points for faster updates
            outmask = 2       # get measured data
            
            # Create plotter
            plotter = LiveS11Plotter(nvna, start, stop, pts, outmask, max_history=30)
            
            # Set up the plot
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            plt.subplots_adjust(hspace=0.3, wspace=0.3)
            
            # Start data acquisition
            plotter.start_acquisition()
            
            # Create animation
            ani = animation.FuncAnimation(fig, plotter.update_plots, 
                                        interval=200, blit=False)
            
            # Show plot (this blocks until window is closed)
            plt.show()
            
            # Cleanup
            plotter.stop_acquisition()
            nvna.resume()
            nvna.disconnect()
            
            print("Live measurement stopped")
            
        except KeyboardInterrupt:
            print("\nMeasurement interrupted by user")
            nvna.resume()
            nvna.disconnect()
        except Exception as e:
            print(f"Error occurred: {e}")
            nvna.resume()
            nvna.disconnect()