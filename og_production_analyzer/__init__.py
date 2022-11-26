# Copyright (c) 2021-2022, James P. Imes. All rights reserved.

"""
A wrapper for pandas DataFrame for checking oil and/or gas production
records for gaps; and tools for generating reports.
"""

__version__ = '0.0.1'
__author__ = 'James P. Imes'
__email__ = 'jamesimes@gmail.com'
__website__ = 'github.com/jamespimes'

from .production_analyzer import ProductionAnalyzer, DataLoader
from .report_generator import ReportGenerator
from .report_generator import Style
from .report_generator import (
    ReportSection,
    TextBlockSection,
    ProductionDatesSection,
    DateRangeSection,
    MaterialsReviewedSection,
)
