"""
Vendor service for managing vendor data and validation
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VendorService:
    """Service for managing vendor data and validation"""

    def __init__(self):
        """Initialize the vendor service"""
        # In a real implementation, this would connect to a database
        # For now, we'll use in-memory storage with sample data
        self._vendors = self._load_sample_vendors()

    def get_vendor_by_id(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Get vendor by ID"""
        try:
            logger.info(f"Looking up vendor: {vendor_id}")
            return self._vendors.get(vendor_id.upper())
        except Exception as e:
            logger.error(f"Error getting vendor {vendor_id}: {e}")
            return None

    def get_vendor_by_name(self, vendor_name: str) -> Optional[Dict[str, Any]]:
        """Get vendor by name"""
        try:
            logger.info(f"Looking up vendor by name: {vendor_name}")
            vendor_lower = vendor_name.lower()

            for vendor in self._vendors.values():
                if vendor["name"].lower() == vendor_lower:
                    return vendor

            return None
        except Exception as e:
            logger.error(f"Error getting vendor by name {vendor_name}: {e}")
            return None

    def get_all_vendors(self) -> List[Dict[str, Any]]:
        """Get all vendors"""
        try:
            return list(self._vendors.values())
        except Exception as e:
            logger.error(f"Error getting all vendors: {e}")
            return []

    def get_active_vendors(self) -> List[Dict[str, Any]]:
        """Get all active vendors"""
        try:
            return [
                vendor
                for vendor in self._vendors.values()
                if vendor["status"] == "ACTIVE"
            ]
        except Exception as e:
            logger.error(f"Error getting active vendors: {e}")
            return []

    def is_vendor_authorized(self, vendor_name: str) -> bool:
        """Check if vendor is authorized"""
        try:
            vendor = self.get_vendor_by_name(vendor_name)
            if vendor:
                return vendor["status"] == "ACTIVE" and vendor["authorized"]
            return False
        except Exception as e:
            logger.error(f"Error checking vendor authorization: {e}")
            return False

    def get_vendor_contracts(self, vendor_id: str) -> List[Dict[str, Any]]:
        """Get contracts for a vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if vendor:
                return vendor.get("contracts", [])
            return []
        except Exception as e:
            logger.error(f"Error getting vendor contracts: {e}")
            return []

    def validate_vendor_invoice(
        self, vendor_name: str, invoice_amount: float
    ) -> Dict[str, Any]:
        """Validate vendor invoice against vendor rules"""
        try:
            logger.info(f"Validating invoice for vendor: {vendor_name}")

            vendor = self.get_vendor_by_name(vendor_name)
            if not vendor:
                return {
                    "valid": False,
                    "reason": "Vendor not found",
                    "severity": "HIGH",
                }

            # Check if vendor is active
            if vendor["status"] != "ACTIVE":
                return {
                    "valid": False,
                    "reason": f"Vendor status is {vendor['status']}",
                    "severity": "HIGH",
                }

            # Check if vendor is authorized
            if not vendor["authorized"]:
                return {
                    "valid": False,
                    "reason": "Vendor is not authorized",
                    "severity": "CRITICAL",
                }

            # Check invoice limit
            if "invoice_limit" in vendor and invoice_amount > vendor["invoice_limit"]:
                return {
                    "valid": False,
                    "reason": f"Invoice amount ${invoice_amount} exceeds vendor limit ${vendor['invoice_limit']}",
                    "severity": "HIGH",
                }

            # Check payment terms
            if "payment_terms" in vendor:
                return {
                    "valid": True,
                    "payment_terms": vendor["payment_terms"],
                    "severity": "LOW",
                }

            return {
                "valid": True,
                "reason": "Vendor validation passed",
                "severity": "LOW",
            }

        except Exception as e:
            logger.error(f"Error validating vendor invoice: {e}")
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "severity": "HIGH",
            }

    def create_vendor(self, vendor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new vendor"""
        try:
            logger.info(f"Creating new vendor: {vendor_data.get('name')}")

            # Validate required fields
            required_fields = ["vendor_id", "name", "status", "authorized"]
            for field in required_fields:
                if field not in vendor_data:
                    raise ValueError(f"Missing required field: {field}")

            # Add creation timestamp
            vendor_data["created_at"] = datetime.now()
            vendor_data["updated_at"] = datetime.now()

            # Add to storage
            self._vendors[vendor_data["vendor_id"].upper()] = vendor_data

            logger.info(f"Successfully created vendor: {vendor_data['vendor_id']}")
            return vendor_data

        except Exception as e:
            logger.error(f"Error creating vendor: {e}")
            return None

    def update_vendor(
        self, vendor_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing vendor"""
        try:
            logger.info(f"Updating vendor: {vendor_id}")

            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                logger.warning(f"Vendor not found: {vendor_id}")
                return None

            # Update fields
            for key, value in updates.items():
                if key in vendor:
                    vendor[key] = value

            # Update timestamp
            vendor["updated_at"] = datetime.now()

            logger.info(f"Successfully updated vendor: {vendor_id}")
            return vendor

        except Exception as e:
            logger.error(f"Error updating vendor {vendor_id}: {e}")
            return None

    def get_vendor_statistics(self) -> Dict[str, Any]:
        """Get statistics about vendors"""
        try:
            total_vendors = len(self._vendors)
            active_vendors = len(
                [v for v in self._vendors.values() if v["status"] == "ACTIVE"]
            )
            authorized_vendors = len(
                [v for v in self._vendors.values() if v["authorized"]]
            )

            # Count by status
            status_counts = {}
            for vendor in self._vendors.values():
                status = vendor["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            # Count by category
            category_counts = {}
            for vendor in self._vendors.values():
                category = vendor.get("category", "Unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

            return {
                "total_vendors": total_vendors,
                "active_vendors": active_vendors,
                "authorized_vendors": authorized_vendors,
                "status_counts": status_counts,
                "category_counts": category_counts,
            }

        except Exception as e:
            logger.error(f"Error getting vendor statistics: {e}")
            return {}

    def _load_sample_vendors(self) -> Dict[str, Dict[str, Any]]:
        """Load sample vendor data"""
        sample_vendors = {}

        # Sample vendor 1
        vendor1 = {
            "vendor_id": "VEND-001",
            "name": "ABC Supplies Inc.",
            "status": "ACTIVE",
            "authorized": True,
            "category": "Office Supplies",
            "payment_terms": "Net 30",
            "invoice_limit": 10000.00,
            "contracts": [
                {
                    "contract_id": "CONTRACT-2024-001",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "status": "ACTIVE",
                }
            ],
            "contact_info": {
                "email": "orders@abcsupplies.com",
                "phone": "555-123-4567",
                "address": "123 Main St, Anytown, USA",
            },
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1),
        }
        sample_vendors["VEND-001"] = vendor1

        # Sample vendor 2
        vendor2 = {
            "vendor_id": "VEND-002",
            "name": "Tech Solutions LLC",
            "status": "ACTIVE",
            "authorized": True,
            "category": "Technology",
            "payment_terms": "Net 30",
            "invoice_limit": 50000.00,
            "contracts": [
                {
                    "contract_id": "CONTRACT-2024-002",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "status": "ACTIVE",
                }
            ],
            "contact_info": {
                "email": "sales@techsolutions.com",
                "phone": "555-987-6543",
                "address": "456 Tech Ave, Tech City, USA",
            },
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1),
        }
        sample_vendors["VEND-002"] = vendor2

        # Sample vendor 3
        vendor3 = {
            "vendor_id": "VEND-003",
            "name": "Office Depot",
            "status": "ACTIVE",
            "authorized": True,
            "category": "Office Supplies",
            "payment_terms": "Net 15",
            "invoice_limit": 5000.00,
            "contracts": [],
            "contact_info": {
                "email": "corporate@officedepot.com",
                "phone": "555-555-5555",
                "address": "789 Office Blvd, Office City, USA",
            },
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1),
        }
        sample_vendors["VEND-003"] = vendor3

        # Sample vendor 4 (inactive)
        vendor4 = {
            "vendor_id": "VEND-004",
            "name": "Old Supplier Corp",
            "status": "INACTIVE",
            "authorized": False,
            "category": "General",
            "payment_terms": "Net 30",
            "invoice_limit": 1000.00,
            "contracts": [],
            "contact_info": {
                "email": "info@oldsupplier.com",
                "phone": "555-111-2222",
                "address": "999 Old St, Old Town, USA",
            },
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 12, 31),
        }
        sample_vendors["VEND-004"] = vendor4

        logger.info(f"Loaded {len(sample_vendors)} sample vendors")
        return sample_vendors
