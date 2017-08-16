import numpy as np
import h5py

from .filterbank import Filterbank
from .block_stats import analyse_block


class DataBlock(object):
    """ Stores a data block in freq-major order (one row = one time sample), along with
    some useful extra information (time stamps, channel frequencies, etc.) """
    def __init__(self, data, times=None, freqs=None, tsamp=1.0):
        self.data = data
        self.times = times
        self.freqs = freqs
        self.tsamp = float(tsamp)
        if times is None:
            self.times = np.arange(self.nsamp, dtype=float)
        if freqs is None:
            self.freqs = np.arange(self.nchan, dtype=float)

    @property
    def nsamp(self):
        return self.data.shape[0]
    
    @property
    def nchan(self):
        return self.data.shape[1]
    
    @property
    def dt(self):
        return self.tsamp
    
    @property
    def df(self):
        if len(self.freqs) > 1:
            return self.freqs[1] - self.freqs[0]
        else:
            return 0.0

    def __str__(self):
        name = type(self).__name__
        header = '{0:s}: {1:d}T x {2:d}F'.format(name, self.nsamp, self.nchan, self.times[0], self.times[-1])
        lines = [
            header,
            '    dt = {0:.5e}'.format(self.tsamp),
            '    df = {0:.5e}'.format(self.df),
            '    t  = {0:12.6f} -> {1:12.6f}'.format(self.times[0], self.times[-1]),
            '    f  = {0:12.6f} -> {1:12.6f}'.format(self.freqs[0], self.freqs[-1]),
            ''
            ]
        return '\n'.join(lines)
    
    def __repr__(self):
        return str(self)
            



class FilterbankIterator(object):
    """ """
    _GULP_MIN = 16
    
    def __init__(self, filterbank, gulp=1024, start=0, end=None):
        if type(filterbank) == str:
            self.filterbank = Filterbank(filterbank)
        else:
            self.filterbank = filterbank
            
        if self.filterbank.nbits != 32:
            raise ValueError('FilterbankIterator: only 32-bit filterbanks are supported')
            
        self.gulp = max(self._GULP_MIN, int(gulp))
        
        # Define bounds
        if end is None:
            end = self.filterbank.nsamp
        self.end = min(int(end), self.filterbank.nsamp)
        self.end = max(0, self.end)
        
        self.start = max(0, int(start))
        self.start = min(self.start, self.end)
        
        self.isamp = self.start
        self.file = open(self.filterbank.fname, 'rb')
        self.file.seek(
            self.filterbank.sample_offset(self.isamp)
            )
        
    def __iter__(self):
        return self
    
    def __next__(self):
        nchan = self.filterbank.nchans
        data = np.fromfile(self.file, dtype=np.float32, count=nchan*self.gulp)
        nsr = data.size // nchan
        self.isamp += nsr
        if nsr < self.gulp or self.isamp > self.end:
            self.file.close()
            raise StopIteration
        else:
            data = data.reshape(nsr, nchan)
            times = np.arange(self.isamp, self.isamp + nsr) * self.filterbank.tsamp
            return DataBlock(data, times=times, freqs=self.filterbank.freqs, tsamp=self.filterbank.tsamp)




class FilterbankStats(object):
    """  """
    def __init__(self, tsamp, freqs, gulp, times, stats_dict):
        self.times = np.asarray(times)
        self.freqs = np.asarray(freqs)
        self.tsamp = tsamp
        self.gulp = gulp
        self.stats_keys = list(stats_dict.keys())
        for key, val in stats_dict.items():
            setattr(self, key, np.asarray(val))
            
    def time_average(self, stat_name):
        return getattr(self, stat_name).mean(axis=0)
        
    @property
    def nblock(self):
        return len(self.times)
    
    @property
    def nchan(self):
        return len(self.freqs)
    
    @property
    def dt(self):
        return self.tsamp
    
    @property
    def df(self):
        if len(self.freqs) > 1:
            return self.freqs[1] - self.freqs[0]
        else:
            return 0.0

    def save_hdf5(self, fname):
        """ Save FilterbankStats object to HDF5 format. """
        with h5py.File(fname, 'w') as fobj:
            # Header stores time stamps, freqs, and other basic data about the
            # filterbank analysed
            header_group = fobj.create_group('header')
            header_group.attrs.update({
                'tsamp' : self.tsamp,
                'gulp' : self.gulp,
                })
            header_group.create_dataset('times', data=self.times, dtype=np.float64, compression='gzip')       
            header_group.create_dataset('freqs', data=self.freqs, dtype=np.float64, compression='gzip')

            # stats_group stores all statistics collected as 2D arrays
            stats_group = fobj.create_group('stats')
            for key in self.stats_keys:
                data = getattr(self, key)
                stats_group.create_dataset(key, data=data, dtype=np.float64, compression='gzip')            
    
    @classmethod
    def load_hdf5(cls, fname):
        """ Load FilterbankStats object from HDF5 file."""
        with h5py.File(fname, 'r') as fobj:
            header_group = fobj['header']
            tsamp = header_group.attrs['tsamp']
            gulp = header_group.attrs['gulp']

            times = header_group['times'].value
            freqs = header_group['freqs'].value

            stats_group = fobj['stats']
            stats_dict = {
                key: dataset.value
                for key, dataset in stats_group.items()
                }    
        return cls(tsamp, freqs, gulp, times, stats_dict)
        

    
    
def analyse_filterbank(fname, start=0, end=None, gulp=2048, wmax=128, wtsp=2.0, thr=6.0):
    fil = Filterbank(fname)
    stats = {}  # dictionary of stats
    times = []  # start times of each block
    
    for block in FilterbankIterator(fil, gulp=gulp, start=start, end=end):
        print(block)
        ndata, mask, df = analyse_block(block.data, wmax=wmax, wtsp=wtsp, thr=thr)
        for key in df.columns:
            if key in stats:
                stats[key].append(df[key].as_matrix())
            else:
                stats[key] = [df[key].as_matrix()]
        times.append(block.times[0])
    return FilterbankStats(fil.tsamp, fil.freqs, gulp, times, stats)
