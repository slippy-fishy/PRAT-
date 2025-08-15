"""
Invoice service for managing processed invoices and recommendations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.models.invoice import Invoice
from app.models.recommendation import ProcessingRecommendation

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for managing processed invoices and recommendations"""

    def __init__(self):
        """Initialize the invoice service"""
        # In a real implementation, this would connect to a database
        # For now, we'll use in-memory storage
        self._invoices = {}
        self._recommendations = {}
        self._processing_history = []

    def save_invoice(
        self, invoice: Invoice, recommendation: ProcessingRecommendation
    ) -> str:
        """Save processed invoice and recommendation"""
        try:
            logger.info(f"Saving invoice: {invoice.invoice_number}")

            # Generate unique ID
            invoice_id = (
                f"INV-{datetime.now().strftime('%Y%m%d')}-{len(self._invoices) + 1:04d}"
            )

            # Store invoice data
            invoice_data = {
                "invoice_id": invoice_id,
                "invoice": invoice.dict(),
                "recommendation": recommendation.dict(),
                "processed_at": datetime.now(),
                "status": "PROCESSED",
            }

            self._invoices[invoice_id] = invoice_data
            self._recommendations[invoice_id] = recommendation

            # Add to processing history
            self._processing_history.append(
                {
                    "invoice_id": invoice_id,
                    "invoice_number": invoice.invoice_number,
                    "vendor_name": invoice.vendor_name,
                    "amount": float(invoice.total_amount),
                    "action": str(recommendation.action),
                    "processed_at": datetime.now(),
                }
            )

            logger.info(f"Successfully saved invoice: {invoice_id}")
            return invoice_id

        except Exception as e:
            logger.error(f"Error saving invoice: {e}")
            raise

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        try:
            logger.info(f"Looking up invoice: {invoice_id}")
            return self._invoices.get(invoice_id)
        except Exception as e:
            logger.error(f"Error getting invoice {invoice_id}: {e}")
            return None

    def get_recommendation(self, invoice_id: str) -> Optional[ProcessingRecommendation]:
        """Get recommendation by invoice ID"""
        try:
            logger.info(f"Looking up recommendation: {invoice_id}")
            return self._recommendations.get(invoice_id)
        except Exception as e:
            logger.error(f"Error getting recommendation {invoice_id}: {e}")
            return None

    def get_invoice_by_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Get invoice by invoice number"""
        try:
            logger.info(f"Looking up invoice by number: {invoice_number}")

            for invoice_data in self._invoices.values():
                if invoice_data["invoice"]["invoice_number"] == invoice_number:
                    return invoice_data

            return None
        except Exception as e:
            logger.error(f"Error getting invoice by number {invoice_number}: {e}")
            return None

    def get_invoices_by_vendor(self, vendor_name: str) -> List[Dict[str, Any]]:
        """Get all invoices for a specific vendor"""
        try:
            logger.info(f"Looking up invoices for vendor: {vendor_name}")

            vendor_invoices = []
            vendor_lower = vendor_name.lower()

            for invoice_data in self._invoices.values():
                if invoice_data["invoice"]["vendor_name"].lower() == vendor_lower:
                    vendor_invoices.append(invoice_data)

            return vendor_invoices
        except Exception as e:
            logger.error(f"Error getting invoices for vendor {vendor_name}: {e}")
            return []

    def get_invoices_by_action(self, action: str) -> List[Dict[str, Any]]:
        """Get invoices by processing action"""
        try:
            logger.info(f"Looking up invoices with action: {action}")

            action_invoices = []

            for invoice_data in self._invoices.values():
                if invoice_data["recommendation"]["action"] == action:
                    action_invoices.append(invoice_data)

            return action_invoices
        except Exception as e:
            logger.error(f"Error getting invoices by action {action}: {e}")
            return []

    def get_invoices_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get invoices within a date range"""
        try:
            logger.info(f"Looking up invoices between {start_date} and {end_date}")

            date_invoices = []

            for invoice_data in self._invoices.values():
                invoice_date = datetime.fromisoformat(
                    invoice_data["invoice"]["invoice_date"]
                )
                if start_date <= invoice_date <= end_date:
                    date_invoices.append(invoice_data)

            return date_invoices
        except Exception as e:
            logger.error(f"Error getting invoices by date range: {e}")
            return []

    def get_all_invoices(self) -> List[Dict[str, Any]]:
        """Get all processed invoices"""
        try:
            return list(self._invoices.values())
        except Exception as e:
            logger.error(f"Error getting all invoices: {e}")
            return []

    def update_invoice_status(
        self, invoice_id: str, status: str, notes: Optional[str] = None
    ) -> bool:
        """Update invoice status"""
        try:
            logger.info(f"Updating invoice status: {invoice_id} -> {status}")

            invoice_data = self.get_invoice(invoice_id)
            if not invoice_data:
                logger.warning(f"Invoice not found: {invoice_id}")
                return False

            # Update status
            invoice_data["status"] = status
            invoice_data["updated_at"] = datetime.now()

            if notes:
                invoice_data["notes"] = notes

            logger.info(f"Successfully updated invoice status: {invoice_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating invoice status {invoice_id}: {e}")
            return False

    def approve_invoice(
        self, invoice_id: str, approved_by: str, notes: Optional[str] = None
    ) -> bool:
        """Approve an invoice"""
        try:
            logger.info(f"Approving invoice: {invoice_id}")

            invoice_data = self.get_invoice(invoice_id)
            if not invoice_data:
                logger.warning(f"Invoice not found: {invoice_id}")
                return False

            # Update status and add approval info
            invoice_data["status"] = "APPROVED"
            invoice_data["approved_by"] = approved_by
            invoice_data["approved_at"] = datetime.now()
            invoice_data["updated_at"] = datetime.now()

            if notes:
                invoice_data["approval_notes"] = notes

            logger.info(f"Successfully approved invoice: {invoice_id}")
            return True

        except Exception as e:
            logger.error(f"Error approving invoice {invoice_id}: {e}")
            return False

    def reject_invoice(
        self,
        invoice_id: str,
        rejected_by: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Reject an invoice"""
        try:
            logger.info(f"Rejecting invoice: {invoice_id}")

            invoice_data = self.get_invoice(invoice_id)
            if not invoice_data:
                logger.warning(f"Invoice not found: {invoice_id}")
                return False

            # Update status and add rejection info
            invoice_data["status"] = "REJECTED"
            invoice_data["rejected_by"] = rejected_by
            invoice_data["rejected_at"] = datetime.now()
            invoice_data["rejection_reason"] = reason
            invoice_data["updated_at"] = datetime.now()

            if notes:
                invoice_data["rejection_notes"] = notes

            logger.info(f"Successfully rejected invoice: {invoice_id}")
            return True

        except Exception as e:
            logger.error(f"Error rejecting invoice {invoice_id}: {e}")
            return False

    def get_processing_history(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get processing history"""
        try:
            history = sorted(
                self._processing_history, key=lambda x: x["processed_at"], reverse=True
            )

            if limit:
                history = history[:limit]

            return history
        except Exception as e:
            logger.error(f"Error getting processing history: {e}")
            return []

    def get_invoice_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed invoices"""
        try:
            total_invoices = len(self._invoices)
            total_amount = sum(
                float(inv["invoice"]["total_amount"]) for inv in self._invoices.values()
            )

            # Count by action
            action_counts = {}
            for invoice_data in self._invoices.values():
                action = invoice_data["recommendation"]["action"]
                action_counts[action] = action_counts.get(action, 0) + 1

            # Count by status
            status_counts = {}
            for invoice_data in self._invoices.values():
                status = invoice_data.get("status", "PROCESSED")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Count by vendor
            vendor_counts = {}
            for invoice_data in self._invoices.values():
                vendor = invoice_data["invoice"]["vendor_name"]
                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

            # Calculate average confidence
            confidence_scores = [
                inv["recommendation"]["confidence_score"]
                for inv in self._invoices.values()
            ]
            avg_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores
                else 0
            )

            return {
                "total_invoices": total_invoices,
                "total_amount": total_amount,
                "average_amount": (
                    total_amount / total_invoices if total_invoices > 0 else 0
                ),
                "action_counts": action_counts,
                "status_counts": status_counts,
                "vendor_counts": vendor_counts,
                "average_confidence": avg_confidence,
            }

        except Exception as e:
            logger.error(f"Error getting invoice statistics: {e}")
            return {}

    def export_invoice_data(self, invoice_id: str) -> Optional[str]:
        """Export invoice data as JSON"""
        try:
            logger.info(f"Exporting invoice data: {invoice_id}")

            invoice_data = self.get_invoice(invoice_id)
            if not invoice_data:
                logger.warning(f"Invoice not found: {invoice_id}")
                return None

            # Convert to JSON
            json_data = json.dumps(invoice_data, default=str, indent=2)

            logger.info(f"Successfully exported invoice data: {invoice_id}")
            return json_data

        except Exception as e:
            logger.error(f"Error exporting invoice data {invoice_id}: {e}")
            return None

    def search_invoices(self, query: str) -> List[Dict[str, Any]]:
        """Search invoices by various criteria"""
        try:
            logger.info(f"Searching invoices: {query}")

            results = []
            query_lower = query.lower()

            for invoice_data in self._invoices.values():
                # Search in invoice number
                if query_lower in invoice_data["invoice"]["invoice_number"].lower():
                    results.append(invoice_data)
                    continue

                # Search in vendor name
                if query_lower in invoice_data["invoice"]["vendor_name"].lower():
                    results.append(invoice_data)
                    continue

                # Search in line item descriptions
                for line_item in invoice_data["invoice"]["line_items"]:
                    if query_lower in line_item["description"].lower():
                        results.append(invoice_data)
                        break

            return results

        except Exception as e:
            logger.error(f"Error searching invoices: {e}")
            return []
