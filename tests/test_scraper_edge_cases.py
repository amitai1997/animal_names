"""Tests for edge cases in the scraper module."""

import os
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests
from bs4 import BeautifulSoup

from src.scraper import Animal, fetch_html, normalize_entry, parse_table

# Add parent directory to path to make imports work with pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_fetch_html_with_request_exception(temp_dir):
    """Test fetch_html with a request exception."""
    url = "https://en.wikipedia.org/wiki/invalid_url"
    dest = temp_dir / "error.html"

    # Mock requests.get to raise an exception
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Test exception")

        # Verify that the exception is propagated
        with pytest.raises(requests.RequestException):
            fetch_html(url, dest)


def test_normalize_entry_complex():
    """Test normalizing entries with complex HTML structures."""
    # Test with complex HTML
    html_input = '<td><a href="/wiki/Mustelidae">Ferret</a> family <small>(incl. badgers, weasels, etc.)</small></td>'
    result = normalize_entry(html_input)

    # Should preserve text content but strip HTML tags
    assert "Ferret" in result
    assert "family" in result
    assert "(incl. badgers, weasels, etc.)" in result
    assert "<td>" not in result
    assert "<a" not in result
    assert "<small>" not in result


def test_parse_table_malformed_html(temp_dir):
    """Test parsing a table with malformed HTML."""
    # Create a file with malformed HTML
    malformed_html = """
    <html>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Animal</th>
                    <th>Collateral adjective</th>
                </tr>
                <tr>
                    <td>Cat</td>
                    <td>feline
                </tr>
                <tr>
                    Dog
                    <td>canine</td>
                </tr>
            </table>
        </body>
    </html>
    """

    test_file = temp_dir / "malformed.html"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(malformed_html)

    # Parse the table, which should handle the malformed HTML gracefully
    try:
        result = parse_table(test_file)
        # If it succeeds, check that at least one adjective was found
        assert (
            "canine" in result or "feline" in result
        ), "No adjectives found in malformed HTML"
    except Exception as e:
        # If it raises an exception, it should be a controlled one
        assert any(
            term in str(e).lower()
            for term in ["not found", "invalid", "missing", "malformed", "empty"]
        )


def test_parse_table_with_merged_cells(temp_dir):
    """Test parsing a table with merged cells (rowspan/colspan)."""
    # Create HTML with merged cells
    html_with_merged_cells = """
    <html>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Animal</th>
                    <th>Young</th>
                    <th>Collateral adjective</th>
                </tr>
                <tr>
                    <td>Cat</td>
                    <td rowspan="2">kitten</td>
                    <td>feline</td>
                </tr>
                <tr>
                    <td>Lion</td>
                    <!-- Young column has rowspan -->
                    <td>leonine</td>
                </tr>
            </table>
        </body>
    </html>
    """

    test_file = temp_dir / "merged_cells.html"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(html_with_merged_cells)

    # The parser should be able to handle this without crashing
    try:
        result = parse_table(test_file)
        assert len(result) > 0  # Should have parsed at least some entries
    except Exception as e:
        # If it does fail, it should be a controlled exception related to the table structure
        assert "table" in str(e).lower()


def test_parse_table_no_table_in_html(temp_dir):
    """Test parsing an HTML file with no tables at all."""
    # Create HTML without any tables
    html_no_tables = """
    <html>
        <body>
            <h1>List of animal names</h1>
            <p>This page does not contain any tables.</p>
        </body>
    </html>
    """

    test_file = temp_dir / "no_tables.html"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(html_no_tables)

    # Should raise a ValueError about the missing table
    with pytest.raises(ValueError, match=".*table.*"):
        parse_table(test_file)
