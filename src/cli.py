#!/usr/bin/env python
"""Command-line interface for the animal_names project."""
import argparse
import json
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

# Set up logging (default to ERROR level to hide INFO logs)
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_animal_names"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Animal names collateral adjective scraper"
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Path to output HTML report"
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("/tmp"),
        help="Directory to save images (default: /tmp)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("./data/manifest.json"),
        help="Path to save the image manifest (default: ./data/manifest.json)",
    )
    parser.add_argument(
        "--html-snapshot",
        type=Path,
        default=Path("./data/raw_snapshot.html"),
        help="Path to save the raw HTML snapshot (default: ./data/raw_snapshot.html)",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=Path("./templates"),
        help="Directory containing Jinja2 templates (default: ./templates)",
    )
    parser.add_argument(
        "--template-name",
        type=str,
        default="report.html.j2",
        help="Name of the template file to use (default: report.html.j2)",
    )
    parser.add_argument(
        "--static-dir",
        type=Path,
        default=Path("./static"),
        help="Directory containing static assets (default: ./static)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of worker threads for downloading images (default: 8)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts for downloading images (default: 3)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading images and use existing manifest",
    )
    parser.add_argument(
        "--no-console-output",
        action="store_true",
        help="Disable printing adjective-animal mappings to console",
    )
    parser.add_argument(
        "--show-logs",
        action="store_true",
        help="Show detailed log messages (default: only show adjective-animal mappings)",
    )
    return parser.parse_args()


def print_adjective_animals(adjective_animals, manifest):
    """
    Print collateral adjectives and their associated animals to the console.

    Include local links to the downloaded images.

    Args:
        adjective_animals: Dict mapping adjectives to lists of Animal objects or dicts
        manifest: Manifest object with image paths
    """
    print("\nCOLLATERAL ADJECTIVES AND THEIR ANIMALS:\n")
    print("-" * 60)

    # If we have a manifest, use it to display image paths
    image_paths = manifest.entries if manifest else {}

    for adjective, animals in sorted(adjective_animals.items()):
        print(f"\n{adjective.upper()}:")
        for animal in animals:
            # Handle both Animal objects and dictionaries
            if isinstance(animal, dict):
                animal_name = animal.get("name")
                animal_image_path = animal.get("image_path")
            else:  # Assume it's an Animal object
                animal_name = animal.name
                animal_image_path = animal.image_path

            image_path = animal_image_path or image_paths.get(
                animal_name, "No image available"
            )
            print(f"  - {animal_name} [Image: {image_path}]")

    print("\n" + "-" * 60)
    print(f"Total: {len(adjective_animals)} adjectives")
    print("-" * 60 + "\n")


def main() -> int:
    """Execute the main CLI program."""
    start_time = time.time()
    args = parse_args()

    # Configure logging based on parameters
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.show_logs:
        logging.getLogger().setLevel(logging.INFO)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        # Default is to hide logs (only show ERROR logs)
        logging.getLogger().setLevel(logging.ERROR)

    # Ensure output directories exist
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.image_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.html_snapshot.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting animal names scraper")

    # Step 1: Fetch and parse the Wikipedia page
    if not args.html_snapshot.exists():
        logger.info(f"Fetching HTML from {WIKIPEDIA_URL}")
        fetch_html(WIKIPEDIA_URL, args.html_snapshot)
    else:
        logger.info(f"Using existing HTML snapshot from {args.html_snapshot}")

    # Step 2: Parse the table to extract adjective → animal mappings
    logger.info("Parsing collateral adjective table")
    adjective_animals = parse_table(args.html_snapshot)
    logger.info(f"Found {len(adjective_animals)} adjective entries")

    # Step 3: Download images for each animal
    if not args.skip_download:
        logger.info(f"Downloading animal images to {args.image_dir}")
        manifest = download_images(
            adjective_animals,
            args.image_dir,
            workers=args.workers,
            retries=args.retries,
            placeholder_path=Path(__file__).parent / "assets" / "placeholder.jpg",
        )
        # Save the manifest
        manifest.to_json(args.manifest)
        logger.info(f"Saved image manifest to {args.manifest}")
    else:
        logger.info("Skipping image download as requested")
        # Load existing manifest if available
        if args.manifest.exists():
            with open(args.manifest, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            # Create a Manifest object from the loaded data
            from src.downloader import Manifest

            manifest = Manifest(entries=manifest_data)
            logger.info(f"Loaded existing manifest from {args.manifest}")
        else:
            logger.warning("No existing manifest found, cannot skip download")
            return 1

    # Step 4: Generate HTML report
    logger.info(f"Generating HTML report at {args.output}")

    # Setup Jinja2 environment
    env = setup_jinja_env(args.template_dir)
    template = load_template(env, args.template_name)

    # Load and transform manifest data for the template
    adjective_to_animals = load_manifest(args.manifest)

    # Print adjective-animal mappings to console with local links (unless disabled)
    if not args.no_console_output:
        print_adjective_animals(adjective_animals, manifest)

    # Generate the report
    generate_report(adjective_to_animals, template, args.output)

    # Copy static assets to the output directory
    copy_static_assets(args.static_dir, args.output.parent)

    logger.info(f"HTML report generated successfully at {args.output}")

    elapsed_time = time.time() - start_time
    logger.info(f"Processing completed in {elapsed_time:.2f} seconds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
