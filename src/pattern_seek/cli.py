"""
cli.py - Command Line Interface for pattern-seek

This module provides the command-line interface for the pattern-seek application,
handling all user inputs, options parsing, and orchestrating the execution flow.
It uses the Click library to define the command structure and options.

The CLI supports two main modes of operation:
1. Pattern searching: Find various data patterns (emails, GUIDs, etc.) in text files
2. File transformation: Query and transform structured data files (CSV, Excel)

Command hierarchy:
- Main command (pattern-seek)
    - Pattern search options
    - Transform options
"""

import os
import sys
from pathlib import Path
import click
from typing import List, Optional

from pattern_seek.core import search_files
from pattern_seek.output import print_matches

# Imrport transform modules
from pattern_seek.transform import (
    transform_csv,
    transform_excel, 
    print_csv_matches,
    print_excel_matches, 
    save_csv_matches,
    save_excel_matches,
    print_transform_summary
)

@click.command()
@click.argument('paths', nargs=-1, required=True)
@click.option(
    '--pattern', '-p', 
    type=click.Choice(['email', 'guid', 'date', 'url', 'ip', 'text', 'all']),
    multiple=True,
    default=['all'],
    help='Pattern types to search for'
)
@click.option(
    '--text', '-t',
    type=str,
    help='Text pattern to search for when using the "text" pattern type'
)
@click.option(
    '--case-sensitive', '-c',
    is_flag=True,
    help='Make text search case-sensitive'
)
@click.option(
    '--whole-word', '-w',
    is_flag=True,
    help='Match whole words only for text search'
)
@click.option(
    '--context', '-C',
    type=int,
    default=0,
    help='Number of context lines to include before and after matches'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable colored output'
)

# Transform group
@click.option(
    '--transform', '-T',
    type=click.Choice(['csv', 'excel']),
    help='Transform structured file formats (CSV, Excel) based on query'
)

# Transform speific options
@click.option(
    '--query', '-q',
    type=str,
    help='Search query for transform mode'
)
@click.option(
    '--column', '-col',
    type=str,
    help='Column name to search in for transform mode'
)
@click.option(
    '--sheet', '-sh',
    type=str,
    help='Column name to search in for transform mode'
)
@click.option(
    '--matchword', '-m',
    is_flag=True,
    help='Match whole words only for transform mode'
)
@click.option(
    '--save', '-s',
    is_flag=True,
    help='Save transformed results to a new file'
)
@click.option(
    '--encoding', '-e',
    type=str,
    help='File encoding for CSV files (default: utf-8)'
)
def main(
    paths: List[str],
    pattern: List[str],
    text: Optional[str],
    case_sensitive: bool,
    whole_word: bool,
    context: int,
    no_color: bool,
    transform: Optional[str],
    query: Optional[str],
    column: Optional[str],
    sheet: Optional[str],
    matchword: bool,
    save: bool,
    encoding: Optional[str]
) -> None:
    """
    Pattern-seek: Search files for specific patterns or transform structured data.
    
    PATHS: One or more files or directories to search.
    Wildcards are supported, e.g., *.txt
    
    Two modes of operation:
    
    1. Pattern Search: Find emails, GUIDs, dates, URLs, IPs, or custom text.
       Example: pattern-seek --pattern email example.txt
    
    2. Transform Mode: Query and filter structured data files (CSV, Excel).
       Example: pattern-seek --transform csv --query "Smith" data.csv
    """

    # Handle transform mode
    if transform:
        _handle_transform_mode(
            paths=paths,
            transform_type=transform,
            query=query,
            column=column,
            sheet=sheet,
            case_sensitive=case_sensitive,
            matchword=matchword,
            save=save,
            encoding=encoding,
        )
        return # Skip the rest of the pattern-based logic
    
    # handle pattern search mode
    _handle_pattern_search(
        paths=paths,
        pattern=pattern,
        text=text,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        context=context,
        no_color=no_color,
    )

