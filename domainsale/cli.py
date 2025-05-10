"""
Command-line interface for the DomainSale library.

This module provides a command-line interface for the DomainSale library.
"""

import argparse
import json
import logging
import sys
from typing import List, Optional

from .api import get_domain_sale_status, DomainSaleOptions


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging for the CLI.

    Args:
        verbose: Whether to enable verbose logging.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Check if a domain is for sale using the _for-sale TXT record."
    )
    
    parser.add_argument(
        "domain",
        help="The domain name to check"
    )
    
    parser.add_argument(
        "--rdap",
        action="store_true",
        help="Enable RDAP cross-check"
    )
    
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=300,
        help="Cache TTL in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout for DNS and RDAP queries in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.

    Returns:
        Exit code.
    """
    parsed_args = parse_args(args)
    
    # Set up logging
    setup_logging(parsed_args.verbose)
    
    # Create options
    options = DomainSaleOptions(
        enable_rdap_check=parsed_args.rdap,
        cache_ttl=parsed_args.cache_ttl,
        timeout=parsed_args.timeout
    )
    
    try:
        # Get domain sale status
        response = get_domain_sale_status(parsed_args.domain, options)
        
        # Output response in the requested format
        if parsed_args.format == "text":
            print(response.to_text())
        elif parsed_args.format == "json":
            print(json.dumps(response.to_dict(), indent=2))
        elif parsed_args.format == "html":
            print(response.to_html())
        
        # Return non-zero exit code if there were errors
        return 1 if response.errors else 0
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
