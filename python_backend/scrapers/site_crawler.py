"""
Website Audit Tool - Multi-page Crawler Module
Crawls multiple pages for comprehensive site audit
"""

import logging
from typing import Dict, Any, List, Set
from urllib.parse import urljoin, urlparse
from collections import deque
import time

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, USER_AGENT
from scrapers.web_scraper import WebScraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SiteCrawler:
    """
    Multi-page site crawler for comprehensive audits
    """
    
    def __init__(self, base_url: str, max_pages: int = 20, delay: float = 0.5):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay  # Delay between requests (be polite)
        self.visited: Set[str] = set()
        self.results: List[Dict[str, Any]] = []
        self.broken_links: List[Dict[str, str]] = []
        self.redirects: List[Dict[str, str]] = []
    
    def is_same_domain(self, url: str) -> bool:
        """
        Check if URL belongs to same domain
        """
        parsed = urlparse(url)
        return parsed.netloc == self.domain
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison
        """
        # Remove fragment
        url = url.split('#')[0]
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
        return url
    
    def get_links_from_page(self, url: str, scraper: WebScraper) -> List[str]:
        """
        Extract internal links from page
        """
        links = []
        soup = scraper.get_soup()
        
        if not soup:
            return links
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip empty, anchor, javascript, mailto links
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert relative to absolute URL
            full_url = urljoin(url, href)
            
            # Only include same-domain links
            if self.is_same_domain(full_url):
                normalized = self.normalize_url(full_url)
                if normalized not in self.visited:
                    links.append(normalized)
        
        return list(set(links))
    
    def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single page and extract data
        """
        logger.info(f"Crawling: {url}")
        
        scraper = WebScraper(url)
        success = scraper.fetch_page()
        
        if not success:
            return {
                'url': url,
                'status': 'failed',
                'error': 'Could not fetch page'
            }
        
        # Get page data
        page_data = {
            'url': url,
            'status': 'success',
            'title': scraper.get_meta_tags().get('title', {}).get('content', ''),
            'h1_count': scraper.get_heading_structure().get('h1', {}).get('count', 0),
            'images': scraper.get_images_analysis(),
            'word_count': len(scraper.get_text_content().split()),
            'page_size_kb': scraper.get_page_size().get('total_kb', 0),
            'canonical': scraper.get_canonical(),
            'meta_description': scraper.get_meta_tags().get('description', {}).get('content', ''),
            'issues': []
        }
        
        # Identify issues
        if not page_data['title']:
            page_data['issues'].append('Missing title')
        if page_data['h1_count'] == 0:
            page_data['issues'].append('Missing H1')
        if page_data['h1_count'] > 1:
            page_data['issues'].append('Multiple H1 tags')
        if page_data['images'].get('without_alt', 0) > 0:
            page_data['issues'].append(f"{page_data['images']['without_alt']} images missing alt text")
        if not page_data['canonical'].get('exists'):
            page_data['issues'].append('Missing canonical URL')
        
        return page_data
    
    def crawl_site(self) -> Dict[str, Any]:
        """
        Crawl entire site starting from base URL
        """
        logger.info(f"Starting site crawl from: {self.base_url}")
        logger.info(f"Max pages: {self.max_pages}")
        
        queue = deque([self.normalize_url(self.base_url)])
        
        while queue and len(self.visited) < self.max_pages:
            url = queue.popleft()
            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            
            # Crawl page
            page_result = self.crawl_page(url)
            self.results.append(page_result)
            
            # Get more links to crawl
            if page_result['status'] == 'success':
                scraper = WebScraper(url)
                scraper.fetch_page()
                new_links = self.get_links_from_page(url, scraper)
                
                for link in new_links:
                    if link not in self.visited:
                        queue.append(link)
            
            # Be polite - delay between requests
            time.sleep(self.delay)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive crawl report
        """
        # Calculate aggregate statistics
        total_pages = len(self.results)
        successful_pages = sum(1 for r in self.results if r['status'] == 'success')
        failed_pages = total_pages - successful_pages
        
        # Aggregate issues
        all_issues = []
        pages_with_issues = 0
        for page in self.results:
            if page.get('issues'):
                all_issues.extend([f"{page['url']}: {issue}" for issue in page['issues']])
                pages_with_issues += 1
        
        # Calculate averages
        avg_word_count = 0
        avg_page_size = 0
        total_images_without_alt = 0
        
        if successful_pages > 0:
            successful_results = [r for r in self.results if r['status'] == 'success']
            avg_word_count = sum(r.get('word_count', 0) for r in successful_results) // successful_pages
            avg_page_size = sum(r.get('page_size_kb', 0) for r in successful_results) // successful_pages
            total_images_without_alt = sum(r.get('images', {}).get('without_alt', 0) for r in successful_results)
        
        return {
            'crawl_summary': {
                'base_url': self.base_url,
                'pages_crawled': total_pages,
                'successful_pages': successful_pages,
                'failed_pages': failed_pages,
                'max_pages_limit': self.max_pages
            },
            'aggregate_stats': {
                'avg_word_count': avg_word_count,
                'avg_page_size_kb': avg_page_size,
                'total_images_without_alt': total_images_without_alt,
                'pages_with_issues': pages_with_issues
            },
            'pages': self.results,
            'all_issues': all_issues[:50],  # Limit to first 50 issues
            'crawl_score': self._calculate_crawl_score()
        }
    
    def _calculate_crawl_score(self) -> int:
        """
        Calculate overall crawl score based on issues found
        """
        if not self.results:
            return 0
        
        score = 100
        total_pages = len(self.results)
        
        # Penalize for failed pages
        failed = sum(1 for r in self.results if r['status'] != 'success')
        score -= (failed / total_pages) * 30
        
        # Penalize for common issues
        for page in self.results:
            issues = page.get('issues', [])
            for issue in issues:
                if 'Missing title' in issue:
                    score -= 2
                elif 'Missing H1' in issue:
                    score -= 3
                elif 'Multiple H1' in issue:
                    score -= 1
                elif 'missing alt' in issue:
                    score -= 0.5
                elif 'Missing canonical' in issue:
                    score -= 1
        
        return max(0, min(100, int(score)))


def run_site_crawl(url: str, max_pages: int = 20) -> Dict[str, Any]:
    """
    Run site crawl and return report
    """
    crawler = SiteCrawler(url, max_pages=max_pages)
    return crawler.crawl_site()


if __name__ == '__main__':
    # Test the crawler
    test_url = 'https://www.chocolaty.in'
    result = run_site_crawl(test_url, max_pages=5)
    
    print(f"\nCrawl Summary:")
    print(f"  Pages Crawled: {result['crawl_summary']['pages_crawled']}")
    print(f"  Successful: {result['crawl_summary']['successful_pages']}")
    print(f"  Crawl Score: {result['crawl_score']}")
    print(f"\nAggregate Stats:")
    print(f"  Avg Word Count: {result['aggregate_stats']['avg_word_count']}")
    print(f"  Avg Page Size: {result['aggregate_stats']['avg_page_size_kb']} KB")
    print(f"  Total Images Without Alt: {result['aggregate_stats']['total_images_without_alt']}")
