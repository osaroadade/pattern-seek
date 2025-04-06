"""
output.py - Formatted output and file saving functionality

This module is responsible for displaying and saving matched data from various
file formats (CSV, Excel, etc.) It handles:

1. Tabular display of matched rows with colorized formatting
2. Saving transformed data to new files
3. Status messages and progress indicators

The module uses colorama for terminal coloring and tabulate for formatted
table display, making the output readable and visually appealing.
"""

import csv
import os
from typing import Dict, List, Optional, Union, TextIO
import sys
from pathlib import Path

# Third-party imports
from colorama import Fore, Style, init
from tabulate import tabulate
import pandas as pd

# Initialize colorama for cross-platform terminal colors
init()


# Utility functions
def _ensure_output_dir(output_path: Union[str, Path]) -> Path:
    """
    Ensures the directory for the output file exists.
    
    Args:
        output_path (Union[str, Path]): Path where the output will be saved
        
    Returns:
        Path: Path object of the output path
        
    Raises:
        IOError: If directory creation fails
    """
    path = Path(output_path)
    output_dir = path.parent

    # Create directory if it doesn't exist and it's not the current directory
    if not output_dir.exists() and str(output_dir) != Path('.'):
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise IOError(f"Could not create directory {output_dir}: {str(e)}")
        
    return path

def _validate_result_dict(result: Dict, format_type: str) -> None:
    """
    alidates that a result dictionary has the expected structure.
    
    Args:
        result (Dict): The result dictionary to validate
        format_type (str): The expected format type ('csv' or 'excel')
        
    Raises:
        ValueError: If the result dictionary is missing required keys or has invalid structure
    """
    # Common validation
    if not isinstance(result, dict):
        raise ValueError(f"Invalid result: expected dictionary, got {type(result).__name__}")
    
    if "file" not in result:
        raise ValueError("Result dictionary must contain 'file' key")
    
    # Format-specific validation
    if format_type == "csv":
        if "header" not in result:
            raise ValueError("CSV result must contain 'header' key")
        if "matches" not in result:
            raise ValueError("CSV result must contain 'matches' key")
        if not isinstance(result["header"], list):
            raise ValueError(f"Invalid CSV result: 'header' must be a list, not {type(result['header']).__name__}")
        if not isinstance(result["matches"], list):
            raise ValueError(f"Invalid CSV result: 'matches' must be a list, not {type(result['matches']).__name__}")
        
    elif format_type == "excel":
        if "sheets" not in result:
            raise ValueError("Excel result must contain 'sheets' key")
        if not isinstance(result["sheets"], list):
            raise ValueError(f"Invalid Excel result: 'sheets' must be a list, not {type(result['sheets']).__name__}")
        
        # Validate each sheet
        for i, sheet in enumerate(result["sheets"]):
            if not isinstance(sheet, dict):
                raise ValueError(f"Invalid Excel result: sheet at index {i} must be a dictionary")
            if "name" not in sheet:
                raise ValueError(f"Invalid Excel result: sheet at index {i} missing 'name' key")
            if "header" not in sheet:
                raise ValueError(f"Invalid Excel result: sheet at index {i} missing 'header' key")
            if "matches" not in sheet:
                raise ValueError(f"Invalid Excel result: sheet at index {i} missing 'matches' key")
            
def _get_sheet_summary(sheets: List[Dict]) -> str:
    """
    Generates a summary of sheet names and match counts.
    
    Args:
        sheets (List[Dict]): List of sheet data dictionaries
        
    Returns:
        str: Formatted summary of sheet matches
    """
    sheet_info = []

    for sheet in sheets:
        name = sheet.get("name", "Unknown")
        match_count = len(sheet.get("matches", []))
        if match_count > 0:
            sheet_info.append(f"{Fore.MAGENTA}{name} ({match_count} matches){Style.RESET_ALL}")
    
    if not sheet_info:
        return f"{Fore.YELLOW}No matches found in any sheets.{Style.RESET_ALL}"
    
    return "\n".join(sheet_info)


# Display functions
def print_csv_matches(result: Dict) -> None:
    """
    Prints the matched rows from a CSV file in a tabular format.

    Args:
        result (Dict): The result dictionary containing:
                      - file: original file path
                      - header: list of column names
                      - matches: list of matched rows as dictionaries
    """
    # Validate result structure
    _validate_result_dict(result, "csv")

    file_path = result.get("file", "Unknown file")
    rows = result.get("matches", [])

    if not rows:
        print(f"{Fore.YELLOW}No matches found in {file_path}.{Style.RESET_ALL}")
        return
    
    # Display the filename
    print(f"\n{Fore.CYAN}{Style.BRIGHT}File: {file_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Found {len(rows)} matching rows{Style.RESET_ALL}")

    # Display the matching rows in a table format
    print(tabulate(rows, headers="keys", tablefmt="grid"))

def print_excel_matches(result: Dict) -> None:
    """
    Prints the matched rows from an Excel file in a tabular format,
    organized by sheet.

    Args:
        result (Dict): The result dictionary containing:
                      - file: original file path
                      - sheets: list of sheet data containing matches
    """
    # Validate result structure
    _validate_result_dict(result, "excel")

    file_path = result.get("file", "Unknown file")
    sheets = result.get("sheets", [])

    # Check if there are any matches across all sheets
    total_matches = sum(len(sheet.get("matches", [])) for sheet in sheets)

    if total_matches == 0:
        print(f"{Fore.YELLOW}No matches found in {file_path}.{Style.RESET_ALL}")
        return
    
    # Display the filename and summary
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Excel File: {file_path}{Style.RESET_ALL}")

    # Get sheet names with matches
    sheet_summary = _get_sheet_summary(sheets)
    print(f"{Fore.GREEN}Found {total_matches} matching rows in: {sheet_summary}{Style.RESET_ALL}")

    # Display matches for each sheet
    for sheet in sheets:
        sheet_name = sheet.get("name", "Unknown Sheet")
        matches = sheet.get("matches", [])
        
        if not matches:
            continue
        
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Sheet: {sheet_name} ({len(matches)} matches){Style.RESET_ALL}")
        print(tabulate(matches, headers="keys", tablefmt="grid"))


