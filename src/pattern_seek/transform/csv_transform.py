"""
csv_transform.py - CSV file transformation functionality

This module provides functionality for transforming CSV files by searching and
filtering rows based on query criteria. It supports column-specific searches,
case sensitivity, and whole-word matching. Matched results can be displayed in
a formatted table or saved to a new CSV file.

The module is designed to handle:
- Different CSV formats and encodings
- Robust error handling for malformed files
- Memory-efficient processing of large files
- Integration with the pattern-seek output system
"""

import csv
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from .common import match_rows

def _read_csv_data(
    csv_path: Path,
    encoding: str = 'utf-8',
    delimiter: Optional[str] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Reads a CSV file and returns the data as a list of dictionaries.
    
    Args:
        csv_path (Path): Path to the CSV file
        encoding (str): File encoding to use
        delimiter (Optional[str]): CSV delimiter character
        
    Returns:
        Tuple[List[Dict], List[str]]: Tuple containing the rows and header
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the CSV has no header
        UnicodeDecodeError: If the file can't be decoded with the specified encoding
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    detected_dialect = None

    # Try to detect the dialect if no delimiter is provided
    if not delimiter:
        try:
            with open(csv_path, mode='r', newline='', encoding=encoding) as sample:
                sample_data = sample.read(4096)  # Read a sample to detect format
                detected_dialect = csv.Sniffer().sniff(sample_data)
        except Exception:
            # If detection fails, fall back to default delimiter (comma)
            pass

    # Read the CSV file
    try:
        with open(csv_path, mode='r', newline='', encoding=encoding) as csvfile:
            # Configure the reader
            if detected_dialect and not delimiter:
                reader = csv.DictReader(csvfile, dialect=detected_dialect)
            else:
                reader = csv.DictReader(csvfile, delimiter=delimiter or ',')

            header = reader.fieldnames

            if not header:
                raise ValueError("CSV file has no header row")
            
            # Read all rows into a list
            rows = [row.copy() for row in reader]

            return rows, header
    
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Cannot decode file using {encoding} encoding. Try specifying a different encoding.")
    except Exception as e:
        # Re-raise with more context
        raise type(e)(f"Error processing CSV file: {csv_path}: {str(e)}")

def transform_csv(
        file_path: str,
        query: str,
        column: Optional[str] = None,
        case_sensitive: bool = False,
        matchword: bool = False,
        save: bool = False,
        encoding: str = 'utf-8',
        delimiter: Optional[str] = None,
) -> Dict:
    """
    Searches a CSV file for rows where the query string appears in one or more fields.

    Args:
        file_path (str): Path to the CSV file to search.
        query (str): The text to search for in the file.
        column (Optional[str]): If provided, only search this specific column.
        case_sensitive (bool): Whether the search should respect letter casing.
        matchword (bool): Whether to match whole words only.
        save (bool): If True, save the matching rows to a new CSV file.
        encoding (str): File encoding to use (default: 'utf-8').
        delimiter (Optional[str]): CSV delimiter character. If None, automatically detected.

    Returns:
        Dict: A dictionary containing:
            - "file": Original file path
            - "header": List of column names
            - "matches": List of matching rows as dictionaries
            If save=True, returns an empty dict after saving results to file.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the CSV file has no header row or other format issues
        UnicodeDecodeError: If the file cannot be decoded using the specified encoding
    """
    # Convert to path for better path handling
    path = Path(file_path)

    # Validate inputs
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    if not query:
        raise ValueError("Search query cannot be empty")

    try:
        # Read CSV data using helper function
        rows, header = _read_csv_data(path, encoding, delimiter)

        # Validate column if specified
        if column and column not in header:
            raise ValueError(f"Column '{column}' not found in CSV. Available columns: {', '.join(header)}")
            
        # Use the match_rows helper to find matching rows
        matches = match_rows(rows, query, column, case_sensitive, matchword)
    
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Cannot decode file using {encoding} encoding. Try specifying a different encoding.")
    except Exception as e:
        # Re-raise with more context
        raise type(e)(f"Error processing CSV file: {file_path}: {str(e)}")
    
    # Prepare result dictionary
    result = {
        "file": file_path,
        "header": header,
        "matches": matches
    }
    
    # Handle saving results if requested
    if save:
        if not matches:
            print(f"No matches found in {file_path}. Nothing was saved.")
            return {}
        
        #Generate output filename
        save_path = path.parent / f"{path.stem}-transformed.csv"

        # Import here to avoid circular imports
        from .output import save_csv_matches

        # Save the matched rows to a new CSV file
        save_success = save_csv_matches(result, str(save_path))

        # Only print message if save was successful
        if save_success:
            print(f"\nSaved transformed results to {save_path}")
    
    # Return the results dictionary
    return result

def detect_csv_format(file_path: str, encoding: str = 'utf-8') -> Tuple[str, Optional[csv.Dialect]]:
    """
    Detects the format of a CSV file, including delimiter and encoding.

    Args:
        file_path (str): Path to the CSV file to analyze.
        encoding (str): Initial encoding to try.

    Returns:
        Tuple[str, Optional[csv.Dialect]]: Detected encoding and dialect (or None if detection failed)

    Note:
        This function attempts to detect the best encoding if the provided one fails
    """
    
    # List of encodings to try if the provided one fails
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    # Start with the provided encoding
    if encoding not in encodings_to_try:
        encodings_to_try.insert(0, encoding)
    else:
        # Move the provided encoding to the front of the list
        encodings_to_try.remove(encoding)
        encodings_to_try.insert(0, encoding)

    # Try each encoding
    detected_encoding = None
    detected_dialect = None

    for enc in encodings_to_try:
        try:
            with open(file_path, mode='r', newline='', encoding=enc) as f:
                # Read a sample to detect the dialect
                sample = f.read(4096)
                detected_dialect = csv.Sniffer().sniff(sample)
                detected_encoding = enc
                break
        except UnicodeDecodeError:
            continue
        except csv.Error:
            # If dialect detection fails but we could read the file, keep the encoding
            detected_encoding = enc
            break

    if not detected_encoding:
        raise UnicodeDecodeError("Could not decode the file with any of the attenpted encodings")
    
    return detected_encoding, detected_dialect