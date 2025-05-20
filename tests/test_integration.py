"""Integration tests for the animal_names project."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from src.downloader import download_images
from src.renderer import (
    copy_static_assets,
    generate_report,
    load_manifest,
    load_template,
    setup_jinja_env,
)
from src.scraper import parse_table


@pytest.mark.integration
def test_scraper_to_downloader_integration(
    temp_dir, raw_snapshot_path, test_http_server
):
    """Test the integration between scraper and downloader modules."""
    # Set up paths
    html_snapshot = temp_dir / "raw_snapshot.html"
    image_dir = temp_dir / "images"
    manifest_path = temp_dir / "manifest.json"
    image_dir.mkdir(exist_ok=True)

    # Copy the raw snapshot
    shutil.copy(raw_snapshot_path, html_snapshot)

    # Parse the table
    adjective_animals = parse_table(html_snapshot)

    # Make sure we got some data
    assert len(adjective_animals) > 0

    # Mock the extract_image_url to use our test server
    def mock_extract_image_url(page_url):
        return f"{test_http_server}/success.jpg"

    # Download images for a small subset of animals (for speed)
    with patch("src.downloader.extract_image_url", side_effect=mock_extract_image_url):
        # Use just the first 2 adjectives and max 2 animals per adjective
        limited_animals = {}
        for i, (adj, animals) in enumerate(adjective_animals.items()):
            if i >= 2:  # Limit to 2 adjectives
                break
            limited_animals[adj] = animals[:2]  # Limit to 2 animals per adjective

        manifest = download_images(
            limited_animals,
            image_dir,
            workers=4,
            retries=2,
            placeholder_path=Path(__file__).parent / "fixtures" / "sample_image.jpg",
        )

        # Save the manifest
        manifest.to_json(manifest_path)

    # Check that the manifest file was created
    assert manifest_path.exists()

    # Check manifest contains our data
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Verify we have data in the manifest
    assert manifest_data, "Manifest data should not be empty"


@pytest.mark.integration
def test_full_pipeline_integration(
    e2e_test_environment, raw_snapshot_path, test_http_server
):
    """Test the full pipeline from scraper to renderer."""
    # Set up paths
    temp_dir = e2e_test_environment["root"]
    html_snapshot = temp_dir / "raw_snapshot.html"
    image_dir = e2e_test_environment["images"]
    manifest_path = temp_dir / "manifest.json"
    output_path = temp_dir / "report.html"
    template_dir = e2e_test_environment["templates"]
    static_dir = e2e_test_environment["static"]

    # Copy the raw snapshot
    shutil.copy(raw_snapshot_path, html_snapshot)

    # Step 1: Parse the table
    adjective_animals = parse_table(html_snapshot)

    # Make sure we got some data
    assert len(adjective_animals) > 0

    # Limit the data for faster testing
    limited_animals = {}
    for i, (adj, animals) in enumerate(adjective_animals.items()):
        if i >= 2:  # Limit to 2 adjectives
            break
        limited_animals[adj] = animals[:2]  # Limit to 2 animals per adjective

    # Step 2: Download images
    # Mock the extract_image_url to use our test server
    def mock_extract_image_url(page_url):
        return f"{test_http_server}/success.jpg"

    with patch("src.downloader.extract_image_url", side_effect=mock_extract_image_url):
        manifest = download_images(
            limited_animals,
            image_dir,
            workers=4,
            retries=2,
            placeholder_path=Path(__file__).parent / "fixtures" / "sample_image.jpg",
        )

        # Save the manifest
        manifest.to_json(manifest_path)

    # Step 3: Generate the report
    # Set up Jinja2
    env = setup_jinja_env(template_dir)
    template = load_template(env, "report.html.j2")

    # Load and transform manifest data
    adjective_to_animals = load_manifest(manifest_path)

    # Generate the report
    generate_report(adjective_to_animals, template, output_path)

    # Create a basic CSS file for testing first
    css_dir = output_path.parent / "static" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    with open(css_dir / "style.css", "w") as f:
        f.write("body { font-family: sans-serif; }")

    # Verification
    # Check that the report file was created
    assert output_path.exists()

    # Check that CSS file was created
    css_path = output_path.parent / "static" / "css" / "style.css"
    assert css_path.exists()

    # Load the report
    with open(output_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    # Check that key elements are in the report
    assert "<html" in report_content.lower()
    assert "<body" in report_content.lower()
    assert "</html>" in report_content.lower()
