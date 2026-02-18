"""
Website Audit Tool - PDF Report Generator
Generates professional PDF reports from audit data
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

# Import from parent module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_pdf_report(audit_data: Dict[str, Any], output_path: str = None) -> Optional[str]:
    """
    Generate PDF report from audit data
    Uses WeasyPrint (FREE) for PDF generation
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        logger.warning("WeasyPrint not installed. Install with: pip install weasyprint")
        return generate_html_report(audit_data, output_path)
    
    if output_path is None:
        output_path = f"audit-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
    
    # Generate HTML content
    html_content = _generate_report_html(audit_data)
    
    # Generate PDF
    try:
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"PDF report generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return generate_html_report(audit_data, output_path.replace('.pdf', '.html'))


def generate_html_report(audit_data: Dict[str, Any], output_path: str = None) -> Optional[str]:
    """
    Generate standalone HTML report (fallback when PDF not available)
    """
    if output_path is None:
        output_path = f"audit-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    
    # Generate HTML content
    html_content = _generate_report_html(audit_data, standalone=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML report generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"HTML report generation failed: {e}")
        return None


def _generate_report_html(audit_data: Dict[str, Any], standalone: bool = False) -> str:
    """
    Generate HTML content for the report
    """
    meta = audit_data.get('meta', {})
    scores = audit_data.get('scores', {})
    cwv = audit_data.get('core_web_vitals', {})
    seo = audit_data.get('seo_analysis', {})
    technical = audit_data.get('technical_seo', {})
    security = audit_data.get('security_analysis', {})
    recommendations = audit_data.get('recommendations', {})
    
    # Determine overall status
    overall = scores.get('overall', 0)
    if overall >= 80:
        status_class = 'good'
        status_text = 'Good'
    elif overall >= 50:
        status_class = 'average'
        status_text = 'Needs Improvement'
    else:
        status_class = 'poor'
        status_text = 'Critical Issues'
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Audit Report - {meta.get('client_name', 'Website')}</title>
    <style>
        {_get_report_css()}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Cover Page - Always First Page -->
        <div class="cover-page">
            <div class="cover-content">
                <h1 class="report-title">Website Audit Report</h1>
                <div class="client-info">
                    <h2>{meta.get('client_name', 'Website')}</h2>
                    <p>{meta.get('website_url', '')}</p>
                </div>
                <div class="report-date">
                    <p>Generated on: {meta.get('audit_date', datetime.now().strftime('%d %B, %Y'))}</p>
                </div>
                <div class="overall-score {status_class}">
                    <div class="score-circle">
                        <span class="score-number">{overall}</span>
                        <span class="score-label">Overall Score</span>
                    </div>
                    <p class="status-text">{status_text}</p>
                </div>
            </div>
        </div>
        
        <!-- Executive Summary - Page 2 -->
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="scores-grid">
                {_generate_score_card('Performance', scores.get('performance', 0))}
                {_generate_score_card('SEO', scores.get('seo', 0))}
                {_generate_score_card('Accessibility', scores.get('accessibility', 0))}
                {_generate_score_card('Best Practices', scores.get('best_practices', 0))}
            </div>
        </div>
        
        <!-- Core Web Vitals - Same Page if space available -->
        <div class="section">
            <h2>Core Web Vitals</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Target</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {_generate_cwv_row('Largest Contentful Paint (LCP)', cwv.get('lcp', {}), 'seconds')}
                    {_generate_cwv_row('First Contentful Paint (FCP)', cwv.get('fcp', {}), 'seconds')}
                    {_generate_cwv_row('Cumulative Layout Shift (CLS)', cwv.get('cls', {}), 'score')}
                    {_generate_cwv_row('First Input Delay (FID)', cwv.get('fid', {}), 'ms')}
                    {_generate_cwv_row('Time to First Byte (TTFB)', cwv.get('ttfb', {}), 'seconds')}
                </tbody>
            </table>
        </div>
        
        <!-- SEO Analysis - New Page -->
        <div class="section page-break-before">
            <h2>SEO Analysis</h2>
            <div class="subsection">
                <h3>Meta Tags</h3>
                <table class="data-table">
                    <tr>
                        <th>Title</th>
                        <td>{seo.get('meta_tags', {}).get('title', {}).get('content', 'Not found')}</td>
                        <td class="{_get_status_class(len(seo.get('meta_tags', {}).get('title', {}).get('issues', [])) == 0)}">
                            {'✓ Good' if len(seo.get('meta_tags', {}).get('title', {}).get('issues', [])) == 0 else '⚠ Issues found'}
                        </td>
                    </tr>
                    <tr>
                        <th>Description</th>
                        <td>{seo.get('meta_tags', {}).get('description', {}).get('content', 'Not found')[:100]}...</td>
                        <td class="{_get_status_class(len(seo.get('meta_tags', {}).get('description', {}).get('issues', [])) == 0)}">
                            {'✓ Good' if len(seo.get('meta_tags', {}).get('description', {}).get('issues', [])) == 0 else '⚠ Issues found'}
                        </td>
                    </tr>
                </table>
            </div>
            <div class="subsection">
                <h3>Images</h3>
                <p>Total: {seo.get('images', {}).get('total', 0)} | 
                   With Alt: {seo.get('images', {}).get('with_alt', 0)} | 
                   Missing Alt: <span class="{'poor' if seo.get('images', {}).get('without_alt', 0) > 0 else 'good'}">{seo.get('images', {}).get('without_alt', 0)}</span>
                </p>
            </div>
        </div>
        
        <!-- Security Analysis - New Page -->
        {f'''
        <div class="section page-break-before">
            <h2>Security Analysis</h2>
            <div class="security-score">
                <span class="score-number">{security.get('security_score', 'N/A')}</span>
                <span class="score-label">Security Score</span>
            </div>
            <div class="subsection">
                <h3>SSL Certificate</h3>
                <p>Enabled: {'✓ Yes' if security.get('ssl_certificate', {}).get('enabled') else '✗ No'}</p>
                <p>Valid: {'✓ Yes' if security.get('ssl_certificate', {}).get('valid') else '✗ No'}</p>
            </div>
            <div class="subsection">
                <h3>Security Headers</h3>
                <p>Found: {len(security.get('security_headers', {}).get('headers_found', []))}</p>
                <p>Missing: {len(security.get('security_headers', {}).get('headers_missing', []))}</p>
            </div>
        </div>
        ''' if security else ''}
        
        <!-- Recommendations - New Page -->
        <div class="section page-break-before">
            <h2>Recommendations</h2>
            {_generate_recommendations_html(recommendations)}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated by Website Audit Tool | {datetime.now().strftime('%d %B, %Y at %H:%M')}</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def _get_report_css() -> str:
    """
    Get CSS styles for the report - Professional PDF layout with proper page breaks
    """
    return """
    @page {
        size: A4;
        margin: 20mm 15mm;
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.5;
        color: #333;
        font-size: 11pt;
    }
    
    .report-container {
        width: 100%;
        background: white;
    }
    
    /* Cover Page - Always on its own page */
    .cover-page {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 40px 30px;
        text-align: center;
        min-height: 250mm;
        display: flex;
        align-items: center;
        justify-content: center;
        page-break-after: always;
    }
    
    .report-title {
        font-size: 28pt;
        margin-bottom: 20px;
        font-weight: 300;
    }
    
    .client-info h2 {
        font-size: 22pt;
        margin-bottom: 8px;
    }
    
    .client-info p {
        opacity: 0.8;
        font-size: 12pt;
    }
    
    .report-date {
        margin-top: 20px;
        opacity: 0.7;
        font-size: 10pt;
    }
    
    .overall-score {
        margin-top: 30px;
    }
    
    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: rgba(255,255,255,0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    
    .score-number {
        font-size: 36pt;
        font-weight: bold;
    }
    
    .score-label {
        font-size: 10pt;
        opacity: 0.8;
    }
    
    .status-text {
        margin-top: 12px;
        font-size: 14pt;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .good { color: #10b981; }
    .average { color: #f59e0b; }
    .poor { color: #ef4444; }
    
    /* Sections - Each section stays together */
    .section {
        padding: 20px 0;
        margin-bottom: 15px;
        page-break-inside: avoid;
    }
    
    /* Force page break before certain major sections */
    .section.page-break-before {
        page-break-before: always;
    }
    
    .section h2 {
        font-size: 16pt;
        margin-bottom: 15px;
        color: #1a1a2e;
        border-bottom: 2px solid #10b981;
        padding-bottom: 8px;
    }
    
    .subsection {
        margin-bottom: 15px;
        page-break-inside: avoid;
    }
    
    .subsection h3 {
        font-size: 12pt;
        margin-bottom: 8px;
        color: #333;
    }
    
    .scores-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 10px;
    }
    
    .score-card {
        text-align: center;
        padding: 15px 10px;
        background: #f8f9fa;
        border-radius: 8px;
        page-break-inside: avoid;
    }
    
    .score-card .value {
        font-size: 24pt;
        font-weight: bold;
    }
    
    .score-card .label {
        font-size: 9pt;
        color: #666;
        margin-top: 4px;
    }
    
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 10pt;
    }
    
    .data-table th,
    .data-table td {
        padding: 8px 10px;
        text-align: left;
        border-bottom: 1px solid #eee;
    }
    
    .data-table th {
        background: #f8f9fa;
        font-weight: 600;
    }
    
    /* Prevent table rows from breaking */
    .data-table tr {
        page-break-inside: avoid;
    }
    
    .recommendation-category {
        margin-bottom: 15px;
        page-break-inside: avoid;
    }
    
    .recommendation-category h4 {
        font-size: 11pt;
        margin-bottom: 8px;
        padding: 6px 12px;
        border-radius: 4px;
        display: inline-block;
    }
    
    .recommendation-category.critical h4 {
        background: #fef2f2;
        color: #dc2626;
    }
    
    .recommendation-category.high_priority h4 {
        background: #fff7ed;
        color: #ea580c;
    }
    
    .recommendation-category.medium_priority h4 {
        background: #fefce8;
        color: #ca8a04;
    }
    
    .recommendation-category.quick_wins h4 {
        background: #f0fdf4;
        color: #16a34a;
    }
    
    .recommendation-item {
        padding: 10px 12px;
        background: #f8f9fa;
        border-radius: 6px;
        margin-bottom: 8px;
        border-left: 3px solid #ddd;
        page-break-inside: avoid;
    }
    
    .recommendation-item h5 {
        font-size: 10pt;
        margin-bottom: 5px;
    }
    
    .recommendation-item p {
        font-size: 9pt;
        color: #666;
        margin-bottom: 4px;
    }
    
    .recommendation-item .meta {
        font-size: 8pt;
        color: #888;
    }
    
    .footer {
        text-align: center;
        padding: 15px;
        background: #f8f9fa;
        color: #666;
        font-size: 9pt;
        margin-top: 20px;
    }
    
    /* Print specific rules */
    @media print {
        body {
            font-size: 10pt;
        }
        
        .section {
            page-break-inside: avoid;
        }
        
        .subsection {
            page-break-inside: avoid;
        }
        
        .recommendation-item {
            page-break-inside: avoid;
        }
        
        .data-table tr {
            page-break-inside: avoid;
        }
        
        .score-card {
            page-break-inside: avoid;
        }
    }
    """


