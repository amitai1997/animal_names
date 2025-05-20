# Animal Names Project

A Python application that scrapes Wikipedia's "List of animal names" page, extracts collateral adjectives and their associated animals, downloads images, and generates an HTML report.

## Project Overview

This project walks from concept to delivery in a structured approach:
1. Scrape the Wikipedia page to extract animal-adjective mappings
2. Download images for each animal concurrently
3. Render an HTML report showing adjectives with their associated animals and images
4. Validate with automated tests and continuous integration

## Architecture

The project is organized into several core components:
- `src/scraper.py`: HTML fetching and parsing
- `src/downloader.py`: Threaded image downloads with retry logic
- `src/renderer.py`: HTML/Jinja2 output generation
- `src/cli.py`: Command-line interface

### Core Components

1. **Scraper Component**
   - Fetches HTML from Wikipedia's "List of animal names" page
   - Parses the table to extract collateral adjectives and animal names
   - Handles multiple adjectives per cell and footnotes

2. **Downloader Component**
   - Downloads animal images concurrently using a thread pool
   - Implements retry logic with exponential backoff
   - Creates a manifest of downloaded images

3. **Renderer Component**
   - Generates HTML reports using Jinja2 templates
   - Provides responsive design with mobile-first approach
   - Properly organizes content by collateral adjective

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd animal_names

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.cli --output report.html
```

### CLI Options

```bash
# Basic usage
python -m src.cli --output report.html

# Skip downloading images and use existing ones
python -m src.cli --output report.html --skip-download

# Specify custom directories
python -m src.cli --output report.html \
  --image-dir=./data/images \
  --manifest=./data/manifest.json \
  --html-snapshot=./data/raw_snapshot.html \
  --static-dir=./static \
  --template-dir=./templates

# Configure download parameters
python -m src.cli --output report.html --workers=16 --retries=5

# Control console output
python -m src.cli --output report.html --verbose
```

## Development

### Testing

```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=src --cov-report=term

# Skip tests that require internet
python -m pytest -m "not online"

# Skip slow tests
python -m pytest -m "not slow"
```

### Code Quality

This project follows these quality standards:
- PEP 8 compliant code style (enforced by Flake8)
- Black code formatting with 88 character line limit
- Type annotations for all functions and classes
- Comprehensive test coverage (>90%)

```bash
# Format code
python -m black .

# Run linting
python -m flake8

# Sort imports
python -m isort .
```

## Continuous Integration

This project uses GitHub Actions for continuous integration:
- Automatic testing on each push to main or PR
- Coverage enforcement (minimum 90%)
- Code quality checks (Flake8 linting and Black formatting)

## License

[MIT License](LICENSE)
