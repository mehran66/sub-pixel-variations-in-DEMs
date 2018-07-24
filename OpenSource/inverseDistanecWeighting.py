import numpy as np
import math

# Weighted Average Interpolation module
# x and y are the unknown coordinates
# xCoords, yCoords, elevs are the known coordinates of the nehbor pixels
# order is the power of distance in the inverse distance that is used as a weight in IDW

def IDW(x, y, xCoords, yCoords, elevs, order=2):

    d =  np.zeros(len(xCoords))
    w =  np.zeros(len(xCoords))

    # if the distance from the unknown point to the central pixel is less than 1 cm, the evlevation of central pixel is assigned without using IDW
    if  math.sqrt((x-xCoords[0])**2 +(y-yCoords[0])**2) < 0.01:
        z = elevs[0]
    else:
        for i in range(len(xCoords)):
            d[i] = math.sqrt((x-xCoords[i])**2 +(y-yCoords[i])**2)
            w[i] = 1.0 / (d[i]**order)
        z = (np.sum(elevs*w)) / float(np.sum(w))

    return z

