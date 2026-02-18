"""
Website Audit Tool - SEO Analyzer Module
Comprehensive SEO analysis using web scraper
"""

import logging
from typing import Dict, Any

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.web_scraper import WebScraper
from utils.helpers import count_words, calculate_keyword_density, extract_domain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """
    Comprehensive SEO analyzer class
    """
    
    def __init__(self, url: str):
        self.url = url
        self.domain = extract_domain(url)
        self.scraper = WebScraper(url)
        self._fetched = False
    
    def fetch_data(self) -> bool:
        """
        Fetch page data
        """
        if not self._fetched:
            self._fetched = self.scraper.fetch_page()
        return self._fetched
    
    def analyze_seo(self) -> Dict[str, Any]:
        """
        Run complete SEO analysis
        """
        logger.info(f"Starting SEO analysis for: {self.url}")
        
        # Fetch page if not already fetched
        self.fetch_data()
        
        analysis = {
            'meta_tags': self.analyze_meta_tags(),
            'heading_structure': self.analyze_headings(),
            'images': self.analyze_images(),
            'canonical': self.analyze_canonical(),
            'robots_txt': self.check_robots_txt(),
            'sitemap': self.check_sitemap(),
            'structured_data': self.analyze_structured_data(),
            'open_graph': self.analyze_open_graph(),
            'twitter_cards': self.analyze_twitter_cards(),
            'url_structure': self.analyze_url_structure(),
            'links': self.analyze_links(),
            'keyword_analysis': self.analyze_keywords(),
            'mobile_friendliness': self.check_mobile_friendliness()
        }
        
        logger.info("SEO analysis completed")
        return analysis
    
    def analyze_meta_tags(self) -> Dict[str, Any]:
        """
        Analyze meta tags
        """
        return self.scraper.get_meta_tags()
    
    def analyze_headings(self) -> Dict[str, Any]:
        """
        Analyze heading structure
        """
        return self.scraper.get_heading_structure()
    
    def analyze_images(self) -> Dict[str, Any]:
        """
        Analyze images
        """
        return self.scraper.get_images_analysis()
    
    def analyze_canonical(self) -> Dict[str, Any]:
        """
        Analyze canonical URL
        """
        return self.scraper.get_canonical()
    
    def check_robots_txt(self) -> Dict[str, Any]:
        """
        Check robots.txt
        """
        return self.scraper.check_robots_txt()
    
    def check_sitemap(self) -> Dict[str, Any]:
        """
        Check sitemap.xml
        """
        return self.scraper.check_sitemap()
    
    def analyze_structured_data(self) -> Dict[str, Any]:
        """
        Analyze structured data
        """
        return self.scraper.get_structured_data()
    
    def analyze_open_graph(self) -> Dict[str, Any]:
        """
        Analyze Open Graph tags
        """
        return self.scraper.get_open_graph()
    
    def analyze_twitter_cards(self) -> Dict[str, Any]:
        """
        Analyze Twitter Card tags
        """
        return self.scraper.get_twitter_cards()
    
    def analyze_url_structure(self) -> Dict[str, Any]:
        """
        Analyze URL structure for SEO best practices
        """
        from urllib.parse import urlparse
        
        result = {
            'url': self.url,
            'is_https': self.url.startswith('https://'),
            'has_www': 'www.' in self.url,
            'url_length': len(self.url),
            'has_underscores': '_' in self.url,
            'has_special_chars': any(c in self.url for c in ['%', '$', '&', '+', ',']),
            'issues': [],
            'recommendations': []
        }
        
        # Check for HTTPS
        if not result['is_https']:
            result['issues'].append('URL is not using HTTPS')
            result['recommendations'].append('Migrate to HTTPS for better security and SEO')
        
        # Check URL length
        if result['url_length'] > 100:
            result['issues'].append('URL is too long (over 100 characters)')
            result['recommendations'].append('Keep URLs concise and descriptive')
        
        # Check for underscores
        if result['has_underscores']:
            result['issues'].append('URL contains underscores')
            result['recommendations'].append('Use hyphens instead of underscores to separate words')
        
        # Check for special characters
        if result['has_special_chars']:
            result['issues'].append('URL contains special characters')
            result['recommendations'].append('Avoid special characters in URLs')
        
        # Check for dynamic parameters
        parsed = urlparse(self.url)
        if parsed.query:
            result['has_parameters'] = True
            param_count = len(parsed.query.split('&'))
            result['param_count'] = param_count
            if param_count > 2:
                result['issues'].append(f'URL has {param_count} query parameters')
                result['recommendations'].append('Minimize URL parameters for cleaner URLs')
        else:
            result['has_parameters'] = False
            result['param_count'] = 0
        
        return result
    
    def analyze_links(self) -> Dict[str, Any]:
        """
        Analyze internal and external links
        """
        result = {
            'internal_links': 0,
            'external_links': 0,
            'broken_links': 0,
            'nofollow_links': 0,
            'links_without_text': 0,
            'issues': [],
            'recommendations': []
        }
        
        if not self.scraper.soup:
            return result
        
        links = self.scraper.soup.find_all('a', href=True)
        base_domain = self.domain
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            rel = link.get('rel', [])
            
            # Check if link has text
            if not link_text:
                result['links_without_text'] += 1
            
            # Check nofollow
            if 'nofollow' in rel:
                result['nofollow_links'] += 1
            
            # Classify as internal or external
            if href.startswith('/') or href.startswith('#') or base_domain in href:
                result['internal_links'] += 1
            elif href.startswith('http'):
                result['external_links'] += 1
        
        # Generate recommendations
        if result['links_without_text'] > 0:
            result['issues'].append(f'{result["links_without_text"]} links have no descriptive text')
            result['recommendations'].append('Add descriptive anchor text to all links')
        
        if result['internal_links'] < 3:
            result['issues'].append('Very few internal links found')
            result['recommendations'].append('Add more internal links to improve navigation and SEO')
        
        return result
    
    def analyze_keywords(self) -> Dict[str, Any]:
        """
        Analyze keyword usage in content
        """
        result = {
            'word_count': 0,
            'top_keywords': [],
            'keyword_density': {},
            'issues': [],
            'recommendations': []
        }
        
        if not self.scraper.soup:
            return result
        
        # Get text content
        text_content = self.scraper.soup.get_text(separator=' ', strip=True)
        result['word_count'] = count_words(text_content)
        
        # Get title and meta description for keyword analysis
        title = self.scraper.soup.find('title')
        title_text = title.get_text() if title else ''
        
        meta_desc = self.scraper.soup.find('meta', attrs={'name': 'description'})
        meta_text = meta_desc.get('content', '') if meta_desc else ''
        
        # Check content length
        if result['word_count'] < 300:
            result['issues'].append(f'Content is too short ({result["word_count"]} words)')
            result['recommendations'].append('Add more content (aim for at least 300 words)')
        elif result['word_count'] < 600:
            result['issues'].append(f'Content could be longer ({result["word_count"]} words)')
            result['recommendations'].append('Consider expanding content for better SEO')
        
        # Extract potential keywords from title
        if title_text:
            # Simple keyword extraction (words longer than 3 chars)
            title_words = [w.lower() for w in title_text.split() if len(w) > 3]
            result['title_keywords'] = title_words[:5]
        
        return result
    
    def check_mobile_friendliness(self) -> Dict[str, Any]:
        """
        Check basic mobile friendliness indicators
        """
        result = {
            'has_viewport_meta': False,
            'has_mobile_viewport': False,
            'uses_responsive_images': False,
            'font_size_issues': False,
            'issues': [],
            'recommendations': []
        }
        
        if not self.scraper.soup:
            return result
        
        # Check for viewport meta tag
        viewport = self.scraper.soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            result['has_viewport_meta'] = True
            viewport_content = viewport.get('content', '')
            if 'width=device-width' in viewport_content:
                result['has_mobile_viewport'] = True
        
        # Check for responsive images
        picture_tags = self.scraper.soup.find_all('picture')
        srcset_attrs = self.scraper.soup.find_all(attrs={'srcset': True})
        if picture_tags or srcset_attrs:
            result['uses_responsive_images'] = True
        
        # Generate recommendations
        if not result['has_viewport_meta']:
            result['issues'].append('Missing viewport meta tag')
            result['recommendations'].append('Add viewport meta tag for mobile responsiveness')
        elif not result['has_mobile_viewport']:
            result['issues'].append('Viewport meta tag not properly configured')
            result['recommendations'].append('Use viewport meta with width=device-width')
        
        if not result['uses_responsive_images']:
            result['issues'].append('No responsive images detected')
            result['recommendations'].append('Use srcset or picture element for responsive images')
        
        return result
    
    def get_seo_score(self, analysis: Dict[str, Any] = None) -> int:
        """
        Calculate SEO score based on analysis
        """
        if analysis is None:
            analysis = self.analyze_seo()
        
        score = 100
        
        # Meta tags scoring
        meta = analysis.get('meta_tags', {})
        if not meta.get('title', {}).get('exists'):
            score -= 15
        elif not meta.get('title', {}).get('optimal'):
            score -= 5
        
        if not meta.get('description', {}).get('exists'):
            score -= 15
        elif not meta.get('description', {}).get('optimal'):
            score -= 5
        
        # Heading structure scoring
        headings = analysis.get('heading_structure', {})
        if headings.get('h1', {}).get('count', 0) == 0:
            score -= 15
        elif headings.get('h1', {}).get('count', 0) > 1:
            score -= 5
        
        if not headings.get('hierarchy_valid', True):
            score -= 5
        
        # Images scoring
        images = analysis.get('images', {})
        if images.get('total', 0) > 0:
            missing_alt_ratio = images.get('without_alt', 0) / images.get('total', 1)
            score -= int(missing_alt_ratio * 15)
        
        # Canonical scoring
        if not analysis.get('canonical', {}).get('exists'):
            score -= 5
        
        # Structured data scoring
        if not analysis.get('structured_data', {}).get('exists'):
            score -= 10
        
        # Open Graph scoring
        if not analysis.get('open_graph', {}).get('exists'):
            score -= 5
        
        # Robots.txt scoring
        if not analysis.get('robots_txt', {}).get('exists'):
            score -= 5
        
        # Sitemap scoring
        if not analysis.get('sitemap', {}).get('exists'):
            score -= 5
        
        # URL structure scoring (new)
        url_structure = analysis.get('url_structure', {})
        if url_structure.get('issues'):
            score -= len(url_structure.get('issues', [])) * 3
        
        # Mobile friendliness scoring (new)
        mobile = analysis.get('mobile_friendliness', {})
        if not mobile.get('has_viewport_meta'):
            score -= 10
        if not mobile.get('has_mobile_viewport'):
            score -= 5
        
        # Keyword/content scoring (new)
        keywords = analysis.get('keyword_analysis', {})
        if keywords.get('word_count', 0) < 300:
            score -= 10
        
        # Links scoring (new)
        links = analysis.get('links', {})
        if links.get('links_without_text', 0) > 0:
            score -= min(links.get('links_without_text', 0) * 2, 10)
        
        return max(0, min(100, score))


def run_seo_analysis(url: str) -> Dict[str, Any]:
    """
    Run complete SEO analysis and return results
    """
    analyzer = SEOAnalyzer(url)
    analysis = analyzer.analyze_seo()
    analysis['seo_score'] = analyzer.get_seo_score(analysis)
    return analysis


if __name__ == '__main__':
    # Test the analyzer
    test_url = 'https://www.chocolaty.in'
    result = run_seo_analysis(test_url)
    print(f"SEO Score: {result.get('seo_score')}")
    print(f"Meta Tags: {result.get('meta_tags')}")
    print(f"Headings: {result.get('heading_structure')}")
    print(f"Images: {result.get('images')}")
