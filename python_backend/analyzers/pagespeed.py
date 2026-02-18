"""
Website Audit Tool - PageSpeed API Integration
Fetches performance data from Google PageSpeed Insights API
"""

import requests
import logging
from typing import Dict, Optional, Any

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PAGESPEED_API_KEY, 
    PAGESPEED_API_URL, 
    PAGESPEED_CATEGORIES,
    REQUEST_TIMEOUT
)
from utils.helpers import get_core_web_vital_status

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_pagespeed_data(url: str, strategy: str = 'mobile') -> Dict[str, Any]:
    """
    Fetch data from Google PageSpeed Insights API
    
    Args:
        url: Website URL to analyze
        strategy: 'mobile' or 'desktop'
    
    Returns:
        Dictionary with PageSpeed results for all categories
    """
    results = {}
    
    for category in PAGESPEED_CATEGORIES:
        try:
            api_url = f"{PAGESPEED_API_URL}?url={requests.utils.quote(url)}&category={category}&strategy={strategy}"
            
            # Add API key if available
            if PAGESPEED_API_KEY:
                api_url += f"&key={PAGESPEED_API_KEY}"
            
            logger.info(f"Fetching PageSpeed data for {category}...")
            
            response = requests.get(api_url, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                results[category] = response.json()
                logger.info(f"Successfully fetched {category} data")
            else:
                logger.warning(f"PageSpeed API error for {category}: {response.status_code}")
                results[category] = None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {category} data")
            results[category] = None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {category}: {e}")
            results[category] = None
        except Exception as e:
            logger.error(f"Unexpected error for {category}: {e}")
            results[category] = None
    
    return results


def parse_pagespeed_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse PageSpeed results into our format
    
    Args:
        results: Raw PageSpeed API results
    
    Returns:
        Parsed results with scores and metrics
    """
    parsed = {
        'scores': {},
        'metrics': {},
        'audits': {}
    }
    
    # Extract scores
    for category, data in results.items():
        if data and 'lighthouseResult' in data:
            categories = data['lighthouseResult'].get('categories', {})
            if category in categories:
                score = categories[category].get('score', 0)
                parsed['scores'][category.replace('-', '_')] = round(score * 100)
    
    # Extract Core Web Vitals from performance data
    performance_data = results.get('performance', {})
    if performance_data and 'lighthouseResult' in performance_data:
        audits = performance_data['lighthouseResult'].get('audits', {})
        
        # Largest Contentful Paint
        lcp = audits.get('largest-contentful-paint', {})
        parsed['metrics']['lcp_seconds'] = round(lcp.get('numericValue', 6600) / 1000, 1)
        
        # First Contentful Paint
        fcp = audits.get('first-contentful-paint', {})
        parsed['metrics']['fcp_seconds'] = round(fcp.get('numericValue', 3800) / 1000, 1)
        
        # Cumulative Layout Shift
        cls = audits.get('cumulative-layout-shift', {})
        parsed['metrics']['cls'] = round(cls.get('numericValue', 0.85), 2)
        
        # Speed Index
        si = audits.get('speed-index', {})
        parsed['metrics']['speed_index_seconds'] = round(si.get('numericValue', 6200) / 1000, 1)
        
        # Total Blocking Time (proxy for FID)
        tbt = audits.get('total-blocking-time', {})
        parsed['metrics']['tbt_ms'] = round(tbt.get('numericValue', 150))
        
        # Time to First Byte
        ttfb = audits.get('server-response-time', {})
        parsed['metrics']['ttfb_seconds'] = round(ttfb.get('numericValue', 1200) / 1000, 1)
        
        # Store important audits
        parsed['audits'] = {
            'bootup-time': audits.get('bootup-time', {}),
            'mainthread-work-breakdown': audits.get('mainthread-work-breakdown', {}),
            'render-blocking-resources': audits.get('render-blocking-resources', {}),
            'uses-optimized-images': audits.get('uses-optimized-images', {}),
            'offscreen-images': audits.get('offscreen-images', {}),
            'unminified-css': audits.get('unminified-css', {}),
            'unminified-javascript': audits.get('unminified-javascript', {}),
            'unused-css-rules': audits.get('unused-css-rules', {}),
            'unused-javascript': audits.get('unused-javascript', {}),
        }
    
    return parsed


def get_core_web_vitals(metrics: Dict[str, float]) -> Dict[str, Dict]:
    """
    Format Core Web Vitals data
    
    Args:
        metrics: Raw metrics from PageSpeed
    
    Returns:
        Formatted Core Web Vitals with status
    """
    return {
        'lcp': {
            'value': metrics.get('lcp_seconds', 6.6),
            'unit': 'seconds',
            'status': get_core_web_vital_status(metrics.get('lcp_seconds', 6.6), 2.5, 'lcp'),
            'target': 2.5
        },
        'fcp': {
            'value': metrics.get('fcp_seconds', 3.8),
            'unit': 'seconds',
            'status': get_core_web_vital_status(metrics.get('fcp_seconds', 3.8), 1.8, 'fcp'),
            'target': 1.8
        },
        'cls': {
            'value': metrics.get('cls', 0.85),
            'unit': 'score',
            'status': get_core_web_vital_status(metrics.get('cls', 0.85), 0.1, 'cls'),
            'target': 0.1
        },
        'fid': {
            'value': metrics.get('tbt_ms', 150),
            'unit': 'ms',
            'status': get_core_web_vital_status(metrics.get('tbt_ms', 150), 100, 'fid'),
            'target': 100
        },
        'ttfb': {
            'value': metrics.get('ttfb_seconds', 1.2),
            'unit': 'seconds',
            'status': get_core_web_vital_status(metrics.get('ttfb_seconds', 1.2), 0.6, 'ttfb'),
            'target': 0.6
        }
    }


def run_pagespeed_audit(url: str) -> Dict[str, Any]:
    """
    Run complete PageSpeed audit
    
    Args:
        url: Website URL to analyze
    
    Returns:
        Complete audit data from PageSpeed
    """
    logger.info(f"Starting PageSpeed audit for: {url}")
    
    # Fetch raw data
    raw_results = fetch_pagespeed_data(url)
    
    # Parse results
    parsed_results = parse_pagespeed_results(raw_results)
    
    # Get Core Web Vitals
    core_web_vitals = get_core_web_vitals(parsed_results['metrics'])
    
    return {
        'scores': parsed_results['scores'],
        'metrics': parsed_results['metrics'],
        'core_web_vitals': core_web_vitals,
        'audits': parsed_results['audits'],
        'raw_data': raw_results  # Keep raw data for detailed analysis
    }


if __name__ == '__main__':
    # Test the module
    test_url = 'https://www.chocolaty.in'
    result = run_pagespeed_audit(test_url)
    print(f"Scores: {result['scores']}")
    print(f"Core Web Vitals: {result['core_web_vitals']}")
