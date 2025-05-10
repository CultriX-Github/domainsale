"""
Example script to generate a valid "_for-sale" TXT record.

This script demonstrates how to create a valid "_for-sale" TXT record
for a domain to indicate it's for sale.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a valid '_for-sale' TXT record."
    )
    
    parser.add_argument(
        "--price",
        required=True,
        help="Price in format 'CUR:AMOUNT' (e.g., 'USD:1000')"
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="URL for more information (must be HTTPS)"
    )
    
    parser.add_argument(
        "--contact",
        required=True,
        help="Contact email (will be formatted as mailto:)"
    )
    
    parser.add_argument(
        "--expires",
        help="Expiration date in format 'YYYY-MM-DD' (default: 1 year from now)"
    )
    
    return parser.parse_args()


def validate_price(price):
    """Validate the price format."""
    parts = price.split(":")
    if len(parts) != 2:
        raise ValueError("Price must be in format 'CUR:AMOUNT' (e.g., 'USD:1000')")
    
    currency, amount = parts
    
    # Check currency code (3 uppercase letters)
    if not (len(currency) == 3 and currency.isalpha() and currency.isupper()):
        raise ValueError("Currency code must be 3 uppercase letters (e.g., 'USD')")
    
    # Check amount (numeric)
    try:
        float(amount)
    except ValueError:
        raise ValueError("Amount must be numeric")
    
    return price


def validate_url(url):
    """Validate the URL format."""
    if not url.startswith("https://"):
        raise ValueError("URL must start with 'https://'")
    
    return url


def validate_contact(contact):
    """Validate and format the contact email."""
    # Add mailto: prefix if not present
    if not contact.startswith("mailto:"):
        contact = f"mailto:{contact}"
    
    # Check that there's an email address after mailto:
    if len(contact) <= 7:  # "mailto:" is 7 characters
        raise ValueError("Contact must contain an email address")
    
    return contact


def validate_expires(expires):
    """Validate the expiration date format."""
    if not expires:
        # Default to 1 year from now
        expires = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    else:
        # Check format (YYYY-MM-DD)
        try:
            datetime.strptime(expires, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Expiration date must be in format 'YYYY-MM-DD'")
        
        # Check that the date is in the future
        if datetime.strptime(expires, "%Y-%m-%d").date() <= datetime.now().date():
            raise ValueError("Expiration date must be in the future")
    
    return expires


def main():
    """Generate a valid '_for-sale' TXT record."""
    args = parse_args()
    
    try:
        # Validate and format the inputs
        price = validate_price(args.price)
        url = validate_url(args.url)
        contact = validate_contact(args.contact)
        expires = validate_expires(args.expires)
        
        # Create the record data
        record_data = {
            "v": "1",
            "price": price,
            "url": url,
            "contact": contact,
            "expires": expires
        }
        
        # Convert to JSON
        json_data = json.dumps(record_data, separators=(",", ":"))
        
        # Create the TXT record
        txt_record = f"v=FORSALE1;{json_data}"
        
        # Check the size
        if len(txt_record.encode("utf-8")) > 255:
            raise ValueError("TXT record exceeds maximum size of 255 bytes")
        
        # Print the TXT record
        print("\nGenerated TXT Record:")
        print("-" * 40)
        print(txt_record)
        print("-" * 40)
        
        # Print instructions
        print("\nTo add this TXT record to your domain, use the following settings:")
        print(f"Name: _for-sale.yourdomain.com")
        print(f"Type: TXT")
        print(f"Value: {txt_record}")
        print("\nReplace 'yourdomain.com' with your actual domain name.")
        
        # Print DNS zone file example
        print("\nDNS Zone File Example:")
        print("-" * 40)
        print(f"_for-sale.yourdomain.com. IN TXT \"{txt_record}\"")
        print("-" * 40)
        
        return 0
    
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
