"""
Shared Pydantic validators for DormTel input models.

This module provides reusable validator functions to handle common parsing issues:
- Date format flexibility (ISO + MM/DD/YYYY)
- Empty string → None conversion for Optional fields
- Enum string normalization (lowercase)
- Decimal parsing with currency/comma handling
- Boolean parsing with various truthy/falsy strings
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Union
from pydantic import field_validator, model_validator
from uuid import UUID


def parse_date_flexible(value: Any) -> Optional[date]:
    """
    Parse date from multiple formats:
    - ISO format: YYYY-MM-DD
    - US format: MM/DD/YYYY
    - Already a date object: pass through
    - None or empty: return None
    """
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # Try ISO format first (YYYY-MM-DD)
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(value, "%m/%d/%Y").date()
        except ValueError:
            pass
        # Try M/D/YYYY (single digit month/day)
        try:
            return datetime.strptime(value, "%m/%d/%Y").date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD or MM/DD/YYYY")


def empty_string_to_none(value: Any) -> Any:
    """Convert empty string to None for Optional fields (UUID, int, dict, list, etc.)"""
    if value == "" or value is None:
        return None
    return value


def normalize_enum_string(value: Any) -> Optional[str]:
    """Normalize enum strings to lowercase and strip whitespace"""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value.strip().lower()
    return value


def parse_decimal(value: Any) -> Optional[Decimal]:
    """
    Parse decimal from multiple formats:
    - Plain number: 6000, 6000.50
    - Currency strings: ₱6,000, $1,234.56
    - Comma-separated: 6,000, 1,234,567.89
    - Empty string: return None
    """
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # Remove currency symbols and commas
        value = value.replace("₱", "").replace("$", "").replace(",", "").strip()
        try:
            return Decimal(value)
        except InvalidOperation:
            raise ValueError(f"Invalid decimal format: {value}")
    raise ValueError(f"Cannot convert to decimal: {value}")


def parse_bool(value: Any) -> Optional[bool]:
    """
    Parse boolean from various formats:
    - Python bool: True, False
    - Strings: "true", "false", "yes", "no", "1", "0" (case-insensitive)
    - Integers: 1, 0
    - Empty string: return None
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ("true", "yes", "1", "on"):
            return True
        if value in ("false", "no", "0", "off"):
            return False
        raise ValueError(f"Invalid boolean value: {value}")
    raise ValueError(f"Cannot convert to boolean: {value}")


# Reusable validator decorators
def date_validator(*fields: str):
    """Apply flexible date parsing to specified fields"""
    return field_validator(*fields, mode="before")(lambda cls, v: parse_date_flexible(v))


def empty_to_none_validator(*fields: str):
    """Apply empty string → None conversion to specified fields"""
    return field_validator(*fields, mode="before")(lambda cls, v: empty_string_to_none(v))


def enum_validator(*fields: str):
    """Apply enum normalization to specified fields"""
    return field_validator(*fields, mode="before")(lambda cls, v: normalize_enum_string(v))


def decimal_validator(*fields: str):
    """Apply decimal parsing to specified fields"""
    return field_validator(*fields, mode="before")(lambda cls, v: parse_decimal(v))


def bool_validator(*fields: str):
    """Apply boolean parsing to specified fields"""
    return field_validator(*fields, mode="before")(lambda cls, v: parse_bool(v))


class SanitizedModel:
    """
    Mixin class that automatically converts empty strings to None for all Optional fields.
    
    Usage:
        class MyModel(BaseModel, SanitizedModel):
            optional_field: Optional[str] = None
    """
    
    @model_validator(mode="before")
    @classmethod
    def sanitize_empty_strings(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # Get all Optional fields from the model
        result = {}
        for key, value in data.items():
            if value == "":
                # Check if this field is Optional in the model
                field_info = cls.model_fields.get(key)
                if field_info and not field_info.is_required():
                    result[key] = None
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
