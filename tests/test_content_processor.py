"""
Unit Tests for Content Processor
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from content_processor import ContentProcessor


@pytest.fixture
def processor():
    """Create content processor instance"""
    return ContentProcessor(ocr_language='en', link_timeout=10)


def test_processor_initialization(processor):
    """Test processor initialization"""
    assert processor.ocr_language == 'en'
    assert processor.link_timeout == 10


def test_detect_content_type(processor):
    """Test content type detection"""
    # Text post
    post_data = {'is_self': True, 'selftext': 'content'}
    assert processor.detect_content_type(post_data) == 'text'
    
    # Image post
    post_data = {'is_self': False, 'url': 'https://i.redd.it/image.jpg'}
    assert processor.detect_content_type(post_data) == 'image'
    
    # Video post
    post_data = {'is_self': False, 'url': 'https://v.redd.it/video'}
    assert processor.detect_content_type(post_data) == 'video'
    
    # Link post
    post_data = {'is_self': False, 'url': 'https://example.com/article'}
    assert processor.detect_content_type(post_data) == 'link'
    
    # Pre-determined type
    post_data = {'content_type': 'gallery'}
    assert processor.detect_content_type(post_data) == 'gallery'


def test_process_text_post(processor):
    """Test processing text post"""
    post_data = {
        'title': 'Test Title',
        'selftext': 'Test content here',
        'is_self': True,
        'content_type': 'text'
    }
    
    result = processor.process_post(post_data)
    
    assert 'extracted_text' in result
    assert 'Test Title' in result['extracted_text']
    assert 'Test content' in result['extracted_text']


def test_clean_ocr_text(processor):
    """Test OCR text cleaning"""
    raw_text = """
    
    Line 1
    
    Line 2    with   spaces
    
    
    Line 3
    
    """
    
    cleaned = processor._clean_ocr_text(raw_text)
    
    assert 'Line 1' in cleaned
    assert 'Line 2' in cleaned
    assert 'Line 3' in cleaned
    assert '\n\n' not in cleaned  # No excessive newlines
    assert '   ' not in cleaned  # No excessive spaces


def test_extract_text_summary(processor):
    """Test text summarization"""
    # Short text (no truncation)
    short_text = "This is a short text."
    summary = processor.extract_text_summary(short_text, max_length=100)
    assert summary == short_text
    
    # Long text (should truncate)
    long_text = "A" * 1000
    summary = processor.extract_text_summary(long_text, max_length=100)
    assert len(summary) <= 103  # 100 + "..."
    assert summary.endswith('...')


def test_validate_url(processor):
    """Test URL validation"""
    # Note: This test may fail without internet connection
    # In production, this should be mocked
    
    # Valid URL (mocked)
    with patch.object(processor.session, 'head') as mock_head:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        assert processor.validate_url('https://example.com') is True
    
    # Invalid URL (mocked)
    with patch.object(processor.session, 'head') as mock_head:
        mock_head.side_effect = Exception("Connection error")
        
        assert processor.validate_url('https://invalid-url-12345.com') is False


@patch('content_processor.PIL_AVAILABLE', False)
def test_extract_from_image_no_pil():
    """Test image extraction when PIL is not available"""
    processor = ContentProcessor()
    result = processor.extract_from_image('https://example.com/image.jpg')
    assert result is None


@patch('content_processor.BS4_AVAILABLE', False)
def test_extract_from_link_no_bs4():
    """Test link extraction when BeautifulSoup is not available"""
    processor = ContentProcessor()
    result = processor.extract_from_link('https://example.com')
    assert result is None


def test_process_video_post(processor):
    """Test processing video post (should skip)"""
    post_data = {
        'title': 'Video Post',
        'url': 'https://v.redd.it/video123',
        'content_type': 'video'
    }
    
    result = processor.process_post(post_data)
    
    assert 'extracted_text' in result
    assert '[Video content - unsupported' in result['extracted_text']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
