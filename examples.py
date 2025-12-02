"""
Example Usage Script for Reddit Analysis System
Demonstrates various ways to use the system
"""

import os
from dotenv import load_dotenv
from reddit_analyzer import RedditAnalyzer
import json


def example_1_basic_analysis():
    """Example 1: Basic post analysis with environment variables"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Post Analysis")
    print("="*60 + "\n")
    
    # Load credentials from .env file
    load_dotenv()
    
    # Initialize analyzer from environment
    analyzer = RedditAnalyzer.from_env()
    
    # Analyze a post
    post_url = "https://www.reddit.com/r/AskReddit/comments/example/"
    result = analyzer.analyze_post_url(post_url)
    
    # Print summary
    print("Executive Summary:")
    print(result['synthesis']['executive_summary'])
    print()
    
    print("Key Insights:")
    for insight in result['synthesis']['key_insights']:
        print(f"  • {insight}")


def example_2_with_config():
    """Example 2: Using configuration file"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Using Configuration File")
    print("="*60 + "\n")
    
    # Initialize from config file
    analyzer = RedditAnalyzer.from_config_file('config.yaml')
    
    # Analyze post
    post_url = "https://www.reddit.com/r/Python/comments/example/"
    result = analyzer.analyze_post_url(post_url)
    
    print(f"Analyzed post in r/{result['metadata']['subreddit']}")
    print(f"Found {result['comments_analysis']['high_quality_count']} high-quality comments")


def example_3_manual_initialization():
    """Example 3: Manual initialization with credentials"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Manual Initialization")
    print("="*60 + "\n")
    
    # Manual credential setup
    reddit_credentials = {
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'user_agent': 'RedditAnalyzer/1.0'
    }
    
    gemini_api_key = 'your_gemini_api_key'
    
    # Custom configuration
    config = {
        'processing': {
            'max_comments_process': 50,  # Process fewer comments
            'comment_quality_threshold': 7.0,  # Higher quality threshold
            'batch_size': 5
        },
        'output': {
            'format': 'json',  # Only JSON output
            'save_to_file': True
        }
    }
    
    # Initialize
    analyzer = RedditAnalyzer(reddit_credentials, gemini_api_key, config)
    
    print("Analyzer initialized with custom config")


def example_4_batch_analysis():
    """Example 4: Batch analysis of multiple posts"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Analysis")
    print("="*60 + "\n")
    
    load_dotenv()
    analyzer = RedditAnalyzer.from_env()
    
    # List of posts to analyze
    post_urls = [
        "https://www.reddit.com/r/Python/comments/example1/",
        "https://www.reddit.com/r/learnpython/comments/example2/",
        "https://www.reddit.com/r/AskReddit/comments/example3/"
    ]
    
    # Analyze all posts
    results = analyzer.analyze_multiple_posts(post_urls)
    
    # Print summary for each
    for i, result in enumerate(results, 1):
        if result.get('success'):
            print(f"\nPost {i}: r/{result['metadata']['subreddit']}")
            print(f"  Key Issue: {result['synthesis']['key_issue']}")
        else:
            print(f"\nPost {i}: Failed - {result.get('error')}")


