"""
Test data helper module
Contains paths and utilities for test data files
"""

import os
from pathlib import Path

# Base path for test data
TEST_DATA_DIR = Path(__file__).parent

# Test data file paths
TEST_FILES = {
    'valid_prices': TEST_DATA_DIR / 'valid_prices.csv',
    'invalid_missing_columns': TEST_DATA_DIR / 'invalid_missing_columns.csv',
    'empty_data': TEST_DATA_DIR / 'empty_data.csv',
    'invalid_price_data': TEST_DATA_DIR / 'invalid_price_data.csv',
    'negative_price_data': TEST_DATA_DIR / 'negative_price_data.csv',
}

# Excel test data for creating temp files
VALID_EXCEL_DATA = [
    ["name", "category", "unit", "price", "description"],
    ["Cement Portland", "Building Materials", "kg", 45.50, "High quality cement"],
    ["Sand Construction", "Building Materials", "m3", 1200.00, "Washed construction sand"],
]

def get_test_file_path(file_key: str) -> str:
    """Get absolute path to test data file"""
    return str(TEST_FILES[file_key])

def read_test_file_content(file_key: str) -> str:
    """Read content of test data file"""
    with open(TEST_FILES[file_key], 'r', encoding='utf-8') as f:
        return f.read() 