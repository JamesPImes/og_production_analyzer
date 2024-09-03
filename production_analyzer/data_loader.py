
"""
Helper classes for loading production data from various sources (.csv,
.xlsx, existing ``DataFrame`` objects, and directly from websites).
"""

import os
from pathlib import Path
from io import StringIO

import pandas as pd
import requests


class DataLoader:
    """
    Load production data from one or more .csv or .xlsx files, or
    incorporate any number of existing ``DataFrame``.

    Note: All data sources should have the same headers, etc.
    """
    def __init__(
            self,
            date_col: str,
            oil_prod_col: str = None,
            gas_prod_col: str = None,
            days_produced_col: str = None,
            status_col: str = None,
    ):
        """
        Load production data from one or more .csv or .xlsx files, or
        incorporate any number of existing ``DataFrame``.

        Note: All data sources should have the same headers, etc.

        :param date_col: The header of the date column in all of the
         data sources that will be added.
        """
        self.date_col = date_col
        self.oil_prod_col = oil_prod_col
        self.gas_prod_col = gas_prod_col
        self.days_produced_col = days_produced_col
        self.status_col = status_col
        self.dfs = []
        self.files_saved = []

    @classmethod
    def from_config(cls, config):
        """
        Get a new ``DataLoader`` from a config dict.

        :param config: A config dict, as loaded by ``config_loader``
         module.
        :return: A new ``DataLoader`` that incorporates the config
         data.
        """
        relevant_fields = [
            'date_col',
            'oil_prod_col',
            'gas_prod_col',
            'days_produced_col',
            'status_col',
        ]
        kw = {
            param: val for param, val in config.items()
            if param in relevant_fields
        }
        return cls(**kw)

    @property
    def configured_columns(self):
        """
        Get a list of column headers that have been configured for this
        ``DataLoader``.
        """
        possible = [
            self.date_col,
            self.oil_prod_col,
            self.gas_prod_col,
            self.days_produced_col,
            self.status_col,
        ]
        return [col for col in possible if col is not None]

    def add_csv(
            self,
            fp,
            header_row: int = 0,
            source_value: str = None,
            source_header='data_source'):
        """
        Add a .csv file.
        :param fp: The filepath of the .csv file to add.
        :param header_row: The row number (0-indexed) that contains
         headers in all of the .csv files to incorporate.
        :param source_value: (Optional) Specify where this data came
         from.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_value`` is specified.)
        :return: None.
        """
        df = pd.read_csv(fp, parse_dates=[self.date_col], header=header_row)
        if source_value is not None:
            df[source_header] = source_value
        self.dfs.append(df)
        return None

    def add_xlsx(
            self,
            fp,
            ws_names: list,
            header_row: int = 0,
            source_values: list = None,
            source_header='data_source'
    ) -> None:
        """
        Add one or more sheets from a single .xlsx file.
        :param fp: The filepath of the .xlsx file to add.
        :param ws_names: A list of sheet names to add. (Use ``None``
         to load all.)
        :param header_row: The row number (0-indexed) that contains
         headers in all of the sheets to incorporate.
        :param source_values: (Optional) Specify where this data came
         from. Pass a list (equal in length to the number of sheets to
         load) of strings to apply to each; or pass a single string to
         apply to all.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_value`` is specified.)
        :return: None.
        """
        if isinstance(ws_names, str):
            ws_names = [ws_names]
        dfs = pd.read_excel(
            fp,
            sheet_name=ws_names,
            header=header_row,
            parse_dates=[self.date_col])
        if source_values is None:
            pass
        elif isinstance(source_values, str):
            for i, df in enumerate(dfs.values()):
                df[source_header] = source_values
        else:
            for i, df in enumerate(dfs.values()):
                df[source_header] = source_values[i]
        self.dfs.extend(dfs.values())
        return None

    def add_dataframe(
            self,
            df: pd.DataFrame,
            source_value: str = None,
            source_header='data_source'
    ) -> None:
        """
        Add an existing ``DataFrame`` of production data.
        :param df: The ``DataFrame`` to add.
        :param source_value: (Optional) Specify where this data came
         from.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_value`` is specified.)
        :return: None.
        """
        if source_value is not None:
            df[source_header] = source_value
        self.dfs.append(df)
        return None

    def add_multiple_csv(
            self,
            fps: list,
            header_row: int = 0,
            source_values: list = None,
            source_header='data_source'
    ) -> None:
        """
        Add multiple .csv files.
        :param fps: A list of filepaths to the .csv files to add.
        :param header_row: The row number (0-indexed) that contains
         headers in all of the .csv files to incorporate.
        :param source_values: (Optional) A list of strings that specify
         each source of the data. If passed, the list should be equal in
         length to the list of files added, and in the same order.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_values`` is specified.)
        :return: None.
        """
        for i, fp in enumerate(fps):
            source = None
            if isinstance(source_values, list):
                source = source_values[i]
            elif source_values is not None:
                source = source_values
            self.add_csv(fp, header_row, source, source_header)
        return None

    def add_multiple_xlsx(
            self,
            fps: list,
            ws_names: list,
            header_row: int = 0,
            source_values: list = None,
            source_header='data_source'
    ) -> None:
        """
        Add multiple .xlsx files, all with the same sheet names.
        :param fps: A list of filepaths of the .xlsx files to add.
        :param ws_names: A list of sheet names to add. (Each sheet name
         must exist in every .xlsx file. Otherwise, use the
         ``.add_xlsx()`` method on each file.)
        :param header_row: The row number (0-indexed) that contains
         headers in all of the sheets to incorporate.
        :param source_values: (Optional) A list of strings that specify
         each source of the data. If passed, the list should be equal in
         length to the list of files added, and in the same order.
         (Note: If different data sources are needed for different
         sheets within each .xlsx file, use the ``.add_xlsx()``
         method on each file instead.)
        :param source_values: (Optional) Specify where this data came
         from. Pass a list (equal in length to the number of sheets to
         load) of strings to apply to each; or pass a single string to
         apply to all.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_value`` is specified.)
        :return: None.
        """
        for i, fp in enumerate(fps):
            source = None
            if isinstance(source_values, list):
                source = source_values[i]
            elif source_values is not None:
                source = source_values
            self.add_xlsx(fp, ws_names, header_row, source, source_header)
        return None

    def add_multiple_dfs(
            self,
            dfs: list,
            source_values: list = None,
            source_header='data_source'
    ) -> None:
        """
        Add multiple existing ``DataFrame`` of production data.
        :param dfs: A list of ``DataFrame``.
        :param source_values: (Optional) A list of strings that specify
         each source of the data. If passed, the list should be equal in
         length to the list of files added, and in the same order.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ``source_values`` is specified.)
        :return: None.
        """
        for i, df in enumerate(dfs):
            source = None
            if isinstance(source_values, list):
                source = source_values[i]
            elif source_values is not None:
                source = source_values
            df[source_header] = source
        self.dfs.extend(dfs)

    def output(self, empty_as_error=False) -> pd.DataFrame:
        """
        Get the concatenated ``DataFrame`` for all data sources that
        have been loaded so far.
        :param empty_as_error: (Optional) Specify ``True`` to raise
         a ``ValueError`` if no data has been successfully loaded.
        :return: A ``DataFrame`` of all data sources, with no grouping
         and without filling any empty values.
        """
        if self.dfs:
            return pd.concat(self.dfs, ignore_index=True)
        elif empty_as_error:
            raise ValueError('No data loaded.')
        else:
            return pd.DataFrame(data=[], columns=self.configured_columns)


