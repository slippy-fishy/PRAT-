"""
Tests for invoice processing functionality
"""

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from app.models.invoice import Invoice, InvoiceLineItem
from app.models.purchase_order import PurchaseOrder, POLineItem
from app.models.recommendation import (
    ProcessingRecommendation,
    ValidationResult,
    ActionType,
)
from app.core.document_processor import DocumentProcessor
from app.core.po_matcher import POMatcher
from app.core.business_rules import BusinessRulesEngine
from app.core.recommendation_engine import RecommendationEngine
from app.services.po_service import POService


class TestInvoiceProcessing:
    """Test invoice processing functionality"""

    @pytest.fixture
    def sample_invoice(self):
        """Create a sample invoice for testing"""
        return Invoice(
            invoice_number="INV-2024-001",
            vendor_name="ABC Supplies Inc.",
            vendor_id="VEND-001",
            invoice_date=datetime(2024, 1, 15),
            due_date=datetime(2024, 2, 15),
            total_amount=Decimal("2750.00"),
            tax_amount=Decimal("250.00"),
            subtotal_amount=Decimal("2500.00"),
            currency="USD",
            line_items=[
                InvoiceLineItem(
                    description="Office Chairs",
                    quantity=10,
                    unit_price=Decimal("150.00"),
                    total_price=Decimal("1500.00"),
                    sku="CHAIR-001",
                ),
                InvoiceLineItem(
                    description="Desk Lamps",
                    quantity=20,
                    unit_price=Decimal("50.00"),
                    total_price=Decimal("1000.00"),
                    sku="LAMP-001",
                ),
            ],
            po_reference="PO-2024-001",
        )

    @pytest.fixture
    def sample_po(self):
        """Create a sample purchase order for testing"""
        return PurchaseOrder(
            po_number="PO-2024-001",
            vendor_name="ABC Supplies Inc.",
            vendor_id="VEND-001",
            po_date=datetime(2024, 1, 10),
            total_authorized=Decimal("2500.00"),
            currency="USD",
            line_items=[
                POLineItem(
                    description="Office Chairs",
                    quantity=10,
                    unit_price=Decimal("150.00"),
                    total_price=Decimal("1500.00"),
                    sku="CHAIR-001",
                ),
                POLineItem(
                    description="Desk Lamps",
                    quantity=20,
                    unit_price=Decimal("50.00"),
                    total_price=Decimal("1000.00"),
                    sku="LAMP-001",
                ),
            ],
        )

    def test_invoice_creation(self, sample_invoice):
        """Test invoice creation and validation"""
        assert sample_invoice.invoice_number == "INV-2024-001"
        assert sample_invoice.vendor_name == "ABC Supplies Inc."
        assert sample_invoice.total_amount == Decimal("2750.00")
        assert len(sample_invoice.line_items) == 2

        # Test line item validation
        for item in sample_invoice.line_items:
            assert item.total_price == item.quantity * item.unit_price

    def test_po_creation(self, sample_po):
        """Test purchase order creation and validation"""
        assert sample_po.po_number == "PO-2024-001"
        assert sample_po.vendor_name == "ABC Supplies Inc."
        assert sample_po.total_authorized == Decimal("2500.00")
        assert len(sample_po.line_items) == 2

        # Test line item validation
        for item in sample_po.line_items:
            assert item.total_price == item.quantity * item.unit_price

    @patch("app.core.document_processor.ChatOpenAI")
    def test_document_processor_initialization(self, mock_llm):
        """Test document processor initialization"""
        processor = DocumentProcessor()
        assert processor.llm is not None

    def test_po_matcher_initialization(self):
        """Test PO matcher initialization"""
        po_service = POService()
        matcher = POMatcher(po_service)
        assert matcher.po_service is not None

    def test_business_rules_engine_initialization(self):
        """Test business rules engine initialization"""
        engine = BusinessRulesEngine()
        assert engine.auto_approve_threshold > 0
        assert engine.require_manual_review_threshold > 0

    @patch("app.core.recommendation_engine.ChatOpenAI")
    def test_recommendation_engine_initialization(self, mock_llm):
        """Test recommendation engine initialization"""
        engine = RecommendationEngine()
        assert engine.llm is not None

    def test_po_matching_by_reference(self, sample_invoice, sample_po):
        """Test PO matching by direct reference"""
        po_service = POService()
        matcher = POMatcher(po_service)

        # Mock the PO service to return our sample PO
        with patch.object(po_service, "get_po_by_number", return_value=sample_po):
            matching_po = matcher.find_matching_po(sample_invoice)
            assert matching_po is not None
            assert matching_po.po_number == "PO-2024-001"

    def test_po_validation(self, sample_invoice, sample_po):
        """Test PO validation against invoice"""
        po_service = POService()
        matcher = POMatcher(po_service)

        validation_result = matcher.validate_invoice_against_po(
            sample_invoice, sample_po
        )

        assert validation_result.po_found is True
        assert validation_result.po_number == "PO-2024-001"
        assert validation_result.total_line_items == 2
        assert validation_result.matched_line_items == 2

        # Should have violations due to amount overage
        assert len(validation_result.violations) > 0

    def test_business_rules_check(self, sample_invoice):
        """Test business rules validation"""
        engine = BusinessRulesEngine()
        violations = engine.check_business_rules(sample_invoice)

        # Should have violations due to amount exceeding threshold
        assert len(violations) > 0

        # Check for specific violation types
        violation_types = [v.violation_type.value for v in violations]
        assert "AMOUNT_EXCEEDS_THRESHOLD" in violation_types

    @patch("app.core.recommendation_engine.ChatOpenAI")
    def test_recommendation_generation(self, mock_llm, sample_invoice):
        """Test recommendation generation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = (
            '{"action": "MANUAL_REVIEW", "reasoning": "Test reasoning"}'
        )
        mock_llm.return_value.invoke.return_value = mock_response

        engine = RecommendationEngine()

        # Create mock validation result
        validation_result = ValidationResult(
            is_valid=False,
            confidence_score=0.8,
            po_found=True,
            po_number="PO-2024-001",
            total_line_items=2,
            matched_line_items=2,
        )

        # Create mock business rule violations
        from app.models.recommendation import BusinessRuleViolation, ViolationType

        violations = [
            BusinessRuleViolation(
                violation_type=ViolationType.AMOUNT_EXCEEDS_THRESHOLD,
                severity="MEDIUM",
                description="Amount exceeds threshold",
            )
        ]

        recommendation = engine.generate_recommendation(
            sample_invoice, validation_result, violations
        )

        assert recommendation is not None
        assert recommendation.action in [
            ActionType.APPROVE,
            ActionType.REJECT,
            ActionType.HOLD,
            ActionType.MANUAL_REVIEW,
        ]
        assert recommendation.confidence_score >= 0.0
        assert recommendation.confidence_score <= 1.0

    def test_invoice_line_item_validation(self):
        """Test invoice line item validation"""
        # Valid line item
        valid_item = InvoiceLineItem(
            description="Test Item",
            quantity=5,
            unit_price=Decimal("10.00"),
            total_price=Decimal("50.00"),
        )
        assert valid_item.total_price == Decimal("50.00")

        # Invalid line item (should raise validation error)
        with pytest.raises(ValueError):
            InvoiceLineItem(
                description="Test Item",
                quantity=5,
                unit_price=Decimal("10.00"),
                total_price=Decimal("60.00"),  # Incorrect total
            )

    def test_po_line_item_validation(self):
        """Test PO line item validation"""
        # Valid line item
        valid_item = POLineItem(
            description="Test Item",
            quantity=5,
            unit_price=Decimal("10.00"),
            total_price=Decimal("50.00"),
        )
        assert valid_item.total_price == Decimal("50.00")

        # Invalid line item (should raise validation error)
        with pytest.raises(ValueError):
            POLineItem(
                description="Test Item",
                quantity=5,
                unit_price=Decimal("10.00"),
                total_price=Decimal("60.00"),  # Incorrect total
            )

    def test_invoice_total_validation(self):
        """Test invoice total validation"""
        # Valid invoice
        valid_invoice = Invoice(
            invoice_number="INV-001",
            vendor_name="Test Vendor",
            invoice_date=datetime.now(),
            due_date=datetime.now(),
            total_amount=Decimal("110.00"),
            tax_amount=Decimal("10.00"),
            subtotal_amount=Decimal("100.00"),
            line_items=[
                InvoiceLineItem(
                    description="Item 1",
                    quantity=1,
                    unit_price=Decimal("100.00"),
                    total_price=Decimal("100.00"),
                )
            ],
        )
        assert valid_invoice.total_amount == Decimal("110.00")

        # Invalid invoice (should raise validation error)
        with pytest.raises(ValueError):
            Invoice(
                invoice_number="INV-001",
                vendor_name="Test Vendor",
                invoice_date=datetime.now(),
                due_date=datetime.now(),
                total_amount=Decimal("120.00"),  # Incorrect total
                tax_amount=Decimal("10.00"),
                subtotal_amount=Decimal("100.00"),
                line_items=[
                    InvoiceLineItem(
                        description="Item 1",
                        quantity=1,
                        unit_price=Decimal("100.00"),
                        total_price=Decimal("100.00"),
                    )
                ],
            )

    def test_po_total_validation(self):
        """Test PO total validation"""
        # Valid PO
        valid_po = PurchaseOrder(
            po_number="PO-001",
            vendor_name="Test Vendor",
            po_date=datetime.now(),
            total_authorized=Decimal("100.00"),
            line_items=[
                POLineItem(
                    description="Item 1",
                    quantity=1,
                    unit_price=Decimal("100.00"),
                    total_price=Decimal("100.00"),
                )
            ],
        )
        assert valid_po.total_authorized == Decimal("100.00")

        # Invalid PO (should raise validation error)
        with pytest.raises(ValueError):
            PurchaseOrder(
                po_number="PO-001",
                vendor_name="Test Vendor",
                po_date=datetime.now(),
                total_authorized=Decimal("120.00"),  # Incorrect total
                line_items=[
                    POLineItem(
                        description="Item 1",
                        quantity=1,
                        unit_price=Decimal("100.00"),
                        total_price=Decimal("100.00"),
                    )
                ],
            )


class TestDocumentProcessing:
    """Test document processing functionality"""

    def test_text_extraction_from_pdf(self):
        """Test PDF text extraction (mock)"""
        processor = DocumentProcessor()

        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\nTest PDF content\n%%EOF")
            temp_file_path = temp_file.name

        try:
            # Test text extraction (this will fail without proper PDF content, but tests the method)
            with patch("pdfplumber.open") as mock_pdfplumber:
                mock_page = Mock()
                mock_page.extract_text.return_value = "Test invoice content"
                mock_pdfplumber.return_value.__enter__.return_value.pages = [mock_page]

                text = processor.extract_text_from_pdf(temp_file_path)
                assert "Test invoice content" in text
        finally:
            os.unlink(temp_file_path)

    def test_ocr_processing(self):
        """Test OCR processing (mock)"""
        processor = DocumentProcessor()

        # Create a temporary image file for testing
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(b"PNG\nTest image content")
            temp_file_path = temp_file.name

        try:
            # Test OCR (this will fail without proper image content, but tests the method)
            with patch("pytesseract.image_to_string") as mock_ocr:
                mock_ocr.return_value = "Test OCR content"

                text = processor.perform_ocr(temp_file_path)
                assert "Test OCR content" in text
        finally:
            os.unlink(temp_file_path)

    def test_file_type_detection(self):
        """Test file type detection"""
        processor = DocumentProcessor()

        # Test PDF detection
        text, file_type = processor.extract_text_from_file("test.pdf")
        assert file_type == "pdf"

        # Test image detection
        with patch.object(processor, "perform_ocr") as mock_ocr:
            mock_ocr.return_value = "Test content"
            text, file_type = processor.extract_text_from_file("test.png")
            assert file_type == "image"

        # Test unsupported file type
        with pytest.raises(ValueError):
            processor.extract_text_from_file("test.txt")


if __name__ == "__main__":
    pytest.main([__file__])
