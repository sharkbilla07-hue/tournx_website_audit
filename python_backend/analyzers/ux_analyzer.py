"""
Website Audit Tool - UX/UI Analyzer Module
Analyzes actual website HTML for UX/UI issues
"""

import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import re

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, USER_AGENT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UXAnalyzer:
    """
    UX/UI Analyzer - Analyzes website for user experience issues
    """
    
    def __init__(self, url: str, scraper=None):
        self.url = url
        self.scraper = scraper
        self.soup = None
        
    def analyze(self) -> Dict[str, Any]:
        """
        Run complete UX/UI analysis
        """
        logger.info(f"Starting UX/UI analysis for: {self.url}")
        
        # Get soup from scraper if available
        if self.scraper:
            self.soup = self.scraper.get_soup()
        
        if not self.soup:
            logger.warning("No HTML content available for UX analysis")
            return self._get_default_analysis()
        
        results = {
            'navigation': self._analyze_navigation(),
            'cta': self._analyze_cta(),
            'readability': self._analyze_readability(),
            'accessibility': self._analyze_accessibility(),
            'design': self._analyze_design(),
            'forms': self._analyze_forms(),
            'mobile': self._analyze_mobile(),
            'score': 0
        }
        
        # Calculate overall UX score
        scores = []
        if results['navigation'].get('score'):
            scores.append(results['navigation']['score'])
        if results['cta'].get('score'):
            scores.append(results['cta']['score'])
        if results['readability'].get('score'):
            scores.append(results['readability']['score'])
        if results['accessibility'].get('score'):
            scores.append(results['accessibility']['score'])
        if results['design'].get('score'):
            scores.append(results['design']['score'])
        if results['forms'].get('score'):
            scores.append(results['forms']['score'])
            
        if scores:
            results['score'] = round(sum(scores) / len(scores))
        
        logger.info(f"UX/UI analysis completed with score: {results['score']}")
        return results
    
    def _analyze_navigation(self) -> Dict[str, Any]:
        """
        Analyze navigation structure
        """
        issues = []
        score = 100
        
        # Check for nav element
        nav_elements = self.soup.find_all('nav')
        if not nav_elements:
            issues.append('No semantic <nav> element found')
            score -= 15
        
        # Check for header navigation
        header = self.soup.find('header')
        if header:
            nav_in_header = header.find('nav') or header.find('ul')
            if not nav_in_header:
                issues.append('No navigation found in header')
                score -= 10
        else:
            issues.append('No semantic <header> element found')
            score -= 10
        
        # Check for breadcrumbs
        breadcrumb_patterns = ['breadcrumb', 'breadcrumbs', 'bread-crumb']
        has_breadcrumb = False
        for pattern in breadcrumb_patterns:
            if self.soup.find(class_=re.compile(pattern, re.I)) or \
               self.soup.find(attrs={'aria-label': re.compile(pattern, re.I)}):
                has_breadcrumb = True
                break
        
        if not has_breadcrumb:
            issues.append('No breadcrumb navigation found')
            score -= 10
        
        # Check navigation links count
        nav_links = self.soup.find_all('a', href=True)
        nav_menu_links = [a for a in nav_links if a.find_parent('nav') or 
                         (a.find_parent('ul') and a.find_parent('li'))]
        
        if len(nav_menu_links) < 3:
            issues.append('Very few navigation links (less than 3)')
            score -= 15
        elif len(nav_menu_links) > 15:
            issues.append('Too many navigation links (more than 15) - can overwhelm users')
            score -= 5
        
        # Check for dropdown menus
        dropdowns = self.soup.find_all(class_=re.compile('dropdown|submenu|sub-menu', re.I))
        if dropdowns:
            # Check if dropdowns have proper ARIA
            for dropdown in dropdowns:
                if not dropdown.get('aria-expanded') and not dropdown.get('aria-haspopup'):
                    issues.append('Dropdown menus missing ARIA attributes')
                    score -= 5
                    break
        
        return {
            'score': max(0, score),
            'nav_elements': len(nav_elements),
            'nav_links': len(nav_menu_links),
            'has_breadcrumb': has_breadcrumb,
            'has_dropdowns': len(dropdowns) > 0 if 'dropdowns' in dir() else False,
            'issues': issues
        }
    
    def _analyze_cta(self) -> Dict[str, Any]:
        """
        Analyze Call-to-Action elements
        """
        issues = []
        score = 100
        ctas = []
        
        # Common CTA patterns
        cta_patterns = [
            'buy', 'purchase', 'order', 'subscribe', 'sign up', 'signup',
            'register', 'join', 'contact', 'get started', 'learn more',
            'book now', 'book', 'hire', 'download', 'try', 'start',
            'call', 'email', 'send', 'submit', 'apply', 'donate'
        ]
        
        # Find all buttons and links
        buttons = self.soup.find_all(['button', 'a'])
        input_buttons = self.soup.find_all('input', {'type': ['submit', 'button']})
        all_clickables = buttons + input_buttons
        
        for element in all_clickables:
            text = element.get_text(strip=True).lower()
            href = element.get('href', '')
            
            # Check if it's a CTA
            is_cta = any(pattern in text for pattern in cta_patterns)
            
            if is_cta:
                ctas.append({
                    'text': element.get_text(strip=True),
                    'tag': element.name,
                    'href': href if href else None
                })
        
        # Analyze CTA placement
        if not ctas:
            issues.append('No clear Call-to-Action buttons found')
            score -= 30
        elif len(ctas) < 2:
            issues.append('Very few Call-to-Action buttons')
            score -= 15
        
        # Check for primary CTA styling (buttons with distinctive classes)
        styled_buttons = self.soup.find_all(['button', 'a'], class_=re.compile(
            'btn|button|cta|primary|action|submit', re.I
        ))
        
        if not styled_buttons:
            issues.append('No styled CTA buttons found - CTAs may not stand out')
            score -= 15
        
        # Check for above-fold CTAs (simplified check)
        # In real implementation, would check actual viewport position
        hero_section = self.soup.find(['section', 'div'], class_=re.compile('hero|banner|header|top', re.I))
        has_above_fold_cta = False
        if hero_section:
            for cta in ctas:
                if hero_section.get_text(strip=True).lower().find(cta['text'].lower()) != -1:
                    has_above_fold_cta = True
                    break
        
        if ctas and not has_above_fold_cta:
            issues.append('No Call-to-Action visible above the fold')
            score -= 20
        
        return {
            'score': max(0, score),
            'cta_count': len(ctas),
            'ctas': ctas[:10],  # Limit to first 10
            'has_styled_buttons': len(styled_buttons) > 0,
            'has_above_fold_cta': has_above_fold_cta if ctas else False,
            'issues': issues
        }
    
    def _analyze_readability(self) -> Dict[str, Any]:
        """
        Analyze content readability
        """
        issues = []
        score = 100
        
        # Get all text content
        paragraphs = self.soup.find_all('p')
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Analyze paragraph length
        long_paragraphs = 0
        total_words = 0
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            words = len(text.split())
            total_words += words
            if words > 150:  # More than 150 words is considered long
                long_paragraphs += 1
        
        if paragraphs and long_paragraphs / len(paragraphs) > 0.3:
            issues.append(f'{long_paragraphs} paragraphs are too long (over 150 words)')
            score -= 10
        
        # Check heading structure
        h1_count = len(self.soup.find_all('h1'))
        if h1_count == 0:
            issues.append('No H1 heading found')
            score -= 20
        elif h1_count > 1:
            issues.append(f'Multiple H1 headings found ({h1_count}) - should be only one')
            score -= 10
        
        # Check heading hierarchy
        heading_levels = [int(h.name[1]) for h in headings]
        if heading_levels:
            prev_level = 0
            for level in heading_levels:
                if level > prev_level + 1 and prev_level != 0:
                    issues.append('Heading hierarchy is not proper (skipped levels)')
                    score -= 10
                    break
                prev_level = level
        
        # Check for sufficient content
        if total_words < 300:
            issues.append(f'Low content volume ({total_words} words) - consider adding more content')
            score -= 15
        
        # Check font sizes in style attributes (simplified)
        small_text_elements = self.soup.find_all(style=re.compile('font-size:\s*\d{1,2}px', re.I))
        for el in small_text_elements:
            style = el.get('style', '')
            match = re.search(r'font-size:\s*(\d+)px', style, re.I)
            if match and int(match.group(1)) < 14:
                issues.append('Some text has font-size smaller than 14px')
                score -= 10
                break
        
        # Check line height (simplified)
        tight_line_height = self.soup.find_all(style=re.compile('line-height:\s*[01]\.\d', re.I))
        if tight_line_height:
            issues.append('Some text has tight line-height (less than 1.5)')
            score -= 5
        
        return {
            'score': max(0, score),
            'word_count': total_words,
            'paragraph_count': len(paragraphs),
            'heading_count': len(headings),
            'h1_count': h1_count,
            'long_paragraphs': long_paragraphs,
            'issues': issues
        }
    
    def _analyze_accessibility(self) -> Dict[str, Any]:
        """
        Analyze accessibility features
        """
        issues = []
        score = 100
        
        # Check images for alt text
        images = self.soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        
        if images_without_alt:
            issues.append(f'{len(images_without_alt)} images missing alt text')
            score -= min(20, len(images_without_alt) * 2)
        
        # Check for ARIA labels on interactive elements
        buttons = self.soup.find_all('button')
        links_without_text = [a for a in self.soup.find_all('a') if not a.get_text(strip=True) and not a.get('aria-label')]
        
        if links_without_text:
            issues.append(f'{len(links_without_text)} links have no visible text or aria-label')
            score -= min(15, len(links_without_text) * 3)
        
        # Check for skip links
        skip_link = self.soup.find('a', href=re.compile('#main|#content|#skip', re.I))
        if not skip_link:
            issues.append('No skip navigation link found')
            score -= 10
        
        # Check for proper form labels
        inputs = self.soup.find_all('input', {'type': ['text', 'email', 'password', 'tel', 'number']})
        inputs_without_labels = []
        
        for inp in inputs:
            inp_id = inp.get('id')
            if inp_id:
                label = self.soup.find('label', {'for': inp_id})
            else:
                label = inp.find_parent('label')
            
            if not label and not inp.get('aria-label') and not inp.get('placeholder'):
                inputs_without_labels.append(inp)
        
        if inputs_without_labels:
            issues.append(f'{len(inputs_without_labels)} form inputs without labels')
            score -= min(15, len(inputs_without_labels) * 3)
        
        # Check for lang attribute
        html_tag = self.soup.find('html')
        if not html_tag or not html_tag.get('lang'):
            issues.append('HTML element missing lang attribute')
            score -= 10
        
        # Check for focus indicators (simplified - checks for :focus styles in inline styles)
        # This is a basic check; comprehensive check would need CSS parsing
        
        # Check for sufficient color contrast would require CSS analysis
        # For now, we'll flag it as a manual check needed
        
        return {
            'score': max(0, score),
            'images_total': len(images),
            'images_without_alt': len(images_without_alt),
            'links_without_text': len(links_without_text),
            'inputs_without_labels': len(inputs_without_labels),
            'has_skip_link': skip_link is not None,
            'has_lang_attr': html_tag and html_tag.get('lang') is not None,
            'issues': issues
        }
    
    def _analyze_design(self) -> Dict[str, Any]:
        """
        Analyze design elements
        """
        issues = []
        score = 100
        
        # Check for responsive viewport meta
        viewport = self.soup.find('meta', {'name': 'viewport'})
        if not viewport:
            issues.append('No viewport meta tag - page may not be mobile-friendly')
            score -= 20
        elif 'width=device-width' not in viewport.get('content', ''):
            issues.append('Viewport meta tag not properly configured for mobile')
            score -= 10
        
        # Check for favicon
        favicon = self.soup.find('link', rel=re.compile('icon|shortcut', re.I))
        if not favicon:
            issues.append('No favicon found')
            score -= 5
        
        # Check for consistent styling (presence of CSS)
        styles = self.soup.find_all('link', rel='stylesheet')
        inline_styles = self.soup.find_all('style')
        
        if not styles and not inline_styles:
            issues.append('No external or internal CSS found')
            score -= 20
        
        # Check for modern HTML5 elements
        modern_elements = ['header', 'footer', 'main', 'article', 'section', 'aside', 'nav']
        found_modern = [el for el in modern_elements if self.soup.find(el)]
        
        if len(found_modern) < 3:
            issues.append('Limited use of semantic HTML5 elements')
            score -= 10
        
        # Check for social meta tags
        og_tags = self.soup.find_all('meta', property=re.compile('og:', re.I))
        twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile('twitter:', re.I)})
        
        if not og_tags and not twitter_tags:
            issues.append('No Open Graph or Twitter Card meta tags')
            score -= 5
        
        return {
            'score': max(0, score),
            'has_viewport': viewport is not None,
            'has_favicon': favicon is not None,
            'css_files': len(styles),
            'semantic_elements': len(found_modern),
            'has_social_meta': len(og_tags) > 0 or len(twitter_tags) > 0,
            'issues': issues
        }
    
    def _analyze_forms(self) -> Dict[str, Any]:
        """
        Analyze form elements
        """
        issues = []
        score = 100
        
        forms = self.soup.find_all('form')
        
        if not forms:
            return {
                'score': 100,  # No forms is fine
                'forms_count': 0,
                'issues': []
            }
        
        for form in forms:
            # Check for action attribute
            if not form.get('action'):
                issues.append('Form missing action attribute')
                score -= 10
            
            # Check for method attribute
            if not form.get('method'):
                issues.append('Form missing method attribute (defaults to GET)')
                score -= 5
            
            # Check for submit button
            submit_btn = form.find(['button', 'input'], attrs={'type': 'submit'}) or \
                        form.find('button') or \
                        form.find('input', {'type': 'image'})
            
            if not submit_btn:
                issues.append('Form has no submit button')
                score -= 15
            
            # Check for autocomplete
            inputs = form.find_all('input')
            sensitive_inputs = [i for i in inputs if i.get('type') in ['password', 'email', 'tel']]
            
            # Check for CSRF token (simplified)
            hidden_inputs = form.find_all('input', {'type': 'hidden'})
            csrf_found = any('csrf' in (i.get('name', '')).lower() or 
                           'token' in (i.get('name', '')).lower() 
                           for i in hidden_inputs)
            
            if not csrf_found and form.get('method', '').lower() == 'post':
                issues.append('Form may be missing CSRF protection')
                score -= 5
        
        return {
            'score': max(0, score),
            'forms_count': len(forms),
            'issues': issues
        }
    
    def _analyze_mobile(self) -> Dict[str, Any]:
        """
        Analyze mobile-friendliness
        """
        issues = []
        score = 100
        
        # Check viewport
        viewport = self.soup.find('meta', {'name': 'viewport'})
        if not viewport:
            issues.append('No viewport meta tag - critical for mobile')
            score -= 30
        else:
            content = viewport.get('content', '')
            if 'width=device-width' not in content:
                issues.append('Viewport not set to device-width')
                score -= 15
            if 'initial-scale=1' not in content:
                issues.append('Viewport initial-scale not set to 1')
                score -= 5
        
        # Check for mobile-specific styles
        mobile_css = self.soup.find_all('link', media=re.compile('mobile|handheld|max-width', re.I))
        
        # Check for touch-friendly elements (simplified)
        # Large buttons/links are better for touch
        buttons = self.soup.find_all('button')
        small_buttons = []
        for btn in buttons:
            style = btn.get('style', '')
            # Check for small padding/size in inline styles
            if re.search(r'padding:\s*\d{1,2}px', style) or \
               re.search(r'width:\s*\d{1,2}px', style):
                small_buttons.append(btn)
        
        if len(small_buttons) > len(buttons) * 0.3 and buttons:
            issues.append('Some buttons may be too small for touch')
            score -= 10
        
        # Check for tables (often problematic on mobile)
        tables = self.soup.find_all('table')
        if tables:
            responsive_tables = [t for t in tables if 
                               t.find_parent('div', class_=re.compile('responsive|scroll|overflow', re.I)) or
                               t.get('class') and any('responsive' in c for c in t.get('class'))]
            if len(responsive_tables) < len(tables):
                issues.append(f'{len(tables) - len(responsive_tables)} tables may not be mobile-friendly')
                score -= 10
        
        # Check for horizontal scroll risk (elements with fixed large width)
        fixed_width_elements = self.soup.find_all(style=re.compile('width:\s*[5-9]\d{2,}px|width:\s*\d{4,}px', re.I))
        if fixed_width_elements:
            issues.append(f'{len(fixed_width_elements)} elements with fixed width may cause horizontal scroll')
            score -= 10
        
        return {
            'score': max(0, score),
            'has_viewport': viewport is not None,
            'tables_count': len(tables) if 'tables' in dir() else 0,
            'fixed_width_elements': len(fixed_width_elements) if 'fixed_width_elements' in dir() else 0,
            'issues': issues
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        Return default analysis when no HTML is available
        """
        return {
            'navigation': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'cta': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'readability': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'accessibility': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'design': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'forms': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'mobile': {'score': 0, 'issues': ['Could not analyze - no HTML content']},
            'score': 0
        }


def run_ux_analysis(url: str, scraper=None) -> Dict[str, Any]:
    """
    Main function to run UX analysis
    """
    analyzer = UXAnalyzer(url, scraper)
    return analyzer.analyze()