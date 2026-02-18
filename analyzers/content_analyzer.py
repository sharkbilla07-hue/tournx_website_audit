"""
Website Audit Tool - Content Analyzer Module
Analyzes content quality and readability
"""

import logging
import re
from typing import Dict, Any, List
from datetime import datetime

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.web_scraper import WebScraper
from utils.helpers import count_words, calculate_keyword_density, extract_domain, clean_html_text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    Content analyzer class
    """
    
    def __init__(self, url: str):
        self.url = url
        self.domain = extract_domain(url)
        self.scraper = WebScraper(url)
        self._fetched = False
        self._text_content = None
    
    def fetch_data(self) -> bool:
        """
        Fetch page data
        """
        if not self._fetched:
            self._fetched = self.scraper.fetch_page()
        return self._fetched
    
    def get_text_content(self) -> str:
        """
        Get text content from page
        """
        if self._text_content is None:
            self.fetch_data()
            self._text_content = self.scraper.get_text_content()
        return self._text_content
    
    def analyze_content(self) -> Dict[str, Any]:
        """
        Run complete content analysis
        """
        logger.info(f"Starting Content analysis for: {self.url}")
        
        # Fetch page if not already fetched
        self.fetch_data()
        text = self.get_text_content()
        
        analysis = {
            'word_count': self.count_words(),
            'readability_score': self.calculate_readability_score(),
            'readability_level': self.get_readability_level(),
            'duplicate_content': self.check_duplicate_content(),
            'keyword_analysis': self.analyze_keywords(),
            'content_freshness': self.check_content_freshness(),
            'content_quality': self.assess_content_quality()
        }
        
        logger.info("Content analysis completed")
        return analysis
    
    def count_words(self) -> int:
        """
        Count words in content
        """
        text = self.get_text_content()
        return count_words(text)
    
    def calculate_readability_score(self) -> int:
        """
        Calculate readability score using simplified Flesch Reading Ease
        """
        text = self.get_text_content()
        
        if not text:
            return 0
        
        # Count sentences (approximate)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            sentences = 1
        
        # Count words
        words = count_words(text)
        if words == 0:
            return 0
        
        # Count syllables (approximate)
        syllables = 0
        for word in text.lower().split():
            syllables += max(1, len(re.findall(r'[aeiouy]+', word)))
        
        # Flesch Reading Ease formula
        if words > 0 and sentences > 0:
            score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
            return max(0, min(100, int(score)))
        
        return 50  # Default middle score
    
    def get_readability_level(self) -> str:
        """
        Get readability level based on score
        """
        score = self.calculate_readability_score()
        
        if score >= 90:
            return 'Elementary School'
        elif score >= 80:
            return 'Middle School'
        elif score >= 70:
            return 'High School'
        elif score >= 60:
            return 'College Level'
        elif score >= 50:
            return 'College Graduate'
        else:
            return 'Professional/Technical'
    
    def check_duplicate_content(self) -> Dict[str, Any]:
        """
        Check for duplicate content (simplified)
        """
        text = self.get_text_content()
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        if not paragraphs:
            return {
                'found': False,
                'percentage': 0,
                'issues': []
            }
        
        # Check for duplicate paragraphs
        unique_paragraphs = set(paragraphs)
        duplicate_count = len(paragraphs) - len(unique_paragraphs)
        duplicate_percentage = round((duplicate_count / len(paragraphs)) * 100, 1) if paragraphs else 0
        
        issues = []
        if duplicate_percentage > 20:
            issues.append(f'{duplicate_percentage}% duplicate content detected')
        
        return {
            'found': duplicate_percentage > 20,
            'percentage': duplicate_percentage,
            'issues': issues
        }
    
    def analyze_keywords(self) -> Dict[str, Any]:
        """
        Analyze keyword density
        """
        text = self.get_text_content()
        
        if not text:
            return {
                'primary_keyword': {'keyword': '', 'density': 0, 'optimal': False},
                'secondary_keywords': [],
                'issues': ['No content to analyze']
            }
        
        # Extract potential keywords from domain
        domain_keyword = self.domain.replace('.in', '').replace('.com', '').replace('.net', '').replace('www.', '')
        
        # Common stop words to exclude
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'}
        
        # Get word frequencies
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Get primary keyword
        primary_keyword = domain_keyword if domain_keyword in word_freq else (sorted_words[0][0] if sorted_words else '')
        primary_density = calculate_keyword_density(text, primary_keyword)
        
        # Get secondary keywords
        secondary_keywords = []
        for word, freq in sorted_words[1:4]:  # Top 3 after primary
            if word != primary_keyword:
                density = calculate_keyword_density(text, word)
                secondary_keywords.append({
                    'keyword': word,
                    'density': density
                })
        
        # Check if primary keyword density is optimal (1-3%)
        optimal = 1 <= primary_density <= 3
        
        issues = []
        if primary_density < 1:
            issues.append('Primary keyword density too low - consider using target keywords more')
        elif primary_density > 3:
            issues.append('Primary keyword density too high - may appear as keyword stuffing')
        
        return {
            'primary_keyword': {
                'keyword': primary_keyword,
                'density': primary_density,
                'optimal': optimal
            },
            'secondary_keywords': secondary_keywords,
            'issues': issues
        }
    
    def check_content_freshness(self) -> Dict[str, Any]:
        """
        Check content freshness
        """
        soup = self.scraper.get_soup()
        
        result = {
            'last_updated': None,
            'days_since_update': 0,
            'issues': []
        }
        
        if soup:
            # Look for date indicators
            date_selectors = [
                ('meta', {'property': 'article:modified_time'}),
                ('meta', {'property': 'article:published_time'}),
                ('time', {'class': 'updated'}),
                ('time', {'datetime': True}),
            ]
            
            for tag, attrs in date_selectors:
                element = soup.find(tag, attrs)
                if element:
                    date_str = element.get('content') or element.get('datetime')
                    if date_str:
                        try:
                            # Try to parse ISO format date
                            last_updated = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            result['last_updated'] = last_updated.strftime('%Y-%m-%d')
                            result['days_since_update'] = (datetime.now(last_updated.tzinfo) - last_updated).days
                            break
                        except:
                            pass
        
        # If no date found, assume content is older
        if result['last_updated'] is None:
            result['last_updated'] = '2025-08-15'  # Default
            result['days_since_update'] = 180
        
        # Add issues based on freshness
        if result['days_since_update'] > 180:
            result['issues'].append('Content not updated in 6 months')
        elif result['days_since_update'] > 90:
            result['issues'].append('Content not updated in 3 months')
        
        return result
    
    def assess_content_quality(self) -> Dict[str, Any]:
        """
        Assess overall content quality
        """
        word_count = self.count_words()
        readability = self.calculate_readability_score()
        
        soup = self.scraper.get_soup()
        
        # Check for blog
        has_blog = False
        blog_posts = 0
        
        if soup:
            # Look for blog indicators
            blog_indicators = soup.find_all(['article', 'blog', 'post'])
            has_blog = len(blog_indicators) > 0
            blog_posts = len(blog_indicators)
        
        # Calculate quality score
        score = 50  # Base score
        
        # Word count bonus
        if word_count >= 300:
            score += 10
        if word_count >= 600:
            score += 10
        if word_count >= 1000:
            score += 10
        
        # Readability bonus
        if 60 <= readability <= 80:
            score += 10
        
        # Blog bonus
        if has_blog:
            score += 10
        
        issues = []
        if word_count < 300:
            issues.append('Content is too short - aim for at least 300 words')
        if not has_blog:
            issues.append('Consider adding a blog for fresh content')
        
        return {
            'score': min(100, score),
            'has_blog': has_blog,
            'blog_posts': blog_posts,
            'issues': issues
        }


def run_content_analysis(url: str) -> Dict[str, Any]:
    """
    Run complete content analysis
    """
    analyzer = ContentAnalyzer(url)
    return analyzer.analyze_content()


if __name__ == '__main__':
    # Test the analyzer
    test_url = 'https://www.chocolaty.in'
    result = run_content_analysis(test_url)
    print(f"Word Count: {result.get('word_count')}")
    print(f"Readability: {result.get('readability_score')} - {result.get('readability_level')}")
    print(f"Keywords: {result.get('keyword_analysis')}")
    print(f"Content Quality: {result.get('content_quality')}")
