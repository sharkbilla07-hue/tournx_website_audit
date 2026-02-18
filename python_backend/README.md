# Website Audit Tool - Python Backend

## 🚀 Enhanced Features

This Python backend provides a comprehensive website audit with:

- ✅ **PageSpeed API Integration** - Real performance data (FREE 25K requests/day)
- ✅ **SEO Analysis** - Meta tags, headings, images, structured data
- ✅ **Technical SEO** - HTTPS, mobile-friendly, links, indexability
- ✅ **Security Analysis** - SSL certificate, security headers, vulnerabilities
- ✅ **Multi-page Crawling** - Audit multiple pages (configurable)
- ✅ **AI Recommendations** - Smart suggestions (FREE Gemini API)
- ✅ **PDF Report Generation** - Professional reports for clients

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Python Server

```bash
cd python_backend
python app.py
```

Server will start on: `http://localhost:5000`

### 3. Open the Frontend

Open `index.html` in your browser and enter a URL to audit.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit` | POST | Run website audit |
| `/api/audit/sync` | POST | Run audit and get data directly |
| `/api/data` | GET | Get latest audit data |
| `/api/sample` | GET | Get sample audit data |
| `/health` | GET | Health check |

## Example Usage

### Run Audit via API

```bash
curl -X POST http://localhost:5000/api/audit/sync \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.chocolaty.in"}'
```

### Run Audit via Python Script

```bash
cd python_backend
python audit_runner.py https://www.example.com
```

### Run with Multi-page Crawling

```bash
python audit_runner.py https://www.example.com --crawl --max-pages 20
```

## Architecture

```
python_backend/
├── app.py                 # Flask API server
├── config.py              # Configuration settings
├── audit_runner.py        # Main audit orchestrator
│
├── analyzers/
│   ├── pagespeed.py       # PageSpeed API integration
│   ├── seo_analyzer.py    # SEO analysis
│   ├── technical_seo.py   # Technical SEO checks
│   ├── content_analyzer.py # Content analysis
│   ├── security_analyzer.py # Security analysis (NEW)
│   └── ai_recommendations.py # AI recommendations (NEW)
│
├── scrapers/
│   ├── web_scraper.py     # BeautifulSoup scraper
│   └── site_crawler.py    # Multi-page crawler (NEW)
│
└── utils/
    ├── helpers.py         # Utility functions
    └── pdf_generator.py   # PDF report generator (NEW)
```

## Data Sources

| Source | Cost | Data Provided |
|--------|------|---------------|
| PageSpeed Insights API | FREE (25K/day) | Performance, Core Web Vitals, Accessibility, SEO |
| BeautifulSoup Scraper | FREE (Unlimited) | Meta tags, headings, images, links |
| SSL/TLS Check | FREE | Certificate validity, protocol |
| Security Headers | FREE | HSTS, CSP, X-Frame-Options, etc. |
| Google Gemini API | FREE (60 req/min) | AI-powered recommendations |

## Configuration

Edit `config.py` to customize:

```python
# PageSpeed API
PAGESPEED_API_KEY = 'your-api-key-here'

# Gemini AI (for recommendations)
GEMINI_API_KEY = 'your-gemini-api-key'

# Contact info
CONTACT = {
    'agency_name': "Your Agency",
    'email': "hello@youragency.com",
    ...
}
```

## New Features

### Security Analysis

Checks for:
- SSL certificate validity
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Common vulnerabilities
- Mixed content issues

### Multi-page Crawling

Crawls multiple pages to find site-wide issues:
- Missing titles
- Missing H1 tags
- Images without alt text
- Missing canonical URLs

### AI Recommendations

Uses Google Gemini API (FREE) to generate:
- Critical issues
- High priority fixes
- Medium priority improvements
- Quick wins

### PDF Report Generation

Generates professional PDF reports:
- Executive summary
- Core Web Vitals
- SEO analysis
- Security analysis
- Recommendations

## Troubleshooting

### Backend not running error

If you see "Python Backend is not running", make sure:

1. Python server is running: `python app.py`
2. Server is on port 5000
3. No firewall blocking the connection

### PageSpeed API errors

If PageSpeed API fails, the system will:
1. Use fallback scores
2. Continue with other analysis
3. Still generate a complete report

### PDF Generation Issues

If PDF generation fails:
1. Install WeasyPrint: `pip install weasyprint`
2. Or use HTML report (automatic fallback)

## Requirements

- Python 3.8+
- Flask
- requests
- beautifulsoup4
- lxml
- (Optional) weasyprint for PDF
- (Optional) google-generativeai for AI recommendations
