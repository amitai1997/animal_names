"""
Tests for the manifest loading functionality in the renderer module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.renderer import load_manifest


@pytest.fixture
def manifest_data():
    """Create a sample manifest data dictionary."""
    return {
        "cat": "data/images/cat.jpg",
        "dog": "data/images/dog.jpg",
        "bird": "data/images/bird.jpg",
    }


@pytest.fixture
def adjective_to_animals_data():
    """Create a sample adjective_to_animals data dictionary."""
    return {
        "feline": [{"name": "cat", "image_path": "data/images/cat.jpg"}],
        "canine": [{"name": "dog", "image_path": "data/images/dog.jpg"}],
        "avian": [{"name": "bird", "image_path": "data/images/bird.jpg"}],
    }


@pytest.fixture
def sample_manifest_file(manifest_data):
    """Create a temporary manifest.json file with sample data."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(manifest_data, f)
        manifest_path = Path(f.name)

    yield manifest_path

    # Clean up
    os.unlink(manifest_path)


@pytest.fixture
def sample_adjective_manifest_file(adjective_to_animals_data):
    """Create a temporary manifest.json file with adjective_to_animals format."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"adjective_to_animals": adjective_to_animals_data}, f)
        manifest_path = Path(f.name)

    yield manifest_path

    # Clean up
    os.unlink(manifest_path)


def test_load_manifest_with_adjective_format(
    sample_adjective_manifest_file, adjective_to_animals_data
):
    """Test loading a manifest that is already in the adjective_to_animals format."""
    result = load_manifest(sample_adjective_manifest_file)
    assert result == adjective_to_animals_data


@patch("src.scraper.parse_table")
def test_load_manifest_with_animal_format(
    mock_parse_table, sample_manifest_file, manifest_data
):
    """Test loading a manifest in the animal_name -> image_path format."""
    # Mock the parse_table function to return a sample mapping
    animal1 = MagicMock()
    animal1.name = "cat"
    animal2 = MagicMock()
    animal2.name = "dog"
    animal3 = MagicMock()
    animal3.name = "bird"

    # Create a mock adjective -> animals mapping
    mock_mapping = {"feline": [animal1], "canine": [animal2], "avian": [animal3]}

    mock_parse_table.return_value = mock_mapping

    # Create a dummy html_path that would be in the same directory as the manifest
    with patch("pathlib.Path.exists", return_value=True):
        result = load_manifest(sample_manifest_file)

    # Check that the parse_table function was called with the correct path
    mock_parse_table.assert_called_once()

    # Check that the returned mapping has the correct structure
    assert "feline" in result
    assert "canine" in result
    assert "avian" in result

    # Check that the animal entries have the correct data
    assert result["feline"][0]["name"] == "cat"
    assert result["feline"][0]["image_path"] == "data/images/cat.jpg"
    assert result["canine"][0]["name"] == "dog"
    assert result["canine"][0]["image_path"] == "data/images/dog.jpg"
    assert result["avian"][0]["name"] == "bird"
    assert result["avian"][0]["image_path"] == "data/images/bird.jpg"
