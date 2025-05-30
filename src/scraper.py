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


def clean_animal_name(name: str) -> str:
    """
    Clean up animal names by removing annotations like '(list)' and 'Also see X'.

    Args:
        name: Raw animal name that may contain annotations.

    Returns:
        Cleaned animal name.
    """
    # Remove '(list)' annotation
    name = re.sub(r"\s*\(list\)", "", name)

    # Remove 'Also see X' annotations
    name = re.sub(r"\s*;\s*Also see.*", "", name)

    # Remove square bracket annotations like [C], [D], etc.
    name = re.sub(r"\s*\[[A-Za-z0-9]\]", "", name)

    # Strip any remaining whitespace
    return name.strip()


def create_wikipedia_url(animal_name: str) -> str:
    """
    Generate a Wikipedia URL for an animal based on its name, following Wikipedia's URL conventions.

    This function is used only as a fallback when no direct link can be found in the HTML.

    Args:
        animal_name: The name of the animal.

    Returns:
        A Wikipedia URL for the animal.
    """
    import urllib.parse

    clean_name = clean_animal_name(animal_name)
    if not clean_name:
        return "https://en.wikipedia.org/wiki/"
    # Wikipedia: only first character is capitalized, spaces to underscores, percent-encode
    wiki_name = clean_name.replace(" ", "_")
    if wiki_name:
        wiki_name = wiki_name[0].upper() + wiki_name[1:]
    wiki_name = urllib.parse.quote(wiki_name, safe="_")
    return f"https://en.wikipedia.org/wiki/{wiki_name}"


def parse_table(html_path: Path) -> Dict[str, List[Animal]]:
    """
    Parse the "Collateral adjective" table from an HTML file.

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
    if not target_tables:
        error_msg = "Could not find any tables with 'Collateral adjective' header"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create adjective to animal mapping
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

                    # Always use the URL directly from the Wikipedia page if available
                    # Only fall back to generating a URL as a last resort for animals without links
                    if page_url is None:
                        # Log warning when no direct link found
                        logger.warning(
                            f"No direct link found for animal '{animal_name}', falling back to generated URL"
                        )
                        page_url = create_wikipedia_url(animal_name)

                    # Clean the animal name before creating the Animal object
                    clean_name = clean_animal_name(animal_name)
                    animal_obj = Animal(name=clean_name, page_url=page_url)

                    # Check if this animal already exists in the list
                    if not any(a.name == clean_name for a in result[adj_lower]):
                        result[adj_lower].append(animal_obj)

    logger.info(f"Extracted {len(result)} adjective-animal mappings")
    return result
