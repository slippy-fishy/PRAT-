#!/usr/bin/env python3
"""
Demo script for PRAT batch processing functionality
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

async def demo_batch_processing():
    """Demonstrate the batch processing functionality"""
    
    base_url = "http://localhost:8000"
    
    print("PRAT Batch Processing Demo")
    print("=" * 50)
    print()
    
    # Check if the application is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code != 200:
                print("❌ Application is not responding properly")
                return
    except httpx.ConnectError:
        print("❌ Cannot connect to PRAT application")
        print("   Make sure the application is running on http://localhost:8000")
        print("   Run: python start_app.py")
        return
    
    print("✅ Connected to PRAT application")
    print()
    
    # Demo 1: Create required folders
    print("1. Creating required folders...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/api/v1/folder-monitoring/create-folders")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Folders created: {result.get('folders_created', [])}")
            else:
                print(f"   ⚠️  Folder creation response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error creating folders: {e}")
    
    print()
    
    # Demo 2: Get system status
    print("2. Getting system status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/folder-monitoring/status")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Monitoring status: {result.get('monitoring_status', 'Unknown')}")
                print(f"   ✅ Configured PO folder: {result.get('configured_folder', 'Unknown')}")
            else:
                print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting status: {e}")
    
    print()
    
    # Demo 3: Scan sample data folder
    print("3. Scanning sample data folder...")
    sample_folder = os.path.join(os.path.dirname(__file__), "sample_data")
    
    if not os.path.exists(sample_folder):
        print(f"   ❌ Sample data folder not found: {sample_folder}")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v1/folder-monitoring/scan-folder",
                json={"folder_path": sample_folder}
            )
            
            if response.status_code == 200:
                result = response.json()
                files = result.get('scan_results', {}).get('files', [])
                print(f"   ✅ Found {len(files)} files in sample data folder")
                
                # Show file details
                for file in files:
                    status_icon = "📄" if file['extension'] == '.pdf' else "📁"
                    print(f"      {status_icon} {file['name']} ({file['extension']}) - {file['size']} bytes")
            else:
                print(f"   ❌ Folder scan failed: {response.status_code}")
                print(f"      Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error scanning folder: {e}")
    
    print()
    
    # Demo 4: Batch process sample data
    print("4. Batch processing sample data...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v1/folder-monitoring/batch-process",
                json={"folder_path": sample_folder}
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('summary', {})
                
                print(f"   ✅ Batch processing completed!")
                print(f"      📊 Summary: {summary.get('successful', 0)} successful, "
                      f"{summary.get('failed', 0)} failed, {summary.get('skipped', 0)} skipped")
                
                # Show processing results
                if result.get('processed_files'):
                    print("      📋 Successfully processed:")
                    for file in result['processed_files']:
                        print(f"         ✅ {file['name']} - PO: {file.get('po_number', 'N/A')}")
                
                if result.get('errors'):
                    print("      ⚠️  Errors/Skipped:")
                    for file in result['errors']:
                        icon = "⚠️" if file['status'] == 'skipped' else "❌"
                        print(f"         {icon} {file['name']} - {file.get('error', 'No error details')}")
            else:
                print(f"   ❌ Batch processing failed: {response.status_code}")
                print(f"      Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error during batch processing: {e}")
    
    print()
    
    # Demo 5: Show web interface info
    print("5. Web Interface Information")
    print("   🌐 Open your browser and navigate to: http://localhost:8000")
    print("   📚 API documentation available at: http://localhost:8000/docs")
    print("   🔍 Use the web interface to:")
    print("      - Select different folders for processing")
    print("      - Monitor processing progress in real-time")
    print("      - View detailed results and statistics")
    print("      - Start/stop folder monitoring")
    
    print()
    print("=" * 50)
    print("Demo completed! 🎉")
    print()
    print("Next steps:")
    print("1. Try the web interface at http://localhost:8000")
    print("2. Test with your own PO folders")
    print("3. Check the API documentation for more details")
    print("4. Run the test script: python test_batch_processing.py")

def main():
    """Main function"""
    try:
        asyncio.run(demo_batch_processing())
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()