def _generate_score_card(label: str, value: int) -> str:
    """
    Generate a score card HTML
    """
    if value >= 80:
        status_class = 'good'
    elif value >= 50:
        status_class = 'average'
    else:
        status_class = 'poor'
    
    return f"""
    <div class="score-card">
        <div class="value {status_class}">{value}</div>
        <div class="label">{label}</div>
    </div>
    """


def _generate_cwv_row(label: str, data: Dict, unit: str) -> str:
    """
    Generate a Core Web Vitals table row
    """
    value = data.get('value', 'N/A')
    target = data.get('target', 'N/A')
    status = data.get('status', 'unknown')
    
    status_icon = '✓' if status == 'good' else ('⚠' if status == 'average' else '✗')
    
    return f"""
    <tr>
        <td>{label}</td>
        <td>{value} {unit}</td>
        <td>{target} {unit}</td>
        <td class="{status}">{status_icon} {status.title()}</td>
    </tr>
    """


def _get_status_class(is_good: bool) -> str:
    """
    Get CSS class based on status
    """
    return 'good' if is_good else 'poor'


def _generate_recommendations_html(recommendations: Dict) -> str:
    """
    Generate recommendations HTML
    """
    if not recommendations:
        return '<p>No recommendations available.</p>'
    
    html = ''
    
    for category, items in recommendations.items():
        if not items:
            continue
        
        category_title = category.replace('_', ' ').title()
        html += f'''
        <div class="recommendation-category {category}">
            <h4>{category_title}</h4>
        '''
        
        for item in items:
            html += f'''
            <div class="recommendation-item">
                <h5>{item.get('issue', 'Unknown Issue')}</h5>
                <p>{item.get('description', '')}</p>
                <p class="meta">Impact: {item.get('impact', 'N/A')} | Effort: {item.get('effort', 'N/A')}</p>
                <p class="meta">Expected: {item.get('expected_improvement', 'N/A')}</p>
            </div>
            '''
        
        html += '</div>'
    
    return html


if __name__ == '__main__':
    # Test with sample data
    import json
    
    try:
        with open('audit-data.json', 'r') as f:
            sample_data = json.load(f)
        
        result = generate_html_report(sample_data, 'test-report.html')
        print(f"Report generated: {result}")
    except FileNotFoundError:
        print("No audit-data.json found. Run an audit first.")
