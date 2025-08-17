# PRAT Batch Processing Feature

This document describes the new batch processing functionality that allows you to process multiple Purchase Order (PO) files from a selected folder instead of uploading them individually.

## Overview

The batch processing feature enables you to:
- Select a folder containing PO files
- Scan the folder to discover all files
- Process all files in the folder automatically
- View detailed results and statistics
- Monitor processing progress

## New Features

### 1. Web Interface
- **Location**: `http://localhost:8000/` (after starting the application)
- **Features**:
  - Folder path input field
  - Scan folder button
  - Batch process button
  - Real-time file status display
  - Processing statistics
  - Progress tracking

### 2. New API Endpoints

#### Scan Custom Folder
```http
POST /api/v1/folder-monitoring/scan-folder
Content-Type: application/json

{
  "folder_path": "/path/to/your/po/folder"
}
```

#### Batch Process Folder
```http
POST /api/v1/folder-monitoring/batch-process
Content-Type: application/json

{
  "folder_path": "/path/to/your/po/folder"
}
```

## How to Use

### 1. Start the Application
```bash
cd PRAT-
uvicorn app.main:app --reload
```

### 2. Access the Web Interface
Open your browser and navigate to `http://localhost:8000/`

### 3. Select a Folder
- Enter the path to your PO folder in the input field
- Or click "Browse" to enter a path manually
- Click "Scan Folder" to discover files

### 4. Process Files
- Review the discovered files
- Click "Process All Files" to start batch processing
- Monitor progress and results in real-time

### 5. View Results
- Check the statistics dashboard for processing summary
- Review individual file statuses
- See detailed error messages for failed files

## Supported File Types

- **PDF files** (.pdf) - Fully supported for PO processing
- **Other file types** - Marked as "skipped" with appropriate messages

## Processing Results

### Success Status
- Files successfully processed show as "completed"
- PO number and vendor information extracted and displayed
- Data stored in the database

### Error Status
- Files with processing errors show as "error"
- Detailed error messages provided
- Original files remain unchanged

### Skipped Status
- Unsupported file types marked as "skipped"
- Reason for skipping provided

## Configuration

The system uses the following configuration from `app/config.py`:
- `po_folder_path`: Default PO folder path
- `invoice_folder_path`: Default invoice folder path
- `processed_folder_path`: Default processed files folder

## Testing

Use the provided test script to verify functionality:

```bash
python test_batch_processing.py
```

This script will:
1. Test folder scanning
2. Test batch processing
3. Verify system status
4. Display detailed results

## API Response Format

### Scan Folder Response
```json
{
  "message": "Folder scan completed for: /path/to/folder",
  "folder_path": "/path/to/folder",
  "scan_results": {
    "files": [
      {
        "name": "po_001.pdf",
        "size": 12345,
        "modified": 1234567890,
        "extension": ".pdf"
      }
    ],
    "total_files": 1,
    "total_size": 12345
  }
}
```

### Batch Process Response
```json
{
  "message": "Batch processing completed for folder: /path/to/folder",
  "folder_path": "/path/to/folder",
  "total_files": 5,
  "processed_files": [
    {
      "name": "po_001.pdf",
      "status": "success",
      "po_number": "PO-2024-001",
      "vendor_name": "ABC Company"
    }
  ],
  "errors": [
    {
      "name": "image.jpg",
      "status": "skipped",
      "error": "File type .jpg not supported"
    }
  ],
  "summary": {
    "successful": 4,
    "failed": 0,
    "skipped": 1
  }
}
```

## Error Handling

The system provides comprehensive error handling:
- Invalid folder paths
- File access permissions
- PDF processing errors
- Database connection issues
- Individual file processing failures

## Performance Considerations

- Large folders are processed sequentially to avoid overwhelming the system
- Progress tracking provides real-time feedback
- Error handling ensures one failed file doesn't stop the entire batch
- Database transactions are handled per file for data integrity

## Troubleshooting

### Common Issues

1. **Folder not found**
   - Verify the folder path is correct
   - Check file permissions
   - Ensure the path is accessible from the application

2. **Processing errors**
   - Check file format (PDF files only)
   - Verify file integrity
   - Check application logs for detailed error messages

3. **Database errors**
   - Ensure database is running and accessible
   - Check database connection configuration
   - Verify required tables exist

### Logs
Check the application logs in the `logs/` directory for detailed error information.

## Future Enhancements

Potential improvements for future versions:
- Parallel processing for better performance
- File type conversion support
- Batch processing scheduling
- Email notifications for completion
- Integration with external systems
- Advanced filtering and selection options

## Support

For issues or questions about the batch processing feature:
1. Check the application logs
2. Review this documentation
3. Test with the provided test script
4. Check the API documentation at `http://localhost:8000/docs`
