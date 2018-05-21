"""
Compute the Dynamic Spectrum of a Filterbank at a specified DM.
"""
import argparse
from sigproc_header import SigprocHeader
from dedisperse import DedispersionManager

import numpy
from numpy import log2

def num_block_samples(tblock, tsamp):
    """ Determine the number of samples in a block, making sure it is a power
    of two. """
    n = int(tblock / tsamp)

    # Round down to lower power-of-two
    n = 2 ** int(log2(n))
    return n


def dynamic_spectrum(data, tsamp, tblock=10.0):
    tobs = data.size * tsamp
    bsamp = num_block_samples(tblock, tsamp)
    nblocks = data.size // bsamp

    nsamp_eff = nblocks * bsamp
    tblock_eff = bsamp * tsamp
    print("Cutting input data ({0:d} samples) into {1:d} blocks of {2:d} samples, tblock = {3:.6f} s".format(data.size, nblocks, bsamp, tblock_eff))

    data = data[:nsamp_eff].reshape(nblocks, bsamp)
    ft = numpy.fft.rfft(data)

    # Center times of every block
    times = numpy.arange(nblocks) * tblock_eff + 0.5 * tblock_eff

    # Frequencies of every Fourier bin
    freqs = numpy.fft.rfftfreq(bsamp, tsamp)

    return times, freqs, ft


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

    # Dedisperse using external program, automatically cleanup
    # temporary output files
    with DedispersionManager(args.filterbank, args.outdir, dm=args.dm) as manager:
        data = manager.get_output()

    # Compute and save dynamic spectrum, the center times of each
    # block, and the frequencies of every Fourier bin
    tsamp = header['tsamp']
    times, freqs, dynspec = dynamic_spectrum(data, tsamp, args.tblock)
    numpy.savez("dynamic_spectrum.npz", times=times, freqs=freqs, dynspec=dynspec)
