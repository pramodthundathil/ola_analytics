"""
MCP (Model Context Protocol) Server for Ola Analytics.
Exposes read-only AI agent tools over Streamable HTTP/JSON-RPC and stdio for Claude, Antigravity, ChatGPT, and AI agents.
"""

import os
import sys
import json
import logging

# Ensure Django settings are configured for standalone MCP execution
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ola_analytics.settings")
import django
try:
    django.setup()
except Exception:
    pass

from mcp_integration.tools import (
    mcp_discover_schema,
    mcp_validate_sql,
    mcp_execute_read_query,
    mcp_get_standard_metrics,
    mcp_count_documents,
    mcp_execute_aggregation,
    mcp_get_all_collection_stats,
    mcp_get_date_breakdown_analytics,
    mcp_get_invoices_breakdown,
    mcp_query_collection_records
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def handle_request(request: dict) -> dict:
    """Handles JSON-RPC 2.0 requests for MCP tools including initialize handshake."""
    if not isinstance(request, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request object"}
        }

    req_id = request.get("id", 1)
    method = request.get("method")
    params = request.get("params", {})

    # 1. MCP Protocol Initialization Handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "ola_car_analytics",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return {
            "jsonrpc": "2.0",
            "result": {}
        }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    # 2. Tool Discovery
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "discover_schema",
                        "description": "Inspect ERP database schema, collections/tables, fields, data types, and foreign key relations.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection_name": {"type": "string", "description": "Optional specific collection/table name"}
                            }
                        }
                    },
                    {
                        "name": "run_query",
                        "description": "Run a safe, read-only SELECT query, JSON filter query, COUNT query, or MongoDB aggregation pipeline against Ola Cars database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Read-only SQL query, JSON payload, or MongoDB query string"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "execute_read_query",
                        "description": "Execute a validated read-only query (SQL SELECT, JSON payload, or MongoDB query) against the connected ERP database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Validated SQL SELECT, JSON query string, or MongoDB query"},
                                "db_alias": {"type": "string", "default": "default"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "count_documents",
                        "description": "Count total documents in any MongoDB collection across all records without a 500-row cap.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection_name": {"type": "string", "description": "Collection name (e.g. drivers, vehicles, invoices, customers, bills)"},
                                "filter_dict": {"type": "object", "description": "Optional query filter dict (e.g. {'status': 'ACTIVE'})"}
                            },
                            "required": ["collection_name"]
                        }
                    },
                    {
                        "name": "execute_aggregation",
                        "description": "Execute a full MongoDB aggregation pipeline (e.g. $match, $group, $sort) across all documents in a collection.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection_name": {"type": "string", "description": "Collection name (e.g. drivers, vehicles, invoices)"},
                                "pipeline": {
                                    "type": "array",
                                    "description": "List of aggregation stage dictionaries (e.g. [{'\\$group': {'_id': '\\$status', 'count': {'\\$sum': 1}}}])"
                                }
                            },
                            "required": ["collection_name", "pipeline"]
                        }
                    },
                    {
                        "name": "analyze_collections",
                        "description": "Get total document counts, status breakdowns, and statistics for ALL ERP collections in the database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_standard_metrics",
                        "description": "Retrieve standard predefined business metrics (revenue, bookings, fleet utilization, overdue payments) with optional time_range filtering and monthly trends.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "metric_type": {"type": "string", "description": "revenue, bookings, fleet_utilization, outstanding_payments, or all"},
                                "time_range": {"type": "string", "enum": ["7d", "30d", "90d", "6m", "ytd", "all"], "description": "Time horizon (default: all)"},
                                "start_date": {"type": "string", "description": "Optional start date in YYYY-MM-DD format"},
                                "end_date": {"type": "string", "description": "Optional end date in YYYY-MM-DD format"}
                            }
                        }
                    },
                    {
                        "name": "get_date_breakdown_analytics",
                        "description": "Retrieve time-series date-breakdown analytics (monthly/weekly/daily) across invoices, payments, bills, or expenses with exact revenue, collections, and volume totals.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection_name": {"type": "string", "description": "invoices, paymentreceiveds, bills, or expenses (default: invoices)"},
                                "time_range": {"type": "string", "enum": ["7d", "30d", "90d", "6m", "ytd", "all"], "description": "Time range filter (default: all)"},
                                "group_by": {"type": "string", "enum": ["month", "week", "day"], "description": "Grouping interval (default: month)"},
                                "start_date": {"type": "string", "description": "Optional custom start date in YYYY-MM-DD format"},
                                "end_date": {"type": "string", "description": "Optional custom end date in YYYY-MM-DD format"}
                            }
                        }
                    },
                    {
                        "name": "get_invoices_breakdown",
                        "description": "Comprehensive multi-aspect invoice analytics: group by date (month), payment status (PAID/PENDING/OVERDUE), or customer with total billed, paid, balance due, and collection efficiency. Call this whenever leadership asks for invoice totals, billing performance, or accounts receivable.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "group_by": {"type": "string", "enum": ["month", "status", "customer"], "description": "Grouping dimension (default: month)"},
                                "time_range": {"type": "string", "enum": ["7d", "30d", "90d", "6m", "ytd", "all"], "description": "Time range filter (default: all)"},
                                "status": {"type": "string", "description": "Optional status filter (e.g. PAID, PENDING, OVERDUE, PARTIAL)"},
                                "start_date": {"type": "string", "description": "Optional custom start date in YYYY-MM-DD format"},
                                "end_date": {"type": "string", "description": "Optional custom end date in YYYY-MM-DD format"},
                                "limit": {"type": "integer", "description": "Maximum number of rows/customers (default: 50)"}
                            }
                        }
                    },
                    {
                        "name": "query_collection_records",
                        "description": "Safely query individual records from any collection (e.g. 'invoices', 'customers', 'vehicles', 'drivers', 'paymentreceiveds') with automatic sensitive data masking, reference enrichment, and sorting. Call this to retrieve the latest invoice batch, individual invoice details, driver profiles, or vehicle statuses.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection_name": {"type": "string", "description": "Name of MongoDB collection (e.g. invoices, vehicles, customers)"},
                                "filter_dict": {"type": "object", "description": "Optional query filter dictionary"},
                                "sort_field": {"type": "string", "description": "Optional field name to sort by (e.g. createdAt, dueDate, paymentDate)"},
                                "sort_order": {"type": "integer", "enum": [-1, 1], "description": "Sort direction: -1 (descending) or 1 (ascending)"},
                                "limit": {"type": "integer", "description": "Max records to return (default: 25, capped at 50)"}
                            },
                            "required": ["collection_name"]
                        }
                    },
                    {
                        "name": "validate_sql",
                        "description": "Validate if an SQL query is safe and strictly read-only (SELECT).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "SQL query string to validate"}
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }

    # 3. Tool Execution
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            if tool_name == "discover_schema":
                res = mcp_discover_schema(collection_name=args.get("collection_name"))
            elif tool_name in ["run_query", "execute_read_query"]:
                res = mcp_execute_read_query(query=args.get("query", ""), db_alias=args.get("db_alias", "default"))
            elif tool_name == "count_documents":
                res = mcp_count_documents(collection_name=args.get("collection_name", "drivers"), filter_dict=args.get("filter_dict"))
            elif tool_name == "execute_aggregation":
                res = mcp_execute_aggregation(collection_name=args.get("collection_name", "drivers"), pipeline=args.get("pipeline", []))
            elif tool_name == "analyze_collections":
                res = mcp_get_all_collection_stats()
            elif tool_name == "get_standard_metrics":
                res = mcp_get_standard_metrics(
                    metric_type=args.get("metric_type", "all"),
                    time_range=args.get("time_range", "all"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date")
                )
            elif tool_name == "get_date_breakdown_analytics":
                res = mcp_get_date_breakdown_analytics(
                    collection_name=args.get("collection_name", "invoices"),
                    time_range=args.get("time_range", "all"),
                    group_by=args.get("group_by", "month"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date")
                )
            elif tool_name == "get_invoices_breakdown":
                res = mcp_get_invoices_breakdown(
                    time_range=args.get("time_range", "all"),
                    group_by=args.get("group_by", "month"),
                    status=args.get("status"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                    limit=args.get("limit", 50)
                )
            elif tool_name == "query_collection_records":
                res = mcp_query_collection_records(
                    collection_name=args.get("collection_name", "invoices"),
                    filter_dict=args.get("filter_dict"),
                    sort_field=args.get("sort_field"),
                    sort_order=args.get("sort_order", -1),
                    limit=args.get("limit", 25)
                )
            elif tool_name == "validate_sql":
                res = mcp_validate_sql(query=args.get("query", ""))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not supported."}
    }


def main():
    """Runs MCP server listening on stdin/stdout."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as err:
            logging.error(f"Error handling MCP stdio input: {err}")


if __name__ == "__main__":
    main()
