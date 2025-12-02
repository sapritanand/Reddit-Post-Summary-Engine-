"""
Gemini Analyzer Module - AI-powered analysis using Google's Gemini API
Handles post enrichment, comment analysis, and synthesis
"""

import logging
import json
import re
import time
from typing import Dict, List, Any, Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.error("google-generativeai not available - Gemini features will be disabled")


class GeminiAnalyzer:
    """Handles AI analysis using Gemini API"""
    
    # Prompt templates
    POST_ANALYSIS_PROMPT = """You are analyzing a Reddit post. Extract and structure the following information.

POST CONTENT:
{post_text}

SUBREDDIT: {subreddit}
TITLE: {title}

Return a JSON object with this exact structure:
{{
  "entities": {{
    "organizations": ["list of organizations mentioned"],
    "people": ["list of people mentioned"],
    "products": ["list of products/services mentioned"],
    "locations": ["list of locations mentioned"]
  }},
  "sentiment": {{
    "primary": "positive/negative/neutral/mixed",
    "intensity": "low/medium/high",
    "emotional_tone": "frustrated/humorous/angry/hopeful/etc",
    "targets": {{"entity": "positive/negative/neutral"}}
  }},
  "core_issue": "brief description of the main issue or topic",
  "irony_or_contradiction": "any irony or contradiction if present, otherwise null",
  "summaries": {{
    "one_sentence": "ultra-concise one sentence summary",
    "actionable": "2-3 sentence summary focused on actionable information",
    "analytical": "detailed paragraph providing context and analysis"
  }},
  "classification": {{
    "type": "complaint/question/discussion/news/creative/other",
    "topics": ["main subject areas"]
  }}
}}

Respond with ONLY the JSON object, no additional text."""
    
    COMMENTS_ANALYSIS_PROMPT = """Analyze these Reddit comments in the context of the original post.

POST SUMMARY: {post_summary}

COMMENTS (with scores):
{comments_text}

For EACH comment, analyze and return a JSON array with this structure:
[
  {{
    "comment_id": "comment identifier",
    "quality_score": 7.5,
    "intent_primary": "SUPPORTIVE/SOLUTION/EXPLANATORY/ANECDOTAL/HUMOROUS/CRITICAL/QUESTIONING",
    "intent_secondary": "secondary intent if applicable",
    "sentiment": {{
      "toward_op": "supportive/neutral/critical",
      "toward_subject": "positive/negative/neutral",
      "overall_tone": "empathetic/cynical/helpful/etc"
    }},
    "key_insights": ["important insight 1", "insight 2"],
    "actionable_advice": ["practical advice if any"],
    "shared_experiences": ["relevant experiences shared"],
    "relevance_score": 8.5
  }}
]

Quality score (0-10) based on:
- Length and depth (20+ words = good)
- Upvote score (community validation)
- Contains actionable advice or valuable information
- Contains sources or references

Relevance score (0-10): How relevant and valuable is this comment to understanding the post.

Respond with ONLY the JSON array, no additional text."""
    
    SYNTHESIS_PROMPT = """Create a comprehensive analysis combining the post and its top comments.

POST DATA:
{post_data}

TOP COMMENTS DATA:
{comments_data}

Generate a final analysis as a JSON object:
{{
  "executive_summary": "2-3 sentence comprehensive overview",
  "key_issue": "the core problem or topic identified",
  "community_consensus": {{
    "validation_status": "validated/questioned/mixed/contradicted",
    "agreement_level": "high/medium/low",
    "top_solutions": ["ranked actionable solutions from comments"],
    "sentiment_breakdown": {{
      "supportive": 60,
      "critical": 30,
      "neutral": 10
    }}
  }},
  "context_and_background": "broader context provided by comments",
  "recommended_actions": ["prioritized list of 3-5 recommended actions - NEVER use N/A - adapt to post type: for entertainment posts suggest follow-ups/engagement/awareness uses; for problem posts suggest solutions; for informational posts suggest learning next steps"],
  "key_insights": ["most important takeaways - include frequency indicators when multiple comments mention same pattern (e.g., '15+ commenters reported X'), provide specific memorable examples, and explain why each insight matters"],
  "systemic_patterns": ["systemic issues or patterns identified, if any"],
  "notable_perspectives": ["unique or valuable perspectives shared"],
  "information_quality": {{
    "factual_accuracy": "high/medium/low/unknown",
    "expert_input": "whether expert perspectives were provided",
    "source_citations": "whether sources were cited"
  }},
  "comment_themes": {{"theme_name": count_of_comments}},
  "engagement_metrics": {{"humorous": percent, "concerned": percent, "informative": percent}}
}}

IMPORTANT GUIDANCE:
- For ENTERTAINMENT/DISCUSSION posts: Suggest follow-up questions, related topics to explore, ways to use insights for awareness/education, community engagement ideas
- For PROBLEM/HELP posts: Provide direct solutions, resources, step-by-step action plans
- For INFORMATIONAL posts: Suggest learning next steps, related topics, practical applications
- For KEY INSIGHTS: Count how many comments mention each pattern and include specific examples
- ALWAYS provide actionable suggestions - NEVER use "N/A" or dismissive language

Respond with ONLY the JSON object, no additional text."""
    
    def __init__(self, api_key: str, model: str = 'models/gemini-2.5-flash',
                 temperature: float = 0.3, max_tokens: int = 8192):
        """
        Initialize Gemini API client
        
        Args:
            api_key: Gemini API key
            model: Model name to use (e.g., 'models/gemini-1.5-flash', 'models/gemini-1.5-pro')
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum output tokens
        """
        if not GENAI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        # Ensure model name has 'models/' prefix
        if not model.startswith('models/'):
            model = f'models/{model}'
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.generation_config = {
            'temperature': temperature,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': max_tokens,
        }
        
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=self.generation_config
        )
        
        self.logger.info(f"Gemini API initialized with model: {model}")
    
    def analyze_post(self, post_text: str, subreddit: str, 
                    title: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze post content with Gemini
        
        Args:
            post_text: Extracted post text
            subreddit: Subreddit name
            title: Post title
            metadata: Additional metadata
            
        Returns:
            Enriched post data dictionary
        """
        try:
            # Create prompt
            prompt = self.POST_ANALYSIS_PROMPT.format(
                post_text=post_text[:10000],  # Truncate if too long
                subreddit=subreddit,
                title=title
            )
            
            self.logger.info("Sending post to Gemini for analysis...")
            
            # Generate response
            response = self._generate_with_retry(prompt)
            
            # Parse JSON response
            analysis = self._parse_json_response(response)
            
            if analysis:
                self.logger.info("Post analysis completed successfully")
                return analysis
            else:
                self.logger.warning("Failed to parse post analysis response")
                return self._get_default_post_analysis()
        
        except Exception as e:
            self.logger.error(f"Error analyzing post: {e}")
            return self._get_default_post_analysis()
    
    def analyze_comments_batch(self, comments_list: List[Dict[str, Any]], 
                               post_context: str, batch_size: int = 20) -> List[Dict[str, Any]]:
        """
        Analyze comments in batches
        
        Args:
            comments_list: List of comment dictionaries
            post_context: Summary of post for context
            batch_size: Number of comments per batch
            
        Returns:
            List of enriched comment dictionaries
        """
        enriched_comments = []
        
        # Process in batches
        for i in range(0, len(comments_list), batch_size):
            batch = comments_list[i:i + batch_size]
            
            try:
                # Create comments text
                comments_text = self._format_comments_for_prompt(batch)
                
                # Create prompt
                prompt = self.COMMENTS_ANALYSIS_PROMPT.format(
                    post_summary=post_context[:1000],
                    comments_text=comments_text
                )
                
                self.logger.info(f"Analyzing comment batch {i//batch_size + 1} ({len(batch)} comments)...")
                
                # Generate response
                response = self._generate_with_retry(prompt)
                
                # Parse JSON response
                analyses = self._parse_json_response(response)
                
                if analyses and isinstance(analyses, list):
                    # Match analyses with original comments
                    for j, analysis in enumerate(analyses):
                        if j < len(batch):
                            enriched_comment = {**batch[j], **analysis}
                            enriched_comments.append(enriched_comment)
                else:
                    # Fallback: add default analysis
                    for comment in batch:
                        enriched_comments.append({
                            **comment,
                            **self._get_default_comment_analysis(comment['id'])
                        })
                
                # Rate limiting pause
                time.sleep(1)
            
            except Exception as e:
                self.logger.error(f"Error analyzing comment batch: {e}")
                # Add default analysis for failed batch
                for comment in batch:
                    enriched_comments.append({
                        **comment,
                        **self._get_default_comment_analysis(comment['id'])
                    })
        
        self.logger.info(f"Completed analysis of {len(enriched_comments)} comments")
        return enriched_comments
    
    def synthesize_analysis(self, enriched_post: Dict[str, Any], 
                           enriched_comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize final comprehensive analysis
        
        Args:
            enriched_post: Post data with Gemini analysis
            enriched_comments: Comments with Gemini analysis
            
        Returns:
            Synthesis report dictionary
        """
        try:
            # Prepare post data summary
            post_data = json.dumps({
                'title': enriched_post.get('title', ''),
                'core_issue': enriched_post.get('core_issue', ''),
                'sentiment': enriched_post.get('sentiment', {}),
                'summaries': enriched_post.get('summaries', {})
            }, indent=2)
            
            # Prepare top comments summary
            top_comments = sorted(
                enriched_comments, 
                key=lambda x: x.get('relevance_score', 0) * x.get('score', 0),
                reverse=True
            )[:20]  # Top 20 most relevant
            
            comments_data = json.dumps([{
                'score': c.get('score', 0),
                'body': c.get('body', '')[:500],  # Truncate
                'intent': c.get('intent_primary', ''),
                'sentiment': c.get('sentiment', {}),
                'key_insights': c.get('key_insights', [])
            } for c in top_comments], indent=2)
            
            # Create prompt
            prompt = self.SYNTHESIS_PROMPT.format(
                post_data=post_data[:5000],
                comments_data=comments_data[:5000]
            )
            
            self.logger.info("Generating synthesis analysis...")
            
            # Generate response
            response = self._generate_with_retry(prompt)
            
            # Parse JSON response
            synthesis = self._parse_json_response(response)
            
            if synthesis:
                self.logger.info("Synthesis completed successfully")
                return synthesis
            else:
                self.logger.warning("Failed to parse synthesis response")
                return self._get_default_synthesis()
        
        except Exception as e:
            self.logger.error(f"Error generating synthesis: {e}")
            return self._get_default_synthesis()
    
    def _format_comments_for_prompt(self, comments: List[Dict[str, Any]]) -> str:
        """Format comments for inclusion in prompt"""
        formatted = []
        for i, comment in enumerate(comments, 1):
            score = comment.get('score', 0)
            body = comment.get('body', '')[:1000]  # Truncate long comments
            formatted.append(f"{i}. [Score: {score}] \"{body}\"")
        return '\n\n'.join(formatted)
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate response with retry logic
        
        Args:
            prompt: Prompt text
            max_retries: Maximum number of retries
            
        Returns:
            Response text
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                if response.text:
                    return response.text
                else:
                    self.logger.warning(f"Empty response on attempt {attempt + 1}")
            
            except Exception as e:
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception("All generation attempts failed")
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from Gemini response
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object/array in text
        json_obj_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        json_arr_pattern = r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'
        
        for pattern in [json_obj_pattern, json_arr_pattern]:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    # Validate it's a substantial object
                    if isinstance(parsed, (dict, list)) and len(str(parsed)) > 50:
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        self.logger.error(f"Failed to parse JSON from response: {response_text[:500]}")
        return None
    
    def _get_default_post_analysis(self) -> Dict[str, Any]:
        """Return default post analysis structure"""
        return {
            'entities': {'organizations': [], 'people': [], 'products': [], 'locations': []},
            'sentiment': {'primary': 'neutral', 'intensity': 'medium', 'emotional_tone': 'neutral', 'targets': {}},
            'core_issue': 'Unable to analyze',
            'irony_or_contradiction': None,
            'summaries': {
                'one_sentence': 'Analysis unavailable',
                'actionable': 'Analysis unavailable',
                'analytical': 'Analysis unavailable'
            },
            'classification': {'type': 'other', 'topics': []}
        }
    
    def _get_default_comment_analysis(self, comment_id: str) -> Dict[str, Any]:
        """Return default comment analysis structure"""
        return {
            'comment_id': comment_id,
            'quality_score': 5.0,
            'intent_primary': 'UNKNOWN',
            'intent_secondary': None,
            'sentiment': {'toward_op': 'neutral', 'toward_subject': 'neutral', 'overall_tone': 'neutral'},
            'key_insights': [],
            'actionable_advice': [],
            'shared_experiences': [],
            'relevance_score': 5.0
        }
    
    def _get_default_synthesis(self) -> Dict[str, Any]:
        """Return default synthesis structure"""
        return {
            'executive_summary': 'Synthesis unavailable',
            'key_issue': 'Unable to synthesize',
            'community_consensus': {
                'validation_status': 'unknown',
                'agreement_level': 'unknown',
                'top_solutions': [],
                'sentiment_breakdown': {}
            },
            'context_and_background': 'Unavailable',
            'recommended_actions': [],
            'key_insights': [],
            'systemic_patterns': [],
            'notable_perspectives': [],
            'information_quality': {
                'factual_accuracy': 'unknown',
                'expert_input': 'unknown',
                'source_citations': 'unknown'
            }
        }
    
    def test_connection(self) -> bool:
        """
        Test Gemini API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.model.generate_content("Respond with 'OK'")
            self.logger.info("Gemini API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Gemini API connection test failed: {e}")
            return False
