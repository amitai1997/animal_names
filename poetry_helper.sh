#!/bin/bash
# poetry_helper.sh - A script to run Poetry commands for the animal_names project

set -e  # Exit on error

# Define colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$HOME/Documents/animal_names"

# Move to project directory
cd "$PROJECT_DIR"

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[Poetry Helper]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to show usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC} ./poetry_helper.sh <command>"
    echo -e "Available commands:"
    echo -e "  ${GREEN}install${NC}         - Install project dependencies"
    echo -e "  ${GREEN}update${NC}          - Update project dependencies"
    echo -e "  ${GREEN}shell${NC}           - Activate Poetry virtual environment"
    echo -e "  ${GREEN}test${NC}            - Run tests (arguments passed to pytest)"
    echo -e "  ${GREEN}lint${NC}            - Run linters (flake8, black, mypy)"
    echo -e "  ${GREEN}format${NC}          - Format code with black"
    echo -e "  ${GREEN}run${NC}             - Run the CLI with arguments"
    echo -e "  ${GREEN}build${NC}           - Build the project"
    echo -e "  ${GREEN}publish${NC}         - Publish the project"
    echo -e "  ${GREEN}precommit${NC}       - Install pre-commit hooks"
    echo -e "  ${GREEN}check${NC}           - Run pre-commit checks on all files"
    echo -e "  ${GREEN}help${NC}            - Show this help message"
}

# Check if a command was provided
if [ $# -eq 0 ]; then
    print_error "No command provided"
    show_usage
    exit 1
fi

COMMAND=$1
shift  # Remove the first argument, leaving the rest for the command

case "$COMMAND" in
    install)
        print_message "Installing dependencies..."
        python3 -m poetry install
        print_success "Dependencies installed successfully"
        ;;
    update)
        print_message "Updating dependencies..."
        python3 -m poetry update
        print_success "Dependencies updated successfully"
        ;;
    shell)
        print_message "Activating Poetry shell..."
        python3 -m poetry shell
        ;;
    test)
        print_message "Running tests..."
        python3 -m poetry run pytest "$@"
        ;;
    lint)
        print_message "Running linters..."
        print_message "Running flake8..."
        python3 -m poetry run flake8 src tests
        print_message "Running black check..."
        python3 -m poetry run black --check src tests
        print_message "Running mypy..."
        python3 -m poetry run mypy src tests
        print_success "All linters passed"
        ;;
    format)
        print_message "Formatting code with black..."
        python3 -m poetry run black src tests
        print_success "Code formatted successfully"
        ;;
    run)
        print_message "Running CLI..."
        python3 -m poetry run python -m src.cli "$@"
        ;;
    build)
        print_message "Building project..."
        python3 -m poetry build
        print_success "Project built successfully"
        ;;
    publish)
        print_message "Publishing project..."
        python3 -m poetry publish
        print_success "Project published successfully"
        ;;
    precommit)
        print_message "Installing pre-commit hooks..."
        python3 -m poetry run pre-commit install
        print_success "Pre-commit hooks installed successfully"
        ;;
    check)
        print_message "Running pre-commit checks on all files..."
        python3 -m poetry run pre-commit run --all-files
        print_success "Pre-commit checks passed"
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
