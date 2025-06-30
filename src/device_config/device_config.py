# a class for device configuration settings
# this is for the CURRENT device config settings and some error logging

import os
import pandas as pd

try:
    from src.device_config.presets import config_tinysa_basic as tinyBasic
except:
    from device_config.presets import config_tinysa_basic as tinyBasic


class deviceConfig():
    def __init__(self, parent=None):
        self.name = "tinySA_device"
        self.deviceModel = None
        self.deviceConfig = None
        self.presetSelected = None

            
    def select_preset_model(self, model):

       
        if model == "BASIC":
            self.presetSelected = tinyBasic
        else:
            self.presetSelected = None
            self.deviceModel = None
            print("ERROR: selected preset not in library")
            return False
        

        self.deviceModel = model
        print("Device set successfully")
        return True
        
    # DEVICE CONFIG
    def set_default_params(self):
            df = pd.DataFrame({})

            #custom
            df['device_type'] = pd.Series(int(self.presetSelected.SCREEN_WIDTH))
            df['device_name'] = pd.Series(str(self.name))


            #screen
            df['screen_width'] = pd.Series(int(self.presetSelected.SCREEN_WIDTH))
            df['screen_height'] = pd.Series(int(self.presetSelected.SCREEN_HEIGHT))
            df['screen_size'] = pd.Series(int(self.presetSelected.SCREEN_SIZE_IN))
            df['screen_disp_pts'] = pd.Series(int(self.presetSelected.DISPLAY_PTS)) #default MAX
            self.deviceConfig = df
    
    def get_default_params(self):
        return self.deviceConfig
    

    # CUSTOM DEVICE NAME
    def set_device_name(self, n):
        self.name = str(n)
    
    def get_device_name(self):
        return self.name
    
    # LOAD/SAVE USER DEVICE CONFIGS
    def load_device_config(self, filepath):           
        if os.path.exists(filepath):
            self.deviceConfig = pd.read_table(filepath, sep=",", index_col=False)
        else:
            print("ERROR: path " + str(filepath) + " is not found")
    
    def save_device_config(self, filepath):
        if os.path.exists(filepath):
            self.deviceConfig.to_csv(filepath, delimiter=',', index=False)
        else:
            print("ERROR: path " + str(filepath) + " is not found")
    
