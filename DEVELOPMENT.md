# Development Guide

This document provides detailed information about the development process for the Animal Names project.

## Project Structure

```
animal_names/
├── src/                  # Source code
│   ├── __init__.py      # Package initialization
│   ├── scraper.py       # HTML fetching & parsing
│   ├── downloader.py    # Image downloading (Day 2)
│   ├── renderer.py      # HTML report generation (Day 3)
│   └── cli.py           # Command-line interface
├── tests/               # Test suite
│   ├── __init__.py      # Test package initialization
│   ├── test_scraper.py  # Scraper tests
│   ├── fixtures/        # Test data
│   │   └── sample_table.html  # Sample HTML for testing
├── data/                # Data storage
│   └── images/          # Downloaded images
├── templates/           # HTML templates
├── static/              # Static assets
│   └── css/             # CSS stylesheets
├── pyproject.toml       # Poetry configuration
├── setup.py             # Package setup
├── pytest.ini          # Pytest configuration
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── README.md           # Project documentation
└── CONTRIBUTING.md     # Contribution guidelines
```

## Helper Scripts

To simplify development, we have created several helper scripts:

### 1. Project Management (`/root/project.py`)

This script provides high-level commands for managing the project:

```bash
# Show help
python /root/project.py help

# Run tests
python /root/project.py test

# Run verbose tests
python /root/project.py test -v

# Run tests with a specific keyword
python /root/project.py test -k "normalize"

# Run linting
python /root/project.py lint

# Format code
python /root/project.py format

# Install dependencies
python /root/project.py install

# Install and configure pre-commit hooks
python /root/project.py precommit

# Clean temporary files
python /root/project.py clean
```

### 2. Git Workflow (`/root/git_workflow.py`)

This script simplifies Git operations:

```bash
# Show help
python /root/git_workflow.py help

# Check status
python /root/git_workflow.py status

# Commit changes
python /root/git_workflow.py commit "your commit message"

# Create a new branch
python /root/git_workflow.py create-branch branch-name

# Checkout a branch
python /root/git_workflow.py checkout branch-name

# Push changes
python /root/git_workflow.py push

# Pull changes
python /root/git_workflow.py pull
```

### 3. Day Runner (`/root/day_runner.py`)

This script automates the tasks for each day of the project:

```bash
# Run tasks for a specific day (1-6)
python /root/day_runner.py <day_number>
```

### 4. Test Runner (`/root/run_project_tests.py`)

This script sets up the Python environment and runs tests:

```bash
# Run all tests
python /root/run_project_tests.py
```

### 5. Command in Directory (`/root/run_in_dir.py`)

This utility allows running commands in specific directories:

```bash
# Run a command in a specific directory
python /root/run_in_dir.py /path/to/directory "command to run"
```

## Code Quality & Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. These hooks run automatically before each commit and check:

- Trailing whitespace
- End of file issues
- YAML syntax
- Large file additions
- Python debug statements
- Black code formatting
- Flake8 linting
- MyPy type checking

To set up the pre-commit hooks:

```bash
python /root/project.py precommit
```

Once installed, pre-commit will automatically run these checks when you try to commit changes. If any issues are found, the commit will be aborted and you'll need to fix the issues before committing.

You can also run the hooks manually on all files:

```bash
# Run in virtual environment
/tmp/venv/bin/pre-commit run --all-files
```

## Development Workflow

### Day 1: Scraper Implementation

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day1-feature
   ```

2. Implement the scraper functionality in `src/scraper.py`:
   - `fetch_html(url: str, dest: Path) -> None`
   - `normalize_entry(raw: str) -> str`
   - `parse_table(html_path: Path) -> Dict[str, List[str]]`

3. Run tests:
   ```bash
   python /root/project.py test -v
   ```

4. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

5. Commit changes:
   ```bash
   python /root/git_workflow.py commit "feat(scraper): implement HTML parsing"
   ```

### Day 2: Downloader Implementation

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day2-feature
   ```

2. Implement the downloader functionality in `src/downloader.py`

3. Run tests:
   ```bash
   python /root/project.py test -v
   ```

4. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

5. Commit changes:
   ```bash
   python /root/git_workflow.py commit "feat(downloader): implement image downloading"
   ```

### Day 3: Renderer Implementation

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day3-feature
   ```

2. Implement the renderer functionality in `src/renderer.py`

3. Update CLI module (`src/cli.py`) to integrate scraper, downloader, and renderer

4. Run tests:
   ```bash
   python /root/project.py test -v
   ```

5. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

6. Commit changes:
   ```bash
   python /root/git_workflow.py commit "feat(renderer): implement HTML report generation"
   ```

### Day 4: Comprehensive Testing

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day4-feature
   ```

2. Add comprehensive tests for all components

3. Run tests with coverage:
   ```bash
   python /root/run_project_tests.py
   ```

4. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

5. Commit changes:
   ```bash
   python /root/git_workflow.py commit "test: add comprehensive tests"
   ```

### Day 5: Documentation and Polish

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day5-feature
   ```

2. Update documentation

3. Polish code and fix any remaining issues

4. Run final tests:
   ```bash
   python /root/project.py test -v
   ```

5. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

6. Commit changes:
   ```bash
   python /root/git_workflow.py commit "docs: update documentation"
   ```

### Day 6: Final Packaging

1. Create a feature branch:
   ```bash
   python /root/git_workflow.py create-branch day6-feature
   ```

2. Create distribution package

3. Final testing and verification

4. Format code and check for issues:
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

5. Commit changes:
   ```bash
   python /root/git_workflow.py commit "chore: prepare for release"
   ```

## Troubleshooting

### Common Issues

1. **Import Errors**

   If you encounter import errors when running tests, make sure the project is installed in development mode:
   ```bash
   python /root/project.py install
   ```

2. **Test Failures**

   If tests are failing, check the error messages and fix the issues in the corresponding modules. Then run:
   ```bash
   python /root/project.py test -v
   ```

3. **Pre-commit Hook Failures**

   If pre-commit hooks are failing:
   - Fix formatting issues with `python /root/project.py format`
   - Fix linting issues manually by addressing the reported errors
   - Run `python /root/project.py precommit` to reinstall hooks if needed

4. **Git Issues**

   If you encounter git-related issues, use the git_workflow.py helper:
   ```bash
   python /root/git_workflow.py status
   ```

### Getting Help

If you need further assistance, refer to the following resources:
- README.md for general project information
- CONTRIBUTING.md for contribution guidelines
- This DEVELOPMENT.md for detailed development instructions
