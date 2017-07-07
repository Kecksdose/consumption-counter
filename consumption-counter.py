import matplotlib.pyplot as plt

import datetime
from dateutil.relativedelta import relativedelta

dates = ["01.08.2015", "31.08.2015", "17.11.2015", "13.12.2015",
         "17.01.2016", "06.03.2016", "06.07.2016", "31.07.2016",
         "04.12.2016", "19.01.2017", "07.02.2017", "21.03.2017",
         "14.05.2017", "28.05.2017", "04.06.2017", "25.06.2017"]
counts = [13169, 13263, 13470, 13548,
          13673, 13835, 14275, 14348,
          14698, 14876, 14965, 15117,
          15439, 15518, 15557, 15656]

class ConsumptionCounter(object):
    """Calculate and plots consumtion in certain time intervals."""
    def __init__(self, date_strings, counts, date_format='%d.%m.%Y'):
        if not isinstance(date_strings, list):
            date_strings = [date_strings]

        if not isinstance(counts, list):
            counts = [counts]



def month_starts(dates):
    first_date = dates[0]
    first_date_month = first_date.month
    first_date_year = first_date.year

    # Get first day of month (kalendae)
    first_kalendae = datetime.datetime(day=1, month=first_date_month, year=first_date_year)

    last_date = dates[-1]
    last_date_month = last_date.month
    last_date_year = last_date.year

    last_kalendae = datetime.datetime(day=1, month=last_date_month, year=last_date_year)

    # If last day is not kalendea, choose the next month
    if not last_date.day == 1:
        last_kalendae += relativedelta(months=1)

    delta_dates = relativedelta(last_kalendae, first_kalendae)
    n_months = delta_dates.years * 12 + delta_dates.months

    return [first_kalendae + relativedelta(months=m) for m in range(n_months + 1)]

dates_to_determine = month_starts(dates_formatted)

def lenght_of_month(date):
    first = datetime.datetime(day=1, month=date.month, year=date.year)
    if date.month == 12:
        later = datetime.datetime(day=1, month=1, year=date.year + 1)
    else:
        later = datetime.datetime(day=1, month=date.month + 1, year=date.year)
    return later - first



def interpolate(dtd, dates, counts):
    """Interpolates the the counts at a specific date.

    Inputs:
        dtd: datetime object, date to determine.
        dates: list of two dates.
        counts: corresponting counts.

    Returns:
        (interpolation value, certainty fraction)
    """

    n_seconds = (dates[1] - dates[0]).total_seconds()
    n_counts = (counts[1] - counts[0])
    counts_per_seconds = n_counts / n_seconds

    if dtd < dates[0]:
        # Interpolate left
        #print('Interpolate left')
        interpolation = counts[0] - (dates[0] - dtd).total_seconds() * counts_per_seconds
        certainty_frac = 1 - ((dates[0] - dtd).total_seconds() /
                         lenght_of_month(dtd).total_seconds())
    elif dtd > dates[1]:
        # Interpolate right
        #print('Interpolate right')
        interpolation = counts[1] + (dtd - dates[1]).total_seconds() * counts_per_seconds
        certainty_frac = 1 - ((dtd - dates[1]).total_seconds() /
                         lenght_of_month(dtd).total_seconds())
    else:
        # Interpolate center
        #print('Interpolate center')
        interpolation = counts[0] + (dtd - dates[0]).total_seconds() * counts_per_seconds
        certainty_frac = 1

    return interpolation, certainty_frac


def get_closest_indices(val, arr):
    if val < arr[0]:
        #print('Quick left')
        return 0, 2
    elif val > arr[-1]:
        #print('Quick right')
        return len(arr) - 2, len(arr)
    else:
        for a in arr:
            if a > val:
                cur_index = arr.index(a) - 1
                break
        if cur_index > len(arr) - 2:
            #print('Normal:')
            return len(arr) - 2, len(arr)
        else:
            #print('Else:')
            return cur_index, cur_index + 2


def prepare_data(dtds, dates, counts):
    counts_and_certainties = []
    for dtd in dtds:
        for df, c in zip(dates, counts):
            indices = get_closest_indices(dtd, dates)
            result = interpolate(dtd,
                                 dates[indices[0]: indices[1]],
                                 counts[indices[0]: indices[1]])
            counts_and_certainties.append(result)
            break
    return counts_and_certainties


def plot_data(data, dtds, registerd_dates, daily=True):
    month_names = [calendar.month_abbr[m] for m in range(1, 13)]
    calculated_counts = [d[0] for d in data]
    fractions = [d[1] for d in data]
    print(fractions)
    # Only one month
    if len(fractions) == 2:
        fractions = [ (registerd_dates[1] - registerd_dates[0]).days / \
        (dtds[1]-dtds[0]).days]

    if len(fractions) >= 3:
        fractions.pop(1)

    calculated_deltas = []

    for i in range(len(calculated_counts) - 1):
        calculated_deltas.append(calculated_counts[i + 1] - calculated_counts[i])

    if daily:
        normed_deltas = []
        for d, dtd in zip(calculated_deltas, dtds):
            normed_deltas.append(d / lenght_of_month(dtd).days)
        calculated_deltas = normed_deltas

    counts_times_fractions = [c*f for c, f in zip(calculated_deltas, fractions)]

    # Plot yearly
    years = range(dtds[0].year, dtds[-1].year + 1)

    for year in years:
        dates_in_year = [date for date in dtds if date.year == year]
        dates_indices = [dtds.index(date) for date in dtds if date.year == year]

        # 12 months
        inputs = {m: (0, 0) for m in range(12)}
        for diy, c, ctf in zip(dates_in_year,
                               calculated_deltas[dates_indices[0]: dates_indices[-1] + 1],
                               counts_times_fractions[dates_indices[0]: dates_indices[-1] + 1]):
            inputs[diy.month - 1] = (c, ctf)

        plt.bar(list(inputs.keys()), [val[0] for val in list(inputs.values())], alpha=0.5)
        plt.bar(list(inputs.keys()), [val[1] for val in list(inputs.values())], alpha=1,
                color='#1f77b4')
        plt.title(year)
        plt.grid()
        plt.xticks(range(12), month_names)

        plt.show()


data = prepare_data(dates_to_determine, dates_formatted, counts)
    plot_data(data, dates_to_determine, dates_formatted, daily=True)
