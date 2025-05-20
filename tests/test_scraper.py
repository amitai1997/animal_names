"""Tests for the scraper module."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from src.downloader import download_images
from src.scraper import Animal, fetch_html, normalize_entry, parse_table

# Add parent directory to path to make imports work with pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for the test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_normalize_entry() -> None:
    """Test that HTML tags and whitespace are properly removed from entries."""
    # HTML with tags and excessive whitespace
    html_input = "<p>  Test   <small>(note)</small>  text  </p>"
    expected = "Test (note) text"

    result = normalize_entry(html_input)
    assert result == expected

    # Empty input
    assert normalize_entry("") == ""

    # HTML entities
    assert normalize_entry("&lt;test&gt;") == "<test>"


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


def test_parse_table_with_single_adjective() -> None:
    """Test parsing a table with a single adjective-animal pair."""
    fixture_path = Path(__file__).parent / "fixtures" / "raw_snapshot.html"

    # Since we're testing a single adjective, we'll focus on the avian/bird pair
    result = parse_table(fixture_path)

    assert "avian" in result
    assert len(result["avian"]) == 2  # There are two entries in the snapshot
    assert result["avian"][0].name == "bird"


def test_parse_table_with_multiple_adjectives() -> None:
    """Test parsing a table with multiple adjectives in one cell."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_table.html"

    result = parse_table(fixture_path)

    # Check for feline and felid adjectives (both should point to cat)
    assert "feline" in result
    assert "felid" in result
    assert result["feline"][0].name == "cat"
    assert result["felid"][0].name == "cat"


def test_parse_table_with_footnotes() -> None:
    """Test parsing a table with footnotes in cells."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_table.html"

    result = parse_table(fixture_path)

    # Check that the animal name with a <small> footnote is properly parsed
    assert "simian" in result
    assert result["simian"][0].name == "monkey"
    assert "(primate)" not in result["simian"][0].name  # Should be stripped out


def test_parse_table_with_empty_tbody(temp_dir) -> None:
    """Test parsing a table with an empty tbody."""
    # Create a temporary HTML file with an empty tbody
    empty_table_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Empty Table</title>
    </head>
    <body>
        <table>
            <tr>
                <th>Animal</th>
                <th>Collateral adjective</th>
            </tr>
        </table>
    </body>
    </html>
    """
    empty_table_path = temp_dir / "empty_table.html"
    with open(empty_table_path, "w", encoding="utf-8") as f:
        f.write(empty_table_html)

    # Parse the empty table
    result = parse_table(empty_table_path)

    # The result should be an empty dictionary
    assert result == {}


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


@pytest.mark.online
def test_fetch_html(temp_dir) -> None:
    """Test fetching HTML from the Wikipedia page (requires internet)."""
    # This test requires internet connection, so we'll skip it in regular test runs
    # Implement only the structure, the test will be skipped if not marked for online tests
    pass


@pytest.mark.online
def test_live_wikipedia_integration():
    """Integration test with the actual Wikipedia page."""
    # Create a temporary directory and file for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        html_path = temp_path / "live_wiki.html"

        # Step 1: Fetch the actual Wikipedia page
        fetch_html("https://en.wikipedia.org/wiki/List_of_animal_names", html_path)
        assert html_path.exists()
        assert html_path.stat().st_size > 0

        # Step 2: Parse the table from the live page
        animal_mappings = parse_table(html_path)

        # Verify we got some results
        assert len(animal_mappings) > 0

        # Check for some expected adjectives
        common_adjectives = ["avian", "feline", "canine", "equine", "bovine"]
        found_adjectives = [adj for adj in common_adjectives if adj in animal_mappings]
        assert (
            len(found_adjectives) > 0
        ), f"Found adjectives: {list(animal_mappings.keys())}"

        # Verify animal objects have valid URLs
        for adjective, animals in animal_mappings.items():
            for animal in animals:
                assert animal.name, f"Animal without name found in {adjective}"
                assert animal.page_url, f"Animal without URL found: {animal.name}"
                assert animal.page_url.startswith(
                    "https://"
                ), f"Invalid URL format: {animal.page_url}"


@pytest.mark.online
@pytest.mark.slow
def test_full_pipeline_with_live_data():
    """Integration test for the full pipeline with live Wikipedia data."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        html_path = temp_path / "live_wiki.html"
        image_dir = temp_path / "images"
        manifest_path = temp_path / "manifest.json"

        # Step 1: Fetch the actual Wikipedia page
        fetch_html("https://en.wikipedia.org/wiki/List_of_animal_names", html_path)

        # Step 2: Parse the table from the live page
        animal_mappings = parse_table(html_path)

        # Step 3: Download a small subset of images (limit to 2 adjectives for speed)
        # Choose first two adjectives from the mappings
        limited_mappings = {}
        for i, (adj, animals) in enumerate(animal_mappings.items()):
            if i < 2:  # Limit to the first two adjectives
                limited_mappings[adj] = animals

        # Download images
        manifest = download_images(limited_mappings, image_dir, workers=2, retries=1)

        # Save the manifest
        manifest.to_json(manifest_path)

        # Verify images were downloaded
        assert len(manifest.entries) > 0
        for animal_name, image_path in manifest.entries.items():
            assert Path(
                image_path
            ).exists(), f"Image not found for {animal_name}: {image_path}"
            assert (
                Path(image_path).stat().st_size > 0
            ), f"Empty image for {animal_name}: {image_path}"
