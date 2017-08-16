import numpy
import struct
import os

################################################################################
# HEADER READ/WRITE FUNCTIONS
################################################################################

def read_string(fobj, maxbytes=2000):
    # Length stored in 32-bit (4 bytes) int
    length, = struct.unpack('i', fobj.read(4))
    
    if length > maxbytes:
        raise RuntimeError('read_string: unreasonable read length: %d' % length)
    
    # The decode() method is a necessity in python 3
    # as the output of fobj.read() is a builtin 'bytes' object.
    # The output of decode() is string (UTF-8 by default)
    return fobj.read(length).decode()
    
def read_key_string(fobj, dic):
    key = read_string(fobj)
    val = read_string(fobj)
    dic[key] = val

def read_key_value(fobj, typefmt, bytesize, dic):
    key = read_string(fobj)
    val, = struct.unpack(typefmt, fobj.read(bytesize))
    dic[key] = val

def read_lenstring(fobj):
    """ Read one int specifying a length, and then a string of that length
    from given OPEN file object.
    """
    length = numpy.fromfile(fobj, dtype=numpy.int32, count=1)[0]
    return fobj.read(length).decode()

def parse_filterbank_header(fname):
    typedict = {
        'HEADER_START': None,
        'rawdatafile' : 's' ,
        'source_name' : 's' ,
        'machine_id'  : 'i' ,
        'telescope_id': 'i' ,
        'HEADER_END'  : None,
        'src_raj'     : 'd' ,
        'src_dej'     : 'd',
        'az_start'    : 'd',
        'za_start'    : 'd',
        'data_type'   : 'i',
        'fch1'        : 'd',
        'foff'        : 'd',
        'nchans'      : 'i',
        'nbeams'      : 'i',
        'ibeam'       : 'i',
        'nbits'       : 'i',
        'tstart'      : 'd',
        'tsamp'       : 'd',
        'nifs'        : 'i',
        }
        
    sizedict = {
        'i' : 4,
        'd' : 8
        }
    
    header = {}
    fobj = open(fname, 'rb')
 
    header_start_flag = read_string(fobj)
    if header_start_flag != 'HEADER_START':
        raise RuntimeError(
            'parse_filterbank_header: failed to parse HEADER_START flag'
            )
    
    while True:
        key = read_string(fobj)
        if key == 'HEADER_END':
            break
        typefmt = typedict[key]
        if typefmt == 's':
            val = read_string(fobj)
        else:
            bytesize = sizedict[typefmt]
            val, = struct.unpack(typefmt, fobj.read(bytesize))
        header[key] = val
        
    header_bytesize = fobj.tell()
    fobj.close()
    return header, header_bytesize


def format_filterbank_header(header):
    """ Pack a filterbank header into a sequence of bytes ready to be written.
    example: file.write(format_filterbank_header(header))
    """
    keytypes = [
        ('HEADER_START', None),
        ('rawdatafile', 's'),
        ('source_name', 's'),
        ('machine_id', 'i'),
        ('telescope_id', 'i'),
        ('src_raj', 'd'),
        ('src_dej', 'd'),
        ('az_start', 'd'),
        ('za_start', 'd'),
        ('data_type', 'i'),
        ('fch1', 'd'),
        ('foff', 'd'),
        ('nchans', 'i'),
        ('nbeams', 'i'),
        #('ibeam', 'i'),
        ('nbits', 'i'),
        ('tstart', 'd'),
        ('tsamp', 'd'),
        ('nifs', 'i'),
        ('HEADER_END', None),
        ]
        
    format = '<' # THIS IS SUPREMELY IMPORTANT
    args = []
    for key, typ in keytypes:
        format += 'i%ds' % len(key)
        args.append(len(key))
        args.append(key.encode())
        if typ is 's':
            format += 'i%ds' % len(header[key])
            args.append(len(header[key]))
            args.append(header[key].encode())
        elif typ is 'i':
            format += 'i'
            args.append(header[key])
        elif typ is 'd':
            format += 'd'
            args.append(header[key])
    
    return struct.pack(format, *args)

def format_float_coord(f):
    """ Convert coordinate in decimal floating point format to HH:MM:SS.CC
    """
    sign = numpy.sign(f)
    x = abs(f)
    hh, x = divmod(x, 10000.)
    mm, ss = divmod(x, 100.)
    if sign >= 0: 
        sign = '+'
    else:
        sign = '-'
    return '%s%02d:%02d:%05.2f' % (sign, hh, mm, ss)

################################################################################

class Filterbank(object):
    def __init__(self, fname):
        self.fname = os.path.abspath(fname)
        (self._header, self._header_bytesize) = parse_filterbank_header(fname)
        
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
