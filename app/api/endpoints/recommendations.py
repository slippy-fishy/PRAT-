"""
Recommendations API endpoints
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize service
invoice_service = InvoiceService()


@router.get("/")
async def list_recommendations(
    action: Optional[str] = Query(None, description="Filter by recommendation action"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, description="Maximum number of recommendations to return"),
    offset: int = Query(0, description="Number of recommendations to skip"),
):
    """List processing recommendations with optional filtering"""
    try:
        invoices = invoice_service.get_all_invoices()

        # Extract recommendations
        recommendations = []
        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation:
                recommendation["invoice_id"] = invoice_data["invoice_id"]
                recommendation["invoice_number"] = invoice_data["invoice"][
                    "invoice_number"
                ]
                recommendation["vendor_name"] = invoice_data["invoice"]["vendor_name"]
                recommendation["total_amount"] = invoice_data["invoice"]["total_amount"]
                recommendations.append(recommendation)

        # Apply filters
        if action:
            recommendations = [r for r in recommendations if r.get("action") == action]

        if risk_level:
            recommendations = [
                r for r in recommendations if r.get("risk_level") == risk_level
            ]

        # Apply pagination
        total_count = len(recommendations)
        recommendations = recommendations[offset : offset + limit]

        return {
            "recommendations": recommendations,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{invoice_id}")
async def get_recommendation(invoice_id: str):
    """Get recommendation by invoice ID"""
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


@router.get("/action/{action}")
async def get_recommendations_by_action(action: str):
    """Get all recommendations for a specific action"""
    try:
        invoices = invoice_service.get_invoices_by_action(action)

        recommendations = []
        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation:
                recommendation["invoice_id"] = invoice_data["invoice_id"]
                recommendation["invoice_number"] = invoice_data["invoice"][
                    "invoice_number"
                ]
                recommendation["vendor_name"] = invoice_data["invoice"]["vendor_name"]
                recommendation["total_amount"] = invoice_data["invoice"]["total_amount"]
                recommendations.append(recommendation)

        return {
            "recommendations": recommendations,
            "action": action,
            "count": len(recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting recommendations by action {action}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/risk-level/{risk_level}")
async def get_recommendations_by_risk_level(risk_level: str):
    """Get all recommendations for a specific risk level"""
    try:
        invoices = invoice_service.get_all_invoices()

        recommendations = []
        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation and recommendation.get("risk_level") == risk_level:
                recommendation["invoice_id"] = invoice_data["invoice_id"]
                recommendation["invoice_number"] = invoice_data["invoice"][
                    "invoice_number"
                ]
                recommendation["vendor_name"] = invoice_data["invoice"]["vendor_name"]
                recommendation["total_amount"] = invoice_data["invoice"]["total_amount"]
                recommendations.append(recommendation)

        return {
            "recommendations": recommendations,
            "risk_level": risk_level,
            "count": len(recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting recommendations by risk level {risk_level}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/summary")
async def get_recommendation_statistics():
    """Get recommendation statistics"""
    try:
        invoices = invoice_service.get_all_invoices()

        # Count by action
        action_counts = {}
        risk_level_counts = {}
        confidence_scores = []

        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation:
                action = recommendation.get("action", "UNKNOWN")
                action_counts[action] = action_counts.get(action, 0) + 1

                risk_level = recommendation.get("risk_level", "UNKNOWN")
                risk_level_counts[risk_level] = risk_level_counts.get(risk_level, 0) + 1

                confidence = recommendation.get("confidence_score", 0)
                confidence_scores.append(confidence)

        # Calculate average confidence
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )

        return {
            "total_recommendations": len(
                [inv for inv in invoices if inv.get("recommendation")]
            ),
            "action_counts": action_counts,
            "risk_level_counts": risk_level_counts,
            "average_confidence": avg_confidence,
        }

    except Exception as e:
        logger.error(f"Error getting recommendation statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/high-risk/list")
async def get_high_risk_recommendations():
    """Get all high-risk recommendations that require attention"""
    try:
        invoices = invoice_service.get_all_invoices()

        high_risk_recommendations = []
        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation and recommendation.get("risk_level") in [
                "HIGH",
                "CRITICAL",
            ]:
                recommendation["invoice_id"] = invoice_data["invoice_id"]
                recommendation["invoice_number"] = invoice_data["invoice"][
                    "invoice_number"
                ]
                recommendation["vendor_name"] = invoice_data["invoice"]["vendor_name"]
                recommendation["total_amount"] = invoice_data["invoice"]["total_amount"]
                high_risk_recommendations.append(recommendation)

        return {
            "high_risk_recommendations": high_risk_recommendations,
            "count": len(high_risk_recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting high-risk recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/auto-approvable/list")
async def get_auto_approvable_recommendations():
    """Get all recommendations that can be auto-approved"""
    try:
        invoices = invoice_service.get_all_invoices()

        auto_approvable_recommendations = []
        for invoice_data in invoices:
            recommendation = invoice_data.get("recommendation", {})
            if recommendation and recommendation.get("auto_approvable", False):
                recommendation["invoice_id"] = invoice_data["invoice_id"]
                recommendation["invoice_number"] = invoice_data["invoice"][
                    "invoice_number"
                ]
                recommendation["vendor_name"] = invoice_data["invoice"]["vendor_name"]
                recommendation["total_amount"] = invoice_data["invoice"]["total_amount"]
                auto_approvable_recommendations.append(recommendation)

        return {
            "auto_approvable_recommendations": auto_approvable_recommendations,
            "count": len(auto_approvable_recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting auto-approvable recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
