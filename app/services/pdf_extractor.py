"""
PDF Text Extraction Service
Extracts actual text content from PDF files using multiple methods
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import time

import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Service for extracting text content from PDF files"""
    
    def __init__(self):
        """Initialize the PDF extractor"""
        # Set Tesseract command if available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available")
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file using multiple methods"""
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            start_time = time.time()
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Method 1: Try pdfplumber first (better for structured documents)
            text_content = self._extract_with_pdfplumber(file_path)
            if text_content and len(text_content.strip()) > 10:
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"Successfully extracted text using pdfplumber in {processing_time:.2f}ms")
                return text_content.strip()
            
            # Method 2: Fallback to PyPDF2
            text_content = self._extract_with_pypdf2(file_path)
            if text_content and len(text_content.strip()) > 10:
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"Successfully extracted text using PyPDF2 in {processing_time:.2f}ms")
                return text_content.strip()
            
            # Method 3: Try OCR if text extraction failed
            text_content = self._extract_with_ocr(file_path)
            if text_content and len(text_content.strip()) > 10:
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"Successfully extracted text using OCR in {processing_time:.2f}ms")
                return text_content.strip()
            
            # If all methods failed
            raise ValueError("Could not extract meaningful text from PDF using any method")
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def _extract_with_pdfplumber(self, file_path: str) -> Optional[str]:
        """Extract text using pdfplumber (best for structured documents)"""
        try:
            text_content = ""
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            
            return text_content if text_content.strip() else None
            
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None
    
    def _extract_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            
            return text_content if text_content.strip() else None
            
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return None
    
    def _extract_with_ocr(self, file_path: str) -> Optional[str]:
        """Extract text using OCR (for scanned PDFs)"""
        try:
            # Convert PDF pages to images and perform OCR
            text_content = ""
            
            # For now, we'll use a simplified approach
            # In production, you might want to use pdf2image to convert PDF to images
            logger.info("OCR extraction attempted (simplified implementation)")
            
            # This is a placeholder - in a real implementation you'd convert PDF to images
            # and perform OCR on each image
            return None
            
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> dict:
        """Get basic information about the PDF file"""
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # Try to get page count
            page_count = 0
            try:
                with pdfplumber.open(file_path) as pdf:
                    page_count = len(pdf.pages)
            except:
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                except:
                    pass
            
            return {
                "file_path": file_path,
                "file_size": file_size,
                "file_size_kb": round(file_size / 1024, 2),
                "page_count": page_count,
                "extraction_method": "pdfplumber/pypdf2/ocr"
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
