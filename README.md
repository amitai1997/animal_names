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
   - Uses direct Wikipedia URLs from the HTML rather than generating them

2. **Downloader Component**
   - Downloads animal images concurrently using a thread pool
   - Intelligently extracts appropriate images while filtering out Wikipedia icons and small thumbnails
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

# Run the application (basic usage)
python -m src.cli --output report.html
```

### CLI Output

When running the application, each animal with an available image will be shown as a clickable local link to its photo. For example:

```
Adjective: feline
  - <a href="./data/images/cat.jpg">Cat</a>
  - <a href="./data/images/cheetah.jpg">Cheetah</a>
  - <a href="./data/images/cougar.jpg">Cougar</a>
  - <a href="./data/images/bobcat.jpg">Bobcat</a>
  - <a href="./data/images/margay.jpg">Margay</a>
```

If an animal does not have an image, only its name will be shown (without a link).

No additional logs or information will be printed.

Example output:

```
Adjective: Aquatic
  - <a href="./data/images/fish.jpg">Fish</a>
  - <a href="./data/images/dolphin.jpg">Dolphin</a>
  ...
Adjective: Feline
  - <a href="./data/images/cat.jpg">Cat</a>
  - <a href="./data/images/lion.jpg">Lion</a>
  ...
```

## Docker Usage

You can build and run this project using Docker. This ensures a consistent environment and avoids dependency issues.

### Build the Docker Image

```bash
docker build -t animal-names .
```

### Run the CLI to Generate the Report

```bash
docker run --rm -v $(pwd):/app animal-names
```

This will generate `report.html` and a `static/` directory in your project root.

### Opening the Generated Report

After running the Docker command:

```bash
docker run --rm -v $(pwd):/app animal-names
```

the generated `report.html` file will appear in your current working directory on your host machine (not inside the container).
To open it, simply run:

```bash
open report.html
```

on macOS, or double-click the file in your file explorer.

### Run the CLI with Custom Arguments

You can override the default command. For example:

```bash
docker run --rm -v $(pwd):/app animal-names python -m src.cli --output report.html
```

### Run Tests in Docker

```bash
docker run --rm -v $(pwd):/app animal-names python -m pytest
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
