"""
Website Audit Tool - Configuration
Hybrid approach: Lighthouse + PageSpeed API + BeautifulSoup
"""

import os

# =============================================
# PAGESPEED API CONFIGURATION
# =============================================

# Google PageSpeed Insights API (Free tier: 25,000 requests/day)
# Get your API key from: https://console.cloud.google.com/apis/credentials
# Set the API key as an environment variable: PAGESPEED_API_KEY
# On Render.com: Dashboard → Environment → Add PAGESPEED_API_KEY
PAGESPEED_API_KEY = os.environ.get('PAGESPEED_API_KEY', '')  # Read from environment variable
PAGESPEED_API_URL = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'

# Categories to analyze
PAGESPEED_CATEGORIES = ['performance', 'accessibility', 'best-practices', 'seo']

# =============================================
# LIGHTHOUSE CLI CONFIGURATION
# =============================================

# Lighthouse CLI settings (Completely FREE, unlimited)
LIGHTHOUSE_ENABLED = True
LIGHTHOUSE_TIMEOUT = 120  # seconds

# =============================================
# TARGET METRICS (Industry Standards)
# =============================================

TARGETS = {
    'lcp': 2.5,      # Largest Contentful Paint (seconds)
    'fcp': 1.8,      # First Contentful Paint (seconds)
    'cls': 0.1,      # Cumulative Layout Shift
    'fid': 100,      # First Input Delay (ms)
    'ttfb': 0.6,     # Time to First Byte (seconds)
    'speed_index': 3.0  # Speed Index (seconds)
}

# =============================================
# CONTACT INFO (Customize for your agency)
# =============================================

CONTACT = {
    'agency_name': 'TournX Web Studio',
    'email': 'hello@tournxwebstudio.com',
    'phone': '+91-9876543210',
    'whatsapp': '+91-9876543210',
    'website': 'tournxwebstudio.com'
}

# =============================================
# REQUEST SETTINGS
# =============================================

REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# =============================================
# SEO ANALYSIS SETTINGS
# =============================================

SEO_SETTINGS = {
    'title_min_length': 30,
    'title_max_length': 60,
    'description_min_length': 120,
    'description_max_length': 160,
    'max_h1_tags': 1,
    'min_word_count': 300
}

# =============================================
# INDUSTRY STANDARDS (for comparison)
# =============================================

INDUSTRY_STANDARDS = {
    'performance': 75,
    'seo': 80,
    'mobile': 80,
    'accessibility': 85,
    'load_time': 3.0
}
