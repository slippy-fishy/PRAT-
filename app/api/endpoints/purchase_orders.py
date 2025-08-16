"""
Purchase Order API endpoints
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db_context
from app.services.po_folder_service import POFolderService, POFolderHandler
from app.models.database_models import PurchaseOrderDB, POLineItemDB

logger = logging.getLogger(__name__)

router = APIRouter()
po_folder_service = POFolderService()

class CreatePORequest(BaseModel):
    """Request model for creating a PO manually"""
    po_number: str
    vendor_name: str
    vendor_id: Optional[str] = None
    po_date: datetime
    total_amount: float
    currency: str = "USD"
    line_items: List[dict]
    contract_reference: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None

@router.get("/")
async def list_purchase_orders(
    vendor: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    """List all stored purchase orders"""
    try:
        with get_db_context() as db:
            # Build query
            query = db.query(PurchaseOrderDB)
            
            # Apply filters
            if vendor:
                query = query.filter(PurchaseOrderDB.vendor_name.ilike(f"%{vendor}%"))
            if status:
                query = query.filter(PurchaseOrderDB.status == status)
            if min_amount is not None:
                query = query.filter(PurchaseOrderDB.total_amount >= min_amount)
            if max_amount is not None:
                query = query.filter(PurchaseOrderDB.total_amount <= max_amount)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            pos = query.offset(offset).limit(limit).all()
            
            # Convert to dict format
            po_list = []
            for po in pos:
                po_dict = {
                    "id": str(po.id),
                    "po_number": po.po_number,
                    "vendor_name": po.vendor_name,
                    "vendor_id": po.vendor_id,
                    "total_amount": float(po.total_amount),
                    "currency": po.currency,
                    "po_date": po.po_date.isoformat() if po.po_date else None,
                    "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                    "status": po.status,
                    "file_path": po.file_path,
                    "created_at": po.created_at.isoformat() if po.created_at else None,
                    "updated_at": po.updated_at.isoformat() if po.updated_at else None
                }
                po_list.append(po_dict)
            
            return {
                "purchase_orders": po_list,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"Error listing POs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{po_number}")
async def get_purchase_order_details(po_number: str):
    """Get detailed PO information for matching"""
    try:
        with get_db_context() as db:
            po = db.query(PurchaseOrderDB).filter_by(po_number=po_number).first()
            
            if not po:
                raise HTTPException(status_code=404, detail="Purchase order not found")
            
            # Get line items
            line_items = db.query(POLineItemDB).filter_by(po_id=po.id).all()
            
            # Build detailed response
            po_details = {
                "id": str(po.id),
                "po_number": po.po_number,
                "vendor_name": po.vendor_name,
                "vendor_id": po.vendor_id,
                "total_amount": float(po.total_amount),
                "currency": po.currency,
                "po_date": po.po_date.isoformat() if po.po_date else None,
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                "status": po.status,
                "file_path": po.file_path,
                "file_hash": po.file_hash,
                "created_at": po.created_at.isoformat() if po.created_at else None,
                "updated_at": po.updated_at.isoformat() if po.updated_at else None,
                "line_items": [
                    {
                        "id": str(item.id),
                        "line_number": item.line_number,
                        "description": item.description,
                        "quantity": float(item.quantity),
                        "unit_price": float(item.unit_price),
                        "total_amount": float(item.total_amount),
                        "product_code": item.product_code,
                        "category": item.category
                    }
                    for item in line_items
                ]
            }
            
            return po_details
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PO details for {po_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/scan-folder")
async def scan_po_folder():
    """Manually trigger PO folder scan"""
    try:
        from app.config import settings
        
        with get_db_context() as db:
            result = po_folder_service.scan_folder(db, settings.po_folder_path)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "PO folder scan completed",
            "scan_results": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning PO folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan folder")

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
            from app.core.document_processor import DocumentProcessor
            document_processor = DocumentProcessor()
            
            extracted_text = document_processor.extract_text_from_pdf(temp_file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise HTTPException(status_code=400, detail="Could not extract meaningful text from PDF")
            
            logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            
            # Process the extracted text to extract PO data
            po_data = document_processor.extract_po_data(extracted_text)
            
            # Store to database using folder service
            with get_db_context() as db:
                handler = POFolderHandler(db)
                handler._store_po_data(po_data, temp_file_path, handler._get_file_hash(temp_file_path))
            
            return {
                "message": "Purchase Order uploaded and processed successfully",
                "po_number": po_data.get('po_number'),
                "vendor_name": po_data.get('vendor_name'),
                "total_amount": po_data.get('total_authorized', 0)
            }
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error processing PO upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PO: {str(e)}")

@router.get("/vendor/{vendor_name}")
async def get_pos_by_vendor(vendor_name: str):
    """Get purchase orders by vendor name"""
    try:
        with get_db_context() as db:
            pos = db.query(PurchaseOrderDB).filter(
                PurchaseOrderDB.vendor_name.ilike(f"%{vendor_name}%")
            ).all()
            
            po_list = []
            for po in pos:
                po_dict = {
                    "id": str(po.id),
                    "po_number": po.po_number,
                    "vendor_name": po.vendor_name,
                    "total_amount": float(po.total_amount),
                    "status": po.status,
                    "po_date": po.po_date.isoformat() if po.po_date else None
                }
                po_list.append(po_dict)
            
            return {
                "vendor_name": vendor_name,
                "purchase_orders": po_list,
                "total_count": len(po_list)
            }
            
    except Exception as e:
        logger.error(f"Error getting POs for vendor {vendor_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics/summary")
async def get_po_statistics():
    """Get purchase order statistics"""
    try:
        with get_db_context() as db:
            total_pos = db.query(PurchaseOrderDB).count()
            total_amount = db.query(PurchaseOrderDB.total_amount).scalar() or 0
            
            # Count by status
            status_counts = {}
            status_results = db.query(PurchaseOrderDB.status, db.func.count(PurchaseOrderDB.id))\
                .group_by(PurchaseOrderDB.status).all()
            
            for status, count in status_results:
                status_counts[status] = count
            
            # Count by vendor
            vendor_counts = {}
            vendor_results = db.query(PurchaseOrderDB.vendor_name, db.func.count(PurchaseOrderDB.id))\
                .group_by(PurchaseOrderDB.vendor_name).all()
            
            for vendor, count in vendor_results:
                vendor_counts[vendor] = count
            
            # Average PO amount
            avg_amount = total_amount / total_pos if total_pos > 0 else 0
            
            stats = {
                "total_pos": total_pos,
                "total_amount": float(total_amount),
                "average_amount": float(avg_amount),
                "status_distribution": status_counts,
                "vendor_distribution": vendor_counts,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error generating PO statistics: {e}")
        return {
            "total_pos": 0,
            "total_amount": 0.0,
            "average_amount": 0.0,
            "status_distribution": {},
            "vendor_distribution": {},
            "last_updated": datetime.utcnow().isoformat(),
            "error": str(e)
        }
