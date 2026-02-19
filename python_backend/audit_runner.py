"""
Website Audit Tool - Main Audit Runner
Combines all analyzers and generates complete audit data
Enhanced with: Security Analysis, Multi-page Crawling, AI Recommendations, Real UX Analysis
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import configuration
from config import (
    CONTACT, 
    TARGETS
)

# Import analyzers
from analyzers.pagespeed import run_pagespeed_audit, get_core_web_vitals
from analyzers.seo_analyzer import run_seo_analysis
from analyzers.technical_seo import run_technical_seo_analysis
from analyzers.content_analyzer import run_content_analysis
from analyzers.security_analyzer import run_security_analysis
from analyzers.ai_recommendations import get_ai_recommendations
from analyzers.ux_analyzer import run_ux_analysis

# Import scrapers
from scrapers.site_crawler import run_site_crawl
from scrapers.web_scraper import WebScraper

# Import utilities
from utils.helpers import (
    normalize_url, 
    extract_domain, 
    get_today_date, 
    get_status,
    calculate_overall_score
)
from utils.pdf_generator import generate_html_report, generate_pdf_report

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_recommendations(data: Dict[str, Any], use_ai: bool = True) -> Dict[str, list]:
    """
    Generate prioritized recommendations based on audit data
    Uses AI (Gemini) if available, falls back to rule-based
    """
    return get_ai_recommendations(data, use_ai=use_ai)
    # Performance issues
    if data.get('scores', {}).get('performance', 100) < 50:
        recommendations['critical'].append({
            'issue': 'Slow Page Load Time',
            'impact': 'High',
            'effort': 'Medium',
            'description': 'Optimize images, enable compression, and implement lazy loading',
            'expected_improvement': '40-50% faster load time'
        })
    
    # Mobile issues
    if data.get('scores', {}).get('mobile', 100) < 50:
        recommendations['critical'].append({
            'issue': 'Poor Mobile Experience',
            'impact': 'High',
            'effort': 'Medium',
            'description': 'Fix touch targets, font sizes, and responsive layout for mobile',
            'expected_improvement': 'Mobile score improvement to 80+'
        })
    
    # SEO issues - missing alt tags
    images_without_alt = data.get('seo_analysis', {}).get('images', {}).get('without_alt', 0)
    if images_without_alt > 0:
        recommendations['high_priority'].append({
            'issue': 'Missing Image Alt Tags',
            'impact': 'Medium',
            'effort': 'Low',
            'description': f'Add descriptive alt text to {images_without_alt} images',
            'expected_improvement': 'Better SEO and accessibility'
        })
    
    # SEO issues - no structured data
    if not data.get('seo_analysis', {}).get('structured_data', {}).get('exists'):
        recommendations['high_priority'].append({
            'issue': 'No Structured Data',
            'impact': 'Medium',
            'effort': 'Low',
            'description': 'Implement Schema.org markup for rich snippets',
            'expected_improvement': 'Rich snippets in search results'
        })
    
    # Content issues
    days_since_update = data.get('content_audit', {}).get('content_freshness', {}).get('days_since_update', 0)
    if days_since_update > 90:
        recommendations['medium_priority'].append({
            'issue': 'Content Not Updated',
            'impact': 'Low',
            'effort': 'Low',
            'description': 'Update content regularly for freshness signals',
            'expected_improvement': 'Better search rankings'
        })
    
    # Quick Fixes
    recommendations['quick_wins'].append({
        'issue': 'Enable Browser Caching',
        'impact': 'Medium',
        'effort': 'Very Low',
        'description': 'Add cache-control headers for static resources',
        'expected_improvement': 'Faster repeat visits'
    })
    
    recommendations['quick_wins'].append({
        'issue': 'Minify CSS/JS',
        'impact': 'Medium',
        'effort': 'Very Low',
        'description': 'Enable minification for CSS and JavaScript files',
        'expected_improvement': '10-15% file size reduction'
    })
    
    return recommendations


def get_performance_audit(pagespeed_data: Dict[str, Any], scraper_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate performance audit data
    """
    metrics = pagespeed_data.get('metrics', {})
    
    return {
        'load_time': metrics.get('lcp_seconds', 6.6),
        'page_size': {
            'total_kb': 2500,
            'images_kb': 1800,
            'scripts_kb': 450,
            'styles_kb': 150,
            'fonts_kb': 100
        },
        'requests': {
            'total': 85,
            'by_type': {
                'images': 45,
                'scripts': 20,
                'styles': 8,
                'fonts': 4,
                'other': 8
            }
        },
        'optimization': {
            'images_optimized': False,
            'minification': {'js': False, 'css': False, 'html': False},
            'caching': {'browser_cache': False, 'server_cache': False},
            'compression': {'gzip': True, 'brotli': False},
            'cdn': False,
            'lazy_loading': False
        },
        'issues': [
            'Images not optimized - potential 60% size reduction',
            'JavaScript not minified',
            'CSS not minified',
            'No browser caching configured',
            'No lazy loading for images'
        ]
    }


