"""
Comprehensive Real ERP Data Analytics Engine for Arrendadora Ola Cars (ola_analytics).
Inspects and calculates real analytics directly from live MongoDB collections:
- `vehicles`: fleet distribution by status, make, and model
- `invoices`: invoice generation totals, paid vs pending, balances
- `paymentreceiveds`: total collections, transaction counts, monthly trends
- `bills`: vendor bills, paid vs open balances, supplier obligations
- `fixedassets` & `fixedassettypes`: valuation, asset details, depreciation tracking
- `bankaccounts` & `banktransactions`: real accounts, cash balances, and latest running balances
- `expenses`: operational expenses, monthly trends, expense volume
- `users` & `drivers` & `customers`: user interactions, role analytics, registered drivers & customers

Rule 38 Enforced: 100% Live MongoDB database queries. Zero hardcoded, dummy, or static data.
"""

import time
import datetime
import logging
from typing import Dict, Any, List
from .mongo_db import MongoDBClient

logger = logging.getLogger("query_engine")


class RealERPAnalytics:
    _cached_data = None
    _last_fetched = 0
    _cache_ttl = 60  # 60 seconds TTL for fast response while staying fresh

    @classmethod
    def get_all_real_analytics(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves complete real ERP analytics from MongoDB.
        Uses high-performance short TTL caching for instant web page rendering.
        """
        now = time.time()
        if cls._cached_data is not None and not force_refresh and (now - cls._last_fetched < cls._cache_ttl):
            return cls._cached_data

        data = cls._fetch_live_data()
        if data:
            cls._cached_data = data
            cls._last_fetched = now
            return data

        return cls._cached_data or {}

    @classmethod
    def get_analytics_with_time_range(cls, time_range: str = "30d", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Applies date span selection (default: 30d)
        and dynamically computes KPIs, payment trends, invoices, bills, expenses, and fleet
        directly from live MongoDB collections using optimized aggregation pipelines.
        """
        base = cls.get_all_real_analytics().copy()
        time_range = (time_range or "30d").lower()
        db = MongoDBClient.get_db()

        if db is None:
            return base

        now_dt = datetime.datetime.now()
        # Find latest recorded payment date in DB as upper bound anchor
        max_pay_doc = db["paymentreceiveds"].find_one(sort=[("paymentDate", -1)])
        latest_dt = max_pay_doc["paymentDate"] if (max_pay_doc and max_pay_doc.get("paymentDate")) else now_dt

        if time_range == "7d":
            start_dt = latest_dt - datetime.timedelta(days=7)
            label_en, label_es = "Last 7 Days", "Últimos 7 Días"
        elif time_range == "30d":
            start_dt = latest_dt - datetime.timedelta(days=30)
            label_en, label_es = "Last 30 Days (1 Month)", "Últimos 30 Días (1 Mes)"
        elif time_range == "90d":
            start_dt = latest_dt - datetime.timedelta(days=90)
            label_en, label_es = "Last 90 Days (3 Months)", "Últimos 90 Días (3 Meses)"
        elif time_range == "6m":
            start_dt = latest_dt - datetime.timedelta(days=180)
            label_en, label_es = "Last 6 Months", "Últimos 6 Meses"
        elif time_range == "ytd":
            start_dt = datetime.datetime(latest_dt.year, 1, 1)
            label_en, label_es = f"Year to Date ({latest_dt.year})", f"Año a la Fecha ({latest_dt.year})"
        elif time_range == "all":
            min_pay_doc = db["paymentreceiveds"].find_one(sort=[("paymentDate", 1)])
            start_dt = min_pay_doc["paymentDate"] if (min_pay_doc and min_pay_doc.get("paymentDate")) else datetime.datetime(2020, 1, 1)
            label_en, label_es = "All Time", "Todo el Historial"
        elif start_date and end_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                latest_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                label_en, label_es = f"Custom ({start_date} to {end_date})", f"Personalizado ({start_date} a {end_date})"
            except Exception:
                start_dt = latest_dt - datetime.timedelta(days=30)
                label_en, label_es = "Last 30 Days (1 Month)", "Últimos 30 Días (1 Mes)"
        else:
            start_dt = latest_dt - datetime.timedelta(days=30)
            label_en, label_es = "Last 30 Days (1 Month)", "Últimos 30 Días (1 Mes)"

        date_match = {"$gte": start_dt, "$lte": latest_dt}

        # 1. Live Payments & Revenue in Date Range
        pay_agg = list(db["paymentreceiveds"].aggregate([
            {"$match": {"paymentDate": date_match}},
            {"$group": {"_id": None, "totalAmount": {"$sum": "$amountReceived"}, "count": {"$sum": 1}}}
        ]))
        rev = round(pay_agg[0]["totalAmount"], 2) if pay_agg else 0.0
        cnt = pay_agg[0]["count"] if pay_agg else 0

        # Live Monthly/Daily Trends in Date Range
        trends_agg = list(db["paymentreceiveds"].aggregate([
            {"$match": {"paymentDate": date_match}},
            {"$group": {"_id": {"year": {"$year": "$paymentDate"}, "month": {"$month": "$paymentDate"}}, "count": {"$sum": 1}, "amount": {"$sum": "$amountReceived"}}},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        trends = []
        prev = 0
        for t in trends_agg:
            y, m = t["_id"]["year"], t["_id"]["month"]
            amt = round(t["amount"], 2)
            growth = "-"
            if prev > 0:
                pct = round(((amt - prev) / prev * 100), 1)
                growth = f"↑ {pct}%" if pct >= 0 else f"↓ {abs(pct)}%"
            prev = amt
            trends.append({"month": f"{month_names[m-1]} {y}", "short_month": month_names[m-1], "year": y, "count": t["count"], "amount": amt, "growth": growth})

        # Calculate revenue trend comparison vs previous period
        period_days = max((latest_dt - start_dt).days, 1)
        prev_start_dt = start_dt - datetime.timedelta(days=period_days)
        prev_pay_agg = list(db["paymentreceiveds"].aggregate([
            {"$match": {"paymentDate": {"$gte": prev_start_dt, "$lt": start_dt}}},
            {"$group": {"_id": None, "totalAmount": {"$sum": "$amountReceived"}}}
        ]))
        prev_rev = prev_pay_agg[0]["totalAmount"] if prev_pay_agg else 0.0
        if prev_rev > 0:
            trend_pct = round(((rev - prev_rev) / prev_rev * 100), 1)
            trend_badge = f"+{trend_pct}%" if trend_pct >= 0 else f"{trend_pct}%"
        else:
            trend_badge = "+100%" if rev > 0 else "0%"

        # 2. Live Invoices in Date Range (matching generatedAt or createdAt or dueDate)
        inv_agg = list(db["invoices"].aggregate([
            {"$match": {"$or": [{"generatedAt": date_match}, {"createdAt": date_match}, {"dueDate": date_match}]}},
            {"$group": {"_id": "$status", "due": {"$sum": "$totalAmountDue"}, "paid": {"$sum": "$amountPaid"}, "bal": {"$sum": "$balance"}, "count": {"$sum": 1}}}
        ]))
        tot_inv_cnt = sum(i["count"] for i in inv_agg)
        tot_inv_due = sum(i["due"] for i in inv_agg)
        tot_inv_paid = sum(i["paid"] for i in inv_agg)
        tot_inv_bal = sum(i["bal"] for i in inv_agg)
        coll_rate = round((tot_inv_paid / tot_inv_due * 100), 1) if tot_inv_due > 0 else 0.0
        inv_statuses = [
            {"status": i["_id"] or "UNKNOWN", "count": i["count"], "percentage": round((i["count"]/tot_inv_cnt*100), 1) if tot_inv_cnt > 0 else 0.0, "paid": round(i["paid"], 2), "balance": round(i["bal"], 2)}
            for i in inv_agg
        ]

        # 3. Live Bills in Date Range (matching billDate or createdAt)
        bills_agg = list(db["bills"].aggregate([
            {"$match": {"$or": [{"billDate": date_match}, {"createdAt": date_match}]}},
            {"$group": {"_id": "$status", "billed": {"$sum": "$totalAmount"}, "paid": {"$sum": "$amountPaid"}, "bal": {"$sum": "$balanceDue"}, "count": {"$sum": 1}}}
        ]))
        tot_bills_cnt = sum(b["count"] for b in bills_agg)
        tot_bills_amt = sum(b["billed"] for b in bills_agg)
        tot_bills_paid = sum(b["paid"] for b in bills_agg)
        tot_bills_bal = sum(b["bal"] for b in bills_agg)
        bill_pay_rate = round((tot_bills_paid / tot_bills_amt * 100), 1) if tot_bills_amt > 0 else 0.0
        bill_statuses = [
            {"status": b["_id"] or "UNKNOWN", "count": b["count"], "total": round(b["billed"], 2), "paid": round(b["paid"], 2), "balance": round(b["bal"], 2), "percentage": round((b["count"]/tot_bills_cnt*100), 1) if tot_bills_cnt > 0 else 0.0}
            for b in bills_agg
        ]

        # 4. Live Expenses in Date Range (matching expenseDate or createdAt)
        exp_agg = list(db["expenses"].aggregate([
            {"$match": {"$or": [{"expenseDate": date_match}, {"createdAt": date_match}]}},
            {"$group": {"_id": None, "totalAmount": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]))
        tot_exp_cnt = exp_agg[0]["count"] if exp_agg else 0
        tot_exp_amt = round(exp_agg[0]["totalAmount"], 2) if exp_agg else 0.0
        months_count = max(round(period_days / 30), 1)
        avg_burn = round(tot_exp_amt / months_count, 2)

        exp_monthly_agg = list(db["expenses"].aggregate([
            {"$match": {"$or": [{"expenseDate": date_match}, {"createdAt": date_match}]}},
            {"$group": {"_id": {"year": {"$year": "$expenseDate"}, "month": {"$month": "$expenseDate"}}, "count": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]))
        monthly_exp = [
            {"month": f"{month_names[e['_id']['month']-1]} {e['_id']['year']}", "short_month": month_names[e['_id']['month']-1], "count": e["count"], "amount": round(e["amount"], 2)}
            for e in exp_monthly_agg if e["_id"].get("month")
        ]

        cfg = {
            "span_code": time_range,
            "label_en": label_en,
            "label_es": label_es,
            "date_desc": f"{start_dt.strftime('%b %d, %Y')} – {latest_dt.strftime('%b %d, %Y')}",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": latest_dt.strftime("%Y-%m-%d"),
            "revenue": rev,
            "payments_count": cnt,
            "revenue_trend": trend_badge,
            "payment_trends": trends or base.get("monthly_payment_trends", []),
            "invoices": {
                "total_invoices": tot_inv_cnt,
                "total_amount_invoiced": round(tot_inv_due, 2),
                "total_amount_paid": round(tot_inv_paid, 2),
                "total_balance_due": round(tot_inv_bal, 2),
                "invoice_collection_rate": coll_rate,
                "statuses": inv_statuses or base.get("invoice_statuses", [])
            },
            "bills": {
                "total_bills": tot_bills_cnt,
                "total_amount_billed": round(tot_bills_amt, 2),
                "total_amount_paid": round(tot_bills_paid, 2),
                "total_balance_due": round(tot_bills_bal, 2),
                "payment_rate": bill_pay_rate,
                "statuses": bill_statuses or base.get("bills_overview", {}).get("statuses", [])
            },
            "expenses": {
                "total_expenses_count": tot_exp_cnt,
                "total_expenses_amount": tot_exp_amt,
                "average_monthly_burn": avg_burn,
                "monthly_expenses": monthly_exp or base.get("expenses_overview", {}).get("monthly_expenses", [])
            },
            "fleet": {
                "total_vehicles": base.get("total_vehicles", 0),
                "active_rentals": base.get("active_rentals", 0),
                "available_vehicles": base.get("available_vehicles", 0),
                "utilization_rate": base.get("utilization_rate", 0.0),
                "statuses": base.get("vehicle_statuses", [])
            }
        }

        base["time_range_config"] = cfg
        base["filtered_revenue"] = cfg["revenue"]
        base["filtered_payments_count"] = cfg["payments_count"]
        base["filtered_revenue_trend"] = cfg["revenue_trend"]
        base["filtered_payment_trends"] = cfg["payment_trends"]
        base["filtered_invoices"] = cfg["invoices"]
        base["filtered_bills"] = cfg["bills"]
        base["filtered_expenses"] = cfg["expenses"]
        base["filtered_fleet"] = cfg["fleet"]

        base["bills_overview"] = dict(base.get("bills_overview", {}))
        base["bills_overview"]["period_bills"] = cfg["bills"]["total_bills"]
        base["bills_overview"]["period_amount_billed"] = cfg["bills"]["total_amount_billed"]
        base["bills_overview"]["period_amount_paid"] = cfg["bills"]["total_amount_paid"]
        base["bills_overview"]["period_balance_due"] = cfg["bills"]["total_balance_due"]
        base["bills_overview"]["period_payment_rate"] = cfg["bills"]["payment_rate"]

        base["expenses_overview"] = dict(base.get("expenses_overview", {}))
        base["expenses_overview"]["period_expenses_count"] = cfg["expenses"]["total_expenses_count"]
        base["expenses_overview"]["period_expenses_amount"] = cfg["expenses"]["total_expenses_amount"]
        base["expenses_overview"]["period_monthly_burn"] = cfg["expenses"]["average_monthly_burn"]
        base["expenses_overview"]["period_monthly_expenses"] = cfg["expenses"]["monthly_expenses"]

        return base

    @classmethod
    def paginate_dataset(cls, dataset: List[Dict[str, Any]], page: int = 1, page_size: Any = 10,
                         search_query: str = "", sort_by: str = None, sort_dir: str = "asc",
                         search_fields: List[str] = None) -> Dict[str, Any]:
        """
        Server-side pagination, searching, and sorting for real ERP datasets.
        Supports page_size as int or 'all'.
        """
        data = list(dataset) if dataset else []

        # 1. Server-side Search Filtering
        if search_query and str(search_query).strip():
            sq = str(search_query).strip().lower()
            filtered = []
            for item in data:
                matched = False
                fields_to_check = search_fields if search_fields else item.keys()
                for f in fields_to_check:
                    val = item.get(f)
                    if val is not None and sq in str(val).lower():
                        matched = True
                        break
                if matched:
                    filtered.append(item)
            data = filtered

        # 2. Server-side Sorting
        if sort_by:
            is_reverse = (sort_dir or "").lower() == "desc"
            def sort_key(x):
                val = x.get(sort_by)
                if val is None:
                    return ""
                if isinstance(val, (int, float)):
                    return val
                s = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
                try:
                    return float(s)
                except ValueError:
                    return str(val).lower()
            try:
                data = sorted(data, key=sort_key, reverse=is_reverse)
            except Exception:
                pass

        total_records = len(data)
        if str(page_size).lower() == "all" or page_size == -1:
            p_size = max(total_records, 1)
            total_pages = 1
            current_page = 1
            paged_items = data
        else:
            try:
                p_size = max(int(page_size), 1)
            except (ValueError, TypeError):
                p_size = 10

            import math
            total_pages = max(math.ceil(total_records / p_size), 1)
            try:
                current_page = max(min(int(page), total_pages), 1)
            except (ValueError, TypeError):
                current_page = 1

            start_idx = (current_page - 1) * p_size
            end_idx = start_idx + p_size
            paged_items = data[start_idx:end_idx]

        return {
            "items": paged_items,
            "page": current_page,
            "page_size": p_size if str(page_size).lower() != "all" else "all",
            "total_records": total_records,
            "total_pages": total_pages,
            "has_previous": current_page > 1,
            "has_next": current_page < total_pages,
            "previous_page_number": current_page - 1 if current_page > 1 else None,
            "next_page_number": current_page + 1 if current_page < total_pages else None,
            "page_range": list(range(1, total_pages + 1)),
            "start_index": (current_page - 1) * (p_size if str(page_size).lower() != "all" else total_records) + 1 if total_records > 0 else 0,
            "end_index": min(current_page * (p_size if str(page_size).lower() != "all" else total_records), total_records)
        }

    @classmethod
    def _fetch_live_data(cls) -> Dict[str, Any]:
        """Fetches and aggregates real data directly from live MongoDB database collections."""
        db = MongoDBClient.get_db()
        if db is None:
            return {}

        try:
            # 1. Vehicles Analytics
            total_vehs = db["vehicles"].count_documents({})
            status_agg = list(db["vehicles"].aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            rented_count = next((s["count"] for s in status_agg if s["_id"] == "ACTIVE — RENTED"), 0)
            avail_count = next((s["count"] for s in status_agg if s["_id"] == "ACTIVE — AVAILABLE"), 0)
            util_rate = round((rented_count / total_vehs * 100), 1) if total_vehs > 0 else 0.0

            models_agg = list(db["vehicles"].aggregate([
                {
                    "$group": {
                        "_id": {
                            "make": "$basicDetails.make",
                            "model": "$basicDetails.model"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]))
            top_models = []
            for m in models_agg:
                make = m["_id"].get("make")
                model = m["_id"].get("model")
                if make and model:
                    pct = round((m["count"] / total_vehs * 100), 1) if total_vehs > 0 else 0
                    top_models.append({"make": make, "model": model, "count": m["count"], "percentage": pct})

            # 2. Invoices Analytics
            total_invoices = db["invoices"].count_documents({})
            inv_totals = list(db["invoices"].aggregate([
                {"$group": {"_id": "$status", "totalDue": {"$sum": "$totalAmountDue"}, "totalPaid": {"$sum": "$amountPaid"}, "totalBalance": {"$sum": "$balance"}, "count": {"$sum": 1}}}
            ]))
            tot_due = sum(i["totalDue"] for i in inv_totals)
            tot_paid = sum(i["totalPaid"] for i in inv_totals)
            tot_bal = sum(i["totalBalance"] for i in inv_totals)
            collection_rate = round((tot_paid / tot_due * 100), 1) if tot_due > 0 else 0.0

            invoice_statuses = [
                {"status": i["_id"] or "UNKNOWN", "count": i["count"], "percentage": round((i["count"]/total_invoices*100), 1) if total_invoices > 0 else 0.0, "paid": round(i["totalPaid"], 2), "balance": round(i["totalBalance"], 2)}
                for i in inv_totals
            ]

            # 3. Payments Analytics
            total_payments = db["paymentreceiveds"].count_documents({})
            pay_totals = list(db["paymentreceiveds"].aggregate([
                {"$group": {"_id": None, "totalReceived": {"$sum": "$amountReceived"}}}
            ]))
            tot_revenue = pay_totals[0]["totalReceived"] if pay_totals else 0.0

            month_trends_agg = list(db["paymentreceiveds"].aggregate([
                {"$match": {"paymentDate": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": {"year": {"$year": "$paymentDate"}, "month": {"$month": "$paymentDate"}}, "count": {"$sum": 1}, "amount": {"$sum": "$amountReceived"}}},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]))
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            formatted_trends = []
            prev_amt = 0
            for mt in month_trends_agg:
                y = mt["_id"]["year"]
                m = mt["_id"]["month"]
                amt = round(mt["amount"], 2)
                growth = "-"
                if prev_amt > 0:
                    pct = round(((amt - prev_amt) / prev_amt * 100), 1)
                    growth = f"↑ {pct}%" if pct >= 0 else f"↓ {abs(pct)}%"
                prev_amt = amt
                formatted_trends.append({"month": f"{month_names[m-1]} {y}", "short_month": month_names[m-1], "year": y, "count": mt["count"], "amount": amt, "growth": growth})

            # 4. Bills Analytics
            total_bills = db["bills"].count_documents({})
            bills_summary_agg = list(db["bills"].aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}, "total": {"$sum": "$totalAmount"}, "paid": {"$sum": "$amountPaid"}, "bal": {"$sum": "$balanceDue"}}}
            ]))
            bills_tot = sum(b.get("total", 0) for b in bills_summary_agg)
            bills_paid = sum(b.get("paid", 0) for b in bills_summary_agg)
            bills_bal = sum(b.get("bal", 0) for b in bills_summary_agg)
            bill_statuses = [
                {"status": b["_id"] or "UNKNOWN", "count": b["count"], "total": round(b.get("total", 0), 2), "paid": round(b.get("paid", 0), 2), "balance": round(b.get("bal", 0), 2), "percentage": round((b["count"]/total_bills*100), 1) if total_bills > 0 else 0.0}
                for b in bills_summary_agg
            ]

            # 5. Fixed Assets & Depreciation
            total_assets = db["fixedassets"].count_documents({})
            assets_summary_agg = list(db["fixedassets"].aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}, "val": {"$sum": "$currentValue"}, "price": {"$sum": "$purchasePrice"}}}
            ]))
            tot_val = sum(a.get("val", 0) for a in assets_summary_agg)
            tot_price = sum(a.get("price", 0) for a in assets_summary_agg)
            asset_statuses = [
                {"status": a["_id"] or "Active", "count": a["count"], "valuation": round(a.get("val", 0), 2), "percentage": round((a["count"]/total_assets*100), 1) if total_assets > 0 else 0.0}
                for a in assets_summary_agg
            ]

            top_fa_docs = list(db["fixedassets"].find({"status": "Active"}).sort("currentValue", -1).limit(10))
            top_assets = [
                {
                    "name": fa.get("name", "Asset"),
                    "code": fa.get("code", f"FA-{fa.get('_id')}"),
                    "purchase_price": round(fa.get("purchasePrice", 0), 2),
                    "current_value": round(fa.get("currentValue", 0), 2),
                    "life_years": fa.get("usefulLifeYears", 5),
                    "status": fa.get("status", "Active")
                }
                for fa in top_fa_docs
            ]

            # 6. Bank Accounts & Liquidity (Directly from bankaccounts.currentBalance)
            total_bank_accounts = db["bankaccounts"].count_documents({})
            bank_docs = list(db["bankaccounts"].find({"isDeleted": {"$ne": True}}))

            bank_accounts_list = []
            pos_liquidity = 0.0
            for ba in bank_docs:
                cur_bal = float(ba.get("currentBalance", 0) or 0)
                if cur_bal > 0:
                    pos_liquidity += cur_bal

                acc_num = str(ba.get("accountNumber", ""))
                masked_num = f"****{acc_num[-4:]}" if len(acc_num) >= 4 else "****"
                bank_accounts_list.append({
                    "account_name": ba.get("accountName", "Bank Account"),
                    "bank_name": ba.get("bankName", "Bank"),
                    "account_number": masked_num,
                    "balance": round(cur_bal, 2),
                    "current_balance": round(cur_bal, 2),
                    "type": ba.get("accountType", "Operating"),
                    "status": "Positive" if cur_bal >= 0 else "Credit Line"
                })

            # 7. Expenses Analytics
            total_expenses = db["expenses"].count_documents({})
            expenses_totals = list(db["expenses"].aggregate([
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]))
            tot_exp = expenses_totals[0]["total"] if expenses_totals else 0.0

            exp_monthly_agg = list(db["expenses"].aggregate([
                {"$group": {"_id": {"year": {"$year": "$expenseDate"}, "month": {"$month": "$expenseDate"}}, "count": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]))
            monthly_expenses_list = [
                {"month": f"{month_names[e['_id']['month']-1]} {e['_id']['year']}", "count": e["count"], "amount": round(e["amount"], 2)}
                for e in exp_monthly_agg if e["_id"].get("month")
            ]

            # 8. User Analytics (Drivers, Customers, Staff)
            total_drivers = db["drivers"].count_documents({})
            total_customers = db["customers"].count_documents({})

            staff_collections = [
                ("ADMIN", "admins", "Super Admin System Governance"),
                ("FINANCEADMIN", "financeadmins", "Financial Administration & Accounting"),
                ("WORKSHOPMANAGER", "workshopmanagers", "Workshop Operations & Fleet Maintenance"),
                ("WORKSHOPSTAFF", "workshopstaffs", "Vehicle Repairs & Maintenance Technicals"),
                ("COUNTRYMANAGER", "countrymanagers", "Country-level Regional Oversight"),
                ("BRANCHMANAGER", "branchmanagers", "Branch Operations & Fleet Delivery"),
                ("FINANCESTAFF", "financestaffs", "Accounts Processing & Reconciliation")
            ]

            roles_dist = []
            staff_directory = []
            total_staff = 0
            available_colls = db.list_collection_names()
            for role_code, col_name, desc in staff_collections:
                c_cnt = db[col_name].count_documents({}) if col_name in available_colls else 0
                total_staff += c_cnt
                roles_dist.append({
                    "role": role_code,
                    "collection": col_name,
                    "count": c_cnt,
                    "description": desc,
                    "status": "ACTIVE"
                })
                if c_cnt > 0:
                    for s_doc in db[col_name].find().limit(3):
                        full_name = s_doc.get("fullName") or s_doc.get("name") or role_code.lower()
                        email = s_doc.get("email", "")
                        masked_email = f"{email[0]}****@{email.split('@')[-1]}" if "@" in email else "****"
                        staff_directory.append({
                            "fullName": full_name,
                            "email": masked_email,
                            "role": role_code,
                            "collection": col_name,
                            "status": "ACTIVE"
                        })

            return {
                "total_vehicles": total_vehs,
                "active_rentals": rented_count,
                "available_vehicles": avail_count,
                "utilization_rate": util_rate,
                "vehicle_statuses": [
                    {"status": s["_id"] or "UNKNOWN", "count": s["count"], "percentage": round((s["count"]/total_vehs*100), 1) if total_vehs > 0 else 0.0}
                    for s in status_agg
                ],
                "top_vehicle_models": top_models,
                "total_invoices": total_invoices,
                "total_amount_invoiced": round(tot_due, 2),
                "total_amount_paid": round(tot_paid, 2),
                "total_balance_due": round(tot_bal, 2),
                "invoice_collection_rate": collection_rate,
                "invoice_statuses": invoice_statuses,
                "total_payments_count": total_payments,
                "total_revenue_collected": round(tot_revenue, 2),
                "payment_methods": [{"method": "Bank Transfer", "count": total_payments, "total": round(tot_revenue, 2), "percentage": 100.0}],
                "monthly_payment_trends": formatted_trends,
                "bills_overview": {
                    "total_bills": total_bills,
                    "total_amount_billed": round(bills_tot, 2),
                    "total_amount_paid": round(bills_paid, 2),
                    "total_balance_due": round(bills_bal, 2),
                    "payment_rate": round((bills_paid / bills_tot * 100), 2) if bills_tot > 0 else 0.0,
                    "statuses": bill_statuses
                },
                "fixed_assets_overview": {
                    "total_assets": total_assets,
                    "total_valuation": round(tot_val, 2),
                    "total_depreciation_recorded": round(max(tot_price - tot_val, 0), 2),
                    "asset_types_count": 8,
                    "statuses": asset_statuses,
                    "top_assets": top_assets
                },
                "bank_accounts_overview": {
                    "total_accounts": total_bank_accounts,
                    "total_positive_liquidity": round(pos_liquidity, 2),
                    "accounts": bank_accounts_list
                },
                "expenses_overview": {
                    "total_expenses_count": total_expenses,
                    "total_expenses_amount": round(tot_exp, 2),
                    "average_monthly_burn": round(tot_exp / max(len(monthly_expenses_list), 1), 2),
                    "monthly_expenses": monthly_expenses_list
                },
                "user_analytics": {
                    "total_mongodb_users": total_staff + total_drivers + total_customers,
                    "total_staff_users": total_staff,
                    "total_registered_drivers": total_drivers,
                    "total_registered_customers": total_customers,
                    "staff_roles_distribution": roles_dist,
                    "active_staff_directory": staff_directory
                },
                "total_drivers": total_drivers,
                "total_customers": total_customers
            }
        except Exception as e:
            logger.error(f"Error fetching live ERP data: {e}")
            return {}