class HTMLLoader:
    """
    A class to scrape production data from webpages that contain tabular
    monthly production data in HTML.
    """

    def __init__(
            self,
            prod_url_template: str,
            date_col: str,
            oil_prod_col: str = None,
            gas_prod_col: str = None,
            days_produced_col: str = None,
            status_col: str = None,
            auth=None,
    ):
        """
        A class to scrape production data from webpages that contain
        tabular monthly production data in HTML.

        The URL template should have formatting brackets
        ``prod_url_template`` should be a string to the URL for the
        production records, with formatting brackets for the portion
        that will be filled in with meaningful data for each unique
        well.

        For example, Colorado uses a URL schema as follows:
            ``"https://cogcc.state.co.us/cogisdb/Facility/Production?api_county_code={0}&api_seq_num={1}"``

        ... which uses portions of the API number for a given well
        (unique to each well) -- e.g., ``'05-001-12345'``.  In this,
        ``'001'`` encodes the county, and ``'12345'`` is a unique
        sequence for a specific well within that county.  These are
        plugged into ``{0}`` and ``{1}`` within an f-string, to
        generate the following URL:
          ``"https://cogcc.state.co.us/cogisdb/Facility/Production?api_county_code=001&api_seq_num=12345"``

        On the other hand, North Dakota uses a URL schema as follows:
          ``https://www.dmr.nd.gov/oilgas/feeservices/getwellprod.asp?filenumber={0}``

        ... where ``{0}`` would be filled with a unique, incrementing
        5-digit number that gets assigned to wells by the State of North
        Dakota itself.

        :param prod_url_template: The template for the URL to the page
         that will contain the data to scrape. (See above.)
        :param date_col: The column header for the ``datetime`` that
         represents its entire month (e.g., 1/1/2011 for January 2011).
        :param oil_prod_col: (Optional) The header for oil production.
        :param gas_prod_col: (Optional) The header for gas production.
        :param days_produced_col: The column header for the number of
         days that the well produced during this month.
        :param status_col: (Optional) The header for the column
         containing status codes.
        :param auth: (Optional) If needed, provide the appropriate
         ``requests.auth`` object for this state's website, such as:
         ``requests.auth.HTTPBasicAuth('user_name', 'password')``.
        """
        self.prod_url_template = prod_url_template
        self.date_col = date_col
        self.oil_prod_col = oil_prod_col
        self.gas_prod_col = gas_prod_col
        self.days_produced_col = days_produced_col
        self.status_col = status_col
        self.auth = auth
        self.dfs = []
        self.files_saved = []

    @classmethod
    def from_config(cls, config: dict, auth=None):
        """
        Get a new ``HTMLLoader`` from a config dict.

        :param config: A config dict, as loaded by ``config_loader``
         module.
        :param auth: (Optional) If needed, provide the appropriate
         ``requests.auth`` object for this state, such as:
         ``requests.auth.HTTPBasicAuth('user_name', 'password')``.
        :return: A new ``HTMLLoader`` that incorporates the config
         data.
        """
        relevant_fields = [
            'prod_url_template',
            'date_col',
            'oil_prod_col',
            'gas_prod_col',
            'days_produced_col',
            'status_col',
        ]
        kw = {
            param: val for param, val in config.items()
            if param in relevant_fields
        }
        return cls(**kw, auth=auth)

    @property
    def configured_columns(self):
        """
        Get a list of column headers that have been configured for this
        ``HTMLLoader``.
        """
        possible = [
            self.date_col,
            self.oil_prod_col,
            self.gas_prod_col,
            self.days_produced_col,
            self.status_col,
        ]
        return [col for col in possible if col is not None]

    def reset(self) -> None:
        """
        Reset the list of ``DataFrame`` objects in ``.dfs`` and the
        list of filepaths in ``.files_saved`` to new, empty lists.
        :return: None
        """
        self.dfs = []
        self.files_saved = []

    def get_html(self, url) -> str:
        """
        Get the HTML from the specified URL.

        :param url: The webpage to scrape.
        :return: The raw HTML text of the webpage.
        """
        r = requests.get(url=url, auth=self.auth)
        return r.text

    def save_html(self, txt, fp):
        """
        Save the HTML (``txt``) to the specified filepath (``fp``).

        .. warning::

            This will overwrite any file at ``fp`` without warning.
        """
        fp = Path(fp)
        os.makedirs(fp.parent, exist_ok=True)
        with open(fp, 'w') as f:
            f.write(txt)
        self.files_saved.append(fp)
        return None

    def save_csv(self, df, fp) -> None:
        """
        Save the production ``DataFrame`` (``df``) to .csv at the
        specified filepath ``fp``.

        .. warning::

            This will overwrite any file at ``fp`` without warning.
        """
        fp = Path(fp)
        os.makedirs(fp.parent, exist_ok=True)
        df.to_csv(fp)
        self.files_saved.append(fp)
        return None

    def get_production_url(self, url_components):
        """
        Get the production URL for a specific well.

        :param url_components: The components (i.e. a list of strings)
         to plug into the url to get the correct URL.  For example,
         the Colorado URL template takes two components, carved out of
         the unique API code for each well: specifically, the county
         code (3 digits) and a 5-digit sequence unique to each well.
        :return:
        """
        if self.prod_url_template is None:
            msg = 'URL not configured (may not be possible for this state).'
            raise RuntimeError(msg)
        return self.prod_url_template.format(*url_components)

    def get_production_data_from_html(self, html):
        """
        Extract the production table(s) found in the provided HTML text
        to a single ``DataFrame``. If not found return ``None``.

        :param html: The raw text of the HTML from which to pull
         production data table(s).
        :return: The production ``DataFrame``, if found. If not found,
         then ``None``.
        """
        matching_dfs = []
        target_cols = set(self.configured_columns)
        dfs = pd.read_html(StringIO(html))
        for df in dfs:
            df_cols = set(df.columns)
            if target_cols.issubset(df_cols):
                matching_dfs.append(df)
        if not matching_dfs:
            return None
        # Taking the final dataframe should work for most states. If we
        # encounter issues with this approach, will address at that time.
        output = matching_dfs[-1]
        output[self.date_col] = pd.to_datetime(output[self.date_col])
        self.dfs.append(output)
        return output
