# PRAT - Pay Request Approval Tool

An AI-powered invoice processing system that uses machine learning to compare invoices against purchase orders and subcontracts to make intelligent payment processing recommendations.

## Features

- **Document Processing**: Extract data from PDFs and images using OCR
- **AI-Powered Analysis**: Use LLMs to extract structured data and analyze discrepancies
- **Purchase Order Matching**: Compare invoices against existing POs
- **Business Rules Engine**: Apply approval thresholds and compliance checks
- **Recommendation System**: Generate intelligent payment recommendations
- **REST API**: Full API for integration with existing systems

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
   uvicorn app.main:app --reload
   ```

5. **Process an Invoice**
   ```bash
   curl -X POST "http://localhost:8000/process-invoice" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@sample_invoice.pdf"
   ```

## Project Structure

```
PRAT-/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes and endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Data models and schemas
│   ├── services/          # External service integrations
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── scripts/               # Database and setup scripts
├── tests/                 # Test suite
├── docs/                  # Documentation
└── sample_data/           # Sample invoices and test data
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

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_invoice_processing.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 
