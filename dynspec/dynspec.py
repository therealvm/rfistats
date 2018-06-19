"""
Compute the Dynamic Spectrum of a Filterbank at a specified DM.
"""
import os
import argparse
import numpy

from rfistats.dynspec.sigproc_header import SigprocHeader
from rfistats.dynspec.presto_inf import PrestoInf
from rfistats.dynspec.core import dynamic_spectrum


def parse_arguments():
    """ Parse command line arguments with which the script was called. Returns
    an object containing them all.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'fname', type=str,
        help="Dedispersed time series file to process."
    )
    parser.add_argument(
        'outdir', type=str,
        help="Output directory for data products and temporary files."
    )
    parser.add_argument(
        '-f', '--format', type=str,
        help="Input time series format.",
        choices=['presto', 'sigproc'],
        required=True
    )
    parser.add_argument(
        '-s', '--skip', type=float, default=0.0,
        help="Ignore this many seconds worth of data at the start of the file."
    )
    parser.add_argument(
        '-L', '--tblock', type=float, default=10.0,
        help="Length of time series blocks to FFT independently, in seconds. \
NOTE: Will be set to the largest power-of-two number of samples that is lower\
or equal to the specified duration."
    )
    args = parser.parse_args()
    return args


def outfile_name(input_fname, outdir):
    print(input_fname, outdir)
    __, name = os.path.split(input_fname)
    name = name.rsplit('.', maxsplit=1)[0]
    outfile = "{:s}_dynspec.npz".format(name)
    return os.path.realpath(os.path.join(outdir, outfile))


def load_data(fname, fmt='presto'):
    if fmt == 'presto':
        inf = PrestoInf(fname)
        data = inf.load_data()
        tsamp = inf['tsamp']
    elif fmt == 'sigproc':
        sh = SigprocHeader(fname)
        with open(fname, 'rb') as fobj:
            fobj.seek(sh.bytesize)
            data = numpy.fromfile(fobj, dtype=numpy.float32)
        tsamp = sh['tsamp']
    return data, tsamp

if __name__ == "__main__":
    args = parse_arguments()
    data, tsamp = load_data(args.fname, fmt=args.format.lower())

    # Compute and save dynamic spectrum, the center times of each
    # block, and the frequencies of every Fourier bin
    times, freqs, dynspec = dynamic_spectrum(data, tsamp, tblock=args.tblock, tskip=args.skip)

    outfile = outfile_name(args.fname, args.outdir)
    print("Saving output to:", outfile)
    numpy.savez(outfile, times=times, freqs=freqs, dynspec=dynspec)
