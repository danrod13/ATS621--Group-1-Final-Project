#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 15:03:01 2026

@author: DannyRodriguez
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import cartopy
import cartopy.crs as ccrs
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import pandas as pd

#%% This little guy divides sections in Spyder so I can run each block individually. 
# It may not work in other IDEs.

# === File Reading ===
we_can_merge = 'Path/to/file/wecan-mrg01-c130_merge_20180809_R4.ict'

# === ICARRT Metadata ===
# We define a lil helper guy to define all the headers in the ICARTT file
def get_icartt_metadata( filepath, color_var ):
    """
    Reads the first line of the ICARTT file to determine header length, searches
    the header block for the requested variables units
    """
    unit ="unknown units"
    with open( filepath, 'r' ) as f:
        # ICARTT line 1: "Number of header lines, Data_format_code"
        first_line= f.readline()
        try:
            # Subtract 1 cuz we just read the first line
            header_lines = int( first_line.split(',')[0].strip()) - 1
        except ValueError:
            print( "Warning: Could not parse ICARTT header length, default to 400 (change this if you'd like)" )
            header_lines = 400
        
        # Search the remaining header lines for the variable definition
        for _ in range( header_lines ):
            line = f.readline()
            parts = [p.strip() for p in line.split(',')]
            
            # ICARTT variable definitions start with the var_name, then the units
            if parts[0] == color_var and len(parts) > 1:
                unit = parts[1]
                break
    # Return the total rows to ski for pandas (header_lines + 1 for the first line)
    return header_lines + 1, unit

# === Fxn Definition ===
# Define the function so we can call it whenever we want

def plot_aircraft_track( filepath, color_var='ALTP', vmin=None, vmax=None, scale=12, pan_lat=0.0, pan_lon=0.0 ):
    """
    Reads aircraft ICT/CSV data and plots the flight track colored by a specific variable.
    
    Parameters:
    - filepath (str): Path to the data file.
    - color_var (str): The column header to color the track by.
    - vmin (float): Minimum value for the colorbar (optional).
    - vmax (float): Maximum value for the colorbar (optional).
    - scale (int/float): Zoom scale for the map (smaller = tighter zoom).
    """
    # === Data loading and cleaning ===
    # Use the lil helper guy from above to get extract the units
    skip_rows, var_unit = get_icartt_metadata( filepath, color_var)
    
    # Read the data and strip whitespace from the col headers
    df = pd.read_csv( filepath, skiprows=400, sep=',', skipinitialspace=True )
    
    # Drop rows where ANY of our required cols have missing values (-9999999)
    df = df[ (df['LATITUDE'] != -9999999 ) &
             (df['LONGITUDE'] != -9999999 ) &
             (df['ALTP'] != -9999999) &
             (df[color_var] != -9999999 )]
    
    # Extract the final, clean arrays
    lat_data = df[ 'LATITUDE' ].to_numpy()
    lon_data = df[ 'LONGITUDE'].to_numpy()
    color_data = df[color_var].to_numpy()
    
    # === Plotting Setup ===
    plt.close( 'all' )
    plt.style.use( 'default' )
    fig=plt.figure( figsize=(15,10) )
    
    lat_center=np.mean( lat_data )
    lon_center=np.mean( lon_data )
    
    ax1 = plt.axes( projection=ccrs.Orthographic( central_latitude=lat_center, central_longitude=lon_center ))
    ax1.set_aspect( 'equal' )
    
    # Set spatial extent using scale variable
    ax1.set_extent(( lon_center + pan_lon - (0.5*scale), lon_center + pan_lon + (0.5*scale),
                    lat_center + pan_lat - (0.5*scale), lat_center + pan_lat + (0.5*scale)),
                    crs=ccrs.PlateCarree() )
    
    # === Map features ===
    ax1.add_feature(cartopy.feature.NaturalEarthFeature(
        category='cultural', scale='10m', facecolor='none', name='admin_1_states_provinces_shp'
    ), zorder=2, linewidth=0.5, edgecolor='grey', alpha=0.5)
    
    ax1.add_feature(cartopy.feature.RIVERS.with_scale('10m'), zorder=2, linewidth=1.0, edgecolor='lightblue')
    ax1.add_feature(cartopy.feature.LAKES.with_scale('10m'), zorder=2, linewidth=1.0, edgecolor='gray')

    try:
        reader = cartopy.io.shapereader.Reader('countyl010g.shp')
        counties = list(reader.geometries())
        COUNTIES = cartopy.feature.ShapelyFeature(counties, ccrs.PlateCarree())
        ax1.add_feature(COUNTIES, facecolor='none', alpha=0.5, zorder=2, edgecolor='gray')
    except Exception as e:
        print(f"Could not load counties: {e}")
        
    # === Flight track plotting ===
    # Create segments for LineCollection: pairs of (x, y) coordinates
    points = np.array([lon_data, lat_data]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Use provided vmin/vmax, otherwise default to the data's min/max
    cbar_vmin = vmin if vmin is not None else color_data.min()
    cbar_vmax = vmax if vmax is not None else color_data.max()
    
    norm = plt.Normalize(vmin=cbar_vmin, vmax=cbar_vmax)
    cmap = plt.get_cmap('viridis')
    
    # Create and add the LineCollection
    lc = LineCollection(segments, cmap=cmap, norm=norm, transform=ccrs.PlateCarree(), 
                        zorder=3, alpha=0.8, linewidth=5.0)
    lc.set_array(color_data[:-1])
    line = ax1.add_collection(lc)
    
    # === Colorbar ===
    cbar = fig.colorbar(line, ax=ax1, orientation='vertical', fraction=0.046, pad=0.04)
    # Note: You may want to pass a 'units' argument if you color by something other than ALTP
    cbar.set_label(f'{color_var} ({var_unit})', fontsize=20)
    cbar.ax.tick_params(labelsize=16)

    fig.tight_layout()
    plt.show()
    
    return fig, ax1

#%%
# To make quick adjustments: scale = zoom; 
#                            pan_lat = moves horizontally ( -: left, +: right)
#                            pan_lon = moves verticall    ( -: down, +: up )

plot_aircraft_track( we_can_merge, color_var= 'ALTP', scale = 1.3   , pan_lat = -1.5, pan_lon = 1.5 )

