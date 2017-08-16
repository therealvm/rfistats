import numpy as np
import pandas

from .stats_utils import robust_std
from .convolution import BoxcarConvolver

def normalise_block(data):
    med = np.median(data, axis=0)
    std = robust_std(data, axis=0)
    ndata = (data - med) / std
    return ndata, med, std


def occupancy_mask_1d(ndata, convolver, thr=6.0):
    """ Find out which samples in a normalised time series are part of a statistically
    significant pulse.

    Parameters:
    -----------
        ndata: ndarray, 1D
            Normalised data segment from a single channel.
        convolver: BoxcarConvolver
            BoxcarConvolver instance adapted to data's number of samples.
        thr: float
            threshold in number of sigma
            
    Returns:
    --------
        conv: ndarray
            Convolution products of ndata with all boxcars.
        mask: ndarray
            Mask equal to True for all samples considered part of a pulse with a S/N exceeding
            the specified threshold 'thr'.
    """
    # Convolution products
    x = convolver.process(ndata)
    
    # Trivial first step: flag any data point above threshold
    mask = x[0] > thr

    # Then look at possible wider pulses
    for iw, width in enumerate(convolver.widths[1:], start=1):
        hw = width // 2

        # m is True for points on which a significant pulse of width 'width' is centered
        y = x[iw]
        m = y > thr

        # Go through every potential pulse of width 'width' centered around sample index 'ii'
        for ii in np.where(m)[0]:
            istart = max(ii-hw, 0)
            iend = min(ii+hw+1, x.shape[1])

            # To be considered a significant pulse, it must attain or exceed the S/N of any
            # overlapping pulse with a width up to 'width'
            if y[ii] >= x[:iw+1, istart:iend].max(): # this is a GREATER OR EQUAL SIGN BY THE WAY. IMPORTANT.
                mask[istart:iend] = True
    return x, mask

    
def analyse_segment(data, convolver, thr=6.0):
    """ Compute a number of statistics of a 1D time series.

    Parameters:
    -----------
        data: ndarray
            Raw data segment from a single channel.
        convolver: BoxcarConvolver
            BoxcarConvolver instance adapted to data's number of samples.
        thr: float
            Significance threshold in number of Gaussian sigmas.
            
    Returns:
    --------
        stats: dict
            Segment statistics.
    """
    # Normalise to zero mean and unit robust standard deviation
    # robust std. is calculated form the interquertile range of the data,
    # which is not sensitive to outliers
    ndata, med, std = normalise_block(data)

    # Compute occupancy mask
    conv, mask = occupancy_mask_1d(ndata, convolver, thr=thr)
    occupancy = mask.mean()
    
    avg_power = (ndata**2).mean()
    
    stats = {
        'median' : med,
        'robust_std' : std,
        'occupancy' : occupancy,
        'avg_power' : avg_power,
        'ndata' : ndata,
        'conv' : conv,
        'mask' : mask,
        }
    
    return stats


def analyse_block(data, wmax=256, wtsp=2.0, thr=6.0):
    """ Compute a number of statistics of a 2D data block. 
   
    Parameters:
    -----------
        data: ndarray
            Data block of shape (num_samples, num_channels)
        wmax: int
            Maximum pulse width trial in number of bins
        wtsp: float
            Ratio between two consecutive pulse width trials.
        thr: float
            Minimum S/N of a pulse for it to be considered
            statistically significant.
            
    Returns:
    --------
        ndata: ndarray
            Normalised data block TRANSPOSED, i.e. shape is (num_channels, num_samples)
        mask: ndarray
            Bitmask of same shape as ndata. True for any data point that is part of a
            statistically significant pulse.
        stats: pandas.DataFrame
            Segment statistics per channel.
    
    """
    nsamp, nchan = data.shape
    convolver = BoxcarConvolver(nsamp, wmax=wmax, wtsp=wtsp)
    output = [analyse_segment(channel, convolver, thr=thr) for channel in data.T]
    
    mask  = np.asarray([dic['mask']  for dic in output])
    ndata = np.asarray([dic['ndata'] for dic in output])

    columns = [
        'median', 'robust_std', 'avg_power', 'occupancy'
        ]
    stats = pandas.DataFrame(output, columns=columns)
    return ndata, mask, stats
