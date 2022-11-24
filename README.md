# Oil & Gas Production Analyzer

A Python package for analyzing monthly oil and/or gas production records
that are provided by various state agencies, such as:

* Colorado : [Colorado Oil and Gas
Conservation Commission](https://cogcc.state.co.us/#/home)

* North Dakota : [North Dakota Department of Mineral Resources](https://www.dmr.nd.gov/oilgas/)

* Wyoming : [Wyoming Oil and Gas
Conservation Commission](https://wogcc.wyo.gov/)

These agencies typically provide for each well production records for
each well, typically including many of the following fields:

* How many BBLs of oil produced each month
* How many MCF of gas produced each month
* On how many days the well produced each month
* The well's "status code" for a given month (e.g., shut-in, producing, etc.)

This package analyzes the records for one or more wells to look for
periods of time when there is no production in any of the examined wells,
and/or when the status code for the well(s) is "shut-in".
