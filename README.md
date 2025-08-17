# PRAT - Pay Request Approval Tool

An AI-powered invoice processing system that uses machine learning to compare invoices against purchase orders and subcontracts to make intelligent payment processing recommendations.

## Features

- **Document Processing**: Extract data from PDFs and images using OCR
- **AI-Powered Analysis**: Use LLMs to extract structured data and analyze discrepancies
- **Purchase Order Matching**: Compare invoices against existing POs
- **Business Rules Engine**: Apply approval thresholds and compliance checks
- **Recommendation System**: Generate intelligent payment recommendations
- **REST API**: Full API for integration with existing systems
- **🆕 Batch Processing**: Process multiple PO files from a selected folder automatically
- **🆕 Web Interface**: User-friendly web interface for folder selection and batch processing

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

4. **Run the Application**
   ```bash
   # Option 1: Use the startup script (recommended)
   python start_app.py
   
   # Option 2: Use uvicorn directly
   uvicorn app.main:app --reload
   ```

5. **Access the Web Interface**
   Open your browser and navigate to `http://localhost:8000`

6. **Process Files in Batch**
   - Enter the path to your PO folder
   - Click "Scan Folder" to discover files
   - Click "Process All Files" to start batch processing
   - Monitor progress and view results in real-time

## New Batch Processing Feature

The latest version includes a powerful batch processing capability that allows you to:

- **Select any folder** containing PO files for processing
- **Scan folders** to discover all files automatically
- **Process multiple files** in a single operation
- **Monitor progress** with real-time status updates
- **View detailed results** including success, failure, and skip statistics
- **Handle errors gracefully** without stopping the entire batch

### Batch Processing Workflow

1. **Folder Selection**: Choose any folder containing PO files
2. **File Discovery**: Automatically scan and identify all files
3. **Batch Processing**: Process all files sequentially
4. **Result Analysis**: View comprehensive processing results
5. **Error Handling**: Identify and resolve any processing issues

### Supported File Types

- **PDF files** (.pdf) - Fully supported for PO processing
- **Other file types** - Automatically skipped with appropriate messages

## Project Structure

```
PRAT-/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes and endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Data models and schemas
│   ├── services/          # External service integrations
│   ├── static/            # Web interface files
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── scripts/               # Database and setup scripts
├── tests/                 # Test suite
├── docs/                  # Documentation
├── sample_data/           # Sample invoices and test data
├── start_app.py           # 🆕 Application startup script
├── test_batch_processing.py # 🆕 Batch processing test script
└── demo_batch_processing.py # 🆕 Demo script
```

## Configuration

The system uses environment variables for configuration. See `.env.example` for all available options.

### Required API Keys
- `OPENAI_API_KEY`: OpenAI API key for GPT-4
- `DATABASE_URL`: PostgreSQL connection string
- `OCR_SERVICE_KEY`: OCR service API key (optional)

### Business Rules
- `AUTO_APPROVE_THRESHOLD`: Maximum amount for auto-approval
- `REQUIRE_MANUAL_REVIEW_THRESHOLD`: Amount requiring manual review
- `MAX_OVERAGE_PERCENTAGE`: Maximum allowed overage percentage

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints
- `POST /process-invoice`: Process uploaded invoice
- `GET /invoices/{id}/recommendation`: Get processing recommendation
- `POST /invoices/{id}/approve`: Approve invoice for payment
- `GET /invoices/{id}/validation`: Get validation results
- `🆕 POST /api/v1/folder-monitoring/scan-folder`: Scan a folder for files
- `🆕 POST /api/v1/folder-monitoring/batch-process`: Process all files in a folder

## Testing and Demo

### Test Batch Processing
```bash
python test_batch_processing.py
```

### Run Demo
```bash
python demo_batch_processing.py
```

### Run All Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_invoice_processing.py
```

## Web Interface

The new web interface provides:

- **Folder Selection**: Input field for folder paths
- **File Discovery**: Scan folders to find all files
- **Batch Processing**: Process multiple files at once
- **Progress Tracking**: Real-time processing status
- **Result Display**: Comprehensive processing results
- **Statistics Dashboard**: Processing summary and metrics
- **System Controls**: Start/stop monitoring and folder management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 
