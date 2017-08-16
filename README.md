# rfistats

Gather data statistics from a SIGPROC 32-bit Filterbank file as a function of time and observing frequency. One of the goals is to run it on a number of MeerKAT pulsar search mode observations, to determine which frequency bands are usable. The main feature of this piece of code is its ability to sensibly compute what fraction of a frequency channel is occupied by statistically significant pulses of any width.

### Required python packages

* numpy
* scipy
* pandas
* h5py

matplotlib is of course highly recommended to plot the outputs.

### Pipeline overview

The idea is to read the data in blocks sufficiently large (on order of 1,000 samples) to compute statistics for every channel. For every block, every channel is normalised to zero mean and unit variance, in a way that is robust to outliers. 
```
normalised_data = (data - median) / robust_std
```

The robust standard deviation is defined as
```
robust_std = IQR / 1.3489795
```
where IQR stands for inter-quartile range. Both median and robust\_std are recorded as a function of time (data block index) and frequency. Once the data have been normalised, we further compute:

* Average normalised power: the mean of squares of the data in every channel
* occupancy: the fraction of samples that are part of a statistically significant pulse (assumed to be the manifestation of RFI). More details below.


### Calculating occupancy

For a given frequency channel, we define a sample as occupied if it is part of a square (boxcar) pulse exceeding a certain signal-to-noise ratio threshold. This is sensibly calculated, in such a way that pulses of any width are detected, and that no sample gets abusively flagged. 

The steps are:

* Convolve the **normalised** data with boxcars of different widths W\_n, and heights W\_n^-0.5. The output is a 2D array (num\_widths, num\_samples) that can be interpreted as a signal-to-noise ratio as a function of width and time.
* We iterate through the array above in (width, time) order: we flag a pulse of width W centered on the current time sample if two conditions are met. First, its S/N must exceed a predefined threshold. Second, it must not overlap with a brighter pulse of equal or lower width.


### Usage

The main executable script in the module is analyse\_filterbank.py. A description of its command-line argmuments can be obtained with:

```
python analyse_filterbank.py -h
```


### Reading the output files

The output of the executable above is a FilterbankStats object (defined in filterbank\_stats.py) which is saved in HDF5 format. To read it and play around with the output, simply type something like this in an ipython console:

```
from rfistats import FilterbankStats
fstats = FilterbankStats.load_hdf5('stats.h5')
```

fstats contains as class members a number of 2D numpy arrays (shape = num\_blocks x num\_channels) named after the statistics gathered:

* median
* robust\_std
* avg\_power
* occupancy

... and also the starting times of each block, the frequencies of each channels, and more.


### Limitations

* Only 32-bit SIGPROC filterbanks are supported.
* Slow: about 10x real time for 4,096 channel data sampled at 153 us.
* A wide pulse spread across two consecutive data blocks may not be properly flagged. It should not be much of a problem as long as 'gulp' is always much (8+ times) larger than 'wmax'.


