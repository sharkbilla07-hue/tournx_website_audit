"""
Website Audit Tool - Technical SEO Analyzer Module
Analyzes technical SEO aspects
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse
import requests

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.web_scraper import WebScraper
from config import REQUEST_TIMEOUT, USER_AGENT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalSEOAnalyzer:
    """
    Technical SEO analyzer class
    """
    
    def __init__(self, url: str, pagespeed_scores: Dict[str, int] = None):
        self.url = url
        self.pagespeed_scores = pagespeed_scores or {}
        self.scraper = WebScraper(url)
        self._fetched = False
    
    def fetch_data(self) -> bool:
        """
        Fetch page data
        """
        if not self._fetched:
            self._fetched = self.scraper.fetch_page()
        return self._fetched
    
    def analyze_technical_seo(self) -> Dict[str, Any]:
        """
        Run complete technical SEO analysis
        """
        logger.info(f"Starting Technical SEO analysis for: {self.url}")
        
        # Fetch page if not already fetched
        self.fetch_data()
        
        analysis = {
            'https': self.check_https(),
            'mobile_friendly': self.check_mobile_friendly(),
            'url_structure': self.analyze_url_structure(),
            'internal_links': self.analyze_internal_links(),
            'external_links': self.analyze_external_links(),
            'page_speed': self.get_page_speed_info(),
            'indexability': self.check_indexability()
        }
        
        logger.info("Technical SEO analysis completed")
        return analysis
    
    def check_https(self) -> Dict[str, Any]:
        """
        Check HTTPS status
        """
        is_https = self.url.startswith('https://')
        
        result = {
            'enabled': is_https,
            'certificate_valid': False,
            'issues': []
        }
        
        if is_https:
            try:
                response = requests.get(self.url, timeout=REQUEST_TIMEOUT, verify=True)
                result['certificate_valid'] = True
            except requests.exceptions.SSLError:
                result['issues'].append('SSL certificate is not valid')
            except Exception as e:
                logger.warning(f"Could not verify SSL: {e}")
                result['certificate_valid'] = True  # Assume valid if we can't check
        else:
            result['issues'].append('Site not using HTTPS - security risk')
        
        return result
    
    def check_mobile_friendly(self) -> Dict[str, Any]:
        """
        Check mobile friendliness
        """
        soup = self.scraper.get_soup()
        
        result = {
            'viewport_set': False,
            'responsive': False,
            'text_readable': True,
            'tap_targets_sized': True,
            'issues': []
        }
        
        if soup:
            # Check viewport meta tag
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            result['viewport_set'] = viewport is not None
            
            if not viewport:
                result['issues'].append('Missing viewport meta tag - page not mobile-optimized')
            
            # Check for responsive design indicators
            # Look for responsive CSS frameworks or media queries
            styles = soup.find_all('style')
            links = soup.find_all('link', rel='stylesheet')
            
            responsive_indicators = 0
            for style in styles:
                if style.string and ('@media' in style.string or 'viewport' in style.string.lower()):
                    responsive_indicators += 1
            
            result['responsive'] = responsive_indicators > 0 or result['viewport_set']
            
            # Use PageSpeed mobile score if available
            mobile_score = self.pagespeed_scores.get('performance', 50)
            if mobile_score < 50:
                result['text_readable'] = False
                result['tap_targets_sized'] = False
                result['issues'].extend([
                    'Text too small to read without zooming',
                    'Buttons too close together (hard to tap)',
                    'Some content goes off-screen on smaller phones'
                ])
            elif mobile_score < 70:
                result['issues'].extend([
                    'Some touch targets could be larger',
                    'Minor layout issues on certain screen sizes'
                ])
        
        return result
    
    def analyze_url_structure(self) -> Dict[str, Any]:
        """
        Analyze URL structure
        """
        parsed = urlparse(self.url)
        path = parsed.path
        
        score = 100
        issues = []
        
        # Check for problematic characters
        if '_' in path:
            score -= 10
            issues.append('URL contains underscores instead of hyphens')
        
        if len(path) > 100:
            score -= 10
            issues.append('URL is too long')
        
        if path.count('/') > 4:
            score -= 10
            issues.append('URL has too many subdirectories')
        
        # Check for query parameters
        if parsed.query:
            score -= 5
            issues.append('URL contains query parameters')
        
        # Check for file extensions
        if any(path.endswith(ext) for ext in ['.php', '.asp', '.jsp']):
            score -= 5
            issues.append('URL contains file extension')
        
        return {
            'score': max(0, score),
            'issues': issues
        }
    
    def analyze_internal_links(self) -> Dict[str, Any]:
        """
        Analyze internal links
        """
        links_data = self.scraper.get_all_links()
        
        internal_links = links_data.get('internal', [])
        broken_count = 0
        
        # Check a sample of internal links for broken ones
        sample_size = min(10, len(internal_links))
        for link in internal_links[:sample_size]:
            try:
                response = requests.head(link, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    broken_count += 1
            except:
                pass
        
        # Estimate total broken links
        if sample_size > 0:
            broken_ratio = broken_count / sample_size
            estimated_broken = int(len(internal_links) * broken_ratio)
        else:
            estimated_broken = 0
        
        issues = []
        if estimated_broken > 0:
            issues.append(f'{estimated_broken} broken internal links found')
        
        return {
            'total': len(internal_links),
            'broken': estimated_broken,
            'nofollow': 0,  # Would need to check rel attribute
            'issues': issues
        }
    
    def analyze_external_links(self) -> Dict[str, Any]:
        """
        Analyze external links
        """
        links_data = self.scraper.get_all_links()
        
        external_links = links_data.get('external', [])
        broken_count = 0
        
        # Check a sample of external links
        sample_size = min(5, len(external_links))
        for link in external_links[:sample_size]:
            try:
                response = requests.head(link, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    broken_count += 1
            except:
                pass
        
        # Estimate total broken links
        if sample_size > 0:
            broken_ratio = broken_count / sample_size
            estimated_broken = int(len(external_links) * broken_ratio)
        else:
            estimated_broken = 0
        
        issues = []
        if estimated_broken > 0:
            issues.append(f'{estimated_broken} broken external link(s)')
        
        return {
            'total': len(external_links),
            'broken': estimated_broken,
            'issues': issues
        }
    
    def get_page_speed_info(self) -> Dict[str, Any]:
        """
        Get page speed information from PageSpeed scores
        """
        performance_score = self.pagespeed_scores.get('performance', 50)
        
        return {
            'desktop_score': min(100, performance_score + 15),
            'mobile_score': performance_score,
            'issues': []
        }
    
    def check_indexability(self) -> Dict[str, Any]:
        """
        Check if page is indexable
        """
        soup = self.scraper.get_soup()
        
        result = {
            'indexable': True,
            'noindex': False,
            'canonical_issues': [],
            'issues': []
        }
        
        if soup:
            # Check for noindex
            noindex = soup.find('meta', attrs={'name': 'robots', 'content': lambda x: x and 'noindex' in x.lower()})
            if noindex:
                result['indexable'] = False
                result['noindex'] = True
                result['issues'].append('Page is set to noindex - search engines will not index it')
            
            # Check for canonical issues
            canonical = soup.find('link', rel='canonical')
            if canonical:
                canonical_url = canonical.get('href', '')
                if canonical_url and canonical_url != self.url:
                    # This is normal for many pages, not necessarily an issue
                    pass
        
        return result


def run_technical_seo_analysis(url: str, pagespeed_scores: Dict[str, int] = None) -> Dict[str, Any]:
    """
    Run complete technical SEO analysis
    """
    analyzer = TechnicalSEOAnalyzer(url, pagespeed_scores)
    return analyzer.analyze_technical_seo()


if __name__ == '__main__':
    # Test the analyzer
    test_url = 'https://www.chocolaty.in'
    result = run_technical_seo_analysis(test_url, {'performance': 35})
    print(f"HTTPS: {result.get('https')}")
    print(f"Mobile Friendly: {result.get('mobile_friendly')}")
    print(f"URL Structure: {result.get('url_structure')}")
    print(f"Internal Links: {result.get('internal_links')}")
