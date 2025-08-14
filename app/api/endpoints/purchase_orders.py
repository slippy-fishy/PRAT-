"""
Purchase Order API endpoints
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.po_service import POService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize service
po_service = POService()


class CreatePORequest(BaseModel):
    """Request model for creating a purchase order"""

    po_number: str
    vendor_name: str
    vendor_id: Optional[str] = None
    po_date: datetime
    total_authorized: float
    currency: str = "USD"
    line_items: List[dict]
    contract_reference: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_purchase_orders(
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    status: Optional[str] = Query(None, description="Filter by PO status"),
    limit: int = Query(50, description="Maximum number of POs to return"),
    offset: int = Query(0, description="Number of POs to skip"),
):
    """List purchase orders with optional filtering"""
    try:
        pos = po_service.get_all_pos()

        # Apply filters
        if vendor:
            pos = [po for po in pos if po.vendor_name.lower() == vendor.lower()]

        if status:
            pos = [po for po in pos if po.status.upper() == status.upper()]

        # Apply pagination
        total_count = len(pos)
        pos = pos[offset : offset + limit]

        return {
            "purchase_orders": [po.dict() for po in pos],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing purchase orders: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{po_number}")
async def get_purchase_order(po_number: str):
    """Get purchase order by PO number"""
    try:
        po = po_service.get_po_by_number(po_number)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return po.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase order {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_purchase_order(request: CreatePORequest):
    """Create a new purchase order"""
    try:
        po_data = request.dict()
        po = po_service.create_po(po_data)

        if not po:
            raise HTTPException(
                status_code=400, detail="Failed to create purchase order"
            )

        return {"message": "Purchase order created successfully", "po": po.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating purchase order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{po_number}")
async def update_purchase_order(po_number: str, updates: dict):
    """Update an existing purchase order"""
    try:
        po = po_service.update_po(po_number, updates)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return {"message": "Purchase order updated successfully", "po": po.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating purchase order {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{po_number}")
async def delete_purchase_order(po_number: str):
    """Delete a purchase order"""
    try:
        success = po_service.delete_po(po_number)
        if not success:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return {"message": "Purchase order deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting purchase order {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vendor/{vendor_name}")
async def get_pos_by_vendor(vendor_name: str):
    """Get all purchase orders for a specific vendor"""
    try:
        pos = po_service.get_pos_by_vendor(vendor_name)
        return {"purchase_orders": [po.dict() for po in pos], "vendor": vendor_name}

    except Exception as e:
        logger.error(f"Error getting POs for vendor {vendor_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/summary")
async def get_po_statistics():
    """Get purchase order statistics"""
    try:
        stats = po_service.get_po_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting PO statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
