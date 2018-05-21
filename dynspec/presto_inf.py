import os
import json


class PrestoInf(dict):
    """ Parse PRESTO's .inf files that contain dedispersed time series
    metadata. """

    parsing_guide = {
        }

    final_key_types = {
        }

    def __init__(self, fname):
        self._fname = os.path.realpath(fname)

        with open(self.fname) as fobj:
            lines = fobj.read().strip().split('\n')



        raw_attrs = {}
        for line in lines:
            try:
                key, val = line.split('=')
                key = key.strip().lower()
                val = val.strip()
            except:
                continue
            key = key.strip().lower()
            raw_attrs[key] = val

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
    inf = PrestoInf("/home/vince/work/pulsars/presto_time_series/J1855+0307/J1855+0307_DM400.00.inf")
    print(json.dumps(inf, indent=4))
