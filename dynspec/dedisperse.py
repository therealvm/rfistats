"""
Wrapper around SIGPROC's dedisperse command-line program
"""
import os
import subprocess
import uuid
import numpy

class DedispersionManager(object):
    """ Context manager for dedispersion. """
    def __init__(self, obsfile, outdir, dm=0.0):
        self._obsfile = os.path.realpath(str(obsfile))
        self._outdir = os.path.realpath(outdir)
        self._dm = float(dm)

        # Path of temporary dedispersed output
        self._outname = os.path.join(self.outdir, str(uuid.uuid4()) + ".tim")

    @property
    def obsfile(self):
        """ Input observation file """
        return self._obsfile

    @property
    def outdir(self):
        """ Output directory """
        return self._outdir

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
        return numpy.fromfile(self.outname, dtype=numpy.float32)

    def dedispersion_command(self):
        return "dedisperse {obsfile:s} -d {dm:.6f} > {outfile:s}".format(
            obsfile=self.obsfile,
            dm=self.dm,
            outfile=self.outname)

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