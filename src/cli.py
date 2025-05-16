#!/usr/bin/env python
"""
Command-line interface for the animal_names project.
"""
import argparse
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Animal names collateral adjective scraper")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="Path to output HTML report")
    parser.add_argument("--image-dir", type=Path, default=Path("./data/images"),
                        help="Directory to save images (default: ./data/images)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress all output except errors")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of worker threads for downloading images (default: 8)")
    parser.add_argument("--retries", type=int, default=3,
                        help="Number of retry attempts for downloading images (default: 3)")
    return parser.parse_args()

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Ensure output directories exist
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.image_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting animal names scraper")
    
    # TODO: Implement the actual scraping, downloading, and rendering pipeline
    # This will be filled in during Day 1, 2, and 3 implementations
    
    logger.info(f"Report generated at {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
