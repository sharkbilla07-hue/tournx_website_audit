"""
Website Audit Tool - Flask API Server
Provides REST API endpoints for the frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import requests
import socket

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audit_runner import run_complete_audit, save_audit_data
from utils.helpers import normalize_url, is_valid_url

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
AUDIT_OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audit-data.json')

# Simple in-memory cache for audit results
audit_cache = {}
CACHE_DURATION = timedelta(hours=1)  # Cache results for 1 hour


def get_cache_key(url):
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()


def get_cached_audit(url):
    """Get cached audit result if available and not expired"""
    key = get_cache_key(url)
    if key in audit_cache:
        cached = audit_cache[key]
        if datetime.now() - cached['timestamp'] < CACHE_DURATION:
            logger.info(f"Cache hit for: {url}")
            return cached['data']
    return None


def set_cached_audit(url, data):
    """Cache audit result"""
    key = get_cache_key(url)
    audit_cache[key] = {
        'data': data,
        'timestamp': datetime.now()
    }
    logger.info(f"Cached audit for: {url}")


def check_url_accessible(url):
    """
    Check if URL is actually accessible (website exists)
    Returns: (is_accessible: bool, error_message: str or None)
    """
    try:
        # Extract domain for DNS check first
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # DNS resolution check
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            return False, f"Website '{domain}' does not exist or DNS resolution failed"
        
        # HTTP request check with short timeout
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code >= 400:
            return False, f"Website returned error status: {response.status_code}"
        
        return True, None
        
    except requests.exceptions.Timeout:
        return False, "Website is not responding (timeout)"
    except requests.exceptions.ConnectionError as e:
        return False, "Could not connect to website. Please check if the URL is correct."
    except Exception as e:
        logger.error(f"URL check error: {e}")
        return False, f"Could not access website: {str(e)}"


@app.route('/')
def index():
    """
    API root endpoint
    """
    return jsonify({
        'name': 'Website Audit Tool API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/audit': 'Run website audit',
            'GET /api/status/<audit_id>': 'Get audit status',
            'GET /api/data': 'Get latest audit data',
            'GET /health': 'Health check'
        }
    })


@app.route('/health')
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/audit', methods=['POST'])
def run_audit():
    """
    Run website audit
    """
    try:
        # Get URL from request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        url = data['url']
        
        # Normalize URL
        url = normalize_url(url)
        
        # Validate URL
        if not is_valid_url(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format'
            }), 400
        
        # Check if website is actually accessible
        is_accessible, error_msg = check_url_accessible(url)
        if not is_accessible:
            logger.warning(f"URL not accessible: {url} - {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'url_not_accessible'
            }), 400
        
        logger.info(f"Starting audit for: {url}")
        
        # Run audit
        audit_data = run_complete_audit(url)
        
        # Save to file
        save_audit_data(audit_data, AUDIT_OUTPUT_PATH)
        
        return jsonify({
            'success': True,
            'data': audit_data,
            'message': 'Audit completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Audit error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/audit/sync', methods=['POST'])
def run_audit_sync():
    """
    Run website audit synchronously and return data
    Uses caching to avoid repeated audits of same URL
    """
    try:
        # Get URL from request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        url = normalize_url(data['url'])
        
        if not is_valid_url(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format'
            }), 400
        
        # Check if website is actually accessible
        is_accessible, error_msg = check_url_accessible(url)
        if not is_accessible:
            logger.warning(f"URL not accessible: {url} - {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'url_not_accessible'
            }), 400
        
        # Check cache first
        cached_result = get_cached_audit(url)
        if cached_result:
            logger.info(f"Returning cached result for: {url}")
            return jsonify(cached_result)
        
        logger.info(f"Starting sync audit for: {url}")
        
        # Run audit
        audit_data = run_complete_audit(url)
        
        # Cache the result
        set_cached_audit(url, audit_data)
        
        # Save to file
        save_audit_data(audit_data, AUDIT_OUTPUT_PATH)
        
        # Return the data directly
        return jsonify(audit_data)
        
    except Exception as e:
        logger.error(f"Sync audit error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data', methods=['GET'])
def get_audit_data():
    """
    Get latest audit data
    """
    try:
        if os.path.exists(AUDIT_OUTPUT_PATH):
            with open(AUDIT_OUTPUT_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({
                'success': False,
                'error': 'No audit data found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status/<audit_id>')
def get_status(audit_id):
    """
    Get audit status (for future async implementation)
    """
    return jsonify({
        'audit_id': audit_id,
        'status': 'completed',
        'progress': 100
    })


@app.route('/api/sample', methods=['GET'])
def get_sample_data():
    """
    Get sample audit data for testing
    """
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audit-data.json')
    
    try:
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({
                'success': False,
                'error': 'Sample data not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear the audit cache
    """
    global audit_cache
    audit_cache = {}
    logger.info("Audit cache cleared")
    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully'
    })


@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """
    Get cache status
    """
    return jsonify({
        'cached_audits': len(audit_cache),
        'cache_duration_hours': CACHE_DURATION.total_seconds() / 3600
    })


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("WEBSITE AUDIT TOOL - Python Backend Server")
    print("="*60)
    print("\nServer starting on http://localhost:5000")
    print("API Endpoints:")
    print("  - POST /api/audit      : Run website audit")
    print("  - POST /api/audit/sync : Run audit and get data")
    print("  - GET  /api/data       : Get latest audit data")
    print("  - GET  /api/sample     : Get sample audit data")
    print("  - GET  /health         : Health check")
    print("-"*60 + "\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
