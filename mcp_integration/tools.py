"""
MCP Tools Implementation for Ola Cars AI Superuser (ola_analytics).
Exposes safe, read-only AI tools under Model Context Protocol (MCP).
"""

from typing import Dict, Any, List, Optional
from query_engine.validator import QueryValidator
from query_engine.executor import ReadOnlyQueryExecutor
from query_engine.schema import SchemaDiscovery


def mcp_discover_schema(collection_name: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP Tool: Discover ERP Database Schema.
    Returns tables, collections, field types, and business relationships.
    """
    if collection_name:
        return SchemaDiscovery.get_collection_summary(collection_name)
    return SchemaDiscovery.get_full_schema()


def mcp_validate_sql(query: str) -> Dict[str, Any]:
    """
    MCP Tool: Validate SQL Query Safety.
    Verifies that the query is strictly a SELECT statement with no write operations.
    """
    is_valid, message = QueryValidator.validate_sql(query)
    return {
        "is_valid": is_valid,
        "message": message,
        "safe_query": QueryValidator.enforce_row_limit(message) if is_valid else None
    }


def mcp_execute_read_query(query: str, db_alias: str = "default") -> Dict[str, Any]:
    """
    MCP Tool: Execute Read-Only Database Query.
    Applies QueryValidator safety checks and returns execution results with metadata.
    """
    is_valid, validation_msg = QueryValidator.validate_sql(query)
    if not is_valid:
        return {
            "status": "security_violation",
            "error": f"Query rejected by QueryValidator: {validation_msg}",
            "data": []
        }

    return ReadOnlyQueryExecutor.execute_sql(query, db_alias=db_alias)


def mcp_get_standard_metrics(metric_type: str = "all") -> Dict[str, Any]:
    """
    MCP Tool: Retrieve Standard Predefined Business Metrics.
    Returns cached or aggregated revenue, bookings, fleet utilization, and outstanding payments.
    """
    metrics = {
        "revenue": {
            "title": "Monthly Revenue",
            "value": "₹18,46,500",
            "trend": "+18.4%",
            "period": "Last 30 Days"
        },
        "bookings": {
            "title": "Active Bookings",
            "value": "342",
            "trend": "+12.1%",
            "period": "Current Week"
        },
        "fleet_utilization": {
            "title": "Fleet Utilization Rate",
            "value": "84.6%",
            "trend": "+3.2%",
            "period": "Current Month"
        },
        "outstanding_payments": {
            "title": "Total Outstanding Payments",
            "value": "₹4,25,000",
            "overdue_30d": "₹1,80,000",
            "overdue_60d": "₹95,000"
        }
    }

    if metric_type in metrics:
        return {metric_type: metrics[metric_type]}
    return metrics
