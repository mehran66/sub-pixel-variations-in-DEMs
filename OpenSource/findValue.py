import numpy as np

def extractValue(x, y, dataset):
    '''
    This function extract value of a point from a raster
    :param x: x coordinate of point
    :param y: y coordinate of point
    :param dataset: a raster object imported by Rasterio
    :return: return the elevation of point
    '''
    val = dataset.sample([(x, y)])
    return val.next()[0]

def extractWindow(x, y, dataset, cellSize):
    '''
    This function aims to extract a 5*5 matrix from the input raster
    Also, this function convert the UTM coordinates to the local coordinate system of the extracted matrix
    :param x: x coordinate of point
    :param y: y coordinate of point
    :param dataset: a raster object imported by Rasterio
    :param cellSize: raster cell size
    :return: three 5*5 matrix (x, y, and elevation). Also the local coordinates of the input point
    '''
    row, col = dataset.index(x, y) # where the point is located in the raster
    rasterBlock_elev = dataset.read(1, window=((row-2, row+3), (col-2, col+3))) # extract the 5*5 raster block
    
    #find the upper left corner coordinates of the extracted 5*5 matrix
    ulp = dataset.affine * (col-2, row-2)#src.affine * (col, row)
    ulpCX= ulp[0] + (cellSize/2.0) # coordinates of central point of the upper left corner pixel
    ulpCY= ulp[1] - (cellSize/2.0)

    # coordinates of the  5*5 matrix
    X = np.arange(ulpCX, ulpCX+cellSize*5, cellSize)
    Y = np.arange(ulpCY, ulpCY-cellSize*5, -cellSize)
    X, Y = np.meshgrid(X, Y)
    
    # A local coordinate system is created; the center of the 5*5 matrix is (0,0)
    x=x-X[2,2]
    y=y-Y[2,2]

    rasterBlock_x = X - X[2,2]
    rasterBlock_y = Y - Y[2,2]
    
    return x, y, rasterBlock_x, rasterBlock_y, rasterBlock_elev




