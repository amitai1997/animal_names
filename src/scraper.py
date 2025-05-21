"""
Scraper module for extracting collateral adjectives and animal mappings.

This module fetches and parses the "List of animal names" Wikipedia page,
focusing on the collateral adjective table.
"""

import html
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests  # type: ignore
from bs4 import BeautifulSoup, Tag  # type: ignore


@dataclass
class Animal:
    """Class representing an animal with its name and corresponding page URL."""

    name: str
    page_url: Optional[str] = None
    image_path: Optional[str] = None


# Configure logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_html(url: str, dest: Path) -> None:
    """
    Download HTML from URL and save to a destination path.

    Args:
        url: The URL to fetch HTML from.
        dest: Path object where the HTML should be saved.

    Raises:
        requests.RequestException: If the request fails for any reason.
    """
    logger.info(f"Fetching HTML from {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
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

    # Replace <br> tags with a semicolon to ensure they're treated as separators
    for br in soup.find_all("br"):
        br.replace_with("; ")

    # Get text with whitespace preserved
    text = soup.get_text()  # type: str

    # Unescape HTML entities
    text = html.unescape(text)

    # Normalize whitespace - collapse multiple spaces to single space
    text = re.sub(r"\s+", " ", text).strip()

    return text


def parse_table(html_path: Path) -> Dict[str, List[Animal]]:
    """
    Parse the "Collateral adjective" table from HTML file.

    Args:
        html_path: Path to the HTML file to parse.

    Returns:
        Dictionary mapping collateral adjectives to lists of Animal objects.

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

    # Find all tables with "Collateral adjective" column
    target_tables = []
    table_column_info = (
        []
    )  # Stores (table, animal_col_idx, adjective_col_idx, column_headers)

    # First scan through all tables with the wikitable class
    for table in soup.find_all("table", class_=["wikitable", "sortable"]):
        if isinstance(table, Tag):
            # Get all header rows in the table
            header_rows = table.find_all("tr", limit=1)
            if not header_rows:
                continue

            header_row = header_rows[0]
            header_cells = header_row.find_all("th")

            # Extract all column header texts
            header_texts = []
            animal_col_idx = -1
            adjective_col_idx = -1

            for idx, cell in enumerate(header_cells):
                text = cell.get_text(strip=True)
                header_texts.append(text)
                # Look for the Collateral adjective column
                if "Collateral adjective" in text:
                    adjective_col_idx = idx
                # Look for potential animal column headers
                if text in ["Animal", "Trivial name", "Scientific term"]:
                    animal_col_idx = idx

            # If we found both required columns, save this table's info
            if adjective_col_idx >= 0 and animal_col_idx >= 0:
                target_tables.append(table)
                table_column_info.append(
                    (table, animal_col_idx, adjective_col_idx, header_texts)
                )
                logger.info(f"Found table with columns: {header_texts}")
                logger.info(
                    f"Using '{header_texts[animal_col_idx]}' (index {animal_col_idx}) "
                    f"and '{header_texts[adjective_col_idx]}' (index {adjective_col_idx})"
                )

    # TODO: Remove this block and related tests after confirming the first scan works
    # If we couldn't find with specific classes, try any table (helpful for tests)
    if not target_tables:
        for table in soup.find_all("table"):
            if isinstance(table, Tag):
                # Get header row
                header_rows = table.find_all("tr", limit=1)
                if not header_rows:
                    continue

                header_row = header_rows[0]
                header_cells = header_row.find_all("th")

                # Extract all column header texts
                header_texts = []
                animal_col_idx = -1
                adjective_col_idx = -1

                for idx, cell in enumerate(header_cells):
                    text = cell.get_text(strip=True)
                    header_texts.append(text)
                    # Look for the Collateral adjective column
                    if "Collateral adjective" in text:
                        adjective_col_idx = idx
                    # Look for potential animal column headers
                    if text in ["Animal", "Trivial name", "Scientific term"]:
                        animal_col_idx = idx

                # For test fixtures - use first column as animal if not found
                if (
                    adjective_col_idx >= 0
                    and animal_col_idx < 0
                    and len(header_texts) > 0
                ):
                    if header_texts[0] == "Animal":
                        animal_col_idx = 0

                # If we found both required columns, save this table's info
                if adjective_col_idx >= 0 and animal_col_idx >= 0:
                    target_tables.append(table)
                    table_column_info.append(
                        (table, animal_col_idx, adjective_col_idx, header_texts)
                    )
                    logger.info(f"Found table with columns: {header_texts}")
                    logger.info(
                        f"Using '{header_texts[animal_col_idx]}' (index {animal_col_idx}) "
                        f"and '{header_texts[adjective_col_idx]}' (index {adjective_col_idx})"
                    )

    if not target_tables:
        error_msg = "Could not find any tables with 'Collateral adjective' header"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create adjective to animals mapping
    result: Dict[str, List[Animal]] = {}

    # Process all found tables
    for table_info in table_column_info:
        table, animal_col_idx, adjective_col_idx, column_headers = table_info

        # Process rows in the table body
        if isinstance(table, Tag):
            rows = table.find_all("tr")[1:]  # Skip header row
            for row in rows:
                if isinstance(row, Tag):
                    cells = row.find_all(["td", "th"])

                    # Skip rows with insufficient cells
                    if len(cells) <= max(animal_col_idx, adjective_col_idx):
                        logger.warning(f"Skipping row with insufficient cells: {row}")
                        continue

                animal_cell = cells[animal_col_idx]
                adjective_cell = cells[adjective_col_idx]

                # Handle rowspan/colspan
                if isinstance(animal_cell, Tag) and (
                    "rowspan" in animal_cell.attrs or "colspan" in animal_cell.attrs
                ):
                    logger.warning(
                        "Row contains merged cells (rowspan/colspan). "
                        "This might affect parsing accuracy."
                    )

                # Extract and normalize animal name, handling footnotes in <small> tags
                page_url = None
                if isinstance(animal_cell, Tag):
                    # Extract the href from the first <a> tag if present
                    link = animal_cell.find("a")
                    if link and "href" in link.attrs:
                        # Convert relative URL to absolute URL
                        href = link["href"]
                        if href.startswith("/wiki/"):
                            page_url = f"https://en.wikipedia.org{href}"
                            logger.debug(f"Found direct link in cell: {page_url}")

                    # Remove <small> tags
                    for small in animal_cell.find_all("small"):
                        # Remove the <small> tag and its contents
                        small.decompose()

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

                    # Always prioritize the URL directly from the Wikipedia page
                    # Only fall back to generating a URL if absolutely necessary
                    if page_url is None:
                        # Log warning when falling back to generated URL
                        logger.warning(
                            f"No direct link found for animal '{animal_name}', falling back to generated URL"
                        )
                        # page_url = create_wikipedia_url(animal_name)
                        a = 1

                    animal_obj = Animal(name=animal_name, page_url=page_url)

                    # Check if this animal already exists in the list
                    if not any(a.name == animal_name for a in result[adj_lower]):
                        result[adj_lower].append(animal_obj)

    logger.info(f"Extracted {len(result)} adjective-animal mappings")
    return result
