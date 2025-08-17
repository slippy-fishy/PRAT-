#!/usr/bin/env python3
"""
Startup script for PRAT application
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Main startup function"""
    print("PRAT - Pay Request Approval Tool")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("Error: Please run this script from the PRAT- directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    # Check for required files
    required_files = [
        "app/main.py",
        "app/config.py",
        "requirements.txt"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("Error: Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        sys.exit(1)
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("Warning: .env file not found. Using default configuration.")
        print("Consider copying .env.example to .env and configuring your settings.")
        print()
    
    # Create required directories
    directories = ["logs", "uploads", "purchase_orders", "invoices", "processed"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Starting PRAT application...")
    print("Web interface will be available at: http://localhost:8000")
    print("API documentation will be available at: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the application")
    print("=" * 40)
    
    try:
        # Start the application
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
