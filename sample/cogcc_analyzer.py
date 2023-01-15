
"""
A sample script for loading production data directly from the website
of the state reporting agency -- in this case, for Colorado (i.e. from
the COGCC's online records) -- then analyzing that data, and generating
a sample report and graph.
"""

import os
from pathlib import Path
from time import sleep

from production_analyzer import (
    ProductionAnalyzer,
    DataLoader,
    HTMLLoader
)
from production_analyzer.report_generator import (
    ReportGenerator,
    TextBlockSection,
    ProductionDatesSection,
    DateRangeSection,
    MaterialsReviewedSection,
)
from production_analyzer.config import load_config_preset

SLEEP_SECONDS = 2


# Load preset headers, etc. for Colorado records.  (This pulls
# relevant pre-configured data from `config\state_configs\co_config.json`.)
config = load_config_preset(state='CO')

# Load DataFrames of production data directly from the COGCC website.

data_loader = DataLoader.from_config(config=config)
html_loader = HTMLLoader.from_config(config=config, auth=None)

# Where we'll save our data.
analysis_dir = Path(r"./sample analysis results")
data_dir = analysis_dir / "production records"
os.makedirs(data_dir, exist_ok=True)

# The API numbers for the wells we'll include in our research.
# (These wells were arbitrarily chosen.)
api_nums = ['05-001-07727', '05-001-08288', '05-123-08053', '05-123-09456']
api_success = {}

for i, api_num in enumerate(api_nums, start=1):
    print(f"Collecting production records for well: {api_num}... ", end='')
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
    if i < len(api_nums):
        print(f"Waiting {SLEEP_SECONDS} seconds.", end="")
        sleep(SLEEP_SECONDS)
    print("")

# Export a single DataFrame with all loaded production data.
total_prod_df = data_loader.output()
total_prod_df.to_csv(data_dir / f"combined_data.csv")
print("All data loaded.")


print("Analyzing... ", end="")
# Now that all the relevant data has been loaded, begin the analysis...
analyzer = ProductionAnalyzer.from_config(total_prod_df, config)

no_shutin_label = 'Gaps in Production (Shut-in does NOT count as production)'
analyzer.gaps_by_production_threshold(
    shutin_as_producing=False,
    analysis_id=no_shutin_label
)
yes_shutin_label = 'Gaps in Production (Shut-in DOES count as production)'
analyzer.gaps_by_production_threshold(
    shutin_as_producing=True,
    analysis_id=yes_shutin_label
)
shutin_only_label = 'Shut-In Periods'
analyzer.periods_of_shutin(analysis_id=shutin_only_label)
print("Done.")


# Generate a text report of our results.
print("Generating report... ", end="")

# Generate and store individual report sections, in the intended order
# they should appear in the report.
report_sections = []
textblock_1 = TextBlockSection(
    text='A sample report for production analysis.'
)
report_sections.append(textblock_1)

# Start / end dates of the records we reviewed.
records_daterange = ProductionDatesSection(
    production_df=analyzer.prod_df,
    date_col=analyzer.date_col,
    header='For records for the following dates:'
)
report_sections.append(records_daterange)

# What records were incorporated into our analysis.
materials_reviewed = MaterialsReviewedSection(
    materials=api_nums,
    header='Considering the following wells:',
)
report_sections.append(materials_reviewed)

# The results of each analysis (in this case: production gaps where shut-in was
# considered producing, and another where it was not considered producing).
for analysis_id, results_df in analyzer.results.items():
    date_range_section = DateRangeSection(
        date_range_df=results_df,
        header=analysis_id,
        include_max=True
    )
    report_sections.append(date_range_section)

# Use those individual report sections to write the full report.
report_generator = ReportGenerator(report_sections=report_sections)
# If we just need the report text as a string.
txt = report_generator.generate_report_text()
# If we want to write the text to a .txt file.
report_fp = analysis_dir / 'production analysis.txt'
report_text = report_generator.write_report_to_file(report_fp, mode='w')
print("Done.")


# Generate a basic graph of total oil production and gas production, and
# highlighting the gaps in production (using the results in which shut-in
# did not count as production).
print("Generating production graph... ", end="")
graph_fp = analysis_dir / 'gaps_graph.png'
analyzer.generate_graph(gaps_df=analyzer.results[no_shutin_label], fp=graph_fp)
print("Done.", end="\n\n")

print(report_text)
print("Analysis complete.")
input()
