# Animal Names Project

A Python application that scrapes Wikipedia's "List of animal names" page, extracts collateral adjectives and their associated animals, downloads images, and generates an HTML report.

## Project Overview

This project walks from concept to delivery in a structured approach:
1. Scrape the Wikipedia page to extract animal-adjective mappings
2. Download images for each animal concurrently
3. Render an HTML report showing adjectives with their associated animals and images
4. Validate with automated tests

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd animal_names

# Install dependencies with Poetry
poetry install

# Run the application (when implemented)
poetry run python -m src.cli --output /path/to/report.html
```

## Architecture

The project is organized into several core components:
- `src/scraper.py`: HTML fetching and parsing
- `src/downloader.py`: Threaded image downloads
- `src/renderer.py`: HTML/Jinja2 output generation
- `src/cli.py`: Command-line interface

## Development Setup

```bash
# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Run tests
poetry run pytest

# Run linting and type checking
poetry run flake8 src tests
poetry run mypy src tests
poetry run black src tests
```

## Code Conventions & Quality

This project follows these quality standards:
- **PEP 8** compliant code style, enforced by Flake8
- **Black** code formatting with 88 character line limit
- **Type annotations** for all functions and classes
- **Google-style docstrings** for all public APIs
- **Comprehensive test coverage** (>90%)

## Branching Strategy

We follow a trunk-based development model:
- `main`: Protected branch for stable releases
- Feature branches: Short-lived branches for specific tasks

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

[MIT License](LICENSE)
