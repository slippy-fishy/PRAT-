"""
Document processing module for extracting data from invoices
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path
import time

import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.models.invoice import Invoice, InvoiceLineItem
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing and data extraction from invoices"""

    def __init__(self):
        """Initialize the document processor"""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            openai_api_key=settings.openai_api_key,
        )

        # Configure tesseract if path is provided
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF invoice"""
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            start_time = time.time()

            text_content = ""

            # Try pdfplumber first (better for structured documents)
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"

                if text_content.strip():
                    logger.info(f"Successfully extracted text using pdfplumber")
                    return text_content.strip()

            except Exception as e:
                logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")

            # Fallback to PyPDF2
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"PDF text extraction completed in {processing_time:.2f}ms")

            return text_content.strip()

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise

    def perform_ocr(self, image_path: str) -> str:
        """Convert image to text using OCR"""
        try:
            logger.info(f"Performing OCR on image: {image_path}")
            start_time = time.time()

            # Open image
            image = Image.open(image_path)

            # Perform OCR
            text = pytesseract.image_to_string(image)

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"OCR completed in {processing_time:.2f}ms")

            return text.strip()

        except Exception as e:
            logger.error(f"Error performing OCR on {image_path}: {e}")
            raise

    def extract_text_from_file(self, file_path: str) -> Tuple[str, str]:
        """Extract text from file based on its type"""
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()

        if file_extension == ".pdf":
            text = self.extract_text_from_pdf(str(file_path))
            return text, "pdf"
        elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]:
            text = self.perform_ocr(str(file_path))
            return text, "image"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def create_extraction_prompt(self, invoice_text: str) -> str:
        """Generate prompt for LLM to extract invoice data"""
        return f"""
You are an expert invoice data extraction system. Extract structured data from the following invoice text and return it as a JSON object.

INVOICE TEXT:
{invoice_text}

Please extract the following information and return as JSON:
{{
    "invoice_number": "string",
    "vendor_name": "string", 
    "vendor_id": "string or null",
    "invoice_date": "YYYY-MM-DD",
    "due_date": "YYYY-MM-DD",
    "total_amount": "decimal",
    "tax_amount": "decimal",
    "subtotal_amount": "decimal",
    "currency": "string (default USD)",
    "po_reference": "string or null",
    "contract_reference": "string or null",
    "payment_terms": "string or null",
    "shipping_address": "string or null",
    "billing_address": "string or null",
    "notes": "string or null",
    "line_items": [
        {{
            "description": "string",
            "quantity": "integer",
            "unit_price": "decimal",
            "total_price": "decimal",
            "sku": "string or null",
            "po_reference": "string or null"
        }}
    ]
}}

Important:
- All amounts should be decimal numbers (e.g., 1234.56)
- Dates should be in YYYY-MM-DD format
- If a field is not found, use null
- Ensure line item totals match quantity * unit_price
- Ensure invoice total matches subtotal + tax
- Be as accurate as possible with the extraction
"""

    def extract_invoice_data(self, text: str) -> Invoice:
        """Use LLM to extract structured data from invoice text"""
        try:
            logger.info("Extracting structured invoice data using LLM")
            start_time = time.time()

            # Create extraction prompt
            prompt = self.create_extraction_prompt(text)

            # Get LLM response
            messages = [
                SystemMessage(
                    content="You are an expert invoice data extraction system. Always respond with valid JSON."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)

            # Parse JSON response
            import json

            try:
                # Extract JSON from response (handle markdown formatting)
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]

                data = json.loads(content.strip())

                # Add processing metadata
                data["extracted_at"] = time.time()
                data["confidence_score"] = (
                    0.85  # Placeholder - could be calculated based on LLM confidence
                )

                # Create Invoice object
                invoice = Invoice(**data)

                processing_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Invoice data extraction completed in {processing_time:.2f}ms"
                )

                return invoice

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response content: {response.content}")
                raise ValueError(f"Invalid JSON response from LLM: {e}")

        except Exception as e:
            logger.error(f"Error extracting invoice data: {e}")
            raise

    def process_invoice_file(self, file_path: str) -> Invoice:
        """Complete invoice processing pipeline"""
        try:
            logger.info(f"Processing invoice file: {file_path}")
            start_time = time.time()

            # Extract text from file
            text, file_type = self.extract_text_from_file(file_path)

            if not text.strip():
                raise ValueError("No text content extracted from file")

            # Extract structured data
            invoice = self.extract_invoice_data(text)

            # Add file metadata
            invoice.file_path = file_path

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Invoice processing completed in {processing_time:.2f}ms")

            return invoice

        except Exception as e:
            logger.error(f"Error processing invoice file {file_path}: {e}")
            raise
