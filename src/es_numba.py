#!/usr/bin/env python
# coding: utf-8

import numpy as np
import netCDF4
from numba import jit
from mpi4py import MPI
from scipy import sparse
import pandas as pd
import sys
import time
from numba import types
from numba.typed import Dict
import collections.abc


# uniquely pairing two numbers
@jit(nopython=True)
def cantor_pairing(num1, num2):
    return 0.5 * (num1 + num2) * (num1 + num2 + 1) + num2


# flattend a nested dictionary with float values as keys
def flatten(d):
    dict_list = []
    for k, v in d.items():
        for k2, v2 in v.items():
            dict_list.append((cantor_pairing(k, k2), v2))
    return dict(dict_list)


@jit(nopython=True)
def eventsync(es1, es2, taumax, ts1=None,
              ts2=None):  # taumax in Zeitschritten, im fall von täglichen daten ist ein Zeitschritt ein Tag / np.inf
    # Get time indices
    if ts1 is None:
        e1 = np.where(es1)[0]
    else:
        e1 = ts1[es1.astype(np.bool_)]
    if ts2 is None:
        e2 = np.where(es2)[0]
    else:
        e2 = ts2[es2.astype(np.bool_)]
    # del es1, es2, ts1 , ts2
    # Number of events
    l1 = len(e1)
    l2 = len(e2)
    if l1 == 0 or l2 == 0:  # Division by zero in output
        return np.nan, np.nan
    if l1 in [1, 2] or l2 in [1, 2]:  # Too few events to calculate
        return 0., 0.

    E1 = np.empty((l2 - 2, e1[1:-1].shape[0]))
    for i in range(l2 - 2):
        E1[i, :] = e1[1:-1]

    E2 = np.empty((l1 - 2, e2[1:-1].shape[0]))
    for i2 in range(l1 - 2):
        E2[i2, :] = e2[1:-1]

    dst12 = E1.astype(np.int32).T - E2.astype(np.int32)

    # Dynamical delay
    diff1 = np.diff(e1)
    diff2 = np.diff(e2)
    diff1min = np.minimum(diff1[1:], diff1[:-1])
    diff2min = np.minimum(diff2[1:], diff2[:-1])

    Diff1 = np.empty((l2 - 2, diff1min.shape[0]))
    for i3 in range(l2 - 2):
        Diff1[i3, :] = diff1min

    Diff2 = np.empty((l1 - 2, diff2min.shape[0]))
    for i4 in range(l1 - 2):
        Diff2[i4, :] = diff2min

    tau = 0.5 * np.minimum(Diff1.astype(np.float32).T, Diff2.astype(np.float32))

    efftau = np.minimum(tau, taumax)
    # del diff1 , diff2 , diff1min, diff2min, tau
    # Count equal time events and synchronised events
    eqtime = 0.5 * np.sum(dst12 == 0)
    count12 = np.sum(
        (dst12 > 0) * (dst12 <= efftau)) + eqtime  # extreme-events happen on node 2 before happening on node 1
    count21 = np.sum(
        (dst12 < 0) * (-dst12 <= efftau)) + eqtime  # extreme-events happen on node 1 before happening on node 2
    norm = np.sqrt((l1 - 2) * (l2 - 2))  # necessary?
    # del dst12
    return np.float32(count12 / norm), np.float32(count21 / norm)  # np.float32 in front of (count##/nom)


# returns ES in two directions es1->es2, es2->es1

# cleaning the event time series of consecutive events/ events on consecutive timesteps (6h) are considered as single
# events and are placed on the first timestep
@jit(nopython=True)
def clean_consecutive_events(data, ts):  # every node in data as the same timesteps
    clean_data = np.copy(data)
    for i in range(clean_data.shape[0]):
        for j in range(clean_data.shape[1] - 1):
            diff_ts = ts[j + 1] - ts[j]
            if data[i][j] == 1 and data[i][j + 1] == 1 and diff_ts == 1:
                clean_data[i][j + 1] = 0
            else:
                continue
    return clean_data


