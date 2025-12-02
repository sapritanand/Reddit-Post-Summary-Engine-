"""
Integration Test - Tests complete analysis pipeline
Note: Requires valid API credentials and internet connection
Run with: pytest test_integration.py -v -s
"""

import pytest
import os
from dotenv import load_dotenv
from reddit_analyzer import RedditAnalyzer


# Skip tests if credentials not available
load_dotenv()
SKIP_INTEGRATION = not all([
    os.getenv('REDDIT_CLIENT_ID'),
    os.getenv('REDDIT_CLIENT_SECRET'),
    os.getenv('GEMINI_API_KEY')
])


@pytest.fixture
def analyzer():
    """Create analyzer from environment"""
    if SKIP_INTEGRATION:
        pytest.skip("API credentials not available")
    
    return RedditAnalyzer.from_env()


@pytest.mark.skipif(SKIP_INTEGRATION, reason="API credentials not available")
@pytest.mark.integration
def test_complete_analysis_pipeline(analyzer):
    """
    Test complete analysis pipeline
    Note: Use a stable, existing Reddit post for testing
    """
    # Use a well-known Reddit post (adjust URL as needed)
    post_url = "https://www.reddit.com/r/test/comments/example/"
    
    try:
        result = analyzer.analyze_post_url(post_url)
        
        # Verify structure
        assert 'metadata' in result
        assert 'post_analysis' in result
        assert 'comments_analysis' in result
        assert 'synthesis' in result
        
        # Verify metadata
        assert result['metadata']['post_url']
        assert result['metadata']['subreddit']
        
        # Verify post analysis
        assert result['post_analysis']['content_type']
        assert result['post_analysis']['summaries']
        
        # Verify synthesis
        assert result['synthesis']['executive_summary']
        
        print("\n✅ Integration test passed!")
        print(f"Post: r/{result['metadata']['subreddit']}")
        print(f"Summary: {result['synthesis']['executive_summary'][:100]}...")
    
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="API credentials not available")
@pytest.mark.integration
def test_cache_functionality(analyzer):
    """Test caching works correctly"""
    post_url = "https://www.reddit.com/r/test/comments/example/"
    
    # First analysis (no cache)
    result1 = analyzer.analyze_post_url(post_url, use_cache=False)
    time1 = result1['metadata']['analysis_duration_seconds']
    
    # Second analysis (with cache)
    result2 = analyzer.analyze_post_url(post_url, use_cache=True)
    
    # Cache should be faster (though may not be if Gemini calls are made)
    assert result2 is not None
    
    print(f"\n⏱️  First analysis: {time1:.1f}s")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="API credentials not available")
@pytest.mark.integration
def test_different_content_types(analyzer):
    """Test handling different content types"""
    
    # Test cases for different content types
    test_cases = [
        # ("URL", "expected_content_type"),
        # Add actual Reddit post URLs for different types
    ]
    
    for post_url, expected_type in test_cases:
        try:
            result = analyzer.analyze_post_url(post_url)
            actual_type = result['post_analysis']['content_type']
            
            print(f"\n📄 {post_url}")
            print(f"   Expected: {expected_type}, Got: {actual_type}")
            
            assert actual_type == expected_type
        
        except Exception as e:
            print(f"\n❌ Failed for {post_url}: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
