"""Tests for the scraper module."""
import pytest
from pathlib import Path
from typing import Dict, List

# This is just a skeleton test file that will be implemented
# when we develop the scraper functionality

def test_normalize_entry():
    """Test that HTML tags and whitespace are properly removed from entries."""
    # Will be implemented with the scraper module
    pass


def test_parse_table_with_single_adjective():
    """Test parsing a table with a single adjective-animal pair."""
    # Will be implemented with the scraper module
    pass


def test_parse_table_with_multiple_adjectives():
    """Test parsing a table with multiple adjectives in one cell."""
    # Will be implemented with the scraper module
    pass


def test_parse_table_with_footnotes():
    """Test parsing a table with footnotes in cells."""
    # Will be implemented with the scraper module
    pass


@pytest.mark.online
def test_fetch_html():
    """Test fetching HTML from the Wikipedia page (requires internet)."""
    # Will be implemented with the scraper module
    pass
