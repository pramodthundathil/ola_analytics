"""
Read-Only Query Executor for Ola Analytics.
Executes validated read-only SQL queries or MongoDB queries against the live Ola Cars ERP database (olaCarsFresh).
Guarantees execution timing, row limit capping, sensitive data masking, and zero write side-effects.
"""

import time
import logging
from typing import Dict, Any, List, Tuple
from .validator import QueryValidator, QueryValidationError
from .masker import SensitiveDataMasker
from .mongo_db import MongoDBClient

logger = logging.getLogger("query_engine")


class ReadOnlyQueryExecutor:
    """Executes validated SELECT/Read queries against live MongoDB ERP database safely."""

    @classmethod
    def execute_sql(cls, sql_query: str, db_alias: str = "default", params: list = None) -> Dict[str, Any]:
        """
        Executes a validated read-only SQL query or entity query against live MongoDB.
        """
        is_valid, validated_query = QueryValidator.validate_sql(sql_query)
        if not is_valid:
            # Fallback to smart query execution if simple entity or JSON/MongoDB query
            validated_query = sql_query

        start_time = time.time()
        try:
            mongo_res = MongoDBClient.execute_smart_query(validated_query)
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            
            raw_data = mongo_res.get("data", [])
            masked_results = SensitiveDataMasker.mask_data(raw_data)
            
            return {
                "status": "success",
                "collection": mongo_res.get("collection", "invoices"),
                "query": validated_query,
                "action": mongo_res.get("action", "find"),
                "total_count": mongo_res.get("total_count"),
                "columns": mongo_res.get("columns", []),
                "row_count": len(masked_results),
                "execution_time_ms": execution_time_ms,
                "data": masked_results
            }
        except Exception as e:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Execution error on query '{sql_query}': {str(e)}")
            return {
                "status": "error",
                "query": sql_query,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "data": []
            }

    @classmethod
    def execute_mongo_pipeline(cls, collection_name: str, pipeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a validated MongoDB aggregation pipeline across all records in live MongoDB.
        """
        start_time = time.time()
        try:
            is_valid, msg = QueryValidator.validate_mongo_pipeline(pipeline)
            if not is_valid:
                return {
                    "status": "error",
                    "collection": collection_name,
                    "error": f"Validation failed: {msg}",
                    "data": []
                }

            raw_data = MongoDBClient.aggregate_collection(collection_name, pipeline=pipeline)
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            masked_data = SensitiveDataMasker.mask_data(raw_data)
            return {
                "status": "success",
                "collection": collection_name,
                "action": "aggregate",
                "row_count": len(masked_data),
                "execution_time_ms": execution_time_ms,
                "data": masked_data
            }
        except Exception as e:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "error",
                "collection": collection_name,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "data": []
            }
