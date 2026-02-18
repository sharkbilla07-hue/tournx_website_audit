"""
Website Audit Tool - Web Scraper Module
Uses BeautifulSoup to scrape and analyze website content
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, List, Optional, Tuple, Any
import re

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, USER_AGENT, SEO_SETTINGS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """
    Web scraper class for fetching and parsing website content
    """
    
    def __init__(self, url: str):
        self.url = url
        self.domain = urlparse(url).netloc
        self.soup = None
        self.response = None
        self.html = None
        
    def fetch_page(self) -> bool:
        """
        Fetch the page content
        """
        try:
            headers = {'User-Agent': USER_AGENT}
            self.response = requests.get(self.url, headers=headers, timeout=REQUEST_TIMEOUT)
            self.response.raise_for_status()
            self.html = self.response.text
            self.soup = BeautifulSoup(self.html, 'lxml')
            logger.info(f"Successfully fetched page: {self.url}")
            return True
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching page: {self.url}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return False
    
    def get_soup(self) -> Optional[BeautifulSoup]:
        """
        Get BeautifulSoup object
        """
        if self.soup is None:
            self.fetch_page()
        return self.soup
    
    def get_meta_tags(self) -> Dict[str, Any]:
        """
        Extract and analyze meta tags
        """
        soup = self.get_soup()
        if not soup:
            return self._get_empty_meta_tags()
        
        meta_tags = {
            'title': self._analyze_title(soup),
            'description': self._analyze_description(soup),
            'keywords': self._analyze_keywords(soup)
        }
        
        return meta_tags
    
    def _analyze_title(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze title tag
        """
        title_tag = soup.find('title')
        result = {
            'exists': False,
            'content': '',
            'length': 0,
            'optimal': False,
            'issues': []
        }
        
        if title_tag and title_tag.string:
            content = title_tag.string.strip()
            result['exists'] = True
            result['content'] = content
            result['length'] = len(content)
            
            # Check length
            if result['length'] < SEO_SETTINGS['title_min_length']:
                result['issues'].append(f"Title too short ({result['length']} chars) - should be 50-60 characters")
            elif result['length'] > SEO_SETTINGS['title_max_length']:
                result['issues'].append(f"Title too long ({result['length']} chars) - should be under 60 characters")
            else:
                result['optimal'] = True
        else:
            result['issues'].append('Missing page title')
        
        return result
    
    def _analyze_description(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze meta description
        """
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        result = {
            'exists': False,
            'content': '',
            'length': 0,
            'optimal': False,
            'issues': []
        }
        
        if desc_tag:
            content = desc_tag.get('content', '').strip()
            result['exists'] = True
            result['content'] = content
            result['length'] = len(content)
            
            # Check length
            if result['length'] < SEO_SETTINGS['description_min_length']:
                result['issues'].append(f"Description too short ({result['length']} chars) - should be 150-160 characters")
            elif result['length'] > SEO_SETTINGS['description_max_length']:
                result['issues'].append(f"Description too long ({result['length']} chars) - should be under 160 characters")
            else:
                result['optimal'] = True
        else:
            result['issues'].append('Missing meta description')
        
        return result
    
    def _analyze_keywords(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze meta keywords
        """
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        result = {
            'exists': False,
            'content': '',
            'issues': []
        }
        
        if keywords_tag:
            result['exists'] = True
            result['content'] = keywords_tag.get('content', '')
        else:
            result['issues'].append('Meta keywords tag missing (though less important for SEO)')
        
        return result
    
    def _get_empty_meta_tags(self) -> Dict[str, Any]:
        """
        Return empty meta tags structure
        """
        return {
            'title': {'exists': False, 'content': '', 'length': 0, 'optimal': False, 'issues': ['Could not fetch page']},
            'description': {'exists': False, 'content': '', 'length': 0, 'optimal': False, 'issues': ['Could not fetch page']},
            'keywords': {'exists': False, 'content': '', 'issues': ['Could not fetch page']}
        }
    
    def get_heading_structure(self) -> Dict[str, Any]:
        """
        Analyze heading structure (H1, H2, H3)
        """
        soup = self.get_soup()
        if not soup:
            return self._get_empty_headings()
        
        headings = {
            'h1': {'count': 0, 'contents': [], 'issues': []},
            'h2': {'count': 0, 'contents': [], 'issues': []},
            'h3': {'count': 0, 'contents': [], 'issues': []},
            'hierarchy_valid': True,
            'issues': []
        }
        
        # Analyze H1
        h1_tags = soup.find_all('h1')
        headings['h1']['count'] = len(h1_tags)
        headings['h1']['contents'] = [h.get_text(strip=True) for h in h1_tags if h.get_text(strip=True)]
        
        if len(h1_tags) == 0:
            headings['h1']['issues'].append('No H1 tag found - critical for SEO')
            headings['hierarchy_valid'] = False
        elif len(h1_tags) > SEO_SETTINGS['max_h1_tags']:
            headings['h1']['issues'].append(f"Multiple H1 tags found ({len(h1_tags)}) - should have only one")
        
        # Analyze H2
        h2_tags = soup.find_all('h2')
        headings['h2']['count'] = len(h2_tags)
        
        # Analyze H3
        h3_tags = soup.find_all('h3')
        headings['h3']['count'] = len(h3_tags)
        
        # Check hierarchy
        if headings['h1']['count'] == 0 and headings['h2']['count'] > 0:
            headings['issues'].append('H2 tags found without H1 - improper hierarchy')
            headings['hierarchy_valid'] = False
        
        return headings
    
    def _get_empty_headings(self) -> Dict[str, Any]:
        """
        Return empty headings structure
        """
        return {
            'h1': {'count': 0, 'contents': [], 'issues': ['Could not fetch page']},
            'h2': {'count': 0, 'contents': [], 'issues': []},
            'h3': {'count': 0, 'contents': [], 'issues': []},
            'hierarchy_valid': False,
            'issues': ['Could not analyze page']
        }
    
    def get_images_analysis(self) -> Dict[str, Any]:
        """
        Analyze images on the page
        """
        soup = self.get_soup()
        if not soup:
            return {'total': 0, 'with_alt': 0, 'without_alt': 0, 'issues': ['Could not fetch page']}
        
        images = soup.find_all('img')
        total = len(images)
        with_alt = 0
        without_alt = 0
        missing_alt_images = []
        
        for img in images:
            alt = img.get('alt')
            if alt is not None and alt.strip():
                with_alt += 1
            else:
                without_alt += 1
                src = img.get('src', 'unknown')
                missing_alt_images.append(src)
        
        issues = []
        if without_alt > 0:
            issues.append(f"{without_alt} images missing alt text")
        
        return {
            'total': total,
            'with_alt': with_alt,
            'without_alt': without_alt,
            'missing_alt_images': missing_alt_images[:10],  # Limit to first 10
            'issues': issues
        }
    
    def get_canonical(self) -> Dict[str, Any]:
        """
        Check canonical URL
        """
        soup = self.get_soup()
        if not soup:
            return {'exists': False, 'url': '', 'issues': ['Could not fetch page']}
        
        canonical = soup.find('link', rel='canonical')
        
        if canonical:
            return {
                'exists': True,
                'url': canonical.get('href', ''),
                'issues': []
            }
        
        return {
            'exists': False,
            'url': '',
            'issues': ['No canonical URL specified']
        }
    
    def get_structured_data(self) -> Dict[str, Any]:
        """
        Check for structured data (Schema.org)
        """
        soup = self.get_soup()
        if not soup:
            return {'exists': False, 'types': [], 'issues': ['Could not fetch page']}
        
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        if json_ld_scripts:
            types = []
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string or '{}')
                    if '@type' in data:
                        types.append(data['@type'])
                    elif isinstance(data.get('@graph'), list):
                        for item in data['@graph']:
                            if '@type' in item:
                                types.append(item['@type'])
                except:
                    pass
            
            return {
                'exists': True,
                'types': types if types else ['Schema.org'],
                'issues': []
            }
        
        return {
            'exists': False,
            'types': [],
            'issues': ['No structured data/schema markup found']
        }
    
    def get_open_graph(self) -> Dict[str, Any]:
        """
        Check Open Graph meta tags
        """
        soup = self.get_soup()
        if not soup:
            return {'exists': False, 'tags_found': [], 'issues': ['Could not fetch page']}
        
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        
        if og_tags:
            tags_found = [tag.get('property') for tag in og_tags if tag.get('property')]
            return {
                'exists': True,
                'tags_found': tags_found,
                'issues': []
            }
        
        return {
            'exists': False,
            'tags_found': [],
            'issues': ['No Open Graph meta tags found']
        }
    
    def get_twitter_cards(self) -> Dict[str, Any]:
        """
        Check Twitter Card meta tags
        """
        soup = self.get_soup()
        if not soup:
            return {'exists': False, 'issues': ['Could not fetch page']}
        
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        
        if twitter_tags:
            return {
                'exists': True,
                'tags_found': [tag.get('name') for tag in twitter_tags if tag.get('name')],
                'issues': []
            }
        
        return {
            'exists': False,
            'issues': ['Twitter card meta tags not found']
        }
    
    def check_robots_txt(self) -> Dict[str, Any]:
        """
        Check robots.txt
        """
        robots_url = urljoin(self.url, '/robots.txt')
        
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(robots_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if response.status_code == 200:
                return {
                    'exists': True,
                    'accessible': True,
                    'content': response.text[:500],  # First 500 chars
                    'issues': []
                }
            else:
                return {
                    'exists': False,
                    'accessible': False,
                    'issues': ['robots.txt not found or not accessible']
                }
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            return {
                'exists': False,
                'accessible': False,
                'issues': ['robots.txt not found or not accessible']
            }
    
    def check_sitemap(self) -> Dict[str, Any]:
        """
        Check sitemap.xml
        """
        sitemap_url = urljoin(self.url, '/sitemap.xml')
        
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(sitemap_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if response.status_code == 200:
                # Try to parse XML to count URLs
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'xml')
                    urls = soup.find_all('url')
                    entries = len(urls)
                except:
                    entries = 0
                
                return {
                    'exists': True,
                    'url': sitemap_url,
                    'entries': entries,
                    'issues': []
                }
            else:
                return {
                    'exists': False,
                    'url': '',
                    'issues': ['sitemap.xml not found']
                }
        except Exception as e:
            logger.warning(f"Error checking sitemap: {e}")
            return {
                'exists': False,
                'url': '',
                'issues': ['sitemap.xml not found']
            }
    
    def get_page_size(self) -> Dict[str, int]:
        """
        Get page size information
        """
        if self.response:
            return {
                'total_bytes': len(self.html) if self.html else 0,
                'total_kb': round(len(self.html) / 1024, 2) if self.html else 0
            }
        return {'total_bytes': 0, 'total_kb': 0}
    
    def get_all_links(self) -> Dict[str, Any]:
        """
        Get all links from the page
        """
        soup = self.get_soup()
        if not soup:
            return {'internal': [], 'external': [], 'broken': []}
        
        internal_links = []
        external_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Skip empty, anchor, or javascript links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Check if internal or external
            parsed = urlparse(href)
            if parsed.netloc:
                if parsed.netloc == self.domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            else:
                # Relative URL - internal
                internal_links.append(urljoin(self.url, href))
        
        return {
            'internal': list(set(internal_links)),
            'external': list(set(external_links)),
            'internal_count': len(set(internal_links)),
            'external_count': len(set(external_links))
        }
    
    def get_text_content(self) -> str:
        """
        Get visible text content from the page
        """
        soup = self.get_soup()
        if not soup:
            return ''
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text


if __name__ == '__main__':
    # Test the scraper
    test_url = 'https://www.chocolaty.in'
    scraper = WebScraper(test_url)
    
    if scraper.fetch_page():
        print("Meta Tags:", scraper.get_meta_tags())
        print("Headings:", scraper.get_heading_structure())
        print("Images:", scraper.get_images_analysis())
        print("Canonical:", scraper.get_canonical())
        print("Structured Data:", scraper.get_structured_data())
        print("Open Graph:", scraper.get_open_graph())
        print("Twitter Cards:", scraper.get_twitter_cards())