@jit(nopython=True)
def treshhold_params(thresh, ES_surrogate_i_j, ES_surrogate_j_i, unique_num_of_events, ts1, ts2, taumax, sign):
    for i in range(unique_num_of_events.shape[0]):
        for j in range(unique_num_of_events.shape[0]):
            for n in range(len(ES_surrogate_i_j)):
                sur1 = (np.random.random(size=6130) < (unique_num_of_events[
                                                           i] / 6130))  # 6130 - temporal size of data and 308/6130 -
                # prbability of an event
                sur2 = (np.random.random(size=6130) < (unique_num_of_events[j] / 6130))
                ES_surrogate_i_j[n] = eventsync(sur1, sur2, taumax, ts1, ts2)[0]
                ES_surrogate_j_i[n] = eventsync(sur1, sur2, taumax, ts1, ts2)[1]
            thresh[i, j] = np.percentile(ES_surrogate_i_j,
                                         sign)  # diagonal elements are calculated twice... could be optimized with
            # an if i == j condition
            thresh[j, i] = np.percentile(ES_surrogate_j_i, sign)
    return thresh


@jit(nopython=True)
def es_loop(clean_data, es, sign_es, size, rank, ts1, ts2, d,
            taumax):  # clean_data should be the cleaned version of data
    prange = int(clean_data.shape[0] / size)
    for i in range(prange * rank, prange * (rank + 1)):
        for j in range(i + 1, clean_data.shape[0]):
            es_val1 = eventsync(clean_data[i], clean_data[j], taumax, ts1, ts2)[0]
            es_val2 = eventsync(clean_data[i], clean_data[j], taumax, ts1, ts2)[1]
            es[i, j] = es_val1
            es[j, i] = es_val2
            if es_val1 >= d[
                cantor_pairing(clean_data[i].sum(), clean_data[j].sum())]:  # str function causes errors with numba
                sign_es[i, j] = 1
            else:
                sign_es[i, j] = 0
            if es_val2 >= d[cantor_pairing(clean_data[j].sum(), clean_data[i].sum())]:
                sign_es[j, i] = 1
            else:
                sign_es[j, i] = 0
    return es, sign_es


def get_timesteps():
    # time steps for NDJFM daily data from 1979-2019(JFM) with 14690 time steps in total and with 6130 time steps
    # for only ndjfm
    time_steps = []
    counter = 0
    for i in range(1, 14691):
        if counter <= 90 or counter > 304:
            time_steps.append(i)
        counter += 1
        if counter == 366:
            counter = 1
    return np.array(time_steps)


