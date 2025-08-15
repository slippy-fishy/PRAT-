"""
Document processing module for extracting data from invoices
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import time
from datetime import datetime

import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.models.invoice import Invoice, InvoiceLineItem
from app.models.purchase_order import PurchaseOrder, POLineItem
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Document processor for extracting data from various file types"""
    
    def __init__(self):
        """Initialize the document processor"""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
        
        # Set Tesseract command if specified
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
            with open(file_path, 'rb') as file:
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
            
            # Open and process the image
            image = Image.open(image_path)
            
            # Perform OCR
            text_content = pytesseract.image_to_string(image)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"OCR completed in {processing_time:.2f}ms")
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR on {image_path}: {e}")
            raise
    
    def extract_text_from_file(self, file_path: str) -> Tuple[str, str]:
        """Extract text from file based on file type"""
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(str(file_path))
            return text, 'pdf'
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif']:
            text = self.perform_ocr(str(file_path))
            return text, 'image'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def create_extraction_prompt(self, invoice_text: str) -> str:
        """Create prompt for LLM to extract invoice data"""
        prompt = f"""
You are an expert data extraction system. You have been given the TEXT CONTENT from an invoice document.

Here is the extracted text from the invoice:

{invoice_text}

Your task is to extract the structured data from this text and return ONLY valid JSON.

IMPORTANT: 
- This is the actual document text, not a request to access files
- Respond with ONLY the JSON data, no explanations
- Do not include markdown formatting or code blocks
- The response must be parseable JSON

Extract and return this exact JSON structure:
{{
    "invoice_number": "string",
    "vendor_name": "string", 
    "vendor_id": "string or null",
    "invoice_date": "YYYY-MM-DD",
    "due_date": "YYYY-MM-DD",
    "total_amount": "decimal",
    "tax_amount": "decimal",
    "subtotal_amount": "decimal",
    "currency": "string (default: USD)",
    "line_items": [
        {{
            "description": "string",
            "quantity": "integer",
            "unit_price": "decimal",
            "total_price": "decimal",
            "sku": "string or null",
            "po_reference": "string or null"
        }}
    ],
    "po_reference": "string or null",
    "contract_reference": "string or null",
    "payment_terms": "string or null",
    "shipping_address": "string or null",
    "billing_address": "string or null",
    "notes": "string or null"
}}

Rules:
- All monetary values must be decimal numbers (not strings)
- Dates must be in YYYY-MM-DD format
- Quantities must be integers
- If a field is not found, use null
- Return ONLY the JSON object, nothing else
"""
        return prompt
    
    def create_po_extraction_prompt(self, po_text: str) -> str:
        """Create prompt for LLM to extract purchase order data"""
        prompt = f"""
You are an expert data extraction system. You have been given the TEXT CONTENT from a purchase order document.

Here is the extracted text from the purchase order:

{po_text}

Your task is to extract the structured data from this text and return ONLY valid JSON.

IMPORTANT: 
- This is the actual document text, not a request to access files
- Respond with ONLY the JSON data, no explanations
- Do not include markdown formatting or code blocks
- The response must be parseable JSON

Extract and return this exact JSON structure:
{{
    "po_number": "string",
    "vendor_name": "string",
    "vendor_id": "string or null",
    "po_date": "YYYY-MM-DD",
    "total_authorized": "decimal",
    "currency": "string (default: USD)",
    "line_items": [
        {{
            "description": "string",
            "quantity": "integer",
            "unit_price": "decimal",
            "total_price": "decimal",
            "sku": "string or null",
            "part_number": "string or null",
            "delivery_date": "YYYY-MM-DD or null"
        }}
    ],
    "contract_reference": "string or null",
    "payment_terms": "string or null",
    "delivery_address": "string or null",
    "billing_address": "string or null",
    "notes": "string or null",
    "status": "string (default: OPEN)",
    "approved_by": "string or null",
    "approved_date": "YYYY-MM-DD or null"
}}

Rules:
- All monetary values must be decimal numbers (not strings)
- Dates must be in YYYY-MM-DD format
- Quantities must be integers
- If a field is not found, use null
- Return ONLY the JSON object, nothing else
"""
        return prompt
    
    def extract_invoice_data(self, text: str) -> Invoice:
        """Extract structured invoice data from text using LLM"""
        try:
            logger.info("Extracting invoice data using LLM")
            start_time = time.time()
            
            prompt = self.create_extraction_prompt(text)
            
            # Get LLM response with system message
            messages = [
                SystemMessage(content="You are a data extraction system. You must respond with ONLY valid JSON. No explanations, no markdown, just JSON."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            logger.info(f"LLM Response received: {len(response_text)} characters")
            logger.debug(f"LLM Response content: {response_text[:500]}...")
            
            # Check if response is empty
            if not response_text:
                raise ValueError("LLM returned empty response")
            
            # Parse JSON response
            import json
            try:
                # Try to extract JSON if response contains extra text
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif response_text.startswith('```'):
                    response_text = response_text.split('```')[1].split('```')[0]
                
                # Clean up the response text
                response_text = response_text.strip()
                
                # Try to parse as JSON
                po_data = json.loads(response_text)
                
                # Convert to Invoice object
                invoice = Invoice(**po_data)
                
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"Invoice data extraction completed in {processing_time:.2f}ms")
                
                return invoice
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response text: {response_text}")
                logger.error(f"Response length: {len(response_text)}")
                
                # Try to find any JSON-like content
                import re
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        logger.info(f"Found JSON-like content: {json_content[:200]}...")
                        po_data = json.loads(json_content)
                        invoice = Invoice(**po_data)
                        return invoice
                    except json.JSONDecodeError:
                        pass
                
                raise ValueError(f"LLM response could not be parsed as JSON: {e}")
                
        except Exception as e:
            logger.error(f"Error extracting invoice data: {e}")
            raise
    
    def extract_po_data(self, text: str) -> Dict[str, Any]:
        """Extract structured purchase order data from text using LLM"""
        try:
            logger.info("Extracting PO data using LLM")
            logger.info(f"Input text length: {len(text)} characters")
            logger.info(f"Input text preview: {text[:500]}...")
            start_time = time.time()
            
            prompt = self.create_po_extraction_prompt(text)
            
            # Get LLM response with system message
            messages = [
                SystemMessage(content="You are a data extraction system. You must respond with ONLY valid JSON. No explanations, no markdown, just JSON."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            logger.info(f"LLM Response received: {len(response_text)} characters")
            logger.debug(f"LLM Response content: {response_text[:500]}...")
            
            # Check if response is empty
            if not response_text:
                raise ValueError("LLM returned empty response")
            
            # Parse JSON response
            import json
            try:
                # Try to extract JSON if response contains extra text
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif response_text.startswith('```'):
                    response_text = response_text.split('```')[1].split('```')[0]
                
                # Clean up the response text
                response_text = response_text.strip()
                
                # Try to parse as JSON
                po_data = json.loads(response_text)
                
                logger.info(f"Successfully parsed PO data: {po_data}")
                
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"PO data extraction completed in {processing_time:.2f}ms")
                
                return po_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response text: {response_text}")
                logger.error(f"Response length: {len(response_text)}")
                
                # Try to find any JSON-like content
                import re
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        logger.info(f"Found JSON-like content: {json_content[:200]}...")
                        po_data = json.loads(json_content)
                        return po_data
                    except json.JSONDecodeError:
                        pass
                
                raise ValueError(f"LLM response could not be parsed as JSON: {e}")
                
        except Exception as e:
            logger.error(f"Error extracting PO data: {e}")
            raise
    
    def process_invoice_file(self, file_path: str) -> Invoice:
        """Process an invoice file and extract data"""
        try:
            logger.info(f"Processing invoice file: {file_path}")
            start_time = time.time()
            
            # Extract text from file
            text, file_type = self.extract_text_from_file(file_path)
            
            # Extract structured data
            invoice = self.extract_invoice_data(text)
            
            # Add metadata
            invoice.file_path = file_path
            invoice.extracted_at = datetime.now()
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Invoice processing completed in {processing_time:.2f}ms")
            
            return invoice
            
        except Exception as e:
            logger.error(f"Error processing invoice file {file_path}: {e}")
            raise
