
"""
Load JSON files of config data (column headers, etc.) for production
records of various states.

JSON files should contain the following fields:

{
  "file_exts": <list of file extensions that may be interpreted>,
  "header_row": <row number that contains the headers in the files>,
  "date_col": <column header for 'Date' (i.e. month)>,
  "oil_prod_col": <column header for quantity of oil production>,
  "gas_prod_col": <column header for quantity of gas production>,
  "days_produced_col":
     <column header for number of days of production in each month>,
  "status_col": <column header for well status>,
  "shutin_codes": <list of status codes that mean 'shut-in'>,
  "url": <url to the state agency website>,
  "prod_url_template": <template for the production URL -- see below.>,
  "prod_url_components":
     <list of components that need to be plugged into the url template>,
  "requires_credentials":
     <whether the production URL will require login credentials>
}

```prod_url_template``` should be a string to the URL for the production
records, with formatting brackets for the portion that will be filled in
with meaningful data for each unique well.

Correspondingly, ```'prod_url_components'``` is a list of strings that
explain what components should go in those brackets.

For example, Colorado uses a URL schema that uses the American Petroleum
Institute (API) unique number -- e.g., ```'05-001-12345'```.  In this,
```'001'``` encodes the county, and ```'12345'``` is a unique sequence
for a specific well within that county.

And to generate the meaningful URL for that well, we would take this
URL template:
  ```"https://cogcc.state.co.us/cogisdb/Facility/Production?api_county_code={0}&api_seq_num={1}"```

... and plug in ```'001'``` and ```'12345'``` respectively, thus:
  ```"https://cogcc.state.co.us/cogisdb/Facility/Production?api_county_code=001&api_seq_num=12345"```

Thus, these two fields are configured as follows in the JSON file for
Colorado:

  "prod_url_template": ```"https://cogcc.state.co.us/cogisdb/Facility/Production?api_county_code={0}&api_seq_num={1}"```
  "prod_url_components": ["API county code (3 digits)", "Unique API sequence (5 digits)"],

The user is responsible to provide the actual components. The
```'prod_url_components'``` field is intended only for reference.

Moreover, not all states expose such URL's to the public; and even if
they are exposed, scraping data from them may be against the Terms of
Service. Use such functionality at your own discretion and risk.
"""

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "state_configs"
CONFIG_FILENAME_TEMPLATE = "{0}_config.json"


def load_config_preset(state: str) -> dict:
    """
    Load config data for a preset state.

    :param state: The state to be loaded. (By default, takes the
     2-character abbreviation for each state. If ```CONFIG_DIR``` or
     ```CONFIG_FILENAME_TEMPLATE``` constants are modified, then
     ```state``` parameter would follow the custom filename schema.)
    :return: Dict containing the config data.
    """
    fp = CONFIG_DIR / CONFIG_FILENAME_TEMPLATE.format(state)
    try:
        with open(fp, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        raise ValueError(f"State {state!r} not pre-configured.")


def load_config_custom(fp) -> dict:
    """
    Load costum config data.
    :param fp: Path to a .json file containing config data.
    :return: Dict containing the config data.
    """
    with open(fp, 'r') as config_file:
        return json.load(config_file)


__all__ = [
    'CONFIG_DIR',
    'CONFIG_FILENAME_TEMPLATE',
    'load_config_preset',
    'load_config_custom',
]
