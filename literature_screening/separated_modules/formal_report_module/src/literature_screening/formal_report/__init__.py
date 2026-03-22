"""Detached formal report helpers.

The preferred workflow is the concise simple-report pipeline, which produces
the detached module's default literature report style.
"""

from literature_screening.formal_report.simple_report import DEFAULT_SIMPLE_REPORT_FILENAME
from literature_screening.formal_report.simple_report import LEGACY_SIMPLE_REPORT_FILENAME
from literature_screening.formal_report.simple_report import SimplePaperNote
from literature_screening.formal_report.simple_report import generate_simple_report
from literature_screening.formal_report.simple_report import render_simple_report_markdown
from literature_screening.formal_report.reference_list import APA7_STYLE_URL
from literature_screening.formal_report.reference_list import GB_T_7714_STYLE_URL
from literature_screening.formal_report.reference_list import build_reference_list

__all__ = [
    "APA7_STYLE_URL",
    "DEFAULT_SIMPLE_REPORT_FILENAME",
    "GB_T_7714_STYLE_URL",
    "LEGACY_SIMPLE_REPORT_FILENAME",
    "SimplePaperNote",
    "build_reference_list",
    "generate_simple_report",
    "render_simple_report_markdown",
]
