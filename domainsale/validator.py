"""
Validator module for "_for-sale" TXT records.

This module handles schema validation and field validation for "_for-sale" TXT records.
It addresses the critical security issues of Phishing & Malware Delivery and Content Injection / XSS.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import urlparse

from .exceptions import SchemaValidationError, FieldValidationError, SizeExceededError

logger = logging.getLogger(__name__)

# Constants
MAX_TXT_SIZE = 255  # Maximum size in bytes for TXT record content
VERSION_TAG = "v=FORSALE1;"
REQUIRED_FIELDS = ["v", "price", "url", "contact"]
OPTIONAL_FIELDS = ["expires"]
ALLOWED_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS
ALLOWED_URL_SCHEMES = ["https"]
ALLOWED_CONTACT_SCHEMES = ["mailto"]


class ForSaleValidator:
    """
    Validator for "_for-sale" TXT records.
    """

    def __init__(self):
        """Initialize the validator."""
        # Compile regex patterns for field validation
        self.price_pattern = re.compile(r'^[A-Z]{3}:[0-9]+(\.[0-9]{1,2})?$')
        self.date_pattern = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

    def extract_and_validate_record(self, txt_record: str) -> Optional[Dict[str, Any]]:
        """
        Extract and validate a "_for-sale" TXT record.

        Args:
            txt_record: The TXT record content.

        Returns:
            A dictionary containing the validated record fields, or None if the record is invalid.

        Raises:
            SizeExceededError: If the record exceeds the maximum allowed size.
            SchemaValidationError: If the record schema is invalid.
            FieldValidationError: If a field in the record is invalid.
        """
        # Check size limit
        if len(txt_record.encode('utf-8')) > MAX_TXT_SIZE:
            logger.warning(f"TXT record exceeds maximum size of {MAX_TXT_SIZE} bytes")
            raise SizeExceededError(f"TXT record exceeds maximum size of {MAX_TXT_SIZE} bytes")

        # Check for version tag
        if not txt_record.startswith(VERSION_TAG):
            logger.info(f"TXT record does not start with version tag {VERSION_TAG}")
            return None

        # Extract JSON content after version tag
        json_content = txt_record[len(VERSION_TAG):]
        
        try:
            # Parse JSON content
            record = json.loads(json_content)
            
            # Validate record schema
            self._validate_schema(record)
            
            # Validate record fields
            self._validate_fields(record)
            
            return record
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON content: {e}")
            raise SchemaValidationError(f"Failed to parse JSON content: {e}")
        except (SchemaValidationError, FieldValidationError) as e:
            # Re-raise these exceptions
            raise
        except Exception as e:
            logger.error(f"Error validating TXT record: {e}")
            raise SchemaValidationError(f"Error validating TXT record: {e}")

    def _validate_schema(self, record: Dict[str, Any]) -> None:
        """
        Validate the schema of a "_for-sale" TXT record.

        Args:
            record: The record to validate.

        Raises:
            SchemaValidationError: If the record schema is invalid.
        """
        # Check if record is a dictionary
        if not isinstance(record, dict):
            raise SchemaValidationError("Record must be a JSON object")

        # Check for required fields
        for field in REQUIRED_FIELDS:
            if field not in record:
                raise SchemaValidationError(f"Missing required field: {field}")

        # Check for unknown fields
        for field in record:
            if field not in ALLOWED_FIELDS:
                raise SchemaValidationError(f"Unknown field: {field}")

    def _validate_fields(self, record: Dict[str, Any]) -> None:
        """
        Validate the fields of a "_for-sale" TXT record.

        Args:
            record: The record to validate.

        Raises:
            FieldValidationError: If a field in the record is invalid.
        """
        # Validate version field
        if record["v"] != "1":
            raise FieldValidationError(f"Invalid version: {record['v']}")

        # Validate price field
        if not self.price_pattern.match(record["price"]):
            raise FieldValidationError(
                f"Invalid price format: {record['price']}. "
                f"Must be in format 'CUR:AMOUNT' (e.g., 'USD:1000')"
            )

        # Validate URL field
        self._validate_url(record["url"])

        # Validate contact field
        self._validate_contact(record["contact"])

        # Validate expires field if present
        if "expires" in record:
            self._validate_expires(record["expires"])

    def _validate_url(self, url: str) -> None:
        """
        Validate a URL field.

        Args:
            url: The URL to validate.

        Raises:
            FieldValidationError: If the URL is invalid.
        """
        try:
            parsed_url = urlparse(url)
            
            # Check scheme
            if parsed_url.scheme not in ALLOWED_URL_SCHEMES:
                raise FieldValidationError(
                    f"Invalid URL scheme: {parsed_url.scheme}. "
                    f"Must be one of: {', '.join(ALLOWED_URL_SCHEMES)}"
                )
            
            # Check netloc (domain)
            if not parsed_url.netloc:
                raise FieldValidationError("URL must contain a domain")
            
        except Exception as e:
            raise FieldValidationError(f"Invalid URL: {e}")

    def _validate_contact(self, contact: str) -> None:
        """
        Validate a contact field.

        Args:
            contact: The contact to validate.

        Raises:
            FieldValidationError: If the contact is invalid.
        """
        try:
            parsed_contact = urlparse(contact)
            
            # Check scheme
            if parsed_contact.scheme not in ALLOWED_CONTACT_SCHEMES:
                raise FieldValidationError(
                    f"Invalid contact scheme: {parsed_contact.scheme}. "
                    f"Must be one of: {', '.join(ALLOWED_CONTACT_SCHEMES)}"
                )
            
            # For mailto, check that there's an email address
            if parsed_contact.scheme == "mailto" and not parsed_contact.path:
                raise FieldValidationError("mailto: URI must contain an email address")
            
        except Exception as e:
            raise FieldValidationError(f"Invalid contact: {e}")

    def _validate_expires(self, expires: str) -> None:
        """
        Validate an expires field.

        Args:
            expires: The expires date to validate.

        Raises:
            FieldValidationError: If the expires date is invalid.
        """
        # Check format (YYYY-MM-DD)
        if not self.date_pattern.match(expires):
            raise FieldValidationError(
                f"Invalid expires format: {expires}. "
                f"Must be in format 'YYYY-MM-DD'"
            )
        
        try:
            # Parse date
            expire_date = datetime.strptime(expires, "%Y-%m-%d").date()
            
            # Check if date is in the past
            if expire_date < datetime.now().date():
                raise FieldValidationError(f"Expires date is in the past: {expires}")
            
        except ValueError as e:
            raise FieldValidationError(f"Invalid expires date: {e}")
