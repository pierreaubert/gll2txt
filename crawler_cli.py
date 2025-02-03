#!/usr/bin/env python3
"""CLI tool for fetching speaker specifications."""

import sys
import asyncio
import argparse
import logging
from typing import Optional
from crawler import SpecificationCrawler, SpecData


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)


def format_spec_value(value: Optional[float], unit: str) -> str:
    """Format a specification value with its unit."""
    if value is None:
        return "N/A"
    return f"{value:.1f} {unit}"


def format_specifications(spec: SpecData) -> str:
    """Format specifications into a readable string."""
    lines = [
        "Speaker Specifications:",
        "-" * 30,
        f"Sensitivity:  {format_spec_value(spec.sensitivity, 'dB')}",
        f"Impedance:    {format_spec_value(spec.impedance, 'Ω')}",
        f"Weight:       {format_spec_value(spec.weight, 'kg')}",
        "Dimensions:",
        f"  Height:     {format_spec_value(spec.height, 'mm')}",
        f"  Width:      {format_spec_value(spec.width, 'mm')}",
        f"  Depth:      {format_spec_value(spec.depth, 'mm')}",
        "",
        f"Source: {spec.source_url}",
    ]
    return "\n".join(lines)


async def fetch_specifications(speaker_name: str, verbose: bool) -> Optional[SpecData]:
    """
    Fetch specifications for a speaker.

    Args:
        speaker_name: Name of the speaker
        verbose: Enable verbose output

    Returns:
        SpecData object if found, None otherwise
    """
    crawler = SpecificationCrawler()
    logger = logging.getLogger(__name__)

    # Search for specifications
    search_query = f"{speaker_name} speaker specifications technical data"
    if verbose:
        logger.debug("Searching for: %s", search_query)

    results = await crawler.search_web(search_query)
    if not results:
        if verbose:
            logger.debug("No search results found")
        return None

    # Try each result until we find valid specifications
    if verbose:
        logger.debug("Found %d potential sources", len(results))

    for i, url in enumerate(results[:3], 1):
        if verbose:
            logger.debug("Trying source %d: %s", i, url)

        content = await crawler.fetch_url_content(url)
        if not content:
            if verbose:
                logger.debug("Failed to fetch content")
            continue

        spec_data = crawler.extract_specifications(content, url)

        # Check if we found any useful specifications
        has_specs = any(
            getattr(spec_data, field) is not None
            for field in [
                "sensitivity",
                "impedance",
                "weight",
                "height",
                "width",
                "depth",
            ]
        )

        if has_specs:
            if verbose:
                logger.debug("Found specifications")
            return spec_data
        elif verbose:
            logger.debug("No specifications found in content")

    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fetch speaker specifications")
    parser.add_argument("speaker_name", help="Name of the speaker to search for")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        spec_data = asyncio.run(fetch_specifications(args.speaker_name, args.verbose))
        if spec_data:
            print(format_specifications(spec_data))
            sys.exit(0)
        else:
            print(
                f"Error: Could not find specifications for '{args.speaker_name}'",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
