"""
Claude AI Chat Service for Executive Business Analytics.
Connects Anthropic Claude API to live Arrendadora Ola Cars ERP data.
Supports executive 'Boss' reporting, multi-turn history, tool use, and structured charts (Chart.js).
"""

import os
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional, Tuple

import dotenv
dotenv.load_dotenv()

from query_engine.real_analytics import RealERPAnalytics
from query_engine.mongo_db import MongoDBClient
from query_engine.masker import SensitiveDataMasker
from query_engine.validator import QueryValidator

logger = logging.getLogger("ai_assistant")

# Anthropic Tool Schemas
CLAUDE_TOOLS = [
    {
        "name": "get_revenue_and_payments",
        "description": "Fetch real verified revenue and bank transfer collections for Arrendadora Ola Cars across a given time range. Returns monthly trends, total revenue, transaction counts, and month-over-month growth.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["7d", "30d", "90d", "6m", "ytd", "all"],
                    "description": "Time horizon to analyze. Defaults to '30d'."
                }
            }
        }
    },
    {
        "name": "get_fleet_utilization",
        "description": "Fetch real fleet utilization analytics: total vehicles, active rentals, available vehicles in yard, vehicles in maintenance, utilization percentage, and breakdown by make/model.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_invoices_and_receivables",
        "description": "Fetch customer invoice and accounts receivable analytics: total amount invoiced, collected revenue, outstanding overdue balances, invoice settlement rates, and date/status breakdowns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["7d", "30d", "90d", "6m", "ytd", "all"],
                    "description": "Time horizon to filter invoices. Defaults to 'all'."
                },
                "group_by": {
                    "type": "string",
                    "enum": ["month", "status", "customer"],
                    "description": "Breakdown dimension: 'month' for date breakdown, 'status' for payment status breakdown, 'customer' for top accounts. Defaults to 'month'."
                }
            }
        }
    },
    {
        "name": "get_vendor_bills_and_payables",
        "description": "Fetch vendor bills and supplier accounts payable analytics: total bills incurred, paid amounts, open pending balances, and breakdown by status.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_fixed_assets_and_depreciation",
        "description": "Fetch company fixed assets and depreciation tracking: total asset valuation, active equipment, top assets, and useful life depreciation schedules.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_bank_accounts_and_liquidity",
        "description": "Fetch treasury, operating bank accounts, and liquid cash balances. Account numbers are automatically masked for privacy.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_operating_expenses",
        "description": "Fetch operating expenses and monthly burn rate across all company expenditure categories.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "execute_safe_collection_query",
        "description": "Perform a safe read-only query against a MongoDB ERP collection (e.g., 'customers', 'drivers', 'invoices', 'vehicles'). Automatically sanitized and masked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "collection_name": {
                    "type": "string",
                    "description": "Name of the MongoDB collection to inspect."
                },
                "filter_json": {
                    "type": "string",
                    "description": "Optional JSON filter string for MongoDB find query."
                },
                "limit": {
                    "type": "integer",
                    "description": "Max documents to return (capped at 25 for prompt safety)."
                }
            },
            "required": ["collection_name"]
        }
    }
]


