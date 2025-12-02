"""
Utility functions for Reddit Analysis System
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2):
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def format_timestamp(timestamp_str: str, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format ISO timestamp to readable string
    
    Args:
        timestamp_str: ISO format timestamp
        format: Output format
        
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime(format)
    except:
        return timestamp_str


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_reddit_post_id(url: str) -> str:
    """
    Extract post ID from Reddit URL
    
    Args:
        url: Reddit post URL
        
    Returns:
        Post ID
    """
    import re
    match = re.search(r'/comments/([a-z0-9]+)', url)
    if match:
        return match.group(1)
    return ''


def format_score(score: int) -> str:
    """
    Format score with k/M suffix
    
    Args:
        score: Score number
        
    Returns:
        Formatted score string
    """
    if score >= 1_000_000:
        return f"{score/1_000_000:.1f}M"
    elif score >= 1_000:
        return f"{score/1_000:.1f}k"
    else:
        return str(score)


def calculate_sentiment_percentage(sentiment_dict: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate percentage distribution from sentiment counts
    
    Args:
        sentiment_dict: Dictionary with sentiment counts
        
    Returns:
        Dictionary with percentages
    """
    total = sum(sentiment_dict.values())
    if total == 0:
        return {k: 0.0 for k in sentiment_dict.keys()}
    
    return {k: (v / total) * 100 for k, v in sentiment_dict.items()}


def merge_insights(insights_list: List[List[str]]) -> List[str]:
    """
    Merge and deduplicate insights from multiple sources
    
    Args:
        insights_list: List of insight lists
        
    Returns:
        Merged and deduplicated insights
    """
    all_insights = []
    for insights in insights_list:
        all_insights.extend(insights)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_insights = []
    for insight in all_insights:
        insight_lower = insight.lower().strip()
        if insight_lower not in seen:
            seen.add(insight_lower)
            unique_insights.append(insight)
    
    return unique_insights


def create_analysis_summary(result: Dict[str, Any]) -> str:
    """
    Create a brief text summary from analysis result
    
    Args:
        result: Analysis result dictionary
        
    Returns:
        Summary string
    """
    lines = []
    
    # Header
    lines.append(f"Post: r/{result['metadata']['subreddit']}")
    lines.append(f"Score: {format_score(result['metadata']['score'])}")
    lines.append(f"Comments: {result['metadata']['comment_count']}")
    lines.append("")
    
    # Summary
    lines.append("Summary:")
    lines.append(result['synthesis']['executive_summary'])
    lines.append("")
    
    # Key insights
    if result['synthesis']['key_insights']:
        lines.append("Key Insights:")
        for insight in result['synthesis']['key_insights'][:3]:
            lines.append(f"  • {insight}")
    
    return '\n'.join(lines)


def validate_reddit_url(url: str) -> bool:
    """
    Validate Reddit URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid Reddit URL
    """
    import re
    pattern = r'https?://(www\.)?reddit\.com/r/\w+/comments/[a-z0-9]+/'
    return bool(re.match(pattern, url))


def get_output_filename(post_id: str, extension: str = 'json', include_timestamp: bool = True) -> str:
    """
    Generate output filename
    
    Args:
        post_id: Reddit post ID
        extension: File extension
        include_timestamp: Whether to include timestamp
        
    Returns:
        Filename string
    """
    if include_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{post_id}_{timestamp}.{extension}"
    else:
        return f"{post_id}.{extension}"


def estimate_analysis_time(num_comments: int) -> float:
    """
    Estimate analysis time based on comment count
    
    Args:
        num_comments: Number of comments
        
    Returns:
        Estimated time in seconds
    """
    base_time = 10  # Base time for post analysis
    comment_time = 0.5  # Time per comment (batched)
    
    return base_time + (num_comments * comment_time)
