import numpy as np

def padlength(n):
    """ Returns the smallest number larger than n that can be written as 2^k x f,
    where f is one of [2, 3, 5]. """
    factors = np.asarray([2, 3, 5])
    k = np.log2(n) - np.log2(factors)
    lengths = 2**np.ceil(k) * factors
    return int(lengths.min())
  

def boxcar(size, width):
    """ Generate an array of size elements containing a boxcar of given width
    centered around the first element of the array. """
    box = np.zeros(size)
    box[:width] = width**-0.5
    box = np.roll(box, -(width // 2)) # Parentheses do matter: -1//2 != -(1//2)
    return box

def generate_width_trials(wmax, wtsp=1.5):
    """ Generate a sequence of geometrically increasing width trials, 
    not exceeding wmax. 
    
    Starting with w = 1, the next width trial is obtained with w = max(w + 1, wtsp x w)
    """
    w = 1
    widths = []
    while w <= wmax:
        widths.append(w)
        w = int(max(w+1, wtsp * w))
    return np.asarray(widths)



class BoxcarConvolver(object):
    """ Handles the padding and convolution of 1D normalised data with boxcars, to obtain
    signal-to-noise ratio values. """
    def __init__(self, nsamp, wmax=128, wtsp=1.5):
        """
        Parameters:
        -----------
            nsamp: int
                Number of samples in the data segments this BoxcarConvolver instance
                can deal with.
            wmax: int
                Maximum boxcar width trial
            wtsp: float
                Ratio between consecutive width trials, starting from 1, up to wmax.
        """
        self.nsamp = int(nsamp)
        self.widths = generate_width_trials(int(wmax), wtsp)
        
        # Compute padding lengths on each side before convolving
        # This is to accelerate the subsequent FFTs
        self.wmax = self.widths[-1]
        self.padlength = padlength(self.nsamp + self.wmax + 1)
        npad = self.padlength - nsamp
        lpad = npad // 2
        rpad = npad - lpad
        (self.lpad, self.rpad) = lpad, rpad
        
        # Generate boxcars
        self.boxcars = np.asarray([
            boxcar(self.padlength, w)
            for w in self.widths
            ])
        
        # Pre-compute boxcar FFTs
        self.fboxcars = np.fft.rfft(self.boxcars)
        
    def process(self, ndata):
        """
        Parameters:
        -----------
            ndata: ndarray, 1D
                Data from a single channel, normalised to zero mean (or median) 
                and unit standard deviation.
                
        Returns:
        --------
            conv: ndarray, 2D, shape = (num_widths, num_samples)
                Convolution products of ndata and boxcars of pre-determined widths.
        """
        X = np.pad(ndata, (self.lpad, self.rpad), 'constant', constant_values=(0.0, 0.0))
        conv = np.fft.irfft(np.fft.rfft(X) * self.fboxcars.conj())
        
        # Un-pad
        conv = conv[:, self.lpad:-self.rpad]
        return conv
