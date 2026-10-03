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
    mcp_get_all_collection_stats
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
                        "description": "Retrieve standard predefined business metrics (revenue, bookings, fleet utilization, overdue payments).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "metric_type": {"type": "string", "description": "revenue, bookings, fleet_utilization, outstanding_payments, or all"}
                            }
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
                res = mcp_get_standard_metrics(metric_type=args.get("metric_type", "all"))
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
