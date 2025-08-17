"""
Invoice processing API endpoints
"""

import logging
import os
import time
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.document_processor import DocumentProcessor
from app.core.po_matcher import POMatcher
from app.core.business_rules import BusinessRulesEngine
from app.core.recommendation_engine import RecommendationEngine
from app.services.po_service import POService
from app.services.vendor_service import VendorService
from app.services.invoice_service import InvoiceService
from app.models.invoice import Invoice
from app.models.recommendation import ProcessingRecommendation
from app.config import settings
from app.core.database import get_db_context
from app.models.database_models import InvoiceDB

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize services
po_service = POService()
vendor_service = VendorService()
invoice_service = InvoiceService()

# Initialize core components
document_processor = DocumentProcessor()
po_matcher = POMatcher(po_service)
business_rules_engine = BusinessRulesEngine()
recommendation_engine = RecommendationEngine()


@router.post("/process-invoice")
async def process_invoice(
    file: UploadFile = File(..., description="Invoice file to process"),
    auto_approve: bool = Query(False, description="Auto-approve if within thresholds"),
):
    """
    Process an uploaded invoice and generate processing recommendation

    This endpoint:
    1. Extracts data from the uploaded invoice file
    2. Finds matching purchase order
    3. Validates against business rules
    4. Generates AI-powered recommendation
    5. Returns processing results
    """
    try:
        start_time = time.time()
        logger.info(f"Processing invoice file: {file.filename}")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file.size} exceeds maximum allowed size {settings.max_file_size}",
            )

        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in [f".{ext}" for ext in settings.allowed_extensions]:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not allowed. Allowed types: {settings.allowed_extensions}",
            )

        # Save uploaded file
        file_path = os.path.join(
            settings.upload_dir, f"{int(time.time())}_{file.filename}"
        )
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"File saved to: {file_path}")

        # Process invoice
        invoice = document_processor.process_invoice_file(file_path)

        # Find matching PO
        matching_po = po_matcher.find_matching_po(invoice)

        # Validate against PO if found
        if matching_po:
            validation_result = po_matcher.validate_invoice_against_po(
                invoice, matching_po
            )
        else:
            # Create empty validation result for no PO found
            from app.models.recommendation import (
                ValidationResult,
                BusinessRuleViolation,
                ViolationType,
            )

            validation_result = ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                po_found=False,
                total_line_items=len(invoice.line_items),
                matched_line_items=0,
                violations=[
                    BusinessRuleViolation(
                        violation_type=ViolationType.PO_NOT_FOUND,
                        severity="HIGH",
                        description=f"No matching purchase order found for vendor {invoice.vendor_name}",
                        field_name="po_reference",
                    )
                ],
            )

        # Check business rules
        business_rule_violations = business_rules_engine.check_business_rules(invoice)

        # Generate recommendation
        recommendation = recommendation_engine.generate_recommendation(
            invoice, validation_result, business_rule_violations
        )

        # Save invoice and recommendation
        invoice_id = invoice_service.save_invoice(invoice, recommendation)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Prepare response
        response = {
            "invoice_id": invoice_id,
            "invoice_number": invoice.invoice_number,
            "vendor_name": invoice.vendor_name,
            "total_amount": float(invoice.total_amount),
            "recommendation": {
                "action": str(recommendation.action),
                "confidence_score": recommendation.confidence_score,
                "reasoning": recommendation.reasoning,
                "risk_level": recommendation.risk_level,
                "auto_approvable": recommendation.auto_approvable,
                "requires_manual_review": recommendation.requires_manual_review,
            },
            "validation": {
                "po_found": validation_result.po_found,
                "po_number": validation_result.po_number,
                "is_valid": validation_result.is_valid,
                "match_percentage": validation_result.get_match_percentage(),
                "violations_count": len(validation_result.violations),
            },
            "business_rules": {
                "violations_count": len(business_rule_violations),
                "risk_level": business_rules_engine.get_rule_summary(
                    business_rule_violations
                )["risk_level"],
            },
            "processing_time_ms": int(processing_time),
            "file_path": file_path,
        }

        logger.info(f"Invoice processing completed in {processing_time:.2f}ms")
        return response

    except Exception as e:
        logger.error(f"Error processing invoice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing invoice: {str(e)}"
        )