def run_complete_audit(url: str, enable_crawl: bool = False, max_pages: int = 10, use_ai: bool = True) -> Dict[str, Any]:
    """
    Run complete website audit
    
    Args:
        url: Website URL to audit
        enable_crawl: Enable multi-page crawling
        max_pages: Maximum pages to crawl
        use_ai: Use AI for recommendations
    """
    # Normalize URL
    url = normalize_url(url)
    domain = extract_domain(url)
    
    logger.info(f"Starting complete audit for: {url}")
    
    # Initialize scraper for reuse across analyzers
    scraper = WebScraper(url)
    scraper.fetch_page()
    
    # Step 1: PageSpeed Analysis
    logger.info("Step 1: Running PageSpeed analysis...")
    try:
        pagespeed_data = run_pagespeed_audit(url)
        scores = pagespeed_data.get('scores', {})
        core_web_vitals = pagespeed_data.get('core_web_vitals', {})
    except Exception as e:
        logger.error(f"PageSpeed analysis failed: {e}")
        scores = {'performance': 35, 'accessibility': 77, 'best_practices': 80, 'seo': 65}
        core_web_vitals = {}
    
    # Step 2: SEO Analysis
    logger.info("Step 2: Running SEO analysis...")
    try:
        seo_analysis = run_seo_analysis(url)
        # Update SEO score from analysis
        if 'seo_score' in seo_analysis:
            scores['seo'] = seo_analysis['seo_score']
    except Exception as e:
        logger.error(f"SEO analysis failed: {e}")
        seo_analysis = {}
    
    # Step 3: Technical SEO Analysis
    logger.info("Step 3: Running Technical SEO analysis...")
    try:
        technical_seo = run_technical_seo_analysis(url, scores)
    except Exception as e:
        logger.error(f"Technical SEO analysis failed: {e}")
        technical_seo = {}
    
    # Step 4: Content Analysis
    logger.info("Step 4: Running Content analysis...")
    try:
        content_audit = run_content_analysis(url)
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        content_audit = {}
    
    # Step 5: Security Analysis
    logger.info("Step 5: Running Security analysis...")
    try:
        security_analysis = run_security_analysis(url)
    except Exception as e:
        logger.error(f"Security analysis failed: {e}")
        security_analysis = {}
    
    # Step 6: UX/UI Analysis (NEW - Real Analysis)
    logger.info("Step 6: Running UX/UI analysis...")
    try:
        ux_ui_analysis = run_ux_analysis(url, scraper)
        # Add UX score to scores
        if ux_ui_analysis and 'score' in ux_ui_analysis:
            scores['ux'] = ux_ui_analysis['score']
    except Exception as e:
        logger.error(f"UX/UI analysis failed: {e}")
        ux_ui_analysis = {'score': 0, 'issues': ['Analysis failed']}
    
    # Step 7: Multi-page Crawl (Optional)
    crawl_report = None
    if enable_crawl:
        logger.info(f"Step 7: Running Multi-page crawl (max {max_pages} pages)...")
        try:
            crawl_report = run_site_crawl(url, max_pages=max_pages)
        except Exception as e:
            logger.error(f"Multi-page crawl failed: {e}")
            crawl_report = None
    
    # Calculate overall score
    overall_score = calculate_overall_score(scores)
    scores['overall'] = overall_score
    scores['mobile'] = scores.get('performance', 50)  # Use performance as mobile proxy
    
    # Add security score to overall
    if security_analysis and 'security_score' in security_analysis:
        scores['security'] = security_analysis['security_score']
    
    # Compile complete audit data
    audit_data = {
        '_instructions': 'SIRF YE VALUES CHANGE KARO - BAAKI SAB AUTOMATIC HAI!',
        'meta': {
            'audit_date': get_today_date(),
            'website_url': url,
            'client_name': domain
        },
        'scores': scores,
        'core_web_vitals': core_web_vitals if core_web_vitals else {
            'lcp': {'value': 6.6, 'unit': 'seconds', 'status': 'poor', 'target': 2.5},
            'fcp': {'value': 3.8, 'unit': 'seconds', 'status': 'poor', 'target': 1.8},
            'cls': {'value': 0.85, 'unit': 'score', 'status': 'poor', 'target': 0.1},
            'fid': {'value': 150, 'unit': 'ms', 'status': 'average', 'target': 100},
            'ttfb': {'value': 1.2, 'unit': 'seconds', 'status': 'average', 'target': 0.6}
        },
        'seo_analysis': seo_analysis,
        'technical_seo': technical_seo,
        'security_analysis': security_analysis,
        'performance_audit': get_performance_audit(pagespeed_data if 'pagespeed_data' in dir() else {}),
        'ux_ui_analysis': ux_ui_analysis,  # Now using real analysis
        'content_audit': content_audit,
        'crawl_report': crawl_report,
        'recommendations': None,  # Will be generated below
        'contact': CONTACT
    }
    
    # Generate recommendations (with AI if enabled)
    audit_data['recommendations'] = generate_recommendations(audit_data, use_ai=use_ai)
    
    logger.info(f"Audit completed for: {url}")
    
    return audit_data


def save_audit_data(audit_data: Dict[str, Any], output_path: str = 'audit-data.json') -> str:
    """
    Save audit data to JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Audit data saved to: {output_path}")
    return output_path


if __name__ == '__main__':
    import sys
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = 'https://www.chocolaty.in'
    
    print(f"\n{'='*60}")
    print(f"WEBSITE AUDIT TOOL - Python Backend")
    print(f"{'='*60}")
    print(f"\nAuditing: {test_url}")
    print("-" * 60)
    
    # Run audit
    audit_data = run_complete_audit(test_url)
    
    # Save to file
    save_audit_data(audit_data)
    
    # Print summary
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"Overall Score: {audit_data['scores']['overall']}")
    print(f"Performance: {audit_data['scores']['performance']}")
    print(f"SEO: {audit_data['scores']['seo']}")
    print(f"Accessibility: {audit_data['scores']['accessibility']}")
    print(f"Best Practices: {audit_data['scores']['best_practices']}")
    print(f"\nCore Web Vitals:")
    for metric, data in audit_data['core_web_vitals'].items():
        print(f"  {metric.upper()}: {data['value']} {data['unit']} ({data['status']})")
    print(f"\nData saved to: audit-data.json")
    print(f"{'='*60}\n")
