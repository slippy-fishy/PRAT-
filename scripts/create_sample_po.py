#!/usr/bin/env python3
"""
Create a sample Purchase Order PDF for testing PRAT
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

def create_sample_po():
    """Create a sample PDF purchase order"""
    
    # Create the sample_data directory if it doesn't exist
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Create the PDF file
    pdf_path = sample_dir / "sample_purchase_order.pdf"
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
    story.append(Paragraph("PURCHASE ORDER", title_style))
    story.append(Spacer(1, 20))
    
    # PO header
    header_data = [
        ['PO Number:', 'PO-2024-001'],
        ['Date:', '2024-01-15'],
        ['Vendor:', 'ABC Supplies Inc.'],
        ['Vendor ID:', 'VEND-001']
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
        ['Company:', 'ABC Supplies Inc.'],
        ['Address:', '123 Main St, Anytown, USA 12345'],
        ['Phone:', '555-123-4567'],
        ['Email:', 'orders@abcsupplies.com'],
        ['Contact:', 'John Smith']
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
        ['Description', 'Qty', 'Unit Price', 'Total', 'SKU', 'Part #'],
        ['Office Chairs', '10', '$150.00', '$1,500.00', 'CHAIR-001', 'OC-100'],
        ['Desk Lamps', '20', '$50.00', '$1,000.00', 'LAMP-001', 'DL-200']
    ]
    
    line_items_table = Table(line_items_data, colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch])
    line_items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
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
        ['Tax (0%):', '$0.00'],
        ['Total Authorized:', '$2,500.00']
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
    
    # Terms and conditions
    terms_data = [
        ['Payment Terms:', 'Net 30'],
        ['Delivery Address:', '123 Business Ave, Corp City, USA 54321'],
        ['Billing Address:', '123 Business Ave, Corp City, USA 54321'],
        ['Contract Reference:', 'CONTRACT-2024-001'],
        ['Status:', 'OPEN'],
        ['Approved By:', 'John Smith'],
        ['Approval Date:', '2024-01-16']
    ]
    
    terms_table = Table(terms_data, colWidths=[2*inch, 4*inch])
    terms_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(terms_table)
    
    # Build the PDF
    doc.build(story)
    
    print(f"✅ Sample PO PDF created: {pdf_path}")
    print(f"📄 File size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    return str(pdf_path)

if __name__ == "__main__":
    try:
        pdf_path = create_sample_po()
        print(f"\n🎉 Success! You can now use this PO PDF to test PRAT:")
        print(f"   1. Start the server: make run")
        print(f"   2. Go to: http://localhost:8000/docs")
        print(f"   3. Use the file: {pdf_path}")
        print(f"   4. Test the POST /api/v1/purchase-orders/upload endpoint")
        print(f"   5. Then test invoice processing against your uploaded PO!")
    except Exception as e:
        print(f"❌ Error creating PO PDF: {e}")
        sys.exit(1)
