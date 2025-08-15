"""
Recommendation and validation models for invoice processing
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


class ActionType(str, Enum):
    """Possible processing actions"""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    HOLD = "HOLD"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ViolationType(str, Enum):
    """Types of business rule violations"""

    AMOUNT_EXCEEDS_THRESHOLD = "AMOUNT_EXCEEDS_THRESHOLD"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    INVALID_TAX_CALCULATION = "INVALID_TAX_CALCULATION"
    VENDOR_NOT_AUTHORIZED = "VENDOR_NOT_AUTHORIZED"
    PO_NOT_FOUND = "PO_NOT_FOUND"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    DELIVERY_DATE_ISSUE = "DELIVERY_DATE_ISSUE"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
    OVERAGE_EXCEEDS_LIMIT = "OVERAGE_EXCEEDS_LIMIT"


class BusinessRuleViolation(BaseModel):
    """Individual business rule violation"""

    violation_type: ViolationType = Field(..., description="Type of violation")
    severity: str = Field(..., description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    description: str = Field(..., description="Human-readable description")
    field_name: Optional[str] = Field(None, description="Field that caused violation")
    expected_value: Optional[Any] = Field(None, description="Expected value")
    actual_value: Optional[Any] = Field(None, description="Actual value")
    rule_id: Optional[str] = Field(None, description="Business rule identifier")

    class Config:
        use_enum_values = True


class ValidationResult(BaseModel):
    """Results of invoice validation against PO and business rules"""

    is_valid: bool = Field(..., description="Overall validation result")
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence in validation"
    )

    # PO matching results
    po_found: bool = Field(..., description="Whether matching PO was found")
    po_number: Optional[str] = Field(None, description="Matching PO number")
    po_match_confidence: Optional[float] = Field(
        None, ge=0, le=1, description="PO match confidence"
    )

    # Line item validation
    line_item_matches: List[Dict[str, Any]] = Field(
        default_factory=list, description="Line item matching results"
    )
    total_line_items: int = Field(..., description="Total number of line items")
    matched_line_items: int = Field(..., description="Number of matched line items")

    # Amount validation
    amount_difference: Optional[Decimal] = Field(
        None, description="Difference between invoice and PO amounts"
    )
    amount_difference_percentage: Optional[float] = Field(
        None, description="Percentage difference"
    )
    overage_amount: Optional[Decimal] = Field(
        None, description="Amount exceeding PO authorization"
    )
    overage_percentage: Optional[float] = Field(None, description="Percentage overage")

    # Business rule violations
    violations: List[BusinessRuleViolation] = Field(
        default_factory=list, description="Business rule violations"
    )
    critical_violations: int = Field(
        default=0, description="Number of critical violations"
    )
    high_violations: int = Field(
        default=0, description="Number of high severity violations"
    )

    # Additional validation details
    tax_validation: Dict[str, Any] = Field(
        default_factory=dict, description="Tax calculation validation"
    )
    vendor_validation: Dict[str, Any] = Field(
        default_factory=dict, description="Vendor validation results"
    )
    duplicate_check: Dict[str, Any] = Field(
        default_factory=dict, description="Duplicate invoice check results"
    )

    # Processing metadata
    validation_date: datetime = Field(
        default_factory=datetime.now, description="When validation was performed"
    )
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )

    def get_violations_by_severity(self, severity: str) -> List[BusinessRuleViolation]:
        """Get violations by severity level"""
        return [v for v in self.violations if v.severity.upper() == severity.upper()]

    def has_critical_violations(self) -> bool:
        """Check if there are any critical violations"""
        return self.critical_violations > 0

    def has_high_violations(self) -> bool:
        """Check if there are any high severity violations"""
        return self.high_violations > 0

    def get_match_percentage(self) -> float:
        """Get percentage of line items that matched"""
        if self.total_line_items == 0:
            return 0.0
        return (self.matched_line_items / self.total_line_items) * 100

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class ProcessingRecommendation(BaseModel):
    """Final processing recommendation for an invoice"""

    action: ActionType = Field(..., description="Recommended action")
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence in recommendation"
    )
    reasoning: str = Field(..., description="Detailed reasoning for recommendation")

    # Flagged issues
    flagged_issues: List[str] = Field(
        default_factory=list, description="List of flagged issues"
    )
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")

    # Validation results
    validation_result: ValidationResult = Field(..., description="Validation results")

    # Approval details
    auto_approvable: bool = Field(
        ..., description="Whether invoice can be auto-approved"
    )
    requires_manual_review: bool = Field(
        ..., description="Whether manual review is required"
    )
    approval_threshold_exceeded: bool = Field(
        ..., description="Whether approval threshold was exceeded"
    )

    # Additional recommendations
    suggested_actions: List[str] = Field(
        default_factory=list, description="Suggested follow-up actions"
    )
    next_steps: List[str] = Field(
        default_factory=list, description="Recommended next steps"
    )

    # Processing metadata
    recommendation_date: datetime = Field(
        default_factory=datetime.now, description="When recommendation was generated"
    )
    processing_time_ms: Optional[int] = Field(None, description="Total processing time")

    def is_high_risk(self) -> bool:
        """Check if recommendation indicates high risk"""
        return self.risk_level.upper() in ["HIGH", "CRITICAL"]

    def requires_escalation(self) -> bool:
        """Check if recommendation requires escalation"""
        return (
            self.action == ActionType.REJECT
            or self.action == ActionType.MANUAL_REVIEW
            or self.is_high_risk()
            or self.validation_result.has_critical_violations()
        )

    def get_summary(self) -> str:
        """Get a brief summary of the recommendation"""
        return f"{str(self.action)} - {self.reasoning[:100]}..."

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}
