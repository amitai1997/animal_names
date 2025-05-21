"""
Tests for the downloader module.
"""

import json
import shutil
import time
from pathlib import Path
from unittest import mock

import pytest
import requests

from src.downloader import (
    Manifest,
    download_images,
    extract_image_url,
    fetch_with_retries,
    slugify,
)
from src.scraper import Animal


@pytest.fixture
def temp_image_dir(tmp_path):
    """Create and return a temporary directory for image downloads."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    yield image_dir
    # Cleanup
    shutil.rmtree(image_dir, ignore_errors=True)


@pytest.fixture
def sample_image_path():
    """Path to the sample image for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    image_path = fixtures_dir / "sample_image.jpg"

    # Create a sample image if it doesn't exist
    if not image_path.exists():
        image_path.parent.mkdir(parents=True, exist_ok=True)
        with open(image_path, "wb") as f:
            # Write a minimal valid JPEG
            f.write(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13\"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9"
            )

    return image_path


@pytest.fixture
def placeholder_image_path():
    """Path to the placeholder image."""
    return Path(__file__).parent.parent / "src" / "assets" / "placeholder.jpg"


@pytest.fixture
def mock_responses():
    """Mock responses for testing."""
    return {
        "success": mock.Mock(
            status_code=200,
            raise_for_status=mock.Mock(),
            content=b"test image content",
            headers={"Content-Length": "100"},
            iter_content=mock.Mock(return_value=[b"test image content"]),
        ),
        "large_file": mock.Mock(
            status_code=200,
            headers={"Content-Length": str(6 * 1024 * 1024)},  # 6MB
        ),
        "not_found": mock.Mock(
            status_code=404,
            raise_for_status=mock.Mock(side_effect=requests.HTTPError("404 Not Found")),
        ),
        "server_error": mock.Mock(
            status_code=500,
            raise_for_status=mock.Mock(
                side_effect=requests.HTTPError("500 Server Error")
            ),
        ),
        "timeout": mock.Mock(
            side_effect=requests.Timeout("Connection timed out"),
        ),
    }


def test_slugify():
    """Test the slugify function with various inputs."""
    assert slugify("Cat") == "cat"
    assert slugify("domestic cat") == "domestic-cat"
    assert slugify("African elephant") == "african-elephant"
    assert slugify("Dog (wild)") == "dog-wild"
    assert slugify("  Spaces  ") == "spaces"
    assert slugify("Special !@#$%^&*() Characters") == "special-characters"
    assert slugify("Multiple--Hyphens") == "multiple-hyphens"
    assert slugify("-Leading-and-trailing-") == "leading-and-trailing"
    assert slugify("Underscore_Test") == "underscore_test"


@mock.patch("src.downloader.get_session")
def test_extract_image_url(mock_get_session, mock_responses):
    """Test extracting image URLs from Wikipedia pages."""
    # Setup mock response with infobox image
    mock_response_with_infobox = mock.Mock()
    mock_response_with_infobox.text = """
    <html>
        <body>
            <table class="infobox">
                <tr>
                    <td><img src="//example.com/cat.jpg" alt="Cat"></td>
                </tr>
            </table>
        </body>
    </html>
    """
    mock_response_with_infobox.raise_for_status = mock.Mock()

    # Setup mock response with only article image
    mock_response_with_article_image = mock.Mock()
    mock_response_with_article_image.text = """
    <html>
        <body>
            <p>Some text</p>
            <img src="//example.com/dog.jpg" alt="Dog">
        </body>
    </html>
    """
    mock_response_with_article_image.raise_for_status = mock.Mock()

    # Setup mock response with no image
    mock_response_no_image = mock.Mock()
    mock_response_no_image.text = """
    <html>
        <body>
            <p>Some text with no images</p>
        </body>
    </html>
    """
    mock_response_no_image.raise_for_status = mock.Mock()

    # Setup mock session
    mock_session = mock.Mock()
    mock_get_session.return_value = mock_session

    # Test infobox image extraction
    mock_session.get.return_value = mock_response_with_infobox
    assert (
        extract_image_url("https://en.wikipedia.org/wiki/Cat")
        == "https://example.com/cat.jpg"
    )

    # Test article image extraction
    mock_session.get.return_value = mock_response_with_article_image
    assert (
        extract_image_url("https://en.wikipedia.org/wiki/Dog")
        == "https://example.com/dog.jpg"
    )

    # Test no image found
    mock_session.get.return_value = mock_response_no_image
    assert extract_image_url("https://en.wikipedia.org/wiki/NoImage") is None

    # Test exception handling
    mock_session.get.side_effect = requests.RequestException("Error")
    assert extract_image_url("https://en.wikipedia.org/wiki/Error") is None


