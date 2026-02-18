"""
Website Audit Tool - Security Analyzer Module
Analyzes website security: SSL, Security Headers, Vulnerabilities
"""

import logging
import ssl
import socket
from typing import Dict, Any, List
from urllib.parse import urlparse
import requests

# Import from parent module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, USER_AGENT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """
    Security analyzer class for SSL, headers, and vulnerability checks
    """
    
    def __init__(self, url: str):
        self.url = url
        self.parsed_url = urlparse(url)
        self.domain = self.parsed_url.netloc
        self._response = None
    
    def fetch_page(self) -> bool:
        """
        Fetch page for header analysis
        """
        try:
            headers = {'User-Agent': USER_AGENT}
            self._response = requests.get(self.url, headers=headers, timeout=REQUEST_TIMEOUT)
            return True
        except Exception as e:
            logger.warning(f"Could not fetch page for security analysis: {e}")
            return False
    
    def analyze_security(self) -> Dict[str, Any]:
        """
        Run complete security analysis
        """
        logger.info(f"Starting Security analysis for: {self.url}")
        
        self.fetch_page()
        
        analysis = {
            'ssl_certificate': self.check_ssl_certificate(),
            'security_headers': self.check_security_headers(),
            'vulnerabilities': self.check_vulnerabilities(),
            'mixed_content': self.check_mixed_content(),
            'cors_policy': self.check_cors_policy(),
            'https_redirect': self.check_https_redirect(),
            'security_score': 0
        }
        
        # Calculate security score
        analysis['security_score'] = self._calculate_security_score(analysis)
        
        logger.info("Security analysis completed")
        return analysis
    
    def check_ssl_certificate(self) -> Dict[str, Any]:
        """
        Check SSL certificate details
        """
        result = {
            'enabled': self.url.startswith('https://'),
            'valid': False,
            'issuer': '',
            'expires_days': 0,
            'protocol': '',
            'issues': []
        }
        
        if not result['enabled']:
            result['issues'].append('Site not using HTTPS - critical security risk')
            return result
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    result['valid'] = True
                    result['issuer'] = dict(x[0] for x in cert.get('issuer', [])).get('organizationName', 'Unknown')
                    
                    # Get expiry date
                    from datetime import datetime
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    result['expires_days'] = days_until_expiry
                    
                    # Get protocol
                    result['protocol'] = ssock.version()
                    
                    # Check for issues
                    if days_until_expiry < 30:
                        result['issues'].append(f'SSL certificate expires in {days_until_expiry} days')
                    if days_until_expiry < 0:
                        result['valid'] = False
                        result['issues'].append('SSL certificate has expired')
                    
        except ssl.SSLCertVerificationError as e:
            result['issues'].append(f'SSL certificate verification failed: {str(e)}')
        except Exception as e:
            result['issues'].append(f'Could not verify SSL certificate: {str(e)}')
        
        return result
    
    def check_security_headers(self) -> Dict[str, Any]:
        """
        Check for important security headers
        """
        headers_to_check = {
            'strict-transport-security': {
                'name': 'Strict-Transport-Security (HSTS)',
                'description': 'Forces HTTPS connections',
                'critical': True
            },
            'content-security-policy': {
                'name': 'Content-Security-Policy (CSP)',
                'description': 'Prevents XSS attacks',
                'critical': True
            },
            'x-frame-options': {
                'name': 'X-Frame-Options',
                'description': 'Prevents clickjacking',
                'critical': False
            },
            'x-content-type-options': {
                'name': 'X-Content-Type-Options',
                'description': 'Prevents MIME sniffing',
                'critical': False
            },
            'x-xss-protection': {
                'name': 'X-XSS-Protection',
                'description': 'XSS filter (legacy)',
                'critical': False
            },
            'referrer-policy': {
                'name': 'Referrer-Policy',
                'description': 'Controls referrer information',
                'critical': False
            },
            'permissions-policy': {
                'name': 'Permissions-Policy',
                'description': 'Controls browser features',
                'critical': False
            }
        }
        
        result = {
            'headers_found': [],
            'headers_missing': [],
            'issues': []
        }
        
        if self._response is None:
            result['issues'].append('Could not fetch headers')
            return result
        
        response_headers = {k.lower(): v for k, v in self._response.headers.items()}
        
        for header_key, header_info in headers_to_check.items():
            if header_key in response_headers:
                result['headers_found'].append({
                    'name': header_info['name'],
                    'value': response_headers[header_key][:100]  # Truncate long values
                })
            else:
                result['headers_missing'].append({
                    'name': header_info['name'],
                    'description': header_info['description'],
                    'critical': header_info['critical']
                })
                if header_info['critical']:
                    result['issues'].append(f"Missing critical header: {header_info['name']}")
        
        return result
    
    def check_vulnerabilities(self) -> Dict[str, Any]:
        """
        Check for common vulnerabilities
        """
        result = {
            'issues': [],
            'warnings': [],
            'safe': []
        }
        
        if self._response is None:
            result['issues'].append('Could not check vulnerabilities')
            return result
        
        response_headers = {k.lower(): v for k, v in self._response.headers.items()}
        
        # Check for server version disclosure
        server_header = response_headers.get('server', '')
        if server_header and any(version in server_header.lower() for version in ['apache/', 'nginx/', 'iis/']):
            result['warnings'].append(f'Server version disclosed: {server_header}')
        
        # Check for powered-by header
        powered_by = response_headers.get('x-powered-by', '')
        if powered_by:
            result['warnings'].append(f'Technology stack disclosed: {powered_by}')
        
        # Check for cookies security
        set_cookie = response_headers.get('set-cookie', '')
        if set_cookie:
            cookie_issues = []
            if 'secure' not in set_cookie.lower():
                cookie_issues.append('Cookie without Secure flag')
            if 'httponly' not in set_cookie.lower():
                cookie_issues.append('Cookie without HttpOnly flag')
            if 'samesite' not in set_cookie.lower():
                cookie_issues.append('Cookie without SameSite attribute')
            
            if cookie_issues:
                result['warnings'].append(f'Cookie security issues: {", ".join(cookie_issues)}')
        
        # Check for information disclosure
        if response_headers.get('x-aspnet-version'):
            result['warnings'].append('ASP.NET version disclosed')
        
        # Positive checks
        if not server_header or '/' not in server_header:
            result['safe'].append('Server version not disclosed')
        
        return result
    
    def check_mixed_content(self) -> Dict[str, Any]:
        """
        Check for mixed content (HTTP resources on HTTPS page)
        """
        result = {
            'has_mixed_content': False,
            'mixed_content_count': 0,
            'issues': []
        }
        
        if not self.url.startswith('https://'):
            return result
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self._response.text, 'lxml') if self._response else None
            
            if soup:
                # Check for HTTP resources
                http_resources = []
                
                # Check images
                for img in soup.find_all('img', src=True):
                    if img['src'].startswith('http://'):
                        http_resources.append(f"Image: {img['src'][:50]}")
                
                # Check scripts
                for script in soup.find_all('script', src=True):
                    if script['src'].startswith('http://'):
                        http_resources.append(f"Script: {script['src'][:50]}")
                
                # Check stylesheets
                for link in soup.find_all('link', rel='stylesheet', href=True):
                    if link['href'].startswith('http://'):
                        http_resources.append(f"Stylesheet: {link['href'][:50]}")
                
                if http_resources:
                    result['has_mixed_content'] = True
                    result['mixed_content_count'] = len(http_resources)
                    result['issues'].append(f'{len(http_resources)} HTTP resources found on HTTPS page (mixed content)')
                    result['examples'] = http_resources[:5]  # First 5 examples
        except Exception as e:
            logger.warning(f"Could not check mixed content: {e}")
        
        return result
    
    def check_cors_policy(self) -> Dict[str, Any]:
        """
        Check CORS (Cross-Origin Resource Sharing) policy
        """
        result = {
            'has_cors': False,
            'cors_origin': '',
            'is_wildcard': False,
            'issues': []
        }
        
        if self._response is None:
            return result
        
        response_headers = {k.lower(): v for k, v in self._response.headers.items()}
        
        # Check Access-Control-Allow-Origin
        cors_origin = response_headers.get('access-control-allow-origin', '')
        if cors_origin:
            result['has_cors'] = True
            result['cors_origin'] = cors_origin
            
            if cors_origin == '*':
                result['is_wildcard'] = True
                result['issues'].append('CORS allows all origins (*) - potential security risk')
        
        return result
    
    def check_https_redirect(self) -> Dict[str, Any]:
        """
        Check if HTTP redirects to HTTPS
        """
        result = {
            'redirects_to_https': False,
            'redirect_url': '',
            'issues': []
        }
        
        if self.url.startswith('https://'):
            result['redirects_to_https'] = True
            return result
        
        # Try HTTP version
        http_url = self.url.replace('https://', 'http://')
        try:
            response = requests.get(http_url, timeout=REQUEST_TIMEOUT, allow_redirects=False)
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('location', '')
                result['redirect_url'] = location
                if location.startswith('https://'):
                    result['redirects_to_https'] = True
                else:
                    result['issues'].append('HTTP does not redirect to HTTPS')
            else:
                result['issues'].append('HTTP version accessible without redirect')
        except Exception as e:
            # If HTTP fails, that's actually good
            result['redirects_to_https'] = True
        
        return result
    
    def _calculate_security_score(self, analysis: Dict[str, Any]) -> int:
        """
        Calculate overall security score
        """
        score = 100
        
        # SSL Certificate (40 points)
        ssl = analysis.get('ssl_certificate', {})
        if not ssl.get('enabled'):
            score -= 40
        elif not ssl.get('valid'):
            score -= 30
        elif ssl.get('expires_days', 0) < 30:
            score -= 10
        
        # Security Headers (30 points)
        headers = analysis.get('security_headers', {})
        missing_critical = sum(1 for h in headers.get('headers_missing', []) if h.get('critical'))
        score -= missing_critical * 15
        
        missing_non_critical = sum(1 for h in headers.get('headers_missing', []) if not h.get('critical'))
        score -= missing_non_critical * 3
        
        # Vulnerabilities (20 points)
        vulns = analysis.get('vulnerabilities', {})
        score -= len(vulns.get('issues', [])) * 10
        score -= len(vulns.get('warnings', [])) * 3
        
        # Mixed Content (10 points)
        mixed = analysis.get('mixed_content', {})
        if mixed.get('has_mixed_content'):
            score -= 10
        
        # CORS Policy (5 points)
        cors = analysis.get('cors_policy', {})
        if cors.get('is_wildcard'):
            score -= 5
        
        # HTTPS Redirect (5 points)
        https_redirect = analysis.get('https_redirect', {})
        if not https_redirect.get('redirects_to_https'):
            score -= 5
        
        return max(0, min(100, score))


def run_security_analysis(url: str) -> Dict[str, Any]:
    """
    Run complete security analysis
    """
    analyzer = SecurityAnalyzer(url)
    return analyzer.analyze_security()


if __name__ == '__main__':
    # Test the analyzer
    test_url = 'https://www.chocolaty.in'
    result = run_security_analysis(test_url)
    print(f"Security Score: {result.get('security_score')}")
    print(f"SSL: {result.get('ssl_certificate')}")
    print(f"Headers Missing: {result.get('security_headers', {}).get('headers_missing', [])}")
    print(f"Vulnerabilities: {result.get('vulnerabilities')}")
