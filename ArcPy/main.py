# -*- coding: utf-8 -*-
'''----------------------------------------------------------------------------------
File Name      : main.py
Author         : Mehran Ghandehari
Organization   : University of Colorado at Boulder
Created        : Mar. 20th, 2016
Python Version : 2.7

-- Description --
In this project we want to calculate surface-adjusted elevation using different interpolation methods

and different contiguity configurations across different resolutions
----------------------------------------------------------------------------------'''
#Import modules
import arcpy
import numpy as np
from arcpy import env
import arcpy.sa as sa
from time import time

#Import my modules
import neighbors
import polyInterpolation
import inverseDistanecWeighting

#Set Arcpy environment properties: Import arc license, set workspace, and set spatial reference
path = r"E:\Surface_adjusted\ICC17\Code\Python\main_V3\Results"
dataPath = r"E:\Surface_adjusted\ICC17\Code\Data\NC_cub"
env.workspace = path
env.overwriteOutput = 'True'
spatialRef = arcpy.Describe(dataPath + '\dem10m').spatialReference
arcpy.env.outputCoordinateSystem = spatialRef
arcpy.CheckOutExtension("Spatial")

#set the input parameters.
# The inputs are DEMs in 4 different resolutions (10m, 30m, 100m, and 1000m)
listDEM = [sa.Raster(dataPath + '\dem10m'), sa.Raster(dataPath + '\dem30m'), sa.Raster(dataPath + '\dem100m'), sa.Raster(dataPath + '\dem1000m')] # list of DEMs of different resolutions

#Generate random points and extract their benchmark elevation from 3m lidar
sampleSize = 20000 # Number of random points
#extent = dataPath + r"\extent.shp"
#arcpy.Buffer_analysis(extent, "extent_Buffer", buffer_distance_or_field="-5000 Meters", line_side="FULL", line_end_type="ROUND", dissolve_option="NONE", dissolve_field="", method="PLANAR")
#extent = "405786 3949655 509706 3972169" # "X_West Y_South X_East Y_North"
#arcpy.CreateRandomPoints_management(path, "randomPnts.shp", "extent_Buffer.shp", constraining_extent="0 0 250 250", number_of_points_or_field=sampleSize, minimum_allowed_distance="0 Millimeters", create_multipoint_output="POINT", multipoint_size="0")
samples = "samples.shp"
arcpy.gp.ExtractValuesToPoints_sa("randomPnts.shp", sa.Raster(dataPath + '\dem3m'), samples, "NONE", "VALUE_ONLY")# Extracting the elevation of random points from benchmark (here, 3m DEM)

#Deleting extra fields in the "samples" feature class and just keeping  FID and RASTERVALUE (3m elevation values)
try:
    discard = []
    for field in [f.name for f in arcpy.ListFields(samples)if f.type <> 'Geometry']:
        if field == 'FID' or field == 'OID' or field == 'RASTERVALU':
            pass
        else:
            discard.append(field)
    arcpy.DeleteField_management(samples, discard)
except:
    arcpy.GetMessages(2)

# List of diffrent resolutions, and DEM left lower points
rsolutions = [(i.meanCellWidth) for i in listDEM]
llpnts = [i.extent.lowerLeft for i in listDEM]

# list of attributes that would be added to the attribute table of the samples feature class (here are diffeent interpolation methods, and the number shows the contiguity configuration used for that method)
attributes = ['WP', 'WA4', 'Li3', 'BiLi4', 'BiQ9', 'BiC16']

# declare the variables for keeping running time of different interpolation methods
timeWP, timeWA4, timeLi3, timeBiLi4, timeBiQ9, timeBiC16 = 0, 0, 0, 0, 0, 0

#Add new feilds to the the "samples" feature class based on all combination of resolutions and methods
fields = ['OID@', 'SHAPE@']
for res in rsolutions:
    for att in attributes:
        arcpy.AddField_management(samples, att + str(int(res)), 'FLOAT')
        fields = fields + [att + str(int(res))]

