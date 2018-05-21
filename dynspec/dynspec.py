"""
Compute the Dynamic Spectrum of a Filterbank at a specified DM.
"""
import argparse
from sigproc_header import SigprocHeader
from dedisperse import DedispersionManager


def dynamic_spectrum(fil, dm=0.0):
    pass


def parse_arguments():
    """ Parse command line arguments with which the script was called. Returns
    an object containing them all.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'filterbank', type=str,
        help="SIGPROC Filterbank to process."
        )
    parser.add_argument(
        'outdir', type=str,
        help="Output directory for data products and temporary files."
        )
    parser.add_argument(
        '-d', '--dm', type=float, default=0.0,
        help="DM at which to dedisperse the input data before analysis."
        )
    parser.add_argument(
        '-L', '--tblock', type=float, default=10.0,
        help="Length of time series blocks to FFT independently, in seconds. \
NOTE: Will be set to the largest power-of-two number of samples that is lower\
or equal to the specified duration."
        )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    header = SigprocHeader(args.filterbank)
    print(header)

    with DedispersionManager(args.filterbank, args.outdir, dm=args.dm) as manager:
        data = manager.get_output()
    
    print(data)
