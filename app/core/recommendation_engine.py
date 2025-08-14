"""
Recommendation engine for generating invoice processing recommendations
"""

import logging
from typing import List, Dict, Any
import time

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.models.recommendation import (
    ProcessingRecommendation,
    ValidationResult,
    BusinessRuleViolation,
    ActionType,
)
from app.config import settings

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates intelligent processing recommendations for invoices"""

    def __init__(self):
        """Initialize the recommendation engine"""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            openai_api_key=settings.openai_api_key,
        )

    def generate_recommendation(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        business_rule_violations: List[BusinessRuleViolation],
    ) -> ProcessingRecommendation:
        """Generate final processing recommendation using AI"""
        try:
            logger.info(
                f"Generating recommendation for invoice {invoice.invoice_number}"
            )
            start_time = time.time()

            # Combine all violations
            all_violations = validation_result.violations + business_rule_violations

            # Determine base action based on rules
            base_action = self._determine_base_action(
                invoice, validation_result, all_violations
            )

            # Generate AI reasoning
            reasoning = self._generate_ai_reasoning(
                invoice, validation_result, all_violations, base_action
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                validation_result, all_violations
            )

            # Determine risk level
            risk_level = self._determine_risk_level(all_violations)

            # Check approval criteria
            auto_approvable = self._is_auto_approvable(invoice, all_violations)
            requires_manual_review = self._requires_manual_review(
                invoice, all_violations
            )
            approval_threshold_exceeded = self._approval_threshold_exceeded(invoice)

            # Generate flagged issues
            flagged_issues = self._generate_flagged_issues(all_violations)

            # Generate suggested actions
            suggested_actions = self._generate_suggested_actions(
                invoice, validation_result, all_violations
            )

            # Generate next steps
            next_steps = self._generate_next_steps(base_action, all_violations)

            processing_time = (time.time() - start_time) * 1000

            recommendation = ProcessingRecommendation(
                action=base_action,
                confidence_score=confidence_score,
                reasoning=reasoning,
                flagged_issues=flagged_issues,
                risk_level=risk_level,
                validation_result=validation_result,
                auto_approvable=auto_approvable,
                requires_manual_review=requires_manual_review,
                approval_threshold_exceeded=approval_threshold_exceeded,
                suggested_actions=suggested_actions,
                next_steps=next_steps,
                processing_time_ms=int(processing_time),
            )

            logger.info(f"Recommendation generated in {processing_time:.2f}ms")
            return recommendation

        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            raise

    def _determine_base_action(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
    ) -> ActionType:
        """Determine base action based on validation results and violations"""

        # Check for critical violations (automatic reject)
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        if critical_violations:
            return ActionType.REJECT

        # Check for high severity violations
        high_violations = [v for v in violations if v.severity == "HIGH"]
        if high_violations:
            return ActionType.MANUAL_REVIEW

        # Check if PO was found and validation passed
        if validation_result.po_found and validation_result.is_valid:
            # Check if amount is within auto-approve threshold
            if invoice.total_amount <= settings.auto_approve_threshold:
                return ActionType.APPROVE
            else:
                return ActionType.MANUAL_REVIEW

        # Check if PO was not found
        if not validation_result.po_found:
            return ActionType.HOLD

        # Check for medium violations
        medium_violations = [v for v in violations if v.severity == "MEDIUM"]
        if medium_violations:
            return ActionType.MANUAL_REVIEW

        # Default to manual review for safety
        return ActionType.MANUAL_REVIEW

    def _generate_ai_reasoning(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
        action: ActionType,
    ) -> str:
        """Generate AI-powered reasoning for the recommendation"""
        try:
            # Create prompt for AI reasoning
            prompt = self._create_reasoning_prompt(
                invoice, validation_result, violations, action
            )

            messages = [
                SystemMessage(
                    content="You are an expert invoice processing analyst. Provide clear, concise reasoning for processing recommendations."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generating AI reasoning: {e}")
            # Fallback to rule-based reasoning
            return self._generate_fallback_reasoning(
                invoice, validation_result, violations, action
            )

    def _create_reasoning_prompt(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
        action: ActionType,
    ) -> str:
        """Create prompt for AI reasoning generation"""

        # Summarize validation results
        po_status = "found" if validation_result.po_found else "not found"
        po_number = validation_result.po_number or "N/A"
        match_percentage = validation_result.get_match_percentage()

        # Summarize violations
        violation_summary = []
        for violation in violations:
            violation_summary.append(f"- {violation.severity}: {violation.description}")

        violations_text = "\n".join(violation_summary) if violation_summary else "None"

        return f"""
Based on the following invoice processing results, provide a clear and professional reasoning for the recommended action.

INVOICE DETAILS:
- Invoice Number: {invoice.invoice_number}
- Vendor: {invoice.vendor_name}
- Amount: ${invoice.total_amount}
- Date: {invoice.invoice_date}

VALIDATION RESULTS:
- Purchase Order: {po_status} ({po_number})
- Line Item Match: {match_percentage:.1f}%
- Overall Valid: {validation_result.is_valid}
- Confidence Score: {validation_result.confidence_score:.2f}

VIOLATIONS FOUND:
{violations_text}

RECOMMENDED ACTION: {action.value}

Please provide a 2-3 sentence explanation that:
1. Summarizes the key findings
2. Explains why this action was recommended
3. Mentions any specific issues that need attention

