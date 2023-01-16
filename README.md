# Oil & Gas Production Analyzer

A Python package for analyzing monthly oil and/or gas production records
that are provided by various state agencies, such as:

* [__Colorado__ Oil and Gas Conservation Commission](https://cogcc.state.co.us/#/home)

* [__Montana__ Board of Oil and Gas Conservation](http://dnrc.mt.gov/divisions/board-of-oil-and-gas-conservation/)

* [__North Dakota__ Department of Mineral Resources](https://www.dmr.nd.gov/oilgas/)

* [__Wyoming__ Oil and Gas Conservation Commission](https://wogcc.wyo.gov/)

(And agencies in other oil/gas-producing states.)

The production records provided by the state agencies typically include
the following data for each well:

* Quantity of oil produced each month (typically measured in barrels, or "BBLs")
* Quantity of gas produced each month (typically measured in thousand-cubic-feet, or "MCF")
* On how many days substances were produced from the well during each month
* The well's "status code" for a given month (e.g., shut-in, producing, etc.)

This package analyzes the records for one or more wells to look for
periods of time when there is no production in any of the examined wells,
and/or when the status code for the well(s) is "shut-in" (i.e. temporarily
turned off but still capable of producing).



## Why?

An "oil and gas lease" is a contract between a landowner and an oil company
that lays out the terms for the company to drill wells on the land, the
royalties they must pay to the landowner, etc.

A typical lease is negotiated to last a specific period of time (e.g., 1 year,
5 years, whatever gets negotiated) -- __and then to continue indefinitely,
for as long as oil and/or gas are produced from one or more wells on the
leased lands.__
Without consistent production, the lease will automatically terminate.
The lease will often specify just how consistent the production must be
-- commonly allowing up to 90 consecutive days before expiration.
It might also specify the *quantity* of oil or gas to be produced in order
to extend the lease indefinitely. If sufficient production resumes soon
enough, the termination timer is reset to 90 days (or whatever was
negotiated).

However, it is not always obvious to either party when production has
ceased and a lease has terminated -- especially when there are many wells
to check, multiple leases to keep track of, and decades have passed.
(When a lease termination isn't noticed, the company may need to negotiate
some sort of resolution or face litigation, if production is resumed late
or new wells are drilled without a valid lease in place -- and those risks
and penalties may compound as time goes on.)

This tool quickly analyzes the production records for one or more wells
to look for any periods of time when there might not be sufficient
production, during which a lease might have terminated.


## Configuring by State

Currently, there are preset configurations for use in Colorado, Montana,
North Dakota, and Wyoming (the states where I do most of my consulting).

```
from production_analyzer import ProductionAnalyzer
from production_analyzer.config import load_config_preset

colorado_cfg = load_config_preset(state='CO')
analyzer = ProductionAnalyzer.from_config(some_dataframe, config=colorado_cfg)

# etc.
```

But it can also be manually configured for whatever headers, etc. are
put out by other states:

```
from production_analyzer import ProductionAnalyzer

analyzer = ProductionAnalyzer(
    some_dataframe,
    date_col='First of Month',
    oil_prod_col='Oil Produced',
    gas_prod_col='Gas Produced',
    days_produced_col='Days Produced',
    status_col='Well Status',
    shutin_codes=['SI'],
)

# etc.
```


## Sample output

Check out the [sample script](sample/sample_readme.md), which generated
a report that looks like this:

```
A production analysis report.

For records for the following dates:
 >> First month: 1999-01-01
 >> Last month: 2021-09-01

Considering the following wells:
 >> 05-001-07727
 >> 05-001-07729 (no records)
 >> 05-123-08053
 >> 05-123-09456

Gaps in Production (Shut-in does NOT count as production)
---- Biggest: 214 days ----
 >> 2021-03-01 : 2021-09-30
---- All those that are at least 0 days in length. ----
 >> 61 days (2 calendar months)    2002-05-01 : 2002-06-30
 >> 30 days (1 calendar months)    2002-09-01 : 2002-09-30
 >> 29 days (1 calendar months)    2016-02-01 : 2016-02-29
 >> 30 days (1 calendar months)    2016-06-01 : 2016-06-30
 >> 214 days (7 calendar months)   2021-03-01 : 2021-09-30

Gaps in Production (Shut-in DOES count as production)
---- Biggest: 0 days ----
 >> n/a
---- All those that are at least 0 days in length. ----
 >> None that meet the threshold.

Shut-In Periods
---- Biggest: 214 days ----
 >> 2021-03-01 : 2021-09-30
---- All those that are at least 0 days in length. ----
 >> 61 days (2 calendar months)    2002-05-01 : 2002-06-30
 >> 30 days (1 calendar months)    2002-09-01 : 2002-09-30
 >> 29 days (1 calendar months)    2016-02-01 : 2016-02-29
 >> 30 days (1 calendar months)    2016-06-01 : 2016-06-30
 >> 214 days (7 calendar months)   2021-03-01 : 2021-09-30
```

...and a graph that looks like this, highlighting in red the periods
during which no production occurred in any of the wells:

![gaps_graph](sample/sample%20analysis%20results/gaps_graph.png)
