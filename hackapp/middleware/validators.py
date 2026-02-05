"""
Validators
Security and medical data validation
"""

import re
from typing import List, Optional
from .models import ValidationResult, ICD10Code


class ICD10Validator:
    """Validates ICD-10 diagnosis codes"""

    # ICD-10 format: Letter + 2 digits + optional (dot + 1-4 alphanumeric)
    # Examples: J18, J18.9, S06.0X0A
    PATTERN = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')

    def __init__(self, catalog: Optional[dict] = None):
        """
        Initialize validator

        Args:
            catalog: Optional ICD-10 catalog for existence checks
        """
        self.catalog = catalog or {}

    def validate_format(self, code: str) -> ValidationResult:
        """
        Validate ICD-10 code format only

        Args:
            code: ICD-10 code to validate

        Returns:
            ValidationResult with validation status
        """
        code = code.upper().strip()

        if not self.PATTERN.match(code):
            return ValidationResult(
                valid=False,
                error=f"Invalid ICD-10 format: {code}. Expected format: A00 or A00.0",
                details={"code": code, "pattern": self.PATTERN.pattern}
            )

        return ValidationResult(valid=True)

    def validate_exists(self, code: str) -> ValidationResult:
        """
        Check if code exists in catalog (if catalog is loaded)

        Args:
            code: ICD-10 code to check

        Returns:
            ValidationResult
        """
        code = code.upper().strip()

        # First validate format
        format_result = self.validate_format(code)
        if not format_result.valid:
            return format_result

        # If no catalog, just pass format validation
        if not self.catalog:
            return ValidationResult(
                valid=True,
                details={"note": "Catalog not loaded, format validation only"}
            )

        # Check existence
        if code not in self.catalog:
            return ValidationResult(
                valid=False,
                error=f"ICD-10 code not found in catalog: {code}",
                details={"code": code, "catalog_size": len(self.catalog)}
            )

        return ValidationResult(
            valid=True,
            details={"label": self.catalog[code].label}
        )

    def validate(self, code: str, check_existence: bool = False) -> ValidationResult:
        """
        Main validation method

        Args:
            code: ICD-10 code to validate
            check_existence: Whether to check if code exists in catalog

        Returns:
            ValidationResult
        """
        if check_existence:
            return self.validate_exists(code)
        return self.validate_format(code)


class FieldWhitelistValidator:
    """Validates that target fields are in whitelist"""

    def __init__(self, allowed_fields: List[str]):
        """
        Initialize validator

        Args:
            allowed_fields: List of allowed field names
        """
        self.allowed_fields = set(field.lower() for field in allowed_fields)

    def validate(self, field: str) -> ValidationResult:
        """
        Validate field is in whitelist

        Args:
            field: Field name to validate

        Returns:
            ValidationResult
        """
        field_lower = field.lower()

        if field_lower not in self.allowed_fields:
            return ValidationResult(
                valid=False,
                error=f"Field '{field}' is not in whitelist",
                details={
                    "field": field,
                    "allowed_fields": sorted(self.allowed_fields)
                }
            )

        return ValidationResult(valid=True)


class InputValidator:
    """Validates workflow input"""

    def validate_text_length(
        self,
        text: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate text length

        Args:
            text: Text to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Returns:
            ValidationResult
        """
        length = len(text)

        if min_length is not None and length < min_length:
            return ValidationResult(
                valid=False,
                error=f"Text too short: {length} chars (min: {min_length})",
                details={"length": length, "min": min_length}
            )

        if max_length is not None and length > max_length:
            return ValidationResult(
                valid=False,
                error=f"Text too long: {length} chars (max: {max_length})",
                details={"length": length, "max": max_length}
            )

        return ValidationResult(valid=True)

    def validate_required_fields(
        self,
        data: dict,
        required_fields: List[str]
    ) -> ValidationResult:
        """
        Validate that all required fields are present

        Args:
            data: Data dictionary to check
            required_fields: List of required field names

        Returns:
            ValidationResult
        """
        missing = [field for field in required_fields if field not in data]

        if missing:
            return ValidationResult(
                valid=False,
                error=f"Missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing}
            )

        return ValidationResult(valid=True)


class SecurityValidator:
    """Security-related validations"""

    def validate_response_size(
        self,
        content: str,
        max_size: int = 100000
    ) -> ValidationResult:
        """
        Validate response size doesn't exceed limit

        Args:
            content: Content to check
            max_size: Maximum size in bytes

        Returns:
            ValidationResult
        """
        size = len(content.encode('utf-8'))

        if size > max_size:
            return ValidationResult(
                valid=False,
                error=f"Response too large: {size} bytes (max: {max_size})",
                details={"size": size, "max": max_size}
            )

        return ValidationResult(valid=True)

    def validate_no_script_injection(self, text: str) -> ValidationResult:
        """
        Basic XSS prevention - check for script tags

        Args:
            text: Text to check

        Returns:
            ValidationResult
        """
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',  # onclick=, onload=, etc.
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(
                    valid=False,
                    error="Potential script injection detected",
                    details={"pattern": pattern}
                )

        return ValidationResult(valid=True)


# ============================================================================
# Convenience functions
# ============================================================================

def validate_icd10(code: str, catalog: Optional[dict] = None) -> ValidationResult:
    """Quick ICD-10 validation"""
    validator = ICD10Validator(catalog)
    return validator.validate(code)


def validate_field_whitelist(field: str, allowed: List[str]) -> ValidationResult:
    """Quick field whitelist validation"""
    validator = FieldWhitelistValidator(allowed)
    return validator.validate(field)


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing validators...")
    print("=" * 60)

    # Test ICD-10 validation
    print("\n1. ICD-10 Validation:")
    validator = ICD10Validator()

    test_codes = [
        ("J18.9", True),      # Valid
        ("I10", True),         # Valid
        ("E11.65", True),      # Valid
        ("S06.0X0A", True),    # Valid with complex subcategory
        ("XYZ", False),        # Invalid format
        ("123", False),        # Invalid format
        ("A", False),          # Too short
    ]

    for code, should_pass in test_codes:
        result = validator.validate_format(code)
        status = "✅" if result.valid == should_pass else "❌"
        print(f"  {status} {code}: {'Valid' if result.valid else result.error}")

    # Test field whitelist
    print("\n2. Field Whitelist Validation:")
    whitelist_validator = FieldWhitelistValidator(
        ["DiagnosisText", "DiagnosisCode", "ClinicalNotes"]
    )

    test_fields = [
        ("DiagnosisText", True),
        ("DiagnosisCode", True),
        ("SocialSecurityNumber", False),
        ("BankAccount", False),
    ]

    for field, should_pass in test_fields:
        result = whitelist_validator.validate(field)
        status = "✅" if result.valid == should_pass else "❌"
        print(f"  {status} {field}: {'Allowed' if result.valid else 'Blocked'}")

    # Test input validation
    print("\n3. Input Length Validation:")
    input_validator = InputValidator()

    text_short = "Hi"
    text_good = "Patient presents with symptoms"
    text_long = "A" * 10000

    result = input_validator.validate_text_length(text_short, min_length=10)
    print(f"  {'❌' if not result.valid else '✅'} Short text: {result.error or 'Valid'}")

    result = input_validator.validate_text_length(text_good, min_length=10, max_length=1000)
    print(f"  {'✅' if result.valid else '❌'} Good text: {result.error or 'Valid'}")

    result = input_validator.validate_text_length(text_long, max_length=5000)
    print(f"  {'❌' if not result.valid else '✅'} Long text: {result.error or 'Valid'}")

    print("\n✅ Validator tests complete!")
