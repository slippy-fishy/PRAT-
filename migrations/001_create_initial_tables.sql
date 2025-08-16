-- Migration: 001_create_initial_tables.sql
-- Description: Create initial database schema for PRAT system
-- Date: 2024-08-15

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Purchase Orders table
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_number VARCHAR(100) UNIQUE NOT NULL,
    vendor_name VARCHAR(255),
    vendor_id VARCHAR(100),
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    po_date DATE,
    delivery_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    file_path TEXT,
    file_hash VARCHAR(64), -- For detecting file changes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- PO Line Items table
CREATE TABLE po_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    line_number INTEGER,
    description TEXT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    product_code VARCHAR(100),
    category VARCHAR(100)
);

-- Invoices table
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_id VARCHAR(100),
    invoice_date DATE NOT NULL,
    due_date DATE,
    total_amount DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    subtotal_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    po_reference VARCHAR(100),
    contract_reference VARCHAR(255),
    payment_terms VARCHAR(100),
    shipping_address TEXT,
    billing_address TEXT,
    notes TEXT,
    file_path TEXT,
    file_hash VARCHAR(64),
    status VARCHAR(50) DEFAULT 'pending',
    recommendation TEXT,
    confidence_score DECIMAL(3,2),
    processed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Invoice Line Items table
CREATE TABLE invoice_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    line_number INTEGER,
    description TEXT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    product_code VARCHAR(100),
    category VARCHAR(100)
);

-- Processing History table
CREATE TABLE processing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    action VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2),
    reasoning TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_po_number ON purchase_orders(po_number);
CREATE INDEX idx_vendor_id ON purchase_orders(vendor_id);
CREATE INDEX idx_po_line_items_po_id ON po_line_items(po_id);
CREATE INDEX idx_invoice_vendor_name ON invoices(vendor_name);
CREATE INDEX idx_invoice_status ON invoices(status);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_invoice_line_items_invoice_id ON invoice_line_items(invoice_id);

-- Add comments for documentation
COMMENT ON TABLE purchase_orders IS 'Purchase orders extracted from uploaded documents';
COMMENT ON TABLE po_line_items IS 'Individual line items within purchase orders';
COMMENT ON TABLE invoices IS 'Invoices processed by the system';
COMMENT ON TABLE invoice_line_items IS 'Individual line items within invoices';
COMMENT ON TABLE processing_history IS 'History of invoice processing decisions';

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_purchase_orders_updated_at 
    BEFORE UPDATE ON purchase_orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at 
    BEFORE UPDATE ON invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
