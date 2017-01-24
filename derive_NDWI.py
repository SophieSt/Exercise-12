# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 10:51:23 2017

@author: user
"""


# remember to set your working directories for both Python, but also Linux 
# import modules
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32
import numpy as np
import urllib
import tarfile
import fnmatch
import os
import matplotlib.pyplot as plt

# create data and output folder, if not yet existent
if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists('output'):
    os.makedirs('output')

# download Landsat data
url = 'https://www.dropbox.com/s/zb7nrla6fqi1mq4/LC81980242014260-SC20150123044700.tar.gz?dl=1'
urllib.urlretrieve(url, "data/Landsat.tar.gz")

# Extract all .tar / .tar.gz data in given directory
def extract_in_dir(directory):
    for filename in os.listdir(directory):
        if fnmatch.fnmatch(filename, '*.tar.gz'):
            tar = tarfile.open(directory + '/' + filename, 'r:gz')
            tar.extractall(directory)
            tar.close()
        elif fnmatch.fnmatch(filename, '*.tar'):
            tar = tarfile.open(directory + '/' + filename, 'r:')
            tar.extractall(directory)
            tar.close()

extract_in_dir('data')

# function to calculate a normalized difference index based on two bands
def calc_ratio(band1_path, band2_path, ratio_name):
    # Input Arguments: band1, band2, name of ratio to calculate (example: 'ndwi') 
    # The calculation is based on the formula: (first input - second input) / (first input + second input)
    
    # Open files
    band1 = gdal.Open(band1_path, GA_ReadOnly)
    band2 = gdal.Open(band2_path, GA_ReadOnly)
    
    # Read data into an array
    band1Arr = band4.ReadAsArray(0, 0, band4.RasterXSize, band1.RasterYSize)
    band2Arr = band5.ReadAsArray(0, 0, band5.RasterXSize, band2.RasterYSize)
    
    # set the data type
    band1Arr = band1Arr.astype(np.float32)
    band2Arr = band2Arr.astype(np.float32)
    
    # Derive the NDWI
    mask = np.greater(band1Arr + band2Arr, 0)
    
    # set np.errstate to avoid warning of invalid values (i.e. NaN values) in the divide 
    with np.errstate(invalid = 'ignore'):
        ratio = np.choose(mask, (-99, (band1Arr - band2Arr) / (band1Arr + band2Arr)))
        
    # Write the result to disk, output in folder 'output', filename: ratio_name
    driver = gdal.GetDriverByName('GTiff')
    outDataSet = driver.Create('output/' + ratio_name + '.tif', band1.RasterXSize, band1.RasterYSize, 1, GDT_Float32)
    outBand = outDataSet.GetRasterBand(1)
    outBand.WriteArray(ratio, 0, 0)
    outBand.SetNoDataValue(-99)
    
    # set the projection and extent information of the dataset to the projection of Input
    outDataSet.SetProjection(band1.GetProjection())
    outDataSet.SetGeoTransform(band1.GetGeoTransform())

    # Finally let's save it... or like in the OGR example flush it
    outBand.FlushCache()
    outDataSet.FlushCache()
    
    return ratio

# calculate NDWI
ndwi = calc_ratio('data/LC81980242014260LGN00_sr_band4.tif', 'data/LC81980242014260LGN00_sr_band5.tif', 'ndwi')

# plot NDWI with minimum -1, maximum +1 (calculation determines possible outcomes)
plt.imshow(ndwi, interpolation = 'nearest', vmin = -1, vmax = 1, cmap=plt.cm.gist_earth)
plt.title('NDWI based on Landsat Bands 4 and 5')
plt.show()

# transform into Lat/Long WGS84 in bash
bash_transform = 'gdalwarp -t_srs "EPSG:4326" output/ndwi.tif output/ndwi_ll.tif'
os.system(bash_transform)
bash_info = 'gdalinfo output/ndwi_ll.tif'
os.system(bash_info)
