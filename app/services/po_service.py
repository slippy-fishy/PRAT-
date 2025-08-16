"""
Purchase Order service for managing PO data
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.purchase_order import PurchaseOrder, POLineItem
from app.models.database_models import PurchaseOrderDB, POLineItemDB
from app.core.database import get_db_context
from app.config import settings

logger = logging.getLogger(__name__)


class POService:
    """Service for managing purchase order data"""

    def __init__(self):
        """Initialize the PO service"""
        logger.info("PO Service initialized with database storage")

    def get_po_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number"""
        try:
            with get_db_context() as db:
                po_db = db.query(PurchaseOrderDB).filter_by(po_number=po_number).first()
                
                if po_db:
                    logger.info(f"Found PO: {po_number}")
                    # Convert database model to Pydantic model
                    return PurchaseOrder(
                        po_number=po_db.po_number,
                        vendor_name=po_db.vendor_name,
                        vendor_id=po_db.vendor_id,
                        total_authorized=float(po_db.total_amount) if po_db.total_amount else 0.0,
                        currency=po_db.currency,
                        po_date=po_db.po_date,
                        delivery_date=po_db.delivery_date,
                        status=po_db.status,
                        line_items=[]
                    )
                else:
                    logger.info(f"PO not found: {po_number}")
                    return None

        except Exception as e:
            logger.error(f"Error getting PO {po_number}: {e}")
            return None

    def get_pos_by_vendor(self, vendor_name: str) -> List[PurchaseOrder]:
        """Get all purchase orders for a specific vendor"""
        try:
            logger.info(f"Looking up POs for vendor: {vendor_name}")
            
            with get_db_context() as db:
                vendor_pos_db = db.query(PurchaseOrderDB).filter(
                    PurchaseOrderDB.vendor_name.ilike(f"%{vendor_name}%")
                ).all()
                
                pos_list = []
                for po_db in vendor_pos_db:
                    po = PurchaseOrder(
                        po_number=po_db.po_number,
                        vendor_name=po_db.vendor_name,
                        vendor_id=po_db.vendor_id,
                        total_authorized=float(po_db.total_amount) if po_db.total_amount else 0.0,
                        currency=po_db.currency,
                        po_date=po_db.po_date,
                        delivery_date=po_db.delivery_date,
                        status=po_db.status,
                        line_items=[]
                    )
                    pos_list.append(po)

                logger.info(f"Found {len(pos_list)} POs for vendor {vendor_name}")
                return pos_list

        except Exception as e:
            logger.error(f"Error getting POs for vendor {vendor_name}: {e}")
            return []

    def get_all_pos(self) -> List[PurchaseOrder]:
        """Get all purchase orders"""
        try:
            with get_db_context() as db:
                pos_db_list = db.query(PurchaseOrderDB).all()
                
                pos_list = []
                for po_db in pos_db_list:
                    po = PurchaseOrder(
                        po_number=po_db.po_number,
                        vendor_name=po_db.vendor_name,
                        vendor_id=po_db.vendor_id,
                        total_authorized=float(po_db.total_amount) if po_db.total_amount else 0.0,
                        currency=po_db.currency,
                        po_date=po_db.po_date,
                        delivery_date=po_db.delivery_date,
                        status=po_db.status,
                        line_items=[]
                    )
                    pos_list.append(po)

                logger.info(f"Retrieved {len(pos_list)} purchase orders")
                return pos_list

        except Exception as e:
            logger.error(f"Error getting all POs: {e}")
            return []

    def get_pos_by_status(self, status: str) -> List[PurchaseOrder]:
        """Get purchase orders by status"""
        try:
            logger.info(f"Looking up POs with status: {status}")
            
            with get_db_context() as db:
                status_pos_db = db.query(PurchaseOrderDB).filter_by(status=status).all()
                
                pos_list = []
                for po_db in status_pos_db:
                    po = PurchaseOrder(
                        po_number=po_db.po_number,
                        vendor_name=po_db.vendor_name,
                        vendor_id=po_db.vendor_id,
                        total_authorized=float(po_db.total_amount) if po_db.total_amount else 0.0,
                        currency=po_db.currency,
                        po_date=po_db.po_date,
                        delivery_date=po_db.delivery_date,
                        status=po_db.status,
                        line_items=[]
                    )
                    pos_list.append(po)

                return pos_list

        except Exception as e:
            logger.error(f"Error getting POs by status {status}: {e}")
            return []

    def get_pos_by_amount_range(
        self, min_amount: float, max_amount: float
    ) -> List[PurchaseOrder]:
        """Get purchase orders within an amount range"""
        try:
            logger.info(f"Looking up POs between ${min_amount} and ${max_amount}")
            
            with get_db_context() as db:
                pos_in_range_db = db.query(PurchaseOrderDB).filter(
                    PurchaseOrderDB.total_amount.between(min_amount, max_amount)
                ).all()
                
                pos_list = []
                for po_db in pos_in_range_db:
                    po = PurchaseOrder(
                        po_number=po_db.po_number,
                        vendor_name=po_db.vendor_name,
                        vendor_id=po_db.vendor_id,
                        total_authorized=float(po_db.total_amount) if po_db.total_amount else 0.0,
                        currency=po_db.currency,
                        po_date=po_db.po_date,
                        delivery_date=po_db.delivery_date,
                        status=po_db.status,
                        line_items=[]
                    )
                    pos_list.append(po)

                return pos_list

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

    def create_po_from_data(self, po_data: Dict[str, Any]) -> Optional[PurchaseOrder]:
        """Create a PO from extracted data (e.g., from PDF upload)"""
        try:
            logger.info(f"Creating PO from extracted data: {po_data.get('po_number')}")

            # Set default values for missing fields
            if 'status' not in po_data:
                po_data['status'] = 'OPEN'
            if 'created_at' not in po_data:
                po_data['created_at'] = datetime.now()
            if 'updated_at' not in po_data:
                po_data['updated_at'] = datetime.now()

            # Create the PO
            po = self.create_po(po_data)

            if po:
                logger.info(f"Successfully created PO from data: {po.po_number}")
                return po
            else:
                logger.error("Failed to create PO from extracted data")
                return None

        except Exception as e:
            logger.error(f"Error creating PO from data: {e}")
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

            # Average PO amount
            avg_amount = total_amount / total_pos if total_pos > 0 else 0

            stats = {
                "total_pos": total_pos,
                "total_amount": float(total_amount),
                "average_amount": float(avg_amount),
                "status_distribution": status_counts,
                "vendor_distribution": vendor_counts,
                "last_updated": datetime.now().isoformat()
            }

            logger.info(f"Generated PO statistics: {total_pos} POs, ${total_amount} total")
            return stats

        except Exception as e:
            logger.error(f"Error generating PO statistics: {e}")
            return {
                "total_pos": 0,
                "total_amount": 0.0,
                "average_amount": 0.0,
                "status_distribution": {},
                "vendor_distribution": {},
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }

    def clear_all_pos(self) -> bool:
        """Clear all purchase orders (useful for testing)"""
        try:
            count = len(self._pos)
            self._pos.clear()
            logger.info(f"Cleared {count} purchase orders")
            return True
        except Exception as e:
            logger.error(f"Error clearing POs: {e}")
            return False

    def get_po_count(self) -> int:
        """Get the total number of purchase orders"""
        return len(self._pos)

    def is_empty(self) -> bool:
        """Check if there are no purchase orders"""
        return len(self._pos) == 0
