
"""
A sample script for loading production data directly from the website
of the state reporting agency -- in this case, for Colorado (i.e. from
the COGCC's online records).
"""

import os
from pathlib import Path
from time import sleep

from production_analyzer import (
    ProductionAnalyzer,
    DataLoader,
    HTMLLoader
)
from production_analyzer.config import load_config_preset

SLEEP_SECONDS = 10


# Load preset headers, etc. for Colorado records.  (This pulls
# relevant pre-configured data from `config\state_configs\co_config.json`.)
config = load_config_preset(state='CO')

# Load DataFrames of production data directly from the COGCC website.

data_loader = DataLoader.from_config(config=config)
html_loader = HTMLLoader.from_config(config=config, auth=None)

# Where we'll save our data.
analysis_dir = Path(r"C:\Production_Research")
data_dir = analysis_dir / "production_data"
os.makedirs(data_dir, exist_ok=True)

# The API numbers for the wells we'll include in our research.
# (These wells were arbitrarily chosen.)
api_nums = ['05-001-07727', '05-001-08288', '05-123-08053', '05-123-09456']
api_success = {}

for api_num in api_nums:
    print(f"Collecting data records for well: {api_num}... ", end='')
    html_fp = data_dir / f"{api_num}_production_data_raw.html"
    csv_fp = data_dir / f"{api_num}_production_data.csv"

    # The template for the production URL was configured in `co_config.json`,
    # which was loaded into `config` with `load_config_preset()` above.
    # Note that the relevant URL in Colorado is built from only the second
    # and third components of each well's API number. (Other states do it
    # differently, or not at all.)
    url_components = api_num.split('-')
    url_components.pop(0)
    # Use those components to get the relevant URL for this well.
    url = html_loader.get_production_url(url_components)

    html = html_loader.get_html(url)
    # Save raw HTML to disk, in case we need it later.
    html_loader.save_html(html, fp=html_fp)

    # Extract the production data from the HTML.
    prod_df = html_loader.get_production_data_from_html(html)
    if prod_df is not None:
        # Add the dataframe to the data loader.
        api_success[api_num] = True
        data_loader.add_dataframe(prod_df, source_value=api_num)
        # Save this well's production data to csv, in case we need it later.
        html_loader.save_csv(prod_df, fp=csv_fp)
        print('Done. ', end='')
    else:
        api_success[api_num] = False
        print('No production records. ', end='')

    # Be kind to the COGCC's server.
    print(f"Sleeping {SLEEP_SECONDS} seconds.")
    sleep(SLEEP_SECONDS)


# Export a single DataFrame with all loaded production data.
total_prod_df = data_loader.output()
total_prod_df.to_csv(data_dir / f"combined_data.csv")


# Now that all the relevant data has been loaded, begin the analysis...
analyzer = ProductionAnalyzer.from_config(total_prod_df, config)

# etc.
