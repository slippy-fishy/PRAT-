"""
Purchase Order matching and validation module
"""

import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
import time

from app.models.invoice import Invoice, InvoiceLineItem
from app.models.purchase_order import PurchaseOrder, POLineItem
from app.models.recommendation import (
    ValidationResult,
    BusinessRuleViolation,
    ViolationType,
)
from app.services.po_service import POService

logger = logging.getLogger(__name__)


class POMatcher:
    """Handles purchase order matching and validation"""

    def __init__(self, po_service: POService):
        """Initialize the PO matcher"""
        self.po_service = po_service

    def find_matching_po(self, invoice: Invoice) -> Optional[PurchaseOrder]:
        """Find corresponding purchase order for invoice"""
        try:
            logger.info(f"Finding matching PO for invoice {invoice.invoice_number}")
            start_time = time.time()

            # Try multiple matching strategies
            matching_po = None

            # Strategy 1: Direct PO reference
            if invoice.po_reference:
                matching_po = self.po_service.get_po_by_number(invoice.po_reference)
                if matching_po:
                    logger.info(f"Found PO by direct reference: {invoice.po_reference}")
                    return matching_po

            # Strategy 2: Vendor + amount matching
            if not matching_po:
                matching_po = self._find_po_by_vendor_and_amount(invoice)

            # Strategy 3: Line item matching
            if not matching_po:
                matching_po = self._find_po_by_line_items(invoice)

            # Strategy 4: Fuzzy vendor name matching
            if not matching_po:
                matching_po = self._find_po_by_fuzzy_vendor(invoice)

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"PO matching completed in {processing_time:.2f}ms")

            return matching_po

        except Exception as e:
            logger.error(f"Error finding matching PO: {e}")
            return None

    def _find_po_by_vendor_and_amount(
        self, invoice: Invoice
    ) -> Optional[PurchaseOrder]:
        """Find PO by vendor name and total amount"""
        try:
            # Get POs for this vendor
            vendor_pos = self.po_service.get_pos_by_vendor(invoice.vendor_name)

            if not vendor_pos:
                return None

            # Find PO with matching amount (within tolerance)
            tolerance = Decimal("0.01")  # 1 cent tolerance
            for po in vendor_pos:
                if abs(po.total_authorized - invoice.total_amount) <= tolerance:
                    logger.info(f"Found PO by vendor and amount match: {po.po_number}")
                    return po

            return None

        except Exception as e:
            logger.error(f"Error in vendor/amount matching: {e}")
            return None

    def _find_po_by_line_items(self, invoice: Invoice) -> Optional[PurchaseOrder]:
        """Find PO by matching line items"""
        try:
            # Get POs for this vendor
            vendor_pos = self.po_service.get_pos_by_vendor(invoice.vendor_name)

            if not vendor_pos:
                return None

            best_match = None
            best_score = 0

            for po in vendor_pos:
                score = self._calculate_line_item_match_score(invoice, po)
                if score > best_score and score > 0.5:  # Minimum 50% match
                    best_score = score
                    best_match = po

            if best_match:
                logger.info(
                    f"Found PO by line item matching: {best_match.po_number} (score: {best_score:.2f})"
                )

            return best_match

        except Exception as e:
            logger.error(f"Error in line item matching: {e}")
            return None

    def _find_po_by_fuzzy_vendor(self, invoice: Invoice) -> Optional[PurchaseOrder]:
        """Find PO using fuzzy vendor name matching"""
        try:
            # Get all POs and try fuzzy matching on vendor names
            all_pos = self.po_service.get_all_pos()

            best_match = None
            best_score = 0

            for po in all_pos:
                score = self._calculate_vendor_similarity(
                    invoice.vendor_name, po.vendor_name
                )
                if score > best_score and score > 0.8:  # Minimum 80% similarity
                    best_score = score
                    best_match = po

            if best_match:
                logger.info(
                    f"Found PO by fuzzy vendor matching: {best_match.po_number} (score: {best_score:.2f})"
                )

            return best_match

        except Exception as e:
            logger.error(f"Error in fuzzy vendor matching: {e}")
            return None

    def _calculate_line_item_match_score(
        self, invoice: Invoice, po: PurchaseOrder
    ) -> float:
        """Calculate how well invoice line items match PO line items"""
        if not invoice.line_items or not po.line_items:
            return 0.0

        total_matches = 0
        total_items = len(invoice.line_items)

        for invoice_item in invoice.line_items:
            best_item_score = 0

            for po_item in po.line_items:
                # Check description similarity
                desc_similarity = self._calculate_text_similarity(
                    invoice_item.description.lower(), po_item.description.lower()
                )

                # Check quantity match
                qty_match = 1.0 if invoice_item.quantity == po_item.quantity else 0.0

                # Check price match (within 5% tolerance)
                price_tolerance = po_item.unit_price * Decimal("0.05")
                price_match = (
                    1.0
                    if abs(invoice_item.unit_price - po_item.unit_price)
                    <= price_tolerance
                    else 0.0
                )

                # Calculate overall item score
                item_score = desc_similarity * 0.6 + qty_match * 0.2 + price_match * 0.2
                best_item_score = max(best_item_score, item_score)

            total_matches += best_item_score

        return total_matches / total_items if total_items > 0 else 0.0

    def _calculate_vendor_similarity(self, vendor1: str, vendor2: str) -> float:
        """Calculate similarity between vendor names"""
        # Simple implementation - could be enhanced with more sophisticated algorithms
        v1_words = set(vendor1.lower().split())
        v2_words = set(vendor2.lower().split())

        if not v1_words or not v2_words:
            return 0.0

        intersection = v1_words.intersection(v2_words)
        union = v1_words.union(v2_words)

        return len(intersection) / len(union)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def validate_invoice_against_po(
        self, invoice: Invoice, po: PurchaseOrder
    ) -> ValidationResult:
        """Compare invoice details against PO terms"""
        try:
            logger.info(
                f"Validating invoice {invoice.invoice_number} against PO {po.po_number}"
            )
            start_time = time.time()

            violations = []
            line_item_matches = []

            # Validate vendor
            if invoice.vendor_name.lower() != po.vendor_name.lower():
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.VENDOR_NOT_AUTHORIZED,
                        severity="HIGH",
                        description=f"Invoice vendor '{invoice.vendor_name}' doesn't match PO vendor '{po.vendor_name}'",
                        field_name="vendor_name",
                        expected_value=po.vendor_name,
                        actual_value=invoice.vendor_name,
                    )
                )

            # Validate line items
            matched_line_items = 0
            for invoice_item in invoice.line_items:
                po_item = po.get_line_item_by_description(invoice_item.description)
                if not po_item and invoice_item.sku:
                    po_item = po.get_line_item_by_sku(invoice_item.sku)

                match_result = {
                    "invoice_description": invoice_item.description,
                    "matched": po_item is not None,
                    "po_description": po_item.description if po_item else None,
                    "quantity_match": False,
                    "price_match": False,
                    "violations": [],
                }

                if po_item:
                    matched_line_items += 1

                    # Check quantity
                    if invoice_item.quantity != po_item.quantity:
                        match_result["quantity_match"] = False
                        violations.append(
                            BusinessRuleViolation(
                                violation_type=ViolationType.QUANTITY_MISMATCH,
                                severity="MEDIUM",
                                description=f"Quantity mismatch for '{invoice_item.description}': expected {po_item.quantity}, got {invoice_item.quantity}",
                                field_name="quantity",
                                expected_value=po_item.quantity,
                                actual_value=invoice_item.quantity,
                            )
                        )
                        match_result["violations"].append("quantity_mismatch")
                    else:
                        match_result["quantity_match"] = True

                    # Check unit price (within 5% tolerance)
                    price_tolerance = po_item.unit_price * Decimal("0.05")
                    if (
                        abs(invoice_item.unit_price - po_item.unit_price)
                        > price_tolerance
                    ):
                        match_result["price_match"] = False
                        violations.append(
                            BusinessRuleViolation(
                                violation_type=ViolationType.PRICE_MISMATCH,
                                severity="MEDIUM",
                                description=f"Price mismatch for '{invoice_item.description}': expected {po_item.unit_price}, got {invoice_item.unit_price}",
                                field_name="unit_price",
                                expected_value=float(po_item.unit_price),
                                actual_value=float(invoice_item.unit_price),
                            )
                        )
                        match_result["violations"].append("price_mismatch")
                    else:
                        match_result["price_match"] = True
                else:
                    violations.append(
                        BusinessRuleViolation(
                            violation_type=ViolationType.QUANTITY_MISMATCH,
                            severity="HIGH",
                            description=f"Line item '{invoice_item.description}' not found in PO",
                            field_name="description",
                            actual_value=invoice_item.description,
                        )
                    )
                    match_result["violations"].append("item_not_found")

                line_item_matches.append(match_result)

            # Calculate amount differences
            amount_difference = invoice.total_amount - po.total_authorized
            amount_difference_percentage = (
                (amount_difference / po.total_authorized * 100)
                if po.total_authorized > 0
                else 0
            )

            overage_amount = max(amount_difference, Decimal("0"))
            overage_percentage = (
                (overage_amount / po.total_authorized * 100)
                if po.total_authorized > 0
                else 0
            )

            # Check for overage violations
            if overage_amount > 0:
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.OVERAGE_EXCEEDS_LIMIT,
                        severity="MEDIUM",
                        description=f"Invoice amount {invoice.total_amount} exceeds PO authorization {po.total_authorized} by {overage_amount}",
                        field_name="total_amount",
                        expected_value=float(po.total_authorized),
                        actual_value=float(invoice.total_amount),
                    )
                )

            # Count violations by severity
            critical_violations = len(
                [v for v in violations if v.severity == "CRITICAL"]
            )
            high_violations = len([v for v in violations if v.severity == "HIGH"])

            # Calculate confidence score
            confidence_score = self._calculate_validation_confidence(
                matched_line_items, len(invoice.line_items), violations
            )

            processing_time = (time.time() - start_time) * 1000

            validation_result = ValidationResult(
                is_valid=len(violations) == 0,
                confidence_score=confidence_score,
                po_found=True,
                po_number=po.po_number,
                po_match_confidence=0.95,  # High confidence since we found a match
                line_item_matches=line_item_matches,
                total_line_items=len(invoice.line_items),
                matched_line_items=matched_line_items,
                amount_difference=amount_difference,
                amount_difference_percentage=float(amount_difference_percentage),
                overage_amount=overage_amount,
                overage_percentage=float(overage_percentage),
                violations=violations,
                critical_violations=critical_violations,
                high_violations=high_violations,
                processing_time_ms=int(processing_time),
            )

            logger.info(f"Validation completed in {processing_time:.2f}ms")
            return validation_result

        except Exception as e:
            logger.error(f"Error validating invoice against PO: {e}")
            raise

    def _calculate_validation_confidence(
        self,
        matched_items: int,
        total_items: int,
        violations: List[BusinessRuleViolation],
    ) -> float:
        """Calculate confidence score for validation"""
        if total_items == 0:
            return 0.0

        # Base confidence on line item match percentage
        item_confidence = matched_items / total_items

        # Reduce confidence based on violations
        violation_penalty = min(len(violations) * 0.1, 0.5)  # Max 50% penalty

        # Weight critical violations more heavily
        critical_penalty = (
            len([v for v in violations if v.severity == "CRITICAL"]) * 0.2
        )

        confidence = item_confidence - violation_penalty - critical_penalty
        return max(confidence, 0.0)  # Ensure non-negative
