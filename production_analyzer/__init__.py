# Copyright (c) 2021-2022, James P. Imes. All rights reserved.

"""
A wrapper for pandas DataFrame for checking oil and/or gas production
records for gaps; and tools for generating reports.
"""

from ._constants import (
    __version__,
    __author__,
    __email__,
    __website__,
    __version_date__,
    __license__,
)
from .production_analyzer import ProductionAnalyzer
from .data_loader import DataLoader, HTMLLoader
from .config import load_config_preset, load_config_custom
from .report_generator import ReportGenerator
from .report_generator import Style
from .report_generator import (
    ReportSection,
    TextBlockSection,
    ProductionDatesSection,
    DateRangeSection,
    MaterialsReviewedSection,
)
