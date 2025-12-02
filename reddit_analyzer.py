"""
Reddit Analyzer - Main orchestration module
Coordinates all components for comprehensive Reddit post analysis
"""

import logging
import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import os
import concurrent.futures

from reddit_scraper import RedditScraper
from content_processor import ContentProcessor
from gemini_analyzer import GeminiAnalyzer
from cache_manager import CacheManager


class RedditAnalyzer:
    """Main orchestration class for Reddit analysis system"""
    
    def __init__(self, reddit_credentials: Dict[str, str], gemini_api_key: str,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Reddit Analyzer with all components
        
        Args:
            reddit_credentials: Dict with client_id, client_secret, user_agent
            gemini_api_key: Gemini API key
            config: Optional configuration dictionary
        """
        # Setup logging
        self._setup_logging(config)
        self.logger = logging.getLogger(__name__)
        
        # Store configuration
        self.config = config or self._load_default_config()
        
        # Initialize components
        self.logger.info("Initializing Reddit Analyzer...")
        
        try:
            # Reddit scraper
            self.scraper = RedditScraper(**reddit_credentials)
            
            # Gemini analyzer
            gemini_config = self.config.get('gemini', {})
            self.analyzer = GeminiAnalyzer(
                api_key=gemini_api_key,
                model=gemini_config.get('model', 'models/gemini-2.5-flash'),
                temperature=gemini_config.get('temperature', 0.3),
                max_tokens=gemini_config.get('max_tokens', 8192)
            )

            # Content processor
            processor_config = self.config.get('processing', {})
            self.processor = ContentProcessor(
                ocr_language=processor_config.get('ocr_language', 'en'),
                link_timeout=processor_config.get('link_fetch_timeout', 10),
                use_easyocr=processor_config.get('use_easyocr', False),
                skip_ocr_if_unavailable=processor_config.get('skip_ocr_if_unavailable', True),
                use_gemini_vision=processor_config.get('use_gemini_vision', True),
                gemini_api_key=gemini_api_key,
                gemini_model=gemini_config.get('model', 'models/gemini-2.5-flash')
            )
            
            # Cache manager
            cache_config = self.config.get('processing', {})
            self.cache = CacheManager(
                expiry_hours=cache_config.get('cache_expiry_hours', 24)
            )
            
            self.logger.info("Reddit Analyzer initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit Analyzer: {e}")
            raise
    
    @classmethod
    def from_config_file(cls, config_path: str = 'config.yaml'):
        """
        Create RedditAnalyzer from configuration file
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            RedditAnalyzer instance
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        reddit_creds = config['reddit']
        gemini_key = config['gemini']['api_key']
        
        return cls(reddit_creds, gemini_key, config)
    
    @classmethod
    def from_env(cls, config_path: str = 'config.yaml'):
        """
        Create RedditAnalyzer using environment variables for credentials
        
        Args:
            config_path: Path to YAML config file for other settings
            
        Returns:
            RedditAnalyzer instance
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        reddit_creds = {
            'client_id': os.getenv('REDDIT_CLIENT_ID'),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'user_agent': os.getenv('REDDIT_USER_AGENT')
        }
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Load other config from file
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        
        return cls(reddit_creds, gemini_key, config)
    
    def analyze_post_url(self, reddit_post_url: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Main analysis pipeline for a Reddit post
        
        Args:
            reddit_post_url: URL of Reddit post to analyze
            use_cache: Whether to use cached data
            
        Returns:
            Complete analysis result dictionary
        """
        self.logger.info(f"Starting analysis of post: {reddit_post_url}")
        start_time = datetime.now()
        
        try:
            # Check cache first
            if use_cache:
                cached_result = self.cache.get_post_cache(reddit_post_url)
                if cached_result and cached_result.get('enriched_data'):
                    self.logger.info("Using cached analysis")
                    return self._format_cached_result(cached_result)
            
            # Step 1: Scrape post data
            self.logger.info("Step 1: Fetching post data from Reddit...")
            post_data = self.scraper.fetch_post(reddit_post_url)
            
            # Step 2: Process content (OCR, link extraction)
            self.logger.info("Step 2: Processing post content...")
            post_data = self._extract_post_content(post_data)
            
            # Cache raw post data
            self.cache.cache_post(reddit_post_url, post_data, post_data.get('extracted_text'))
            
            # Step 3: Fetch comments
            self.logger.info("Step 3: Fetching comments...")
            comments = self.scraper.fetch_comments(
                reddit_post_url,
                limit=self.config.get('processing', {}).get('max_comments_process', 100)
            )
            
            # Step 4: Enrich post with Gemini
            self.logger.info("Step 4: Analyzing post with Gemini...")
            post_analysis = self.analyzer.analyze_post(
                post_text=post_data.get('extracted_text', ''),
                subreddit=post_data.get('subreddit', ''),
                title=post_data.get('title', ''),
                metadata=post_data
            )
            
            # Merge analysis into post data
            enriched_post = {**post_data, **post_analysis}
            
            # Step 5: Filter and enrich comments
            self.logger.info("Step 5: Analyzing comments with Gemini...")
            
            # Flatten comment tree for processing
            flat_comments = self._flatten_comments(comments)

            # Pre-filter comments heuristically BEFORE Gemini to save tokens
            max_pre = self.config.get('processing', {}).get('max_comments_process', 100)
            top_comments = self._pre_filter_comments(flat_comments, max_pre)
            
            # Analyze comments with parallel processing if enabled
            if top_comments:
                post_context = post_analysis.get('summaries', {}).get('one_sentence', post_data.get('title', ''))
                batch_size = self.config.get('processing', {}).get('batch_size', 20)
                use_parallel = self.config.get('processing', {}).get('use_parallel_processing', True)
                
                if use_parallel and len(top_comments) > batch_size:
                    enriched_comments = self._analyze_comments_parallel(top_comments, post_context, batch_size)
                else:
                    enriched_comments = self.analyzer.analyze_comments_batch(
                        top_comments,
                        post_context,
                        batch_size=batch_size
                    )
            else:
                enriched_comments = []
            
            # Step 6: Filter by quality threshold
            quality_threshold = self.config.get('processing', {}).get('comment_quality_threshold', 2.0)
            # Debug: log comment quality scores
            for c in enriched_comments:
                qs = c.get('quality_score', 0)
                self.logger.info(f"DEBUG: Comment {c.get('id','?')} quality_score={qs}")
            quality_comments = self._filter_quality_comments(enriched_comments, quality_threshold)
            
            self.logger.info(f"Filtered to {len(quality_comments)} high-quality comments (threshold={quality_threshold})")
            
            # Step 7: Synthesize final analysis
            self.logger.info("Step 6: Generating synthesis...")
            synthesis = self.analyzer.synthesize_analysis(enriched_post, quality_comments)
            
            # Step 8: Build final output
            result = self._build_final_output(
                post_data=enriched_post,
                post_analysis=post_analysis,
                comments=enriched_comments,
                quality_comments=quality_comments,
                synthesis=synthesis,
                start_time=start_time
            )
            
            # Cache enriched result
            self.cache.cache_post(
                reddit_post_url,
                post_data,
                post_data.get('extracted_text'),
                result
            )
            
            # Save to file if configured
            if self.config.get('output', {}).get('save_to_file', True):
                self._save_output(result, reddit_post_url)
            
            self.logger.info(f"Analysis completed in {(datetime.now() - start_time).total_seconds():.1f}s")
            return result
        
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            raise
    
    def analyze_multiple_posts(self, post_urls: List[str], use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Analyze multiple posts in batch
        
        Args:
            post_urls: List of Reddit post URLs
            use_cache: Whether to use cached data
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, url in enumerate(post_urls, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing post {i}/{len(post_urls)}")
            self.logger.info(f"{'='*60}\n")
            
            try:
                result = self.analyze_post_url(url, use_cache=use_cache)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to analyze {url}: {e}")
                results.append({
                    'error': str(e),
                    'post_url': url,
                    'success': False
                })
        
        return results
    
    def _extract_post_content(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from post using ContentProcessor
        
        Args:
            post_data: Raw post data
            
        Returns:
            Post data with extracted_text
        """
        # Check cache for OCR and link content
        content_type = self.processor.detect_content_type(post_data)
        
        if content_type == 'image':
            image_url = post_data.get('url')
            cached_ocr = self.cache.get_ocr_cache(image_url)
            if cached_ocr:
                self.logger.info("Using cached OCR result")
                post_data['extracted_text'] = f"Title: {post_data.get('title', '')}\n\nImage Text: {cached_ocr}"
                return post_data
        
        elif content_type == 'link':
            link_url = post_data.get('url')
            cached_link = self.cache.get_link_cache(link_url)
            if cached_link:
                self.logger.info("Using cached link content")
                post_data['extracted_text'] = f"Title: {post_data.get('title', '')}\n\nLinked Article: {cached_link['title']}\n{cached_link['content']}"
                return post_data
        
        # Process content
        post_data = self.processor.process_post(post_data)
        
        # Cache results
        if content_type == 'image':
            image_url = post_data.get('url')
            ocr_text = post_data.get('extracted_text', '')
            if 'Image Text:' in ocr_text:
                ocr_only = ocr_text.split('Image Text:')[1].strip()
                self.cache.cache_ocr(image_url, ocr_only)
        
        elif content_type == 'link':
            # Cache link content if available from processor
            link_url = post_data.get('url')
            link_content = post_data.get('link_content')
            if link_url and link_content and all(k in link_content for k in ('title', 'text', 'source_domain')):
                try:
                    self.cache.cache_link(
                        link_url,
                        link_content['title'],
                        link_content['text'],
                        link_content['source_domain']
                    )
                except Exception as e:
                    self.logger.debug(f"Link caching skipped: {e}")
        
        return post_data

    def _pre_filter_comments(self, comments: List[Dict[str, Any]], max_count: int) -> List[Dict[str, Any]]:
        """
        Heuristically filter comments before Gemini to save tokens.
        Scoring factors: length (20+ words), score, and depth (prefer shallow).
        """
        if not comments:
            return []
        
        def heuristic_score(c: Dict[str, Any]) -> float:
            body = c.get('body', '') or ''
            words = len(body.split())
            length_bonus = 1.0 if words >= 20 else (words / 20.0)
            score = float(c.get('score', 0))
            depth_penalty = 1.0 - min(float(c.get('depth', 0)) * 0.05, 0.5)
            return (length_bonus * 0.5 + depth_penalty * 0.3) + (score / 1000.0)  # normalize score
        
        ranked = sorted(comments, key=heuristic_score, reverse=True)
        return ranked[:max_count]
    
    def _flatten_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flatten nested comment tree to list
        
        Args:
            comments: Nested comment structure
            
        Returns:
            Flat list of comments
        """
        flat = []
        
        def flatten_recursive(comment_list):
            for comment in comment_list:
                # Add comment without replies
                comment_copy = {k: v for k, v in comment.items() if k != 'replies'}
                flat.append(comment_copy)
                
                # Process replies recursively
                if 'replies' in comment and comment['replies']:
                    flatten_recursive(comment['replies'])
        
        flatten_recursive(comments)
        return flat
    
    def _analyze_comments_parallel(self, comments: List[Dict[str, Any]], 
                                   post_context: str, batch_size: int = 20) -> List[Dict[str, Any]]:
        """
        Analyze comments in parallel batches for faster processing
        
        Args:
            comments: List of comments to analyze
            post_context: Summary of post for context
            batch_size: Size of each batch
            
        Returns:
            List of enriched comment dictionaries
        """
        # Split into batches
        batches = [comments[i:i+batch_size] for i in range(0, len(comments), batch_size)]
        self.logger.info(f"Processing {len(batches)} batches in parallel (max 3 concurrent)...")
        
        enriched_comments = []
        
        # Process batches in parallel (max 3 concurrent to respect rate limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {
                executor.submit(self.analyzer.analyze_comments_batch, batch, post_context, batch_size): i
                for i, batch in enumerate(batches)
            }
            
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    enriched_comments.extend(batch_results)
                    self.logger.info(f"Completed batch {batch_num + 1}/{len(batches)}")
                except Exception as e:
                    self.logger.error(f"Batch {batch_num + 1} failed: {e}")
        
        return enriched_comments
    
    def _filter_quality_comments(self, comments: List[Dict[str, Any]], 
                                 threshold: float = 5.0) -> List[Dict[str, Any]]:
        """
        Filter comments by quality score
        
        Args:
            comments: List of enriched comments
            threshold: Minimum quality score
            
        Returns:
            Filtered list of comments
        """
        return [c for c in comments if c.get('quality_score', 0) >= threshold]
    
    def _build_final_output(self, post_data: Dict, post_analysis: Dict,
                           comments: List[Dict], quality_comments: List[Dict],
                           synthesis: Dict, start_time: datetime) -> Dict[str, Any]:
        """Build final structured output"""
        
        # Calculate detailed comment statistics
        comment_stats = self._calculate_comment_statistics(comments, quality_comments)
        sentiment_counts = comment_stats['sentiment_counts']
        intent_counts = comment_stats['intent_counts']
        
        # Normalize synthesis keys to match spec where needed
        synth = dict(synthesis)
        if 'community_consensus' in synth:
            cc = dict(synth['community_consensus'])
            if 'validation' not in cc and 'validation_status' in cc:
                cc['validation'] = cc.get('validation_status')
            synth['community_consensus'] = cc
        if 'context' not in synth and 'context_and_background' in synth:
            synth['context'] = synth.get('context_and_background')

        # Build output structure
        output = {
            'metadata': {
                'post_url': post_data.get('permalink', ''),
                'post_id': post_data.get('id', ''),
                'subreddit': post_data.get('subreddit', ''),
                'author': post_data.get('author', ''),
                'timestamp': post_data.get('created_utc', ''),
                'score': post_data.get('score', 0),
                'upvote_ratio': post_data.get('upvote_ratio', 0),
                'comment_count': post_data.get('num_comments', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_duration_seconds': (datetime.now() - start_time).total_seconds()
            },
            
            'post_analysis': {
                'content_type': post_data.get('content_type', 'unknown'),
                'extracted_text': post_data.get('extracted_text', ''),
                'entities': post_analysis.get('entities', {}),
                'sentiment': post_analysis.get('sentiment', {}),
                'core_issue': post_analysis.get('core_issue', ''),
                'irony_or_contradiction': post_analysis.get('irony_or_contradiction'),
                'summaries': post_analysis.get('summaries', {}),
                'classification': post_analysis.get('classification', {})
            },
            
            'comments_analysis': {
                'total_fetched': len(comments),
                'total_processed': len(comments),
                'high_quality_count': len(quality_comments),
                'high_quality_percentage': round((len(quality_comments) / len(comments) * 100) if comments else 0, 1),
                'sentiment_distribution': sentiment_counts,
                'intent_distribution': intent_counts,
                'theme_percentages': comment_stats.get('theme_percentages', {}),
                'tone_distribution': comment_stats.get('tone_distribution', {}),
                'top_comments': [
                    {
                        **c,
                        'text': c.get('body', c.get('text', ''))
                    }
                    for c in sorted(
                        quality_comments,
                        key=lambda x: x.get('relevance_score', 0) * x.get('score', 0),
                        reverse=True
                    )[:10]
                ],  # Top 10 most relevant
                'all_insights': self._extract_all_insights(quality_comments),
                'all_advice': self._extract_all_advice(quality_comments)
            },
            
            'synthesis': synth,
            
            'success': True
        }
        
        return output
    
    def _extract_all_insights(self, comments: List[Dict]) -> List[str]:
        """Extract all key insights from comments"""
        insights = []
        for comment in comments:
            insights.extend(comment.get('key_insights', []))
        return list(set(insights))  # Remove duplicates
    
    def _extract_all_advice(self, comments: List[Dict]) -> List[str]:
        """Extract all actionable advice from comments"""
        advice = []
        for comment in comments:
            advice.extend(comment.get('actionable_advice', []))
        return list(set(advice))
    
    def _calculate_comment_statistics(self, all_comments: List[Dict], 
                                      quality_comments: List[Dict]) -> Dict[str, Any]:
        """
        Calculate detailed comment statistics including themes and sentiment
        
        Args:
            all_comments: All enriched comments
            quality_comments: Filtered high-quality comments
            
        Returns:
            Dictionary with detailed statistics
        """
        stats = {
            'total_analyzed': len(all_comments),
            'high_quality_count': len(quality_comments),
            'sentiment_counts': {},
            'intent_counts': {},
            'theme_distribution': {},
            'tone_distribution': {}
        }
        
        # Count sentiments
        for comment in all_comments:
            sentiment = comment.get('sentiment', {}).get('toward_op', 'neutral')
            stats['sentiment_counts'][sentiment] = stats['sentiment_counts'].get(sentiment, 0) + 1
            
            # Count overall tone
            tone = comment.get('sentiment', {}).get('overall_tone', 'neutral')
            stats['tone_distribution'][tone] = stats['tone_distribution'].get(tone, 0) + 1
        
        # Count intents/themes
        for comment in all_comments:
            intent = comment.get('intent_primary', 'UNKNOWN')
            stats['intent_counts'][intent] = stats['intent_counts'].get(intent, 0) + 1
        
        # Calculate percentages for top themes
        total = len(all_comments) if all_comments else 1
        stats['theme_percentages'] = {
            theme: round((count / total) * 100, 1)
            for theme, count in sorted(
                stats['intent_counts'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
        
        return stats
    
    def _format_cached_result(self, cached_data: Dict) -> Dict[str, Any]:
        """Format cached data for output"""
        enriched = cached_data.get('enriched_data', {})
        enriched['metadata']['from_cache'] = True
        return enriched
    
    def _save_output(self, result: Dict[str, Any], post_url: str):
        """Save output to file"""
        try:
            output_config = self.config.get('output', {})
            output_dir = Path(output_config.get('output_directory', './analysis_results'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename from post ID
            post_id = result['metadata']['post_id']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            output_format = output_config.get('format', 'both')
            
            # Save JSON
            if output_format in ['json', 'both']:
                json_path = output_dir / f"{post_id}_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=output_config.get('json_indent', 2), ensure_ascii=False)
                self.logger.info(f"Saved JSON output to {json_path}")
            
            # Save Markdown
            if output_format in ['markdown', 'both']:
                md_path = output_dir / f"{post_id}_{timestamp}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(self._generate_markdown_report(result))
                self.logger.info(f"Saved Markdown output to {md_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")
    
    def _generate_markdown_report(self, result: Dict[str, Any]) -> str:
        """Generate human-readable markdown report"""
        md = []
        
        # Header
        md.append(f"# Reddit Post Analysis Report\n")
        md.append(f"**Subreddit:** r/{result['metadata']['subreddit']}")
        md.append(f"**Author:** u/{result['metadata']['author']}")
        md.append(f"**Score:** {result['metadata']['score']} ({result['metadata'].get('upvote_ratio', 0)*100:.0f}% upvoted)")
        md.append(f"**Comments:** {result['metadata']['comment_count']}")
        md.append(f"**Posted:** {result['metadata']['timestamp']}")
        md.append(f"**Analyzed:** {result['metadata']['analysis_timestamp']}\n")
        
        # Executive Summary
        md.append(f"## Executive Summary\n")
        md.append(result['synthesis']['executive_summary'])
        md.append("")
        
        # Post Analysis
        md.append(f"## Post Analysis\n")
        md.append(f"**Type:** {result['post_analysis']['content_type']}")
        md.append(f"**Core Issue:** {result['post_analysis']['core_issue']}\n")
        
        md.append(f"### Summary")
        md.append(result['post_analysis']['summaries'].get('analytical', ''))
        md.append("")
        
        md.append(f"### Sentiment")
        sentiment = result['post_analysis']['sentiment']
        md.append(f"- **Primary:** {sentiment.get('primary', 'N/A')}")
        md.append(f"- **Intensity:** {sentiment.get('intensity', 'N/A')}")
        md.append(f"- **Tone:** {sentiment.get('emotional_tone', 'N/A')}\n")
        
        # Community Response
        md.append(f"## Community Response\n")
        consensus = result['synthesis']['community_consensus']
        md.append(f"**Validation Status:** {consensus.get('validation_status', 'N/A')}")
        md.append(f"**Agreement Level:** {consensus.get('agreement_level', 'N/A')}\n")
        
        # Comment Themes (if available)
        if result['comments_analysis'].get('theme_percentages'):
            md.append(f"### Comment Themes\n")
            for theme, pct in result['comments_analysis']['theme_percentages'].items():
                md.append(f"- **{theme}**: {pct}%")
            md.append("")
        
        # Key Insights
        if result['synthesis'].get('key_insights'):
            md.append(f"### Key Insights\n")
            for insight in result['synthesis']['key_insights']:
                md.append(f"- {insight}")
            md.append("")
        
        # Recommended Actions
        if result['synthesis'].get('recommended_actions'):
            md.append(f"### Recommended Actions\n")
            for action in result['synthesis']['recommended_actions']:
                md.append(f"- {action}")
            md.append("")
        
        # Top Comments
        md.append(f"## Top Comments\n")
        for i, comment in enumerate(result['comments_analysis']['top_comments'][:5], 1):
            md.append(f"### Comment {i} (Score: {comment.get('score', 0)})")
            md.append(f"**Intent:** {comment.get('intent_primary', 'N/A')}")
            md.append(f"**Sentiment toward OP:** {comment.get('sentiment', {}).get('toward_op', 'N/A')}")
            md.append(f"\n{comment.get('body', '')[:500]}...\n")
        
        return '\n'.join(md)
    
    def _setup_logging(self, config: Optional[Dict]):
        """Setup logging configuration"""
        log_config = config.get('logging', {}) if config else {}
        
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create logs directory if logging to file
        log_file = log_config.get('log_file')
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(level=log_level, format=log_format)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'processing': {
                'cache_expiry_hours': 24,
                'max_comments_process': 100,
                'comment_quality_threshold': 2.0,
                'batch_size': 20,
                'ocr_language': 'en',
                'link_fetch_timeout': 10,
                'use_gemini_vision': True,
                'use_parallel_processing': True
            },
            'output': {
                'format': 'both',
                'save_to_file': True,
                'output_directory': './analysis_results',
                'json_indent': 2
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.cache.get_cache_stats()
    
    def clear_cache(self, expired_only: bool = True) -> Dict[str, int]:
        """
        Clear cache entries
        
        Args:
            expired_only: If True, only clear expired entries
            
        Returns:
            Dict with counts of cleared entries
        """
        if expired_only:
            return self.cache.clear_expired_cache()
        else:
            self.cache.clear_all_cache()
            return {'message': 'All cache cleared'}
