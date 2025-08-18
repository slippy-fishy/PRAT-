"""
Folder Monitoring API endpoints
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any
import time

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db_context
from app.services.po_folder_service import POFolderService
from app.config import settings
from app.services.pdf_extractor import PDFExtractor
from app.services.ai_analysis import AIAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global folder service instance
po_folder_service = POFolderService()
pdf_extractor = PDFExtractor()
ai_analysis_service = AIAnalysisService()

class FolderScanRequest(BaseModel):
    """Request model for scanning a custom folder"""
    folder_path: str

@router.get("/test-api")
async def test_api():
    """Simple test endpoint to verify API is working"""
    return {"message": "API is working correctly", "timestamp": "2024-01-01T00:00:00Z"}

@router.post("/echo-path")
async def echo_path(request: FolderScanRequest):
    """Echo back the path to debug path handling"""
    return {
        "received_path": request.folder_path,
        "path_type": type(request.folder_path).__name__,
        "path_length": len(request.folder_path) if request.folder_path else 0
    }

@router.post("/start-monitoring")
async def start_po_monitoring():
    """Start monitoring the PO folder for new files"""
    try:
        with get_db_context() as db:
            po_folder_service.start_monitoring(db, settings.po_folder_path)
        
        return {
            "message": "PO folder monitoring started",
            "folder_path": settings.po_folder_path,
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error starting PO monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/stop-monitoring")
async def stop_po_monitoring():
    """Stop monitoring the PO folder"""
    try:
        po_folder_service.stop_monitoring()
        
        return {
            "message": "PO folder monitoring stopped",
            "status": "inactive"
        }
        
    except Exception as e:
        logger.error(f"Error stopping PO monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.post("/scan-folder")
async def scan_po_folder(request: FolderScanRequest):
    """Manually scan a folder for files"""
    try:
        import os
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Received scan folder request for: {request.folder_path}")
        logger.info(f"Request object: {request}")
        
        folder_path = request.folder_path
        logger.info(f"Processing folder path: {folder_path}")
        
        # Resolve absolute path for debugging
        abs_path = os.path.abspath(folder_path)
        logger.info(f"Absolute path: {abs_path}")
        
        # Validate folder path
        if not os.path.exists(folder_path):
            logger.warning(f"Folder does not exist: {folder_path}")
            raise HTTPException(status_code=400, detail=f"Folder does not exist: {folder_path}")
        
        if not os.path.isdir(folder_path):
            logger.warning(f"Path is not a directory: {folder_path}")
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        logger.info(f"Scanning folder: {folder_path}")
        with get_db_context() as db:
            result = po_folder_service.scan_folder(db, folder_path)
        
        if "error" in result:
            logger.error(f"Error in scan result: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"Folder scan completed successfully for: {folder_path}")
        return {
            "message": f"Folder scan completed for: {folder_path}",
            "folder_path": folder_path,
            "scan_results": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning folder {request.folder_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan folder: {str(e)}")

@router.post("/batch-process")
async def batch_process_folder(request: FolderScanRequest):
    """Process all files in a folder in batch"""
    try:
        folder_path = request.folder_path
        
        # Validate folder path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail=f"Folder does not exist: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        # Use the service method for batch processing
        with get_db_context() as db:
            result = po_folder_service.batch_process_folder(db, folder_path)
            
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return {
                "message": f"Batch processing completed for folder: {folder_path}",
                "folder_path": folder_path,
                "total_files": result["total_files"],
                "processed_files": result["processed_files"],
                "errors": result["errors"],
                "summary": result["summary"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch processing folder {request.folder_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch process folder: {str(e)}")

@router.get("/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    try:
        status = po_folder_service.get_monitoring_status()
        
        return {
            "monitoring_status": status,
            "configured_folder": settings.po_folder_path,
            "folder_exists": os.path.exists(settings.po_folder_path),
            "folder_contents": _get_folder_contents(settings.po_folder_path)
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/create-folders")
async def create_monitoring_folders():
    """Create the monitoring folders if they don't exist"""
    try:
        folders_created = []
        
        for folder_path in [settings.po_folder_path, settings.invoice_folder_path, settings.processed_folder_path]:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                folders_created.append(folder_path)
                logger.info(f"Created folder: {folder_path}")
        
        return {
            "message": "Monitoring folders created",
            "folders_created": folders_created,
            "all_folders": {
                "po_folder": settings.po_folder_path,
                "invoice_folder": settings.invoice_folder_path,
                "processed_folder": settings.processed_folder_path
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating folders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create folders: {str(e)}")

@router.get("/folder-contents")
async def get_folder_contents():
    """Get contents of all monitoring folders"""
    try:
        contents = {}
        
        for folder_name, folder_path in [
            ("po_folder", settings.po_folder_path),
            ("invoice_folder", settings.invoice_folder_path),
            ("processed_folder", settings.processed_folder_path)
        ]:
            contents[folder_name] = _get_folder_contents(folder_path)
        
        return {
            "folder_contents": contents,
            "folder_paths": {
                "po_folder": settings.po_folder_path,
                "invoice_folder": settings.invoice_folder_path,
                "processed_folder": settings.processed_folder_path
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting folder contents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get folder contents: {str(e)}")

@router.post("/process-po-file")
async def process_po_file(
    file: UploadFile = File(..., description="PO file to process"),
):
    """
    Process an individual PO file and extract data using AI
    """
    try:
        logger.info(f"Processing individual PO file: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.pdf', '.txt', '.html', '.doc', '.docx']:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not allowed. Allowed types: .pdf, .txt, .html, .doc, .docx"
            )
        
        # Save uploaded file temporarily
        temp_dir = Path(settings.temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / f"{int(time.time())}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File saved to: {file_path}")
        
        try:
            # 1. Extract text from PDF using PDF extractor
            logger.info(f"Extracting text from PDF: {file_path}")
            extracted_text = pdf_extractor.extract_text_from_pdf(str(file_path))
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValueError("Failed to extract meaningful text from PDF")
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            
            # 2. Analyze extracted text using AI
            logger.info(f"Analyzing extracted text with AI...")
            po_data = ai_analysis_service.analyze_po_document(extracted_text)
            
            if not po_data:
                raise ValueError("AI analysis failed to return structured data")
            
            logger.info(f"AI analysis successful, extracted PO data: {po_data.get('po_number', 'Unknown')}")
            
            # Clean up temp file
            if file_path.exists():
                file_path.unlink()
            
            return {
                "filename": file.filename,
                "po_number": po_data.get("po_number"),
                "vendor_name": po_data.get("vendor_name"),
                "total_amount": po_data.get("total_authorized"),
                "po_date": po_data.get("po_date"),
                "delivery_date": po_data.get("delivery_date"),
                "currency": po_data.get("currency", "USD"),
                "status": po_data.get("status", "active"),
                "line_items": po_data.get("line_items", []),
                "processing_time": time.time(),
                "extraction_method": "pdf_extractor + ai_analysis"
            }
            
        except Exception as processing_error:
            logger.error(f"Error processing PO file {file.filename}: {processing_error}")
            
            # Clean up temp file
            if file_path.exists():
                file_path.unlink()
            
            # Provide specific error messages based on error type
            if "Failed to extract meaningful text" in str(processing_error):
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF text extraction failed: {str(processing_error)}"
                )
            elif "AI analysis failed" in str(processing_error):
                raise HTTPException(
                    status_code=500,
                    detail=f"AI analysis failed: {str(processing_error)}"
                )
            elif "OpenAI" in str(processing_error) or "quota" in str(processing_error).lower():
                raise HTTPException(
                    status_code=429,
                    detail="AI processing quota exceeded. Please try again later."
                )
            elif "insufficient_quota" in str(processing_error).lower():
                raise HTTPException(
                    status_code=429,
                    detail="OpenAI API quota exceeded. Please check your billing and try again."
                )
            else:
                # Generic error for unexpected issues
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process PO file: {str(processing_error)}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing PO file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def _get_folder_contents(folder_path: str) -> Dict[str, Any]:
    """Get contents of a specific folder"""
    try:
        if not os.path.exists(folder_path):
            return {
                "exists": False,
                "files": [],
                "total_files": 0,
                "total_size": 0
            }
        
        files = []
        total_size = 0
        
        for file_path in Path(folder_path).glob("*"):
            if file_path.is_file():
                file_stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": file_stat.st_size,
                    "modified": file_stat.st_mtime,
                    "extension": file_path.suffix.lower()
                })
                total_size += file_stat.st_size
        
        return {
            "exists": True,
            "files": files,
            "total_files": len(files),
            "total_size": total_size
        }
        
    except Exception as e:
        logger.error(f"Error getting contents of {folder_path}: {e}")
        return {
            "exists": False,
            "error": str(e),
            "files": [],
            "total_files": 0,
            "total_size": 0
        }
