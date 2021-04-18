import numpy as np
import pandas as pd
import netCDF4
import sys
from ece_timeseries import extreme_events
from es_numba import get_timesteps, clean_consecutive_events


def read_nc_data(file_path):
    dataset = netCDF4.Dataset(file_path, 'r')
    # extract the raw data out of the dataset
    var = dataset.variables['var1'][:].data

    return var


def get_lats_lons(file_path):
    lat_list = []
    lon_list = []
    counter = 0
    with open(file_path, "r") as file:
        for line in file:
            # file_grid_cells specific tasks
            if 2 < counter < 83:
                lon_list.append(np.array(line.split(' ')[:-1], dtype=np.float64))
            if counter > 84:
                lat_list.append(np.array(line.split(' ')[:-1], dtype=np.float64))

            counter += 1
    lat = np.concatenate(lat_list, axis=0)
    lon = np.concatenate(lon_list, axis=0)

    lat_lon_list = []
    for i in range(lat.shape[0]):
        lat_lon_list.append((lat[i], lon[i]))
    lat_lon = np.array(lat_lon_list)

    return lat_lon


def regional_timeseries(slp_data, lats_lons, regional_lats_lons):
    relevant_nodes = np.argwhere(((lats_lons[:, 0] <= regional_lats_lons[1]) & (
            lats_lons[:, 0] >= regional_lats_lons[0]) & (lats_lons[:, 1] <= regional_lats_lons[3]) & (
                                          lats_lons[:, 1] >= regional_lats_lons[2])) == True)
    regional_ts = (slp_data[relevant_nodes].sum(axis=0) / slp_data[relevant_nodes].shape[0])[0, :]

    return regional_ts


def clean_events(ev_ts1, ev_ts2, time_steps_arr):
    data = np.zeros((2, 6130))
    data[0, :] = ev_ts1
    data[1, :] = ev_ts2
    clean_data = clean_consecutive_events(data, time_steps_arr)
    clean_ev_ts1 = clean_data[0, :]
    clean_ev_ts2 = clean_data[1, :]

    return clean_ev_ts1, clean_ev_ts2, clean_data


def get_teleconnection_ece_times(clean_eces_region, clean_eces_spitsbergen, ts, region_to_spitsbergen,
                                 spitsbergen_to_region, df):
    event_times_region = ts[clean_eces_region.astype(np.bool_)]
    event_times_spitsbergen = ts[clean_eces_spitsbergen.astype(np.bool_)]
    # for knowing which indices the events have in the array
    event_time_indices_region = np.where(clean_eces_region)[0]
    # for knowing which indices the events have in the array
    event_time_indices_spitsbergen = np.where(clean_eces_spitsbergen)[0]

    number_of_events_region = len(event_times_region)
    number_of_events_spitsbergen = len(event_times_spitsbergen)

    # time differences of all events in spitsbergen and all events in region and vice versa
    # dimension 0 displays the event times in spitsbergen and dimension 1 displays event times in region
    dst12 = (np.array([event_times_spitsbergen[1:-1]] * (number_of_events_region - 2), dtype='int32').T - np.array(
        [event_times_region[1:-1]] * (number_of_events_spitsbergen - 2), dtype='int32'))

    diff_between_events_region = np.diff(event_times_region)
    diff_between_events_spitsbergen = np.diff(event_times_spitsbergen)
    diff1min = np.minimum(diff_between_events_spitsbergen[1:], diff_between_events_spitsbergen[:-1])
    diff2min = np.minimum(diff_between_events_region[1:], diff_between_events_region[:-1])

    tau = 0.5 * np.minimum(np.array([diff1min] * (number_of_events_region - 2), dtype='float32').T,
                           np.array([diff2min] * (number_of_events_spitsbergen - 2), dtype='float32'))

    tau_max = 16
    eff_tau = np.minimum(tau, tau_max)

    if region_to_spitsbergen:
        event_times_region_spitsbergen = event_time_indices_region[np.where(((dst12 > 0) * (dst12 <= eff_tau)))[1] + 1]
    elif spitsbergen_to_region:
        event_times_region_spitsbergen = event_time_indices_spitsbergen[
            np.where(((dst12 < 0) * (-dst12 <= eff_tau)))[0] + 1]

    # checks inside the dataframe, if the difference in days is always equal to tau_max, because we look at winter
    # months only
    filter_arr = ((df.iloc[event_times_region_spitsbergen + 16]['time steps in days'].to_numpy() -
                   df.iloc[event_times_region_spitsbergen]['time steps in days'].to_numpy())) == 16

    # filtering times out that are not part of the dataset, because for example if there is an event on the 31st march,
    # then we dont have data for 16 days later
    event_times_region_spitsbergen = event_times_region_spitsbergen[filter_arr]

    return event_times_region_spitsbergen


