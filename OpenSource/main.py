# -*- coding: utf-8 -*-
'''----------------------------------------------------------------------------------
File Name      : main.py
Author         : Mehran Ghandehari
Organization   : University of Colorado at Boulder
Created        : Dec. 20th, 2016
Python Version : 2.7

-- Description --
**Surface-adjusted elevation is calculated in this code using different interpolation 
methods and different contiguity configurations across different resolutions
**Note: Lidar data (3 DEM) is used as benchmark
----------------------------------------------------------------------------------'''
# Import modules
import os
from time import time
import geopandas as gpd
import pandas as pd
import rasterio

# Import my modules
import findValue # This module extracts value of a point from raster. Also it is possible to extract a chunck of raster centered on the point
import neighbors # create the proper contiguity configuration for an interpolation method
import polyInterpolation # Polynomial interpolation
import inverseDistanecWeighting # IDW interpolation

if __name__ == '__main__':

    # Set the current workspace
    os.chdir(r"E:\Surface_adjusted\ICC17\Code\Data\NC_cub_resample2")

    # Results are saved in the following directory
    output = r"E:\Surface_adjusted\ICC17\Code\Python\OpenSource\Results"
    if os.path.isdir(output) == False:
        print("The output directoru does not exist")

    # Input data (DEMs)
    benchmark = 'dem3m'
    DEMs = ['dem10m', 'dem30m', 'dem100m', 'dem1000m']
    resolutions = [10, 30, 100, 1000]
    
    #Random points: extract the benchmark elevation of each point from 3m lidar
    with rasterio.open(benchmark) as dem3m:
        samples = gpd.read_file(output + r'\randomPnts.shp') # randomPnts shapefile is imported a geodataframe
        samples['elev3m'] = None # adding a new attribute "elev3m" to the geodataframe
        for index, row in samples.iterrows():
            X = row['geometry'].x
            Y = row['geometry'].y
            samples.at[index, 'elev3m'] = findValue.extractValue(X,Y,dem3m).astype('float64')

    # Create the residual geodataframe. This dataframe is completed at the end
    residuals = samples.copy()

    # Methods used for calculating surface area
    methods = ['WP', 'WA4', 'Li3', 'BiLi4', 'BiQ9', 'BiC16']

	# Declare vaqriable to keep track of time for each interpolation method
    for mth in methods:
        globals()['time' + mth] = 0

    #Add new feilds to the the "samples" feature class based on all combinations of resolutions and methods
    fields = []
    for res in resolutions:
        for mth in methods:
            samples[mth + str(int(res))] = None
            fields = fields + [mth + str(res)]
        
    for dem in DEMs:  # for each resolution surface-adjusted elevations are estimated for various interpolation methods
        with rasterio.open(dem) as src:
            cellSize = src.transform[1] # get actual DEM resolution fo computations
            res = resolutions[DEMs.index(dem)] # get nominal DEM resolution for labeling

            for index, row in samples.iterrows(): # iterating through all of the points
                X = row['geometry'].x
                Y = row['geometry'].y
                # The extractWindow function in the findValue module returns the 5*5 elevation matrix for the DEM based on the point
                # The coordinate of the central pixel is (0,0). x,y are the coordinates of the point in this local coordinate system
                x, y, rasterBlock_x, rasterBlock_y, rasterBlock_elev = findValue.extractWindow(X, Y, src, cellSize)
                
                # for the point x,y, the n closest pixel value from the 5*5 matrix is selected
                xCoor1, yCoor1, elev1 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 1)
                xCoor3, yCoor3, elev3 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 3)
                xCoor4, yCoor4, elev4 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 4)
                xCoor9, yCoor9, elev9 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 9)
                xCoor16, yCoor16, elev16 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 16)
                
                #whithin a pixel
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'WP' + str(res)] = elev1.astype('float64')
                if dem == DEMs[0]: timeWP = timeWP + (time() - temp)
    
                #weighted average
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'WA4'+ str(res)] = inverseDistanecWeighting.IDW(x, y, xCoor4, yCoor4, elev4, 2).astype('float64')
                if dem == DEMs[0]: timeWA4 = timeWA4 + (time() - temp)
    
                #Linear interpolation
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'Li3'+ str(res)] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor3, yCoor3, elev3, 0)).astype('float64')
                if dem == DEMs[0]: timeLi3 = timeLi3 + (time() - temp)
    
                #Bilinear interpolation
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'BiLi4'+ str(res)] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor4, yCoor4, elev4, 1)).astype('float64')
                if dem == DEMs[0]: timeBiLi4 = timeBiLi4 + (time() - temp)
    
                #Biquadratic interpolation
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'BiQ9'+ str(res)] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor9, yCoor9, elev9, 2)).astype('float64')
                if dem == DEMs[0]: timeBiQ9 = timeBiQ9 + (time() - temp)
    
                #BiCubic interpolation
                if dem == DEMs[0]: temp = time()
                samples.at[index, 'BiC16'+ str(res)] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor16, yCoor16, elev16, 3)).astype('float64')
                if dem == DEMs[0]: timeBiC16 = timeBiC16 + (time() - temp)

    # calculating the residuals for each interpolation method  (3m DEM - estimated elevation)
    for fld in fields:
        residuals[fld] = samples['elev3m']-samples[fld]
    #     b = pd.DataFrame(samples[0:1000]['elev3m'])
    #     a = pd.DataFrame(samples[1000:2000][fld])
    #     import numpy as np
    #     a.index = np.arange(0, len(a))
    #     residuals[fld] = a[fld]-b['elev3m']
    # residuals.dropna()

    samples.to_file(driver = 'ESRI Shapefile', filename = output + r'\samples.shp') # Export estimated eleavtions as a shapefile
    residuals.to_file(driver = 'ESRI Shapefile', filename = output + r'\residuals.shp') # Export estimated residuals as a shapefile

    # Calculate statistics for the residuals
    df_stat = pd.DataFrame(index=fields, columns=['RMSE', 'MAE', 'MBE', 'STD', 'MIN', 'MAX'])
    for fld in fields:
        df_stat.loc[fld, 'RMSE'] = ((residuals[fld]) ** 2).mean() ** 0.5
        df_stat.loc[fld, 'MAE'] = (residuals[fld].abs()).mean()
        df_stat.loc[fld, 'MBE'] = residuals[fld].mean()
        df_stat.loc[fld, 'STD'] = residuals[fld].std()
        df_stat.loc[fld, 'MIN'] = residuals[fld].min()
        df_stat.loc[fld, 'MAX'] = residuals[fld].max()
    df_stat.to_csv(output + r'\result.csv', sep=',') # save the statistics as a csv file

    # print the timing
    for mth in methods:
        print ("Processing time for " + mth + "is: " + str(globals()['time' + mth]))









