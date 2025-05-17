#!/usr/bin/env python3
"""
Demo script to parse the raw Wikipedia snapshot and display sample results.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scraper import parse_table

def main():
    """Parse the raw snapshot and display sample results."""
    # Define path to raw snapshot
    snapshot_path = Path('tests/fixtures/raw_snapshot.html')
    
    # Parse the table
    print(f"Parsing table from {snapshot_path}...")
    mapping = parse_table(snapshot_path)
    
    # Print statistics
    print(f"Found {len(mapping)} unique adjectives")
    total_animals = sum(len(animals) for animals in mapping.values())
    print(f"Found {total_animals} animal entries")
    
    # Print a few sample mappings
    print("\nSample mappings:")
    sample_adjectives = list(mapping.keys())[:5]  # Take first 5 adjectives
    for adj in sample_adjectives:
        print(f"- {adj}: {', '.join(mapping[adj])}")
    
    # Find adjectives with the most animals
    print("\nAdjectives with the most animals:")
    top_adjectives = sorted(mapping.items(), key=lambda x: len(x[1]), reverse=True)[:3]
    for adj, animals in top_adjectives:
        print(f"- {adj}: {len(animals)} animals")

if __name__ == "__main__":
    main()
