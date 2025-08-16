"""
Folder Monitoring API endpoints
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_context
from app.services.po_folder_service import POFolderService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global folder service instance
po_folder_service = POFolderService()

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
async def scan_po_folder():
    """Manually scan the PO folder for files"""
    try:
        with get_db_context() as db:
            result = po_folder_service.scan_folder(db, settings.po_folder_path)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "PO folder scan completed",
            "scan_results": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning PO folder: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan folder: {str(e)}")

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
