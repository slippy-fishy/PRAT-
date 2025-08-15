#!/usr/bin/env python3
"""
Create a sample PDF invoice for testing PRAT
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

def create_sample_invoice():
    """Create a sample PDF invoice"""
    
    # Create the sample_data directory if it doesn't exist
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Create the PDF file
    pdf_path = sample_dir / "sample_invoice.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Build the story (content)
    story = []
    
    # Title
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 20))
    
    # Invoice header
    header_data = [
        ['Invoice Number:', 'INV-2024-001'],
        ['Date:', '2024-01-15'],
        ['Due Date:', '2024-02-15'],
        ['PO Reference:', 'PO-2024-001']
    ]
    
    header_table = Table(header_data, colWidths=[2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Vendor information
    vendor_data = [
        ['Vendor:', 'ABC Supplies Inc.'],
        ['Vendor ID:', 'VEND-001'],
        ['Address:', '123 Main St, Anytown, USA 12345'],
        ['Phone:', '555-123-4567'],
        ['Email:', 'orders@abcsupplies.com']
    ]
    
    vendor_table = Table(vendor_data, colWidths=[2*inch, 4*inch])
    vendor_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(vendor_table)
    story.append(Spacer(1, 20))
    
    # Line items
    line_items_data = [
        ['Description', 'Qty', 'Unit Price', 'Total'],
        ['Office Chairs', '10', '$150.00', '$1,500.00'],
        ['Desk Lamps', '20', '$50.00', '$1,000.00']
    ]
    
    line_items_table = Table(line_items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    line_items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
    ]))
    story.append(Paragraph("Line Items:", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(line_items_table)
    story.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ['Subtotal:', '$2,500.00'],
        ['Tax (10%):', '$250.00'],
        ['Total:', '$2,750.00']
    ]
    
    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey)
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 20))
    
    # Payment terms
    payment_data = [
        ['Payment Terms:', 'Net 30'],
        ['Payment Address:', 'ABC Supplies Inc., 123 Main St, Anytown, USA 12345']
    ]
    
    payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(payment_table)
    
    # Build the PDF
    doc.build(story)
    
    print(f"✅ Sample PDF invoice created: {pdf_path}")
    print(f"📄 File size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    return str(pdf_path)

if __name__ == "__main__":
    try:
        pdf_path = create_sample_invoice()
        print(f"\n🎉 Success! You can now use this PDF to test PRAT:")
        print(f"   1. Start the server: make run")
        print(f"   2. Go to: http://localhost:8000/docs")
        print(f"   3. Use the file: {pdf_path}")
        print(f"   4. Test the POST /api/v1/invoices/process-invoice endpoint")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        sys.exit(1)
