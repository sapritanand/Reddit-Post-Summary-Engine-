"""
Content Processor Module - Extracts text from various content types
Handles OCR for images and content extraction from links
"""

import logging
import requests
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
from io import BytesIO
import time

# Optional imports with fallbacks
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - image processing will be limited")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract not available - OCR will be disabled")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.debug("EasyOCR not available - falling back to Tesseract only")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup4 not available - link extraction will be limited")

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logging.debug("newspaper3k not available - falling back to BeautifulSoup")

# Optional Gemini Vision support
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.debug("google-generativeai not available - Gemini Vision disabled")


class ContentProcessor:
    """Processes different types of Reddit post content"""
    
    def __init__(self, ocr_language: str = 'en', link_timeout: int = 10, 
                 use_easyocr: bool = False, skip_ocr_if_unavailable: bool = True,
                 use_gemini_vision: bool = False, gemini_api_key: Optional[str] = None,
                 gemini_model: str = 'models/gemini-2.5-flash'):
        """
        Initialize content processor
        
        Args:
            ocr_language: Language for OCR (e.g., 'en', 'es', 'fr')
            link_timeout: Timeout for link fetching in seconds
            use_easyocr: Use EasyOCR instead of Tesseract (slower but more accurate)
            skip_ocr_if_unavailable: Skip OCR silently if no OCR engine is available
            use_gemini_vision: If True, use Gemini Vision to extract text from images
            gemini_api_key: Optional API key for Gemini Vision (falls back to env)
            gemini_model: Gemini model to use for vision tasks
        """
        self.logger = logging.getLogger(__name__)
        self.ocr_language = ocr_language
        self.link_timeout = link_timeout
        self.skip_ocr_if_unavailable = skip_ocr_if_unavailable
        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE
        self.use_gemini_vision = use_gemini_vision and GENAI_AVAILABLE and PIL_AVAILABLE
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model if gemini_model.startswith('models/') else f'models/{gemini_model}'
        
        # Initialize EasyOCR reader if requested
        self.easyocr_reader = None
        if self.use_easyocr:
            try:
                self.easyocr_reader = easyocr.Reader([ocr_language])
                self.logger.info("EasyOCR initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.use_easyocr = False
        
        # Setup requests session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Configure Gemini if enabled
        if self.use_gemini_vision:
            try:
                api_key = self.gemini_api_key
                if not api_key:
                    import os
                    api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.logger.info("Gemini Vision enabled for image text extraction")
                else:
                    self.use_gemini_vision = False
                    self.logger.warning("Gemini API key not provided; Vision disabled")
            except Exception as e:
                self.use_gemini_vision = False
                self.logger.warning(f"Failed to configure Gemini Vision: {e}")
    
    def detect_content_type(self, post_data: Dict[str, Any]) -> str:
        """
        Detect content type from post data
        
        Args:
            post_data: Post data dictionary
            
        Returns:
            Content type string
        """
        # Use pre-determined content type if available
        if 'content_type' in post_data:
            return post_data['content_type']
        
        # Detect from post properties
        if post_data.get('is_self'):
            return 'text'
        
        url = post_data.get('url', '').lower()
        
        if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return 'image'
        elif any(domain in url for domain in ['i.redd.it', 'i.imgur.com']):
            return 'image'
        elif any(domain in url for domain in ['v.redd.it', 'youtube.com', 'youtu.be']):
            return 'video'
        elif 'gallery_data' in post_data:
            return 'gallery'
        else:
            return 'link'
    
    def process_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing pipeline for post content
        
        Args:
            post_data: Post data dictionary from Reddit scraper
            
        Returns:
            Enhanced post data with extracted_text field
        """
        content_type = self.detect_content_type(post_data)
        self.logger.info(f"Processing post type: {content_type}")
        
        extracted_texts = []
        
        # Always include title
        if post_data.get('title'):
            extracted_texts.append(f"Title: {post_data['title']}")
        
        # Process based on content type
        if content_type == 'text':
            if post_data.get('selftext'):
                extracted_texts.append(f"Body: {post_data['selftext']}")
        
        elif content_type == 'image':
            image_url = post_data.get('url')
            if image_url:
                ocr_text = self.extract_from_image(image_url)
                if ocr_text:
                    extracted_texts.append(f"Image Text: {ocr_text}")
        
        elif content_type == 'gallery':
            gallery_urls = post_data.get('gallery_data', [])
            for idx, image_url in enumerate(gallery_urls[:5]):  # Limit to 5 images
                ocr_text = self.extract_from_image(image_url)
                if ocr_text:
                    extracted_texts.append(f"Image {idx+1} Text: {ocr_text}")
        
        elif content_type == 'link':
            link_url = post_data.get('url')
            if link_url:
                link_content = self.extract_from_link(link_url)
                if link_content:
                    # Attach raw link content for potential caching by caller
                    post_data['link_content'] = link_content
                    extracted_texts.append(f"Linked Article Title: {link_content.get('title', '')}")
                    if link_content.get('text'):
                        # Truncate long articles
                        article_text = link_content['text'][:5000]
                        extracted_texts.append(f"Article Content: {article_text}")
        
        elif content_type == 'video':
            self.logger.info("Video content type - skipping (unsupported)")
            extracted_texts.append("[Video content - unsupported for text extraction]")
        
        # Combine all extracted text
        post_data['extracted_text'] = '\n\n'.join(extracted_texts)
        post_data['content_type'] = content_type
        
        return post_data
    
    def extract_from_image(self, image_url: str) -> Optional[str]:
        """
        Extract text from image using OCR or Gemini Vision (if enabled)
        
        Args:
            image_url: URL of the image
            
        Returns:
            Extracted text or None if extraction fails
        """
        if not PIL_AVAILABLE:
            if not self.skip_ocr_if_unavailable:
                self.logger.warning("PIL not available - skipping OCR")
            return None
        
        try:
            # Download image
            self.logger.debug(f"Downloading image: {image_url}")
            response = self.session.get(image_url, timeout=self.link_timeout)
            response.raise_for_status()
            
            # Open image
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            extracted_text: Optional[str] = None
            
            # Prefer EasyOCR/Tesseract if available
            if self.use_easyocr and self.easyocr_reader:
                result = self.easyocr_reader.readtext(image, detail=0)
                extracted_text = ' '.join(result)
            elif TESSERACT_AVAILABLE:
                extracted_text = pytesseract.image_to_string(image, lang=self.ocr_language)
            elif self.use_gemini_vision and GENAI_AVAILABLE:
                try:
                    prompt = "Extract all textual content from this image. Return only the text."
                    vision_model = genai.GenerativeModel(self.gemini_model)
                    resp = vision_model.generate_content([prompt, image])
                    extracted_text = getattr(resp, 'text', None)
                except Exception as e:
                    self.logger.warning(f"Gemini Vision failed: {e}")
                    extracted_text = None
            else:
                if not self.skip_ocr_if_unavailable:
                    self.logger.warning("No OCR engine available and Gemini Vision disabled")
                return None
            
            # Clean extracted text
            extracted_text = self._clean_ocr_text(extracted_text or '')
            
            if extracted_text:
                self.logger.info(f"Image text extracted ({len(extracted_text)} chars)")
                return extracted_text
            else:
                self.logger.debug("No text extracted from image")
                return None
        
        except requests.RequestException as e:
            self.logger.error(f"Failed to download image {image_url}: {e}")
            return None
        except Exception as e:
            if not self.skip_ocr_if_unavailable:
                self.logger.error(f"OCR failed for {image_url}: {e}")
            else:
                self.logger.debug(f"OCR skipped for {image_url}: {e}")
            return None
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR output text
        
        Args:
            text: Raw OCR output
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join lines
        cleaned = ' '.join(lines)
        
        # Remove multiple spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def extract_from_link(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract content from external link
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary with title, text, source_domain or None if extraction fails
        """
        try:
            # Parse domain
            parsed = urlparse(url)
            source_domain = parsed.netloc
            
            self.logger.debug(f"Extracting content from: {url}")
            
            # Try newspaper3k first (best for articles)
            if NEWSPAPER_AVAILABLE:
                try:
                    article = Article(url)
                    article.download()
                    article.parse()
                    
                    return {
                        'title': article.title,
                        'text': article.text,
                        'source_domain': source_domain
                    }
                except Exception as e:
                    self.logger.debug(f"newspaper3k failed, falling back to BeautifulSoup: {e}")
            
            # Fallback to BeautifulSoup
            if BS4_AVAILABLE:
                response = self.session.get(url, timeout=self.link_timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title = ''
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                
                # Extract main content
                # Remove script and style elements
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()
                
                # Try to find main content
                main_content = soup.find('article') or soup.find('main') or soup.find('body')
                
                if main_content:
                    # Get text
                    text = main_content.get_text(separator=' ', strip=True)
                    
                    # Clean text
                    text = ' '.join(text.split())  # Remove excessive whitespace
                    
                    # Truncate if too long
                    if len(text) > 10000:
                        text = text[:10000] + '...'
                    
                    return {
                        'title': title,
                        'text': text,
                        'source_domain': source_domain
                    }
            
            self.logger.warning(f"Could not extract content from {url}")
            return None
        
        except requests.Timeout:
            self.logger.warning(f"Timeout fetching {url}")
            return None
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting from {url}: {e}")
            return None
    
    def extract_text_summary(self, text: str, max_length: int = 500) -> str:
        """
        Create a summary of text for preview
        
        Args:
            text: Full text
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        if len(text) <= max_length:
            return text
        
        # Truncate at sentence boundary if possible
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # If period is in last 30%
            return truncated[:last_period + 1]
        else:
            return truncated + '...'
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is accessible
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is accessible, False otherwise
        """
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
