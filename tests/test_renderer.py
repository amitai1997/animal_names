"""
Unit tests for the renderer module.
"""

import json
import os
from pathlib import Path
import tempfile
import shutil

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from src.renderer import (
    setup_jinja_env,
    load_template,
    generate_report,
    copy_static_assets,
)


@pytest.fixture
def template_dir():
    """Return the path to the test templates directory."""
    return Path(__file__).parent / "templates"


@pytest.fixture
def dummy_data():
    """Return dummy data for testing the renderer."""
    fixture_path = Path(__file__).parent / "fixtures" / "dummy_manifest.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    return data["adjective_to_animals"]


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files and return its path."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Clean up the temporary directory after the test
    shutil.rmtree(temp_dir)


def test_setup_jinja_env(template_dir):
    """Test that the Jinja2 environment is set up correctly."""
    env = setup_jinja_env(template_dir)
    
    # Check that the loader is correctly set up
    assert isinstance(env.loader, FileSystemLoader)
    assert str(template_dir) in env.loader.searchpath
    
    # Check that undefined is set to 'strict'
    assert env.undefined.__name__ == "StrictUndefined"


def test_load_template(template_dir):
    """Test that a template can be loaded from the Jinja2 environment."""
    env = setup_jinja_env(template_dir)
    template = load_template(env, "dummy_report.html.j2")
    
    # Check that the template is loaded correctly
    assert template.name == "dummy_report.html.j2"
    assert template.filename.endswith("dummy_report.html.j2")


def test_generate_report_minimal(template_dir, temp_output_dir, dummy_data):
    """Test generating a report with minimal data - one adjective and one animal."""
    # Create a minimal dataset with just one adjective and one animal
    minimal_data = {"feline": [dummy_data["feline"][0]]}
    
    # Set up the environment and load the template
    env = setup_jinja_env(template_dir)
    template = load_template(env, "dummy_report.html.j2")
    
    # Generate the report
    output_path = temp_output_dir / "report.html"
    generate_report(minimal_data, template, output_path)
    
    # Check that the file exists
    assert output_path.exists()
    
    # Read the file and check its contents
    with open(output_path, "r") as f:
        content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(content, "html.parser")
    
    # Check that the title is correct
    assert soup.title.text == "Test Report"
    
    # Check that there's a link to the CSS
    assert soup.find("link", {"rel": "stylesheet", "href": "static/css/style.css"})
    
    # Check that there's one <h2> for the adjective
    h2s = soup.find_all("h2")
    assert len(h2s) == 1
    assert h2s[0].text == "feline"
    
    # Check that there's one <li> for the animal
    lis = soup.find_all("li")
    assert len(lis) == 1
    
    # Check that the animal name and image are correct
    img = lis[0].find("img")
    assert img["src"] == "data/images/cat.jpg"
    assert img["alt"] == "cat"
    assert lis[0].find("span").text == "cat"


def test_generate_report_multiple_animals(template_dir, temp_output_dir, dummy_data):
    """Test generating a report with multiple animals per adjective."""
    # Use the data for "feline" which has multiple animals
    data = {"feline": dummy_data["feline"]}
    
    # Set up the environment and load the template
    env = setup_jinja_env(template_dir)
    template = load_template(env, "dummy_report.html.j2")
    
    # Generate the report
    output_path = temp_output_dir / "report.html"
    generate_report(data, template, output_path)
    
    # Read the file and parse the HTML
    with open(output_path, "r") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    
    # Check that there's one <h2> for the adjective
    h2s = soup.find_all("h2")
    assert len(h2s) == 1
    
    # Check that there are three <li> elements for the animals
    lis = soup.find_all("li")
    assert len(lis) == 3
    
    # Check that all animal names and images are correct
    animal_names = [li.find("span").text for li in lis]
    assert set(animal_names) == {"cat", "lion", "tiger"}
    
    image_srcs = [li.find("img")["src"] for li in lis]
    assert set(image_srcs) == {
        "data/images/cat.jpg",
        "data/images/lion.jpg",
        "data/images/tiger.jpg"
    }


