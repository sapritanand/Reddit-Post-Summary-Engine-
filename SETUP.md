# Reddit Analysis System - Setup Guide

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.9 or higher** installed
   - Check: `python --version`
   - Download: https://www.python.org/downloads/

2. **pip** (Python package manager)
   - Usually comes with Python
   - Check: `pip --version`

3. **Reddit API Credentials**
   - You need a Reddit account
   - Create an app at: https://www.reddit.com/prefs/apps

4. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey

5. **(Optional) Tesseract OCR** for image text extraction
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

---

## Installation Steps

### 1. Download the Project

Save all project files to a directory, for example:
```
C:\Users\HP\OneDrive\Desktop\Reddit\
```

### 2. Install Python Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

This will install:
- PRAW (Reddit API)
- Google Gemini API
- BeautifulSoup4 (web scraping)
- newspaper3k (article extraction)
- pytesseract (OCR)
- And other dependencies

**Note:** If you encounter errors:
- Try: `pip install --upgrade pip`
- Or use: `python -m pip install -r requirements.txt`

### 3. Set Up API Credentials

#### Option A: Using .env file (Recommended)

1. Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

2. Edit `.env` file with your credentials:
```
REDDIT_CLIENT_ID=your_actual_client_id
REDDIT_CLIENT_SECRET=your_actual_client_secret
REDDIT_USER_AGENT=RedditAnalyzer/1.0 by YourRedditUsername
GEMINI_API_KEY=your_actual_gemini_api_key
```

#### Option B: Using config.yaml

Edit `config.yaml` directly:
```yaml
reddit:
  client_id: "your_actual_client_id"
  client_secret: "your_actual_client_secret"
  user_agent: "RedditAnalyzer/1.0 by YourRedditUsername"

gemini:
  api_key: "your_actual_gemini_api_key"
```

### 4. Getting Reddit API Credentials

1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - **Name:** Reddit Analyzer (or any name)
   - **App type:** Select "script"
   - **Description:** Personal use
   - **About URL:** (leave blank)
   - **Redirect URI:** http://localhost:8080
4. Click "Create app"
5. Note down:
   - **Client ID:** The string under "personal use script"
   - **Client Secret:** The "secret" field

### 5. Getting Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### 6. (Optional) Install Tesseract OCR

Only needed if you want to analyze image posts with text.

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer
3. Add to PATH: `C:\Program Files\Tesseract-OCR`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

---

## Verification

### Quick Test

Run the quickstart script:

```powershell
python quickstart.py
```

This will:
- Check if .env file exists
- Verify credentials are set
- Test system initialization
- Show cache statistics

### Expected Output:

```
============================================================
               REDDIT ANALYSIS SYSTEM
                    Quick Start
============================================================

Step 1: Checking environment file...
✅ .env file created!

Step 2: Checking credentials...
✅ Credentials found!

Step 3: Testing system...
Initializing analyzer...
✅ Analyzer initialized successfully!

📦 Cache stats: {'posts': 0, 'comments': 0, 'ocr_results': 0, 'link_content': 0}

✨ System is ready to use!
```

---

## First Analysis

### Using CLI

Analyze a Reddit post:

```powershell
python cli.py analyze "https://www.reddit.com/r/AskReddit/comments/example/"
```

### Using Python Script

Create a test script `test.py`:

```python
from reddit_analyzer import RedditAnalyzer

# Initialize
analyzer = RedditAnalyzer.from_env()

# Analyze a post
result = analyzer.analyze_post_url(
    "https://www.reddit.com/r/Python/comments/example/"
)

# Print summary
print(result['synthesis']['executive_summary'])
```

Run it:
```powershell
python test.py
```

---

## Troubleshooting

### Error: "PRAW authentication failed"

**Problem:** Reddit credentials are incorrect.

**Solution:**
1. Double-check client_id and client_secret
2. Ensure user_agent is properly formatted
3. Verify the app type is "script" in Reddit

### Error: "Gemini API key invalid"

**Problem:** Gemini API key is incorrect or not activated.

**Solution:**
1. Verify the API key is correct
2. Check for trailing spaces
3. Ensure the key is enabled in Google Cloud

### Error: "Tesseract not found"

**Problem:** Tesseract OCR is not installed or not in PATH.

**Solution:**
1. Install Tesseract (see step 6)
2. Add to system PATH
3. Or disable OCR in config:
   ```yaml
   processing:
     use_ocr: false
   ```

### Error: "ModuleNotFoundError: No module named 'praw'"

**Problem:** Dependencies not installed.

**Solution:**
```powershell
pip install -r requirements.txt
```

### Error: "Rate limit exceeded"

**Problem:** Too many API calls.

**Solution:**
1. Wait a few minutes
2. Adjust rate limits in config.yaml:
   ```yaml
   processing:
     max_retries: 3
     retry_delay: 5
   ```

### Slow Performance

**Solutions:**
1. Enable caching (default)
2. Reduce comment processing:
   ```yaml
   processing:
     max_comments_process: 50
   ```
3. Use higher quality threshold:
   ```yaml
   processing:
     comment_quality_threshold: 7.0
   ```

---

## Configuration Options

Edit `config.yaml` to customize:

```yaml
processing:
  # Cache expiry time
  cache_expiry_hours: 24
  
  # Maximum comments to process
  max_comments_process: 100
  
  # Minimum quality score (0-10)
  comment_quality_threshold: 5.0
  
  # Gemini API batch size
  batch_size: 10

output:
  # Output format: json, markdown, or both
  format: "both"
  
  # Save results to files
  save_to_file: true
  
  # Output directory
  output_directory: "./analysis_results"

logging:
  # Logging level: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  
  # Log file location
  log_file: "./logs/reddit_analyzer.log"
```

---

## Next Steps

1. **Read the README.md** for detailed usage examples
2. **Run examples.py** to see various usage patterns
3. **Check tests/** directory for test examples
4. **Explore CLI options:** `python cli.py --help`

---

## Support

For issues:
1. Check the troubleshooting section above
2. Review the error message and logs
3. Verify all dependencies are installed
4. Ensure API credentials are correct

---

## System Requirements

**Minimum:**
- Python 3.9+
- 2GB RAM
- Internet connection

**Recommended:**
- Python 3.10+
- 4GB+ RAM
- SSD storage (for faster cache)
- Stable internet connection

---

## Quick Reference

### Common Commands

```powershell
# Analyze single post
python cli.py analyze "POST_URL"

# Batch analysis
python cli.py batch urls.txt

# Cache statistics
python cli.py cache-stats

# Clear cache
python cli.py cache-clear

# Run tests
pytest tests/ -v

# Run with verbose output
python cli.py analyze "POST_URL" -v
```

### Directory Structure

```
Reddit/
├── reddit_analyzer.py      # Main orchestrator
├── reddit_scraper.py       # Reddit API interface
├── content_processor.py    # Content extraction
├── gemini_analyzer.py      # Gemini API interface
├── cache_manager.py        # Caching system
├── cli.py                  # Command-line interface
├── examples.py             # Usage examples
├── config.yaml             # Configuration
├── requirements.txt        # Dependencies
├── tests/                  # Test files
└── analysis_results/       # Output files
```

---

**Installation Complete! 🎉**

You're ready to analyze Reddit posts with AI-powered insights!
