"""
Purchase Order service for managing PO data
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.purchase_order import PurchaseOrder, POLineItem
from app.config import settings

logger = logging.getLogger(__name__)


class POService:
    """Service for managing purchase order data"""

    def __init__(self):
        """Initialize the PO service"""
        # In a real implementation, this would connect to a database
        # For now, we'll use in-memory storage with sample data
        self._pos = self._load_sample_pos()

    def get_po_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number"""
        try:
            logger.info(f"Looking up PO: {po_number}")
            return self._pos.get(po_number.upper())
        except Exception as e:
            logger.error(f"Error getting PO {po_number}: {e}")
            return None

    def get_pos_by_vendor(self, vendor_name: str) -> List[PurchaseOrder]:
        """Get all POs for a specific vendor"""
        try:
            logger.info(f"Looking up POs for vendor: {vendor_name}")
            vendor_pos = []
            vendor_lower = vendor_name.lower()

            for po in self._pos.values():
                if po.vendor_name.lower() == vendor_lower:
                    vendor_pos.append(po)

            return vendor_pos
        except Exception as e:
            logger.error(f"Error getting POs for vendor {vendor_name}: {e}")
            return []

    def get_all_pos(self) -> List[PurchaseOrder]:
        """Get all purchase orders"""
        try:
            return list(self._pos.values())
        except Exception as e:
            logger.error(f"Error getting all POs: {e}")
            return []

    def get_pos_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[PurchaseOrder]:
        """Get POs within a date range"""
        try:
            logger.info(f"Looking up POs between {start_date} and {end_date}")
            pos_in_range = []

            for po in self._pos.values():
                if start_date <= po.po_date <= end_date:
                    pos_in_range.append(po)

            return pos_in_range
        except Exception as e:
            logger.error(f"Error getting POs by date range: {e}")
            return []

    def get_pos_by_status(self, status: str) -> List[PurchaseOrder]:
        """Get POs by status"""
        try:
            logger.info(f"Looking up POs with status: {status}")
            pos_with_status = []

            for po in self._pos.values():
                if po.status.upper() == status.upper():
                    pos_with_status.append(po)

            return pos_with_status
        except Exception as e:
            logger.error(f"Error getting POs by status {status}: {e}")
            return []

    def get_pos_by_amount_range(
        self, min_amount: Decimal, max_amount: Decimal
    ) -> List[PurchaseOrder]:
        """Get POs within an amount range"""
        try:
            logger.info(f"Looking up POs between ${min_amount} and ${max_amount}")
            pos_in_range = []

            for po in self._pos.values():
                if min_amount <= po.total_authorized <= max_amount:
                    pos_in_range.append(po)

            return pos_in_range
        except Exception as e:
            logger.error(f"Error getting POs by amount range: {e}")
            return []

    def create_po(self, po_data: Dict[str, Any]) -> Optional[PurchaseOrder]:
        """Create a new purchase order"""
        try:
            logger.info(f"Creating new PO: {po_data.get('po_number')}")

            # Validate required fields
            required_fields = [
                "po_number",
                "vendor_name",
                "po_date",
                "total_authorized",
                "line_items",
            ]
            for field in required_fields:
                if field not in po_data:
                    raise ValueError(f"Missing required field: {field}")

            # Create PO object
            po = PurchaseOrder(**po_data)

            # Add to storage
            self._pos[po.po_number.upper()] = po

            logger.info(f"Successfully created PO: {po.po_number}")
            return po

        except Exception as e:
            logger.error(f"Error creating PO: {e}")
            return None

    def update_po(
        self, po_number: str, updates: Dict[str, Any]
    ) -> Optional[PurchaseOrder]:
        """Update an existing purchase order"""
        try:
            logger.info(f"Updating PO: {po_number}")

            po = self.get_po_by_number(po_number)
            if not po:
                logger.warning(f"PO not found: {po_number}")
                return None

            # Update fields
            for key, value in updates.items():
                if hasattr(po, key):
                    setattr(po, key, value)

            # Update timestamp
            po.updated_at = datetime.now()

            logger.info(f"Successfully updated PO: {po_number}")
            return po

        except Exception as e:
            logger.error(f"Error updating PO {po_number}: {e}")
            return None

    def delete_po(self, po_number: str) -> bool:
        """Delete a purchase order"""
        try:
            logger.info(f"Deleting PO: {po_number}")

            if po_number.upper() in self._pos:
                del self._pos[po_number.upper()]
                logger.info(f"Successfully deleted PO: {po_number}")
                return True
            else:
                logger.warning(f"PO not found for deletion: {po_number}")
                return False

        except Exception as e:
            logger.error(f"Error deleting PO {po_number}: {e}")
            return False

    def get_po_statistics(self) -> Dict[str, Any]:
        """Get statistics about purchase orders"""
        try:
            total_pos = len(self._pos)
            total_amount = sum(po.total_authorized for po in self._pos.values())

            # Count by status
            status_counts = {}
            for po in self._pos.values():
                status = po.status
                status_counts[status] = status_counts.get(status, 0) + 1

            # Count by vendor
            vendor_counts = {}
            for po in self._pos.values():
                vendor = po.vendor_name
                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

            return {
                "total_pos": total_pos,
                "total_amount": float(total_amount),
                "status_counts": status_counts,
                "vendor_counts": vendor_counts,
                "average_amount": (
                    float(total_amount / total_pos) if total_pos > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting PO statistics: {e}")
            return {}

    def _load_sample_pos(self) -> Dict[str, PurchaseOrder]:
        """Load sample purchase order data"""
        sample_pos = {}

        # Sample PO 1
        po1 = PurchaseOrder(
            po_number="PO-2024-001",
            vendor_name="ABC Supplies Inc.",
            vendor_id="VEND-001",
            po_date=datetime(2024, 1, 15),
            total_authorized=Decimal("2500.00"),
            currency="USD",
            line_items=[
                POLineItem(
                    description="Office Chairs",
                    quantity=10,
                    unit_price=Decimal("150.00"),
                    total_price=Decimal("1500.00"),
                    sku="CHAIR-001",
                    part_number="OC-100",
                ),
                POLineItem(
                    description="Desk Lamps",
                    quantity=20,
                    unit_price=Decimal("50.00"),
                    total_price=Decimal("1000.00"),
                    sku="LAMP-001",
                    part_number="DL-200",
                ),
            ],
            contract_reference="CONTRACT-2024-001",
            payment_terms="Net 30",
            status="OPEN",
            approved_by="John Smith",
            approved_date=datetime(2024, 1, 16),
            created_at=datetime(2024, 1, 15),
            updated_at=datetime(2024, 1, 16),
        )
        sample_pos["PO-2024-001"] = po1

        # Sample PO 2
        po2 = PurchaseOrder(
            po_number="PO-2024-002",
            vendor_name="Tech Solutions LLC",
            vendor_id="VEND-002",
            po_date=datetime(2024, 1, 20),
            total_authorized=Decimal("5000.00"),
            currency="USD",
            line_items=[
                POLineItem(
                    description="Laptop Computers",
                    quantity=5,
                    unit_price=Decimal("800.00"),
                    total_price=Decimal("4000.00"),
                    sku="LAPTOP-001",
                    part_number="LT-500",
                ),
                POLineItem(
                    description="External Monitors",
                    quantity=5,
                    unit_price=Decimal("200.00"),
                    total_price=Decimal("1000.00"),
                    sku="MONITOR-001",
                    part_number="EM-300",
                ),
            ],
            payment_terms="Net 30",
            status="OPEN",
            approved_by="Jane Doe",
            approved_date=datetime(2024, 1, 21),
            created_at=datetime(2024, 1, 20),
            updated_at=datetime(2024, 1, 21),
        )
        sample_pos["PO-2024-002"] = po2

        # Sample PO 3
        po3 = PurchaseOrder(
            po_number="PO-2024-003",
            vendor_name="Office Depot",
            vendor_id="VEND-003",
            po_date=datetime(2024, 2, 1),
            total_authorized=Decimal("750.00"),
            currency="USD",
            line_items=[
                POLineItem(
                    description="Printer Paper",
                    quantity=50,
                    unit_price=Decimal("15.00"),
                    total_price=Decimal("750.00"),
                    sku="PAPER-001",
                    part_number="PP-100",
                )
            ],
            payment_terms="Net 15",
            status="OPEN",
            approved_by="Mike Johnson",
            approved_date=datetime(2024, 2, 2),
            created_at=datetime(2024, 2, 1),
            updated_at=datetime(2024, 2, 2),
        )
        sample_pos["PO-2024-003"] = po3

        logger.info(f"Loaded {len(sample_pos)} sample purchase orders")
        return sample_pos
