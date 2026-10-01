"""
MongoDB Access Layer for Ola Analytics.
Connects directly to the live Ola Cars ERP MongoDB database (olaCarsFresh) in READ-ONLY mode.
Provides collection querying, SQL-to-Mongo translation, and live document joins for Drivers, Vehicles, Invoices, Customers, and Bills.
"""

import os
import re
import logging
import pymongo
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger("query_engine")


class MongoDBClient:
    _client = None
    _db = None

    # Standard collection mappings for ERP
    COLLECTION_ALIASES = {
        "invoice": "invoices",
        "invoices": "invoices",
        "vehicle": "vehicles",
        "vehicles": "vehicles",
        "car": "vehicles",
        "cars": "vehicles",
        "fleet": "vehicles",
        "customer": "customers",
        "customers": "customers",
        "driver": "drivers",
        "drivers": "drivers",
        "agreement": "agreements",
        "agreements": "agreements",
        "payment": "payments",
        "payments": "payments",
        "paymentreceived": "paymentreceiveds",
        "paymentmade": "paymentmades",
        "bill": "bills",
        "bills": "bills",
        "expense": "expenses",
        "expenses": "expenses",
        "user": "users",
        "users": "users",
        "admin": "admins",
        "admins": "admins",
        "branch": "branches",
        "branches": "branches"
    }

    @classmethod
    def get_db(cls):
        """Returns connected pymongo Database instance for live olaCarsFresh DB."""
        if cls._db is not None:
            return cls._db

        mongo_uri = os.getenv(
            "MONGO_URI",
            getattr(settings, "MONGO_URI", "mongodb+srv://admin:123@cluster0.h9lmv8j.mongodb.net/olaCarsFresh?appName=Cluster0")
        )
        db_name = os.getenv("ERP_DB_NAME", getattr(settings, "ERP_DB_NAME", "olaCarsFresh"))

        try:
            cls._client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            cls._db = cls._client[db_name]
            # Quick ping test
            cls._db.command("ping")
            logger.info(f"Successfully connected to live MongoDB Database: {db_name}")
            return cls._db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB '{mongo_uri}': {e}")
            return None

    @classmethod
    def list_collections(cls) -> List[str]:
        """Lists all available collection names in the MongoDB database."""
        db = cls.get_db()
        if db is not None:
            try:
                colls = db.list_collection_names()
                if colls:
                    return sorted(colls)
            except Exception as e:
                logger.error(f"Error listing collections: {e}")
        return list(set(cls.COLLECTION_ALIASES.values()))

    @classmethod
    def resolve_collection_name(cls, query_target: str) -> str:
        """Resolves table or entity name to exact MongoDB collection name."""
        if not query_target:
            return "invoices"
        clean_target = query_target.strip().lower()
        if clean_target in cls.COLLECTION_ALIASES:
            return cls.COLLECTION_ALIASES[clean_target]
        
        # Check against live collection list
        live_colls = cls.list_collections()
        for c in live_colls:
            if c.lower() == clean_target:
                return c
        return clean_target

    @classmethod
    def serialize_mongo_doc(cls, doc: Any) -> Any:
        """Helper to recursively convert ObjectId and Date objects into JSON serializable format."""
        if isinstance(doc, dict):
            new_doc = {}
            for k, v in doc.items():
                if k in ["_id"] or type(v).__name__ == "ObjectId":
                    new_doc[k] = str(v)
                elif hasattr(v, "isoformat"):
                    new_doc[k] = v.isoformat()
                else:
                    new_doc[k] = cls.serialize_mongo_doc(v)
            return new_doc
        elif isinstance(doc, list):
            return [cls.serialize_mongo_doc(item) for item in doc]
        return doc

    @classmethod
    def populate_references(cls, db, collection_name: str, docs: List[dict]) -> List[dict]:
        """Enriches documents with driver, customer, and vehicle names for complete data visibility."""
        if not docs:
            return docs

        # Cache reference maps
        driver_ids = set()
        customer_ids = set()
        vehicle_ids = set()

        for d in docs:
            if isinstance(d.get("driver"), str) and len(d.get("driver")) == 24:
                driver_ids.add(d.get("driver"))
            if isinstance(d.get("customer"), str) and len(d.get("customer")) == 24:
                customer_ids.add(d.get("customer"))
            if isinstance(d.get("vehicle"), str) and len(d.get("vehicle")) == 24:
                vehicle_ids.add(d.get("vehicle"))
            if isinstance(d.get("currentDriver"), str) and len(d.get("currentDriver")) == 24:
                driver_ids.add(d.get("currentDriver"))

        driver_map = {}
        if driver_ids:
            try:
                from bson.objectid import ObjectId
                obj_ids = [ObjectId(i) for i in driver_ids if ObjectId.is_valid(i)]
                drivers = db["drivers"].find({"_id": {"$in": obj_ids}})
                for drv in drivers:
                    p_info = drv.get("personalInfo", {})
                    name = p_info.get("fullName") or drv.get("driverId") or "Driver"
                    phone = p_info.get("phone", "")
                    driver_map[str(drv["_id"])] = {
                        "driverName": name,
                        "driverPhone": phone,
                        "driverId": drv.get("driverId")
                    }
            except Exception as e:
                logger.error(f"Error fetching driver references: {e}")

        customer_map = {}
        if customer_ids:
            try:
                from bson.objectid import ObjectId
                obj_ids = [ObjectId(i) for i in customer_ids if ObjectId.is_valid(i)]
                custs = db["customers"].find({"_id": {"$in": obj_ids}})
                for c in custs:
                    p_info = c.get("personalInfo", {})
                    name = p_info.get("fullName") or c.get("name") or c.get("companyName") or "Customer"
                    customer_map[str(c["_id"])] = {
                        "customerName": name,
                        "customerPhone": p_info.get("phone") or c.get("phone", "")
                    }
            except Exception as e:
                logger.error(f"Error fetching customer references: {e}")

        vehicle_map = {}
        if vehicle_ids:
            try:
                from bson.objectid import ObjectId
                obj_ids = [ObjectId(i) for i in vehicle_ids if ObjectId.is_valid(i)]
                vehs = db["vehicles"].find({"_id": {"$in": obj_ids}})
                for v in vehs:
                    b_details = v.get("basicDetails", {})
                    l_docs = v.get("legalDocs", {})
                    reg_no = l_docs.get("registrationNumber") or "N/A"
                    model_name = f"{b_details.get('make', '')} {b_details.get('model', '')}".strip()
                    vehicle_map[str(v["_id"])] = {
                        "registrationNumber": reg_no,
                        "vehicleModel": model_name
                    }
            except Exception as e:
                logger.error(f"Error fetching vehicle references: {e}")

        # Inject populated details into docs
        for d in docs:
            drv_id = str(d.get("driver") or d.get("currentDriver") or "")
            if drv_id in driver_map:
                d["driverName"] = driver_map[drv_id]["driverName"]
                d["driverPhone"] = driver_map[drv_id]["driverPhone"]
                if driver_map[drv_id].get("driverId"):
                    d["driverIdCode"] = driver_map[drv_id]["driverId"]

            cust_id = str(d.get("customer") or "")
            if cust_id in customer_map:
                d["customerName"] = customer_map[cust_id]["customerName"]
                d["customerPhone"] = customer_map[cust_id]["customerPhone"]

            veh_id = str(d.get("vehicle") or "")
            if veh_id in vehicle_map:
                d["vehicleRegNumber"] = vehicle_map[veh_id]["registrationNumber"]
                d["vehicleModel"] = vehicle_map[veh_id]["vehicleModel"]

        return docs

    @classmethod
    def query_collection(cls, collection_name: str, filter_dict: dict = None, limit: int = 500) -> List[dict]:
        """Executes read-only query on specified MongoDB collection with reference joins."""
        db = cls.get_db()
        if db is None:
            return []

        coll_name = cls.resolve_collection_name(collection_name)
        try:
            coll = db[coll_name]
            filter_dict = filter_dict or {}
            cursor = coll.find(filter_dict).sort("_id", -1).limit(limit)
            raw_results = list(cursor)
            serialized = cls.serialize_mongo_doc(raw_results)
            enriched = cls.populate_references(db, coll_name, serialized)
            return enriched
        except Exception as e:
            logger.error(f"MongoDB query error on '{coll_name}': {e}")
            return []

    @classmethod
    def execute_smart_query(cls, sql_or_query: str, limit: int = 500) -> Dict[str, Any]:
        """
        Smart SQL & MongoDB Query Executor.
        Translates SQL SELECT statements or queries into live MongoDB execution results.
        """
        db = cls.get_db()
        if db is None:
            return {"status": "error", "error": "Database connection offline", "data": []}

        query_str = (sql_or_query or "").strip()
        
        # Determine target collection
        target_coll = "invoices"
        filter_dict = {}

        if re.search(r"\bFROM\s+([a-zA-Z0-9_]+)", query_str, re.IGNORECASE):
            match = re.search(r"\bFROM\s+([a-zA-Z0-9_]+)", query_str, re.IGNORECASE)
            target_coll = cls.resolve_collection_name(match.group(1))
        elif any(k in query_str.lower() for k in ["vehicle", "car", "fleet"]):
            target_coll = "vehicles"
        elif any(k in query_str.lower() for k in ["driver"]):
            target_coll = "drivers"
        elif any(k in query_str.lower() for k in ["customer"]):
            target_coll = "customers"
        elif any(k in query_str.lower() for k in ["bill"]):
            target_coll = "bills"

        # Check for status filters
        query_upper = query_str.upper()
        if "OVERDUE" in query_upper:
            if target_coll == "invoices":
                filter_dict["$or"] = [
                    {"status": "OVERDUE"},
                    {"status": "PENDING"},
                    {"status": "PARTIAL"}
                ]
            else:
                filter_dict["status"] = {"$regex": "OVERDUE|PENDING|PARTIAL", "$options": "i"}
        elif "AVAILABLE" in query_upper:
            filter_dict["status"] = {"$regex": "AVAILABLE", "$options": "i"}
        elif "RENTED" in query_upper:
            filter_dict["status"] = {"$regex": "RENTED", "$options": "i"}
        elif "PAID" in query_upper:
            filter_dict["status"] = "PAID"

        data = cls.query_collection(target_coll, filter_dict=filter_dict, limit=limit)
        
        # Build column list from data keys
        columns = []
        if data:
            for item in data[:5]:
                for k in item.keys():
                    if k not in columns and k not in ["passwordHash", "otp", "refreshToken"]:
                        columns.append(k)

        return {
            "status": "success",
            "collection": target_coll,
            "query": query_str,
            "columns": columns,
            "row_count": len(data),
            "data": data
        }
