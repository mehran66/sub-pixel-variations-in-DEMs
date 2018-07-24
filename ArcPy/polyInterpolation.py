#import itertools
import numpy as np
from numpy.linalg import inv

# This function calcuates the coefficient of each polynomial function
def polyfit2d(x, y, z, order):
    if order == 0:  # Linear
        G = np.vstack([np.ones(len(x)), x, y]).T
    if order == 1:  # BiLinear
        G = np.vstack([np.ones(len(x)), x, y, x * y]).T
    if order == 2:  # BiQuadratic9
        G = np.vstack([np.ones(len(x)), x, y, x * y, x ** 2, y ** 2, x ** 2 * y ** 2, x ** 2 * y, y ** 2 * x]).T
    if order == 3:  # BiCubic
        G = np.vstack([np.ones(len(x)), x, y, x * y, x ** 2, y ** 2, x ** 3, y ** 3, x ** 2 * y, y ** 2 * x, x ** 3 * y,
                       y ** 3 * x, x ** 2 * y ** 2, y ** 3 * x ** 3, y ** 3 * x ** 2, y ** 2 * x ** 3]).T

    m = np.matmul(inv(G), z)
    #m, _, _, _ = np.linalg.lstsq(G, z)
    return m

# This function calcuates the elevation of unkown point based on the coefficient of the polynomial function
def polyval2d(x, y, m):
    if len(m) == 3:
        z = np.dot(np.array([1, x, y]), m)
    if len(m) == 4:
        z = np.dot(np.array([1, x, y, x * y]), m)
    if len(m) == 9:
        z = np.dot(np.array([1, x, y, x * y, x ** 2, y ** 2, x ** 2 * y ** 2, x ** 2 * y, y ** 2 * x]), m)
    if len(m) == 16:
        z = np.dot(np.array(
            [1, x, y, x * y, x ** 2, y ** 2, x ** 3, y ** 3, x ** 2 * y, y ** 2 * x, x ** 3 * y, y ** 3 * x,
             x ** 2 * y ** 2, y ** 3 * x ** 3, y ** 3 * x ** 2, y ** 2 * x ** 3]), m)

    return z


