"""
Exceptions for the DomainSale library.
"""


class DomainSaleError(Exception):
    """Base exception for all DomainSale errors."""
    pass


class DNSSECValidationError(DomainSaleError):
    """Raised when DNSSEC validation fails."""
    pass


class SchemaValidationError(DomainSaleError):
    """Raised when the TXT record schema validation fails."""
    pass


class FieldValidationError(DomainSaleError):
    """Raised when a field in the TXT record fails validation."""
    pass


class SizeExceededError(DomainSaleError):
    """Raised when the TXT record exceeds the maximum allowed size."""
    pass


class RDAPError(DomainSaleError):
    """Raised when RDAP lookup fails."""
    pass


class TimeoutError(DomainSaleError):
    """Raised when a DNS or RDAP lookup times out."""
    pass
