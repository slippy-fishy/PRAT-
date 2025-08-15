"""
Business rules engine for invoice processing
"""

import logging
from typing import List, Dict, Any
from decimal import Decimal
import time

from app.models.invoice import Invoice
from app.models.recommendation import BusinessRuleViolation, ViolationType
from app.config import settings

logger = logging.getLogger(__name__)


class BusinessRulesEngine:
    """Applies business rules and compliance checks to invoices"""

    def __init__(self):
        """Initialize the business rules engine"""
        self.auto_approve_threshold = Decimal(str(settings.auto_approve_threshold))
        self.require_manual_review_threshold = Decimal(
            str(settings.require_manual_review_threshold)
        )
        self.max_overage_percentage = settings.max_overage_percentage
        self.max_tax_rate = settings.max_tax_rate

    def check_business_rules(self, invoice: Invoice) -> List[BusinessRuleViolation]:
        """Apply business rules and compliance checks"""
        try:
            logger.info(f"Checking business rules for invoice {invoice.invoice_number}")
            start_time = time.time()

            violations = []

            # Check approval thresholds
            violations.extend(self._check_approval_thresholds(invoice))

            # Check for duplicate invoices
            violations.extend(self._check_duplicate_invoice(invoice))

            # Validate tax calculations
            violations.extend(self._validate_tax_calculations(invoice))

            # Validate vendor authorization
            violations.extend(self._validate_vendor_authorization(invoice))

            # Check contract terms
            violations.extend(self._check_contract_terms(invoice))

            # Validate payment terms
            violations.extend(self._validate_payment_terms(invoice))

            # Check for suspicious patterns
            violations.extend(self._check_suspicious_patterns(invoice))

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Business rules check completed in {processing_time:.2f}ms")

            return violations

        except Exception as e:
            logger.error(f"Error checking business rules: {e}")
            raise

    def _check_approval_thresholds(
        self, invoice: Invoice
    ) -> List[BusinessRuleViolation]:
        """Check if invoice exceeds approval thresholds"""
        violations = []

        # Check auto-approve threshold
        if invoice.total_amount > self.auto_approve_threshold:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.AMOUNT_EXCEEDS_THRESHOLD,
                    severity="MEDIUM",
                    description=f"Invoice amount {invoice.total_amount} exceeds auto-approve threshold {self.auto_approve_threshold}",
                    field_name="total_amount",
                    expected_value=float(self.auto_approve_threshold),
                    actual_value=float(invoice.total_amount),
                    rule_id="AUTO_APPROVE_THRESHOLD",
                )
            )

        # Check manual review threshold
        if invoice.total_amount > self.require_manual_review_threshold:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.AMOUNT_EXCEEDS_THRESHOLD,
                    severity="HIGH",
                    description=f"Invoice amount {invoice.total_amount} exceeds manual review threshold {self.require_manual_review_threshold}",
                    field_name="total_amount",
                    expected_value=float(self.require_manual_review_threshold),
                    actual_value=float(invoice.total_amount),
                    rule_id="MANUAL_REVIEW_THRESHOLD",
                )
            )

        return violations

    def _check_duplicate_invoice(self, invoice: Invoice) -> List[BusinessRuleViolation]:
        """Check for duplicate invoices"""
        violations = []

        # This would typically check against a database of processed invoices
        # For now, we'll implement a basic check based on invoice number and vendor
        # In a real implementation, this would query the database

        # Placeholder implementation
        is_duplicate = self._check_duplicate_in_database(invoice)

        if is_duplicate:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.DUPLICATE_INVOICE,
                    severity="CRITICAL",
                    description=f"Duplicate invoice detected: {invoice.invoice_number} from {invoice.vendor_name}",
                    field_name="invoice_number",
                    actual_value=invoice.invoice_number,
                    rule_id="DUPLICATE_CHECK",
                )
            )

        return violations

    def _validate_tax_calculations(
        self, invoice: Invoice
    ) -> List[BusinessRuleViolation]:
        """Validate tax calculations"""
        violations = []

        # Check if tax rate is reasonable
        if invoice.subtotal_amount > 0:
            calculated_tax_rate = invoice.tax_amount / invoice.subtotal_amount
            if calculated_tax_rate > self.max_tax_rate:
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.INVALID_TAX_CALCULATION,
                        severity="HIGH",
                        description=f"Tax rate {calculated_tax_rate:.2%} exceeds maximum allowed rate {self.max_tax_rate:.2%}",
                        field_name="tax_amount",
                        expected_value=f"max {self.max_tax_rate:.2%}",
                        actual_value=f"{calculated_tax_rate:.2%}",
                        rule_id="TAX_RATE_CHECK",
                    )
                )

        # Check if tax calculation is mathematically correct
        expected_tax = invoice.subtotal_amount * Decimal("0.1")  # Assume 10% tax rate
        tax_tolerance = Decimal("0.01")  # 1 cent tolerance

        if abs(invoice.tax_amount - expected_tax) > tax_tolerance:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.INVALID_TAX_CALCULATION,
                    severity="MEDIUM",
                    description=f"Tax amount {invoice.tax_amount} doesn't match expected calculation {expected_tax}",
                    field_name="tax_amount",
                    expected_value=float(expected_tax),
                    actual_value=float(invoice.tax_amount),
                    rule_id="TAX_CALCULATION_CHECK",
                )
            )

        return violations

    def _validate_vendor_authorization(
        self, invoice: Invoice
    ) -> List[BusinessRuleViolation]:
        """Validate vendor authorization"""
        violations = []

        # This would typically check against a vendor database
        # For now, we'll implement basic checks

        # Check if vendor name is suspicious
        suspicious_keywords = ["test", "demo", "sample", "invalid"]
        vendor_lower = invoice.vendor_name.lower()

        for keyword in suspicious_keywords:
            if keyword in vendor_lower:
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.VENDOR_NOT_AUTHORIZED,
                        severity="HIGH",
                        description=f"Vendor name contains suspicious keyword: {keyword}",
                        field_name="vendor_name",
                        actual_value=invoice.vendor_name,
                        rule_id="VENDOR_SUSPICIOUS_CHECK",
                    )
                )
                break

        # Check if vendor has required fields
        if not invoice.vendor_name or len(invoice.vendor_name.strip()) < 2:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.VENDOR_NOT_AUTHORIZED,
                    severity="HIGH",
                    description="Vendor name is missing or too short",
                    field_name="vendor_name",
                    actual_value=invoice.vendor_name,
                    rule_id="VENDOR_NAME_CHECK",
                )
            )

        return violations

    def _check_contract_terms(self, invoice: Invoice) -> List[BusinessRuleViolation]:
        """Check contract terms and conditions"""
        violations = []

        # Check if invoice has contract reference
        if invoice.contract_reference:
            # This would typically validate against contract database
            # For now, we'll do basic validation
            if not self._is_valid_contract(invoice.contract_reference):
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.CONTRACT_VIOLATION,
                        severity="HIGH",
                        description=f"Invalid or expired contract reference: {invoice.contract_reference}",
                        field_name="contract_reference",
                        actual_value=invoice.contract_reference,
                        rule_id="CONTRACT_VALIDATION",
                    )
                )

        return violations

    def _validate_payment_terms(self, invoice: Invoice) -> List[BusinessRuleViolation]:
        """Validate payment terms"""
        violations = []

        # Check if payment terms are reasonable
        if invoice.payment_terms:
            # This would typically validate against standard payment terms
            # For now, we'll do basic validation
            if not self._is_valid_payment_terms(invoice.payment_terms):
                violations.append(
                    BusinessRuleViolation(
                        violation_type=ViolationType.CONTRACT_VIOLATION,
                        severity="MEDIUM",
                        description=f"Unusual payment terms: {invoice.payment_terms}",
                        field_name="payment_terms",
                        actual_value=invoice.payment_terms,
                        rule_id="PAYMENT_TERMS_CHECK",
                    )
                )

        return violations

    def _check_suspicious_patterns(
        self, invoice: Invoice
    ) -> List[BusinessRuleViolation]:
        """Check for suspicious patterns in invoice"""
        violations = []

        # Check for round numbers (might indicate estimates)
        if invoice.total_amount % 100 == 0 and invoice.total_amount > 1000:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.CONTRACT_VIOLATION,
                    severity="LOW",
                    description=f"Suspicious round number amount: {invoice.total_amount}",
                    field_name="total_amount",
                    actual_value=float(invoice.total_amount),
                    rule_id="ROUND_NUMBER_CHECK",
                )
            )

        # Check for very small amounts (might be test invoices)
        if invoice.total_amount < 1.0:
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.CONTRACT_VIOLATION,
                    severity="MEDIUM",
                    description=f"Very small invoice amount: {invoice.total_amount}",
                    field_name="total_amount",
                    actual_value=float(invoice.total_amount),
                    rule_id="SMALL_AMOUNT_CHECK",
                )
            )

        # Check for future dates
        from datetime import datetime

        if invoice.invoice_date > datetime.now():
            violations.append(
                BusinessRuleViolation(
                    violation_type=ViolationType.DELIVERY_DATE_ISSUE,
                    severity="HIGH",
                    description=f"Invoice date is in the future: {invoice.invoice_date}",
                    field_name="invoice_date",
                    actual_value=invoice.invoice_date.isoformat(),
                    rule_id="FUTURE_DATE_CHECK",
                )
            )

        return violations

    def _check_duplicate_in_database(self, invoice: Invoice) -> bool:
        """Check if invoice exists in database (placeholder implementation)"""
        # This would typically query the database
        # For now, return False (no duplicates found)
        return False

    def _is_valid_contract(self, contract_reference: str) -> bool:
        """Check if contract reference is valid (placeholder implementation)"""
        # This would typically query the contract database
        # For now, return True (contract is valid)
        return True

    def _is_valid_payment_terms(self, payment_terms: str) -> bool:
        """Check if payment terms are valid (placeholder implementation)"""
        # This would typically validate against standard payment terms
        # For now, return True (terms are valid)
        return True

    def get_rule_summary(
        self, violations: List[BusinessRuleViolation]
    ) -> Dict[str, Any]:
        """Get summary of business rule violations"""
        summary = {
            "total_violations": len(violations),
            "critical_violations": len(
                [v for v in violations if v.severity == "CRITICAL"]
            ),
            "high_violations": len([v for v in violations if v.severity == "HIGH"]),
            "medium_violations": len([v for v in violations if v.severity == "MEDIUM"]),
            "low_violations": len([v for v in violations if v.severity == "LOW"]),
            "violations_by_type": {},
            "risk_level": "LOW",
        }

        # Count violations by type
        for violation in violations:
            violation_type = str(violation.violation_type)
            if violation_type not in summary["violations_by_type"]:
                summary["violations_by_type"][violation_type] = 0
            summary["violations_by_type"][violation_type] += 1

        # Determine overall risk level
        if summary["critical_violations"] > 0:
            summary["risk_level"] = "CRITICAL"
        elif summary["high_violations"] > 0:
            summary["risk_level"] = "HIGH"
        elif summary["medium_violations"] > 0:
            summary["risk_level"] = "MEDIUM"

        return summary