#***********************************************************
# In he following code block, the table for the "samples" feature class is filled
with arcpy.da.UpdateCursor(samples, (fields)) as uCurs:
    for row in uCurs:
        Id =row[0] # ID of each sample point
        geom = row[1] # Geometry of each sample point
        i =1 # i is a counter for inserting the values into the right field
        for res in rsolutions:

            temp_dem = listDEM[rsolutions.index(res)] # get the corresponding DEM
            temp_llpnts = llpnts[rsolutions.index(res)]# get the left lower point of the corresponding DEM

            rasterBlock_elev = np.zeros((5,5)) # this 5 by 5 matrix would contain the elevation of 16 neighbor pixels of a sample point
            rasterBlock_x = np.zeros((5,5)) # this 5 by 5 matrix would contain the x coordinate of 16 neighbor pixels of a sample point
            rasterBlock_y = np.zeros((5,5)) # this 5 by 5 matrix would contain the y coordinate of 16 neighbor pixels of a sample point

            llpntsX  = temp_llpnts.X # left lower point X
            llpntsY  = temp_llpnts.Y # left lower point Y

            # x and y coordinate of current sample point in the cursor
            x = geom.firstPoint.X
            y = geom.firstPoint.Y

            # calculated the left lower coordinated of the cell encompass the current sample point
            cellX = ((int((x - llpntsX)/ res) * res) + llpntsX)
            cellY = ((int((y - llpntsY)/ res) * res) + llpntsY)

            # calculated the left lower coordinate of 16 cells to be used for interpolation
            llpnts16X = cellX - (2 * res)
            llpnts16Y = cellY - (2 * res)

            # Extract the elevation of a data block (we use the RasterToNumPyArray to extract only the 16 neighbor pixels of a sample point)
            # .5 has been added to the coordinate of the llpnts16X and llpnts16Y in order to prevent from the rounding error
            lowerLeft = arcpy.Point(llpnts16X+.5,llpnts16Y+.5)
            rasterBlock_elev = arcpy.RasterToNumPyArray(temp_dem,lowerLeft,5,5).astype('float')


            # calculate the coordinate of a data block
            for ii in [4,3,2,1,0]:
                dy = (abs(ii-4)+0.5) * res
                rasterBlock_y [ii,:] = llpnts16Y + dy
            for jj in [0,1,2,3,4]:
                dx = (jj+0.5) * res
                rasterBlock_x [:,jj] = llpnts16X + dx

            # for the point x,y, the n closest pixel value from the 5*5 matrix is selected
            xCoor1, yCoor1, elev1 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 1)
            xCoor3, yCoor3, elev3 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 3)
            xCoor4, yCoor4, elev4 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 4)
            xCoor9, yCoor9, elev9 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 9)
            xCoor16, yCoor16, elev16 = neighbors.neibr (rasterBlock_x, rasterBlock_y, rasterBlock_elev, x, y, 16)

            # A local coordinate is created; the center of the 5*5 matrix will be (0,0)
            x=x-xCoor1
            y=y-yCoor1

            xCoor3 = xCoor3 - xCoor1
            xCoor4 = xCoor4 - xCoor1
            xCoor9 = xCoor9 - xCoor1
            xCoor16 = xCoor16 - xCoor1

            yCoor3 = yCoor3 - yCoor1
            yCoor4 = yCoor4 - yCoor1
            yCoor9 = yCoor9 - yCoor1
            yCoor16 = yCoor16 - yCoor1

            #whithin a pixel
            if res == rsolutions[0]: temp = time()
            row[i+1] = elev1
            if res == rsolutions[0]:timeWP = timeWP + (time() - temp)

            #weighted average
            if res == rsolutions[0]: temp = time()
            row[i+2] = inverseDistanecWeighting.IDW(x, y, xCoor4, yCoor4, elev4, 2)
            if res == rsolutions[0]: timeWA4 = timeWA4 + (time() - temp)

            #Linear interpolation
            if res == rsolutions[0]: temp = time()
            row[i+3] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor3, yCoor3, elev3, 0))
            if res == rsolutions[0]: timeLi3 = timeLi3 + (time() - temp)

            #Bilinear interpolation
            if res == rsolutions[0]: temp = time()
            row[i+4] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor4, yCoor4, elev4, 1))
            if res == rsolutions[0]: timeBiLi4 = timeBiLi4 + (time() - temp)

            #Biquadratic interpolation
            if res == rsolutions[0]: temp = time()
            row[i+5] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor9, yCoor9, elev9, 2))
            if res == rsolutions[0]: timeBiQ9 = timeBiQ9 + (time() - temp)

            #BiCubic interpolation
            if res == rsolutions[0]: temp = time()
            row[i+6] = polyInterpolation.polyval2d(x,y,polyInterpolation.polyfit2d(xCoor16, yCoor16, elev16, 3))
            if res == rsolutions[0]: timeBiC16 = timeBiC16 + (time() - temp)

            i+=6

        uCurs.updateRow(row)

print ("running time for WP is:" + str(timeWP))
print ("running time for WA4 is:" + str(timeWA4))
print ("running time for Li3 is:" + str(timeLi3))
print ("running time for BiLi4 is:" + str(timeBiLi4))
print ("running time for BiQ9 is:" + str(timeBiQ9))
print ("running time for BiC16 is:" + str(timeBiC16))
#***********************************************************
# Calculate residuals and export them as a new shapefile
fields2 = []
for res in rsolutions:
    for att in attributes:
        fields2 = fields2 + [att + str(int(res))]

arcpy.CopyFeatures_management(samples, path + "\\residuals.shp")
for i in fields2:
    arcpy.CalculateField_management(in_table="residuals.dbf", field= i, expression="[RASTERVALU] - [" + i + "]" , expression_type="VB", code_block="")

#***********************************************************
# Calculate statistics for each method based on the residuals

# Convert the residulas table to a numpy array
resArray = arcpy.da.TableToNumPyArray("residuals.dbf", fields2)

recs=[]
for i in fields2:
    res = resArray[i]
    RMSE = np.sqrt(((res) ** 2).mean()) # Root Mean Square Error
    MAE = (abs(res)).mean() # Mean Absolute Eror
    MBE = res.mean() # Mean Bias Error
    STD = res.std() # Standard Deviation
    min = res.min() # Minimum Residual
    max = res.max() # Maximum Residual

    upperLim = MBE + 1.96 * STD # Upperbound of 95% confidence interval
    LowerLim = MBE - 1.96 * STD # Lowerbound of 95% confidence interval

    newRes = res[(res >= LowerLim) & (res <= upperLim)] # Eliminating outliers
    RMSE95 = np.sqrt(((newRes) ** 2).mean()) #95% confidence interval RMSE

    recs.append([i, RMSE, MAE, MBE, STD, min, max, upperLim, LowerLim, RMSE95])

dts = {'names': ('method','RMSE','MAE', 'MBE','STD', 'min', 'max', 'upperLim', 'LowerLim', 'RMSE95'),
       'formats':('S10', np.float64, np.float64, np.float64, np.float64, np.float64, np.float64, np.float64, np.float64, np.float64)}

recs.append(['test',1,2,3,4,5,6,7,8,9]) # I added this line to the end of the recs due to a weird issue that I had in the next line
array = np.rec.fromrecords(recs, dtype=dts)

if arcpy.Exists("stats.dbf"):
    arcpy.Delete_management("stats.dbf")

arcpy.da.NumPyArrayToTable(array, path +r"\stats.dbf")# Convert array to a  table


#***********************************************************
