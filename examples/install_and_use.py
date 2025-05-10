"""
Example script demonstrating how to install and use the DomainSale package.

This script shows how to install the package from GitHub or PyPI and use it
to check if a domain is for sale.
"""

import subprocess
import sys


def install_from_github():
    """Install the package from GitHub."""
    print("Installing DomainSale from GitHub...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "git+https://github.com/yourusername/domainsale.git"
    ])
    print("Installation complete!")


def install_from_pypi():
    """Install the package from PyPI."""
    print("Installing DomainSale from PyPI...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "domainsale"
    ])
    print("Installation complete!")


def check_domain(domain):
    """Check if a domain is for sale."""
    # Import the package after installation
    from domainsale import get_domain_sale_status
    from domainsale.api import DomainSaleOptions
    
    print(f"\nChecking if {domain} is for sale...")
    
    # Create options
    options = DomainSaleOptions(
        enable_rdap_check=True,  # Enable RDAP cross-check
        cache_ttl=300,           # Cache TTL in seconds
        timeout=10               # Timeout for DNS and RDAP queries in seconds
    )
    
    # Check if the domain is for sale
    response = get_domain_sale_status(domain, options)
    
    # Print the response
    print("\nResponse as text:")
    print(response.to_text())
    
    # Print the response as JSON
    print("\nResponse as JSON:")
    import json
    print(json.dumps(response.to_dict(), indent=2))
    
    return response


def main():
    """Main function."""
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(
        description="Install and use the DomainSale package."
    )
    
    parser.add_argument(
        "--source",
        choices=["github", "pypi"],
        default="github",
        help="Source to install from (default: github)"
    )
    
    parser.add_argument(
        "--domain",
        default="example.com",
        help="Domain to check (default: example.com)"
    )
    
    args = parser.parse_args()
    
    # Install the package
    if args.source == "github":
        install_from_github()
    else:
        install_from_pypi()
    
    # Check the domain
    check_domain(args.domain)


if __name__ == "__main__":
    main()
