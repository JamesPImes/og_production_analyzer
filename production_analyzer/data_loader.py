
import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import requests


class DataLoader:
    """
    Load production data from one or more .csv or .xlsx files, or
    incorporate any number of existing ```DataFrame```.

    Note: All data sources should have the same headers, etc.
    """
    def __init__(self, date_col: str, config: dict = None):
        """
        Load production data from one or more .csv or .xlsx files, or
        incorporate any number of existing ```DataFrame```.

        Note: All data sources should have the same headers, etc.

        :param date_col: The header of the date column in all of the
         data sources that will be added.
        """
        self.date_col = date_col
        self.dfs = []
        self.config = config
        self.files_saved = []

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
         ```source_value``` is specified.)
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
        :param ws_names: A list of sheet names to add. (Use ```None```
         to load all.)
        :param header_row: The row number (0-indexed) that contains
         headers in all of the sheets to incorporate.
        :param source_values: (Optional) Specify where this data came
         from. Pass a list (equal in length to the number of sheets to
         load) of strings to apply to each; or pass a single string to
         apply to all.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ```source_value``` is specified.)
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
        Add an existing ```DataFrame``` of production data.
        :param df: The ```DataFrame``` to add.
        :param source_value: (Optional) Specify where this data came
         from.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ```source_value``` is specified.)
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
         ```source_values``` is specified.)
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
         ```.add_xlsx()``` method on each file.)
        :param header_row: The row number (0-indexed) that contains
         headers in all of the sheets to incorporate.
        :param source_values: (Optional) A list of strings that specify
         each source of the data. If passed, the list should be equal in
         length to the list of files added, and in the same order.
         (Note: If different data sources are needed for different
         sheets within each .xlsx file, use the ```.add_xlsx()```
         method on each file instead.)
        :param source_values: (Optional) Specify where this data came
         from. Pass a list (equal in length to the number of sheets to
         load) of strings to apply to each; or pass a single string to
         apply to all.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ```source_value``` is specified.)
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
        Add multiple existing ```DataFrame``` of production data.
        :param dfs: A list of ```DataFrame```.
        :param source_values: (Optional) A list of strings that specify
         each source of the data. If passed, the list should be equal in
         length to the list of files added, and in the same order.
        :param source_header: (Optional) Specify the header for the
         column to add for specifying the data source. (Only relevant if
         ```source_values``` is specified.)
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

    def output(self) -> pd.DataFrame:
        """
        Get the concatenated ```DataFrame``` for all data sources that
        have been loaded so far.
        :return: A ```DataFrame``` of all data sources, with no grouping
         and without filling any empty values.
        """
        return pd.concat(self.dfs, ignore_index=True)
