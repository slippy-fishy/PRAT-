#!/usr/bin/env python3
"""
Database initialization script for PRAT
"""
import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def create_directories():
    """Create necessary directories"""
    try:
        # Create upload directory
        os.makedirs(settings.upload_dir, exist_ok=True)
        logger.info(f"Created upload directory: {settings.upload_dir}")
        
        # Create logs directory
        log_dir = Path(settings.log_file).parent
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f"Created logs directory: {log_dir}")
        
        # Create other necessary directories
        directories = [
            "sample_data",
            "temp",
            "exports"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        raise


def validate_configuration():
    """Validate application configuration"""
    try:
        logger.info("Validating configuration...")
        
        # Check required settings
        required_settings = [
            'openai_api_key',
            'secret_key',
            'database_url'
        ]
        
        for setting in required_settings:
            if not getattr(settings, setting, None):
                logger.warning(f"Missing required setting: {setting}")
        
        # Check file permissions
        test_file = os.path.join(settings.upload_dir, "test.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logger.info("File permissions test passed")
        except Exception as e:
            logger.error(f"File permissions test failed: {e}")
            raise
        
        logger.info("Configuration validation completed")
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def create_sample_data():
    """Create sample data files"""
    try:
        logger.info("Creating sample data...")
        
        # Create sample invoice text
        sample_invoice_text = """
INVOICE

Invoice Number: INV-2024-001
Date: 2024-01-15
Due Date: 2024-02-15

Vendor: ABC Supplies Inc.
Vendor ID: VEND-001

Line Items:
1. Office Chairs - Qty: 10 - Unit Price: $150.00 - Total: $1,500.00
2. Desk Lamps - Qty: 20 - Unit Price: $50.00 - Total: $1,000.00

Subtotal: $2,500.00
Tax: $250.00
Total: $2,750.00

Payment Terms: Net 30
PO Reference: PO-2024-001
        """
        
        sample_file = "sample_data/sample_invoice.txt"
        with open(sample_file, 'w') as f:
            f.write(sample_invoice_text)
        
        logger.info(f"Created sample invoice: {sample_file}")
        
        # Create README for sample data
        readme_content = """
# Sample Data

This directory contains sample data for testing the PRAT application.

## Files:
- sample_invoice.txt: Sample invoice text for testing document processing

## Usage:
You can use these files to test the invoice processing functionality.
        """
        
        with open("sample_data/README.md", 'w') as f:
            f.write(readme_content)
        
        logger.info("Created sample data README")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        raise


def main():
    """Main initialization function"""
    try:
        logger.info("Starting PRAT database initialization...")
        
        # Create directories
        create_directories()
        
        # Validate configuration
        validate_configuration()
        
        # Create sample data
        create_sample_data()
        
        logger.info("PRAT initialization completed successfully!")
        logger.info("You can now start the application with: uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 