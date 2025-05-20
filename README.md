# Animal Names Project

A Python application that scrapes Wikipedia's "List of animal names" page, extracts collateral adjectives and their associated animals, downloads images, and generates an HTML report.

> **Note**: The mcp-server-text-editor is now properly configured and working!

## Implementation Progress

### Day 4: Testing and Coverage ✅
- Achieved ≥90% code coverage across all source modules
- Added comprehensive unit tests for edge cases in scraper, downloader, and renderer
- Created integration tests for combinations of modules
- Set up CI workflow with coverage enforcement
- Created test fixtures and helper functions for reliable testing
- Added markers for online, slow, and integration tests
- Implemented a coverage reporting system

### Day 3: Renderer Implementation ✅
- Implemented HTML report generation using Jinja2 templates
- Created responsive design with mobile-first approach using CSS Grid/Flexbox
- Designed base and report templates with proper HTML5 semantics
- Added support for copying static assets to the output directory
- Developed test suite for the renderer module
- Integrated the renderer with the CLI interface

### Day 2: Downloader Implementation ✅
- Implemented multithreaded image downloader with retry logic
- Created Animal dataclass to represent animals with page URLs and image paths
- Built a Manifest system to track downloaded images
- Added comprehensive test suite for the downloader module
- Integrated the downloader with the CLI interface

### Day 1: Scraper Implementation ✅
- Implemented `fetch_html` function to download the Wikipedia page
- Created `normalize_entry` to strip HTML tags and normalize text
- Developed `parse_table` to extract adjective→animal mappings
- Wrote comprehensive tests for all edge cases including empty tables
- Established project scaffolding and test infrastructure

## Project Overview

This project walks from concept to delivery in a structured approach:
1. Scrape the Wikipedia page to extract animal-adjective mappings
2. Download images for each animal concurrently
3. Display collateral adjectives and their animals with image links in the console
4. Render an HTML report showing adjectives with their associated animals and images
4. Validate with automated tests

## Architecture

The project is organized into several core components:
- `src/scraper.py`: HTML fetching and parsing
- `src/downloader.py`: Threaded image downloads with retry logic
- `src/renderer.py`: HTML/Jinja2 output generation
- `src/cli.py`: Command-line interface

### Downloader Component (Day 2)

The downloader module provides functionality for downloading animal images concurrently, with retry logic and error handling:

1. `download_images(mapping: Dict[str, List[Animal]], output_dir: Path, workers: int, retries: int) → Manifest`: Downloads images for all animals in the mapping using a thread pool.
2. `extract_image_url(page_url: str) → str`: Extracts the thumbnail image URL from a Wikipedia page.
3. `fetch_with_retries(url: str, dest: Path, retries: int) → bool`: Downloads an image with exponential backoff and retry logic.
4. `slugify(name: str) → str`: Converts animal names to URL/filename-friendly slugs.

Key features of the downloader:
- Multithreaded downloads using ThreadPoolExecutor
- Exponential backoff with random jitter for retries
- Session reuse per thread for connection optimization
- Progress tracking and detailed logging
- Placeholder image substitution for failed downloads
- Manifest generation for tracking downloaded images

### Scraper Component (Day 1)

The scraper module provides three main functions:

1. `fetch_html(url: str, dest: Path) -> None`: Downloads the HTML from the specified URL and saves it to the destination path.
2. `normalize_entry(raw: str) -> str`: Strips HTML tags, normalizes whitespace, and unescapes HTML entities.
3. `parse_table(html_path: Path) -> Dict[str, List[Animal]])`: Parses the "Collateral adjective" table from the HTML file and returns a dictionary mapping adjectives to lists of Animal objects.

The scraper handles various edge cases:
- Multiple adjectives in a single cell (separated by commas or semicolons)
- Footnotes in `<small>` tags
- Merged cells (rowspan/colspan)
- Empty rows or cells

### Renderer Component (Day 3)

The renderer module generates HTML reports showing collateral adjectives and their associated animals with images:

1. `setup_jinja_env(template_dir: Path) -> Environment`: Configures a Jinja2 environment with templates from the specified directory.
2. `load_template(env: Environment, name: str) -> Template`: Loads a specific template from the Jinja2 environment.
3. `generate_report(data: Dict[str, List[Dict]], template: Template, output_path: Path) -> None`: Renders HTML using the template and data.
4. `copy_static_assets(src_dir: Path, dest_dir: Path) -> None`: Copies static assets (CSS, images) to the output directory.
5. `load_manifest(manifest_path: Path) -> Dict[str, List[Dict]]`: Loads the manifest and transforms it into the format needed for the template.

Key features of the renderer:
- Responsive design using CSS Grid and Flexbox
- Mobile-first approach with appropriate breakpoints
- Proper HTML5 semantic elements (section, h2, ul, img)
- External CSS for maintainability
- Jinja2 templates with inheritance for reusable layouts

