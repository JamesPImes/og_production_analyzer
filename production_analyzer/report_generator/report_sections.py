
"""
The component sections for a report.
"""

from datetime import datetime

import pandas as pd

from .style import Style


class ReportSection:
    """
    Parent class for all report sections. May contain header, subheader,
    and/or footer, as well as the style, but does not have any
    meaningful content beyond that. (Add meaningful content in a child
    class.)
    """
    def __init__(
            self,
            header: str = None,
            subheader: str = None,
            footer: str = None,
            style: Style = None):
        self.header = header
        self.subheader = subheader
        self.footer = footer
        if style is None:
            style = Style()
        self.style = style

    def apply_header(self, s):
        """Apply configured header formatting to a string ```s```."""
        return self.style.header_format.format(s)

    def apply_subheader(self, s):
        """Apply configured subheader formatting to a string ```s```."""
        return self.style.subheader_format.format(s)

    def apply_footer(self, s) -> str:
        """Apply configured footer formatting to a string ```s```."""
        return self.style.footer_format.format(s)

    def apply_date(self, dt) -> str:
        """Apply configured formatting to a ```datetime```."""
        return dt.strftime(self.style.date_format)

    def join_date_range(self, d1: datetime, d2: datetime) -> str:
        """
        Convert two ```datetime``` objects to strings (in the format
        configured in ```.style```) and join them into a single string,
        delimited as configured in the ```.style```).
        """
        return self.style.date_range_delimiter.join((
            self.apply_date(d1),
            self.apply_date(d2)
        ))

    def apply_lineitem(self, s1: str, s2: str = None):
        """
        Apply the ```Style``` formatting to this line item. The input
        may optionally be in two parts. If so, ```s1``` will be
        left-justified (after adding the bullet) according to the
        configured style, and ```s2``` will be added to the right.
        """
        output_str = self.style.lineitem_bullet_format.format(s1)
        if s2 is not None:
            output_str = output_str.ljust(self.style.lineitem_justify, ' ')
            output_str = f"{output_str}{s2}"
        return output_str
    
    def add_header_and_footer(self, s: str) -> str:
        """
        If ```.header```, ```.subheader```, and/or ```.footer``` were
        configured, add them around the string ```s```.
        """
        components = []
        if self.header is not None:
            header = self.apply_header(self.header)
            components.append(header)
        if self.subheader is not None:
            subheader = self.apply_subheader(self.subheader)
            components.append(subheader)
        components.append(s)
        if self.footer is not None:
            footer = self.apply_footer(self.footer)
            components.append(footer)
        return '\n'.join(components)

    def apply_bookend_linebreaks(self, s: str) -> str:
        """
        Apply configured number of linebreaks before and after a string.
        """
        return ''.join((
            '\n' * self.style.leading_linebreaks,
            s,
            '\n' * self.style.trailing_linebreaks
        ))

    def get_body(self) -> str:
        """
        Get the body of this report section (excluding header,
        subheader, and footer).
        (To be overridden in child classes.)
        """
        return ''

    def output_string(self) -> str:
        """
        Get the compiled string for this report section.
        """
        body = self.get_body()
        output = self.add_header_and_footer(body)
        output = self.apply_bookend_linebreaks(output)
        return output


class TextBlockSection(ReportSection):
    """
    A report section that contains a simple text block.
    """
    def __init__(
            self,
            text: str,
            header: str = None,
            subheader: str = None,
            footer: str = None,
            style: Style = None
    ):
        super().__init__(
            header=header, subheader=subheader, footer=footer, style=style)
        self.text = text

    def get_body(self):
        return self.text


class ProductionDatesSection(ReportSection):
    """
    A report section for the earliest and latest reported production.
    """
    def __init__(
            self,
            production_df: pd.DataFrame,
            date_col: str,
            header: str = None,
            subheader: str = None,
            footer: str = None,
            include_earliest_prod: bool = True,
            include_latest_prod: bool = True,
            style: Style = None,
    ):
        super().__init__(
            header=header, subheader=subheader, footer=footer, style=style)
        self.production_df = production_df
        self.date_col = date_col
        self.include_earliest_prod = include_earliest_prod
        self.include_latest_prod = include_latest_prod

    def get_body(self) -> str:
        components = []
        df = self.production_df
        if self.include_earliest_prod:
            earliest = df[self.date_col].min()
            new_line = f"First month: {self.apply_date(earliest)}"
            new_line = self.apply_lineitem(new_line)
            components.append(new_line)
        if self.include_latest_prod:
            latest = df[self.date_col].max()
            new_line = f"Last month: {self.apply_date(latest)}"
            new_line = self.apply_lineitem(new_line)
            components.append(new_line)
        return '\n'.join(components)


class DateRangeSection(ReportSection):
    def __init__(
            self,
            date_range_df: pd.DataFrame,
            header: str = None,
            subheader: str = None,
            footer: str = None,
            threshold_days: int = 0,
            include_max: bool = True,
            style: Style = None,
    ):
        super().__init__(
            header=header, subheader=subheader, footer=footer, style=style)
        self.date_range_df = date_range_df
        self.threshold_days = threshold_days
        self.include_max = include_max

    def get_body(self) -> str:
        df = self.date_range_df
        biggest_num_days = 0
        biggest_dates_lines = []
        lines = []
        for _, row in df.iterrows():
            total_days = row['total_days']
            calendar_months = row['total_months']
            date_range = self.join_date_range(row['start_date'], row['end_date'])
            # Keep track of the biggest gap.
            date_rge_line_item = self.apply_lineitem(date_range)
            if total_days == biggest_num_days:
                line_item = self.apply_lineitem(date_rge_line_item)
                biggest_dates_lines.append(line_item)
            elif total_days > biggest_num_days:
                biggest_num_days = total_days
                biggest_dates_lines = [date_rge_line_item]

            # Report all gaps that meet the threshold.
            if total_days >= self.threshold_days:
                days_months = f"{total_days} days ({calendar_months} calendar months)"
                new_line = self.apply_lineitem(days_months, date_range)
                lines.append(new_line)

        components = []
        if not biggest_dates_lines:
            new_line = self.apply_lineitem('n/a')
            biggest_dates_lines = [new_line]
        if self.include_max:
            biggest = '\n'.join((
                self.apply_subheader(f"Biggest: {biggest_num_days} days"),
                '\n'.join(biggest_dates_lines),
            ))
            components.append(biggest)
        all_subheader = self.apply_subheader(
            f"All those that are at least {self.threshold_days} days in length.")
        if len(lines) == 0:
            new_line = self.apply_lineitem('None that meet the threshold.')
            lines = [new_line]
        components.append(all_subheader)
        components.append('\n'.join(lines))

        return '\n'.join(components)


class MaterialsReviewedSection(ReportSection):
    """
    A report section for displaying the materials that were reviewed.
    """
    def __init__(
            self,
            materials: list,
            header: str = None,
            footer: str = None,
            style: Style = None
    ):
        """
        :param materials: A list of strings representing the materials
         that were reviewed. (Will be converted to line items in the
         report.)
        """
        super().__init__(header=header, footer=footer, style=style)
        self.materials = materials

    def get_body(self):
        components = [self.apply_lineitem(m) for m in self.materials]
        return '\n'.join(components)


__all__ = [
    'ReportSection',
    'TextBlockSection',
    'ProductionDatesSection',
    'DateRangeSection',
    'MaterialsReviewedSection',
]
