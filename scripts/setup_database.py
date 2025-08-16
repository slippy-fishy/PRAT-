#!/usr/bin/env python3
"""
Database setup script for PRAT system
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_database():
    """Set up the database and create tables"""
    try:
        print("🔧 Setting up PRAT database...")
        
        # Import database components
        from app.core.database import init_database, create_tables
        from app.config import settings
        
        print(f"📁 Database URL: {settings.database_url}")
        print(f"📁 PO Folder: {settings.po_folder_path}")
        print(f"📁 Invoice Folder: {settings.invoice_folder_path}")
        print(f"📁 Processed Folder: {settings.processed_folder_path}")
        
        # Initialize database
        print("\n🔄 Initializing database...")
        init_database()
        
        # Create tables
        print("📋 Creating database tables...")
        create_tables()
        
        # Create monitoring folders
        print("📁 Creating monitoring folders...")
        for folder_path in [settings.po_folder_path, settings.invoice_folder_path, settings.processed_folder_path]:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"   ✅ Created: {folder_path}")
            else:
                print(f"   ℹ️  Exists: {folder_path}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Place your PO PDFs in the 'purchase_orders' folder")
        print("   2. Start the server: make run")
        print("   3. Go to: http://localhost:8000/docs")
        print("   4. Use the folder monitoring endpoints to process POs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        print("\n🔍 Troubleshooting:")
        print("   - Check your .env file configuration")
        print("   - Ensure PostgreSQL is running (if using PostgreSQL)")
        print("   - Check database connection settings")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        print("\n📊 Creating sample data...")
        
        # Import services
        from app.services.po_folder_service import POFolderService
        from app.core.database import get_db_context
        
        # Create folder service
        po_service = POFolderService()
        
        # Scan for existing files
        with get_db_context() as db:
            result = po_service.scan_folder(db, "sample_data")
            
            if "error" not in result:
                print(f"   ✅ Processed {result['processed_count']} files")
                print(f"   📁 Total files found: {result['total_files']}")
            else:
                print(f"   ⚠️  Scan result: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Sample data creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PRAT Database Setup")
    print("=" * 50)
    
    # Setup database
    if setup_database():
        # Try to create sample data
        create_sample_data()
        
        print("\n✅ Setup completed! You can now start using PRAT.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
