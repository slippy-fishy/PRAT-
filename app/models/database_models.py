"""
Database models for PRAT system
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Numeric, Date, TIMESTAMP, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class PurchaseOrderDB(Base):
    """Database model for Purchase Orders"""
    __tablename__ = "purchase_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255))
    vendor_id = Column(String(100), index=True)
    total_amount = Column(Numeric(12, 2))
    currency = Column(String(3), default="USD")
    po_date = Column(Date)
    delivery_date = Column(Date)
    status = Column(String(50), default="active")
    file_path = Column(Text)
    file_hash = Column(String(64), index=True)  # For detecting file changes
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    
    # Relationship to line items - temporarily commented out
    # line_items = relationship("POLineItemDB", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder(po_number='{self.po_number}', vendor='{self.vendor_name}')>"

class POLineItemDB(Base):
    """Database model for PO Line Items"""
    __tablename__ = "po_line_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key constraint already exists in DB
    line_number = Column(Integer)
    description = Column(Text)
    quantity = Column(Numeric(10, 2))
    unit_price = Column(Numeric(10, 2))
    total_amount = Column(Numeric(12, 2))
    product_code = Column(String(100))
    category = Column(String(100))
    
    # Relationship to parent PO - temporarily commented out
    # purchase_order = relationship("PurchaseOrderDB", back_populates="line_items")
    
    def __repr__(self):
        return f"<POLineItem(description='{self.description}', quantity={self.quantity})>"

class InvoiceDB(Base):
    """Database model for Invoices"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(100), index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    total_amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    subtotal_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    po_reference = Column(String(100), index=True)
    contract_reference = Column(String(255))
    payment_terms = Column(String(100))
    shipping_address = Column(Text)
    billing_address = Column(Text)
    notes = Column(Text)
    file_path = Column(Text)
    file_hash = Column(String(64))
    status = Column(String(50), default="pending")
    recommendation = Column(Text)
    confidence_score = Column(Numeric(3, 2))
    processed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    
    # Relationship to line items - temporarily commented out
    # line_items = relationship("InvoiceLineItemDB", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(invoice_number='{self.invoice_number}', vendor='{self.vendor_name}')>"

class InvoiceLineItemDB(Base):
    """Database model for Invoice Line Items"""
    __tablename__ = "invoice_line_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key constraint already exists in DB
    line_number = Column(Integer)
    description = Column(Text)
    quantity = Column(Numeric(10, 2))
    unit_price = Column(Numeric(10, 2))
    total_amount = Column(Numeric(12, 2))
    product_code = Column(String(100))
    category = Column(String(100))
    
    # Relationship to parent invoice - temporarily commented out
    # invoice = relationship("InvoiceDB", back_populates="line_items")
    
    def __repr__(self):
        return f"<InvoiceLineItem(description='{self.description}', quantity={self.quantity})>"

class ProcessingHistoryDB(Base):
    """Database model for Processing History"""
    __tablename__ = "processing_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type = Column(String(50), nullable=False)  # 'invoice' or 'po'
    document_id = Column(String(100), nullable=False)   # invoice_number or po_number
    processing_date = Column(TIMESTAMP)
    status = Column(String(50), nullable=False)         # 'success', 'error', 'pending'
    error_message = Column(Text)
    processing_time_ms = Column(Integer)
    ai_confidence_score = Column(Numeric(3, 2))
    recommendation = Column(Text)
    
    def __repr__(self):
        return f"<ProcessingHistory(document_type='{self.document_type}', document_id='{self.document_id}')>"

# Create indexes for better performance
Index('idx_po_number', PurchaseOrderDB.po_number)
Index('idx_vendor_id', PurchaseOrderDB.vendor_id)
Index('idx_po_line_items_po_id', POLineItemDB.po_id)
Index('idx_invoice_number', InvoiceDB.invoice_number)
Index('idx_invoice_vendor', InvoiceDB.vendor_name)
Index('idx_invoice_line_items_invoice_id', InvoiceLineItemDB.invoice_id)
Index('idx_processing_history_document', ProcessingHistoryDB.document_type, ProcessingHistoryDB.document_id)
