"""
Unit Tests for Reddit Scraper
Note: These tests use mocking to avoid actual Reddit API calls
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from reddit_scraper import RedditScraper


@pytest.fixture
def mock_reddit():
    """Create mock Reddit instance"""
    with patch('reddit_scraper.praw.Reddit') as mock:
        reddit_instance = MagicMock()
        mock.return_value = reddit_instance
        
        # Mock user.me() for authentication test
        reddit_instance.user.me.return_value = None
        
        yield reddit_instance


@pytest.fixture
def scraper(mock_reddit):
    """Create scraper with mocked Reddit"""
    return RedditScraper(
        client_id='test_id',
        client_secret='test_secret',
        user_agent='test_agent'
    )


def test_scraper_initialization(scraper):
    """Test scraper initialization"""
    assert scraper.reddit is not None


def test_detect_url_type(scraper):
    """Test URL type detection"""
    assert scraper._detect_url_type('https://i.redd.it/abc.jpg') == 'image'
    assert scraper._detect_url_type('https://example.com/image.png') == 'image'
    assert scraper._detect_url_type('https://v.redd.it/video') == 'video'
    assert scraper._detect_url_type('https://youtube.com/watch?v=123') == 'video'
    assert scraper._detect_url_type('https://example.com/article') == 'link'


def test_fetch_post(scraper, mock_reddit):
    """Test post fetching"""
    # Mock submission
    mock_submission = MagicMock()
    mock_submission.id = 'abc123'
    mock_submission.title = 'Test Post'
    mock_submission.selftext = 'Test content'
    mock_submission.author = 'test_user'
    mock_submission.subreddit = 'test'
    mock_submission.score = 100
    mock_submission.upvote_ratio = 0.95
    mock_submission.num_comments = 50
    mock_submission.created_utc = 1234567890
    mock_submission.url = 'https://reddit.com/r/test/comments/abc123'
    mock_submission.permalink = '/r/test/comments/abc123'
    mock_submission.is_self = True
    mock_submission.link_flair_text = None
    mock_submission.over_18 = False
    mock_submission.spoiler = False
    mock_submission.stickied = False
    mock_submission.locked = False
    
    mock_reddit.submission.return_value = mock_submission
    
    # Fetch post
    post_data = scraper.fetch_post('https://reddit.com/r/test/comments/abc123')
    
    assert post_data['id'] == 'abc123'
    assert post_data['title'] == 'Test Post'
    assert post_data['selftext'] == 'Test content'
    assert post_data['author'] == 'test_user'
    assert post_data['subreddit'] == 'test'
    assert post_data['score'] == 100


def test_sampling_strategy(scraper):
    """Test comment sampling strategy determination"""
    # Small number of comments
    strategy = scraper.determine_sampling_strategy(30)
    assert strategy['strategy'] == 'all'
    assert strategy['max_comments'] is None
    
    # Medium number of comments
    strategy = scraper.determine_sampling_strategy(200)
    assert strategy['strategy'] == 'top_plus_sampling'
    assert strategy['max_comments'] == 50
    
    # Large number of comments
    strategy = scraper.determine_sampling_strategy(1000)
    assert strategy['strategy'] == 'top_clustering'
    assert strategy['max_comments'] == 100


def test_apply_sampling(scraper):
    """Test comment sampling"""
    # Create test comments
    comments = [
        {'id': f'comment_{i}', 'score': 100 - i, 'body': f'Comment {i}'}
        for i in range(50)
    ]
    
    # Sample to 20 comments
    sampled = scraper._apply_sampling(comments, 20)
    assert len(sampled) <= 20
    
    # Top comments should be included
    top_comment = max(sampled, key=lambda x: x['score'])
    assert top_comment['score'] == 100


def test_flatten_comments_helper(scraper):
    """Test comment extraction helper"""
    # Mock comment
    mock_comment = MagicMock()
    mock_comment.id = 'comment1'
    mock_comment.body = 'Test comment'
    mock_comment.author = 'test_user'
    mock_comment.score = 50
    mock_comment.created_utc = 1234567890
    mock_comment.is_submitter = False
    mock_comment.stickied = False
    mock_comment.edited = False
    mock_comment.controversiality = 0
    mock_comment.replies = []
    
    comment_data = scraper._extract_comment_data(mock_comment, depth=0)
    
    assert comment_data['id'] == 'comment1'
    assert comment_data['body'] == 'Test comment'
    assert comment_data['score'] == 50
    assert comment_data['depth'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
