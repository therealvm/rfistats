### Standard library imports
import argparse
from collections import namedtuple

### Non-standard imports
import numpy as np

### Local module imports
from rfistats.filterbank_stats import analyse_filterbank

###############################################################################

def parse_args():
    """ Parse command line arguments with which the script was called. Returns
    an object containing them all.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('fname', type=str, help='SIGPROC 32-bit filterbank file.')
    parser.add_argument('-o', '--outname', type=str, required=True, help='Base name of output file. A suffix .h5 is automatically appended.')
    parser.add_argument('--gulp', type=int, help='Number of samples read into a single data block.', default=2000)
    parser.add_argument('--start', type=int, help='Start sample index.', default=0)
    parser.add_argument('--end', type=int, help='End sample index. If not specified (None), process the file until the end.', default=None)
    parser.add_argument('--wmax', type=int, help='Maximum pulse width (in samples) being searched for.', default=128)
    parser.add_argument('--wtsp', type=float, help='Ratio between two consecutive pulse width trials.', default=2.0)
    parser.add_argument('--thr', type=float, help='S/N threshold used to flag significant pulses when computing channel occupancy.', default=6.0)
    args = parser.parse_args()
    return args


def main(args):
    fstats = analyse_filterbank(args.fname, start=args.start, end=args.end, gulp=args.gulp, wmax=args.wmax, wtsp=args.wtsp)
    outfile = args.outname + '.h5'
    fstats.save_hdf5(outfile)

if __name__ == '__main__':
    args = parse_args()
    main(args)
