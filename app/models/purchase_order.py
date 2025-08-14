"""
Purchase Order data models
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class POLineItem(BaseModel):
    """Individual line item on a purchase order"""

    description: str = Field(..., description="Item description")
    quantity: int = Field(..., ge=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, description="Agreed price per unit")
    total_price: Decimal = Field(..., ge=0, description="Total price for this line")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    part_number: Optional[str] = Field(None, description="Part number")
    delivery_date: Optional[datetime] = Field(
        None, description="Expected delivery date"
    )

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


class PurchaseOrder(BaseModel):
    """Complete purchase order data structure"""

    po_number: str = Field(..., description="Unique purchase order identifier")
    vendor_name: str = Field(..., description="Name of the vendor/supplier")
    vendor_id: Optional[str] = Field(None, description="Vendor identifier")
    po_date: datetime = Field(..., description="Date PO was created")
    total_authorized: Decimal = Field(..., ge=0, description="Total authorized amount")
    currency: str = Field(default="USD", description="Currency code")
    line_items: List[POLineItem] = Field(..., description="List of PO line items")

    # Additional fields
    contract_reference: Optional[str] = Field(None, description="Reference to contract")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    billing_address: Optional[str] = Field(None, description="Billing address")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Status and tracking
    status: str = Field(
        default="OPEN", description="PO status: OPEN, CLOSED, CANCELLED"
    )
    approved_by: Optional[str] = Field(None, description="Who approved the PO")
    approved_date: Optional[datetime] = Field(None, description="When PO was approved")

    # Processing metadata
    created_at: Optional[datetime] = Field(
        None, description="When PO was created in system"
    )
    updated_at: Optional[datetime] = Field(None, description="When PO was last updated")

    @field_validator("total_authorized")
    @classmethod
    def validate_total_authorized(cls, v, info):
        """Validate that total_authorized matches sum of line items"""
        if info.data and "line_items" in info.data:
            expected = sum(item.total_price for item in info.data["line_items"])
            if abs(v - expected) > Decimal("0.01"):  # Allow for rounding differences
                raise ValueError(
                    f"Total authorized {v} doesn't match sum of line items {expected}"
                )
        return v

    def get_line_item_by_description(self, description: str) -> Optional[POLineItem]:
        """Find line item by description"""
        for item in self.line_items:
            if item.description.lower() == description.lower():
                return item
        return None

    def get_line_item_by_sku(self, sku: str) -> Optional[POLineItem]:
        """Find line item by SKU"""
        for item in self.line_items:
            if item.sku and item.sku.lower() == sku.lower():
                return item
        return None

    def get_total_quantity(self) -> int:
        """Get total quantity across all line items"""
        return sum(item.quantity for item in self.line_items)

    def get_remaining_amount(self, invoiced_amount: Decimal = Decimal("0")) -> Decimal:
        """Get remaining authorized amount after invoiced amount"""
        return self.total_authorized - invoiced_amount

    def is_fully_invoiced(self, invoiced_amount: Decimal = Decimal("0")) -> bool:
        """Check if PO is fully invoiced"""
        return self.get_remaining_amount(invoiced_amount) <= Decimal("0")

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}
