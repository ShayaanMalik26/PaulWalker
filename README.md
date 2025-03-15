# Patent Scraper and IPFS Storage System

This project automates the process of scraping patents from Google Patents, storing them in IPFS, and providing semantic search capabilities. The system runs as a Windows service, continuously updating the patent database at regular intervals.

## Prerequisites

### 1. Install IPFS
1. Download IPFS Desktop from [IPFS Desktop Releases](https://github.com/ipfs/ipfs-desktop/releases)
2. Install and run IPFS Desktop
3. Verify installation by opening http://127.0.0.1:5001/webui

### 2. Set up Python Environment
```bash
# Create and activate conda environment
conda create -n patent_env python=3.11.11
conda activate patent_env

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root with:
```env
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
OPENAI_API_KEY=your_openai_api_key_here  # If using OpenAI features
```

## Project Components

### 1. Patent Link Scraper (`getlinks_final.py`)
- Scrapes patent links from Google Patents
- Saves unique patent URLs to `patent_urls.txt`
- Features:
  - Date-based scraping
  - Duplicate detection
  - Rate limiting protection

### 2. Patent Processor (`working.py`)
- Processes patents from `patent_urls.txt`
- Features:
  - Extracts patent information
  - Generates JSON files
  - Stores data in IPFS
  - Creates embeddings for semantic search
  - Saves to ChromaDB

### 3. Scheduler (`scheduler.py`)
- Automates the scraping and processing
- Runs every 6 hours
- Manages IPFS daemon
- Provides real-time logging

### 4. Windows Service (`service_wrapper.py`)
- Runs the scheduler as a Windows service
- Starts automatically with Windows
- Provides system-level logging

### 5. API Server (`app.py`)
- Provides semantic search capabilities
- FastAPI-based REST API
- Searches through ChromaDB collections

## IPFS Handler

The `ipfs_handler.py` module manages all IPFS interactions:

### Features
- Initializes IPFS directory structure
- Uploads patent data to IPFS
- Manages local JSON storage
- Provides verification of uploads
- Handles IPFS pinning
- Creates Mutable File System (MFS) entries

### Access Methods
After a patent is processed, you can access it through:
1. Local Gateway: `http://127.0.0.1:8080/ipfs/<hash>`
2. IPFS Desktop: Files section in WebUI
3. Local JSON: `patent_json/<patent_number>.json`

### File Structure in IPFS
Each patent is stored as a JSON file containing:
```json
{
    "patent_title": "...",
    "abstract": "...",
    "inventions": [...],
    "publication_number": "...",
    "filing_date": "...",
    "assignee_name": "...",
    "inventor_name": "...",
    "patent_url": "...",
    "patent_text": "...",
    "ipfs_hash": "..."
}
```

## Installation and Usage

### 1. Basic Setup
```bash

# Create and activate conda environment
conda create -n patent_env python=3.11.11
conda activate patent_env

# Install requirements
pip install -r requirements.txt
```

### 2. Start IPFS Daemon
```bash
# Start IPFS daemon if not running via IPFS Desktop
ipfs daemon
```


## File Structure
```
project/
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── getlinks_final.py      # Patent URL scraper
├── working.py             # Patent processor
├── scheduler.py           # Automation scheduler
├── app.py                 # API server
├── patent_urls.txt        # Scraped patent URLs
├── patent_json/           # Stored JSON files
├── chromadb_store/        # ChromaDB storage
└── service_logs/          # Service log files

```

## Monitoring and Maintenance


### 2. IPFS Access
- Web UI: http://127.0.0.1:5001/webui
- Files: http://127.0.0.1:5001/ipfs/[hash]/#/files

### 3. API Access
- Start API server: `uvicorn app:app --reload`
- API documentation: http://localhost:8000/docs
- Search endpoint: http://localhost:8000/search?query=your_search_query

## Troubleshooting

1. If patents aren't being scraped:
   - Check internet connection
   - Verify Google Patents accessibility
   - Check rate limiting in `getlinks_final.py`

2. If IPFS storage fails:
   - Verify IPFS daemon is running
   - Check IPFS connection at http://127.0.0.1:5001/webui
   - Ensure sufficient disk space

3. IPFS Connection Issues:
   - Verify IPFS Desktop is running
   - Check http://127.0.0.1:5001/webui
   - Ensure port 5001 is available

4. Patent Processing Issues:
   - Check internet connection
   - Verify patent_urls.txt format (one URL per line)
   - Check patent_json/ directory permissions

5. IPFS Storage Issues:
   - Verify sufficient disk space
   - Check IPFS daemon logs
   - Ensure write permissions in patent_json/

6. Search API Issues:
   - Verify ChromaDB files exist
   - Check if API server is running
   - Ensure all dependencies are installed

## Notes
- Keep IPFS Desktop running during all operations
- Each patent URL should be on a new line in patent_urls.txt
- The scheduler can be stopped with Ctrl+C
- Patents are stored both locally and on IPFS
- IPFS hashes are permanent and content-addressable
- Regular internet connection required



