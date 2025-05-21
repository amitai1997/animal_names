"""
HTML report renderer for the animal names project.

This module provides functionality for generating HTML reports using Jinja2 templates
and copying static assets to the output directory.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, Template


def setup_jinja_env(template_dir: Path) -> Environment:
    """
    Set up the Jinja2 environment with the given template directory.

    Args:
        template_dir: Path to the directory containing templates.

    Returns:
        Jinja2 Environment configured with the template directory and strict undefined.
    """
    from jinja2 import StrictUndefined

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,  # Fail fast on undefined variables
    )
    return env


def load_template(env: Environment, name: str) -> Template:
    """
    Load a template from the Jinja2 environment.

    Args:
        env: Jinja2 Environment to load the template from.
        name: Name of the template to load.

    Returns:
        The loaded template.

    Raises:
        jinja2.exceptions.TemplateNotFound: If the template doesn't exist.
    """
    return env.get_template(name)


def generate_report(
    data: Dict[str, List[Dict]], template: Template, output_path: Path
) -> None:
    """
    Generate an HTML report from the given data and template.

    Args:
        data: Dictionary mapping adjectives to lists of animals with their image paths.
        template: Jinja2 template to use for rendering.
        output_path: Path where the rendered HTML should be written.

    Returns:
        None. The report is written to the output_path.
    """
    rendered_html = template.render(adjective_to_animals=data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)


def copy_static_assets(src_dir: Path, dest_dir: Path) -> None:
    """
    Copy static assets from the source directory to the destination directory.

    Args:
        src_dir: Path to the directory containing static assets.
        dest_dir: Path to the directory where static assets should be copied.

    Returns:
        None. The assets are copied to the destination directory.
    """
    import logging

    logger = logging.getLogger(__name__)

    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if source directory exists
    if not src_dir.exists():
        logger.warning(
            f"Static assets directory {src_dir} does not exist, skipping copy"
        )
        return

    dest_static = dest_dir / "static"

    # Prevent deleting source if source and destination are the same
    if src_dir.resolve() == dest_static.resolve():
        logger.warning(
            f"Source and destination static directories are the same ({src_dir}), skipping copy to avoid data loss."
        )
        return

    if dest_static.exists():
        shutil.rmtree(dest_static)

    dest_static.mkdir(parents=True, exist_ok=True)

    for item in src_dir.glob("**/*"):
        if item.is_file():
            rel_path = item.relative_to(src_dir)
            dest_path = dest_static / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_path)


def load_manifest(manifest_path: Path) -> Dict[str, List[Dict]]:
    """
    Load the manifest file and transform it into the format needed for the template.

    Args:
        manifest_path: Path to the manifest.json file.

    Returns:
        Dictionary mapping adjectives to lists of animals with their image paths.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    try:
        # Check if manifest is already in the right format
        if "adjective_to_animals" in manifest:
            return manifest["adjective_to_animals"]
    except (TypeError, KeyError):
        pass

    # The manifest has a format of animal_name -> image_path
    # We need to transform it to adjective -> [{"name": animal_name, "image_path": image_path}, ...]
    # For this, we'll need to use the scraper's parse_table function to get the adjective -> animal mapping
    from src.scraper import parse_table

    # Get the raw_snapshot.html path from the same directory as manifest.json
    html_path = manifest_path.parent / "raw_snapshot.html"

    # Parse the HTML to get the adjective -> animal mapping
    adjective_to_animals = {}

    # Get the adjective -> animal mapping
    adjective_to_animals_raw = parse_table(html_path)

    # Create a map of animal name to adjectives for reverse lookup
    # This helps correctly group animals under the same adjective regardless of HTML structure
    animal_to_adjectives = {}
    for adjective, animals in adjective_to_animals_raw.items():
        for animal in animals:
            animal_name = animal.name
            if animal_name not in animal_to_adjectives:
                animal_to_adjectives[animal_name] = []
            if adjective not in animal_to_adjectives[animal_name]:
                animal_to_adjectives[animal_name].append(adjective)

    # Transform the mapping to properly group animals under each adjective
    for animal_name, adjectives in animal_to_adjectives.items():
        if animal_name in manifest:
            image_path = manifest[animal_name]
            for adjective in adjectives:
                if adjective not in adjective_to_animals:
                    adjective_to_animals[adjective] = []

                # Check if animal is already in the list to avoid duplicates
                if not any(
                    a.get("name") == animal_name
                    for a in adjective_to_animals[adjective]
                ):
                    adjective_to_animals[adjective].append(
                        {"name": animal_name, "image_path": image_path}
                    )

    return adjective_to_animals
