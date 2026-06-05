#! /usr/bin/python3

##--------------------------------------------------------------------\
#   tinySA_python  config_tinysa_basic.py
#   
#   Configurations for the tinySA Ultra ZS405. Refer to the 
#   README for information on format and arguments. 
#   Format based on device library. 
#
#   See https://www.tinysa.org/wiki/ for official documentation.
#   https://tinysa.org/wiki/pmwiki.php?n=Main.Specification
#   https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Comparison
#
#   Author(s): Lauren Linkous
#   Last update: May 30, 2025
##--------------------------------------------------------------------\

DEVICE_TYPE = "BASIC"

## screen
SCREEN_WIDTH = 320      # size in pixels
SCREEN_HEIGHT = 240     # size in pixels
SCREEN_SIZE_IN = 2.8    # size in inches
DISPLAY_PTS = 290       # max num scan points displayed on screen
    #  51, 101, 145 or 290 
#16 bits per RGB pixel