@mock.patch("src.downloader.get_session")
def test_fetch_with_retries_success(mock_get_session, mock_responses, temp_image_dir):
    """Test successful image download."""
    mock_session = mock.Mock()
    mock_session.get.return_value = mock_responses["success"]
    mock_get_session.return_value = mock_session

    dest_path = temp_image_dir / "test_image.jpg"
    assert fetch_with_retries("https://example.com/image.jpg", dest_path)
    assert dest_path.exists()

    # Verify session was called correctly
    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == "https://example.com/image.jpg"


@mock.patch("src.downloader.get_session")
def test_fetch_with_retries_large_file(
    mock_get_session, mock_responses, temp_image_dir
):
    """Test skipping large files."""
    mock_session = mock.Mock()
    mock_session.get.return_value = mock_responses["large_file"]
    mock_get_session.return_value = mock_session

    dest_path = temp_image_dir / "large_image.jpg"
    assert not fetch_with_retries("https://example.com/large_image.jpg", dest_path)
    assert not dest_path.exists()


@mock.patch("src.downloader.get_session")
def test_fetch_with_retries_not_found(mock_get_session, mock_responses, temp_image_dir):
    """Test handling 404 errors."""
    mock_session = mock.Mock()
    mock_session.get.return_value = mock_responses["not_found"]
    mock_get_session.return_value = mock_session

    dest_path = temp_image_dir / "not_found.jpg"
    assert not fetch_with_retries("https://example.com/not_found.jpg", dest_path)
    assert not dest_path.exists()


@mock.patch("src.downloader.get_session")
def test_fetch_with_retries_server_error(
    mock_get_session, mock_responses, temp_image_dir
):
    """Test retrying on server errors."""
    mock_session = mock.Mock()
    # First two calls return server error, third one succeeds
    mock_session.get.side_effect = [
        mock_responses["server_error"],
        mock_responses["server_error"],
        mock_responses["success"],
    ]
    mock_get_session.return_value = mock_session

    dest_path = temp_image_dir / "retry_success.jpg"

    # Mock sleep to avoid waiting
    with mock.patch("time.sleep"):
        assert fetch_with_retries("https://example.com/retry_success.jpg", dest_path)

    assert dest_path.exists()
    assert mock_session.get.call_count == 3


@mock.patch("src.downloader.get_session")
def test_fetch_with_retries_persistent_error(
    mock_get_session, mock_responses, temp_image_dir
):
    """Test exhausting all retries."""
    mock_session = mock.Mock()
    mock_session.get.side_effect = [
        mock_responses["server_error"],
        mock_responses["server_error"],
        mock_responses["server_error"],
    ]
    mock_get_session.return_value = mock_session

    dest_path = temp_image_dir / "all_retries_failed.jpg"

    # Mock sleep to avoid waiting
    with mock.patch("time.sleep"):
        assert not fetch_with_retries(
            "https://example.com/all_retries_failed.jpg", dest_path
        )

    assert not dest_path.exists()
    assert mock_session.get.call_count == 3