# Save functions
def save_csv_matches(result: Dict, output_file: str) -> None:
    """
    Saves the matched rows from a CSV file to a new CSV file.

    Args:
        result (Dict): The result dictionary containing file path, header, and matches.
        output_file (str): The path to the output CSV file.
        
    Raises:
        ValueError: If the result structure is invalid
        IOError: If there's an error writing to the output file
    """
    # Validate result structure
    _validate_result_dict(result, "csv")
    
    rows = result["matches"]
    header = result["header"]

    if not rows:
        print(f"{Fore.YELLOW}No matches found in {result.get('file', 'input file')}. Nothing saved{Style.RESET_ALL}")
        return
    
    try:
        # Ensure the output directory exists
        save_path = _ensure_output_dir(output_file)

        # Write matched rows to a new CSV file with headers
        with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=result["header"])
            writer.writeheader()  # Write the header to the CSV file
            writer.writerows(result["matches"])  # Write the matched rows to the CSV file

        print(f"\n{Fore.GREEN}Successfully saved {len(rows)} rows to {output_file}{Style.RESET_ALL}")

    except Exception as e:
        raise IOError(f"Error saving CSV data to {output_file}: {str(e)}")
    
def save_excel_matches(result: Dict, output_file: str) -> None:
    """
    Saves the matched rows from an Excel file to a new Excel file,
    preserving sheet structure.

    Args:
        result (Dict): The result dictionary containing file info and sheet data.
        output_file (str): The path to the output Excel file.
        
    Raises:
        ValueError: If the result structure is invalid
        IOError: If there's an error writing to the output file
    """
    # Validate result structure
    _validate_result_dict(result, "excel")
    
    sheets = result["sheets"]
    total_matches = sum(len(sheet.get("matches", [])) for sheet in sheets)

    if total_matches == 0:
        print(f"{Fore.YELLOW}No matches found in {result.get('file', 'input file')}. Nothing saved{Style.RESET_ALL}")
        return
    
    try:
        # Ensure the output directory exists
        save_path = _ensure_output_dir(output_file)

        # Create a Pandas ExcelWriter object
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write each sheets with matches
            sheets_saved = 0
            for sheet in sheets:
                sheet_name = sheet.get("name", "Sheet")
                matches = sheet.get("matches", [])
                
                if not matches:
                    continue

                # Convert matches to DataFrame for easier writing
                df = pd.DataFrame(matches)

                # Write the DataFrame to the Excel file
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                sheets_saved += 1

        # Get sheet names with matches for the success message
        sheet_summary = _get_sheet_summary(sheets)
        print(f"{Fore.GREEN}Successfully saved {total_matches} row(s) across {sheets_saved} sheet(s) to {save_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Sheets with matches: {sheet_summary}{Style.RESET_ALL}")

    except Exception as e:
        raise IOError(f"Error saving Excel data to {output_file}: {str(e)}")
    
def print_transform_summary(
    file_path: str,
    format_type: str,
    query: str,
    column: Optional[str] = None,
    sheet: Optional[str] = None,
    results: Optional[Dict] = None
) -> None:
    """
    Prints a summary of the transform operation results.
    
    Args:
        file_path (str): Path to the input file
        format_type (str): Type of file ('csv', 'excel')
        query (str): The search query used
        column (Optional[str]): Column name if a specific column was searched
        results (Dict): The results from the transform operation
    """
    # Normalize format type
    format_type = format_type.lower()

    # Validate format type
    if format_type not in ["csv", "excel"]:
        raise ValueError(f"Unsupported format type: {format_type}")

    # Print header
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Transform Summary{Style.RESET_ALL}")
    print(f"File: {file_path}")
    print(f"Format: {format_type.upper()}")
    print(f"Query: {query}")

    # Print header/sheet constraints
    if column:
        print(f"Column: {column}")
    else:
        print("Column: All columns")

    if format_type == 'excel' and sheet:
        print(f"Sheet: {sheet}")
    elif format_type == 'excel':
        print("Sheet: All sheets")

    # Print match summary if results are provided
    if results:
        if format_type == 'csv':
            match_count = len(results.get("matches", []))
            print(f"{Fore.GREEN}Matches: {match_count} rows{Style.RESET_ALL}")
        elif format_type.lower() == 'excel':
            sheets = results.get("sheets", [])
            total_matches = sum(len(sheet.get("matches", [])) for sheet in sheets)
            sheets_with_matches = sum(1 for sheet in sheets if len(sheet.get("matches", [])) > 0)
            
            print(f"{Fore.GREEN}Matches: {total_matches} rows across {sheets_with_matches} sheets{Style.RESET_ALL}")

            # Show sheet-specific match counts
            if sheets_with_matches > 0:
                sheet_summary = _get_sheet_summary(sheets)
                print(f"{Fore.GREEN}Matched sheets: {sheet_summary}{Style.RESET_ALL}")