def test_generate_report_empty_adjective(template_dir, temp_output_dir, dummy_data):
    """Test generating a report with an adjective that has no animals."""
    # Use the data for "empty_adjective" which has no animals
    data = {"empty_adjective": dummy_data["empty_adjective"]}
    
    # Set up the environment and load the template
    env = setup_jinja_env(template_dir)
    template = load_template(env, "dummy_report.html.j2")
    
    # Generate the report
    output_path = temp_output_dir / "report.html"
    generate_report(data, template, output_path)
    
    # Read the file and parse the HTML
    with open(output_path, "r") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    
    # Check that there's one <h2> for the adjective
    h2s = soup.find_all("h2")
    assert len(h2s) == 1
    assert h2s[0].text == "empty_adjective"
    
    # Check that there's a paragraph saying "No animals found"
    p = soup.find("p")
    assert p.text == "No animals found."
    
    # Check that there are no <li> elements
    lis = soup.find_all("li")
    assert len(lis) == 0


def test_copy_static_assets(temp_output_dir):
    """Test copying static assets to the output directory."""
    # Create a temporary directory for static assets
    static_dir = Path(tempfile.mkdtemp())
    try:
        # Create a CSS directory and file
        css_dir = static_dir / "css"
        css_dir.mkdir()
        css_file = css_dir / "style.css"
        with open(css_file, "w") as f:
            f.write("body { color: red; }")
        
        # Copy the static assets
        copy_static_assets(static_dir, temp_output_dir)
        
        # Check that the static directory exists in the output directory
        static_output_dir = temp_output_dir / "static"
        assert static_output_dir.exists()
        
        # Check that the CSS directory and file exist in the static directory
        css_output_dir = static_output_dir / "css"
        assert css_output_dir.exists()
        css_output_file = css_output_dir / "style.css"
        assert css_output_file.exists()
        
        # Check that the CSS file has the correct content
        with open(css_output_file, "r") as f:
            content = f.read()
        assert content == "body { color: red; }"
    
    finally:
        # Clean up the temporary static directory
        shutil.rmtree(static_dir)


def test_copy_static_assets_nonexistent_source(temp_output_dir):
    """Test copying static assets when the source directory doesn't exist."""
    # Create a nonexistent path
    nonexistent_dir = Path("/nonexistent/directory")
    
    # This should not raise an exception, but log a warning
    copy_static_assets(nonexistent_dir, temp_output_dir)
    
    # The static directory should not be created in the output directory
    static_output_dir = temp_output_dir / "static"
    assert not static_output_dir.exists()


def test_copy_static_assets_existing_destination(temp_output_dir):
    """Test copying static assets when the destination already exists."""
    # Create a temporary directory for static assets
    static_dir = Path(tempfile.mkdtemp())
    try:
        # Create a CSS directory and file
        css_dir = static_dir / "css"
        css_dir.mkdir()
        css_file = css_dir / "style.css"
        with open(css_file, "w") as f:
            f.write("body { color: red; }")
        
        # Create an existing static directory in the output directory
        dest_static = temp_output_dir / "static"
        dest_static.mkdir()
        
        # Create a file in the existing static directory
        with open(dest_static / "old.txt", "w") as f:
            f.write("This file should be removed")
        
        # Copy the static assets
        copy_static_assets(static_dir, temp_output_dir)
        
        # Check that the static directory exists in the output directory
        assert dest_static.exists()
        
        # Check that the old file was removed
        assert not (dest_static / "old.txt").exists()
        
        # Check that the CSS directory and file exist in the static directory
        css_output_dir = dest_static / "css"
        assert css_output_dir.exists()
        css_output_file = css_output_dir / "style.css"
        assert css_output_file.exists()
        
        # Check that the CSS file has the correct content
        with open(css_output_file, "r") as f:
            content = f.read()
        assert content == "body { color: red; }"
    
    finally:
        # Clean up the temporary static directory
        shutil.rmtree(static_dir)
