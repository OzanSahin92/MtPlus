import numpy as np
import netCDF4


# taking into account that seasonality plays a role in the slp levels, therefore we calculate te slp threshhold for
# extreme events for every single month in winter extracting extreme events out of the slp data by identifying slp
# under the 5th perc as a cyclone
def extreme_events(
        time_series):  # daily time series, which begin in january and only consists of the months j, f, m,  n, d
    # separate the data into the separate months of january, february, march, november and december
    # to calculate the 5th percentile thresholds of the separate months
    nov = []
    dec = []
    jan = []
    feb = []
    mar = []

    counter = 1
    for day in time_series:
        if counter <= 31:
            jan.append(day)
        elif 31 < counter <= 59:
            feb.append(day)
        elif 59 < counter <= 90:
            mar.append(day)
        elif 90 < counter <= 120:
            nov.append(day)
        else:
            dec.append(day)
        counter += 1
        if counter == 152:
            counter = 1

    jan_arr = np.array(jan)
    feb_arr = np.array(feb)
    mar_arr = np.array(mar)
    nov_arr = np.array(nov)
    dec_arr = np.array(dec)

    jan5th_perc = np.percentile(jan_arr, 5, axis=0)
    feb5th_perc = np.percentile(feb_arr, 5, axis=0)
    mar5th_perc = np.percentile(mar_arr, 5, axis=0)
    nov5th_perc = np.percentile(nov_arr, 5, axis=0)
    dec5th_perc = np.percentile(dec_arr, 5, axis=0)

    # identify extreme events with the separate thresholds and create an extreme event time series
    extreme_event_bool = []
    counter = 1
    for day in time_series:
        if counter <= 31:
            extreme_event_bool.append(day < jan5th_perc)
        elif 31 < counter <= 59:
            extreme_event_bool.append(day < feb5th_perc)
        elif 59 < counter <= 90:
            extreme_event_bool.append(day < mar5th_perc)
        elif 90 < counter <= 120:
            extreme_event_bool.append(day < nov5th_perc)
        else:
            extreme_event_bool.append(day < dec5th_perc)
        counter += 1
        if counter == 152:
            counter = 1

    extreme_event_arr = np.array(extreme_event_bool).astype('int')

    return extreme_event_arr


def main():
    data_path = '../data/'
    # read
    slp_data = 'slp.4dx4dy.nh_ndjfm_19792019_subseas_cell.nc'
    # write
    extreme_event_data = 'extreme.4dx4dy.19792019_nh_ndjfm_subseas_cell.txt'

    dataset = netCDF4.Dataset(data_path + slp_data, 'r')
    # extract the raw data out of the dataset
    var = dataset.variables['var1'][:].data

    extreme_event_arr = extreme_events(var)

    print(extreme_event_arr.shape, '\n', extreme_event_arr.sum(axis=0), '\n', extreme_event_arr)

    np.savetxt(data_path + extreme_event_data, extreme_event_arr)


if __name__ == "__main__":
    main()