Keep the tone professional and factual.
"""

    def _generate_fallback_reasoning(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
        action: ActionType,
    ) -> str:
        """Generate fallback reasoning when AI is unavailable"""

        if action == ActionType.APPROVE:
            return f"Invoice {invoice.invoice_number} from {invoice.vendor_name} for ${invoice.total_amount} is approved. Purchase order validation passed with {validation_result.get_match_percentage():.1f}% line item match and no critical violations found."

        elif action == ActionType.REJECT:
            critical_violations = [v for v in violations if v.severity == "CRITICAL"]
            return f"Invoice {invoice.invoice_number} is rejected due to {len(critical_violations)} critical violation(s). Key issues: {', '.join([v.description for v in critical_violations[:2]])}"

        elif action == ActionType.MANUAL_REVIEW:
            return f"Invoice {invoice.invoice_number} requires manual review. Purchase order {'found' if validation_result.po_found else 'not found'} with {len(violations)} violation(s) detected. Amount ${invoice.total_amount} exceeds auto-approval threshold."

        else:  # HOLD
            return f"Invoice {invoice.invoice_number} is placed on hold. No matching purchase order found for vendor {invoice.vendor_name}. Manual intervention required to identify correct PO or create new authorization."

    def _calculate_confidence_score(
        self,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
    ) -> float:
        """Calculate confidence score for the recommendation"""

        # Start with validation confidence
        confidence = validation_result.confidence_score

        # Reduce confidence based on violations
        violation_penalty = min(len(violations) * 0.1, 0.4)  # Max 40% penalty

        # Weight violations by severity
        critical_penalty = (
            len([v for v in violations if v.severity == "CRITICAL"]) * 0.2
        )
        high_penalty = len([v for v in violations if v.severity == "HIGH"]) * 0.15
        medium_penalty = len([v for v in violations if v.severity == "MEDIUM"]) * 0.1

        total_penalty = (
            violation_penalty + critical_penalty + high_penalty + medium_penalty
        )
        confidence = max(confidence - total_penalty, 0.1)  # Minimum 10% confidence

        return confidence

    def _determine_risk_level(self, violations: List[BusinessRuleViolation]) -> str:
        """Determine overall risk level based on violations"""

        critical_count = len([v for v in violations if v.severity == "CRITICAL"])
        high_count = len([v for v in violations if v.severity == "HIGH"])
        medium_count = len([v for v in violations if v.severity == "MEDIUM"])

        if critical_count > 0:
            return "CRITICAL"
        elif high_count > 0:
            return "HIGH"
        elif medium_count > 0:
            return "MEDIUM"
        else:
            return "LOW"

    def _is_auto_approvable(
        self, invoice: Invoice, violations: List[BusinessRuleViolation]
    ) -> bool:
        """Check if invoice can be auto-approved"""

        # Check for critical or high violations
        critical_or_high = [v for v in violations if v.severity in ["CRITICAL", "HIGH"]]
        if critical_or_high:
            return False

        # Check amount threshold
        if invoice.total_amount > settings.auto_approve_threshold:
            return False

        return True

    def _requires_manual_review(
        self, invoice: Invoice, violations: List[BusinessRuleViolation]
    ) -> bool:
        """Check if invoice requires manual review"""

        # Any high or critical violations require review
        high_or_critical = [v for v in violations if v.severity in ["HIGH", "CRITICAL"]]
        if high_or_critical:
            return True

        # Amount exceeds manual review threshold
        if invoice.total_amount > settings.require_manual_review_threshold:
            return True

        return False

    def _approval_threshold_exceeded(self, invoice: Invoice) -> bool:
        """Check if approval threshold was exceeded"""
        return invoice.total_amount > settings.auto_approve_threshold

    def _generate_flagged_issues(
        self, violations: List[BusinessRuleViolation]
    ) -> List[str]:
        """Generate list of flagged issues"""
        issues = []

        for violation in violations:
            if violation.severity in ["HIGH", "CRITICAL"]:
                issues.append(f"{violation.severity}: {violation.description}")

        return issues

    def _generate_suggested_actions(
        self,
        invoice: Invoice,
        validation_result: ValidationResult,
        violations: List[BusinessRuleViolation],
    ) -> List[str]:
        """Generate suggested follow-up actions"""
        actions = []

        # If PO not found, suggest PO creation
        if not validation_result.po_found:
            actions.append("Create purchase order for this vendor")
            actions.append("Verify vendor is authorized")

        # If violations found, suggest resolution
        if violations:
            actions.append("Review and resolve identified violations")
            actions.append("Contact vendor for clarification if needed")

        # If amount is high, suggest additional review
        if invoice.total_amount > settings.require_manual_review_threshold:
            actions.append("Obtain additional approval for high-value invoice")

        # If tax issues, suggest verification
        tax_violations = [
            v for v in violations if v.violation_type.value == "INVALID_TAX_CALCULATION"
        ]
        if tax_violations:
            actions.append("Verify tax calculations with accounting team")

        return actions

    def _generate_next_steps(
        self, action: ActionType, violations: List[BusinessRuleViolation]
    ) -> List[str]:
        """Generate recommended next steps"""
        steps = []

        if action == ActionType.APPROVE:
            steps.append("Process payment according to payment terms")
            steps.append("Update invoice status in system")

        elif action == ActionType.REJECT:
            steps.append("Notify vendor of rejection")
            steps.append("Document rejection reasons")
            steps.append("Return invoice to vendor for correction")

        elif action == ActionType.MANUAL_REVIEW:
            steps.append("Assign to appropriate reviewer")
            steps.append("Gather additional documentation if needed")
            steps.append("Schedule review meeting if required")

        else:  # HOLD
            steps.append("Investigate missing purchase order")
            steps.append("Contact vendor for PO reference")
            steps.append("Create PO if vendor is authorized")

        return steps
