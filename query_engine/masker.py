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
        """Recursively masks sensitive values in dictionaries and lists."""
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
        return data

    @classmethod
    def mask_connection_uri(cls, uri: str) -> str:
        """Masks password inside database connection URIs (e.g. mongodb+srv://user:pass@host)."""
        if not uri or not isinstance(uri, str):
            return uri
        return re.sub(r":([^/@]+)@", r":********@", uri)
