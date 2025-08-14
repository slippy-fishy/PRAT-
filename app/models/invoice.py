"""
Invoice data models
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class InvoiceLineItem(BaseModel):
    """Individual line item on an invoice"""

    description: str = Field(..., description="Item description")
    quantity: int = Field(..., ge=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    total_price: Decimal = Field(..., ge=0, description="Total price for this line")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    po_reference: Optional[str] = Field(None, description="Reference to PO line item")

    @field_validator("total_price")
    @classmethod
    def validate_total_price(cls, v, info):
        """Validate that total_price matches quantity * unit_price"""
        if info.data and "quantity" in info.data and "unit_price" in info.data:
            expected = info.data["quantity"] * info.data["unit_price"]
            if abs(v - expected) > Decimal("0.01"):  # Allow for rounding differences
                raise ValueError(
                    f"Total price {v} doesn't match quantity * unit_price {expected}"
                )
        return v

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class Invoice(BaseModel):
    """Complete invoice data structure"""

    invoice_number: str = Field(..., description="Unique invoice identifier")
    vendor_name: str = Field(..., description="Name of the vendor/supplier")
    vendor_id: Optional[str] = Field(None, description="Vendor identifier")
    invoice_date: datetime = Field(..., description="Date invoice was issued")
    due_date: datetime = Field(..., description="Payment due date")
    total_amount: Decimal = Field(..., ge=0, description="Total invoice amount")
    tax_amount: Decimal = Field(..., ge=0, description="Total tax amount")
    subtotal_amount: Decimal = Field(..., ge=0, description="Subtotal before tax")
    currency: str = Field(default="USD", description="Currency code")
    line_items: List[InvoiceLineItem] = Field(
        ..., description="List of invoice line items"
    )

    # Additional fields
    po_reference: Optional[str] = Field(None, description="Reference to purchase order")
    contract_reference: Optional[str] = Field(None, description="Reference to contract")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    billing_address: Optional[str] = Field(None, description="Billing address")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Processing metadata
    file_path: Optional[str] = Field(None, description="Path to original file")
    extracted_at: Optional[datetime] = Field(
        None, description="When data was extracted"
    )
    confidence_score: Optional[float] = Field(
        None, ge=0, le=1, description="Extraction confidence"
    )

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v, info):
        """Validate that total_amount matches subtotal + tax"""
        if info.data and "subtotal_amount" in info.data and "tax_amount" in info.data:
            expected = info.data["subtotal_amount"] + info.data["tax_amount"]
            if abs(v - expected) > Decimal("0.01"):  # Allow for rounding differences
                raise ValueError(
                    f"Total amount {v} doesn't match subtotal + tax {expected}"
                )
        return v

    @field_validator("subtotal_amount")
    @classmethod
    def validate_subtotal(cls, v, info):
        """Validate that subtotal matches sum of line items"""
        if info.data and "line_items" in info.data:
            expected = sum(item.total_price for item in info.data["line_items"])
            if abs(v - expected) > Decimal("0.01"):  # Allow for rounding differences
                raise ValueError(
                    f"Subtotal {v} doesn't match sum of line items {expected}"
                )
        return v

    def get_line_item_by_description(
        self, description: str
    ) -> Optional[InvoiceLineItem]:
        """Find line item by description"""
        for item in self.line_items:
            if item.description.lower() == description.lower():
                return item
        return None

    def get_total_quantity(self) -> int:
        """Get total quantity across all line items"""
        return sum(item.quantity for item in self.line_items)

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}
