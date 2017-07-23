import os
import datetime
import dateutil
import calendar
import matplotlib.pyplot as plt
plt.ioff()

class ConsumptionCounter():
    '''Consumption Counter!'''

    def __init__(self, date_strings, consumtions, date_format='%d.%m.%Y'):
        if not isinstance(date_strings, list):
            date_strings = [date_strings]

        if not isinstance(consumtions, list):
            consumtions = [consumtions]

        self.dates = [datetime.datetime.strptime(date_string, date_format)
                      for date_string in date_strings]
        self.consumtions = consumtions

        # Calculate anchor points
        self.anchor_points = self.get_anchor_points(self.dates)

        # Calculate consumption of certain anchor points
        self.counts_and_certainties = self.prepare_data(
            self.anchor_points,
            self.dates,
            self.consumtions)

    def get_anchor_points(self, dates, freq='M'):
        available_freqs = ['M']
        if freq not in available_freqs:
            raise ValueError(f'Frequency option not found. Choose one of these: {available_freqs}')
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
            last_kalendae += dateutil.relativedelta.relativedelta(months=1)

        delta_dates = dateutil.relativedelta.relativedelta(last_kalendae, first_kalendae)
        n_months = delta_dates.years * 12 + delta_dates.months

        return [first_kalendae + dateutil.relativedelta.relativedelta(months=m) for m in range(n_months + 1)]

    def get_number_of_days_in_month(self, date):
        first = datetime.datetime(day=1, month=date.month, year=date.year)
        if date.month == 12:
            later = datetime.datetime(day=1, month=1, year=date.year + 1)
        else:
            later = datetime.datetime(day=1, month=date.month + 1, year=date.year)
        return later - first

    def interpolate(self, dtd, dates, counts):
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
                             self.get_number_of_days_in_month(dtd).total_seconds())
        elif dtd > dates[1]:
            # Interpolate right
            #print('Interpolate right')
            interpolation = counts[1] + (dtd - dates[1]).total_seconds() * counts_per_seconds
            certainty_frac = 1 - ((dtd - dates[1]).total_seconds() /
                             self.get_number_of_days_in_month(dtd).total_seconds())
        else:
            # Interpolate center
            #print('Interpolate center')
            interpolation = counts[0] + (dtd - dates[0]).total_seconds() * counts_per_seconds
            certainty_frac = 1

        return interpolation, certainty_frac

    def prepare_data(self, dtds, dates, counts):
        """Interpolates counts on given dates.
        Inputs:
            dtds: 'dates to determine', list of dates you want to interpolates counts for.
            dates: List of dates, where you know the counts.
            counts: list of counts.
        Returns:
            tuple of counts and certainty fraction
        """
        counts_and_certainties = []
        for dtd in dtds:
            for df, c in zip(dates, counts):
                indices = self.get_closest_indices(dtd, dates)
                result = self.interpolate(dtd,
                                          dates[indices[0]: indices[1]],
                                          counts[indices[0]: indices[1]])
                counts_and_certainties.append(result)
                break
        return counts_and_certainties

    def get_closest_indices(self, val, arr):
        if val < arr[0]:
            return 0, 2
        elif val > arr[-1]:
            return len(arr) - 2, len(arr)
        else:
            for a in arr:
                if a > val:
                    cur_index = arr.index(a) - 1
                    break
            if cur_index > len(arr) - 2:
                return len(arr) - 2, len(arr)
            else:
                return cur_index, cur_index + 2

    def plot_data(self, data, dtds, normed=True):
        month_names = [calendar.month_abbr[m] for m in range(1, 13)]
        calculated_counts = [d[0] for d in data]
        fractions = [d[1] for d in data]

        if len(fractions) >= 3:
            fractions.pop(1)

        calculated_deltas = []

        for i in range(len(calculated_counts) - 1):
            calculated_deltas.append(calculated_counts[i + 1] - calculated_counts[i])

        if normed:
            normed_deltas = []
            for d, dtd in zip(calculated_deltas, dtds):
                normed_deltas.append(d / self.get_number_of_days_in_month(dtd).days)
            calculated_deltas = normed_deltas

        counts_times_fractions = [c*f for c, f in zip(calculated_deltas, fractions)]

        # Plot yearly
        if dtds[0].year == dtds[-1].year:
            years = [dtds[0].year]
        else:
            years = range(dtds[0].year, dtds[-1].year + 1)

        figs = []

        for year in years:
            dates_in_year = [date for date in dtds if date.year == year]
            dates_indices = [dtds.index(date) for date in dtds if date.year == year]

            # 12 months
            inputs = {m: (0, 0) for m in range(12)}
            for diy, c, ctf in zip(dates_in_year,
                                   calculated_deltas[dates_indices[0]: dates_indices[-1] + 1],
                                   counts_times_fractions[dates_indices[0]: dates_indices[-1] + 1]):
                inputs[diy.month - 1] = (c, ctf)

            fig1 = plt.figure()

            plt.bar(list(inputs.keys()), [val[0] for val in list(inputs.values())], alpha=0.5)
            plt.bar(list(inputs.keys()), [val[1] for val in list(inputs.values())], alpha=1,
                    color='#1f77b4')
            plt.title(year)
            plt.grid()
            plt.xticks(range(12), month_names)

            figs.append(fig1)

        return figs

if __name__ == '__main__':
    random_dates = ["01.02.2015", "17.05.2016", "29.08.2016"]
    random_counts = [15, 45, 80]

    cc = ConsumptionCounter(random_dates, random_counts)

    figs = cc.plot_data(cc.counts_and_certainties, cc.anchor_points)

    save_path = 'plots/'
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    for i, fig in enumerate(figs, start=1):
        fig.savefig(save_path + f'plot_{i}.pdf')


