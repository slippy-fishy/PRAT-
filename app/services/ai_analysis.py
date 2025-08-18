"""
AI Analysis Service
Uses OpenAI API to analyze extracted text and extract structured data
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """Service for AI-powered document analysis"""
    
    def __init__(self):
        """Initialize the AI analysis service"""
        try:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key
            )
            logger.info(f"AI Analysis Service initialized with model: {settings.llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize AI Analysis Service: {e}")
            raise
    
    def analyze_po_document(self, extracted_text: str) -> Dict[str, Any]:
        """Analyze PO document text using AI and return structured data"""
        try:
            logger.info("Starting AI analysis of PO document")
            start_time = time.time()
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValueError("Insufficient text content for AI analysis")
            
            # Create the analysis prompt
            prompt = self._create_po_analysis_prompt(extracted_text)
            
            # Send to OpenAI
            messages = [
                SystemMessage(content="You are an expert data extraction system. You must respond with ONLY valid JSON. No explanations, no markdown, just JSON."),
                HumanMessage(content=prompt)
            ]
            
            logger.info("Sending PO document to OpenAI for analysis...")
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            if not response_text:
                raise ValueError("OpenAI returned empty response")
            
            logger.info(f"OpenAI response received: {len(response_text)} characters")
            
            # Parse the JSON response
            structured_data = self._parse_ai_response(response_text)
            
            # Validate the extracted data
            validated_data = self._validate_po_data(structured_data)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"AI analysis completed in {processing_time:.2f}ms")
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Error in AI analysis of PO document: {e}")
            raise
    
    def analyze_invoice_document(self, extracted_text: str) -> Dict[str, Any]:
        """Analyze invoice document text using AI and return structured data"""
        try:
            logger.info("Starting AI analysis of invoice document")
            start_time = time.time()
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValueError("Insufficient text content for AI analysis")
            
            # Create the analysis prompt
            prompt = self._create_invoice_analysis_prompt(extracted_text)
            
            # Send to OpenAI
            messages = [
                SystemMessage(content="You are an expert data extraction system. You must respond with ONLY valid JSON. No explanations, no markdown, just JSON."),
                HumanMessage(content=prompt)
            ]
            
            logger.info("Sending invoice document to OpenAI for analysis...")
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            if not response_text:
                raise ValueError("OpenAI returned empty response")
            
            logger.info(f"OpenAI response received: {len(response_text)} characters")
            
            # Parse the JSON response
            structured_data = self._parse_ai_response(response_text)
            
            # Validate the extracted data
            validated_data = self._validate_invoice_data(structured_data)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"AI analysis completed in {processing_time:.2f}ms")
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Error in AI analysis of invoice document: {e}")
            raise
    
    def _create_po_analysis_prompt(self, po_text: str) -> str:
        """Create prompt for PO document analysis"""
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
    "delivery_date": "YYYY-MM-DD or null",
    "total_authorized": "decimal",
    "currency": "string (default: USD)",
    "line_items": [
        {{
            "description": "string",
            "quantity": "integer",
            "unit_price": "decimal",
            "total_price": "decimal",
            "sku": "string or null",
            "part_number": "string or null"
        }}
    ],
    "status": "string (default: active)",
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
    
    def _create_invoice_analysis_prompt(self, invoice_text: str) -> str:
        """Create prompt for invoice document analysis"""
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
    "due_date": "YYYY-MM-DD or null",
    "total_amount": "decimal",
    "tax_amount": "decimal or null",
    "subtotal_amount": "decimal or null",
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
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response and extract JSON data"""
        try:
            # Clean up the response text
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.split('```json')[1].split('```')[0]
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.split('```')[1].split('```')[0]
            
            cleaned_text = cleaned_text.strip()
            
            # Try to parse as JSON
            try:
                data = json.loads(cleaned_text)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response text: {cleaned_text}")
                
                # Try to find JSON-like content using regex
                import re
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, cleaned_text, re.DOTALL)
                
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        logger.info(f"Found JSON-like content, attempting to parse")
                        data = json.loads(json_content)
                        return data
                    except json.JSONDecodeError:
                        pass
                
                raise ValueError(f"AI response could not be parsed as JSON: {e}")
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
    
    def _validate_po_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean PO data"""
        # Ensure required fields exist
        required_fields = ['po_number', 'vendor_name', 'total_authorized']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults for optional fields
        data.setdefault('currency', 'USD')
        data.setdefault('status', 'active')
        data.setdefault('line_items', [])
        
        return data
    
    def _validate_invoice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean invoice data"""
        # Ensure required fields exist
        required_fields = ['invoice_number', 'vendor_name', 'total_amount']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults for optional fields
        data.setdefault('currency', 'USD')
        data.setdefault('line_items', [])
        
        return data
