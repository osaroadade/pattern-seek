"""
common.py - Shared text matching functionality

This module provides reusable text matching logic used across various file
transformation operations (CSV, Excel, etc.). It encapsulates the core matching 
functionality, ensuring consistent behavior between different file formats.

Key features:
- Case-sensitive or case-insensitive matching
- Whole word or substring matching
- Support for None/non-string values

Design considerations:
- Performance optimized for large datasets
- Clear separation from format-specific code
- Consistent behavior across all transform operations
"""

import re
from typing import Any, Union, Optional, Dict, List

def is_match(
    cell_value: Any, 
    query: str, 
    case_sensitive: bool = False, 
    matchword: bool = False
) -> bool:
    """
    Determines if a cell value matches a query string based on specified criteria.

    This is the core matching function used by all transform operations. It handles
    both simple substring matching and more complex whole-word matching with optional
    case sensitivity.

    Args:
        cell_value (Any): The value from a cell/field to check against the query.
                         Will be converted to string if not already.
        query (str): The search term to look for within the cell value.
        case_sensitive (bool): If True, performs case-sensitive comparison.
                              If False (default), ignores case differences.
        matchword (bool): If True, only matches complete words using word boundaries.
                         If False (default), matches substrings anywhere in the text.

    Returns:
        bool: True if the cell value matches the query according to the specified criteria,
              False otherwise.

    Examples:
        >>> is_match("Hello World", "world")
        True
        >>> is_match("Hello World", "world", case_sensitive=True)
        False
        >>> is_match("Hello World", "ello")
        True
        >>> is_match("Hello World", "ello", matchword=True)
        False
        >>> is_match(None, "test")
        False
        >>> is_match(123, "23")
        True      
    """
    # Handles None values
    if cell_value is None:
        return False
    
    # Convert non-string values to strings to ensure compatibility
    if not isinstance(cell_value, str):
        try:
            cell_value = str(cell_value)
        except Exception:
            # If conversion fails (unlikely), treat as no match
            return False
        
    # Validate query is a string
    if not isinstance(query, str) or not query:
        return False
    
    # Handle case sensitivity by converting to lowercase if needed
    if not case_sensitive:
        cell_value = cell_value.lower()
        query = query.lower()
    
    if matchword:
        # For whole word matching, create a regex pattern with word boundaries
        # This ensures we only match complete words, not parts of words
        pattern = r'\b' + re.escape(query) + r'\b'
        return bool(re.search(pattern, cell_value))
    
    # Simple substring search for non-whole-word matching
    return query in cell_value

def match_row(
    row: dict,
    query: str,
    column: Optional[str] = None,
    case_sensitive: bool = False,
    matchword: bool = False,
) -> bool:
    """
    Checks if a row matches a query by checking if any field (or a specific column)
    contains the query string.

    Args:
        row (dict): Dictionary representing a row of data with field names as keys
        query (str): The search term to look for
        column (Optional[str]): If provided, only search this specific column
        case_sensitive (bool): Whether to perform case-sensitive matching
        matchword (bool): Whether to match whole words only

    Returns:
        bool: True if the row contains a field that matches the query

    Raises:
        KeyError: If a specific column is provided but doesn't exist in the row
    """
    if not row:
        return False
    
    # If a specific column is given, only search that column
    if column:
        if column not in row:
            raise KeyError(f"Column '{column}' not found in row. Available columns: {', '.join(row.keys())}")
        return is_match(row[column], query, case_sensitive, matchword)
    
    # Otherwise search all columns
    return any(
        is_match(value, query, case_sensitive, matchword)
        for value in row.values()
    )

def match_rows(
    rows: List[Dict],
    query: str,
    column: Optional[str] = None,
    case_sensitive: bool = False,
    matchword: bool = False,
) -> List[Dict]:
    """
    Filters a list of rows to only those that match the query criteria.
    
    This is a helper function to simplify filtering in transform operations.
    
    Args:
        rows (List[Dict]): List of row dictionaries to filter
        query (str): The search term to look for
        column (Optional[str]): If provided, only search this specific column
        case_sensitive (bool): Whether to perform case-sensitive matching
        matchword (bool): Whether to match whole words only
        
    Returns:
        List[Dict]: List of rows that match the criteria
        
    Raises:
        KeyError: If a specific column is provided but doesn't exist in any row
    """
    if not rows:
        return []
    
    # If a column is specified, verify it exists in the first row
    if column and rows and column not in rows[0]:
        available_columns = list(rows[0].keys()) if rows else []
        raise KeyError(f"Column '{column}' not found. Available columns: {', '.join(available_columns)}")
    
    # Filter rows using match_row
    return [
        row.copy() for row in rows
        if match_row(row, query, column, case_sensitive, matchword)
    ]