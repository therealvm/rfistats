import os
import json



# NOTE: Have a look at this, the original C code that reads/writes .inf files
# https://github.com/scottransom/presto/blob/master/src/ioinf.c

# The official way to parse is based on line order:
# Phase 1: basename, telescope, instrument, source, raj, decj, observer, mjd, nsamp, tsamp, num_onoff (11 keys)
# Parse on off pairs if any
# Parse EM Band (1 key)
# Depending on EM band, different things happen. We care about Radio.
# Phase 2: fov, dm, fbot, bw, nchan, cbw, analyst (7 keys)

# A character '=' is expected on column 40 of each line


def lowercase_stripped(s):
    """ Cast string to lowercase, strip spaces on the edges, and then replace
    sequences of multiple spaces by a single one. This function is applied
    to the value descriptions in a .inf file. """
    return " ".join(s.lower().strip().split())

class PrestoInf(dict):
    """ Parse PRESTO's .inf files that contain dedispersed time series
    metadata. """

    _KEYVAL_SEP = "= " # Note the trailing space

    def __init__(self, fname):
        self._fname = os.path.realpath(fname)

        with open(self.fname) as fobj:
            lines = fobj.read().rstrip().split('\n')

        self.lines = lines

        raw_attrs = {}
        sep = self._KEYVAL_SEP
        for line in lines:
            try:
                descr, val = line.split(sep)
                descr = descr.strip()
                val = val.strip()
            except Exception as err:
                print(type(err))
                print(err)
            raw_attrs[descr] = val

        super(PrestoInf, self).__init__(raw_attrs)

    @property
    def fname(self):
        """ Absolute path to original file. """
        return self._fname

    @property
    def skycoord(self):
        """ astropy.SkyCoord object with the coordinates of the source. """
        return None

if __name__ == '__main__':
    #inf = PrestoInf("/home/vince/work/pulsars/presto_time_series/J1855+0307/J1855+0307_DM400.00.inf")
    inf = PrestoInf("LOTAAS.inf")
    for key in sorted(inf.keys()):
        print('\"' + key + '\"', ':', inf[key])
