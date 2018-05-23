"""
Compute the Dynamic Spectrum of a Filterbank at a specified DM.
"""
import os
import argparse
import numpy

from sigproc_header import SigprocHeader
from dedisperse import DedispersionManager
from core import dynamic_spectrum


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
        '-m', '--maskfile', type=str, default=None,
        help="Optional file specifying a list of channels to ignore, which is \
        passed to SIGPROC's dedisperse."
        )
    parser.add_argument(
        '-L', '--tblock', type=float, default=10.0,
        help="Length of time series blocks to FFT independently, in seconds. \
NOTE: Will be set to the largest power-of-two number of samples that is lower\
or equal to the specified duration."
        )
    args = parser.parse_args()
    return args


def outfile_name(filterbank, dm, outdir):
    rootdir, fname = os.path.split(filterbank)
    outfile = fname.replace(".fil", "_dynspec_DM{:.3f}.npz".format(dm))
    return os.path.join(outdir, outfile)

if __name__ == "__main__":
    args = parse_arguments()
    header = SigprocHeader(args.filterbank)

    # Dedisperse using external program, automatically cleanup
    # temporary output files
    with DedispersionManager(args.filterbank, args.outdir, maskfile=args.maskfile, dm=args.dm) as manager:
        data = manager.get_output()

    # Compute and save dynamic spectrum, the center times of each
    # block, and the frequencies of every Fourier bin
    tsamp = header['tsamp']
    times, freqs, dynspec = dynamic_spectrum(data, tsamp, args.tblock)

    outfile = outfile_name(args.filterbank, args.dm, args.outdir)
    numpy.savez(outfile, times=times, freqs=freqs, dynspec=dynspec)
