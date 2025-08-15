"""
Purchase Order API endpoints
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.services.po_service import POService
from app.core.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

router = APIRouter()
po_service = POService()
document_processor = DocumentProcessor()

class CreatePORequest(BaseModel):
    """Request model for creating a PO manually"""
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

@router.post("/test-llm")
async def test_llm_response():
    """Test endpoint to debug LLM responses"""
    try:
        from app.core.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Test with a simple prompt
        test_text = """
        PO Number: TEST-PO-001
        Vendor: Test Vendor Inc.
        Date: 2024-01-15
        Total: 1000.00
        """
        
        # Test the extraction
        result = processor.extract_po_data(test_text)
        
        return {
            "success": True,
            "extracted_data": result,
            "message": "LLM test successful"
        }
        
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "LLM test failed"
        }

@router.post("/upload")
async def upload_purchase_order(file: UploadFile = File(...)):
    """Upload and process a purchase order PDF"""
    try:
        logger.info(f"Processing uploaded PO file: {file.filename}")
        
        # Save the uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # First extract text from the PDF
            logger.info(f"Extracting text from PDF: {temp_file_path}")
            extracted_text = document_processor.extract_text_from_pdf(temp_file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise HTTPException(status_code=400, detail="Could not extract meaningful text from PDF")
            
            logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            logger.debug(f"Extracted text preview: {extracted_text[:200]}...")
            
            # Process the extracted text to extract PO data
            po_data = document_processor.extract_po_data(extracted_text)
            
            # Save to PO service
            po = po_service.create_po_from_data(po_data)
            
            if po:
                logger.info(f"Successfully processed and saved PO: {po.po_number}")
                return {
                    "message": "Purchase Order uploaded successfully",
                    "po_number": po.po_number,
                    "vendor_name": po.vendor_name,
                    "total_authorized": float(po.total_authorized),
                    "line_items_count": len(po.line_items)
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to create PO from uploaded data")
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error processing PO upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PO: {str(e)}")

@router.get("/")
async def list_purchase_orders(
    vendor: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    """List purchase orders with optional filtering"""
    try:
        pos = po_service.get_all_pos()
        
        # Apply filters
        if vendor:
            pos = [po for po in pos if vendor.lower() in po.vendor_name.lower()]
        if status:
            pos = [po for po in pos if po.status.upper() == status.upper()]
        if min_amount is not None:
            pos = [po for po in pos if float(po.total_authorized) >= min_amount]
        if max_amount is not None:
            pos = [po for po in pos if float(po.total_authorized) <= max_amount]
        
        # Apply pagination
        total_count = len(pos)
        pos = pos[offset:offset + limit]
        
        return {
            "purchase_orders": [po.dict() for po in pos],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing POs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{po_number}")
async def get_purchase_order(po_number: str):
    """Get purchase order by number"""
    try:
        po = po_service.get_po_by_number(po_number)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        return po.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PO {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/")
async def create_purchase_order(request: CreatePORequest):
    """Create a new purchase order manually"""
    try:
        po_data = request.dict()
        po = po_service.create_po(po_data)
        
        if po:
            return po.dict()
        else:
            raise HTTPException(status_code=400, detail="Failed to create purchase order")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating PO: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{po_number}")
async def update_purchase_order(po_number: str, updates: dict):
    """Update an existing purchase order"""
    try:
        po = po_service.update_po(po_number, updates)
        
        if po:
            return po.dict()
        else:
            raise HTTPException(status_code=404, detail="Purchase order not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PO {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{po_number}")
async def delete_purchase_order(po_number: str):
    """Delete a purchase order"""
    try:
        success = po_service.delete_po(po_number)
        
        if success:
            return {"message": f"Purchase order {po_number} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Purchase order not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PO {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/vendor/{vendor_name}")
async def get_pos_by_vendor(vendor_name: str):
    """Get purchase orders by vendor name"""
    try:
        pos = po_service.get_pos_by_vendor(vendor_name)
        return {
            "vendor_name": vendor_name,
            "purchase_orders": [po.dict() for po in pos],
            "total_count": len(pos)
        }
        
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