def main():
    taumax_str = sys.argv[1]
    taumax = int(sys.argv[1])  # f.e. 16
    sign = float(sys.argv[2])  # f.e. 99.5
    goal_dir = str(sys.argv[3])  # f.e. final_es/
    compoundmonths_ndjfm = 0
    compoundmonths_ndjfm_daymean = 0
    compoundmonths_ndjfm_daymean_spatially_reduced = 1
    if compoundmonths_ndjfm:
        # file_path = '/atm_glomod/user/osahin/data/ERA5/6hourlymean_1979-2019/EOFs_4dx4dy_ndjfm/'
        file_path = '/p/tmp/sahin/'

        # files to read
        file_extreme = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180.nc'

        # files to write
        file_es = 'es_reduced.4dx4dy.ndjfm.txt'
        # file_es_surrogate = 'es_surrogate_reduced.4dx4dy.ndjfm.txt'

        dataset = netCDF4.Dataset(file_path + file_extreme2, 'r')  # r steht für read
        var = dataset.variables['extreme_events'][:]
        lats = dataset.variables['latitude'][:]
        lons = dataset.variables['longitude'][:]

        dataset.close()

    elif compoundmonths_ndjfm_daymean:
        # file_path = '/atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/'
        file_path = '/p/tmp/sahin/'

        # file to read
        # file_extreme = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180_daymean.nc'
        # file_extreme = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180.nc'
        file_extreme2 = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180_subseas.nc'

        # files to write
        file_thresh = 'thresh_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.txt'
        file_es = 'es_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.txt'
        file_sign_es = 'sign_es_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.txt'
        file_num_of_events = 'num_of_events_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.txt'
        # file_es_surrogate = 'es_surrogate_thresh.95perc.taumax'+taumax_str+'.4dx4dy.ndjfm_test.txt'

        time_steps_arr = get_timesteps()

        dataset = netCDF4.Dataset(file_path + file_extreme2, 'r')  # r steht für read
        var = dataset.variables['extreme_events'][:]
        lats = dataset.variables['latitude'][:]
        lons = dataset.variables['longitude'][:]

        dataset.close()

    elif compoundmonths_ndjfm_daymean_spatially_reduced:
        # file_path = '/atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/'
        file_path = '/p/tmp/sahin/'

        # file to read
        # file_extreme = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180_daymean.nc'
        # file_extreme = 'extreme.4dx4dy.19792019_nh_ndjfm_lon180180.nc'
        file_extreme2 = 'extreme.4dx4dy.19792019_nh_ndjfm_subseas_cell.txt'

        # files to write
        file_thresh = 'thresh_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.spatiallyReduced.txt'
        file_es = 'es_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.spatiallyReduced.txt'
        file_sign_es = 'sign_es_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.spatiallyReduced.txt'
        file_num_of_events = 'num_of_events_subseas.taumax' + taumax_str + '.4dx4dy.ndjfm.spatiallyReduced.txt'
        # file_es_surrogate = 'es_surrogate_thresh.95perc.taumax'+taumax_str+'.4dx4dy.ndjfm_test.txt'

        # time steps for NDJFM daily data from 1979-2019(JFM) with 14690 time steps in total and with 6130 time steps
        # for only NDJFM
        time_steps = []
        counter = 0
        for i in range(1, 14691):
            if counter <= 90 or counter > 304:
                time_steps.append(i)
            counter += 1
            if counter == 366:
                counter = 1
        time_steps_arr = np.array(time_steps)

        var = np.loadtxt(file_path + file_extreme2)
        # reduced data [:1000,:10,106:116]
        # var2 = var[:,:60,106:206] #var2 = var[:,:54,106:215]

    if compoundmonths_ndjfm or compoundmonths_ndjfm_daymean:
        n = var.shape[1] * var.shape[2]
        # n = var2.shape[1]*var2.shape[2]

        data = np.reshape(var, (var.shape[0], n)).T
        # reduced area containing north america, scandinavia and the rest of europe
        # data = np.reshape(var2, (var2.shape[0], n)).T
    elif compoundmonths_ndjfm_daymean_spatially_reduced:
        n = var.shape[1]
        data = var.T

    es = np.zeros((n, n), dtype=np.float32)
    sign_es = np.zeros((n, n), dtype=np.float32)
    es_surrogate_i_j = np.zeros(1000, dtype=np.float32)
    es_surrogate_j_i = np.zeros(1000, dtype=np.float32)

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    clean_data = clean_consecutive_events(data, time_steps_arr)
    del data

    # creating a dictionary that has es-threshold values for every combination of number of events in time series
    num_of_events = np.unique(clean_data.sum(axis=1))
    thresh = np.zeros((num_of_events.shape[0], num_of_events.shape[0]), dtype=np.float32)
    thresh_val = treshhold_params(thresh, es_surrogate_i_j, es_surrogate_j_i, num_of_events, time_steps_arr,
                                  time_steps_arr, taumax, sign)
    thresh_df = pd.DataFrame(data=thresh_val, index=num_of_events,
                             columns=num_of_events)  # values, 1st column as index, 1st row as the column names
    thresh_nested_dict = thresh_df.to_dict()
    thresh_flat_dict = flatten(thresh_nested_dict)

    # dictionary that is understandable for numba, because it is typed
    d = Dict.empty(key_type=types.float32, value_type=types.float32)

    # filling the numba dict with the threshold dict keys and values
    for k, v in thresh_flat_dict.items():
        d[k] = v

    ev_sync, sign_ev_sync = es_loop(clean_data, es, sign_es, size, rank, time_steps_arr, time_steps_arr, d, taumax)
    del clean_data

    ev_sync_csr = sparse.csr_matrix(ev_sync)
    del ev_sync

    sign_ev_sync_csr = sparse.csr_matrix(sign_ev_sync)
    del sign_ev_sync

    if rank == 0:
        np.savetxt(file_path + goal_dir + str(rank) + '_' + str(sign) + '_' + file_num_of_events, num_of_events)
        np.savetxt(file_path + goal_dir + str(rank) + '_' + str(sign) + '_' + file_thresh, thresh_val)

    sparse.save_npz(file_path + goal_dir + str(rank) + '_' + str(sign) + '_' + file_es, ev_sync_csr)
    sparse.save_npz(file_path + goal_dir + str(rank) + '_' + str(sign) + '_' + file_sign_es, sign_ev_sync_csr)


if __name__ == "__main__":
    main()
