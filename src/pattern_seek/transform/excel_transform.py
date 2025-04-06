"""
excel_transform.py - Excel file transformation functionality

This module provides functionality for transforming Excel files (XLSX, XLS) by
searching and filtering cells based on query criteria. It supports:
- Sheet-specific searches
- Column-specific searches
- Case sensitivity and whole-word matching
- Display of matched results in a formatted table
- Saving filtered data to a new Excel file

The module uses pandas and openpyxl to handle Excel files of various formats
and versions. It's designed to work with the pattern-seek output system.
"""

import pandas as pd
from typing import Dict, List, Optional, Union, Set, Tuple
from pathlib import Path

from .common import match_rows

def _process_sheet(
    df: pd.DataFrame,
    sheet_name: str,
    query: str,
    column: Optional[str] = None,
    case_sensitive: bool = False,
    matchword: bool = False,
) -> Dict:
    """
    Process a single Excel sheet, finding rows that match the query criteria.

    Args:
        df (pd.DataFrame): Pandas DataFrame containing the sheet data
        sheet_name (str): Name of the sheet being processed
        query (str): The text to search for
        column (Optional[str]): If provided, only search this specific column
        case_sensitive (bool): Whether the search should respect letter casing
        matchword (bool): Whether to match whole words only
        
    Returns:
        Dict: Dictionary containing sheet name, header, and matches
        
    Raises:
        ValueError: If a specified column doesn't exist in the sheet
    """
    result = {
        "name": sheet_name,
        "header": [],
        "matches": []
    }

    # Handle empty sheets
    if df.empty:
        return result
    
    # Convert column names to strings to ensure compatibility
    df.columns = df.columns.astype(str)

    # Get headers (Column names)
    header = list(df.columns)
    result["header"] = header

    # Validate column if specified
    if column and column not in header:
        raise ValueError(f"Column '{column}' not found in sheet '{sheet_name}'. Available columns: {', '.join(header)}")
    
    # Convert DataFrame to list of dictionaries for consistent processing
    rows = df.to_dict(orient='records')

    # Use the match_rows helper to find matching rows
    matches = match_rows(rows, query, column, case_sensitive, matchword)
    result["matches"] = matches

    return result


def transform_excel(
        file_path: str,
        query: str,
        sheet: Optional[str] = None,
        column: Optional[str] = None,
        case_sensitive: bool = False,
        matchword: bool = False,
        save: bool = False,
) -> Dict:
    """
    Searches an Excel file for cells where the query string appears in one or more cells.

    Args:
        file_path (str): Path to the Excel file (.xlsx, .xls, etc.).
        query (str): The text to search for in the file.
        sheet (Optional[str]): If provided, only search this specific sheet.
                               Otherwise, search all sheets.
        column (Optional[str]): If provided, only search this specific column.
        case_sensitive (bool): Whether the search should respect letter casing.
        matchword (bool): Whether to match whole words only.
        save (bool): If True, save the matching rows to a new Excel file.

    Returns:
        Dict: A dictionary containing:
            - "file": Original file path
            - "sheets": List of dictionaries with sheet data and matches
            If save=True, returns an empty dict after saving results to file.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the specified sheet or column doesn't exist
        pd.errors.EmptyDataError: If the Excel file has no data
        Exception: For other pandas/openpyxl errors
    """
    # Convert Path object for better path handling
    path = Path(file_path)

    # Validate inputs
    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")
    
    if not query:
        raise ValueError("Search query cannot be empty.")
    
    results = {"file": str(path), "sheets": []}

    try:
        # Get Excel file info to validate sheet name if provided
        xlsx_info = pd.ExcelFile(path)
        available_sheets = xlsx_info.sheet_names

        if not available_sheets:
            raise ValueError(f"Excel file {path} contains no sheets.")
        
        # Determine which sheets to process
        sheets_to_process = [sheet] if sheet else available_sheets

        # Validate specified sheet exists
        if sheet and sheet not in available_sheets:
            raise ValueError(f"Sheet '{sheet}' not found in Excel file. Available sheets: {', '.join(available_sheets)}")
        
        # Process each selected sheet
        for sheet_name in sheets_to_process:
            # Read the sheet with pandas
            df = pd.read_excel(path, sheet_name=sheet_name)

            # Process the sheet
            sheet_result = _process_sheet(
                df,
                sheet_name,
                query,
                column,
                case_sensitive,
                matchword
            )

            # Add to results
            results["sheets"].append(sheet_result)

    except Exception as e:
        # Re-raise with more context
        error_type = type(e).__name__
        raise type(e)(f"Error processing Excel file: {file_path}: {error_type} - {str(e)}")
    
    # Handle saving results if requested
    if save:
        has_matches = any(len(sheet["matches"]) > 0 for sheet in results["sheets"])

        if not has_matches:
            print(f"No matches found in {file_path}. Nothing was saved.")
            return {}
        
        # Generate output filename
        save_path = path.parent / f"{path.stem}-transformed.xlsx"

        # Import here to avoid circular imports
        from .output import save_excel_matches

        # Save the matched rows to a new Excel file
        save_success = save_excel_matches(results, str(save_path))

        # Only print message if save was successful
        if save_success:
            print(f"\nSaved transformed results to {save_path}")
            
        return {}
    
    return results

def get_excel_sheet_names(file_path: str) -> List[str]:
    """
    Returns a list of sheet names in an Excel file.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        List[str]: List of sheet names
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid Excel file
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")
    
    try:
        xlsx_info = pd.ExcelFile(path)
        return xlsx_info.sheet_names
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")