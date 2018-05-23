"""
Wrapper around SIGPROC's dedisperse command-line program
"""
import os
import subprocess
import uuid
import numpy

from sigproc_header import SigprocHeader

class DedispersionManager(object):
    """ Context manager for dedispersion. """
    def __init__(self, obsfile, outdir, maskfile=None, dm=0.0):
        self._obsfile = os.path.realpath(str(obsfile))
        self._maskfile = None
        if maskfile is not None:
            self._maskfile = os.path.realpath(str(maskfile))

        self._outdir = os.path.realpath(outdir)
        self._dm = float(dm)

        # Path of temporary dedispersed output
        #self._outname = os.path.join(self.outdir, str(uuid.uuid4()) + "_DM{:.6f}.tim".format(self.dm))
        __, fn = os.path.split(self.obsfile)
        self._outname = os.path.join(self.outdir, fn.replace(".fil", "_DM{:.6f}.tim".format(self.dm)))

    @property
    def obsfile(self):
        """ Input observation file """
        return self._obsfile

    @property
    def outdir(self):
        """ Output directory """
        return self._outdir

    @property
    def maskfile(self):
        """ Channel mask file to pass to SIGPROC's dedisperse """
        return self._maskfile

    @property
    def dm(self):
        """ DM at which to dedisperse input observation """
        return self._dm

    @property
    def outname(self):
        """ Temporary dedispersed time series file """
        return self._outname

    def get_output(self):
        """ Output dedispersed time series, as numpy float32 array. """
        fname = self.outname
        header = SigprocHeader(fname)

        # Load time series data
        with open(fname, 'rb') as fobj:
            fobj.seek(header.bytesize)
            data = numpy.fromfile(fobj, dtype=numpy.float32)
        return data

    def dedispersion_command(self):
        elements = []
        elements.append("dedisperse {obsfile:s} -d {dm:.6f}".format(
            obsfile=self.obsfile,
            dm=self.dm))
        if self.maskfile:
            elements.append("-i {maskfile:s}".format(maskfile=self.maskfile))
        elements.append("> {outname:s}".format(outname=self.outname))
        return " ".join(elements)

    def execute_dedispersion(self):
        command = self.dedispersion_command()
        print(command)
        try:
            subprocess.call(command, shell=True)
        except Exception as error:
            print("ERROR: {!s}".format(error))

    def cleanup(self):
        fname = self.outname
        try:
            print("Deleting temporary file: {:s}".format(fname))
            os.remove(fname)
        except:
            pass

    def __enter__(self):
        self.execute_dedispersion()
        return self

    def __exit__(self, extype, exval, traceback):
        self.cleanup()
