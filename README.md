# Reddit Post & Comment Analysis System

A comprehensive Python-based system that analyzes Reddit posts and comments to extract meaningful insights, sentiment, and summaries using Google's Gemini API.

## Features

- **Multi-format Content Processing**: Handles text, images (OCR), links, and galleries
- **Intelligent Comment Analysis**: Hierarchical comment processing with quality filtering
- **AI-Powered Insights**: Uses Gemini API for sentiment analysis, entity extraction, and synthesis
- **Smart Caching**: SQLite-based caching to minimize API calls and processing time
- **Comprehensive Output**: Structured JSON output with executive summaries and actionable insights

## Architecture

### Phase 1: Core Data Extraction
- Reddit scraper using PRAW
- Content processor for images (OCR) and links
- SQLite caching layer

### Phase 2: Content Enrichment
- Post enrichment (entities, sentiment, summaries)
- Comment enrichment (quality scoring, intent classification)
- Multi-target sentiment analysis

### Phase 3: Synthesis
- Cross-validation of post claims with comment feedback
- Solution aggregation and ranking
- Final comprehensive analysis generation

## Installation

### Prerequisites
- Python 3.9 or higher
- Tesseract OCR (optional, for image analysis)
- Reddit API credentials
- Google Gemini API key

### Setup

1. **Clone or download the repository**

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR (optional)**:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

4. **Set up credentials**:
   - Copy `.env.example` to `.env`
   - Fill in your Reddit API credentials and Gemini API key
   - Alternatively, edit `config.yaml` directly

### Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Fill in the required fields
5. Copy the client ID and secret

### Getting Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key to your configuration

## Usage

### Basic Usage

```python
from reddit_analyzer import RedditAnalyzer

# Initialize the analyzer
analyzer = RedditAnalyzer(
    reddit_credentials={
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'user_agent': 'RedditAnalyzer/1.0'
    },
    gemini_api_key='your_gemini_api_key'
)

# Analyze a single post
result = analyzer.analyze_post_url(
    'https://www.reddit.com/r/AskReddit/comments/example/'
)

# Access the results
print(result['synthesis']['executive_summary'])
print(result['post_analysis']['summaries']['one_sentence'])
```

### Command-Line Interface

```bash
# Analyze a single post
python cli.py analyze "https://www.reddit.com/r/AskReddit/comments/example/"

# Analyze multiple posts
python cli.py batch urls.txt

# Use custom config
python cli.py analyze "URL" --config custom_config.yaml
```

### Using Environment Variables

```python
import os
from dotenv import load_dotenv
from reddit_analyzer import RedditAnalyzer

# Load credentials from .env file
load_dotenv()

analyzer = RedditAnalyzer.from_env()
result = analyzer.analyze_post_url('POST_URL')
```

## Output Format

The system generates a comprehensive JSON structure:

```json
{
  "metadata": {
    "post_url": "...",
    "subreddit": "...",
    "author": "...",
    "timestamp": "...",
    "score": 1234,
    "comment_count": 567
  },
  "post_analysis": {
    "content_type": "image",
    "extracted_text": "...",
    "entities": {...},
    "sentiment": {...},
    "summaries": {...}
  },
  "comments_analysis": {
    "total_processed": 50,
    "top_comments": [...],
    "sentiment_distribution": {...}
  },
  "synthesis": {
    "executive_summary": "...",
    "recommended_actions": [...],
    "insights": [...]
  }
}
```

## Configuration

Edit `config.yaml` to customize:

- **Processing settings**: Cache duration, comment limits, quality thresholds
- **Gemini parameters**: Model selection, temperature, token limits
- **Output preferences**: Format (JSON/Markdown), save location
- **Logging**: Level and format

## Project Structure

```
Reddit/
├── reddit_analyzer.py      # Main orchestration class
├── reddit_scraper.py       # Reddit API interface
├── content_processor.py    # Content extraction (OCR, links)
├── gemini_analyzer.py      # Gemini API integration
├── cache_manager.py        # SQLite caching layer
├── cli.py                  # Command-line interface
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── tests/                  # Unit tests
└── analysis_results/       # Output directory
```

## Error Handling

The system handles:
- Reddit API rate limits (exponential backoff)
- Deleted/removed posts
- OCR failures
- Link fetch timeouts
- Gemini API errors
- Malformed JSON responses

## Performance

- Post analysis: ~30 seconds (including API calls)
- Comment batch (10): ~15 seconds
- Full analysis (post + 50 comments): ~2 minutes
- Cache hit: <1 second

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_reddit_scraper.py

# Run with coverage
pytest --cov=. tests/
```

## Cost Optimization

- Aggressive caching (OCR, link fetching, API responses)
- Batch processing for comments
- Quality filtering before Gemini API calls
- Configurable limits and thresholds

## Limitations

- Video content is not processed (logged as "unsupported")
- Gallery posts process each image individually (may be slow)
- Rate limits apply to both Reddit and Gemini APIs
- OCR accuracy depends on image quality

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Troubleshooting

### Common Issues

**"PRAW authentication failed"**
- Verify your Reddit API credentials
- Check that user_agent is properly formatted

**"Gemini API key invalid"**
- Ensure your API key is active
- Check for trailing spaces in the key

**"Tesseract not found"**
- Install Tesseract OCR
- Add Tesseract to your system PATH

**"Rate limit exceeded"**
- Wait before retrying
- Adjust retry settings in config.yaml

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the configuration documentation

## Future Enhancements

- Support for multiple LLM providers
- Real-time analysis of live threads
- Visualization dashboard
- Trend analysis across multiple posts
- API endpoint for external integrations
