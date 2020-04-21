import numpy
import struct
import os

from rfistats.sigproc_header import SigprocHeader

################################################################################

class Filterbank(object):
    def __init__(self, fname):
        self.fname = os.path.abspath(fname)
        self._header = SigprocHeader(fname)
        self._header_bytesize = self._header.bytesize
        
        ### Find out file size
        fobj = open(fname, 'rb')
        fobj.seek(0, 2) # Seek to the end of the file
        self._bytesize = fobj.tell()
        fobj.close()

    def sample_offset(self, isamp):
        """ Byte offset in the file where sample number 'isamp' is stored.
        """
        return self.data_offset_start + isamp * self.bytes_per_sample
    
    @property
    def source_name(self):
        return self._header['source_name']
        
    @property
    def nbits(self):
        return self._header['nbits']
        
    @property
    def mjd_start(self):
        """ Start MJD of the observation.
        """
        return self._header['tstart']
        
    @property
    def tsamp(self):
        return self._header['tsamp']
        
    @property
    def nchans(self):
        return self._header['nchans']

    @property
    def fch1(self):
        return self._header['fch1']
        
    @property
    def fchn(self):
        return self.fch1 + self.foff * (self.nchans - 1)

    @property
    def foff(self):
        return self._header['foff']
        
    @property
    def freqs(self):
        return numpy.linspace(self.fch1, self.fchn, self.nchans)
        
    @property
    def ibeam(self):
        if 'ibeam' in self._header:
            return self._header['ibeam']
        else:
            return None
        
    @property
    def data_offset_start(self):
        return self._header_bytesize
        
    @property
    def data_offset_end(self):
        return self._bytesize

    @property
    def bytes_per_sample(self):
        return self.nchans * self.nbits // 8
        
    @property
    def nsamp(self):
        return (self.data_offset_end - self.data_offset_start) // self.bytes_per_sample
        
    @property
    def tobs(self):
        return self.tsamp * self.nsamp

    @property
    def raj(self):
        """ RA in decimal floating point format.
        """
        return self._header['src_raj']
        
    @property
    def dej(self):
        """ Dec in decimal floating point format.
        """
        return self._header['src_dej']
        
    @property
    def ra(self):
        """ RA in HH:MM:SS.CC format.
        """
        return format_float_coord(self._header['src_raj'])
        
    @property
    def dec(self):
        """ Dec in DD:MM:SS.CC format.
        """
        return format_float_coord(self._header['src_dej'])
        
    def __repr__(self):
        return str(self)
        
    def __str__(self):
        tab = '    '  # 4 spaces
        lines = [
            '%s object' % type(self).__name__,
            'Source file      : %s' % self.fname,
            'Source name      : %s' % self.source_name,
            'Source RA        : %s' % self.ra,
            'Source Dec       : %s' % self.dec,
            'Beam Index       : %s' % self.ibeam,
            'Bits             : %d' % self.nbits,
            'Samples          : %d' % self.nsamp,
            'Sampling time (s): %.3e' % self.tsamp,
            'Length (s)       : %.3f' % self.tobs,
            'Start MJD        : %.9f' % self.mjd_start,
            'Channels         : %d' % self.nchans,
            'fch1 (MHz)       : %.3f' % self.fch1,
            'fchn (MHz)       : %.3f' % self.fchn,
            '',
            ]
        for ii in range(1, len(lines)):
            lines[ii] = tab + lines[ii]
            
        return '\n'.join(lines) 
