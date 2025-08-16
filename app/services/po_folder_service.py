"""
Purchase Order Folder Monitoring Service
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session

from app.core.document_processor import DocumentProcessor
from app.models.database_models import PurchaseOrderDB, POLineItemDB

logger = logging.getLogger(__name__)

class POFolderHandler(FileSystemEventHandler):
    """File system event handler for PO folder monitoring"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.document_processor = DocumentProcessor()
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self._is_po_file(event.src_path):
            logger.info(f"New PO file detected: {event.src_path}")
            self.process_po_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self._is_po_file(event.src_path):
            logger.info(f"PO file modified: {event.src_path}")
            self.process_po_file(event.src_path)
    
    def _is_po_file(self, file_path: str) -> bool:
        """Check if file is a PO document"""
        return file_path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))
    
    def process_po_file(self, file_path: str):
        """Process a single PO file and store in database"""
        try:
            # Generate file hash to detect changes
            file_hash = self._get_file_hash(file_path)
            
            # Check if already processed
            existing_po = self.db_session.query(PurchaseOrderDB)\
                .filter_by(file_path=file_path, file_hash=file_hash).first()
            
            if existing_po:
                logger.info(f"File already processed (no changes): {file_path}")
                return  # Already processed, no changes
            
            # Extract text from file first
            extracted_text = self.document_processor.extract_text_from_file(file_path)[0]
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.warning(f"Could not extract meaningful text from: {file_path}")
                return
            
            # Extract data using AI/OCR
            po_data = self.document_processor.extract_po_data(extracted_text)
            
            # Store/update in database
            self._store_po_data(po_data, file_path, file_hash)
            
        except Exception as e:
            logger.error(f"Error processing PO file {file_path}: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.sha256(file_content).hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash for {file_path}: {e}")
            return ""
    
    def _store_po_data(self, po_data: dict, file_path: str, file_hash: str):
        """Store extracted PO data in database"""
        try:
            import uuid
            
            # Create PO record
            po = PurchaseOrderDB(
                id=uuid.uuid4(),  # Explicitly set the ID
                po_number=po_data['po_number'],
                vendor_name=po_data['vendor_name'],
                vendor_id=po_data.get('vendor_id'),
                total_amount=po_data.get('total_authorized', 0),  # LLM returns 'total_authorized'
                po_date=po_data.get('po_date'),
                file_path=file_path,
                file_hash=file_hash
            )
            
            # Add and commit PO first
            self.db_session.add(po)
            self.db_session.commit()
            
            # Now add line items
            for i, item_data in enumerate(po_data.get('line_items', [])):
                line_item = POLineItemDB(
                    po_id=po.id,
                    line_number=i + 1,
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_amount=item_data.get('total_price', 0),  # LLM returns 'total_price'
                    product_code=item_data.get('sku'),  # Map SKU to product_code
                    category=item_data.get('part_number')  # Map part_number to category
                )
                self.db_session.add(line_item)
            
            # Commit line items
            self.db_session.commit()
            logger.info(f"Successfully stored PO {po.po_number} in database")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error storing PO data: {e}")
            raise

class POFolderService:
    """Service for managing PO folder monitoring"""
    
    def __init__(self):
        self.observer = None
        self.handler = None
        self.is_monitoring = False
    
    def start_monitoring(self, db_session: Session, folder_path: str):
        """Start monitoring a folder for PO files"""
        try:
            if self.is_monitoring:
                logger.warning("Folder monitoring is already active")
                return
            
            if not os.path.exists(folder_path):
                logger.error(f"PO folder does not exist: {folder_path}")
                return
            
            # Create handler
            self.handler = POFolderHandler(db_session)
            
            # Create observer
            self.observer = Observer()
            self.observer.schedule(self.handler, folder_path, recursive=False)
            
            # Start monitoring
            self.observer.start()
            self.is_monitoring = True
            
            logger.info(f"Started monitoring PO folder: {folder_path}")
            
        except Exception as e:
            logger.error(f"Error starting folder monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop folder monitoring"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self.is_monitoring = False
            logger.info("Stopped PO folder monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping folder monitoring: {e}")
    
    def scan_folder(self, db_session: Session, folder_path: str) -> Dict[str, Any]:
        """Manually scan folder for PO files"""
        try:
            if not os.path.exists(folder_path):
                return {"error": f"Folder does not exist: {folder_path}"}
            
            # Create temporary handler for scanning
            handler = POFolderHandler(db_session)
            
            # Get all files in folder
            po_files = []
            processed_count = 0
            error_count = 0
            
            for file_path in Path(folder_path).glob("*"):
                if file_path.is_file() and handler._is_po_file(str(file_path)):
                    po_files.append(str(file_path))
                    
                    try:
                        handler.process_po_file(str(file_path))
                        processed_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing {file_path}: {e}")
            
            return {
                "folder_path": folder_path,
                "total_files": len(po_files),
                "processed_count": processed_count,
                "error_count": error_count,
                "files": po_files
            }
            
        except Exception as e:
            logger.error(f"Error scanning folder: {e}")
            return {"error": str(e)}
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "folder_path": getattr(self.handler, 'folder_path', None) if self.handler else None
        }
