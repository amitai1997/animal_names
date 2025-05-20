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
    Download HTML from URL and save to destination path.

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

    # Find the "Collateral adjective" table by header text
    target_table = None
    animal_col_name = ""
    for table in soup.find_all("table", class_=["wikitable", "sortable"]):
        if isinstance(table, Tag):
            headers = table.find_all("th")
            for header in headers:
                if "Collateral adjective" in header.get_text():
                    target_table = table
                    
                    # Find the column that likely contains animal names
                    possible_animal_cols = ["Animal", "Trivial name", "Scientific term"]
                    header_texts = [th.get_text(strip=True) for th in headers]
                    
                    for col in possible_animal_cols:
                        if col in header_texts:
                            animal_col_name = col
                            logger.info(f"Found table with '{col}' and 'Collateral adjective' columns")
                            break
                    
                    if animal_col_name:  # Found a valid animal column
                        break
                    else:
                        # Keep looking for a better table with an animal column
                        target_table = None
        if target_table and animal_col_name:
            break

    if not target_table:
        error_msg = "Could not find table with 'Collateral adjective' header"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Identify column indices for animal column and "Collateral adjective"
    header_row = target_table.find("tr")
    if not isinstance(header_row, Tag):
        error_msg = "Header row is not a Tag"
        logger.error(error_msg)
        raise ValueError(error_msg)

    headers_elements = header_row.find_all("th")
    header_texts: List[str] = [th.get_text(strip=True) for th in headers_elements]

    try:
        animal_idx = header_texts.index(animal_col_name)
        adjective_idx = header_texts.index("Collateral adjective")
        logger.info(f"Using '{animal_col_name}' column (index {animal_idx}) and 'Collateral adjective' column (index {adjective_idx})")
    except ValueError:
        error_msg = (
            f"Required columns '{animal_col_name}' or 'Collateral adjective' " "not found in table"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create adjective to animals mapping
    result: Dict[str, List[Animal]] = {}

    # Process rows in the table body
    if isinstance(target_table, Tag):
        rows = target_table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            if isinstance(row, Tag):
                cells = row.find_all(["td", "th"])

                # Skip rows with insufficient cells
                if len(cells) <= max(animal_idx, adjective_idx):
                    logger.warning(f"Skipping row with insufficient cells: {row}")
                    continue

                animal_cell = cells[animal_idx]
                adjective_cell = cells[adjective_idx]

                # Handle rowspan/colspan
                if isinstance(animal_cell, Tag) and (
                    "rowspan" in animal_cell.attrs or "colspan" in animal_cell.attrs
                ):
                    logger.warning(
                        "Row contains merged cells (rowspan/colspan). "
                        "This might affect parsing accuracy."
                    )

                # Extract and normalize animal name, handling footnotes in <small> tags
                if isinstance(animal_cell, Tag):
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
                    
                    # Create page URL based on animal name
                    page_url = f"https://en.wikipedia.org/wiki/{animal_name.replace(' ', '_')}"
                    animal_obj = Animal(name=animal_name, page_url=page_url)
                    
                    # Check if this animal already exists in the list
                    if not any(a.name == animal_name for a in result[adj_lower]):
                        result[adj_lower].append(animal_obj)

    logger.info(f"Extracted {len(result)} adjective-animal mappings")
    return result
