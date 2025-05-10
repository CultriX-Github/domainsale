"""
Unit tests for the validator module.
"""

import unittest
from domainsale.validator import ForSaleValidator
from domainsale.exceptions import SchemaValidationError, FieldValidationError, SizeExceededError


class TestForSaleValidator(unittest.TestCase):
    """Test cases for the ForSaleValidator class."""

    def setUp(self):
        """Set up the test case."""
        self.validator = ForSaleValidator()
        self.valid_record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com"}'
        self.valid_record_with_expires = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com","expires":"2025-12-31"}'

    def test_valid_record(self):
        """Test that a valid record is accepted."""
        record_data = self.validator.extract_and_validate_record(self.valid_record)
        self.assertIsNotNone(record_data)
        self.assertEqual(record_data["v"], "1")
        self.assertEqual(record_data["price"], "USD:1000")
        self.assertEqual(record_data["url"], "https://example.com")
        self.assertEqual(record_data["contact"], "mailto:owner@example.com")

    def test_valid_record_with_expires(self):
        """Test that a valid record with expires is accepted."""
        record_data = self.validator.extract_and_validate_record(self.valid_record_with_expires)
        self.assertIsNotNone(record_data)
        self.assertEqual(record_data["expires"], "2025-12-31")

    def test_missing_version_tag(self):
        """Test that a record without a version tag is rejected."""
        record = '{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com"}'
        record_data = self.validator.extract_and_validate_record(record)
        self.assertIsNone(record_data)

    def test_invalid_json(self):
        """Test that a record with invalid JSON is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com'
        with self.assertRaises(SchemaValidationError):
            self.validator.extract_and_validate_record(record)

    def test_missing_required_field(self):
        """Test that a record missing a required field is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com"}'
        with self.assertRaises(SchemaValidationError):
            self.validator.extract_and_validate_record(record)

    def test_unknown_field(self):
        """Test that a record with an unknown field is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com","foo":"bar"}'
        with self.assertRaises(SchemaValidationError):
            self.validator.extract_and_validate_record(record)

    def test_invalid_version(self):
        """Test that a record with an invalid version is rejected."""
        record = 'v=FORSALE1;{"v":"2","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com"}'
        with self.assertRaises(FieldValidationError):
            self.validator.extract_and_validate_record(record)

    def test_invalid_price_format(self):
        """Test that a record with an invalid price format is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"1000","url":"https://example.com","contact":"mailto:owner@example.com"}'
        with self.assertRaises(FieldValidationError):
            self.validator.extract_and_validate_record(record)

    def test_invalid_url_scheme(self):
        """Test that a record with an invalid URL scheme is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"http://example.com","contact":"mailto:owner@example.com"}'
        with self.assertRaises(FieldValidationError):
            self.validator.extract_and_validate_record(record)

    def test_invalid_contact_scheme(self):
        """Test that a record with an invalid contact scheme is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"tel:+1-555-555-5555"}'
        with self.assertRaises(FieldValidationError):
            self.validator.extract_and_validate_record(record)

    def test_invalid_expires_format(self):
        """Test that a record with an invalid expires format is rejected."""
        record = 'v=FORSALE1;{"v":"1","price":"USD:1000","url":"https://example.com","contact":"mailto:owner@example.com","expires":"2025/12/31"}'
        with self.assertRaises(FieldValidationError):
            self.validator.extract_and_validate_record(record)

    def test_oversized_record(self):
        """Test that an oversized record is rejected."""
        # Create a record that exceeds the maximum size
        large_url = "https://example.com/" + "x" * 1000
        record = f'v=FORSALE1;{{"v":"1","price":"USD:1000","url":"{large_url}","contact":"mailto:owner@example.com"}}'
        with self.assertRaises(SizeExceededError):
            self.validator.extract_and_validate_record(record)


if __name__ == "__main__":
    unittest.main()
