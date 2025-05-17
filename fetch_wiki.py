#!/usr/bin/env python3
"""
Script to fetch the Wikipedia 'List of animal names' page 
and save it as raw_snapshot.html.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scraper import fetch_html

def main():
    """Fetch and save the Wikipedia page."""
    # Define paths
    wiki_url = "https://en.wikipedia.org/wiki/List_of_animal_names"
    dest_path = Path('tests/fixtures/raw_snapshot.html')
    
    # Ensure the directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Fetch and save the page
    print(f"Fetching {wiki_url}...")
    fetch_html(wiki_url, dest_path)
    print(f"Saved to {dest_path}")

if __name__ == "__main__":
    main()
