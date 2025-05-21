"""
Tests for the load_manifest function.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.renderer import load_manifest
from src.scraper import Animal


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_load_manifest_with_duplicate_adjectives(temp_dir):
    """Test loading a manifest with animals that share the same collateral adjective."""
    # Create test files
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(
            {
                "Duck": "data/images/duck.jpg",
                "Goose": "data/images/goose.jpg",
                "Mallard": "data/images/mallard.jpg",
            },
            f,
        )

    html_path = temp_dir / "raw_snapshot.html"
    html_content = """
    <!DOCTYPE html>
    <html>
    <body>
      <table class="wikitable">
        <tr>
          <th>Animal</th>
          <th>Collateral adjective</th>
        </tr>
        <tr>
          <td>Duck</td>
          <td>anatine</td>
        </tr>
        <tr>
          <td>Goose</td>
          <td>anatine</td>
        </tr>
        <tr>
          <td>Mallard</td>
          <td>anatine</td>
        </tr>
      </table>
    </body>
    </html>
    """
    with open(html_path, "w") as f:
        f.write(html_content)

    # Mock the parse_table function to return test data
    with patch("src.scraper.parse_table") as mock_parse_table:
        # Create mock Animal objects
        duck = Animal(name="Duck", page_url="https://en.wikipedia.org/wiki/Duck")
        goose = Animal(name="Goose", page_url="https://en.wikipedia.org/wiki/Goose")
        mallard = Animal(
            name="Mallard", page_url="https://en.wikipedia.org/wiki/Mallard"
        )

        # Return a dictionary mapping adjectives to animals
        mock_parse_table.return_value = {"anatine": [duck, goose, mallard]}

        # Load the manifest
        result = load_manifest(manifest_path)

        # Check that all animals are correctly grouped under "anatine"
        assert "anatine" in result
        assert len(result["anatine"]) == 3

        # Verify that each animal has the correct name and image path
        animal_names = [animal["name"] for animal in result["anatine"]]
        assert set(animal_names) == {"Duck", "Goose", "Mallard"}

        # Verify that the image paths are correct
        for animal in result["anatine"]:
            if animal["name"] == "Duck":
                assert animal["image_path"] == "data/images/duck.jpg"
            elif animal["name"] == "Goose":
                assert animal["image_path"] == "data/images/goose.jpg"
            elif animal["name"] == "Mallard":
                assert animal["image_path"] == "data/images/mallard.jpg"
