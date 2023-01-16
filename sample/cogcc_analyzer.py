
r"""
A command line script for loading production data directly from the
website of the state reporting agency -- in this case, for Colorado
(i.e. from the COGCC's online records) -- then analyzing that data, and
generating a sample report and graph.

To use, run the script at command line, specifying the API numbers for
the desired wells (separated by comma, with no spaces). Optionally
specify the directory in which to store the results with the
``-d <directory>`` argument. If not specified, the results will be
stored in a new timestamped directory in the current directory.


Example (at command line, assuming we are currently in the same
directory as this script)::

    > py cogcc_analyzer.py 05-001-07727,05-123-09456 -d "C:\land\analysis"


For help (at command line)::

    > py cogcc_analyzer.py --help
"""

import os
import sys
import argparse
from datetime import datetime
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
CO_CONFIG = load_config_preset(state='CO')
DEFAULT_DIRECTORY = '.'


if __name__ == '__main__':
    current_dir = Path(os.path.dirname(sys.argv[0]))

    parser = argparse.ArgumentParser(
        prog="COGCC Production Analyzer",
        description="Pull records from the COGCC and analyze them for gaps",
    )
    parser.add_argument(
        'api_nums',
        help=('API Numbers for the desired wells, separated by comma, '
              'e.g. "05-001-07727,05-123-09456"')
    )
    parser.add_argument(
        '-d',
        '--directory',
        default=DEFAULT_DIRECTORY,
        help="Directory in which to write results",
    )
    args = vars(parser.parse_args())

    # Where we'll save our data.
    if args['directory'] == DEFAULT_DIRECTORY:
        subdir = "production_analysis_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_dir = Path(DEFAULT_DIRECTORY) / subdir
    else:
        analysis_dir = Path(args['directory'])
    data_dir = analysis_dir / "production records"
    os.makedirs(analysis_dir, exist_ok=True)

    # The API numbers for the wells we'll include in our research.
    api_nums_raw = args['api_nums']
    api_nums = [raw.strip() for raw in api_nums_raw.split(',')]
    api_success = {}


    # Load DataFrames of production data directly from the COGCC website.
    data_loader = DataLoader.from_config(config=CO_CONFIG)
    html_loader = HTMLLoader.from_config(config=CO_CONFIG, auth=None)
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


    # Now that all the relevant data has been loaded, begin the analysis...
    print("Analyzing... ", end="")
    analyzer = ProductionAnalyzer.from_config(total_prod_df, CO_CONFIG)

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
    textblock_1 = TextBlockSection(text='A production analysis report.')
    report_sections.append(textblock_1)

    # Start / end dates of the records we reviewed.
    records_daterange = ProductionDatesSection(
        production_df=analyzer.prod_df,
        date_col=analyzer.date_col,
        header='For records for the following dates:'
    )
    report_sections.append(records_daterange)

    # What records were incorporated into our analysis. Specify if there
    # no records for any given well.
    materials = [
        f"{n}{' (no records)' * (not api_success[n])}" for n in api_nums
    ]
    materials_reviewed = MaterialsReviewedSection(
        materials=materials,
        header='Considering the following wells:',
    )
    report_sections.append(materials_reviewed)

    # The results of each analysis we conducted. Note that the analysis_id used
    # for each analysis gets written as a header for each report subsection.
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
    print("Analysis complete. Results saved to:")
    print(os.path.abspath(analysis_dir))
