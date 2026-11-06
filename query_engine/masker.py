"""
Sensitive Data Masking Utility for Ola Analytics.
Ensures passwords, password hashes, secrets, API keys, tokens, and PII are redacted from database outputs,
LLM prompts, MCP tool returns, and log files.
"""

import re
from typing import Any, Dict, List, Union


class SensitiveDataMasker:
    """Masks sensitive fields in query outputs, logs, and dictionaries."""

    # Field name patterns to mask (case-insensitive regex)
    SENSITIVE_FIELD_PATTERNS = [
        r"^pass(word)?$",
        r".*password.*",
        r".*pass_hash.*",
        r".*hash(ed)?_password.*",
        r".*secret.*",
        r".*token.*",
        r".*auth.*key.*",
        r".*api_key.*",
        r".*ssn.*",
        r".*credit_card.*",
        r".*card_number.*",
        r".*cvv.*",
        r".*pin$"
    ]

    MASK_VALUE = "********"

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        """Checks if a field key name is sensitive."""
        if not key or not isinstance(key, str):
            return False
        key_lower = key.strip().lower()
        for pattern in cls.SENSITIVE_FIELD_PATTERNS:
            if re.match(pattern, key_lower):
                return True
        return False

    @classmethod
    def mask_data(cls, data: Union[Dict[str, Any], List[Any], Any]) -> Any:
        """Recursively masks sensitive values in dictionaries and lists, while safely stringifying ObjectIds and datetimes."""
        if isinstance(data, dict):
            masked_dict = {}
            for k, v in data.items():
                if cls.is_sensitive_key(str(k)):
                    masked_dict[k] = cls.MASK_VALUE
                else:
                    masked_dict[k] = cls.mask_data(v)
            return masked_dict
        elif isinstance(data, list):
            return [cls.mask_data(item) for item in data]
        elif type(data).__name__ == "ObjectId":
            return str(data)
        elif hasattr(data, "isoformat"):
            return data.isoformat()
        return data

    @classmethod
    def mask_document(cls, doc: Any) -> Any:
        """Masks sensitive fields in a single document/record."""
        return cls.mask_data(doc)

    @classmethod
    def mask_row(cls, row: Any) -> Any:
        """Masks sensitive fields in a single database row."""
        return cls.mask_data(row)

    @classmethod
    def mask_record(cls, record: Any) -> Any:
        """Masks sensitive fields in a single record."""
        return cls.mask_data(record)

    @classmethod
    def mask_records(cls, records: Any) -> Any:
        """Masks sensitive fields in a list of records."""
        return cls.mask_data(records)

    @classmethod
    def mask_dict(cls, d: Any) -> Any:
        """Masks sensitive fields in a dictionary."""
        return cls.mask_data(d)

    @classmethod
    def mask_field(cls, key: str, value: Any) -> Any:
        """Masks a field value if its key is sensitive."""
        if cls.is_sensitive_key(str(key)):
            return cls.MASK_VALUE
        return cls.mask_data(value)

    @classmethod
    def mask_value(cls, value: Any) -> Any:
        """Replaces a value with the masked indicator."""
        return cls.MASK_VALUE

    @classmethod
    def mask_connection_uri(cls, uri: str) -> str:
        """Masks password inside database connection URIs (e.g. mongodb+srv://user:pass@host)."""
        if not uri or not isinstance(uri, str):
            return uri
        return re.sub(r":([^/@]+)@", r":********@", uri)


# Global helper functions for direct module-level imports
def mask_data(data: Any) -> Any:
    return SensitiveDataMasker.mask_data(data)

def mask_document(doc: Any) -> Any:
    return SensitiveDataMasker.mask_document(doc)

def mask_row(row: Any) -> Any:
    return SensitiveDataMasker.mask_row(row)

def mask_dict(d: Any) -> Any:
    return SensitiveDataMasker.mask_dict(d)

def mask_records(records: Any) -> Any:
    return SensitiveDataMasker.mask_records(records)

