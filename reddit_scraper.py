"""
Reddit Scraper Module - PRAW-based Reddit data extraction
Fetches posts and comments with hierarchy preservation
"""

import praw
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import re
from urllib.parse import urlparse


class RedditScraper:
    """Handles Reddit API interactions using PRAW"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        Initialize Reddit API client
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Test authentication
            self.reddit.user.me()
            self.logger.info("Reddit API initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Reddit API initialization failed: {e}")
            raise
    
    def fetch_post(self, post_url: str) -> Dict[str, Any]:
        """
        Fetch post data from Reddit
        
        Args:
            post_url: URL of the Reddit post
            
        Returns:
            Dictionary containing post data
        """
        try:
            # Extract ID from URL and fetch by id to avoid redirect/alias issues
            post_id, slug_keywords = self._extract_post_id_and_slug(post_url)
            if not post_id:
                # Fallback to URL if ID not found
                submission = self.reddit.submission(url=post_url)
            else:
                submission = self.reddit.submission(id=post_id)

            # Basic debug validation vs slug keywords
            fetched_title = (submission.title or '').lower()
            if slug_keywords and not any(k in fetched_title for k in slug_keywords):
                self.logger.warning(
                    f"Potential mismatch: URL keywords {slug_keywords} not in fetched title '{submission.title}'"
                )
            self.logger.info(
                f"DEBUG: Fetching post ID: {submission.id}; Title: {submission.title}; Subreddit: {submission.subreddit.display_name}"
            )
            
            # Fetch post data
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'selftext': submission.selftext,
                'author': str(submission.author) if submission.author else '[deleted]',
                'subreddit': str(submission.subreddit),
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'is_self': submission.is_self,
                'link_flair_text': submission.link_flair_text,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'stickied': submission.stickied,
                'locked': submission.locked,
            }
            
            # Handle different post types
            if hasattr(submission, 'is_video') and submission.is_video:
                post_data['content_type'] = 'video'
                post_data['video_url'] = submission.url
            elif hasattr(submission, 'is_gallery') and submission.is_gallery:
                post_data['content_type'] = 'gallery'
                post_data['gallery_data'] = self._extract_gallery_urls(submission)
            elif submission.is_self:
                post_data['content_type'] = 'text'
            else:
                post_data['content_type'] = self._detect_url_type(submission.url)
            
            self.logger.info(f"Fetched post: {submission.id} ({post_data['content_type']})")
            return post_data
        
        except Exception as e:
            self.logger.error(f"Error fetching post {post_url}: {e}")
            raise
    
    def _detect_url_type(self, url: str) -> str:
        """
        Detect content type from URL
        
        Args:
            url: Post URL
            
        Returns:
            Content type string
        """
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return 'image'
        elif any(domain in url_lower for domain in ['i.redd.it', 'i.imgur.com']):
            return 'image'
        elif any(domain in url_lower for domain in ['v.redd.it', 'youtube.com', 'youtu.be']):
            return 'video'
        else:
            return 'link'
    
    def _extract_gallery_urls(self, submission) -> List[str]:
        """
        Extract image URLs from gallery post
        
        Args:
            submission: PRAW submission object
            
        Returns:
            List of image URLs
        """
        urls = []
        try:
            if hasattr(submission, 'media_metadata'):
                for item_id in submission.gallery_data['items']:
                    media_id = item_id['media_id']
                    media_item = submission.media_metadata[media_id]
                    
                    # Get highest quality image
                    if 's' in media_item:
                        url = media_item['s']['u']
                        urls.append(url)
        except Exception as e:
            self.logger.warning(f"Error extracting gallery URLs: {e}")
        
        return urls

    def _extract_post_id_and_slug(self, url: str) -> (Optional[str], List[str]):
        """Extract the Reddit post ID and slug keywords from a Reddit URL.
        Supports formats like:
        - https://www.reddit.com/r/sub/comments/POSTID/slug/
        - https://redd.it/POSTID
        - https://www.reddit.com/comments/POSTID/slug/
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            # Try standard /comments/{id}/ pattern
            m = re.search(r"/comments/([a-z0-9]+)/?([^/]*)", path, re.IGNORECASE)
            post_id = None
            slug_keywords: List[str] = []
            if m:
                post_id = m.group(1)
                slug = (m.group(2) or '').lower()
                # Extract simple keywords from slug for validation
                slug_keywords = [w for w in re.split(r"[-_]+", slug) if len(w) >= 4]
            else:
                # Try redd.it shortlink
                m2 = re.search(r"^/([a-z0-9]{5,8})/?", path, re.IGNORECASE)
                if parsed.netloc in {"redd.it", "www.redd.it"} and m2:
                    post_id = m2.group(1)
            return post_id, slug_keywords
        except Exception:
            return None, []
    
    def fetch_comments(self, post_url: str, limit: Optional[int] = None, 
                      strategy: str = 'top') -> List[Dict[str, Any]]:
        """
        Fetch comments with hierarchy preserved
        
        Args:
            post_url: URL of the Reddit post
            limit: Maximum number of comments to fetch (None = all)
            strategy: Sampling strategy ('top', 'best', 'new')
            
        Returns:
            List of comment dictionaries with hierarchy
        """
        try:
            post_id, _ = self._extract_post_id_and_slug(post_url)
            submission = self.reddit.submission(id=post_id) if post_id else self.reddit.submission(url=post_url)
            comment_count = submission.num_comments
            
            # Determine sampling strategy
            sampling_strategy = self.determine_sampling_strategy(comment_count)
            self.logger.info(f"Using sampling strategy: {sampling_strategy} for {comment_count} comments")
            
            # Replace MoreComments objects (0 means fully expand)
            more_limit = sampling_strategy['more_limit'] if sampling_strategy['more_limit'] is not None else 0
            submission.comments.replace_more(limit=more_limit)
            
            # Sort comments
            if strategy == 'new':
                submission.comment_sort = 'new'
            # Always use the submission.comments forest after sorting
            comment_forest = submission.comments
            
            # Debug: total comments in flattened list
            all_flat = list(submission.comments.list())
            self.logger.info(f"DEBUG: Found {len(all_flat)} total comments after expansion")
            if len(all_flat) == 0:
                self.logger.warning(f"WARNING: No comments found for post: {submission.id}; score={submission.score}; created_utc={submission.created_utc}")
            
            # Extract comments with hierarchy
            comments = []
            for comment in comment_forest:
                if isinstance(comment, praw.models.Comment):
                    comment_data = self._extract_comment_data(comment, depth=0)
                    comments.append(comment_data)
            
            # Apply limit if specified
            if limit:
                comments = comments[:limit]
            elif sampling_strategy['max_comments']:
                comments = self._apply_sampling(comments, sampling_strategy['max_comments'])
            
            self.logger.info(f"Fetched {len(comments)} top-level comments; flattened={len(all_flat)}")
            return comments
        
        except Exception as e:
            self.logger.error(f"Error fetching comments for {post_url}: {e}")
            return []
    
    def _extract_comment_data(self, comment, depth: int = 0) -> Dict[str, Any]:
        """
        Extract comment data recursively
        
        Args:
            comment: PRAW comment object
            depth: Depth in comment tree
            
        Returns:
            Dictionary containing comment data with replies
        """
        comment_data = {
            'id': comment.id,
            'body': comment.body,
            'author': str(comment.author) if comment.author else '[deleted]',
            'score': comment.score,
            'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
            'depth': depth,
            'is_submitter': comment.is_submitter,
            'stickied': comment.stickied,
            'edited': bool(comment.edited),
            'controversiality': comment.controversiality,
            'replies': []
        }
        
        # Extract replies recursively (limit depth to prevent excessive nesting)
        if depth < 5 and hasattr(comment, 'replies'):
            for reply in comment.replies:
                if isinstance(reply, praw.models.Comment):
                    reply_data = self._extract_comment_data(reply, depth + 1)
                    comment_data['replies'].append(reply_data)
        
        return comment_data
    
    def determine_sampling_strategy(self, comment_count: int) -> Dict[str, Any]:
        """
        Determine comment sampling strategy based on volume
        
        Args:
            comment_count: Total number of comments
            
        Returns:
            Dictionary with sampling parameters
        """
        if comment_count < 50:
            # Process all comments
            return {
                'strategy': 'all',
                'max_comments': None,
                'more_limit': 0  # Replace all MoreComments
            }
        elif comment_count < 500:
            # Top 20 + strategic sampling
            return {
                'strategy': 'top_plus_sampling',
                'max_comments': 100,
                'more_limit': 0  # Expand fully; rely on our own pre-filtering later
            }
        else:
            # Top 50 + strategic clustering
            return {
                'strategy': 'top_clustering',
                'max_comments': 200,
                'more_limit': 0  # Expand fully; rely on filtering later
            }
    
    def _apply_sampling(self, comments: List[Dict[str, Any]], 
                       max_comments: int) -> List[Dict[str, Any]]:
        """
        Apply intelligent sampling to comment list
        
        Args:
            comments: List of comment dictionaries
            max_comments: Maximum number of comments to keep
            
        Returns:
            Sampled list of comments
        """
        if len(comments) <= max_comments:
            return comments
        
        # Sort by score (descending)
        sorted_comments = sorted(comments, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top comments
        top_count = int(max_comments * 0.7)  # 70% top comments
        sampled = sorted_comments[:top_count]
        
        # Add diverse samples from remaining
        remaining = sorted_comments[top_count:]
        if remaining:
            # Sample evenly from remaining comments
            step = len(remaining) // max(1, (max_comments - top_count))
            step = max(1, step)
            sampled.extend(remaining[::step][:max_comments - top_count])
        
        self.logger.debug(f"Sampled {len(sampled)} comments from {len(comments)}")
        return sampled
    
    def get_post_metadata(self, post_url: str) -> Dict[str, Any]:
        """
        Get lightweight post metadata without full content
        
        Args:
            post_url: URL of the Reddit post
            
        Returns:
            Dictionary with basic post metadata
        """
        try:
            submission = self.reddit.submission(url=post_url)
            
            return {
                'id': submission.id,
                'title': submission.title,
                'subreddit': str(submission.subreddit),
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
            }
        
        except Exception as e:
            self.logger.error(f"Error fetching post metadata: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Test Reddit API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to access Reddit front page
            self.reddit.subreddit('all').hot(limit=1)
            self.logger.info("Reddit API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Reddit API connection test failed: {e}")
            return False
