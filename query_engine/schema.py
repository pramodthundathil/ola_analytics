"""
Schema Discovery Module for Ola Cars ERP.
Inspects database collections/tables, fields, indexes, and relationships.
Provides schema metadata to LLMs and Query Engine.
"""

import os
import json
from typing import Dict, Any, List


class SchemaDiscovery:
    """
    Discovers database schema structures from ERP data sources.
    Supports MongoDB collections (OlaCarsBackend standard) and SQL databases.
    """

    # Pre-cached metadata for core Ola Cars ERP Collections (discovered from OlaCarsBackend)
    KNOWN_COLLECTIONS = {
        "customers": {
            "name": "Customer",
            "description": "Stores client, driver, and company profiles with billing/shipping addresses",
            "fields": {
                "customerId": "String (Unique Customer ID)",
                "name": "String (Customer full name)",
                "email": "String (Customer email)",
                "phone": "String (Contact phone number)",
                "companyName": "String (Organization/Company name)",
                "openingBalance": "Number (Opening account balance)",
                "creditLimit": "Number (Credit threshold)",
                "status": "String (ACTIVE / INACTIVE)",
                "branch": "ObjectId (Ref: Branch)"
            }
        },
        "invoices": {
            "name": "Invoice",
            "description": "Billing records for rental, workshop, manual, and deposit invoices",
            "fields": {
                "invoiceNumber": "String (Unique invoice number)",
                "invoiceType": "String (RENTAL / WORKSHOP / MANUAL / DEPOSIT)",
                "customer": "ObjectId (Ref: Customer)",
                "driver": "ObjectId (Ref: Driver)",
                "vehicle": "ObjectId (Ref: Vehicle)",
                "totalAmountDue": "Number (Total amount payable)",
                "amountPaid": "Number (Amount received)",
                "balance": "Number (Outstanding balance)",
                "status": "String (DRAFT / PENDING / PARTIAL / PAID / OVERDUE / CANCELLED)",
                "dueDate": "Date (Payment due date)",
                "generatedAt": "Date (Creation timestamp)"
            }
        },
        "vehicles": {
            "name": "Vehicle",
            "description": "Vehicle fleet inventory, registration, status, and rental rates",
            "fields": {
                "registrationNumber": "String (License plate / Reg No)",
                "make": "String (Manufacturer e.g. Maruti, Hyundai)",
                "model": "String (Vehicle model name)",
                "year": "Number (Manufacturing year)",
                "status": "String (AVAILABLE / RENTED / MAINTENANCE / SCRAPPED)",
                "branch": "ObjectId (Ref: Branch)",
                "dailyRate": "Number (Daily rental fee)",
                "weeklyRate": "Number (Weekly rental fee)"
            }
        },
        "agreements": {
            "name": "Agreement",
            "description": "Rental contracts binding customers and vehicles for specific durations",
            "fields": {
                "agreementNumber": "String (Contract identifier)",
                "customer": "ObjectId (Ref: Customer)",
                "vehicle": "ObjectId (Ref: Vehicle)",
                "startDate": "Date (Rental start date)",
                "endDate": "Date (Rental end date)",
                "status": "String (ACTIVE / COMPLETED / TERMINATED / CANCELLED)",
                "rate": "Number (Agreed rental rate)"
            }
        },
        "payments": {
            "name": "Payment",
            "description": "Transactions of received payments and collections",
            "fields": {
                "paymentNumber": "String (Payment reference ID)",
                "customer": "ObjectId (Ref: Customer)",
                "invoice": "ObjectId (Ref: Invoice)",
                "amount": "Number (Payment amount)",
                "paymentMethod": "String (Cash, Bank Transfer, Card, Mobile Money)",
                "paymentDate": "Date (Timestamp of transaction)",
                "status": "String (COMPLETED / PENDING / FAILED / REFUNDED)"
            }
        }
    }

    @classmethod
    def get_full_schema(cls) -> Dict[str, Any]:
        """Returns full schema definition for AI query generation."""
        return {
            "database_name": "olaCarsFresh",
            "engine": "MongoDB",
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
