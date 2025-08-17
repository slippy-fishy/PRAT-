#!/usr/bin/env python3
"""
Test script for the new batch processing functionality
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_batch_processing():
    """Test the batch processing functionality"""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test folder path (using sample data)
    test_folder = os.path.join(os.path.dirname(__file__), "sample_data")
    
    print(f"Testing batch processing with folder: {test_folder}")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Scan folder
            print("1. Testing folder scan...")
            scan_response = await client.post(
                f"{base_url}/api/v1/folder-monitoring/scan-folder",
                json={"folder_path": test_folder}
            )
            
            if scan_response.status_code == 200:
                scan_result = scan_response.json()
                print(f"   ✓ Folder scan successful")
                print(f"   ✓ Found {len(scan_result.get('scan_results', {}).get('files', []))} files")
                
                # Display found files
                files = scan_result.get('scan_results', {}).get('files', [])
                for file in files:
                    print(f"      - {file['name']} ({file['extension']}) - {file['size']} bytes")
            else:
                print(f"   ✗ Folder scan failed: {scan_response.status_code}")
                print(f"   Error: {scan_response.text}")
                return
            
            print()
            
            # Test 2: Batch process folder
            print("2. Testing batch processing...")
            batch_response = await client.post(
                f"{base_url}/api/v1/folder-monitoring/batch-process",
                json={"folder_path": test_folder}
            )
            
            if batch_response.status_code == 200:
                batch_result = batch_response.json()
                print(f"   ✓ Batch processing successful")
                print(f"   ✓ Summary: {batch_result['summary']}")
                
                # Display processing results
                if batch_result.get('processed_files'):
                    print("   Processed files:")
                    for file in batch_result['processed_files']:
                        print(f"      ✓ {file['name']} - PO: {file.get('po_number', 'N/A')}")
                
                if batch_result.get('errors'):
                    print("   Errors/Skipped:")
                    for file in batch_result['errors']:
                        status = file['status']
                        error = file.get('error', 'No error details')
                        print(f"      {'⚠' if status == 'skipped' else '✗'} {file['name']} - {error}")
            else:
                print(f"   ✗ Batch processing failed: {batch_response.status_code}")
                print(f"   Error: {batch_response.text}")
                return
            
            print()
            print("3. Testing system status...")
            
            # Test 3: Get system status
            status_response = await client.get(f"{base_url}/api/v1/folder-monitoring/status")
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"   ✓ System status retrieved")
                print(f"   ✓ Monitoring status: {status_result.get('monitoring_status', 'Unknown')}")
                print(f"   ✓ Configured folder: {status_result.get('configured_folder', 'Unknown')}")
            else:
                print(f"   ✗ Status check failed: {status_response.status_code}")
                print(f"   Error: {status_response.text}")
            
            print()
            print("=" * 60)
            print("All tests completed!")
            
        except httpx.ConnectError:
            print("✗ Could not connect to the server. Make sure the PRAT application is running on http://localhost:8000")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")

def main():
    """Main function"""
    print("PRAT Batch Processing Test")
    print("This script tests the new batch processing functionality")
    print()
    
    # Check if the app is running
    try:
        import httpx
        asyncio.run(test_batch_processing())
    except ImportError:
        print("✗ httpx not installed. Install it with: pip install httpx")
    except KeyboardInterrupt:
        print("\n✗ Test interrupted by user")
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    main()
