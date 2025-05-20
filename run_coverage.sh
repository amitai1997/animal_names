#!/bin/bash
# Run tests with coverage and generate a report

# Create reports directory if it doesn't exist
mkdir -p reports/coverage

# Run pytest with coverage
.venv/bin/pytest --cov=src --cov-report=xml:reports/coverage.xml --cov-report=html:reports/coverage --junitxml=reports/results.xml $@

# Check if coverage threshold is met
.venv/bin/coverage report --fail-under=90

echo "Coverage report generated in reports/coverage/"
echo "JUnit report generated in reports/results.xml"
