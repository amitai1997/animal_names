#!/usr/bin/env python
"""
Helper script to run pytest.
Usage: python run_tests.py
"""
import os
import sys
import pytest

if __name__ == "__main__":
    # Add the current directory to the path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run pytest with verbose flag
    result = pytest.main(["-v"])
    
    # Exit with pytest exit code
    sys.exit(result)