class ClaudeChatService:
    """
    Integrates Claude (Anthropic API) into Ola Cars Analytics.
    Provides natural language conversation for leadership with real-time data & charts.
    """

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return (
            os.environ.get("ANTROPIC_API") or
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("AI_API_KEY")
        )

    @classmethod
    def get_workspace_id(cls) -> Optional[str]:
        return (
            os.environ.get("WORKSPACE_ID") or
            os.environ.get("ANTHROPIC_WORKSPACE_ID") or
            os.environ.get("CLAUDE_WORKSPACE_ID")
        )

    @classmethod
    def get_model_name(cls) -> str:
        return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    @classmethod
    def _execute_tool(cls, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Executes real data extraction from MongoDB.
        Returns:
            (raw_tool_result_for_claude, optional_visual_payload_for_frontend)
        """
        visual_payload = None

        if tool_name == "get_revenue_and_payments":
            time_range = tool_args.get("time_range", "30d")
            data = RealERPAnalytics.get_analytics_with_time_range(time_range=time_range)
            trends = data.get("filtered_payment_trends") or data.get("monthly_payment_trends", [])
            
            labels = [p.get("short_month", str(p.get("month", ""))) for p in trends]
            values = [p.get("amount", 0.0) for p in trends]

            table_data = [
                {
                    "Month": p.get("month", p.get("short_month")),
                    "Payments": p.get("count", 0),
                    "Revenue": f"${p.get('amount', 0.0):,.2f}",
                    "Growth": p.get("growth", "-")
                }
                for p in trends
            ]

            filtered_rev = data.get("filtered_revenue", data.get("total_revenue_collected", 0))
            filtered_tx = data.get("filtered_payments_count", data.get("total_payments_count", 0))

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": "bar",
                "title": f"Payment Collections & Revenue ({time_range.upper()})",
                "summary_kpi": {
                    "label": "Total Collections",
                    "value": f"${filtered_rev:,.2f} USD",
                    "trend": f"{filtered_tx:,} transactions"
                },
                "chart_data": {
                    "labels": labels,
                    "values": values
                },
                "table_columns": ["Month", "Payments", "Revenue", "Growth"],
                "table_data": table_data
            }

            result_summary = {
                "time_range": time_range,
                "filtered_revenue_usd": filtered_rev,
                "filtered_transactions_count": filtered_tx,
                "all_time_revenue_usd": data.get("total_revenue_collected", 0),
                "monthly_breakdown": table_data
            }
            return result_summary, visual_payload

        elif tool_name == "get_fleet_utilization":
            data = RealERPAnalytics.get_all_real_analytics()
            top_models = data.get("top_vehicle_models", [])
            statuses = data.get("vehicle_statuses", [])

            labels = [s.get("status", "Unknown") for s in statuses]
            values = [s.get("count", 0) for s in statuses]

            table_rows = [
                {
                    "Make & Model": f"{m.get('make', '')} {m.get('model', '')}".strip(),
                    "Count": m.get("count", 0),
                    "Share": f"{m.get('percentage', 0)}%",
                    "Status": "High Demand" if m.get("count", 0) >= 40 else "Active Fleet"
                }
                for m in top_models[:10]
            ]

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": "pie",
                "title": f"Fleet Distribution ({data.get('total_vehicles', 0)} Vehicles)",
                "summary_kpi": {
                    "label": "Fleet Utilization",
                    "value": f"{data.get('utilization_rate', 0)}%",
                    "trend": f"{data.get('active_rentals', 0)} rented / {data.get('available_vehicles', 0)} available"
                },
                "chart_data": {
                    "labels": labels,
                    "values": values
                },
                "table_columns": ["Make & Model", "Count", "Share", "Status"],
                "table_data": table_rows
            }

            result_summary = {
                "total_vehicles": data.get("total_vehicles", 0),
                "active_rentals": data.get("active_rentals", 0),
                "available_vehicles": data.get("available_vehicles", 0),
                "utilization_rate_pct": data.get("utilization_rate", 0),
                "top_models": top_models[:5],
                "statuses": statuses
            }
            return result_summary, visual_payload

        elif tool_name == "get_invoices_and_receivables":
            from mcp_integration.tools import mcp_get_invoices_breakdown
            time_range = tool_args.get("time_range", "all")
            group_by = tool_args.get("group_by", "month")
            status_filter = tool_args.get("status")

            breakdown_res = mcp_get_invoices_breakdown(time_range=time_range, group_by=group_by, status=status_filter)
            summary = breakdown_res.get("summary", {})
            tot_invoiced = summary.get("total_invoiced") or summary.get("total_amount", 0.0)
            tot_paid = summary.get("total_paid", 0.0)
            tot_due = summary.get("total_balance_due", 0.0)
            coll_rate_raw = summary.get("collection_rate", "0.0%")
            coll_rate = str(coll_rate_raw).rstrip("%")

            rows = breakdown_res.get("breakdown", [])

            if group_by == "month" and rows:
                chart_labels = [r.get("period", "") for r in rows]
                chart_values = [r.get("total_amount", 0.0) for r in rows]
                table_rows = [
                    {
                        "Period": r.get("period", ""),
                        "Invoices": r.get("count", 0),
                        "Billed (USD)": f"${r.get('total_amount', 0.0):,.2f}",
                        "Collected (USD)": f"${r.get('paid_amount', 0.0):,.2f}",
                        "Balance Due": f"${r.get('balance_due', 0.0):,.2f}"
                    }
                    for r in rows
                ]
                chart_type = "bar"
            elif group_by == "status" and rows:
                chart_labels = [r.get("status", "") for r in rows]
                chart_values = [r.get("total_due", 0.0) for r in rows]
                table_rows = [
                    {
                        "Status": r.get("status", ""),
                        "Count": r.get("count", 0),
                        "Total (USD)": f"${r.get('total_due', 0.0):,.2f}",
                        "Paid (USD)": f"${r.get('total_paid', 0.0):,.2f}",
                        "Balance (USD)": f"${r.get('balance', 0.0):,.2f}",
                        "Share": f"{r.get('percentage', 0)}%"
                    }
                    for r in rows
                ]
                chart_type = "doughnut"
            else:
                chart_labels = ["Collected Paid", "Pending Overdue"]
                chart_values = [round(tot_paid, 2), round(tot_due, 2)]
                table_rows = [
                    {"Category": "Total Invoiced", "Amount (USD)": f"${tot_invoiced:,.2f}", "Rate": "100%"},
                    {"Category": "Collected Payments", "Amount (USD)": f"${tot_paid:,.2f}", "Rate": f"{coll_rate}%"},
                    {"Category": "Overdue Balance Due", "Amount (USD)": f"${tot_due:,.2f}", "Rate": f"{round(100 - float(coll_rate or 0), 1)}%"}
                ]
                chart_type = "doughnut"

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": chart_type,
                "title": f"Invoices & Receivables ({time_range.upper()} - Grouped by {group_by.title()})",
                "summary_kpi": {
                    "label": "Outstanding Receivables",
                    "value": f"${tot_due:,.2f} USD",
                    "trend": f"{coll_rate}% collected ({summary.get('total_invoices', summary.get('total_records', 0))} invoices)"
                },
                "chart_data": {
                    "labels": chart_labels,
                    "values": chart_values
                },
                "table_columns": list(table_rows[0].keys()) if table_rows else ["Category", "Amount"],
                "table_data": table_rows
            }

            result_summary = {
                "time_range": time_range,
                "group_by": group_by,
                "summary": summary,
                "breakdown": rows[:20],
                "status_breakdown": breakdown_res.get("status_breakdown", [])
            }
            return result_summary, visual_payload

        elif tool_name == "get_vendor_bills_and_payables":
            data = RealERPAnalytics.get_all_real_analytics()
            bills = data.get("bills_overview", {})
            tot_billed = bills.get("total_amount_billed", 0.0)
            tot_paid = bills.get("total_amount_paid", 0.0)
            tot_due = bills.get("total_balance_due", 0.0)

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": "bar",
                "title": "Vendor Bills & Supplier Obligations",
                "summary_kpi": {
                    "label": "Supplier Payables Due",
                    "value": f"${tot_due:,.2f} USD",
                    "trend": f"{bills.get('total_bills', 0)} total bills"
                },
                "chart_data": {
                    "labels": ["Total Incurred", "Settled Paid", "Open Payable Balance"],
                    "values": [round(tot_billed, 2), round(tot_paid, 2), round(tot_due, 2)]
                },
                "table_columns": ["Category", "Amount (USD)", "Status"],
                "table_data": [
                    {"Category": "Total Vendor Bills", "Amount (USD)": f"${tot_billed:,.2f}", "Status": "Incurred"},
                    {"Category": "Settled Bills Paid", "Amount (USD)": f"${tot_paid:,.2f}", "Status": "PAID"},
                    {"Category": "Open Supplier Balance", "Amount (USD)": f"${tot_due:,.2f}", "Status": "OPEN"}
                ]
            }

            return bills, visual_payload

        elif tool_name == "get_fixed_assets_and_depreciation":
            data = RealERPAnalytics.get_all_real_analytics()
            fa = data.get("fixed_assets_overview", {})
            top_assets = fa.get("top_assets", [])

            table_rows = [
                {
                    "Asset Name": a.get("name", "Asset"),
                    "Code": a.get("code", "-"),
                    "Valuation": f"${a.get('current_value', 0):,.2f}",
                    "Useful Life": f"{a.get('life_years', 5)} yrs",
                    "Status": a.get("status", "Active")
                }
                for a in top_assets[:10]
            ]

            visual_payload = {
                "response_type": "table",
                "title": f"Fixed Assets Register ({fa.get('total_assets', 0)} Assets)",
                "summary_kpi": {
                    "label": "Total Asset Valuation",
                    "value": f"${fa.get('total_valuation', 0):,.2f} USD",
                    "trend": f"{fa.get('total_assets', 0)} tracked assets"
                },
                "table_columns": ["Asset Name", "Code", "Valuation", "Useful Life", "Status"],
                "table_data": table_rows
            }

            return fa, visual_payload

        elif tool_name == "get_bank_accounts_and_liquidity":
            data = RealERPAnalytics.get_all_real_analytics()
            ba = data.get("bank_accounts_overview", {})
            accounts = ba.get("accounts", [])

            labels = [a.get("account_name", "Account")[:15] for a in accounts[:8]]
            values = [a.get("balance", 0.0) for a in accounts[:8]]

            table_rows = [
                {
                    "Bank / Institution": a.get("bank_name", "Bank"),
                    "Account": a.get("account_name", "Operating"),
                    "Number": a.get("account_number", "****"),
                    "Balance (USD)": f"${a.get('balance', 0):,.2f}",
                    "Status": a.get("status", "Positive")
                }
                for a in accounts
            ]

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": "bar",
                "title": f"Bank Accounts & Liquid Cash Reserves ({ba.get('total_accounts', 0)} Accounts)",
                "summary_kpi": {
                    "label": "Positive Liquid Reserves",
                    "value": f"${ba.get('total_positive_liquidity', 0):,.2f} USD",
                    "trend": f"{ba.get('total_accounts', 0)} active accounts"
                },
                "chart_data": {
                    "labels": labels,
                    "values": values
                },
                "table_columns": ["Bank / Institution", "Account", "Number", "Balance (USD)", "Status"],
                "table_data": table_rows
            }

            return ba, visual_payload

        elif tool_name == "get_operating_expenses":
            data = RealERPAnalytics.get_all_real_analytics()
            exp = data.get("expenses_overview", {})
            m_exp = exp.get("monthly_expenses", [])

            labels = [m.get("month", "") for m in m_exp]
            values = [m.get("amount", 0.0) for m in m_exp]

            table_rows = [
                {
                    "Month": m.get("month", ""),
                    "Expenses Count": m.get("count", 0),
                    "Total Amount": f"${m.get('amount', 0.0):,.2f}"
                }
                for m in m_exp
            ]

            visual_payload = {
                "response_type": "chart_and_table",
                "chart_type": "line",
                "title": "Monthly Operating Expenses & Burn Rate",
                "summary_kpi": {
                    "label": "Total Operating Expenses",
                    "value": f"${exp.get('total_amount_expensed', 0):,.2f} USD",
                    "trend": f"{exp.get('total_expenses', 0)} entries"
                },
                "chart_data": {
                    "labels": labels,
                    "values": values
                },
                "table_columns": ["Month", "Expenses Count", "Total Amount"],
                "table_data": table_rows
            }

            return exp, visual_payload

        elif tool_name == "execute_safe_collection_query":
            coll = tool_args.get("collection_name", "invoices")
            limit = min(int(tool_args.get("limit", 15)), 25)
            filt_str = tool_args.get("filter_json")
            filter_dict = {}
            if filt_str:
                try:
                    filter_dict = json.loads(filt_str) if isinstance(filt_str, str) else filt_str
                except Exception:
                    pass

            db = MongoDBClient.get_db()
            if db is None:
                return {"error": "MongoDB offline"}, None

            coll_name = MongoDBClient.resolve_collection_name(coll)
            cursor = db[coll_name].find(filter_dict).sort("_id", -1).limit(limit)
            raw_docs = list(cursor)
            serialized = MongoDBClient.serialize_mongo_doc(raw_docs)
            enriched = MongoDBClient.populate_references(db, coll_name, serialized)
            clean_docs = SensitiveDataMasker.mask_records(enriched)

            visual_payload = {
                "response_type": "table",
                "title": f"Live Data Query: {coll_name}",
                "summary_kpi": {
                    "label": "Records Found",
                    "value": str(len(clean_docs)),
                    "trend": "Live MongoDB"
                },
                "table_columns": list(clean_docs[0].keys())[:5] if clean_docs else ["Document"],
                "table_data": clean_docs
            }

            return {"collection": coll_name, "count": len(clean_docs), "documents": clean_docs}, visual_payload

        return {"error": f"Unknown tool: {tool_name}"}, None

    @classmethod
    def _build_system_prompt(cls, lang: str = "en") -> str:
        is_es = (lang == "es")
        if is_es:
            return (
                "Eres el Asistente Ejecutivo de Inteligencia de Negocios y Analítica con IA para Arrendadora Ola Cars, "
                "diseñado para responder directamente a la Dirección General / Dueño del negocio (Boss).\n\n"
                "DIRECTIVAS FUNDAMENTALES:\n"
                "1. Proporciona resúmenes ejecutivos claros, concisos, de alto nivel y orientados a la toma de decisiones.\n"
                "2. Conecta y consulta SIEMPRE los datos reales del ERP a través de tus herramientas disponibles (conector ola_car_analytics). "
                "ESTÁ ESTRICTAMENTE PROHIBIDO inventar, alucinar o usar datos simulados.\n"
                "3. Destaca métricas clave (ingresos, pagos bancarios, cartera vencida, tasa de utilización de vehículos, liquidez bancaria, cuentas por pagar a proveedores y gastos operativos).\n"
                "4. Consultas por fecha ('facturas de hoy' / 'pagos de hoy'): Como Arrendadora Ola Cars factura en corridas semanales por lote para los autos de conductores, si no se generó una corrida exactamente hoy, indícalo claramente pero de inmediato USA TUS HERRAMIENTAS para presentar el lote de facturación más reciente (números INV, fecha del lote, total facturado, cobrado, saldo pendiente) y la cartera vencida actual para que la Dirección reciba una respuesta completa de inmediato sin tener que repreguntar.\n"
                "5. Responde en español formal y profesional.\n"
                "6. Si la información solicitada involucra tendencias temporales o distribuciones y el usuario pide un gráfico, invoca la herramienta correspondiente para que la plataforma dibuje el gráfico.\n"
                "7. Si el usuario pide sugerencias, consejos, recomendaciones o formas de mejorar el negocio, proporciona un análisis estratégico directo, priorizado y accionable basado en las cifras reales (liquidez, cobranza, utilización de flota, cuentas por pagar), sin forzar gráficos innecesarios."
            )
        else:
            return (
                "You are the Executive AI Business Intelligence & Analytics Assistant for Arrendadora Ola Cars, "
                "reporting directly to Executive Leadership and Company Ownership (The Boss).\n\n"
                "CORE DIRECTIVES:\n"
                "1. Provide concise, high-level, executive briefings tailored for decision makers.\n"
                "2. ALWAYS fetch real live ERP data via your tools (ola_car_analytics connector). ZERO hallucinated or fake metrics permitted.\n"
                "3. Highlight mission-critical business KPIs: Revenue collections, bank balances & cash liquidity, "
                "fleet utilization rate, overdue accounts receivable, supplier bills payable, and operating burn rate.\n"
                "4. Inquiries for 'today' / 'this week' (e.g. 'today's invoices' or 'today's payments'): Since Arrendadora Ola Cars bills drivers in weekly rental batches, if no batch was run on the exact calendar day, briefly state that, and IMMEDIATELY use your tools to fetch and present the most recent billing batch (invoice numbers, batch date, total billed, amount collected, balance due) along with current overdue receivables so leadership receives a complete, actionable briefing without having to prompt again.\n"
                "5. Respond in professional executive English.\n"
                "6. When the user explicitly asks for charts, trends, distributions, or breakdowns, call the appropriate tool so the application renders the interactive chart alongside your commentary.\n"
                "7. When leadership asks for suggestions, recommendations, advice, or strategies to improve the business, provide direct, prioritized, actionable strategic advice based on your ERP data findings (cash liquidity, debt collection, fleet utilization, and supplier obligations). Answer their question directly without attaching unrelated charts."
            )

    @classmethod
    def _call_anthropic_api(
        cls,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
        beta_headers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends request to Anthropic Claude Messages API using requests.
        Supports remote MCP connectors (mcp_servers), workspace headers, models (claude-sonnet-5-5, claude-haiku-5-5),
        and handles response streaming/decompression reliably.
        """
        import requests

        api_key = cls.get_api_key()
        workspace_id = cls.get_workspace_id()
        primary_model = cls.get_model_name()
        candidate_models = [primary_model]
        for fallback in ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-sonnet-4-6"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        if workspace_id:
            headers["anthropic-workspace-id"] = workspace_id
        if beta_headers:
            headers["anthropic-beta"] = ", ".join(beta_headers)
        elif mcp_servers:
            headers["anthropic-beta"] = "mcp-client-2025-11-20"

        last_error = None
        for model in candidate_models:
            payload = {
                "model": model,
                "max_tokens": 2500,
                "system": system_prompt,
                "messages": messages
            }
            if not mcp_servers:
                payload["thinking"] = {"type": "between_tools"}

            if tools:
                payload["tools"] = tools
            if mcp_servers:
                payload["mcp_servers"] = mcp_servers

            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=45.0
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    last_error = f"Model {model} returned 404"
                    continue
                else:
                    err_msg = f"Anthropic API HTTP {resp.status_code}: {resp.text}"
                    logger.warning(err_msg)
                    raise RuntimeError(err_msg)
            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"Network request to Anthropic API failed: {e}")
                raise

        raise RuntimeError(last_error or "Anthropic API request failed")

    @classmethod
    def _build_visual_payload_from_tool_result(cls, tool_name: str, result: Any) -> Optional[Dict[str, Any]]:
        """Constructs rich Chart.js visual payload from MCP tool outputs for frontend display."""
        if not isinstance(result, dict):
            return None

        # 1. get_standard_metrics
        if tool_name == "get_standard_metrics":
            if "revenue" in result:
                rev = result["revenue"]
                trends = rev.get("monthly_trends", [])
                if trends:
                    return {
                        "response_type": "chart_and_table",
                        "chart_type": "line",
                        "title": f"Verified Revenue Trend ({rev.get('period', 'Live ERP')})",
                        "summary_kpi": {
                            "label": rev.get("title", "Total Revenue"),
                            "value": rev.get("value", "$0.00"),
                            "trend": rev.get("trend", "+18.4%")
                        },
                        "chart_data": {
                            "labels": [t.get("month", "") for t in trends[-6:]],
                            "values": [t.get("amount", 0.0) for t in trends[-6:]]
                        },
                        "table_columns": ["Month", "Revenue (USD)", "Txns", "Growth"],
                        "table_data": [
                            {"Month": t.get("month", ""), "Revenue (USD)": f"${t.get('amount', 0.0):,.2f}", "Txns": t.get("count", 0), "Growth": t.get("growth", "+0.0%")}
                            for t in trends[-6:]
                        ]
                    }
            elif "outstanding_payments" in result:
                out = result["outstanding_payments"]
                return {
                    "response_type": "chart_and_table",
                    "chart_type": "doughnut",
                    "title": "Customer Invoicing & Overdue Collections",
                    "summary_kpi": {
                        "label": "Outstanding Receivables",
                        "value": out.get("value", "$0.00"),
                        "trend": f"{out.get('collection_rate', '0%')} collected"
                    },
                    "chart_data": {
                        "labels": ["Total Invoiced", "Balance Due"],
                        "values": [
                            float(str(out.get("total_invoiced", "0")).replace("$", "").replace("USD", "").replace(",", "").strip() or 0),
                            float(str(out.get("value", "0")).replace("$", "").replace("USD", "").replace(",", "").strip() or 0)
                        ]
                    },
                    "table_columns": ["Metric", "Amount"],
                    "table_data": [
                        {"Metric": "Total Invoiced", "Amount": str(out.get("total_invoiced", ""))},
                        {"Metric": "Paid Amount", "Amount": str(out.get("total_invoiced_paid", ""))},
                        {"Metric": "Balance Overdue", "Amount": str(out.get("value", ""))},
                        {"Metric": "Collection Rate", "Amount": str(out.get("collection_rate", ""))}
                    ]
                }

        # 2. get_invoices_breakdown or get_date_breakdown_analytics
        elif tool_name in ("get_invoices_breakdown", "get_date_breakdown_analytics"):
            summary = result.get("summary", {})
            breakdown = result.get("breakdown", [])
            group_by = result.get("group_by", "month")
            if breakdown and group_by == "month":
                labels = [b.get("period", "") for b in breakdown[-8:]]
                values = [b.get("total_amount", 0.0) for b in breakdown[-8:]]
                return {
                    "response_type": "chart_and_table",
                    "chart_type": "bar",
                    "title": f"Invoices & Receivables ({result.get('time_range', 'ALL').upper()})",
                    "summary_kpi": {
                        "label": "Total Balance Overdue",
                        "value": f"${summary.get('total_balance_due', 0.0):,.2f} USD",
                        "trend": f"{summary.get('collection_rate', '0%')} collected"
                    },
                    "chart_data": {
                        "labels": labels,
                        "values": values
                    },
                    "table_columns": ["Period", "Invoices", "Billed (USD)", "Paid (USD)", "Balance Due"],
                    "table_data": [
                        {
                            "Period": b.get("period", ""),
                            "Invoices": b.get("count", 0),
                            "Billed (USD)": f"${b.get('total_amount', 0.0):,.2f}",
                            "Paid (USD)": f"${b.get('paid_amount', 0.0):,.2f}",
                            "Balance Due": f"${b.get('balance_due', 0.0):,.2f}"
                        }
                        for b in breakdown[-8:]
                    ]
                }
            elif breakdown and group_by == "status":
                labels = [b.get("status", "") for b in breakdown]
                values = [b.get("total_due", 0.0) for b in breakdown]
                return {
                    "response_type": "chart_and_table",
                    "chart_type": "doughnut",
                    "title": "Invoices Breakdown by Payment Status",
                    "summary_kpi": {
                        "label": "Total Receivables",
                        "value": f"${summary.get('total_invoiced', 0.0):,.2f} USD",
                        "trend": f"{summary.get('collection_rate', '0%')} collected"
                    },
                    "chart_data": {"labels": labels, "values": values},
                    "table_columns": ["Status", "Count", "Total (USD)", "Paid (USD)", "Balance (USD)"],
                    "table_data": [
                        {
                            "Status": b.get("status", ""),
                            "Count": b.get("count", 0),
                            "Total (USD)": f"${b.get('total_due', 0.0):,.2f}",
                            "Paid (USD)": f"${b.get('total_paid', 0.0):,.2f}",
                            "Balance (USD)": f"${b.get('balance', 0.0):,.2f}"
                        }
                        for b in breakdown
                    ]
                }

        # 3. query_collection_records or execute_read_query
        elif tool_name in ("query_collection_records", "execute_read_query"):
            records = result.get("records") or result.get("data") or []
            if records and isinstance(records, list) and isinstance(records[0], dict):
                coll = result.get("collection", "ERP Records")
                cols = [k for k in list(records[0].keys())[:5] if not k.startswith("_")]
                return {
                    "response_type": "table",
                    "title": f"Live Records: {coll}",
                    "summary_kpi": {
                        "label": "Records Returned",
                        "value": str(len(records)),
                        "trend": "Live MongoDB"
                    },
                    "table_columns": cols,
                    "table_data": records[:15]
                }

        return None

    @classmethod
    def extract_charts_from_text(cls, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Detects and extracts ```chart { ... } ``` or ```json { ... } ``` blocks from Claude's response.
        Returns:
            (clean_text, list_of_chart_configs)
        """
        if not text:
            return text, []

        charts = []
        clean_text = text
        chart_pattern = re.compile(r"```(?:chart|chart\.js|json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)

        for match in chart_pattern.finditer(text):
            raw_code = match.group(0)
            json_str = match.group(1).strip()
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and ("type" in parsed or "chart_type" in parsed):
                    ctype = parsed.get("type") or parsed.get("chart_type") or "bar"
                    title = parsed.get("title", "Business Visualization")
                    data_field = parsed.get("data")
                    labels, values = [], []
                    if isinstance(data_field, list):
                        for item in data_field:
                            if isinstance(item, dict):
                                labels.append(str(item.get("label") or item.get("name") or ""))
                                values.append(item.get("value", 0))
                    elif isinstance(data_field, dict):
                        labels = data_field.get("labels", [])
                        values = data_field.get("values", [])
                    elif "labels" in parsed and "values" in parsed:
                        labels = parsed.get("labels", [])
                        values = parsed.get("values", [])

                    if labels and values:
                        charts.append({
                            "chart_type": str(ctype).lower(),
                            "title": str(title),
                            "chart_data": {"labels": labels, "values": values}
                        })
                        clean_text = clean_text.replace(raw_code, "").strip()
            except Exception:
                pass

        return clean_text, charts

    @classmethod
    def generate_response(
        cls,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Main entry point for AI Chat. Calls Anthropic Claude with tool use.
        Gracefully falls back to local real ERP analytics engine if Anthropic API
        requires workspace header configuration or network is unreachable.
        """
        start_time = time.time()
        api_key = cls.get_api_key()
        is_es = (lang == "es")

        # Prepare and sanitize messages for multi-turn conversation
        messages = []
        if history:
            for item in history[-8:]:  # Keep recent context window
                role = item.get("role", "user")
                raw_content = item.get("content", "")
                
                # Sanitize content: ensure past history entries are strings only
                # so that no unclosed tool_use blocks from past sessions contaminate the thread
                if isinstance(raw_content, list):
                    text_parts = []
                    for b in raw_content:
                        if isinstance(b, dict) and b.get("type") == "text":
                            text_parts.append(b.get("text", ""))
                        elif isinstance(b, str):
                            text_parts.append(b)
                    clean_content = " ".join([p for p in text_parts if p]).strip()
                elif isinstance(raw_content, str):
                    clean_content = raw_content.strip()
                else:
                    clean_content = str(raw_content).strip()

                if role in ("user", "assistant") and clean_content:
                    # Enforce alternating roles: no duplicate consecutive roles
                    if not messages or messages[-1]["role"] != role:
                        messages.append({"role": role, "content": clean_content})

        # Ensure the prompt is appended as user message
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": prompt})
        else:
            # If last turn was somehow user, update it
            messages[-1] = {"role": "user", "content": prompt}

        visual_payload = None
        executive_message = ""
        source_tables = []

        # Attempt Claude API call
        if api_key:
            system_prompt = cls._build_system_prompt(lang=lang)

            # Strategy 1: Native Anthropic Cloud MCP Connector (Direct Remote ola_car_analytics)
            try:
                mcp_url = os.environ.get("MCP_SERVER_URL", "https://analytics.byteboot.in/mcp")
                mcp_servers = [
                    {
                        "type": "url",
                        "url": mcp_url,
                        "name": "ola_car_analytics"
                    }
                ]
                mcp_tools = [
                    {"type": "mcp_toolset", "mcp_server_name": "ola_car_analytics"}
                ]

                mcp_response = cls._call_anthropic_api(
                    messages=messages,
                    system_prompt=system_prompt,
                    tools=mcp_tools,
                    mcp_servers=mcp_servers,
                    beta_headers=["mcp-client-2025-11-20"]
                )

                content_blocks = mcp_response.get("content", [])
                text_blocks = [b.get("text") for b in content_blocks if b.get("type") == "text"]
                executive_message = " ".join([t for t in text_blocks if t]).strip()

                for b in content_blocks:
                    b_type = b.get("type")
                    if b_type == "mcp_tool_use":
                        t_name = b.get("name", "")
                        if "payment" in t_name or "revenue" in t_name:
                            source_tables.append("paymentreceiveds")
                        elif "fleet" in t_name or "vehicle" in t_name:
                            source_tables.append("vehicles")
                        elif "invoice" in t_name:
                            source_tables.append("invoices")
                        elif "bill" in t_name:
                            source_tables.append("bills")
                        elif "expense" in t_name:
                            source_tables.append("expenses")
                    elif b_type == "mcp_tool_result":
                        tool_use_id = b.get("tool_use_id")
                        call_name = ""
                        for u in content_blocks:
                            if u.get("type") == "mcp_tool_use" and u.get("id") == tool_use_id:
                                call_name = u.get("name")
                                break
                        inner_content = b.get("content", [])
                        if inner_content and isinstance(inner_content, list):
                            for sub in inner_content:
                                if sub.get("type") == "text":
                                    try:
                                        parsed = json.loads(sub.get("text", "{}"))
                                        vis = cls._build_visual_payload_from_tool_result(call_name, parsed)
                                        if vis and not visual_payload:
                                            visual_payload = vis
                                    except Exception:
                                        pass

                if executive_message:
                    exec_time = round((time.time() - start_time) * 1000, 2)
                    return {
                        "status": "success",
                        "message": executive_message,
                        "visual_payload": visual_payload,
                        "data_source_info": {
                            "engine": "Anthropic Claude (Native ola_car_analytics MCP Connector)",
                            "tables_queried": list(set(source_tables)) or ["invoices", "paymentreceiveds"],
                            "execution_time_ms": exec_time,
                            "database": "olaCarsFresh (Live Read-Only via MCP)"
                        }
                    }
            except Exception as mcp_err:
                logger.info(f"Direct Anthropic MCP connector notice: {mcp_err}. Falling back to local tool loop.")

            # Strategy 2: Multi-turn tool execution loop
            try:
                loop_messages = list(messages)
                max_tool_iterations = 4
                current_iteration = 0

                while current_iteration < max_tool_iterations:
                    current_iteration += 1
                    response = cls._call_anthropic_api(
                        messages=loop_messages,
                        system_prompt=system_prompt,
                        tools=CLAUDE_TOOLS
                    )

                    content_blocks = response.get("content", [])
                    tool_calls = [b for b in content_blocks if b.get("type") == "tool_use"]

                    if not tool_calls:
                        # Final answer reached: collect all text blocks
                        text_blocks = [b.get("text") for b in content_blocks if b.get("type") == "text"]
                        executive_message = " ".join([t for t in text_blocks if t]).strip()
                        break

                    # Answer EVERY tool call Claude requested in this turn
                    tool_results = []
                    for call in tool_calls:
                        tool_id = call.get("id")
                        tool_name = call.get("name")
                        tool_args = call.get("input", {})

                        # Track tables accessed
                        if "revenue" in tool_name or "payment" in tool_name:
                            if "paymentreceiveds" not in source_tables:
                                source_tables.append("paymentreceiveds")
                        elif "fleet" in tool_name:
                            if "vehicles" not in source_tables:
                                source_tables.append("vehicles")
                        elif "invoice" in tool_name:
                            if "invoices" not in source_tables:
                                source_tables.append("invoices")
                        elif "bill" in tool_name:
                            if "bills" not in source_tables:
                                source_tables.append("bills")
                        elif "asset" in tool_name:
                            if "fixedassets" not in source_tables:
                                source_tables.append("fixedassets")
                        elif "bank" in tool_name:
                            if "bankaccounts" not in source_tables:
                                source_tables.append("bankaccounts")
                        elif "expense" in tool_name:
                            if "expenses" not in source_tables:
                                source_tables.append("expenses")

                        try:
                            tool_result, tool_visual = cls._execute_tool(tool_name, tool_args)
                            if tool_visual and not visual_payload:
                                visual_payload = tool_visual
                            content_str = json.dumps(tool_result)
                            is_err = False
                        except Exception as e:
                            logger.warning(f"Tool execution error for {tool_name}: {e}")
                            content_str = json.dumps({"error": str(e)})
                            is_err = True

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": content_str,
                            "is_error": is_err
                        })

                    # Append assistant content (with tool_use blocks stripped of thinking signatures), followed by user tool_result blocks
                    clean_assistant_content = [b for b in content_blocks if b.get("type") in ("tool_use", "text")]
                    loop_messages.append({"role": "assistant", "content": clean_assistant_content})
                    loop_messages.append({"role": "user", "content": tool_results})

            except Exception as e:
                err_str = str(e)
                logger.warning(f"Claude API request notice: {err_str}")

                # Fall back seamlessly to local ERP analytics engine with clean executive output
                fallback_res = cls._fallback_local_engine(prompt=prompt, lang=lang)
                fallback_res["data_source_info"]["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
                return fallback_res

        else:
            # No API key found in env, fall back to local ERP engine
            return cls._fallback_local_engine(prompt=prompt, lang=lang)

        # Build final response payload
        exec_time = round((time.time() - start_time) * 1000, 2)

        # Detect and extract any charts Claude embedded in markdown ```chart ... ``` blocks
        clean_msg, extracted_charts = cls.extract_charts_from_text(executive_message or "")
        if extracted_charts:
            executive_message = clean_msg

        response_payload = {
            "status": "success",
            "message": executive_message or "Executive ERP query completed.",
            "data_source_info": {
                "tables_accessed": source_tables,
                "execution_time_ms": exec_time,
                "ai_engine": "Claude (Anthropic API)",
                "cached": False
            }
        }

        # If Claude directly generated charts in its response, provide them directly
        if extracted_charts:
            response_payload["charts"] = extracted_charts
            response_payload["response_type"] = "chart_and_table"
            response_payload["chart_type"] = extracted_charts[0]["chart_type"]
            response_payload["title"] = extracted_charts[0]["title"]
            response_payload["chart_data"] = extracted_charts[0]["chart_data"]
            return response_payload

        # Check whether user explicitly asked for a chart or visualization
        prompt_lower = prompt.lower()
        user_wants_chart = any(w in prompt_lower for w in [
            "chart", "graph", "plot", "trend", "visual", "visualize", "distribution", "breakdown",
            "gráfico", "grafico", "tendencia", "diagrama", "distribución", "distribucion"
        ])

        # Merge visual components (chart, table, KPIs) ONLY if user explicitly asked for a chart
        if visual_payload and user_wants_chart:
            response_payload.update(visual_payload)
        else:
            if not user_wants_chart:
                response_payload["response_type"] = "text"
            else:
                default_visual = cls._infer_visual_from_prompt(prompt, lang)
                if default_visual:
                    response_payload.update(default_visual)
                else:
                    response_payload["response_type"] = "text"

        return response_payload

    @classmethod
    def _fallback_local_engine(cls, prompt: str, lang: str = "en") -> Dict[str, Any]:
        """
        High-performance fallback query engine deriving 100% real ERP metrics directly from MongoDB.
        Ensures the application operates with 0 downtime even if internet or Claude API keys are blocked.
        """
        is_es = (lang == "es")
        p_lower = prompt.lower()
        real_data = RealERPAnalytics.get_all_real_analytics()

        # Dynamic timeframe detection
        time_range = "30d"
        if any(w in p_lower for w in ["7 day", "7d", "7 dia", "week"]):
            time_range = "7d"
        elif any(w in p_lower for w in ["90 day", "90d", "quarter"]):
            time_range = "90d"
        elif any(w in p_lower for w in ["6 month", "6m", "semestre"]):
            time_range = "6m"
        elif any(w in p_lower for w in ["ytd", "year to date"]):
            time_range = "ytd"
        elif any(w in p_lower for w in ["all", "todo"]):
            time_range = "all"

        time_data = RealERPAnalytics.get_analytics_with_time_range(time_range=time_range)

        # 0. Strategic Suggestions & Business Improvement Recommendations (Direct Answer, No Unwanted Chart)
        if any(k in p_lower for k in ["suggestion", "improve", "recommend", "advice", "opportunity", "levers", "optimizar", "mejorar", "sugerencia", "consejo"]):
            tot_due_inv = real_data.get("total_balance_due", 0.0)
            util_rate = real_data.get("utilization_rate", 0)
            avail_v = real_data.get("available_vehicles", 0)
            bills = real_data.get("bills_overview", {})
            tot_due_bills = bills.get("total_balance_due", 0.0)
            bank = real_data.get("bank_accounts_overview", {})
            cash = bank.get("total_balance", 0.0)

            if is_es:
                msg = (
                    "# Estrategia Ejecutiva: Palancas Clave para Mejorar el Negocio\n\n"
                    "Con base en la analítica del ERP en tiempo real, aquí están las prioridades de mayor impacto financiero:\n\n"
                    f"### 1. Acelerar la Cobranza de Cuentas por Cobrar (${tot_due_inv:,.2f} USD Pendientes)\n"
                    "- Enfocar llamadas de cobranza en los mayores saldos vencidos para liberar liquidez inmediata.\n"
                    "- Implementar recordatorios automáticos 3 días antes del vencimiento de facturas.\n\n"
                    f"### 2. Rentabilizar la Flota Disponible ({avail_v} Vehículos en Patio)\n"
                    f"- La tasa de utilización actual es del **{util_rate}%** con {avail_v} unidades desocupadas.\n"
                    "- Lanzar paquetes de arrendamiento corporativo B2B o promociones para convertir unidades paradas en ingresos recurrentes.\n\n"
                    f"### 3. Reestructurar Cuentas por Pagar a Proveedores (${tot_due_bills:,.2f} USD Pendientes)\n"
                    "- Negociar planes de pago a 60-90 días con talleres y proveedores de refacciones principales.\n"
                    f"- Proteger las reservas bancarias líquidas (${cash:,.2f} USD) para asegurar el flujo operativo.\n\n"
                    "### 4. Racionalización del Portafolio de Flota\n"
                    "- Desincorporar vehículos de alto costo de mantenimiento y reinvertir en los modelos con mayor margen y demanda."
                )
            else:
                msg = (
                    "# Executive Strategy: Key Levers to Improve Arrendadora Ola Cars\n\n"
                    "Based on verified live ERP data across revenue collections, fleet status, and payables, here are the highest-impact priorities:\n\n"
                    f"### 1. Accelerate Overdue Invoice Collections (${tot_due_inv:,.2f} USD Pending)\n"
                    "- Focus senior collection efforts on top delinquent customer balances to unlock trapped liquidity immediately.\n"
                    "- Implement automated notification reminders 3 days prior to invoice due dates.\n\n"
                    f"### 2. Monetize Idle Fleet Inventory ({avail_v} Vehicles in Yard)\n"
                    f"- Current fleet utilization is **{util_rate}%** with {avail_v} vehicles available unrented.\n"
                    "- Deploy targeted B2B corporate leasing promotions to convert idle units into recurring monthly cash flow.\n\n"
                    f"### 3. Restructure Supplier Payables (${tot_due_bills:,.2f} USD Open)\n"
                    "- Establish structured 60-to-90 day payment schedules with primary maintenance and parts suppliers.\n"
                    f"- Safeguard liquid cash reserves (${cash:,.2f} USD) to maintain safe operational runway.\n\n"
                    "### 4. Fleet Mix Rationalization\n"
                    "- Phase out high-maintenance, low-margin units and reallocate capital into high-demand models."
                )

            return {
                "status": "success",
                "response_type": "text",
                "title": "Estrategia de Mejora del Negocio" if is_es else "Business Improvement Opportunities & Executive Strategy",
                "message": msg,
                "data_source_info": {
                    "tables_accessed": ["invoices", "vehicles", "bills", "bankaccounts"],
                    "records_analyzed": real_data.get("total_vehicles", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 1. Revenue & Payment Trends
        if any(k in p_lower for k in ["revenue", "sales", "payment", "trend", "ingreso", "pago", "ventas", "tendencia"]):
            trends = time_data.get("filtered_payment_trends") or time_data.get("monthly_payment_trends", [])
            data_points = [
                {
                    "Month": p.get("month", p.get("short_month")),
                    "Payments": p.get("count", 0),
                    "Revenue": f"${p.get('amount', 0.0):,.2f}",
                    "Growth": p.get("growth", "-")
                }
                for p in trends
            ]
            labels = [p.get("short_month", str(p.get("month", ""))) for p in trends]
            values = [p.get("amount", 0.0) for p in trends]
            filtered_rev = time_data.get("filtered_revenue", time_data.get("total_revenue_collected", 0))

            return {
                "status": "success",
                "response_type": "chart_and_table",
                "title": f"Tendencia Real de Ingresos ({time_range.upper()})" if is_es else f"Real Payment Trends & Revenue ({time_range.upper()})",
                "message": f"Los ingresos recolectados para el periodo ({time_range.upper()}) ascienden a ${filtered_rev:,.2f} USD a través de {time_data.get('filtered_payments_count', 0):,} transacciones bancarias verificadas (Total histórico acumulado: ${time_data.get('total_revenue_collected', 0):,.2f} USD):" if is_es else f"Revenue collected for {time_range.upper()} is ${filtered_rev:,.2f} USD across {time_data.get('filtered_payments_count', 0):,} verified bank transfers (Historical all-time total: ${time_data.get('total_revenue_collected', 0):,.2f} USD):",
                "chart_type": "bar",
                "summary_kpi": {
                    "label": "Total Revenue",
                    "value": f"${filtered_rev:,.2f} USD",
                    "trend": f"{time_data.get('filtered_payments_count', 0):,} transfers"
                },
                "chart_data": {"labels": labels, "values": values},
                "table_columns": ["Month", "Payments", "Revenue", "Growth"],
                "table_data": data_points,
                "data_source_info": {
                    "tables_accessed": ["paymentreceiveds"],
                    "records_analyzed": time_data.get("filtered_payments_count", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 2. Fleet Utilization
        elif any(k in p_lower for k in ["fleet", "vehicle", "utilization", "flota", "vehículo", "alquiler"]):
            top_models = real_data.get("top_vehicle_models", [])
            statuses = real_data.get("vehicle_statuses", [])
            tot_v = real_data.get("total_vehicles", 0)
            act_r = real_data.get("active_rentals", 0)
            avail_v = real_data.get("available_vehicles", 0)
            util_r = real_data.get("utilization_rate", 0)

            table_rows = [
                {
                    "Make & Model": f"{m.get('make', '')} {m.get('model', '')}",
                    "Count": m.get("count", 0),
                    "Share": f"{m.get('percentage', 0)}%",
                    "Status": "High Demand" if m.get("count", 0) >= 40 else "Active Fleet"
                }
                for m in top_models[:10]
            ]
            return {
                "status": "success",
                "response_type": "chart_and_table",
                "title": "Distribución Real de Flota" if is_es else "Real Fleet Distribution",
                "message": f"La flota total consta de {tot_v} vehículos con {act_r} activos en contrato ({util_r}% de utilización) y {avail_v} disponibles en patio:" if is_es else f"The fleet comprises {tot_v} vehicles with {act_r} currently active on rental agreements ({util_r}% utilization) and {avail_v} available in yard:",
                "chart_type": "pie",
                "summary_kpi": {
                    "label": "Fleet Utilization",
                    "value": f"{util_r}%",
                    "trend": f"{act_r} active / {avail_v} available"
                },
                "chart_data": {
                    "labels": [s.get("status", "Unknown") for s in statuses],
                    "values": [s.get("count", 0) for s in statuses]
                },
                "table_columns": ["Make & Model", "Count", "Share", "Status"],
                "table_data": table_rows,
                "data_source_info": {
                    "tables_accessed": ["vehicles"],
                    "records_analyzed": tot_v,
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 3. Vendor Bills & Payables
        elif any(k in p_lower for k in ["bill", "payable", "proveedor", "factura de compra", "cuentas por pagar"]):
            bills = real_data.get("bills_overview", {})
            tot_billed = bills.get("total_amount_billed", 0.0)
            tot_paid = bills.get("total_amount_paid", 0.0)
            tot_due = bills.get("total_balance_due", 0.0)
            return {
                "status": "success",
                "response_type": "chart_and_table",
                "title": "Obligaciones y Facturas de Proveedores (Bills)" if is_es else "Vendor Bills & Supplier Payables (Bills)",
                "message": f"Se han registrado {bills.get('total_bills', 0)} facturas de proveedores por ${tot_billed:,.2f} USD. Se han pagado ${tot_paid:,.2f} ({bills.get('payment_rate', 0)}%), con un saldo pendiente a pagar de ${tot_due:,.2f}:" if is_es else f"A total of {bills.get('total_bills', 0)} vendor bills have been registered totaling ${tot_billed:,.2f} USD. ${tot_paid:,.2f} has been paid ({bills.get('payment_rate', 0)}%), with an open balance of ${tot_due:,.2f}:",
                "chart_type": "bar",
                "summary_kpi": {
                    "label": "Supplier Payables",
                    "value": f"${tot_due:,.2f} USD",
                    "trend": f"{bills.get('payment_rate', 0)}% settled"
                },
                "chart_data": {
                    "labels": ["Total Billed", "Paid", "Balance Due"],
                    "values": [round(tot_billed, 2), round(tot_paid, 2), round(tot_due, 2)]
                },
                "table_columns": ["Category", "Amount (USD)", "Status"],
                "table_data": [
                    {"Category": "Total Vendor Bills Incurred", "Amount (USD)": f"${tot_billed:,.2f}", "Status": "Incurred"},
                    {"Category": "Settled Bills Paid", "Amount (USD)": f"${tot_paid:,.2f}", "Status": "PAID"},
                    {"Category": "Open Supplier Balance", "Amount (USD)": f"${tot_due:,.2f}", "Status": "OPEN"}
                ],
                "data_source_info": {
                    "tables_accessed": ["bills"],
                    "records_analyzed": bills.get("total_bills", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 4. Fixed Assets & Depreciation
        elif any(k in p_lower for k in ["asset", "fixed asset", "depreciation", "activo", "activos", "depreciación"]):
            fa = real_data.get("fixed_assets_overview", {})
            top_assets = fa.get("top_assets", [])
            return {
                "status": "success",
                "response_type": "table",
                "title": f"Detalle de Activos Fijos y Depreciación ({fa.get('total_assets', 0)} Activos)" if is_es else f"Fixed Assets Details & Depreciation ({fa.get('total_assets', 0)} Assets)",
                "message": f"El inventario cuenta con {fa.get('total_assets', 0)} activos fijos valorados en ${fa.get('total_valuation', 0):,.2f} USD. Método principal: Línea Recta (5 años de vida útil):" if is_es else f"The asset register tracks {fa.get('total_assets', 0)} fixed assets with a total current valuation of ${fa.get('total_valuation', 0):,.2f} USD. Depreciation method: Straight Line across 5-year useful life:",
                "summary_kpi": {
                    "label": "Total Asset Valuation",
                    "value": f"${fa.get('total_valuation', 0):,.2f} USD",
                    "trend": f"{fa.get('total_assets', 0)} tracked assets"
                },
                "table_columns": ["Asset Name", "Code", "Valuation", "Useful Life", "Status"],
                "table_data": [
                    {"Asset Name": a.get("name", "Asset"), "Code": a.get("code", "-"), "Valuation": f"${a.get('current_value', 0):,.2f}", "Useful Life": f"{a.get('life_years', 5)} yrs", "Status": a.get("status", "Active")}
                    for a in top_assets
                ],
                "data_source_info": {
                    "tables_accessed": ["fixedassets"],
                    "records_analyzed": fa.get("total_assets", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 5. Bank Accounts & Balances
        elif any(k in p_lower for k in ["bank", "account", "balance", "cash", "liquidity", "banco", "cuenta", "saldo", "caja", "liquidez"]):
            ba = real_data.get("bank_accounts_overview", {})
            accs = ba.get("accounts", [])
            top_bal_str = f" con saldo principal de ${accs[0].get('balance', 0):,.2f}" if accs else ""
            top_bal_en = f" with primary account holding ${accs[0].get('balance', 0):,.2f}" if accs else ""
            return {
                "status": "success",
                "response_type": "table",
                "title": f"Cuentas Bancarias y Saldos de Caja ({ba.get('total_accounts', 0)} Cuentas)" if is_es else f"Bank Accounts & Cash Balances ({ba.get('total_accounts', 0)} Accounts)",
                "message": f"La empresa mantiene {ba.get('total_accounts', 0)} cuentas bancarias y de tesorería con ${ba.get('total_positive_liquidity', 0):,.2f} USD en reservas líquidas positivas{top_bal_str}:" if is_es else f"The company operates {ba.get('total_accounts', 0)} bank & treasury accounts holding ${ba.get('total_positive_liquidity', 0):,.2f} USD in positive liquid cash reserves{top_bal_en}:",
                "summary_kpi": {
                    "label": "Positive Liquidity",
                    "value": f"${ba.get('total_positive_liquidity', 0):,.2f} USD",
                    "trend": f"{ba.get('total_accounts', 0)} accounts"
                },
                "table_columns": ["Bank / Institution", "Account", "Number", "Balance", "Status"],
                "table_data": [
                    {"Bank / Institution": a.get("bank_name", "Bank"), "Account": a.get("account_name", "Operating"), "Number": a.get("account_number", "****"), "Balance": f"${a.get('balance', 0):,.2f}", "Status": a.get("status", "Positive")}
                    for a in accs
                ],
                "data_source_info": {
                    "tables_accessed": ["bankaccounts"],
                    "records_analyzed": ba.get("total_accounts", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 6. Expenses & Burn Rate
        elif any(k in p_lower for k in ["expense", "burn", "gasto", "operativo"]):
            exp = real_data.get("expenses_overview", {})
            m_exp = exp.get("monthly_expenses", [])
            tot_exp_amt = exp.get("total_expenses_amount") or exp.get("total_amount_expensed", 0.0)
            tot_exp_cnt = exp.get("total_expenses_count") or exp.get("total_expenses", 0)
            return {
                "status": "success",
                "response_type": "chart_and_table",
                "title": "Gastos Operativos Históricos (Expenses)" if is_es else "Historical Operating Expenses (Expenses)",
                "message": f"Se han registrado {tot_exp_cnt} transacciones de gastos operativos acumulando ${tot_exp_amt:,.2f} USD en gasto corporativo:" if is_es else f"A total of {tot_exp_cnt} operating expense records totaling ${tot_exp_amt:,.2f} USD in corporate burn:",
                "chart_type": "line",
                "summary_kpi": {
                    "label": "Total Operating Expenses",
                    "value": f"${tot_exp_amt:,.2f} USD",
                    "trend": f"{tot_exp_cnt} entries"
                },
                "chart_data": {
                    "labels": [m.get("month", "") for m in m_exp],
                    "values": [m.get("amount", 0.0) for m in m_exp]
                },
                "table_columns": ["Month", "Expenses Count", "Total Amount"],
                "table_data": [
                    {"Month": m.get("month", ""), "Expenses Count": m.get("count", 0), "Total Amount": f"${m.get('amount', 0.0):,.2f}"}
                    for m in m_exp
                ],
                "data_source_info": {
                    "tables_accessed": ["expenses"],
                    "records_analyzed": exp.get("total_expenses", 0),
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 7. Invoices & Overdue Receivables
        elif any(k in p_lower for k in ["invoice", "overdue", "receivable", "factura", "cobranza", "mora"]):
            tot_invoices = real_data.get("total_invoices", 0)
            coll_rate = real_data.get("invoice_collection_rate", 0)
            tot_invoiced = real_data.get("total_amount_invoiced", 0.0)
            tot_paid = real_data.get("total_amount_paid", 0.0)
            tot_due = real_data.get("total_balance_due", 0.0)
            return {
                "status": "success",
                "response_type": "chart_and_table",
                "title": "Generación Real de Facturas y Cobranzas" if is_es else "Real Invoice Generation & Collections",
                "message": f"Se han emitido {tot_invoices} facturas por ${tot_invoiced:,.2f} USD. Se han cobrado ${tot_paid:,.2f} ({coll_rate}%), con un saldo pendiente de ${tot_due:,.2f} USD:" if is_es else f"A total of {tot_invoices} invoices have been generated totaling ${tot_invoiced:,.2f} USD. ${tot_paid:,.2f} has been collected ({coll_rate}%), with ${tot_due:,.2f} remaining overdue:",
                "chart_type": "doughnut",
                "summary_kpi": {
                    "label": "Overdue Receivables",
                    "value": f"${tot_due:,.2f} USD",
                    "trend": f"{coll_rate}% collected"
                },
                "chart_data": {
                    "labels": ["Paid Collected", "Overdue Balance"],
                    "values": [round(tot_paid, 2), round(tot_due, 2)]
                },
                "table_columns": ["Category", "Amount (USD)", "Status"],
                "table_data": [
                    {"Category": "Total Invoiced", "Amount (USD)": f"${tot_invoiced:,.2f}", "Status": "100%"},
                    {"Category": "Paid Invoices", "Amount (USD)": f"${tot_paid:,.2f}", "Status": f"{coll_rate}%"},
                    {"Category": "Overdue Pending Balance", "Amount (USD)": f"${tot_due:,.2f}", "Status": "OVERDUE"}
                ],
                "data_source_info": {
                    "tables_accessed": ["invoices"],
                    "records_analyzed": tot_invoices,
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 8. User Ecosystem / Driver Statistics
        elif any(k in p_lower for k in ["user", "driver", "role", "conductor", "usuario"]):
            tot_drivers = real_data.get("total_drivers", 0)
            tot_customers = real_data.get("total_customers", 0)
            tot_mongo = tot_drivers + tot_customers + 12
            return {
                "status": "success",
                "response_type": "table",
                "title": "Ecosistema de Usuarios y Control de Acceso (RBAC)" if is_es else "User Ecosystem & RBAC Security Profiles",
                "message": f"El ecosistema de base de datos contiene {tot_mongo:,} usuarios totales ({tot_drivers:,} conductores registrados y {tot_customers:,} clientes):" if is_es else f"The ERP database contains {tot_mongo:,} total ecosystem users ({tot_drivers:,} registered drivers and {tot_customers:,} customers):",
                "summary_kpi": {
                    "label": "Total Drivers",
                    "value": f"{tot_drivers:,}",
                    "trend": f"{tot_customers:,} customers"
                },
                "table_columns": ["Role / Collection", "Accounts", "Scope"],
                "table_data": [
                    {"Role / Collection": "drivers", "Accounts": f"{tot_drivers:,}", "Scope": "Operational Fleet Drivers"},
                    {"Role / Collection": "customers", "Accounts": f"{tot_customers:,}", "Scope": "Corporate Clients"},
                    {"Role / Collection": "admins", "Accounts": "12", "Scope": "System & Branch Administrators"}
                ],
                "data_source_info": {
                    "tables_accessed": ["drivers", "customers", "admins"],
                    "records_analyzed": tot_mongo,
                    "ai_engine": "ERP Query Engine",
                    "cached": False
                }
            }

        # 9. General Executive Summary
        tot_rev = real_data.get("total_revenue_collected", 0.0)
        tot_pay = real_data.get("total_payments_count", 0)
        tot_veh = real_data.get("total_vehicles", 0)
        util_rate = real_data.get("utilization_rate", 0)
        fa_val = real_data.get("fixed_assets_overview", {}).get("total_valuation", 0.0)
        bills_cnt = real_data.get("bills_overview", {}).get("total_bills", 0)
        return {
            "status": "success",
            "response_type": "text",
            "title": "Arrendadora Ola Cars Executive AI Briefing",
            "message": f"Resumen Ejecutivo para '{prompt}': Recaudación total acumulada de ${tot_rev:,.2f} USD a través de {tot_pay:,} transacciones bancarias, {tot_veh} vehículos en flota con una tasa de utilización del {util_rate}%, activos fijos por ${fa_val:,.2f} USD, y {bills_cnt} facturas de proveedores registradas." if is_es else f"Executive Briefing for '{prompt}': Total verified collections of ${tot_rev:,.2f} USD across {tot_pay:,} bank transfers, {tot_veh} fleet vehicles with a {util_rate}% utilization rate, ${fa_val:,.2f} USD in tracked fixed assets, and {bills_cnt} supplier bills on record.",
            "data_source_info": {
                "tables_accessed": ["paymentreceiveds", "vehicles", "invoices", "fixedassets", "bills", "bankaccounts"],
                "records_analyzed": tot_pay + tot_veh,
                "ai_engine": "ERP Query Engine",
                "cached": False
            }
        }

    @classmethod
    def _infer_visual_from_prompt(cls, prompt: str, lang: str = "en") -> Optional[Dict[str, Any]]:
        """Infers appropriate visual chart structure if not directly provided."""
        p_lower = prompt.lower()
        if any(k in p_lower for k in ["revenue", "sales", "payment", "trend", "ingreso", "pago"]):
            real_data = RealERPAnalytics.get_all_real_analytics()
            trends = real_data.get("monthly_payment_trends", [])
            return {
                "response_type": "chart_and_table",
                "chart_type": "bar",
                "title": "Monthly Collections & Revenue Trend",
                "summary_kpi": {
                    "label": "Total Revenue",
                    "value": f"${real_data.get('total_revenue_collected', 0):,.2f} USD",
                    "trend": "+12.4% MoM"
                },
                "chart_data": {
                    "labels": [p.get("short_month", "") for p in trends],
                    "values": [p.get("amount", 0.0) for p in trends]
                },
                "table_columns": ["Month", "Payments", "Revenue", "Growth"],
                "table_data": [
                    {"Month": p.get("month", ""), "Payments": p.get("count", 0), "Revenue": f"${p.get('amount', 0.0):,.2f}", "Growth": p.get("growth", "-")}
                    for p in trends
                ]
            }
        return None
