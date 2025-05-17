"""
Scraper module for extracting collateral adjectives and animal mappings from Wikipedia.

This module fetches and parses the "List of animal names" Wikipedia page,
focusing on the collateral adjective table.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import html

# Configure logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_html(url: str, dest: Path) -> None:
    """
    Download HTML from URL and save to destination path.

    Args:
        url: The URL to fetch HTML from.
        dest: Path object where the HTML should be saved.

    Raises:
        requests.RequestException: If the request fails for any reason.
    """
    logger.info(f"Fetching HTML from {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Ensure parent directories exist
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        with open(dest, "w", encoding="utf-8") as f:
            f.write(response.text)

        logger.info(f"Successfully saved HTML to {dest}")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        raise


def normalize_entry(raw: str) -> str:
    """
    Strip HTML tags, normalize whitespace, and unescape HTML entities.

    Args:
        raw: Raw text that may contain HTML tags and entities.

    Returns:
        Normalized text with tags removed and entities unescaped.
    """
    if not raw:
        return ""

    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(raw, "html.parser")

    # Process each element to handle (notes) properly
    # Replace <small> tags with space before and after
    for small in soup.find_all("small"):
        small.insert_before(" ")
        small.insert_after(" ")

    # Get text with whitespace preserved
    text = soup.get_text()

    # Unescape HTML entities
    text = html.unescape(text)

    # Normalize whitespace - collapse multiple spaces to single space
    text = re.sub(r"\s+", " ", text).strip()

    return text


def parse_table(html_path: Path) -> Dict[str, List[str]]:
    """
    Parse the "Collateral adjective" table from HTML file.

    Args:
        html_path: Path to the HTML file to parse.

    Returns:
        Dictionary mapping collateral adjectives to lists of animal names.

    Raises:
        FileNotFoundError: If the HTML file doesn't exist.
        ValueError: If the table couldn't be found or parsed.
    """
    logger.info(f"Parsing table from {html_path}")

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"HTML file not found: {html_path}")
        raise

    soup = BeautifulSoup(content, "html.parser")

    # Find the "Collateral adjective" table by header text
    target_table = None
    for table in soup.find_all("table"):
        headers = table.find_all("th")
        for header in headers:
            if "Collateral adjective" in header.get_text():
                target_table = table
                break
        if target_table:
            break

    if not target_table:
        error_msg = "Could not find table with 'Collateral adjective' header"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Identify column indices for "Animal" and "Collateral adjective"
    header_row = target_table.find("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

    try:
        animal_idx = headers.index("Animal")
        adjective_idx = headers.index("Collateral adjective")
    except ValueError:
        error_msg = (
            "Required columns 'Animal' or 'Collateral adjective' not found in table"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create adjective to animals mapping
    result: Dict[str, List[str]] = {}

    # Process rows in the table body
    rows = target_table.find_all("tr")[1:]  # Skip header row
    for row in rows:
        cells = row.find_all(["td", "th"])

        # Skip rows with insufficient cells
        if len(cells) <= max(animal_idx, adjective_idx):
            logger.warning(f"Skipping row with insufficient cells: {row}")
            continue

        animal_cell = cells[animal_idx]
        adjective_cell = cells[adjective_idx]

        # Handle rowspan/colspan
        if "rowspan" in animal_cell.attrs or "colspan" in animal_cell.attrs:
            logger.warning(
                f"Row contains merged cells (rowspan/colspan). This might affect parsing accuracy."
            )

        # Extract and normalize animal name, handling footnotes in <small> tags
        # Replace <small> tags with space before and after
        for small in animal_cell.find_all("small"):
            small.decompose()  # Remove the <small> tag and its contents

        animal_name = normalize_entry(str(animal_cell))
        if not animal_name:
            logger.debug(f"Skipping row with empty animal name: {row}")
            continue

        # Extract and normalize adjective text
        adjective_text = normalize_entry(str(adjective_cell))
        if not adjective_text:
            logger.debug(f"Skipping row with empty adjective: {row}")
            continue

        # Split adjectives on commas or semicolons
        adjectives = []
        for separator in [";", ","]:
            if separator in adjective_text:
                adjectives.extend(
                    [adj.strip() for adj in adjective_text.split(separator)]
                )
                break
        else:
            # If no separator found, use the whole text
            adjectives = [adjective_text]

        # Add entries to result dictionary
        for adjective in adjectives:
            adj_lower = adjective.lower()
            if adj_lower not in result:
                result[adj_lower] = []
            if animal_name not in result[adj_lower]:
                result[adj_lower].append(animal_name)

    logger.info(f"Extracted {len(result)} adjective-animal mappings")
    return result
