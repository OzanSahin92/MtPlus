#!/usr/bin/env python
# coding: utf-8

import numpy as np
import netCDF4

def main():
    data_path = 'Data/'
    # read
    slp_data = 'slp.4dx4dy.nh_ndjfm_19792019_subseas_cell.nc'
    # write
    extreme_event_data = 'extreme.4dx4dy.19792019_nh_ndjfm_subseas_cell.txt'


    dataset = netCDF4.Dataset(data_path+slp_data, 'r')
    # extract the raw data out of the dataset
    var = dataset.variables['var1'][:].data

    # separate the data into the seperate months of january, february, march, november and december
    # to calculate the 5th percentile threshholds of the seperate months
    nov = []
    dec = []
    jan = []
    feb = []
    mar = []

    counter = 1
    for day in var:
        if counter<=31:
            jan.append(day)
        elif counter>31 and counter<=59:
            feb.append(day)
        elif counter>59 and counter<=90:
            mar.append(day)
        elif counter>90 and counter<=120:
            nov.append(day)
        else:
            dec.append(day)
        counter+=1
        if counter==152:
            counter=1

    janArr = np.array(jan) 
    febArr = np.array(feb) 
    marArr = np.array(mar)
    novArr = np.array(nov)
    decArr = np.array(dec)

    jan5thPerc = np.percentile(janArr, 5, axis=0)
    feb5thPerc = np.percentile(febArr, 5, axis=0)
    mar5thPerc = np.percentile(marArr, 5, axis=0)
    nov5thPerc = np.percentile(novArr, 5, axis=0)
    dec5thPerc = np.percentile(decArr, 5, axis=0)

    # identify extreme events with the seperate thresholds and create an extreme event time series
    extreme_event_bool = []
    counter = 1
    for day in var:
        if counter<=31:
            extreme_event_bool.append(day < jan5thPerc)
        elif counter>31 and counter<= 59:
            extreme_event_bool.append(day < feb5thPerc)
        elif counter>59 and counter<=90:
            extreme_event_bool.append(day < mar5thPerc)
        elif counter>90 and counter<=120:
            extreme_event_bool.append(day < nov5thPerc)
        else:
            extreme_event_bool.append(day < dec5thPerc)
        counter+=1
        if counter==152:
            counter=1
        
    extremeEventArr = np.array(extreme_event_bool).astype('int')

    np.savetxt(data_path+extreme_event_data, extremeEventArr)

if __name__== "__main__":
    main()