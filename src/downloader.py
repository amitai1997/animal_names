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
    logger.info(f"Extracting image URL from {page_url}")

    # Common Wikipedia icons and logos to exclude
    excluded_patterns = [
        "wiki/Special:",
        "Wikipedia-logo",
        "Wiki-logo",
        "wiki-logo",
        "wikimedia-button",
        "Commons-logo",
        "Wikiquote-logo",
        "Wiktionary-logo",
        "Wikibooks-logo",
        "Wikinews-logo",
        "Wikiversity-logo",
        "Wikivoyage-logo",
        "Edit-clear",
        "Question_book",
        "Red_question_icon",
        "Portal-puzzle",
        "Folder_Hexagonal_Icon",
        "Symbol_support_vote",
        "Media_Viewer",
        "Fairytale_bookmark",
        "Video-x-generic",
        "P_vip",
        "Ambox",  # Warning/note icons
        "Icon_",  # Various icon prefixes
        "Broom_icon",
        "Emblem-",
        "/Static",
        "/static",
        "/Pictogram",
        "/pictogram",
        "Special:FilePath",
        "Disambig",
        "Help-",
        "Mediawiki",
        "User_",
        "Speaker_Icon",
        "Magnify-clip",
        "magnify",
        "Information_icon",
        "OOjs_UI_icon",
    ]

    # Minimum size for valid images (avoid tiny icons)
    # We'll be more lenient with dimensions now
    MIN_WIDTH = 50  # Reduced from 80
    MIN_HEIGHT = 50  # Reduced from 80

    try:
        session = get_session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = session.get(page_url, headers=headers, timeout=(5, 10))
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug: count total images on page for logging
        all_images = soup.find_all("img")
        logger.info(f"Page has {len(all_images)} total images")

        # STRATEGY 1: Look for the first image in the infobox - THIS SHOULD BE THE HIGHEST PRIORITY
        infobox = soup.find("table", class_="infobox")
        if infobox:
            img_tags = infobox.find_all("img")
            logger.info(f"Found {len(img_tags)} images in infobox")

            for img_tag in img_tags:
                if "src" in img_tag.attrs:
                    # Check if it's a valid size
                    width = int(img_tag.get("width", 0))
                    height = int(img_tag.get("height", 0))

                    # Log image dimensions for debugging
                    logger.debug(
                        f"Infobox image: {img_tag['src']} (w={width}, h={height})"
                    )

                    # Skip small images (likely icons)
                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        logger.debug(
                            f"Skipping infobox image due to small size: {width}x{height}"
                        )
                        continue

                    img_url = img_tag["src"]
                    img_src_lower = img_url.lower()

                    # Skip excluded patterns
                    if any(
                        pattern.lower() in img_src_lower
                        for pattern in excluded_patterns
                    ):
                        logger.debug(
                            f"Skipping infobox image due to pattern match: {img_url}"
                        )
                        continue

                    # Ensure URL is absolute
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        # Handle root-relative URLs
                        parsed_url = requests.utils.urlparse(page_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        img_url = base_url + img_url
                    logger.info(f"Found valid image URL in infobox: {img_url}")
                    return img_url

        # STRATEGY 2: Look at full-size images in image containers/thumbs
        # This often gets higher quality images than just img tags
        image_containers = []
        image_containers.extend(soup.find_all("div", class_="thumbinner"))
        image_containers.extend(soup.find_all("div", class_="thumb"))
        image_containers.extend(soup.find_all("a", class_="image"))

        logger.info(f"Found {len(image_containers)} image containers")

        for container in image_containers:
            # Look for image inside container
            img_tag = container.find("img")
            if img_tag and "src" in img_tag.attrs:
                width = int(img_tag.get("width", 0))
                height = int(img_tag.get("height", 0))

                # Log image dimensions for debugging
                logger.debug(
                    f"Container image: {img_tag['src']} (w={width}, h={height})"
                )

                # Skip very small images (icons)
                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    logger.debug(
                        f"Skipping container image due to small size: {width}x{height}"
                    )
                    continue

                img_url = img_tag["src"]
                img_src_lower = img_url.lower()

                # Skip excluded patterns
                if any(
                    pattern.lower() in img_src_lower for pattern in excluded_patterns
                ):
                    logger.debug(
                        f"Skipping container image due to pattern match: {img_url}"
                    )
                    continue

                # Ensure URL is absolute
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    parsed_url = requests.utils.urlparse(page_url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    img_url = base_url + img_url

                # Look for larger version (Wikipedia often has thumb URLs)
                # If URL contains /thumb/ directory, we can try to get full version
                if "/thumb/" in img_url:
                    try:
                        # Wikipedia thumbnail URLs typically have format: /thumb/path/to/file/width-filename.ext
                        # To get the full size, we remove the /thumb/ part and the width-filename.ext part
                        parts = img_url.split("/")
                        if len(parts) >= 4:
                            # Remove the last part (width-filename.ext)
                            img_url_full = "/".join(parts[:-1])
                            # Remove the 'thumb' directory
                            img_url_full = img_url_full.replace("/thumb/", "/")
                            logger.info(f"Found full-size image URL: {img_url_full}")
                            return img_url_full
                    except Exception as e:
                        logger.debug(f"Error processing thumb URL: {e}")

                logger.info(f"Found valid image URL in container: {img_url}")
                return img_url

        # STRATEGY 3: Look for the right column/sidebar images
        # (often labeled as 'tright' or 'infobox' classes)
        sidebar_containers = soup.find_all(
            ["div", "td", "table"], class_=["tright", "infobox_v2", "sidebar"]
        )
        for container in sidebar_containers:
            img_tags = container.find_all("img")
            logger.info(f"Found {len(img_tags)} images in sidebar container")

            for img_tag in img_tags:
                if "src" in img_tag.attrs:
                    width = int(img_tag.get("width", 0))
                    height = int(img_tag.get("height", 0))

                    logger.debug(
                        f"Sidebar image: {img_tag['src']} (w={width}, h={height})"
                    )

                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        logger.debug(
                            f"Skipping sidebar image due to small size: {width}x{height}"
                        )
                        continue

                    img_url = img_tag["src"]
                    img_src_lower = img_url.lower()

                    if any(
                        pattern.lower() in img_src_lower
                        for pattern in excluded_patterns
                    ):
                        logger.debug(
                            f"Skipping sidebar image due to pattern match: {img_url}"
                        )
                        continue

                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        parsed_url = requests.utils.urlparse(page_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        img_url = base_url + img_url
                    logger.info(f"Found valid image URL in sidebar: {img_url}")
                    return img_url

        # STRATEGY 4: Look in the lead section (first paragraph) for images
        content_div = soup.find("div", id="mw-content-text")
        if content_div:
            # Find the first few paragraphs
            lead_section = content_div.find_all(
                ["p", "div", "figure"], limit=10
            )  # Increased from 5
            logger.info(f"Scanning {len(lead_section)} lead section elements")

            for element in lead_section:
                img_tags = element.find_all("img")
                for img_tag in img_tags:
                    if "src" in img_tag.attrs:
                        # Check if it's a valid size
                        width = int(img_tag.get("width", 0))
                        height = int(img_tag.get("height", 0))

                        logger.debug(
                            f"Lead section image: {img_tag['src']} (w={width}, h={height})"
                        )

                        # Skip small images (likely icons)
                        if width < MIN_WIDTH or height < MIN_HEIGHT:
                            logger.debug(
                                f"Skipping lead section image due to small size: {width}x{height}"
                            )
                            continue

                        img_url = img_tag["src"]
                        img_src_lower = img_url.lower()

                        # Skip excluded patterns
                        if any(
                            pattern.lower() in img_src_lower
                            for pattern in excluded_patterns
                        ):
                            logger.debug(
                                f"Skipping lead section image due to pattern match: {img_url}"
                            )
                            continue

                        # Ensure URL is absolute
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            # Handle root-relative URLs
                            parsed_url = requests.utils.urlparse(page_url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            img_url = base_url + img_url
                        logger.info(f"Found valid image URL in lead section: {img_url}")
                        return img_url

        # STRATEGY 5: Look for image galleries
        galleries = soup.find_all("div", class_=["thumb", "gallery", "thumbinner"])
        logger.info(f"Found {len(galleries)} gallery elements")

        for gallery in galleries:
            img_tags = gallery.find_all("img")
            for img_tag in img_tags:
                if "src" in img_tag.attrs:
                    # Check if it's a valid size
                    width = int(img_tag.get("width", 0))
                    height = int(img_tag.get("height", 0))

                    logger.debug(
                        f"Gallery image: {img_tag['src']} (w={width}, h={height})"
                    )

                    # Skip small images (likely icons)
                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        logger.debug(
                            f"Skipping gallery image due to small size: {width}x{height})"
                        )
                        continue

                    img_url = img_tag["src"]
                    img_src_lower = img_url.lower()

                    # Skip excluded patterns
                    if any(
                        pattern.lower() in img_src_lower
                        for pattern in excluded_patterns
                    ):
                        logger.debug(
                            f"Skipping gallery image due to pattern match: {img_url}"
                        )
                        continue

                    # Ensure URL is absolute
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        # Handle root-relative URLs
                        parsed_url = requests.utils.urlparse(page_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        img_url = base_url + img_url
                    logger.info(f"Found valid image URL in gallery: {img_url}")
                    return img_url

        # STRATEGY 6: Look for any images in figure or figcaption elements
        figures = soup.find_all(["figure", "figcaption"])
        logger.info(f"Found {len(figures)} figure elements")

        for figure in figures:
            img_tags = figure.find_all("img")
            for img_tag in img_tags:
                if "src" in img_tag.attrs:
                    width = int(img_tag.get("width", 0))
                    height = int(img_tag.get("height", 0))

                    logger.debug(
                        f"Figure image: {img_tag['src']} (w={width}, h={height})"
                    )

                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        logger.debug(
                            f"Skipping figure image due to small size: {width}x{height}"
                        )
                        continue

                    img_url = img_tag["src"]
                    img_src_lower = img_url.lower()

                    if any(
                        pattern.lower() in img_src_lower
                        for pattern in excluded_patterns
                    ):
                        logger.debug(
                            f"Skipping figure image due to pattern match: {img_url}"
                        )
                        continue

                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        parsed_url = requests.utils.urlparse(page_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        img_url = base_url + img_url
                    logger.info(f"Found valid image URL in figure: {img_url}")
                    return img_url

        # STRATEGY 7: Last resort - check any remaining images with sufficient size
        # Be less strict with fallback images
        logger.info("Trying fallback strategy with any large enough images")

        # Collect all images first and sort by size (largest first)
        potential_images = []

        for img_tag in all_images:
            if "src" in img_tag.attrs:
                width = int(img_tag.get("width", 0))
                height = int(img_tag.get("height", 0))
                area = width * height

                # Skip very small images
                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    continue

                img_url = img_tag["src"]
                img_src_lower = img_url.lower()

                # Skip excluded patterns
                if any(
                    pattern.lower() in img_src_lower for pattern in excluded_patterns
                ):
                    continue

                # Add to potential images list with size info for sorting
                potential_images.append((img_url, area, width, height))

        # Sort by area (largest first)
        potential_images.sort(key=lambda x: x[1], reverse=True)

        # Log the top candidates
        for i, (url, area, width, height) in enumerate(potential_images[:5]):
            logger.debug(f"Candidate {i+1}: {url} (w={width}, h={height}, area={area})")

        # Use the largest image if available
        if potential_images:
            img_url = potential_images[0][0]

            # Ensure URL is absolute
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                parsed_url = requests.utils.urlparse(page_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                img_url = base_url + img_url

            logger.info(f"Found valid image URL as fallback: {img_url}")
            return img_url

        # If we get here, we couldn't find any suitable image
        logger.warning(f"No suitable image found for {page_url}")

        # Last-resort option: try Commons category search
        # Extract the animal name from the URL
        animal_name = page_url.split("/")[-1].replace("_", " ")
        logger.info(f"Trying Commons search for '{animal_name}'")

        # Construct a link to Wikimedia Commons search
        commons_url = f"https://commons.wikimedia.org/w/index.php?search={animal_name}&title=Special:MediaSearch&type=image"
        try:
            commons_response = session.get(
                commons_url, headers=headers, timeout=(5, 10)
            )
            commons_response.raise_for_status()
            commons_soup = BeautifulSoup(commons_response.text, "html.parser")

            # Look for search result images
            result_images = commons_soup.find_all("img", class_="sdms-image")
            if result_images and len(result_images) > 0:
                for img in result_images:
                    if "src" in img.attrs:
                        img_url = img["src"]
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url

                        logger.info(f"Found Commons search result image: {img_url}")
                        return img_url
        except Exception as e:
            logger.warning(f"Failed to search Commons: {e}")

        return None

    except requests.RequestException as e:
        logger.error(f"Error fetching image URL from {page_url}: {e}")
        return None
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing image data from {page_url}: {e}")
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
    if not placeholder_path:
        # Try multiple possible locations for the placeholder image
        possible_paths = [
            Path(__file__).parent / "assets" / "placeholder.jpg",
            Path(__file__).parent.parent / "src" / "assets" / "placeholder.jpg",
            Path.cwd() / "src" / "assets" / "placeholder.jpg",
        ]

        # Use the first path that exists
        for path in possible_paths:
            if path.exists():
                placeholder_path = path
                break
        # flake8 E713 false positive workaround: use 'placeholder_path is None'
        if placeholder_path is None:  # noqa: E713
            logger.warning(f"Placeholder image not found in any of: {possible_paths}")

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

    # Make sure we update ALL animal objects across all adjectives
    # This is important since the same animal may appear under multiple adjectives
    animal_paths = {}
    for name, path in manifest_entries.items():
        animal_paths[name] = path

    # Update the original animal objects in the mapping
    for adjective, animals in mapping.items():
        for animal in animals:
            if animal.name in animal_paths:
                animal.image_path = animal_paths[animal.name]

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