@mock.patch("src.downloader.extract_image_url")
@mock.patch("src.downloader.fetch_with_retries")
def test_download_images(
    mock_fetch_with_retries,
    mock_extract_image_url,
    temp_image_dir,
    sample_image_path,
    placeholder_image_path,
):
    """Test downloading images for a set of animals."""
    # Setup mock responses
    mock_extract_image_url.side_effect = [
        "https://example.com/cat.jpg",  # Success
        "https://example.com/dog.jpg",  # Success
        None,  # No image found
        "https://example.com/timeout.jpg",  # Will fail
    ]

    mock_fetch_with_retries.side_effect = [
        True,  # Cat - success
        True,  # Dog - success
        False,  # Elephant - fail (no URL)
        False,  # Tiger - fail (timeout)
    ]

    # Create test data
    animals = {
        "feline": [Animal(name="Cat", page_url="https://en.wikipedia.org/wiki/Cat")],
        "canine": [Animal(name="Dog", page_url="https://en.wikipedia.org/wiki/Dog")],
        "elephantine": [
            Animal(name="Elephant", page_url="https://en.wikipedia.org/wiki/Elephant")
        ],
        "tigrine": [
            Animal(name="Tiger", page_url="https://en.wikipedia.org/wiki/Tiger")
        ],
    }

    # Run download_images function
    manifest = download_images(
        animals,
        temp_image_dir,
        workers=2,
        retries=2,
        placeholder_path=sample_image_path,
    )

    # Check the manifest
    assert isinstance(manifest, Manifest)
    assert len(manifest.entries) == 4  # All animals, successful or with placeholder

    # Check that image paths were updated in the original animals
    assert animals["feline"][0].image_path is not None
    assert animals["canine"][0].image_path is not None
    assert animals["elephantine"][0].image_path is not None
    assert animals["tigrine"][0].image_path is not None

    # Save manifest to disk and verify
    manifest_path = temp_image_dir / "manifest.json"
    manifest.to_json(manifest_path)
    assert manifest_path.exists()

    # Verify manifest content
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    assert "Cat" in manifest_data
    assert "Dog" in manifest_data
    assert "Elephant" in manifest_data
    assert "Tiger" in manifest_data


@pytest.mark.online
def test_downloader_integration():
    """
    Integration test making actual network requests.

    This test is marked with 'online' and will be skipped by default.
    Run with: pytest -m online
    """
    # Use a temporary directory
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)

    try:
        # Create test data with real Wikipedia URLs
        animals = {
            "feline": [
                Animal(name="Cat", page_url="https://en.wikipedia.org/wiki/Cat")
            ],
        }

        # Run download_images with just one animal to avoid rate limiting
        manifest = download_images(animals, temp_dir, workers=1, retries=1)

        # Just basic checks to ensure it doesn't error
        assert isinstance(manifest, Manifest)
        assert len(manifest.entries) > 0
        assert "Cat" in manifest.entries

        # Verify the image exists
        image_path = Path(manifest.entries["Cat"])
        assert image_path.exists()
        assert image_path.stat().st_size > 0

    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@mock.patch("src.downloader.extract_image_url")
@mock.patch("src.downloader.fetch_with_retries")
def test_download_images_duplicate_animals(
    mock_fetch_with_retries,
    mock_extract_image_url,
    temp_image_dir,
    sample_image_path,
):
    """Test downloading images for animals that appear under multiple adjectives."""
    # Setup mock responses
    mock_extract_image_url.side_effect = [
        "https://example.com/shark.jpg",  # Success
    ]

    mock_fetch_with_retries.side_effect = [True]  # Shark - success

    # Create test data with the same animal (Shark) under multiple adjectives
    animals = {
        "squaloid": [
            Animal(name="Shark", page_url="https://en.wikipedia.org/wiki/Shark")
        ],
        "selachian": [
            Animal(name="Shark", page_url="https://en.wikipedia.org/wiki/Shark")
        ],
    }

    # Run download_images function
    manifest = download_images(
        animals,
        temp_image_dir,
        workers=1,
        retries=1,
        placeholder_path=sample_image_path,
    )

    # Check the manifest
    assert isinstance(manifest, Manifest)
    assert len(manifest.entries) == 1  # Just the shark
    assert "Shark" in manifest.entries

    # THIS IS THE KEY TEST: Check that image paths were updated in BOTH instances
    # of the Shark animal
    assert animals["squaloid"][0].image_path is not None
    assert animals["selachian"][0].image_path is not None

    # Both instances should have the same image path
    assert animals["squaloid"][0].image_path == animals["selachian"][0].image_path
