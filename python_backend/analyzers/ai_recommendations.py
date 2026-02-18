"""
Website Audit Tool - AI Recommendations Module
Uses Google Gemini API (FREE) for intelligent recommendations
"""

import logging
import json
from typing import Dict, Any, List, Optional

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API Configuration
# Get your FREE API key from: https://makersuite.google.com/app/apikey
# Set the API key as an environment variable: GEMINI_API_KEY
# On Render.com: Dashboard → Environment → Add GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # Read from environment variable
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent'


def get_ai_recommendations(audit_data: Dict[str, Any], use_ai: bool = True) -> Dict[str, List]:
    """
    Get AI-powered recommendations based on audit data
    Uses Google Gemini API (FREE tier available)
    """
    recommendations = {
        'critical': [],
        'high_priority': [],
        'medium_priority': [],
        'quick_wins': []
    }
    
    # Try AI recommendations first
    if use_ai and GEMINI_API_KEY:
        try:
            ai_recs = _get_gemini_recommendations(audit_data)
            if ai_recs:
                return ai_recs
        except Exception as e:
            logger.warning(f"AI recommendations failed: {e}, falling back to rule-based")
    
    # Fallback to rule-based recommendations
    return _get_rule_based_recommendations(audit_data)


def _get_gemini_recommendations(audit_data: Dict[str, Any]) -> Optional[Dict[str, List]]:
    """
    Get recommendations from Google Gemini API
    """
    import requests
    
    # Prepare the prompt
    prompt = _create_audit_prompt(audit_data)
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{
                    'parts': [{'text': prompt}]
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            # Parse the response
            return _parse_ai_response(text)
        else:
            logger.warning(f"Gemini API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return None


def _create_audit_prompt(audit_data: Dict[str, Any]) -> str:
    """
    Create a prompt for the AI based on audit data
    """
    scores = audit_data.get('scores', {})
    cwv = audit_data.get('core_web_vitals', {})
    seo = audit_data.get('seo_analysis', {})
    technical = audit_data.get('technical_seo', {})
    security = audit_data.get('security_analysis', {})
    
    prompt = f"""You are a website audit expert. Based on the following audit data, provide specific, actionable recommendations.

AUDIT DATA:
- Overall Score: {scores.get('overall', 0)}/100
- Performance Score: {scores.get('performance', 0)}/100
- SEO Score: {scores.get('seo', 0)}/100
- Accessibility Score: {scores.get('accessibility', 0)}/100
- Best Practices Score: {scores.get('best_practices', 0)}/100

CORE WEB VITALS:
- LCP (Largest Contentful Paint): {cwv.get('lcp', {}).get('value', 'N/A')} seconds (target: 2.5s)
- FCP (First Contentful Paint): {cwv.get('fcp', {}).get('value', 'N/A')} seconds (target: 1.8s)
- CLS (Cumulative Layout Shift): {cwv.get('cls', {}).get('value', 'N/A')} (target: 0.1)

SEO ISSUES:
- Title Issues: {seo.get('meta_tags', {}).get('title', {}).get('issues', [])}
- Description Issues: {seo.get('meta_tags', {}).get('description', {}).get('issues', [])}
- Images without Alt: {seo.get('images', {}).get('without_alt', 0)}
- Structured Data: {seo.get('structured_data', {}).get('exists', False)}
- Open Graph: {seo.get('open_graph', {}).get('exists', False)}

SECURITY:
- SSL Enabled: {security.get('ssl_certificate', {}).get('enabled', False)}
- Security Headers Missing: {len(security.get('security_headers', {}).get('headers_missing', []))}

Provide recommendations in this EXACT JSON format:
{{
    "critical": [
        {{"issue": "Issue name", "impact": "High/Medium/Low", "effort": "High/Medium/Low", "description": "How to fix", "expected_improvement": "Expected result"}}
    ],
    "high_priority": [...],
    "medium_priority": [...],
    "quick_wins": [...]
}}

Only include 2-3 items per category. Be specific and actionable."""
    
    return prompt


def _parse_ai_response(text: str) -> Dict[str, List]:
    """
    Parse AI response into structured recommendations
    """
    try:
        # Try to extract JSON from the response
        import re
        
        # Find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Return empty if parsing fails
    return {
        'critical': [],
        'high_priority': [],
        'medium_priority': [],
        'quick_wins': []
    }


def _get_rule_based_recommendations(audit_data: Dict[str, Any]) -> Dict[str, List]:
    """
    Generate rule-based recommendations (fallback when AI is not available)
    """
    recommendations = {
        'critical': [],
        'high_priority': [],
        'medium_priority': [],
        'quick_wins': []
    }
    
    scores = audit_data.get('scores', {})
    cwv = audit_data.get('core_web_vitals', {})
    seo = audit_data.get('seo_analysis', {})
    technical = audit_data.get('technical_seo', {})
    security = audit_data.get('security_analysis', {})
    
    # Critical Issues
    if scores.get('performance', 100) < 50:
        recommendations['critical'].append({
            'issue': 'Critical Performance Issues',
            'impact': 'High',
            'effort': 'Medium',
            'description': 'Optimize images, enable compression, implement lazy loading, and minimize JavaScript',
            'expected_improvement': '40-60% faster page load time'
        })
    
    if cwv.get('lcp', {}).get('value', 0) > 4.0:
        recommendations['critical'].append({
            'issue': 'Very Slow Largest Contentful Paint',
            'impact': 'High',
            'effort': 'Medium',
            'description': 'Optimize server response time, use CDN, optimize images, and remove render-blocking resources',
            'expected_improvement': 'LCP under 2.5 seconds'
        })
    
    if not security.get('ssl_certificate', {}).get('enabled', True):
        recommendations['critical'].append({
            'issue': 'No SSL Certificate',
            'impact': 'High',
            'effort': 'Low',
            'description': 'Install SSL certificate to enable HTTPS - critical for security and SEO',
            'expected_improvement': 'Secure connection, better SEO rankings'
        })
    
    # High Priority Issues
    images_without_alt = seo.get('images', {}).get('without_alt', 0)
    if images_without_alt > 0:
        recommendations['high_priority'].append({
            'issue': f'{images_without_alt} Images Missing Alt Text',
            'impact': 'Medium',
            'effort': 'Low',
            'description': 'Add descriptive alt text to all images for better SEO and accessibility',
            'expected_improvement': 'Improved SEO and accessibility compliance'
        })
    
    if not seo.get('structured_data', {}).get('exists', False):
        recommendations['high_priority'].append({
            'issue': 'No Structured Data Markup',
            'impact': 'Medium',
            'effort': 'Low',
            'description': 'Implement Schema.org markup for rich snippets in search results',
            'expected_improvement': 'Rich snippets, better CTR in search results'
        })
    
    missing_headers = security.get('security_headers', {}).get('headers_missing', [])
    critical_headers = [h for h in missing_headers if h.get('critical')]
    if critical_headers:
        recommendations['high_priority'].append({
            'issue': 'Missing Security Headers',
            'impact': 'Medium',
            'effort': 'Low',
            'description': f"Add security headers: {', '.join([h['name'] for h in critical_headers[:3]])}",
            'expected_improvement': 'Better protection against XSS, clickjacking attacks'
        })
    
    # Medium Priority Issues
    if cwv.get('cls', {}).get('value', 0) > 0.25:
        recommendations['medium_priority'].append({
            'issue': 'High Cumulative Layout Shift',
            'impact': 'Medium',
            'effort': 'Medium',
            'description': 'Set explicit dimensions for images and embeds, avoid inserting content above existing content',
            'expected_improvement': 'More stable page layout, better user experience'
        })
    
    if not seo.get('open_graph', {}).get('exists', False):
        recommendations['medium_priority'].append({
            'issue': 'Missing Open Graph Tags',
            'impact': 'Low',
            'effort': 'Low',
            'description': 'Add Open Graph meta tags for better social media sharing',
            'expected_improvement': 'Better appearance when shared on social media'
        })
    
    # Quick Fixes
    recommendations['quick_wins'].append({
        'issue': 'Enable Browser Caching',
        'impact': 'Medium',
        'effort': 'Very Low',
        'description': 'Add cache-control headers for static resources',
        'expected_improvement': 'Faster repeat visits, reduced server load'
    })
    
    recommendations['quick_wins'].append({
        'issue': 'Minify CSS and JavaScript',
        'impact': 'Medium',
        'effort': 'Very Low',
        'description': 'Enable minification for CSS and JavaScript files',
        'expected_improvement': '10-15% reduction in file size'
    })
    
    recommendations['quick_wins'].append({
        'issue': 'Enable GZIP/Brotli Compression',
        'impact': 'Medium',
        'effort': 'Very Low',
        'description': 'Enable server-side compression for text-based resources',
        'expected_improvement': '60-80% reduction in transfer size'
    })
    
    return recommendations


if __name__ == '__main__':
    # Test with sample data
    sample_audit = {
        'scores': {
            'overall': 52,
            'performance': 35,
            'seo': 65,
            'accessibility': 77,
            'best_practices': 80
        },
        'core_web_vitals': {
            'lcp': {'value': 6.6, 'status': 'poor'},
            'fcp': {'value': 3.8, 'status': 'poor'},
            'cls': {'value': 0.85, 'status': 'poor'}
        },
        'seo_analysis': {
            'images': {'without_alt': 7},
            'structured_data': {'exists': False},
            'open_graph': {'exists': True}
        },
        'security_analysis': {
            'ssl_certificate': {'enabled': True},
            'security_headers': {'headers_missing': [{'name': 'Content-Security-Policy', 'critical': True}]}
        }
    }
    
    result = get_ai_recommendations(sample_audit, use_ai=False)  # Use rule-based for testing
    print("Recommendations:")
    for category, items in result.items():
        print(f"\n{category.upper()}:")
        for item in items:
            print(f"  - {item['issue']}: {item['description']}")
