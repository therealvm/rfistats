import numpy as np
import scipy.stats as sst

def robust_std(data, axis=-1):
    """ Estimate the standard deviation of data from its inter-quartile range. """
    iqr = np.percentile(data, 75, axis=axis) - np.percentile(data, 25, axis=axis)
    return iqr / 1.3489795

def outlier_mask(data):
    n = data.size
    nsigma = max(sst.norm.isf(1.0 / n), 3.0)
    s = robust_std(data)
    m = np.median(data)
    vmin = m - nsigma*s
    vmax = m + nsigma*s
    mask = (data < vmin) | (data > vmax)
    stats = {
        'median' : m,
        'robust_std': s,
        'nsigma' : nsigma,
        'vmin' : vmin,
        'vmax': vmax
        }
    return mask, stats 
