"""
Website Audit Tool - Utility Functions
Helper functions for the audit process
"""

from datetime import datetime
from urllib.parse import urlparse
import re


def normalize_url(url: str) -> str:
    """
    Normalize URL - ensure it has protocol
    """
    url = url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc or url.replace('https://', '').replace('http://', '').split('/')[0]
    except:
        return url.replace('https://', '').replace('http://', '').split('/')[0]


def get_today_date() -> str:
    """
    Get today's date formatted
    """
    return datetime.now().strftime('%d %B, %Y')


def get_status(score: float) -> str:
    """
    Get status based on score
    """
    if score >= 80:
        return 'good'
    elif score >= 50:
        return 'average'
    return 'poor'


def get_status_label(status: str) -> str:
    """
    Get status label
    """
    labels = {
        'good': 'Good',
        'average': 'Fair',
        'poor': 'Poor'
    }
    return labels.get(status, 'Unknown')


def calculate_overall_score(scores: dict) -> int:
    """
    Calculate overall score from individual scores
    """
    values = [v for v in scores.values() if isinstance(v, (int, float))]
    if not values:
        return 0
    return round(sum(values) / len(values))


def get_core_web_vital_status(value: float, target: float, metric: str) -> str:
    """
    Get Core Web Vital status based on metric type
    """
    thresholds = {
        'lcp': {'good': 2.5, 'average': 4.0},
        'fcp': {'good': 1.8, 'average': 3.0},
        'cls': {'good': 0.1, 'average': 0.25},
        'fid': {'good': 100, 'average': 300},
        'ttfb': {'good': 0.6, 'average': 1.5},
        'speed_index': {'good': 3.0, 'average': 5.0}
    }
    
    if metric not in thresholds:
        return 'average'
    
    thresh = thresholds[metric]
    if value <= thresh['good']:
        return 'good'
    elif value <= thresh['average']:
        return 'average'
    return 'poor'


def count_words(text: str) -> int:
    """
    Count words in text
    """
    if not text:
        return 0
    # Remove extra whitespace and split
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)


def calculate_keyword_density(text: str, keyword: str) -> float:
    """
    Calculate keyword density in text
    """
    if not text or not keyword:
        return 0.0
    
    total_words = count_words(text)
    if total_words == 0:
        return 0.0
    
    # Count keyword occurrences (case insensitive)
    keyword_count = len(re.findall(rf'\b{re.escape(keyword)}\b', text.lower()))
    
    return round((keyword_count / total_words) * 100, 2)


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max length with ellipsis
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def clean_html_text(text: str) -> str:
    """
    Clean HTML text - remove extra whitespace
    """
    if not text:
        return ''
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
