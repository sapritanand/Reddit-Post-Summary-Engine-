"""
Unit Tests for Cache Manager
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from cache_manager import CacheManager


@pytest.fixture
def temp_cache():
    """Create temporary cache for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    cache = CacheManager(db_path=db_path, expiry_hours=1)
    yield cache
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_cache_initialization(temp_cache):
    """Test cache database initialization"""
    assert temp_cache.db_path
    assert os.path.exists(temp_cache.db_path)


def test_post_caching(temp_cache):
    """Test post cache operations"""
    post_url = "https://reddit.com/r/test/comments/abc123"
    raw_data = {
        'title': 'Test Post',
        'selftext': 'Test content',
        'score': 100
    }
    extracted_text = "Test extracted text"
    
    # Cache post
    result = temp_cache.cache_post(post_url, raw_data, extracted_text)
    assert result is True
    
    # Retrieve from cache
    cached = temp_cache.get_post_cache(post_url)
    assert cached is not None
    assert cached['raw_data']['title'] == 'Test Post'
    assert cached['extracted_text'] == extracted_text


def test_ocr_caching(temp_cache):
    """Test OCR cache operations"""
    image_url = "https://i.redd.it/test123.jpg"
    extracted_text = "Text from image"
    
    # Cache OCR result
    result = temp_cache.cache_ocr(image_url, extracted_text)
    assert result is True
    
    # Retrieve from cache
    cached = temp_cache.get_ocr_cache(image_url)
    assert cached == extracted_text


def test_link_caching(temp_cache):
    """Test link content cache operations"""
    url = "https://example.com/article"
    title = "Test Article"
    content = "Article content here"
    domain = "example.com"
    
    # Cache link content
    result = temp_cache.cache_link(url, title, content, domain)
    assert result is True
    
    # Retrieve from cache
    cached = temp_cache.get_link_cache(url)
    assert cached is not None
    assert cached['title'] == title
    assert cached['content'] == content
    assert cached['source_domain'] == domain


def test_cache_expiry():
    """Test cache expiration"""
    # Create cache with very short expiry
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    cache = CacheManager(db_path=db_path, expiry_hours=0)
    
    try:
        # Cache something
        post_url = "https://reddit.com/test"
        cache.cache_post(post_url, {'title': 'Test'}, 'text')
        
        # Should be expired immediately
        cached = cache.get_post_cache(post_url)
        assert cached is None
    
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_cache_stats(temp_cache):
    """Test cache statistics"""
    # Add some entries
    temp_cache.cache_post("https://reddit.com/1", {'title': 'Post 1'}, 'text1')
    temp_cache.cache_post("https://reddit.com/2", {'title': 'Post 2'}, 'text2')
    temp_cache.cache_ocr("https://i.redd.it/img1.jpg", "text1")
    temp_cache.cache_link("https://example.com", "Title", "Content", "example.com")
    
    # Get stats
    stats = temp_cache.get_cache_stats()
    assert stats['posts'] == 2
    assert stats['ocr_results'] == 1
    assert stats['link_content'] == 1


def test_clear_expired_cache(temp_cache):
    """Test clearing expired cache entries"""
    # Add entries
    temp_cache.cache_post("https://reddit.com/1", {'title': 'Post 1'}, 'text1')
    temp_cache.cache_post("https://reddit.com/2", {'title': 'Post 2'}, 'text2')
    
    # Clear expired (should clear nothing since expiry is 1 hour)
    cleared = temp_cache.clear_expired_cache()
    assert cleared['posts'] == 0
    
    # Verify posts still exist
    stats = temp_cache.get_cache_stats()
    assert stats['posts'] == 2


def test_delete_operations(temp_cache):
    """Test cache deletion operations"""
    post_url = "https://reddit.com/test"
    image_url = "https://i.redd.it/img.jpg"
    link_url = "https://example.com"
    
    # Cache entries
    temp_cache.cache_post(post_url, {'title': 'Post'}, 'text')
    temp_cache.cache_ocr(image_url, "ocr text")
    temp_cache.cache_link(link_url, "Title", "Content", "example.com")
    
    # Delete entries
    assert temp_cache.delete_post_cache(post_url) is True
    assert temp_cache.delete_ocr_cache(image_url) is True
    assert temp_cache.delete_link_cache(link_url) is True
    
    # Verify deletion
    assert temp_cache.get_post_cache(post_url) is None
    assert temp_cache.get_ocr_cache(image_url) is None
    assert temp_cache.get_link_cache(link_url) is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
