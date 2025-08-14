# PRAT API Documentation

## Overview

The PRAT (Pay Request Approval Tool) API provides endpoints for AI-powered invoice processing, purchase order management, vendor validation, and intelligent payment recommendations.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. In production, implement JWT-based authentication.

## Common Response Format

All API responses follow this format:

```json
{
  "data": {...},
  "message": "Success message",
  "status": "success"
}
```

## Error Responses

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "detail": "Additional error details (in debug mode)"
}
```

---

## Invoice Processing

### Process Invoice

**POST** `/invoices/process-invoice`

Process an uploaded invoice file and generate AI-powered recommendations.

**Request:**
- Content-Type: `multipart/form-data`
- Body: File upload with invoice document

**Parameters:**
- `file` (required): Invoice file (PDF, PNG, JPG, TIFF)
- `auto_approve` (optional): Boolean to auto-approve if within thresholds

**Response:**
```json
{
  "invoice_id": "INV-20240115-0001",
  "invoice_number": "INV-2024-001",
  "vendor_name": "ABC Supplies Inc.",
  "total_amount": 2750.00,
  "recommendation": {
    "action": "MANUAL_REVIEW",
    "confidence_score": 0.85,
    "reasoning": "Invoice requires manual review due to amount exceeding auto-approval threshold",
    "risk_level": "MEDIUM",
    "auto_approvable": false,
    "requires_manual_review": true
  },
  "validation": {
    "po_found": true,
    "po_number": "PO-2024-001",
    "is_valid": false,
    "match_percentage": 100.0,
    "violations_count": 1
  },
  "business_rules": {
    "violations_count": 1,
    "risk_level": "MEDIUM"
  },
  "processing_time_ms": 2450,
  "file_path": "uploads/1705123456_invoice.pdf"
}
```

### Get Invoice

**GET** `/invoices/{invoice_id}`

Retrieve a processed invoice by ID.

**Response:**
```json
{
  "invoice_id": "INV-20240115-0001",
  "invoice": {
    "invoice_number": "INV-2024-001",
    "vendor_name": "ABC Supplies Inc.",
    "total_amount": 2750.00,
    "line_items": [...]
  },
  "recommendation": {
    "action": "MANUAL_REVIEW",
    "confidence_score": 0.85,
    "reasoning": "..."
  },
  "processed_at": "2024-01-15T10:30:00Z",
  "status": "PROCESSED"
}
```

### Get Recommendation

**GET** `/invoices/{invoice_id}/recommendation`

Get the processing recommendation for a specific invoice.

### Get Validation Results

**GET** `/invoices/{invoice_id}/validation`

Get detailed validation results for an invoice.

### Approve Invoice

**POST** `/invoices/{invoice_id}/approve`

Approve an invoice for payment.

**Parameters:**
- `approved_by` (required): Name of person approving
- `notes` (optional): Approval notes

### Reject Invoice

**POST** `/invoices/{invoice_id}/reject`

Reject an invoice.

**Parameters:**
- `rejected_by` (required): Name of person rejecting
- `reason` (required): Reason for rejection
- `notes` (optional): Rejection notes

### List Invoices

**GET** `/invoices/`

List all processed invoices with optional filtering.

**Query Parameters:**
- `vendor` (optional): Filter by vendor name
- `action` (optional): Filter by processing action
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

### Search Invoices

**GET** `/invoices/search/{query}`

Search invoices by various criteria.

### Get Invoice Statistics

**GET** `/invoices/statistics/summary`

Get processing statistics.

### Get Recent History

**GET** `/invoices/history/recent`

Get recent processing history.

**Query Parameters:**
- `limit` (optional): Number of recent items (default: 10)

---

## Purchase Orders

### List Purchase Orders

**GET** `/purchase-orders/`

List all purchase orders with optional filtering.

**Query Parameters:**
- `vendor` (optional): Filter by vendor name
- `status` (optional): Filter by PO status
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

### Get Purchase Order

**GET** `/purchase-orders/{po_number}`

Get a specific purchase order by PO number.

### Create Purchase Order

**POST** `/purchase-orders/`

Create a new purchase order.

**Request Body:**
```json
{
  "po_number": "PO-2024-002",
  "vendor_name": "Tech Solutions LLC",
  "vendor_id": "VEND-002",
  "po_date": "2024-01-20T00:00:00Z",
  "total_authorized": 5000.00,
  "currency": "USD",
  "line_items": [
    {
      "description": "Laptop Computers",
      "quantity": 5,
      "unit_price": 800.00,
      "total_price": 4000.00,
      "sku": "LAPTOP-001"
    }
  ],
  "payment_terms": "Net 30"
}
```

### Update Purchase Order

**PUT** `/purchase-orders/{po_number}`

Update an existing purchase order.

### Delete Purchase Order

**DELETE** `/purchase-orders/{po_number}`

Delete a purchase order.

### Get POs by Vendor

**GET** `/purchase-orders/vendor/{vendor_name}`

Get all purchase orders for a specific vendor.

### Get PO Statistics

**GET** `/purchase-orders/statistics/summary`

Get purchase order statistics.

---

## Vendors

### List Vendors

**GET** `/vendors/`

List all vendors with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by vendor status
- `category` (optional): Filter by vendor category
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

### Get Vendor

**GET** `/vendors/{vendor_id}`

Get a specific vendor by ID.

### Get Vendor by Name

**GET** `/vendors/name/{vendor_name}`

Get a vendor by name.

### Create Vendor

**POST** `/vendors/`

Create a new vendor.

**Request Body:**
```json
{
  "vendor_id": "VEND-005",
  "name": "New Supplier Corp",
  "status": "ACTIVE",
  "authorized": true,
  "category": "Technology",
  "payment_terms": "Net 30",
  "invoice_limit": 10000.00,
  "contact_info": {
    "email": "contact@newsupplier.com",
    "phone": "555-123-4567"
  }
}
```

### Update Vendor

**PUT** `/vendors/{vendor_id}`

Update an existing vendor.

### List Active Vendors

**GET** `/vendors/active/list`

Get all active vendors.

### Get Vendor Contracts

**GET** `/vendors/{vendor_id}/contracts`

Get contracts for a specific vendor.

### Validate Vendor Invoice

**POST** `/vendors/{vendor_name}/validate-invoice`

Validate an invoice against vendor rules.

**Request Body:**
```json
{
  "invoice_amount": 2500.00
}
```

### Get Vendor Statistics

**GET** `/vendors/statistics/summary`

Get vendor statistics.

---

## Recommendations

### List Recommendations

**GET** `/recommendations/`

List all processing recommendations with optional filtering.

**Query Parameters:**
- `action` (optional): Filter by recommendation action
- `risk_level` (optional): Filter by risk level
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

### Get Recommendation

**GET** `/recommendations/{invoice_id}`

Get a specific recommendation by invoice ID.

### Get Recommendations by Action

**GET** `/recommendations/action/{action}`

Get all recommendations for a specific action.

### Get Recommendations by Risk Level

**GET** `/recommendations/risk-level/{risk_level}`

Get all recommendations for a specific risk level.

### Get High-Risk Recommendations

**GET** `/recommendations/high-risk/list`

Get all high-risk recommendations that require attention.

### Get Auto-Approvable Recommendations

**GET** `/recommendations/auto-approvable/list`

Get all recommendations that can be auto-approved.

### Get Recommendation Statistics

**GET** `/recommendations/statistics/summary`

Get recommendation statistics.

---

## System Endpoints

### Health Check

**GET** `/health`

Check system health.

**Response:**
```json
{
  "status": "healthy",
  "service": "PRAT - Pay Request Approval Tool",
  "version": "1.0.0"
}
```

### Root

**GET** `/`

Get API information.

**Response:**
```json
{
  "message": "Welcome to PRAT - Pay Request Approval Tool",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Data Models

### Invoice

```json
{
  "invoice_number": "string",
  "vendor_name": "string",
  "vendor_id": "string",
  "invoice_date": "datetime",
  "due_date": "datetime",
  "total_amount": "decimal",
  "tax_amount": "decimal",
  "subtotal_amount": "decimal",
  "currency": "string",
  "line_items": [
    {
      "description": "string",
      "quantity": "integer",
      "unit_price": "decimal",
      "total_price": "decimal",
      "sku": "string"
    }
  ],
  "po_reference": "string",
  "contract_reference": "string",
  "payment_terms": "string"
}
```

### Purchase Order

```json
{
  "po_number": "string",
  "vendor_name": "string",
  "vendor_id": "string",
  "po_date": "datetime",
  "total_authorized": "decimal",
  "currency": "string",
  "line_items": [
    {
      "description": "string",
      "quantity": "integer",
      "unit_price": "decimal",
      "total_price": "decimal",
      "sku": "string"
    }
  ],
  "status": "string",
  "payment_terms": "string"
}
```

### Processing Recommendation

```json
{
  "action": "APPROVE|REJECT|HOLD|MANUAL_REVIEW",
  "confidence_score": "float",
  "reasoning": "string",
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "auto_approvable": "boolean",
  "requires_manual_review": "boolean",
  "flagged_issues": ["string"],
  "suggested_actions": ["string"],
  "next_steps": ["string"]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement appropriate rate limiting.

## File Upload Limits

- Maximum file size: 10MB
- Supported formats: PDF, PNG, JPG, JPEG, TIFF
- Files are stored in the `uploads/` directory

## Configuration

The API behavior can be configured through environment variables:

- `AUTO_APPROVE_THRESHOLD`: Maximum amount for auto-approval
- `REQUIRE_MANUAL_REVIEW_THRESHOLD`: Amount requiring manual review
- `MAX_OVERAGE_PERCENTAGE`: Maximum allowed overage percentage
- `LLM_MODEL`: AI model to use for processing
- `OPENAI_API_KEY`: OpenAI API key

---

## Examples

### Processing an Invoice

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/process-invoice" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@invoice.pdf"
```

### Getting Invoice Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/statistics/summary" \
     -H "accept: application/json"
```

### Approving an Invoice

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/INV-20240115-0001/approve" \
     -H "accept: application/json" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "approved_by=John%20Smith&notes=Approved%20after%20review"
```

---

## Support

For API support and questions, please refer to the project documentation or create an issue in the repository. 