def example_5_accessing_results():
    """Example 5: Detailed result access"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Accessing Analysis Results")
    print("="*60 + "\n")
    
    load_dotenv()
    analyzer = RedditAnalyzer.from_env()
    
    post_url = "https://www.reddit.com/r/technology/comments/example/"
    result = analyzer.analyze_post_url(post_url)
    
    # Access metadata
    print("POST METADATA:")
    print(f"  Subreddit: r/{result['metadata']['subreddit']}")
    print(f"  Author: u/{result['metadata']['author']}")
    print(f"  Score: {result['metadata']['score']}")
    print(f"  Comments: {result['metadata']['comment_count']}")
    
    # Access post analysis
    print("\nPOST ANALYSIS:")
    print(f"  Content Type: {result['post_analysis']['content_type']}")
    print(f"  Sentiment: {result['post_analysis']['sentiment']['primary']}")
    print(f"  Core Issue: {result['post_analysis']['core_issue']}")
    
    # Access entity extraction
    entities = result['post_analysis']['entities']
    if entities['organizations']:
        print(f"  Organizations mentioned: {', '.join(entities['organizations'])}")
    
    # Access comments analysis
    print("\nCOMMENTS ANALYSIS:")
    print(f"  Total Comments: {result['comments_analysis']['total_processed']}")
    print(f"  High Quality: {result['comments_analysis']['high_quality_count']}")
    
    # Access sentiment distribution
    sentiment_dist = result['comments_analysis']['sentiment_distribution']
    print(f"  Supportive: {sentiment_dist.get('supportive', 0)}")
    print(f"  Critical: {sentiment_dist.get('critical', 0)}")
    print(f"  Neutral: {sentiment_dist.get('neutral', 0)}")
    
    # Access top comments
    print("\nTOP COMMENTS:")
    for i, comment in enumerate(result['comments_analysis']['top_comments'][:3], 1):
        print(f"  {i}. Score: {comment['score']}, Intent: {comment['intent_primary']}")
    
    # Access synthesis
    print("\nSYNTHESIS:")
    print(f"  Validation Status: {result['synthesis']['community_consensus']['validation_status']}")
    print(f"  Agreement Level: {result['synthesis']['community_consensus']['agreement_level']}")
    
    # Access recommended actions
    print("\nRECOMMENDED ACTIONS:")
    for i, action in enumerate(result['synthesis']['recommended_actions'][:3], 1):
        print(f"  {i}. {action}")


def example_6_cache_management():
    """Example 6: Cache management"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Cache Management")
    print("="*60 + "\n")
    
    load_dotenv()
    analyzer = RedditAnalyzer.from_env()
    
    # Get cache statistics
    stats = analyzer.get_cache_stats()
    print("CACHE STATISTICS:")
    print(f"  Posts: {stats['posts']}")
    print(f"  Comments: {stats['comments']}")
    print(f"  OCR Results: {stats['ocr_results']}")
    print(f"  Link Content: {stats['link_content']}")
    
    # Clear expired cache
    print("\nClearing expired cache...")
    cleared = analyzer.clear_cache(expired_only=True)
    print(f"Cleared: {cleared}")
    
    # Analyze with cache disabled
    print("\nAnalyzing without cache...")
    result = analyzer.analyze_post_url(
        "https://www.reddit.com/r/Python/comments/example/",
        use_cache=False
    )


def example_7_save_and_load_results():
    """Example 7: Saving and loading results"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Saving and Loading Results")
    print("="*60 + "\n")
    
    load_dotenv()
    analyzer = RedditAnalyzer.from_env()
    
    # Analyze post (automatically saves to file)
    post_url = "https://www.reddit.com/r/science/comments/example/"
    result = analyzer.analyze_post_url(post_url)
    
    post_id = result['metadata']['post_id']
    print(f"Analysis saved for post: {post_id}")
    
    # Load from JSON file
    from pathlib import Path
    output_dir = Path('./analysis_results')
    json_files = list(output_dir.glob(f"{post_id}*.json"))
    
    if json_files:
        with open(json_files[0], 'r') as f:
            loaded_result = json.load(f)
        
        print(f"\nLoaded from: {json_files[0]}")
        print(f"Executive Summary: {loaded_result['synthesis']['executive_summary']}")


def example_8_error_handling():
    """Example 8: Error handling"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Error Handling")
    print("="*60 + "\n")
    
    load_dotenv()
    analyzer = RedditAnalyzer.from_env()
    
    # Try to analyze invalid URL
    try:
        result = analyzer.analyze_post_url("https://reddit.com/invalid/url/")
    except Exception as e:
        print(f"Error caught: {type(e).__name__}: {e}")
    
    # Batch analysis with error handling
    post_urls = [
        "https://www.reddit.com/r/Python/comments/valid/",
        "https://reddit.com/invalid/",
        "https://www.reddit.com/r/AskReddit/comments/another_valid/"
    ]
    
    results = analyzer.analyze_multiple_posts(post_urls)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\nSuccessful: {len(successful)}")
    print(f"Failed: {len(failed)}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print(" "*20 + "REDDIT ANALYSIS SYSTEM - EXAMPLES")
    print("="*80)
    
    examples = [
        ("Basic Analysis", example_1_basic_analysis),
        ("Configuration File", example_2_with_config),
        ("Manual Initialization", example_3_manual_initialization),
        ("Batch Analysis", example_4_batch_analysis),
        ("Accessing Results", example_5_accessing_results),
        ("Cache Management", example_6_cache_management),
        ("Save and Load", example_7_save_and_load_results),
        ("Error Handling", example_8_error_handling),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nNote: These examples require valid Reddit and Gemini API credentials.")
    print("Set up your .env file before running these examples.")
    
    # Uncomment to run specific example:
    # example_1_basic_analysis()
    # example_5_accessing_results()


if __name__ == '__main__':
    main()
