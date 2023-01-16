
# Sample Script

[This command-line script](cogcc_analyzer.py) pulls production records
from Colorado's COGCC website for any number of user-specified wells.

The results shown below are generated as follows -- pulling records for
the four specified API numbers<sup>†</sup>, and saving the results to
a directory at `./sample analysis results`:

```
py cogcc_analyzer.py 05-001-07727,05-001-07729,05-123-08053,05-123-09456 -d "./sample analysis results"
```

<sup>†</sup> *Every well has a unique "API number" (e.g.,
`05-001-07727`). The four API numbers above were chosen arbitrarily --
but in theory, these might be the four wells that are relevant for
determining whether a given oil and gas lease has expired.*


After downloading the records for all of the requested wells, the script
checks them for:

1. periods when there is no reported oil or gas production from any of
    the wells (and *__not__* considering shut-in wells to be producing). 

2. periods when there is no oil or gas production from any of the wells
    (but considering shut-in wells to be producing, which many leases do).

3. periods when there are no wells producing, but there is at least one
    well shut-in (i.e. still capable of producing, but temporarily
    "turned off".)


The script then generates
[a text report](sample%20analysis%20results/production%20analysis.txt)
that reads as follows (as generated on January 16, 2023):

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

And finally, it generates a simple graph of total production from all
the wells examined, highlighting those periods when no wells were
producing, regardless of shut-in status (i.e. using the gaps identified
in analysis #1 above).

![gaps_graph](sample%20analysis%20results/gaps_graph.png)
