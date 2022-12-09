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

* Quantity oil produced each month (typically measured in BBLs)
* Quantity of gas produced each month (typically measured in MCF)
* On how many days substances were produced from the well during each month
* The well's "status code" for a given month (e.g., shut-in, producing, etc.)

This package analyzes the records for one or more wells to look for
periods of time when there is no production in any of the examined wells,
and/or when the status code for the well(s) is "shut-in" (i.e. temporarily
turned off but still capable of producing).



## Why?

An "oil and gas lease" is a contract between a landowner and oil company
that lays out the terms for the company to drill wells on the land, the
royalties they must pay to the landowner, and other terms.

A typical lease is negotiated for a specific period time (e.g., 1 year,
5 years, whatever gets negotiated) -- __and then indefinitely, for as long
as oil and/or gas are produced from one or more wells on the leased lands.__
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


## Note

Currently, there are preset configurations for use in Colorado, Montana,
North Dakota, and Wyoming (the states where I do most of my consulting).

```
from production_analyzer import ProductionAnalyzer
from production_analyzer import config_loader

colorado_cfg = config_loader.load_config_preset(state='CO')
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
