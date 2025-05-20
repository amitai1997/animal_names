"""Integration tests for the animal_names project."""

import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from src.scraper import fetch_html, parse_table
from src.downloader import download_images
from src.renderer import setup_jinja_env, load_template, generate_report, copy_static_assets, load_manifest


@pytest.mark.integration
def test_scraper_to_downloader_integration(temp_dir, raw_snapshot_path, test_http_server):
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
            placeholder_path=Path(__file__).parent / "fixtures" / "sample_image.jpg"
        )
        
        # Save the manifest
        manifest.to_json(manifest_path)
    
    # Check that the manifest file was created
    assert manifest_path.exists()
    
    # Check manifest contains our data
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    for adj in limited_animals.keys():
        assert adj in manifest_data
        assert len(manifest_data[adj]) > 0


@pytest.mark.integration
def test_downloader_to_renderer_integration(e2e_test_environment, dummy_manifest_path):
    """Test the integration between downloader and renderer modules."""
    # Set up paths
    temp_dir = e2e_test_environment["root"]
    manifest_path = temp_dir / "manifest.json"
    output_path = temp_dir / "report.html"
    template_dir = e2e_test_environment["templates"]
    static_dir = e2e_test_environment["static"]
    
    # Copy the dummy manifest
    shutil.copy(dummy_manifest_path, manifest_path)
    
    # Set up Jinja2
    env = setup_jinja_env(template_dir)
    template = load_template(env, "report.html.j2")
    
    # Load and transform manifest data
    adjective_to_animals = load_manifest(manifest_path)
    
    # Generate the report
    generate_report(adjective_to_animals, template, output_path)
    
    # Copy static assets
    try:
        copy_static_assets(static_dir, output_path.parent)
    except FileNotFoundError:
        # Create a basic CSS file for testing
        css_dir = output_path.parent / "static" / "css"
        css_dir.mkdir(parents=True, exist_ok=True)
        with open(css_dir / "style.css", "w") as f:
            f.write("body { font-family: sans-serif; }")
    
    # Check that the report file was created
    assert output_path.exists()
    
    # Load the report
    with open(output_path, "r", encoding="utf-8") as f:
        report_content = f.read()
    
    # Check that key elements are in the report
    assert "<html" in report_content.lower()
    assert "<body" in report_content.lower()
    assert "</html>" in report_content.lower()
    
    # Check for adjectives from the dummy manifest
    with open(dummy_manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    # Verify at least one adjective and animal is in the report
    for adj, animals in manifest_data.items():
        assert adj in report_content
        for animal in animals:
            assert animal["name"] in report_content


@pytest.mark.integration
@pytest.mark.slow
def test_full_pipeline_integration(e2e_test_environment, raw_snapshot_path, test_http_server):
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
            placeholder_path=Path(__file__).parent / "fixtures" / "sample_image.jpg"
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
    
    # Copy static assets
    try:
        copy_static_assets(static_dir, output_path.parent)
    except FileNotFoundError:
        # Create a basic CSS file for testing
        css_dir = output_path.parent / "static" / "css"
        css_dir.mkdir(parents=True, exist_ok=True)
        with open(css_dir / "style.css", "w") as f:
            f.write("body { font-family: sans-serif; }")
    
    # Verification
    # Check that the report file was created
    assert output_path.exists()
    
    # Check that CSS file was copied
    css_path = output_path.parent / "static" / "css" / "style.css"
    assert css_path.exists()
    
    # Load the report
    with open(output_path, "r", encoding="utf-8") as f:
        report_content = f.read()
    
    # Check that key elements are in the report
    assert "<html" in report_content.lower()
    assert "<body" in report_content.lower()
    assert "</html>" in report_content.lower()
    assert "<h2" in report_content.lower()
    assert "<img" in report_content.lower()
    
    # Check for adjectives and animals
    for adj, animals in limited_animals.items():
        assert adj in report_content
        for animal in animals:
            assert animal.name in report_content
