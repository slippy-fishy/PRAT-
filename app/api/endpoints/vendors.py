"""
Vendor API endpoints
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.vendor_service import VendorService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize service
vendor_service = VendorService()


class CreateVendorRequest(BaseModel):
    """Request model for creating a vendor"""

    vendor_id: str
    name: str
    status: str = "ACTIVE"
    authorized: bool = True
    category: Optional[str] = None
    payment_terms: Optional[str] = None
    invoice_limit: Optional[float] = None
    contact_info: Optional[dict] = None


@router.get("/")
async def list_vendors(
    status: Optional[str] = Query(None, description="Filter by vendor status"),
    category: Optional[str] = Query(None, description="Filter by vendor category"),
    limit: int = Query(50, description="Maximum number of vendors to return"),
    offset: int = Query(0, description="Number of vendors to skip"),
):
    """List vendors with optional filtering"""
    try:
        vendors = vendor_service.get_all_vendors()

        # Apply filters
        if status:
            vendors = [v for v in vendors if v["status"].upper() == status.upper()]

        if category:
            vendors = [
                v for v in vendors if v.get("category", "").lower() == category.lower()
            ]

        # Apply pagination
        total_count = len(vendors)
        vendors = vendors[offset : offset + limit]

        return {
            "vendors": vendors,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing vendors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{vendor_id}")
async def get_vendor(vendor_id: str):
    """Get vendor by ID"""
    try:
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        return vendor

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor {vendor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/name/{vendor_name}")
async def get_vendor_by_name(vendor_name: str):
    """Get vendor by name"""
    try:
        vendor = vendor_service.get_vendor_by_name(vendor_name)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        return vendor

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor by name {vendor_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_vendor(request: CreateVendorRequest):
    """Create a new vendor"""
    try:
        vendor_data = request.dict()
        vendor = vendor_service.create_vendor(vendor_data)

        if not vendor:
            raise HTTPException(status_code=400, detail="Failed to create vendor")

        return {"message": "Vendor created successfully", "vendor": vendor}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vendor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{vendor_id}")
async def update_vendor(vendor_id: str, updates: dict):
    """Update an existing vendor"""
    try:
        vendor = vendor_service.update_vendor(vendor_id, updates)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        return {"message": "Vendor updated successfully", "vendor": vendor}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor {vendor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/active/list")
async def list_active_vendors():
    """Get all active vendors"""
    try:
        vendors = vendor_service.get_active_vendors()
        return {"vendors": vendors, "count": len(vendors)}

    except Exception as e:
        logger.error(f"Error getting active vendors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{vendor_id}/contracts")
async def get_vendor_contracts(vendor_id: str):
    """Get contracts for a vendor"""
    try:
        contracts = vendor_service.get_vendor_contracts(vendor_id)
        return {"contracts": contracts, "vendor_id": vendor_id}

    except Exception as e:
        logger.error(f"Error getting vendor contracts {vendor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{vendor_name}/validate-invoice")
async def validate_vendor_invoice(vendor_name: str, invoice_amount: float):
    """Validate vendor invoice against vendor rules"""
    try:
        validation_result = vendor_service.validate_vendor_invoice(
            vendor_name, invoice_amount
        )
        return validation_result

    except Exception as e:
        logger.error(f"Error validating vendor invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/summary")
async def get_vendor_statistics():
    """Get vendor statistics"""
    try:
        stats = vendor_service.get_vendor_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting vendor statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
