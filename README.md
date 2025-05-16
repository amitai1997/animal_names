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

# Install dependencies
pip install -r requirements.txt

# Run the application (when implemented)
python -m animal_names.cli --output /path/to/report.html
```

## Architecture

The project is organized into several core components:
- `src/scraper.py`: HTML fetching and parsing
- `src/downloader.py`: Threaded image downloads
- `src/renderer.py`: HTML/Jinja2 output generation
- `src/cli.py`: Command-line interface

## Development Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (when implemented)
pytest
```

## License

[MIT License](LICENSE)
