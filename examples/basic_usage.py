"""
Basic usage example for the DomainSale library.
"""

from domainsale import get_domain_sale_status
from domainsale.api import DomainSaleOptions


def main():
    """
    Demonstrate basic usage of the DomainSale library.
    """
    # Check if a domain is for sale
    print("Checking if example.nl is for sale...")
    response = get_domain_sale_status("example.nl")
    
    # Print the response as text
    print("\nResponse as text:")
    print(response.to_text())
    
    # Print the response as JSON
    print("\nResponse as JSON:")
    import json
    print(json.dumps(response.to_dict(), indent=2))
    
    # Print the response as HTML
    print("\nResponse as HTML:")
    print(response.to_html())
    
    # Check with RDAP cross-check enabled
    print("\nChecking with RDAP cross-check enabled...")
    options = DomainSaleOptions(enable_rdap_check=True)
    response = get_domain_sale_status("example.nl", options)
    
    # Print the response as text
    print("\nResponse with RDAP as text:")
    print(response.to_text())


if __name__ == "__main__":
    main()