def _handle_transform_mode(
    paths: List[str],
    transform_type: str,
    query: Optional[str],
    column: Optional[str],
    sheet: Optional[str],
    case_sensitive: bool,
    matchword: bool,
    save: bool,
    encoding: Optional[str]
) -> None:
    """
    Handle the transform mode operation.
    
    Args:
        paths: List of file paths to transform
        transform_type: Type of transform ('csv', 'excel')
        query: Search query string
        column: Optional column name to limit search to
        sheet: Optional sheet name for Excel files
        case_sensitive: Whether to do case-sensitive matching
        matchword: Whether to match whole words only
        save: Whether to save results to a new file
        encoding: File encoding for text-based formats
    """

    # Check required parameters
    if not query:
        click.echo("Error: --query must be provided when using --transform", err=True)
        sys.exit(1)

    # Process each file
    for path in paths:
        # Skip directories and non-existing files
        if not os.path.isfile(path):
            click.echo(f"Skipping {path}: Not a file or doesn't exist", err=True)
            continue
        
        # Check file extension matches transform type
        path_lower = path.lower()
        file_ext = os.path.splitext(path_lower)[1]

        if transform_type == 'csv' and file_ext != '.csv':
            click.echo(f"Warning: {path} doesn't have a .csv extension but processing as CSV", err=True)
        elif transform_type == 'excel' and file_ext not in ['.xlsx', '.xls', '.xlsm']:
            click.echo(f"Warning: {path} doesn't have an Excel extension but processing as Excel", err=True)

        try:
            # Process based on transform type
            if transform_type == 'csv':
                result = transform_csv(
                    file_path=path,
                    query=query,
                    column=column,
                    case_sensitive=case_sensitive,
                    matchword=matchword,
                    save=save,
                    encoding=encoding
                )

                if not save and result:
                    print_csv_matches(result)

            elif transform_type == 'excel':
                result = transform_excel(
                    file_path=path,
                    query=query,
                    sheet=sheet,
                    column=column,
                    case_sensitive=case_sensitive,
                    matchword=matchword,
                    save=save
                )

                if not save and result:
                    print_excel_matches(result)

        except Exception as e:
            click.echo(f"Error transforming {path}: {str(e)}", err=True)

def _handle_pattern_search(
    paths: List[str],
    pattern: List[str],
    text: Optional[str],
    case_sensitive: bool,
    whole_word: bool,
    context: int,
    no_color: bool
) -> None:
    """
    Handle the pattern search mode operation.
    
    Args:
        paths: List of file paths to search
        pattern: List of pattern types to search for
        text: Text pattern for 'text' pattern type
        case_sensitive: Whether to do case-sensitive matching
        whole_word: Whether to match whole words only
        context: Number of context lines to include
        no_color: Whether to disable colored output
    """
    # Determine which patterns to search for
    if 'all' in pattern:
        pattern_types = ['email', 'guid', 'date', 'url', 'ip']
    else:
        pattern_types = list(pattern)
        
    # Check if text search is required but no pattern provided
    if 'text' in pattern_types and not text:
        click.echo("Error: Text pattern must be provided when searching for 'text' pattern type.", err=True)
        sys.exit(1)
        
    # Process each path
    all_results = []
    fall_results = []
    for path in paths:
        try:
            results = search_files(
                path, 
                pattern_types, 
                context_lines=context,
                text_pattern=text,
                case_sensitive=case_sensitive,
                whole_word=whole_word
            )
            all_results.extend(results)
        except Exception as e:
            click.echo(f"Error processing {path}: {str(e)}", err=True)
            
    # Print results
    if all_results:
        print_matches(all_results, colored=not no_color, include_file_info=True)
    else:
        click.echo("No matches found.")
        
    # Return non-zero exit code if no matches were found
    has_matches = any(
        len(result.get("matches", [])) > 0 
        for result in all_results
    )
    if not has_matches:
        sys.exit(1)
        
if __name__ == "__main__":
    main()