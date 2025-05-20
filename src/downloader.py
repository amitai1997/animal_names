"""
Image downloader module for the Animal Names project.

This module downloads thumbnail images for animals and manages the download process
with concurrency, retries, and error handling.
"""

import json
import logging
import random
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import local
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from src.scraper import Animal

# Configure logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Thread-local storage for request sessions
thread_local = local()


@dataclass
class Manifest:
    """
    Class representing a manifest of downloaded images.

    Maps animal names to their corresponding local file paths.
    """

    entries: Dict[str, str]

    def to_json(self, path: Path) -> None:
        """
        Save the manifest as a JSON file.

        Args:
            path: Path where the JSON file should be saved.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2)


def get_session() -> requests.Session:
    """
    Get a thread-local session for making HTTP requests.

    Returns:
        A requests.Session object unique to the current thread.
    """
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def slugify(name: str) -> str:
    """
    Convert a string to a slug format suitable for filenames.

    Args:
        name: The string to convert to slug format.

    Returns:
        A lowercase string with spaces replaced by hyphens and
        special characters removed.
    """
    # Convert to lowercase
    slug = name.lower()

    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")

    # Remove invalid characters (only keep alphanumeric, hyphen, and underscore)
    slug = re.sub(r"[^a-z0-9\-_]", "", slug)

    # Remove duplicate hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def extract_image_url(page_url: str) -> Optional[str]:
    """
    Extract the thumbnail image URL from a Wikipedia page.

    Args:
        page_url: URL of the Wikipedia page for the animal.

    Returns:
        URL of the thumbnail image or None if no image was found.
    """
    logger.debug(f"Extracting image URL from {page_url}")

    try:
        session = get_session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = session.get(page_url, headers=headers, timeout=(5, 10))
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for the first image in the infobox
        infobox = soup.find("table", class_="infobox")
        if infobox:
            img_tag = infobox.find("img")
            if img_tag and "src" in img_tag.attrs:
                img_url = img_tag["src"]
                # Ensure URL is absolute
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    # Handle root-relative URLs
                    parsed_url = requests.utils.urlparse(page_url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    img_url = base_url + img_url
                logger.debug(f"Found image URL in infobox: {img_url}")
                return img_url

        # Fallback: look for the first image in the article
        first_img = soup.find("img")
        if first_img and "src" in first_img.attrs:
            img_url = first_img["src"]
            # Ensure URL is absolute
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                # Handle root-relative URLs
                parsed_url = requests.utils.urlparse(page_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                img_url = base_url + img_url
            logger.debug(f"Found first image URL in article: {img_url}")
            return img_url

        logger.warning(f"No image found for {page_url}")
        return None

    except requests.RequestException as e:
        logger.error(f"Error fetching image URL from {page_url}: {e}")
        return None


def fetch_with_retries(url: str, dest: Path, retries: int = 3) -> bool:
    """
    Download an image from URL to destination with retries and exponential backoff.

    Args:
        url: URL of the image to download.
        dest: Path where the image should be saved.
        retries: Maximum number of retry attempts (default: 3).

    Returns:
        True if the download was successful, False otherwise.
    """
    if not url:
        logger.warning(f"No URL provided for {dest.stem}")
        return False

    session = get_session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Ensure directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Base delay for exponential backoff (in seconds)
    base_delay = 0.5

    for attempt in range(retries):
        try:
            # Add jitter to avoid rate limits (between 50-150ms)
            jitter = random.uniform(0.05, 0.15)
            if attempt > 0:
                time.sleep(base_delay * (2 ** (attempt - 1)) + jitter)

            response = session.get(url, headers=headers, timeout=(5, 10), stream=True)

            # Skip large files (>5MB)
            content_length = response.headers.get("Content-Length")
            if (
                content_length
                and isinstance(content_length, str)
                and int(content_length) > 5 * 1024 * 1024
            ):
                logger.warning(f"Skipping large file ({content_length} bytes): {url}")
                return False

            # Handle 4xx errors - we don't retry these
            if 400 <= response.status_code < 500:
                logger.warning(f"Client error ({response.status_code}) for {url}")
                return False

            # Handle 5xx errors - we retry these
            if 500 <= response.status_code < 600:
                logger.warning(
                    f"Server error ({response.status_code}) for {url}, attempt {attempt+1}/{retries}"
                )
                continue

            # If we got here, the response is successful
            response.raise_for_status()

            # Save the file
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Successfully downloaded {url} to {dest}")
            return True

        except requests.RequestException as e:
            logger.warning(
                f"Error downloading {url} (attempt {attempt+1}/{retries}): {e}"
            )

    # If we get here, all retry attempts have failed
    logger.error(f"Failed to download {url} after {retries} attempts")
    return False


def download_images(
    mapping: Dict[str, List[Animal]],
    output_dir: Path,
    workers: int = 8,
    retries: int = 3,
    placeholder_path: Optional[Path] = None,
) -> Manifest:
    """
    Download images for all animals in the mapping using a thread pool.

    Args:
        mapping: Dictionary mapping adjectives to lists of Animal objects.
        output_dir: Directory where images should be saved.
        workers: Number of concurrent download workers (default: 8).
        retries: Maximum number of retry attempts per download (default: 3).
        placeholder_path: Path to the placeholder image for failed downloads.

    Returns:
        Manifest object mapping animal names to their local image paths.
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check disk space (require at least 100MB free)
    try:
        import shutil

        disk_usage = shutil.disk_usage(output_dir)
        free_space_mb = disk_usage.free / (1024 * 1024)
        if free_space_mb < 100:
            logger.warning(f"Low disk space: {free_space_mb:.2f}MB free")
            if free_space_mb < 10:  # Critical threshold
                logger.error("Critical disk space shortage, aborting download")
                raise OSError(f"Insufficient disk space: {free_space_mb:.2f}MB free")
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")

    # Prepare placeholder path
    if placeholder_path is None:
        placeholder_path = Path(__file__).parent / "assets" / "placeholder.jpg"
        if not placeholder_path.exists():
            logger.warning(f"Placeholder image not found at {placeholder_path}")

    # Flatten the mapping to get a list of all animals
    all_animals = []
    for adjective, animals in mapping.items():
        all_animals.extend(animals)

    # Remove duplicates by name
    unique_animals = {}
    for animal in all_animals:
        if animal.name not in unique_animals:
            unique_animals[animal.name] = animal
    unique_animals = list(unique_animals.values())

    logger.info(
        f"Starting download of {len(unique_animals)} unique animal images using {workers} workers"
    )

    # Function to download a single animal image
    def download_animal_image(animal: Animal) -> tuple[str, Optional[str]]:
        name = animal.name
        slug = slugify(name)
        image_path = output_dir / f"{slug}.jpg"

        # Skip if the image already exists
        if image_path.exists():
            logger.debug(f"Image for {name} already exists at {image_path}")
            relative_path = str(image_path)
            animal.image_path = relative_path
            return name, relative_path

        # Extract image URL from the Wikipedia page
        image_url = extract_image_url(animal.page_url) if animal.page_url else None

        # Try to download the image
        if image_url and fetch_with_retries(image_url, image_path, retries):
            relative_path = str(image_path)
            animal.image_path = relative_path
            return name, relative_path

        # Use placeholder for failed downloads
        if placeholder_path and placeholder_path.exists():
            logger.warning(f"Using placeholder image for {name}")
            shutil.copy(placeholder_path, image_path)
            relative_path = str(image_path)
            animal.image_path = relative_path
            return name, relative_path

        logger.error(
            f"Failed to download image for {name} and no placeholder available"
        )
        return name, None

    # Create a manifest to store image paths
    manifest_entries = {}

    # Download images in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(download_animal_image, unique_animals))

        # Process results and update the manifest
        for name, path in results:
            if path:
                manifest_entries[name] = path

    # Update the original animal objects in the mapping
    for adjective, animals in mapping.items():
        for animal in animals:
            if animal.name in manifest_entries:
                animal.image_path = manifest_entries[animal.name]

    # Create and return manifest
    manifest = Manifest(entries=manifest_entries)

    # Count successful and failed downloads
    success_count = len([p for p in manifest_entries.values() if p])
    total_count = len(unique_animals)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0

    logger.info(
        f"Image download complete: {success_count}/{total_count} successful ({success_rate:.1f}%)"
    )

    return manifest
