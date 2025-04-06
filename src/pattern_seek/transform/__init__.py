"""
transform - File transformation functionality

This package provides functionality for transforming structured files (CSV, Excel)
by querying and filtering data based on text matching. It supports multiple file formats,
and provides options for displaying or saving the filtered results.

Main functions:
- transform_csv: Search and filter CSV files
- transform_excel: Search and filter Excel files
- print_csv_matches: Display CSV matches in tabular format
- print_excel_matches: Display Excel matches in tabular format
- save_csv_matches: Save CSV matches to a new file
- save_excel_matches: Save Excel matches to a new file

This package is designed to be extended with additional file formats in the future.
"""

# CSV transform functionality
from .csv_transform import transform_csv

# Excel transform functionality
from .excel_transform import transform_excel, get_excel_sheet_names

# Output formatting and saving
from .output import (
    print_csv_matches,
    print_excel_matches,
    save_csv_matches,
    save_excel_matches,
    print_transform_summary
)

# Import helper functions for direct use
from .common import is_match, match_row

__all__ = [
    "transform_csv",
    "transform_excel", 
    "print_csv_matches",
    "print_excel_matches", 
    "save_csv_matches",
    "save_excel_matches",
    "print_transform_summary",
    "get_excel_sheet_names",
    "is_match",
    "match_row"
]