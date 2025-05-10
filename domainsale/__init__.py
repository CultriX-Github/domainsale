"""
DomainSale - A secure library for discovering and displaying "for-sale" status of internet domains.

This library implements a secure, production-grade solution for discovering and displaying
"for-sale" status of internet domains using the "_for-sale" TXT record specification.
It addresses critical security issues identified in the RFC draft.
"""

__version__ = '0.1.0'

from .api import get_domain_sale_status
from .exceptions import (
    DomainSaleError,
    DNSSECValidationError,
    SchemaValidationError,
    FieldValidationError,
    SizeExceededError,
    RDAPError,
    TimeoutError
)

__all__ = [
    'get_domain_sale_status',
    'DomainSaleError',
    'DNSSECValidationError',
    'SchemaValidationError',
    'FieldValidationError',
    'SizeExceededError',
    'RDAPError',
    'TimeoutError'
]
