"""
QueryValidator - Safety enforcement layer for AI and user data access.
Strictly permits READ-ONLY queries (SELECT in SQL, find/aggregate in MongoDB).
Rejects all write, update, delete, drop, alter, or schema-modifying commands.
"""

import re
from typing import Dict, Any, Tuple


class QueryValidationError(Exception):
    """Exception raised when a query fails security validation."""
    pass


class QueryValidator:
    # Forbidden SQL keywords (Case-insensitive)
    FORBIDDEN_SQL_KEYWORDS = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
        r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bGRANT\b",
        r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bRENAME\b",
        r"\bREPLACE\b", r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b",
        r"\bVACUUM\b"
    ]

    # Forbidden MongoDB operators/methods
    FORBIDDEN_MONGO_OPERATORS = [
        "$out", "$merge", "$where", "deleteMany", "deleteOne",
        "updateMany", "updateOne", "insertMany", "insertOne",
        "drop", "dropDatabase", "eval"
    ]

    DEFAULT_ROW_LIMIT = 1000
    MAX_TIMEOUT_SECONDS = 10

    @classmethod
    def validate_sql(cls, query: str) -> Tuple[bool, str]:
        """
        Validates an SQL query string to ensure it is strictly a read-only SELECT query.
        Returns (is_valid, reason/normalized_query).
        """
        if not query or not isinstance(query, str):
            return False, "Empty or non-string query provided."

        cleaned_query = query.strip()

        # Rejection: Multiple statements separated by semicolon
        statements = [s for s in cleaned_query.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are strictly forbidden."

        single_query = statements[0].strip()

        # Must start with SELECT or WITH (for CTEs) or EXPLAIN
        if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", single_query, re.IGNORECASE):
            return False, "Query must begin with SELECT or WITH."

        # Check for forbidden keywords
        for keyword in cls.FORBIDDEN_SQL_KEYWORDS:
            if re.search(keyword, single_query, re.IGNORECASE):
                return False, f"Forbidden keyword detected in query: {keyword}"

        return True, single_query

    @classmethod
    def validate_mongo_pipeline(cls, pipeline: list) -> Tuple[bool, str]:
        """
        Validates a MongoDB aggregation pipeline to ensure no write stages ($out, $merge) exist.
        """
        if not isinstance(pipeline, list):
            return False, "MongoDB pipeline must be a list of stage dictionaries."

        for stage in pipeline:
            if not isinstance(stage, dict):
                return False, "Each pipeline stage must be a dictionary."

            for key in stage.keys():
                if key in cls.FORBIDDEN_MONGO_OPERATORS:
                    return False, f"Forbidden MongoDB aggregation operator detected: {key}"

        return True, "Pipeline validated successfully."

    @classmethod
    def enforce_row_limit(cls, query: str, limit: int = DEFAULT_ROW_LIMIT) -> str:
        """
        Appends or caps LIMIT in SQL SELECT query.
        """
        query_upper = query.upper()
        if "LIMIT" not in query_upper:
            return f"{query} LIMIT {limit}"
        return query
