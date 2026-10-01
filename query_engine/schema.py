"""
Schema Discovery Module for Ola Cars ERP.
Inspects database collections/tables, fields, indexes, and relationships.
Provides schema metadata to LLMs and Query Engine. All financial metrics are in USD ($).
"""

import os
import json
from typing import Dict, Any, List


class SchemaDiscovery:
    """
    Discovers database schema structures from live ERP data sources.
    Supports MongoDB collections (OlaCarsBackend standard).
    """

    KNOWN_COLLECTIONS = {
        "drivers": {
            "name": "Driver",
            "description": "Registered drivers, personal profiles, licensing, and contact info",
            "fields": {
                "driverId": "String (Unique Driver ID e.g. OLA-000001)",
                "status": "String (ACTIVE / SUSPENDED / DRAFT / REJECTED)",
                "personalInfo.fullName": "String (Driver Full Name)",
                "personalInfo.email": "String (Email Address)",
                "personalInfo.phone": "String (Phone Number)",
                "personalInfo.whatsappNumber": "String (WhatsApp Number)",
                "drivingLicense.licenseNumber": "String (License No)",
                "drivingLicense.expiryDate": "Date (License Expiry)"
            }
        },
        "invoices": {
            "name": "Invoice",
            "description": "Billing records for rental, workshop, manual, and deposit invoices (amounts in USD $)",
            "fields": {
                "invoiceNumber": "String (Unique invoice number e.g. INV-000001)",
                "invoiceType": "String (RENTAL / WORKSHOP / MANUAL / DEPOSIT)",
                "customer": "ObjectId (Ref: Customer)",
                "driver": "ObjectId (Ref: Driver)",
                "vehicle": "ObjectId (Ref: Vehicle)",
                "driverName": "String (Populated Driver Name)",
                "customerName": "String (Populated Customer Name)",
                "totalAmountDue": "Number (Total amount payable in USD $)",
                "amountPaid": "Number (Amount received in USD $)",
                "balance": "Number (Outstanding balance in USD $)",
                "status": "String (PAID / OVERDUE / PENDING / PARTIAL)",
                "dueDate": "Date (Payment due date)"
            }
        },
        "vehicles": {
            "name": "Vehicle",
            "description": "Vehicle fleet inventory, registration, status, and weekly rates (amounts in USD $)",
            "fields": {
                "legalDocs.registrationNumber": "String (License plate / Reg No)",
                "basicDetails.make": "String (Manufacturer e.g. KIA, Hyundai)",
                "basicDetails.model": "String (Vehicle model name)",
                "basicDetails.year": "Number (Manufacturing year)",
                "basicDetails.weeklyRent": "Number (Weekly rent in USD $)",
                "status": "String (ACTIVE — AVAILABLE / ACTIVE — RENTED / MAINTENANCE)",
                "currentDriver": "ObjectId (Ref: Driver)"
            }
        },
        "customers": {
            "name": "Customer",
            "description": "Stores client and driver profiles with billing addresses",
            "fields": {
                "name": "String (Customer full name)",
                "email": "String (Customer email)",
                "phone": "String (Contact phone number)",
                "companyName": "String (Organization/Company name)"
            }
        },
        "bills": {
            "name": "Bill",
            "description": "Vendor bills and supplier records (amounts in USD $)",
            "fields": {
                "billNumber": "String (Unique bill number)",
                "vendor": "String (Supplier name)",
                "totalAmount": "Number (Total amount in USD $)",
                "status": "String (OPEN / PAID / PARTIALLY_PAID)"
            }
        },
        "expenses": {
            "name": "Expense",
            "description": "Operational and maintenance expenses (amounts in USD $)",
            "fields": {
                "expenseCategory": "String (Expense category)",
                "amount": "Number (Expense amount in USD $)",
                "paymentMethod": "String (Payment method)"
            }
        }
    }

    @classmethod
    def get_full_schema(cls) -> Dict[str, Any]:
        """Returns full schema definition for AI query generation."""
        return {
            "database_name": "olaCarsFresh",
            "engine": "MongoDB",
            "currency": "USD ($)",
            "collections": cls.KNOWN_COLLECTIONS
        }

    @classmethod
    def get_collection_summary(cls, collection_name: str) -> Dict[str, Any]:
        """Returns schema summary for a specific collection."""
        return cls.KNOWN_COLLECTIONS.get(collection_name.lower(), {
            "name": collection_name,
            "description": f"ERP collection {collection_name}",
            "fields": {}
        })
