"""
MCP (Model Context Protocol) Server for Ola Analytics.
Exposes read-only AI agent tools over Streamable HTTP/JSON-RPC and stdio for Claude, Antigravity, ChatGPT, and AI agents.
"""

import sys
import json
import logging
from mcp_integration.tools import (
    mcp_discover_schema,
    mcp_validate_sql,
    mcp_execute_read_query,
    mcp_get_standard_metrics
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
                        "description": "Run a safe, read-only SELECT query or MongoDB aggregation pipeline against Ola Cars database (max 1000 rows).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Read-only SQL query or MongoDB query string"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "execute_read_query",
                        "description": "Execute a validated read-only query against the connected ERP database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Validated SQL SELECT or MongoDB query"},
                                "db_alias": {"type": "string", "default": "default"}
                            },
                            "required": ["query"]
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