@router.get("/")
async def get_invoices(
    db: Session = Depends(get_db_context),
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """Get all invoices with pagination"""
    try:
        with get_db_context() as db_session:
            invoice_service = InvoiceService()
            # For now, return empty list since we don't have real invoice data yet
            # TODO: Implement real invoice retrieval from database
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving invoices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve invoices: {str(e)}")

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db_context)
):
    """Get a specific invoice by ID"""
    try:
        with get_db_context() as db_session:
            invoice_service = InvoiceService()
            invoice = invoice_service.get_invoice_by_id(db_session, invoice_id)
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Convert to frontend-friendly format
            formatted_invoice = {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "vendor_name": invoice.vendor_name,
                "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "status": invoice.status or "pending",
                "recommendation": invoice.recommendation or "pending",
                "confidence_score": invoice.confidence_score or 0,
                "po_matches": [],  # TODO: Implement PO matching logic
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None
            }
            
            return formatted_invoice
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve invoice: {str(e)}")

@router.post("/")
async def create_invoice(
    invoice_data: dict,
    db: Session = Depends(get_db_context)
):
    """Create a new invoice"""
    try:
        with get_db_context() as db_session:
            invoice_service = InvoiceService()
            # TODO: Implement invoice creation logic
            return {"message": "Invoice creation endpoint - implementation pending"}
            
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")

@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    invoice_data: dict,
    db: Session = Depends(get_db_context)
):
    """Update an existing invoice"""
    try:
        with get_db_context() as db_session:
            invoice_service = InvoiceService()
            # TODO: Implement invoice update logic
            return {"message": "Invoice update endpoint - implementation pending"}
            
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update invoice: {str(e)}")

@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db_context)
):
    """Delete an invoice"""
    try:
        with get_db_context() as db_session:
            invoice_service = InvoiceService()
            # TODO: Implement invoice deletion logic
            return {"message": "Invoice deletion endpoint - implementation pending"}
            
    except Exception as e:
        logger.error(f"Error deleting invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete invoice: {str(e)}")


@router.get("/{invoice_id}/recommendation")
async def get_recommendation(invoice_id: str):
    """Get processing recommendation for specific invoice"""
    try:
        recommendation = invoice_service.get_recommendation(invoice_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        return recommendation.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{invoice_id}/validation")
async def get_validation(invoice_id: str):
    """Get validation results for specific invoice"""
    try:
        invoice_data = invoice_service.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Extract validation result from recommendation
        recommendation = invoice_data.get("recommendation", {})
        validation_result = recommendation.get("validation_result", {})

        return validation_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: str,
    approved_by: str = Query(..., description="Name of person approving"),
    notes: Optional[str] = Query(None, description="Approval notes"),
):
    """Approve invoice for payment"""
    try:
        success = invoice_service.approve_invoice(invoice_id, approved_by, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {"message": "Invoice approved successfully", "invoice_id": invoice_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{invoice_id}/reject")
async def reject_invoice(
    invoice_id: str,
    rejected_by: str = Query(..., description="Name of person rejecting"),
    reason: str = Query(..., description="Reason for rejection"),
    notes: Optional[str] = Query(None, description="Rejection notes"),
):
    """Reject invoice"""
    try:
        success = invoice_service.reject_invoice(invoice_id, rejected_by, reason, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {"message": "Invoice rejected successfully", "invoice_id": invoice_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def list_invoices(
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    action: Optional[str] = Query(None, description="Filter by processing action"),
    limit: int = Query(50, description="Maximum number of invoices to return"),
    offset: int = Query(0, description="Number of invoices to skip"),
):
    """List processed invoices with optional filtering"""
    try:
        invoices = invoice_service.get_all_invoices()

        # Apply filters
        if vendor:
            invoices = [
                inv
                for inv in invoices
                if inv["invoice"]["vendor_name"].lower() == vendor.lower()
            ]

        if action:
            invoices = [
                inv for inv in invoices if inv["recommendation"]["action"] == action
            ]

        # Apply pagination
        total_count = len(invoices)
        invoices = invoices[offset : offset + limit]

        return {
            "invoices": invoices,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/{query}")
async def search_invoices(query: str):
    """Search invoices by various criteria"""
    try:
        results = invoice_service.search_invoices(query)
        return {"results": results, "query": query, "count": len(results)}

    except Exception as e:
        logger.error(f"Error searching invoices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/summary")
async def get_invoice_statistics():
    """Get invoice processing statistics"""
    try:
        stats = invoice_service.get_invoice_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting invoice statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/recent")
async def get_recent_history(
    limit: int = Query(10, description="Number of recent items to return")
):
    """Get recent processing history"""
    try:
        history = invoice_service.get_processing_history(limit)
        return {"history": history, "limit": limit}

    except Exception as e:
        logger.error(f"Error getting processing history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