def main():
    if len(sys.argv) == 1:
        print('No arguments were given!\n'
              'Possible arguments:\n'
              '\tarabiansea\n'
              '\twestafrica\n'
              '\tpacific\n'
              '\tkazakhstan\n'
              '\tnorthwestrussia\n'
              '\tnorthamerica\n')
    elif len(sys.argv) > 1:
        data_path = '../data/'
        # read
        slp_data_path = 'slp.4dx4dy.nh_ndjfm_19792019_subseas_cell.nc'
        grid_cells_path = 'grid_cell.txt'
        # write
        teleconnection_eces_file = '_ECEs_times.txt'
        regional_ece_timeseries_file = '_clean_ece_timeserie.txt'

        slp_data = read_nc_data(data_path + slp_data_path).T
        lats_lons = get_lats_lons(data_path + grid_cells_path)

        spitsbergen_lats_lons = np.array([76.2997, 79.672035, 9, 24.75])
        spitsbergen = regional_timeseries(slp_data, lats_lons, spitsbergen_lats_lons)
        spitsbergen_eces = extreme_events(spitsbergen)

        if sys.argv[1] == 'arabiansea':
            region_lats_lons = np.array([15, 25, 56, 66])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'Arabian Sea'
            teleconnection_str = 'ASP'
            region_str = 'arabiansea'
            region_to_spitsbergen = 1
            spitsbergen_to_region = 0

        elif sys.argv[1] == 'westafrica':
            region_lats_lons = np.array([12, 22, -33, -15])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'Westafrica'
            teleconnection_str = 'WESP'
            region_str = 'westafrica'
            region_to_spitsbergen = 1
            spitsbergen_to_region = 0

        elif sys.argv[1] == 'pacific':
            region_lats_lons = np.array([22, 33, 150, 160])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'Pacific'
            teleconnection_str = 'PASP'
            region_str = 'pacific'
            region_to_spitsbergen = 1
            spitsbergen_to_region = 0

        elif sys.argv[1] == 'kazakhstan':
            region_lats_lons = np.array([42, 45, 68, 82])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'Kazakhstan'
            teleconnection_str = 'SPKAZ'
            region_str = 'kazakhstan'
            region_to_spitsbergen = 0
            spitsbergen_to_region = 1

        elif sys.argv[1] == 'northwestrussia':
            region_lats_lons = np.array([55, 63, 33, 63])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'Northwest Russia'
            teleconnection_str = 'SPRUS'
            region_str = 'northwestrussia'
            region_to_spitsbergen = 0
            spitsbergen_to_region = 1


        elif sys.argv[1] == 'northamerica':
            region_lats_lons = np.array([51, 60, -108, -88])
            region = regional_timeseries(slp_data, lats_lons, region_lats_lons)
            region_eces = extreme_events(region)

            region_name = 'North America'
            teleconnection_str = 'SPAM'
            region_str = 'northamerica'
            region_to_spitsbergen = 0
            spitsbergen_to_region = 1

        ts = get_timesteps()

        clean_eces_region, clean_eces_spitsbergen, unnecessary = clean_events(region_eces, spitsbergen_eces, ts)

        if region_to_spitsbergen:
            # dataframe has clean events, time_steps and time indices in one dataframe
            df = pd.DataFrame({'events': clean_eces_region, 'time steps in days': ts})

        elif spitsbergen_to_region:
            # dataframe has clean events, time_steps and time indices in one dataframe
            df = pd.DataFrame({'events': clean_eces_spitsbergen, 'time steps in days': ts})

        teleconnection_ece_times = get_teleconnection_ece_times(clean_eces_region, clean_eces_spitsbergen, ts,
                                                                region_to_spitsbergen,
                                                                spitsbergen_to_region, df)

        print('Teleconnection (Spitsbergen and ', region_name, ') ECE times :', teleconnection_ece_times)

        np.savetxt(data_path + region_str + regional_ece_timeseries_file, clean_eces_region, fmt='%i')
        np.savetxt(data_path + 'spitsbergen' + regional_ece_timeseries_file, clean_eces_spitsbergen, fmt='%i')
        np.savetxt(data_path + teleconnection_str + teleconnection_eces_file, teleconnection_ece_times, fmt='%i')


if __name__ == "__main__":
    main()