## Linting and Code Quality

Code quality is enforced through multiple tools:

### Flake8 Configuration

For linting, we use Flake8 with the following configuration in `.flake8`:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, E231, F401, F811, C901, D100, D101, D102, D103, D104, D200, F841, E501, W503, E402
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist,.venv
max-complexity = 20
```

You can run flake8 manually:
```bash
cd ~/Documents/animal_names
.venv/bin/flake8
```

### Pre-commit Configuration

We use pre-commit hooks to enforce code quality with the following checks in `.pre-commit-config.yaml`:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-json
    -   id: debug-statements

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black"]

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black
        language_version: python3

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
```

### Manual Checks

You can also run quality checks manually:

```bash
# For formatting
python -m black .

# For linting
python -m flake8

# For import sorting
python -m isort .

# For type checking
python -m mypy src/ tests/
```

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd animal_names

# Install dependencies with Poetry
poetry install

# Run the application
python -m src.cli --output /path/to/report.html
```

### CLI Options

The command-line interface supports various options:

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
python -m src.cli --output report.html \
  --workers=16 \
  --retries=5

# Control console output
python -m src.cli --output report.html --no-console-output  # Hide adjective-animal console output
python -m src.cli --output report.html --show-logs  # Show detailed logs

# Enable verbose logging
python -m src.cli --output report.html --verbose
```

## Development Setup

### Using Poetry (Recommended)

```bash
# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=term

# Run specific test categories
poetry run pytest -m "not online"  # Skip tests that require internet
poetry run pytest -m "not slow"    # Skip slow tests
poetry run pytest -m integration   # Run only integration tests

# Run the coverage script (creates reports)
./run_coverage.sh

# Run linting and type checking
poetry run flake8 src tests
poetry run mypy src tests
poetry run black src tests

# Install pre-commit hooks
poetry run pre-commit install

# Run pre-commit checks manually
poetry run pre-commit run --all-files
```

### Using Helper Scripts

For convenience, we've provided several helper scripts in the `/root` directory:

```bash
# Run tests
python /root/project.py test

# Run verbose tests
python /root/project.py test -v

# Run linting
python /root/project.py lint

# Format code
python /root/project.py format

# Install dependencies
python /root/project.py install

# Install pre-commit hooks
python /root/project.py precommit

# Run pre-commit checks on all files
python /root/project.py check

# Clean temporary files
python /root/project.py clean
```

Git workflow is also simplified with:

```bash
# Check status
python /root/git_workflow.py status

# Commit changes
python /root/git_workflow.py commit "your commit message"

# Create a new branch
python /root/git_workflow.py create-branch branch-name

# Checkout a branch
python /root/git_workflow.py checkout branch-name
```

Day-specific tasks can be run with:

```bash
# Run tasks for a specific day (1-6)
python /root/day_runner.py <day_number>
```

## Code Quality and Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. These hooks run automatically before each commit and check for:

- Code formatting (Black)
- Linting (Flake8)
- Type checking (MyPy)
- Trailing whitespace
- End of file issues
- And more

To install the pre-commit hooks:

```bash
# Using Poetry
poetry run pre-commit install

# Using helper script
python /root/project.py precommit
```

To manually run the pre-commit checks on all files (without committing):

```bash
# Using Poetry
poetry run pre-commit run --all-files

# Using helper script
python /root/project.py check
```

If you're using empty commits to test the hooks like `git commit --allow-empty`, the hooks may report "no files to check" since no files are staged. Use the `check` command instead to properly test the hooks on all files.

## Code Conventions & Quality

This project follows these quality standards:
- **PEP 8** compliant code style, enforced by Flake8
- **Black** code formatting with 88 character line limit
- **Type annotations** for all functions and classes
- **Google-style docstrings** for all public APIs
- **Comprehensive test coverage** (>90%)

## CI Integration & Code Coverage

This project uses GitHub Actions for continuous integration, with a focus on code quality and testing:

- **Automatic testing**: All tests are run on each push to main or PR
- **Coverage enforcement**: Build fails if coverage falls below 90%
- **Code quality checks**: Flake8 linting and Black formatting verification
- **Reports generation**: Test results and coverage reports are generated and uploaded as artifacts

To run the CI checks locally:

```bash
# Run the full CI suite locally
./run_coverage.sh

# Check code formatting
python -m black --check src tests

# Run linting
python -m flake8 src tests
```

## Branching Strategy

We follow a trunk-based development model:
- `main`: Protected branch for stable releases
- Feature branches: Short-lived branches for specific tasks (e.g., `day1-feature`)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.
See [DEVELOPMENT.md](DEVELOPMENT.md) for more detailed development instructions.

## License

[MIT License](LICENSE)
