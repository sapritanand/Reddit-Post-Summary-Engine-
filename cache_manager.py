"""
Cache Manager Module - SQLite-based caching for Reddit Analysis System
Handles caching of posts, comments, OCR results, and link content
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


class CacheManager:
    """Manages SQLite-based caching for expensive operations"""
    
    def __init__(self, db_path: str = 'reddit_analysis_cache.db', expiry_hours: int = 24):
        """
        Initialize cache manager with SQLite database
        
        Args:
            db_path: Path to SQLite database file
            expiry_hours: Number of hours before cache entries expire
        """
        self.db_path = db_path
        self.expiry_hours = expiry_hours
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Posts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS posts (
                        url TEXT PRIMARY KEY,
                        raw_data TEXT NOT NULL,
                        extracted_text TEXT,
                        enriched_data TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Comments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        comment_id TEXT PRIMARY KEY,
                        post_url TEXT NOT NULL,
                        raw_data TEXT NOT NULL,
                        enriched_data TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (post_url) REFERENCES posts(url)
                    )
                ''')
                
                # Link content table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS link_content (
                        url TEXT PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        source_domain TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # OCR results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ocr_results (
                        image_url TEXT PRIMARY KEY,
                        extracted_text TEXT NOT NULL,
                        method TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_posts_timestamp 
                    ON posts(timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_comments_post_url 
                    ON comments(post_url)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_link_timestamp 
                    ON link_content(timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_ocr_timestamp 
                    ON ocr_results(timestamp)
                ''')
                
                conn.commit()
                self.logger.info(f"Cache database initialized at {self.db_path}")
        
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def _is_expired(self, timestamp_str: str) -> bool:
        """
        Check if cache entry is expired
        
        Args:
            timestamp_str: Timestamp string from database
            
        Returns:
            True if expired, False otherwise
        """
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            expiry_time = datetime.now() - timedelta(hours=self.expiry_hours)
            return timestamp < expiry_time
        except (ValueError, TypeError):
            return True
    
    # Post caching methods
    
    def get_post_cache(self, post_url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached post data
        
        Args:
            post_url: Reddit post URL
            
        Returns:
            Cached post data dict or None if not found/expired
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT raw_data, extracted_text, enriched_data, timestamp FROM posts WHERE url = ?',
                    (post_url,)
                )
                result = cursor.fetchone()
                
                if result:
                    raw_data, extracted_text, enriched_data, timestamp = result
                    
                    # Check if expired
                    if self._is_expired(timestamp):
                        self.logger.debug(f"Cache expired for post: {post_url}")
                        self.delete_post_cache(post_url)
                        return None
                    
                    self.logger.info(f"Cache hit for post: {post_url}")
                    return {
                        'raw_data': json.loads(raw_data),
                        'extracted_text': extracted_text,
                        'enriched_data': json.loads(enriched_data) if enriched_data else None,
                        'timestamp': timestamp
                    }
                
                return None
        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            self.logger.error(f"Error retrieving post cache: {e}")
            return None
    
    def cache_post(self, post_url: str, raw_data: Dict[str, Any], 
                   extracted_text: Optional[str] = None,
                   enriched_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache post data
        
        Args:
            post_url: Reddit post URL
            raw_data: Raw post data from Reddit API
            extracted_text: Extracted text content
            enriched_data: Gemini-enriched data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO posts 
                       (url, raw_data, extracted_text, enriched_data, timestamp) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (
                        post_url,
                        json.dumps(raw_data),
                        extracted_text,
                        json.dumps(enriched_data) if enriched_data else None,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                self.logger.debug(f"Cached post: {post_url}")
                return True
        
        except (sqlite3.Error, TypeError) as e:
            self.logger.error(f"Error caching post: {e}")
            return False
    
    def delete_post_cache(self, post_url: str) -> bool:
        """Delete cached post and associated comments"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM posts WHERE url = ?', (post_url,))
                cursor.execute('DELETE FROM comments WHERE post_url = ?', (post_url,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting post cache: {e}")
            return False
    
    # OCR caching methods
    
    def get_ocr_cache(self, image_url: str) -> Optional[str]:
        """
        Retrieve cached OCR result
        
        Args:
            image_url: URL of the image
            
        Returns:
            Extracted text or None if not found/expired
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT extracted_text, timestamp FROM ocr_results WHERE image_url = ?',
                    (image_url,)
                )
                result = cursor.fetchone()
                
                if result:
                    extracted_text, timestamp = result
                    
                    if self._is_expired(timestamp):
                        self.logger.debug(f"OCR cache expired for: {image_url}")
                        self.delete_ocr_cache(image_url)
                        return None
                    
                    self.logger.info(f"OCR cache hit for: {image_url}")
                    return extracted_text
                
                return None
        
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving OCR cache: {e}")
            return None
    
    def cache_ocr(self, image_url: str, extracted_text: str, method: str = 'tesseract') -> bool:
        """
        Cache OCR result
        
        Args:
            image_url: URL of the image
            extracted_text: Extracted text from OCR
            method: OCR method used (tesseract, easyocr)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO ocr_results 
                       (image_url, extracted_text, method, timestamp) 
                       VALUES (?, ?, ?, ?)''',
                    (image_url, extracted_text, method, datetime.now().isoformat())
                )
                conn.commit()
                self.logger.debug(f"Cached OCR result for: {image_url}")
                return True
        
        except sqlite3.Error as e:
            self.logger.error(f"Error caching OCR result: {e}")
            return False
    
    def delete_ocr_cache(self, image_url: str) -> bool:
        """Delete cached OCR result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM ocr_results WHERE image_url = ?', (image_url,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting OCR cache: {e}")
            return False
    
    # Link content caching methods
    
    def get_link_cache(self, url: str) -> Optional[Dict[str, str]]:
        """
        Retrieve cached link content
        
        Args:
            url: URL of the link
            
        Returns:
            Dict with title, content, source_domain or None if not found/expired
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT title, content, source_domain, timestamp FROM link_content WHERE url = ?',
                    (url,)
                )
                result = cursor.fetchone()
                
                if result:
                    title, content, source_domain, timestamp = result
                    
                    if self._is_expired(timestamp):
                        self.logger.debug(f"Link cache expired for: {url}")
                        self.delete_link_cache(url)
                        return None
                    
                    self.logger.info(f"Link cache hit for: {url}")
                    return {
                        'title': title,
                        'content': content,
                        'source_domain': source_domain
                    }
                
                return None
        
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving link cache: {e}")
            return None
    
    def cache_link(self, url: str, title: str, content: str, source_domain: str) -> bool:
        """
        Cache link content
        
        Args:
            url: URL of the link
            title: Page title
            content: Extracted content
            source_domain: Source domain
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO link_content 
                       (url, title, content, source_domain, timestamp) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (url, title, content, source_domain, datetime.now().isoformat())
                )
                conn.commit()
                self.logger.debug(f"Cached link content for: {url}")
                return True
        
        except sqlite3.Error as e:
            self.logger.error(f"Error caching link content: {e}")
            return False
    
    def delete_link_cache(self, url: str) -> bool:
        """Delete cached link content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM link_content WHERE url = ?', (url,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting link cache: {e}")
            return False
    
    # Utility methods
    
    def clear_expired_cache(self) -> Dict[str, int]:
        """
        Clear all expired cache entries
        
        Returns:
            Dict with counts of deleted entries by type
        """
        expiry_time = (datetime.now() - timedelta(hours=self.expiry_hours)).isoformat()
        counts = {'posts': 0, 'comments': 0, 'ocr_results': 0, 'link_content': 0}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for table in counts.keys():
                    cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (expiry_time,))
                    counts[table] = cursor.rowcount
                
                conn.commit()
                self.logger.info(f"Cleared expired cache entries: {counts}")
                return counts
        
        except sqlite3.Error as e:
            self.logger.error(f"Error clearing expired cache: {e}")
            return counts
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics
        
        Returns:
            Dict with counts of entries by type
        """
        stats = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                tables = ['posts', 'comments', 'ocr_results', 'link_content']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[table] = cursor.fetchone()[0]
                
                return stats
        
        except sqlite3.Error as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_all_cache(self) -> bool:
        """Clear all cache entries (use with caution)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM posts')
                cursor.execute('DELETE FROM comments')
                cursor.execute('DELETE FROM ocr_results')
                cursor.execute('DELETE FROM link_content')
                conn.commit()
                self.logger.warning("All cache entries cleared")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error clearing all cache: {e}")
            return False
