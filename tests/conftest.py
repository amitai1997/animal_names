"""Pytest configuration file."""
import os
import sys
import pytest

# Add the root directory to Python's path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "online: marks tests that require internet connection"
    )
    config.addinivalue_line("markers", "slow: marks tests that are slow to execute")
