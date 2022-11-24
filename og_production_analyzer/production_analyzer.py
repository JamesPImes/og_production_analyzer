# Copyright (c) 2021-2022, James P. Imes. All rights reserved.

"""
A wrapper for pandas DataFrame for checking oil and/or gas production
records for gaps.
"""

from calendar import monthrange
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import date2num


class ProductionAnalyzer:
    """
    Check a DataFrame that contains monthly oil and/or gas production
    data for gaps.
    """

    # Headers to add for aggregation columns.
    ANY_ACTIVE = 'any_active'
    ANY_SHUTIN = 'any_shutin'
    NUM_ACTIVE = 'num_active'
    NUM_SHUTIN = 'num_shutin'
    DAYS_PRODUCING = 'max_days_producing'
    DAYS_NOT_PRODUCING = 'min_days_not_producing'

    def __init__(
            self,
            df: pd.DataFrame,
            date_col: str,
            oil_prod_col: str = None,
            gas_prod_col: str = None,
            days_produced_col: str = None,
            status_col: str = None,
            shutin_codes: list = None,
            oil_prod_min: int = 0,
            gas_prod_min: int = 0,
    ):
        """
        :param df: A ```DataFrame``` containing monthly oil and/or gas
         production data, monthly status codes, and/or the number of
         days of production during each month. (Will not be directly
         modified by this object.)
        :param date_col: The column header for the ```datetime``` that
         represents its entire month (e.g., 1/1/2011 for January 2011).
        :param oil_prod_col: (Optional) The header for oil production.
        :param gas_prod_col: (Optional) The header for gas production.
        :param days_produced_col: The column header for the number of
         days that the well produced during this month.
        :param status_col: (Optional) The header for the column
         containing status codes.
        :param shutin_codes: (Optional) A list of case-sensitive status
         codes that can be considered shut-in.
        :param oil_prod_min: (Optional) Minimum threshold for oil
         production (in BBLs). (Default is ```0```, i.e. no minimum.)
        :param gas_prod_min: (Optional) Minimum threshold for gas
         production (in MCF). (Default is ```0```, i.e. no minimum.)
        """
        self.df = df.copy(deep=True)
        self.date_col = date_col
        self.oil_prod_col = oil_prod_col
        self.gas_prod_col = gas_prod_col
        self.oil_prod_min = oil_prod_min
        self.gas_prod_min = gas_prod_min
        self.status_col = status_col
        if isinstance(shutin_codes, str):
            shutin_codes = [shutin_codes]
        self.shutin_codes = shutin_codes
        self.days_produced_col = days_produced_col
        self._standardize_dates()
        self.prod_df = self.group_by_month()

    @property
    def is_configured_shutin(self):
        """
        Is this ```ProductionAnalyzer``` configured to check for
        shut-in?
        """
        return self.shutin_codes is not None and self.status_col is not None

    @property
    def is_configured_production(self):
        """
        Is this ```ProductionAnalyzer``` configured to check for
        production?
        """
        return self.oil_prod_col is not None or self.gas_prod_col is not None

    @property
    def is_configured_days_produced(self):
        """
        Is this ```ProductionAnalyzer``` configured to check for the
        number of days produced each month?
        """
        return self.days_produced_col is not None

    @property
    def configured_fields(self):
        possible = [
            self.date_col,
            self.oil_prod_col,
            self.gas_prod_col
            ]
        return [f for f in possible if f is not None]

    @property
    def first_month(self):
        """Get the first day of the first month as a ```datetime```."""
        first = self.df[self.date_col].min()
        return first_day_of_month(first)

    @property
    def last_month(self):
        """Get the first day of the last month as a ```datetime```."""
        last = self.df[self.date_col].max()
        return first_day_of_month(last)

    def _standardize_dates(self):
        """
        INTERNAL USE:
        Convert all dates in the configured ```.date_col``` to the first
        of the month, fill in any missing months between the first and
        last months, and sort by date (ascending). Any added dates will
        have values of 0 for the relevant fields.

        Store the results to ```.df``` as a deep copy of the original.
        """
        df = self.df.copy(deep=True)
        df[self.date_col] = df[self.date_col].apply(lambda x: first_day_of_month(x))

        # Ensure there are no months missing from the data.
        every_month = pd.DataFrame()
        every_month[self.date_col] = pd.date_range(
            start=self.first_month, end=self.last_month, freq='MS')
        df = pd.concat([df, every_month], ignore_index=True).fillna(0)
        df.sort_values(by=[self.date_col], ascending=True)
        self.df = df

    def get_relevant_groupby_fields(self):
        """
        Get the grouping fields (i.e. column names, as configured for
        this object and class, as applicable) and their respective
        aggregating functions.
        :return: A list of field names, and a dict of each field's
         aggregating function (i.e. the values are passable to the
         ```.agg()``` method in ```pandas```).
        """
        fields_source = (
            self.date_col,
            self.oil_prod_col,
            self.gas_prod_col,
            self.NUM_ACTIVE,
            self.NUM_SHUTIN,
            self.ANY_ACTIVE,
            self.ANY_SHUTIN,
            # self.DAYS_PRODUCING and self.DAYS_NOT_PRODUCING are added
            # only if days_produced_col is configured.
        )
        aggfuncs_source = {
            self.date_col: 'max',
            self.oil_prod_col: 'sum',
            self.gas_prod_col: 'sum',
            self.NUM_ACTIVE: 'sum',
            self.NUM_SHUTIN: 'sum',
            self.ANY_ACTIVE: 'max',
            self.ANY_SHUTIN: 'max',
            self.DAYS_PRODUCING: 'max',
            self.DAYS_NOT_PRODUCING: 'min',
        }
        fields = [f for f in fields_source if f is not None]
        if self.is_configured_days_produced:
            fields.append(self.DAYS_PRODUCING)
            fields.append(self.DAYS_NOT_PRODUCING)
        aggfuncs = {fd: ag for fd, ag in aggfuncs_source.items() if fd in fields}
        return fields, aggfuncs

    def group_by_month(self):
        """
        Group the DataFrame by month, aggregating the relevant fields by
        the appropriate function.

        Fields that were unspecified at init will not have any effect.
        """
        # This also makes a deep copy.
        prod = self.df.copy(deep=True)

        # Determine whether each well produced in a given month.
        prod[self.ANY_ACTIVE] = prod.apply(lambda row: self.row_is_producing(row), axis=1)
        prod[self.ANY_SHUTIN] = prod.apply(lambda row: self.row_is_shutin(row), axis=1)

        # These columns are identical duplicates and will be overwritten with
        # the aggregated values.
        prod[self.NUM_ACTIVE] = prod[self.ANY_ACTIVE]
        prod[self.NUM_SHUTIN] = prod[self.ANY_SHUTIN]

        if self.days_produced_col is not None:
            # Duplicate 'days producing' column for aggregating by max.
            prod[self.DAYS_PRODUCING] = prod[self.days_produced_col]
            # Corresponding days NOT producing, will be aggregated by min.
            prod[self.DAYS_NOT_PRODUCING] = prod.apply(
                lambda row: self.row_num_unproducing_days(row), axis=1)

        fields, aggfuncs = self.get_relevant_groupby_fields()
        grouped = prod.groupby(self.date_col, as_index=False)
        output = grouped[fields].agg(aggfuncs)
        output.sort_values(by=[self.date_col], ascending=True)
        return output

    def row_is_producing(self, row) -> bool:
        """
        Check if a dataframe row meets the threshold for oil and/or gas
        production. (By default, ANY production of oil and/or gas counts
        as producing -- i.e. minimums of 0 BBLs and 0 MCF.)

        Note: This will consider production only for those columns whose
         headers have been specified. That is, specify the header for
         oil to consider production for oil; and likewise for gas. If
         neither has been specified, this will return ```False``` by
         definition.

        :param row: A DataFrame row containing oil and/or gas
         production data.
        :return: Whether either or both production thresholds are met in
         this row.
        """
        def check_min_prod(row_, prod_col, prod_min) -> int:
            """
            Internal function to return the production if it meets the
            threshold. Otherwise, return 0.
            """
            if prod_col is None:
                return 0
            prod = row_[prod_col]
            if pd.isna(prod):
                prod = 0
            if prod < prod_min:
                prod = 0
            return prod

        oil_prod = check_min_prod(row, self.oil_prod_col, self.oil_prod_min)
        gas_prod = check_min_prod(row, self.gas_prod_col, self.gas_prod_min)
        return oil_prod + gas_prod > 0

    def row_is_shutin(self, row) -> bool:
        """
        Check if a dataframe row meets the criteria for being shut-in,
        based on the status code(s) in the status column.

        If the header for the column containing status codes has not
        been specified, it will return ```False``` by definition.

        :return: Whether this row meets the criteria for being shut-in.
        """
        shutin_codes = self.shutin_codes
        status_col = self.status_col
        if status_col is None:
            return False
        codes = shutin_codes
        if codes is None:
            codes = []
        return row[status_col] in codes

    def row_has_any_producing_days(self, row) -> bool:
        """
        Count the number of days in this month that were NOT producing.

        :param row: A DataFrame row that contains a Datetime, which
         represents its entire month.
        :return: Whether the row is stated to have at least one day of
         production.
        """
        return row[self.days_produced_col] in (0, None)

    def row_num_unproducing_days(self, row) -> int:
        """
        Calculate the number of days in this month that were NOT
        producing (regardless whether shut-in).

        :param row: A DataFrame row that contains a Datetime, which
         represents its entire month.
        :return: The number of days that were NOT produced during this
         month.
        """
        dt = pd.to_datetime(row[self.date_col])
        days_in_month = get_days_in_month(dt)
        days_produced = row[self.days_produced_col]
        if days_produced is None:
            return days_in_month
        return days_in_month - days_produced

    def gaps_by_production_threshold(
            self,
            shutin_as_producing=False,
            new_days_col: str = None,
            new_months_col: str = None
    ):
        """
        Find gaps in oil/gas production for those months that did not
        meet the specified production threshold(s).

        Optionally consider those months with a shut-in status code to
        be producing (i.e. if explicitly shut-in, then will not be
        considered a gap).

        IMPORTANT: This method considers production on a monthly basis,
         so any production that meets the threshold is considered to
         have occurred across the entire month. Thus, in a theoretical
         January when all the production actually occurred only on first
         day of the month (and on no other days), there would NOT be
         considered any gap -- even though the well(s) was technically
         NOT producing for 30 days.

        :param shutin_as_producing: Whether to consider an explicit
         shut-in status code to be "producing".
        :param new_days_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         days. If not specified, that data will not be added.
        :param new_months_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         months. If not specified, that data will not be added.
        :return: A ```DataFrame``` showing the ```'total_months'``` and
         ```'total_days'``` in each gap.
        """
        df = self.prod_df

        running_days_vals = []
        running_months_vals = []
        days_counter = 0
        months_counter = 0
        gap_start_date = None
        previous_last_day = None
        gaps = []

        for _, row in df.iterrows():
            first_day = row[self.date_col]
            days_in_month = get_days_in_month(first_day)
            last_day = last_day_of_month(first_day)
            is_producing = row[self.ANY_ACTIVE]
            is_shutin = False
            if self.is_configured_shutin:
                is_shutin = shutin_as_producing and row[self.ANY_SHUTIN]

            if not (is_producing or is_shutin):
                days_counter += days_in_month
                months_counter += 1
                if gap_start_date is None:
                    gap_start_date = first_day
            else:
                if gap_start_date is not None:
                    new_gap = (gap_start_date, previous_last_day)
                    gaps.append(new_gap)
                days_counter = 0
                months_counter = 0
                gap_start_date = None
            running_days_vals.append(days_counter)
            running_months_vals.append(months_counter)
            previous_last_day = last_day

        if gap_start_date is not None:
            # The final row was part of a gap.
            new_gap = (gap_start_date, previous_last_day)
            gaps.append(new_gap)

        # Add the columns, if requested
        if new_days_col is not None:
            df[new_days_col] = running_days_vals
        if new_months_col is not None:
            df[new_months_col] = running_months_vals
        return self._time_ranges_to_dataframe(gaps)

    def gaps_by_producing_days(
            self,
            shutin_as_producing=False,
            consider_production: bool = None,
            new_days_col: str = None,
            new_months_col: str = None
    ):
        """
        Find gaps in production for those months in which no days of
        production were reported.

        Optionally consider those months with a shut-in status code to
        be producing (i.e. if explicitly shut-in, then will not be
        considered a gap).

        NOTE: A shut-in code will be considered to have started on the
         first day of the month and ended on the last day of the month.

        IMPORTANT: In calculating the total days of each gap, this
         method assumes a 'worst case' scenario. That is, if March has
         21 reported days of production, April has 0 reported days of
         production, and May has 7 reported days of production, this
         method will assume this gap all occurred consecutively, for a
         gap of 64 days (being 10 days in March + 30 days in April + 24
         days in May).

         Moreover, in calculating gaps, this method will assume an
         impossible scenario, that all of the non-producing days
         occurred at the start of the month AND at the end of the month.
         Only one of these scenarios is possible (or none, if the
         non-producing days did not occur consecutively). However, this
         is necessary to determine the 'worst case' scenario -- i.e. the
         largest gap possible, given the available data.

         On the other hand, in calculating total months in each gap,
         this method includes only those months with exactly 0 days of
         production.

        :param shutin_as_producing: Whether to consider an explicit
         shut-in status code to be "producing".
        :param consider_production: (Optional) Whether to also require
         that quantity of production met the threshold in order for any
         stated days of production to be considered actually producing.
         That is, if the threshold is NOT met, the entire month will be
         considered as 0 days producing. (If this parameter is not
         specified, the default behavior is to consider production if
         the oil and/or gas production columns were configured. If those
         were not configured, then this will have no effect.)
        :param new_days_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         days. If not specified, that data will not be added.
        :param new_months_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         months. If not specified, that data will not be added.
        :return: A ```DataFrame``` showing the ```'total_months'``` and
         ```'total_days'``` in each gap.
        """
        df = self.prod_df

        running_days_vals = []
        running_months_vals = []
        days_counter = 0
        months_counter = 0
        gap_start_date = None
        previous_last_day = None
        gaps = []

        if consider_production is None:
            consider_production = self.is_configured_production

        for _, row in df.iterrows():
            first_day = row[self.date_col]
            days_in_month = get_days_in_month(first_day)
            last_day = last_day_of_month(first_day)
            days_producing = row[self.DAYS_PRODUCING]
            days_not_producing = row[self.DAYS_NOT_PRODUCING]
            is_shutin = False
            if self.is_configured_shutin:
                is_shutin = shutin_as_producing and row[self.ANY_SHUTIN]

            if is_shutin:
                # Affirmatively shut-in means consider as fully producing.
                days_producing = days_in_month
                days_not_producing = 0
            elif consider_production:
                if not row[self.ANY_ACTIVE]:
                    # Production falling short of the threshold, means we
                    # consider no days as producing.
                    days_producing = 0
                    days_not_producing = days_in_month

            # TODO: Figure out 'worst-case' scenario. This will entail
            #  partial months adding both forward and backward (two
            #  different scenarios).
            days_counter += days_not_producing
            if days_producing == 0:
                running_days_vals.append(days_counter)
                # No production all month.
                months_counter += 1
                if gap_start_date is None:
                    gap_start_date = first_day
            elif days_not_producing > 0:
                # Partial production.
                running_days_vals.append(days_counter)
                if gap_start_date is None:
                    # If starting a new gap, assume that all the non-producing
                    # days occurred at the end of the month.
                    gap_start_date = last_day - timedelta(days=days_not_producing - 1)
                else:
                    # If ending a gap, assume that all the non-producing days
                    # occurred at the start of the month.
                    gap_end_date = first_day + timedelta(days=days_not_producing - 1)
                    new_gap = (gap_start_date, gap_end_date)
                    gaps.append(new_gap)
                    # Because we're tracking a 'worst-case scenario', we want to
                    # add partial-month gaps as though they occurred BOTH at the
                    # beginning AND end of the month, so that they can be tacked
                    # onto subsequent months. Obviously, only one (or none) of
                    # these two scenarios can actually be true, but because we
                    # don't know which, we'll report it both ways.
                    months_counter = 0
                    days_counter = days_not_producing
                    gap_start_date = last_day - timedelta(days=days_not_producing - 1)
            else:
                # Full production all month.
                days_counter = 0
                months_counter = 0
                running_days_vals.append(days_counter)
                if gap_start_date is not None:
                    new_gap = (gap_start_date, previous_last_day)
                    gaps.append(new_gap)
                gap_start_date = None

            running_months_vals.append(months_counter)
            previous_last_day = last_day

        if gap_start_date is not None:
            # The final row was part of a gap.
            new_gap = (gap_start_date, previous_last_day)
            gaps.append(new_gap)

        # Add the columns, if requested
        if new_days_col is not None:
            df[new_days_col] = running_days_vals
        if new_months_col is not None:
            df[new_months_col] = running_months_vals
        return self._time_ranges_to_dataframe(gaps)

    def periods_of_shutin(
            self,
            consider_production: bool = None,
            new_days_col: str = None,
            new_months_col: str = None,
    ):
        """
        Find the periods during which at least one well is explicitly
        shut-in. With the optional parameter ```consider_production```,
        any oil/gas production that meets the configured threshold will
        render a shut-in status code null (i.e. with sufficient
        production in a given month, that month will not be considered
        shut-in, regardless of its status code).

        IMPORTANT: This method considers production on a monthly basis,
         so any production that meets the threshold is considered to
         have occurred across the entire month. Thus, in a theoretical
         January when all the production actually occurred only on first
         day of the month (and on no other days), there would NOT be
         considered any gap -- even though the well(s) was technically
         NOT producing for 30 days.

        :param consider_production: Whether to consider production at or
         beyond the configured threshold to override an explicit shut-in
         status code.
        :param new_days_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         days. If not specified, that data will not be added.
        :param new_months_col: (Optional) The header to add to the
         production ```DataFrame``` at ```.prod_df``` for the running
         months. If not specified, that data will not be added.
        :return: A ```DataFrame``` showing the ```'total_months'``` and
         ```'total_days'``` in each shut-in time period.
        """
        if consider_production is None:
            consider_production = self.is_configured_production
        df = self.prod_df

        running_days_vals = []
        running_months_vals = []
        days_counter = 0
        months_counter = 0
        period_start_date = None
        previous_last_day = None
        periods = []

        for _, row in df.iterrows():
            first_day = row[self.date_col]
            days_in_month = get_days_in_month(first_day)
            last_day = last_day_of_month(first_day)
            is_producing = False
            if consider_production:
                is_producing = row[self.ANY_ACTIVE]
            is_shutin = row[self.ANY_SHUTIN]

            if is_shutin and not is_producing:
                days_counter += days_in_month
                months_counter += 1
                if period_start_date is None:
                    period_start_date = first_day
            else:
                if period_start_date is not None:
                    new_period = (period_start_date, previous_last_day)
                    periods.append(new_period)
                days_counter = 0
                months_counter = 0
                period_start_date = None
            running_days_vals.append(days_counter)
            running_months_vals.append(months_counter)
            previous_last_day = last_day

        if period_start_date is not None:
            # The final row was part of a matching time period.
            new_period = (period_start_date, previous_last_day)
            periods.append(new_period)

        # Add the columns, if requested
        if new_days_col is not None:
            df[new_days_col] = running_days_vals
        if new_months_col is not None:
            df[new_months_col] = running_months_vals
        return self._time_ranges_to_dataframe(periods)

    @staticmethod
    def _time_ranges_to_dataframe(time_ranges: list) -> pd.DataFrame:
        """
        INTERNAL USE:
        Convert a list of start/end dates into a ```DataFrame``` of the
        total number of calendar months and days within each date pair.
        :param time_ranges: A list of 2 ```datetime``` objects
         representing the start and end dates of each time period.
        :return: A ```DataFrame``` showing the ```'total_months'``` and
         ```'total_days'``` within each date range.
        """
        periods = pd.DataFrame({
            "start_date": [x[0] for x in time_ranges],
            "end_date": [x[1] for x in time_ranges]
        })
        total_months = []
        total_days = []
        if len(periods) > 0:
            # Summarize the total months and days for the gaps dataframe
            total_months = (
                    (periods["end_date"].dt.year - periods["start_date"].dt.year) * 12
                    + (periods["end_date"].dt.month - periods["start_date"].dt.month) + 1
            )
            total_days = (periods["end_date"] - periods["start_date"]).dt.days + 1
        periods["total_months"] = total_months
        periods["total_days"] = total_days
        return periods

    @staticmethod
    def output_gaps_as_string(gaps_df, header='Gaps:', threshold_days=0) -> str:
        """
        Clean up the contents of a ```DataFrame``` that was returned by
        a returned by a gap-determining method. Output as a single
        string, with the specified header, and limited to those periods
        that are at least as long as the specified number of
        ```threshold_days```.
        :param gaps_df: A ```DataFrame``` that was output by a method
         that determines gaps.
        :param header: The header to write before specifying the gaps.
         (Defaults to ```'Gaps:'```.)
        :param threshold_days: The minimum number of days for a gap to
         include it in the output string. (Defaults to ```0``` -- i.e.
         report gaps of all sizes.)
        :return: A single string of the gap sizes and dates.
        """
        lines = []
        max_gap_num_days = 0
        max_gap_dates = []
        for _, row in gaps_df.iterrows():
            total_days = row['total_days']
            date_range = (
                f"{row['start_date'].isoformat()[:10]} "
                f"-- {row['end_date'].isoformat()[:10]}"
            )
            # Keep track of the biggest gap.
            if total_days == max_gap_num_days:
                max_gap_dates.append(f" >> {date_range}")
            elif total_days > max_gap_num_days:
                max_gap_num_days = total_days
                max_gap_dates = [f" >> {date_range}"]

            # Report all gaps that meet the threshold.
            if total_days >= threshold_days:
                s = f" -- {total_days} days " \
                    f"({row['total_months']} calendar months)"
                s = s.ljust(36, ' ')
                s = f"{s}::  {date_range}"
                lines.append(s)
        if len(lines) == 0:
            lines = [' -- None that meet the threshold.']
        lines_joined = '\n'.join(lines)
        dates_joined = '\n'.join(max_gap_dates)
        output = (
            f"{header}\n"
            f"[[Biggest: {max_gap_num_days} days]]\n"
            f"{dates_joined}\n"
            f"[[All those that are at least {threshold_days} days in length]]\n"
            f"{lines_joined}"
        )
        return output

    def generate_graph(
            self,
            gaps_df: pd.DataFrame,
            fp,
            include_production: bool = None,
            threshold_days: int = 0
    ):
        """
        Generate and save a simple graph of production, highlighting the
        gaps.

        :param gaps_df: A
        :param fp: The filepath at which to save the graph.
        :param include_production: (Optional) Whether to also project
         the quantity of production onto the graph. (If this parameter
         is not specified, the default behavior is to project production
         if the oil and/or gas production columns were configured. If
         those were not configured, then this will have no effect.)
        :param threshold_days: The minimum number of days for a gap to
         highlight it on the graph. (Defaults to ```0``` -- i.e.
         highlight gaps of all sizes.)
        :return: None. (Saves graph to the specified filepath.)
        """
        prod_df = self.prod_df
        if include_production is None:
            include_production = self.is_configured_production

        fig, ax = plt.subplots()
        gas_color = 'green'
        oil_color = 'blue'
        highlight_color = 'red'
        gas_al = 1.0
        oil_al = 0.6

        title = (
            f"Total Verified Production "
            f"{self.first_month.isoformat()[:7]} "
            f"to {self.last_month.isoformat()[:7]}"
        )
        ax.set_title(title)
        y_vals = prod_df[self.date_col]
        gas_axis = ax
        oil_axis = ax.twinx()

        if include_production:
            if self.gas_prod_col is not None:
                gas_axis.plot(
                    y_vals, prod_df[self.gas_prod_col], color=gas_color, alpha=gas_al)
                gas_axis.set_ylabel('Gas produced (MCF)', color=gas_color)
            if self.oil_prod_col is not None:
                oil_axis.plot(
                    y_vals, prod_df[self.oil_prod_col], color=oil_color, alpha=oil_al)
                oil_axis.set_ylabel('Oil produced (BBLs)', color=oil_color)
        else:
            # Plot null data, just to get dates onto the plot.
            gas_axis.plot(y_vals, [0 for _ in y_vals], color=gas_color, alpha=0)
        ax.set_xlabel('Time (year)')

        gaps_label = "Production Gaps"
        for _, row in gaps_df.iterrows():
            start_date = row["start_date"]
            end_date = row["end_date"]
            d1 = date2num(datetime(start_date.year, start_date.month, start_date.day))
            d2 = date2num(datetime(end_date.year, end_date.month, end_date.day))
            if d2 - d1 + 1 < threshold_days:
                continue
            ax.axvspan(d1, d2, color=highlight_color, alpha=0.3, label=gaps_label)
            gaps_label = None
        ax.legend()
        fig.savefig(fp)
        return None


def first_day_of_month(dt: datetime) -> datetime:
    """
    Get the date of the first day of the month from the ```datetime```.
    """
    return datetime(dt.year, dt.month, 1)


def last_day_of_month(dt):
    """
    Get the date of the last day of the month from the ```datetime```.
    """
    last_day = get_days_in_month(dt)
    return datetime(dt.year, dt.month, last_day)


def get_days_in_month(dt) -> int:
    """
    From a ```datetime``` object, get the total number of days in a
    given calendar month.

    :param dt: A ```datetime``` object.
    :return: The number of days in the month.
    """
    _, last_day = monthrange(dt.year, dt.month)
    return last_day


__all__ = ['ProductionAnalyzer']
