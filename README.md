# DomainSale

A secure, production-grade library for discovering and displaying "for-sale" status of internet domains.

## Overview

DomainSale is a Python library that implements a secure solution for discovering and displaying "for-sale" status of internet domains using the "_for-sale" TXT record specification. It addresses critical security issues identified in the RFC draft.

## Features

- **DNS Lookup & DNSSEC Validation**
  - Performs DNS lookup of the TXT record at `_for-sale.<domain>`
  - Enforces strict DNSSEC validation (full chain)
  - Uses dnspython, a modern DNSSEC-capable resolver library

- **Structured Payload Schema**
  - Expects the TXT record content to be exactly one JSON object, no larger than 255 bytes
  - Validates each field strictly (e.g., regex for `CUR:AMOUNT`, ISO date)
  - Rejects records that are missing required fields, contain unknown fields, exceed size limits, or fail JSON parsing

- **RDAP Cross-Check**
  - Provides a configurable option to fetch the domain's RDAP data and verify it includes a `"for-sale"` status tag
  - Gracefully handles domains where RDAP is unavailable or returns no such tag

- **Clean API Interface**
  - Exposes a single entry point (`get_domain_sale_status(domain, options)`) that returns a structured response
  - Provides descriptive error codes for DNS resolution failures, DNSSEC validation errors, schema violations, or expired offers

- **Security & Sanitization**
  - Whitelists URI schemes exactly (`https`, `mailto`)
  - Provides utilities for safe HTML rendering (HTML-escapes all dynamic data)

- **Performance & Abuse Mitigation**
  - Implements an in-process cache with configurable TTL (default 300s) to limit repeated DNS/RDAP queries

- **Extensibility & Modularity**
  - Organized into clear modules: DNS resolver, DNSSEC validator, schema parser, RDAP client, API server, HTML renderer
  - Designed for easy unit testing and mock injection

## Installation

### Using pip

```bash
pip install domainsale
```

### Using Poetry

This project supports Poetry for dependency management and packaging. For detailed instructions on using Poetry with this project, see the [Poetry Guide](POETRY_GUIDE.md).

Quick start:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/yourusername/domainsale.git
cd domainsale

# Install dependencies
poetry install

# Run the CLI
poetry run domainsale example.com
```

### Using Docker

This project can also be run in a Docker container. For detailed instructions on using Docker with this project, see the [Docker Guide](examples/DOCKER_README.md).

Quick start:

```bash
# Build the Docker image
docker build -t domainsale -f examples/Dockerfile .

# Run the CLI
docker run domainsale example.com

# Run with Docker Compose
cd examples
docker-compose up
```

## Usage

### Basic Usage

```python
from domainsale import get_domain_sale_status

# Check if a domain is for sale
response = get_domain_sale_status("example.com")

# Check the sale status
if response.for_sale:
    print(f"Domain is for sale for {response.price}")
    print(f"Contact: {response.contact}")
    print(f"URL: {response.url}")
    if response.expires:
        print(f"Offer expires: {response.expires}")
else:
    print("Domain is not for sale")
    if response.errors:
        print(f"Errors: {', '.join(response.errors)}")
```

### Advanced Usage with Options

```python
from domainsale.api import get_domain_sale_status, DomainSaleOptions

# Create options
options = DomainSaleOptions(
    enable_rdap_check=True,  # Enable RDAP cross-check
    cache_ttl=600,           # Cache TTL in seconds
    timeout=10               # Timeout for DNS and RDAP queries in seconds
)

# Check if a domain is for sale with options
response = get_domain_sale_status("example.com", options)

# Convert response to dictionary
response_dict = response.to_dict()
print(response_dict)

# Convert response to HTML
html = response.to_html()
print(html)

# Convert response to plain text
text = response.to_text()
print(text)
```

### Command-Line Interface

```bash
# Basic usage
domainsale example.com

# Enable RDAP cross-check
domainsale example.com --rdap

# Output as JSON
domainsale example.com --format json

# Output as HTML
domainsale example.com --format html

# Set cache TTL and timeout
domainsale example.com --cache-ttl 600 --timeout 10

# Enable verbose logging
domainsale example.com --verbose
```

## Security Considerations

DomainSale addresses several critical security issues identified in the RFC draft:

1. **Phishing & Malware Delivery**
   - Enforces a strict JSON schema for TXT record content
   - Whitelists URI schemes to prevent malicious links

2. **DNS Cache Poisoning & Spoofing**
   - Enforces strict DNSSEC validation
   - Rejects unsigned or insecure records

3. **Denial-of-Service / Enumeration**
   - Implements caching with configurable TTL
   - Enforces size limits on TXT records

4. **Content Injection / XSS**
   - HTML-escapes all dynamic data
   - Validates and sanitizes all fields

5. **Amplification via Large TXT Records**
   - Enforces a 255-byte size limit on TXT records

## Configuration Options

### DomainSaleOptions

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_rdap_check` | bool | `False` | Whether to check RDAP for "for-sale" status |
| `cache_ttl` | int | `300` | Time-to-live for cache entries in seconds |
| `timeout` | int | `5` | Timeout for DNS and RDAP queries in seconds |

## Response Format

The `get_domain_sale_status` function returns a `DomainSaleResponse` object with the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `domain` | str | The domain name |
| `for_sale` | bool | Whether the domain is for sale |
| `price` | str | The price of the domain (e.g., "USD:1000") |
| `url` | str | The URL for more information |
| `contact` | str | The contact information (e.g., "mailto:owner@example.com") |
| `expires` | str | The expiration date (e.g., "2025-12-31") |
| `source` | str/list | The source of the information (e.g., "dns" or ["dns", "rdap"]) |
| `errors` | list | Any errors that occurred during the lookup |

## License

This project is licensed under the MIT License - see the LICENSE file for details.
