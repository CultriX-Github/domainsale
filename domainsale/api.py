"""
API module for the DomainSale library.

This module provides the main API interface for the DomainSale library.
It ties together all the other modules to provide a clean, secure interface
for discovering and displaying "for-sale" status of internet domains.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union

from .resolver import DNSSecResolver
from .validator import ForSaleValidator
from .rdap import RDAPClient
from .cache import Cache, cached
from .renderer import HTMLRenderer, ConsoleRenderer
from .exceptions import (
    DomainSaleError,
    DNSSECValidationError,
    SchemaValidationError,
    FieldValidationError,
    SizeExceededError,
    RDAPError,
    TimeoutError
)

logger = logging.getLogger(__name__)

# Default cache TTL in seconds
DEFAULT_CACHE_TTL = 300

# Create cache instances
dns_cache = Cache[Tuple[List[str], List[str]]](ttl=DEFAULT_CACHE_TTL)
rdap_cache = Cache[bool](ttl=DEFAULT_CACHE_TTL)


class DomainSaleOptions:
    """Options for domain sale status lookup."""

    def __init__(
        self,
        enable_rdap_check: bool = False,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        timeout: int = 5
    ):
        """
        Initialize domain sale options.

        Args:
            enable_rdap_check: Whether to check RDAP for "for-sale" status.
            cache_ttl: Time-to-live for cache entries in seconds.
            timeout: Timeout for DNS and RDAP queries in seconds.
        """
        self.enable_rdap_check = enable_rdap_check
        self.cache_ttl = cache_ttl
        self.timeout = timeout


class DomainSaleResponse:
    """Response from domain sale status lookup."""

    def __init__(
        self,
        domain: str,
        for_sale: bool = False,
        price: Optional[str] = None,
        url: Optional[str] = None,
        contact: Optional[str] = None,
        expires: Optional[str] = None,
        source: Union[str, List[str]] = "dns",
        errors: Optional[List[str]] = None
    ):
        """
        Initialize domain sale response.

        Args:
            domain: The domain name.
            for_sale: Whether the domain is for sale.
            price: The price of the domain.
            url: The URL for more information.
            contact: The contact information.
            expires: The expiration date.
            source: The source of the information.
            errors: Any errors that occurred during the lookup.
        """
        self.domain = domain
        self.for_sale = for_sale
        self.price = price
        self.url = url
        self.contact = contact
        self.expires = expires
        self.source = source
        self.errors = errors or []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.

        Returns:
            A dictionary representation of the response.
        """
        return {
            "domain": self.domain,
            "forSale": self.for_sale,
            "price": self.price,
            "url": self.url,
            "contact": self.contact,
            "expires": self.expires,
            "source": self.source,
            "errors": self.errors
        }

    def to_html(self) -> str:
        """
        Convert the response to HTML.

        Returns:
            An HTML representation of the response.
        """
        renderer = HTMLRenderer()
        if self.for_sale:
            return renderer.render_sale_info(self.to_dict())
        elif self.errors:
            return renderer.render_error(", ".join(self.errors))
        else:
            return renderer.render_error(f"Domain {self.domain} is not for sale")

    def to_text(self) -> str:
        """
        Convert the response to plain text.

        Returns:
            A plain text representation of the response.
        """
        renderer = ConsoleRenderer()
        if self.for_sale:
            return renderer.render_sale_info(self.to_dict())
        elif self.errors:
            return renderer.render_error(", ".join(self.errors))
        else:
            return renderer.render_error(f"Domain {self.domain} is not for sale")


def get_domain_sale_status(
    domain: str,
    options: Optional[DomainSaleOptions] = None
) -> DomainSaleResponse:
    """
    Get the sale status of a domain.

    Args:
        domain: The domain name to check.
        options: Options for the lookup.

    Returns:
        A DomainSaleResponse object containing the sale status.
    """
    # Use default options if none provided
    if options is None:
        options = DomainSaleOptions()

    # Update cache TTL if different from default
    if options.cache_ttl != DEFAULT_CACHE_TTL:
        dns_cache.ttl = options.cache_ttl
        rdap_cache.ttl = options.cache_ttl

    # Create response object
    response = DomainSaleResponse(domain=domain)

    try:
        # Create resolver and validator
        resolver = DNSSecResolver(timeout=options.timeout)
        validator = ForSaleValidator()

        # Look up TXT records
        txt_records, sources = _lookup_txt_records(resolver, domain)

        # Process TXT records
        record_data = None
        for txt_record in txt_records:
            try:
                # Extract and validate record
                record_data = validator.extract_and_validate_record(txt_record)
                if record_data:
                    break
            except (SchemaValidationError, FieldValidationError, SizeExceededError) as e:
                response.errors.append(str(e))

        # If no valid record found, return early
        if not record_data:
            return response

        # Check RDAP if enabled
        rdap_for_sale = False
        if options.enable_rdap_check:
            try:
                rdap_client = RDAPClient(timeout=options.timeout)
                rdap_for_sale = _check_rdap_status(rdap_client, domain)
                if rdap_for_sale:
                    sources.append("rdap")
            except (RDAPError, TimeoutError) as e:
                response.errors.append(f"RDAP check failed: {e}")

        # If RDAP check is enabled and fails, domain is not for sale
        if options.enable_rdap_check and not rdap_for_sale:
            return response

        # Domain is for sale
        response.for_sale = True
        response.price = record_data.get("price")
        response.url = record_data.get("url")
        response.contact = record_data.get("contact")
        response.expires = record_data.get("expires")
        response.source = sources

    except DNSSECValidationError as e:
        response.errors.append(f"DNSSEC validation failed: {e}")
    except TimeoutError as e:
        response.errors.append(f"Timeout: {e}")
    except Exception as e:
        response.errors.append(f"Unexpected error: {e}")
        logger.exception(f"Unexpected error checking domain sale status for {domain}")

    return response


@cached(dns_cache, lambda resolver, domain: f"dns:{domain}")
def _lookup_txt_records(
    resolver: DNSSecResolver,
    domain: str
) -> Tuple[List[str], List[str]]:
    """
    Look up TXT records for a domain with caching.

    Args:
        resolver: The DNS resolver to use.
        domain: The domain name to look up.

    Returns:
        A tuple containing a list of TXT record contents and a list of sources.
    """
    return resolver.lookup_for_sale_record(domain)


@cached(rdap_cache, lambda client, domain: f"rdap:{domain}")
def _check_rdap_status(client: RDAPClient, domain: str) -> bool:
    """
    Check RDAP status for a domain with caching.

    Args:
        client: The RDAP client to use.
        domain: The domain name to check.

    Returns:
        True if the domain has a "for-sale" status tag in RDAP, False otherwise.
    """
    return client.check_for_sale_status(domain)
