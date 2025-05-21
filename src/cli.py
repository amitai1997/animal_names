#!/usr/bin/env python
"""Simplified command-line interface for the animal_names project (basic usage only)."""
import argparse
import logging
import sys
import time
from pathlib import Path

from src.downloader import download_images
from src.renderer import (
    copy_static_assets,
    generate_report,
    load_manifest,
    load_template,
    setup_jinja_env,
)
from src.scraper import fetch_html, parse_table

# Constants
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_animal_names"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments (basic usage only)."""
    parser = argparse.ArgumentParser(
        description="Animal names collateral adjective scraper (basic usage)"
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Path to output HTML report"
    )
    return parser.parse_args()


def main() -> int:
    """Execute the main CLI program (basic usage only)."""
    start_time = time.time()
    args = parse_args()

    # Disable all logging from imported modules
    logging.getLogger().handlers.clear()
    logging.basicConfig(level=logging.CRITICAL)
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    # Also disable warnings from the 'warnings' module
    import warnings

    warnings.filterwarnings("ignore")

    # Set up basic paths
    image_dir = Path("./data/images")
    manifest_path = Path("./data/manifest.json")
    html_snapshot = Path("./data/raw_snapshot.html")
    template_dir = Path("./templates")
    template_name = "report.html.j2"
    static_dir = Path("./static")

    # Ensure output directories exist
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    html_snapshot.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Fetch and parse the Wikipedia page
    if not html_snapshot.exists():
        fetch_html(WIKIPEDIA_URL, html_snapshot)

    # Step 2: Parse the table to extract adjective → animal mappings
    adjective_animals = parse_table(html_snapshot)

    # Step 3: Download images for each animal
    manifest = download_images(
        adjective_animals,
        image_dir,
        workers=8,
        retries=3,
        placeholder_path=Path(__file__).parent / "assets" / "placeholder.jpg",
    )
    manifest.to_json(manifest_path)

    # Step 4: Generate HTML report
    env = setup_jinja_env(template_dir)
    template = load_template(env, template_name)
    adjective_to_animals = load_manifest(manifest_path)
    generate_report(adjective_to_animals, template, args.output)
    copy_static_assets(static_dir, args.output.parent)

    # Print only the required output: adjectives and their animals (no links)
    for adjective, animals in sorted(adjective_to_animals.items()):
        print(f"Adjective: {adjective}")
        for animal in animals:
            animal_name = animal.get("name", "")
            print(f" - {animal_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
