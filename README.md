# 🚀 Enhanced Job Scraper - Completely FREE Edition

A powerful, **100% FREE** job scraping system with multiple trigger types and zero API key requirements. Features enhanced error handling, rate limiting, and comprehensive n8n workflow integration.

## ✨ Key Features

- 🆓 **Completely FREE** - No API keys required
- 🔗 **Multiple Triggers**: Webhook, Manual, Scheduled, and Telegram
- 🛡️ **Enhanced Security** - Non-root Docker containers
- 🔄 **Rate Limiting** - Respectful scraping practices  
- 📊 **Comprehensive Logging** - Full error tracking and monitoring
- 🎯 **Smart Job Scoring** - Relevance-based job ranking
- 🚫 **Duplicate Removal** - Intelligent deduplication
- 📱 **Telegram Integration** - Interactive bot interface
- ⚡ **High Performance** - Optimized Chrome configuration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  n8n Workflows │────│   Flask API     │────│  Job Scrapers   │
│                 │    │                 │    │                 │
│ • Telegram Bot  │    │ • /jobs         │    │ • Pracuj.pl     │
│ • Webhooks      │    │ • /health       │    │ • LinkedIn*     │
│ • Scheduled     │    │ • /config       │    │ • Indeed*       │
│ • Manual        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Database      │
                    │   & Caching     │
                    └─────────────────┘
```

*\*Coming soon*

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/joelfuller2016/enhanced-job-scraper-n8n.git
cd enhanced-job-scraper-n8n

# Set environment variables
echo "EMAIL=your_email@example.com" > .env
echo "PASSWORD=your_password" >> .env

# Build and run
docker build -t enhanced-job-scraper .
docker run -p 5000:5000 --env-file .env enhanced-job-scraper
```

### Option 2: Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export EMAIL=your_email@example.com
export PASSWORD=your_password

# Run the application
cd src
python app.py
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for pracuj.pl login (optional)
EMAIL=your_pracuj_email@example.com
PASSWORD=your_pracuj_password

# Optional API configuration
JOB_API_URL=http://localhost:5000
DEFAULT_CHAT_ID=your_telegram_chat_id
```

### YAML Configuration

Edit `config/config.yaml` to customize:

```yaml
# API Settings
api:
  host: "0.0.0.0"
  port: 5000
  cors_origins: ["*"]

# Chrome Settings  
chrome:
  headless: true
  timeout: 30
  
# Job Sources
sources:
  pracuj:
    enabled: true
    rate_limit: 2
    max_pages: 10
```

## 📡 API Endpoints

### GET /jobs
Search for jobs with optional parameters:

```bash
curl "http://localhost:5000/jobs?keywords=python%20engineer&max_results=20"
```

**Parameters:**
- `keywords` - Search keywords (default: "python engineer")
- `max_results` - Maximum results (default: 100)
- `sources` - Comma-separated list of sources (default: all enabled)

**Response:**
```json
{
  "success": true,
  "jobs": [...],
  "total_count": 15,
  "processing_time": 12.34,
  "timestamp": "2025-05-30T01:00:00Z"
}
```

### GET /health
Health check endpoint:

```json
{
  "status": "healthy",
  "timestamp": "2025-05-30T01:00:00Z",
  "components": {
    "database": "ok",
    "chrome": "ok"
  }
}
```

## 🔗 n8n Workflow Setup

### Import the Workflow

1. Copy the content from `n8n_workflows/free_multi_trigger_workflow.json`
2. In n8n, go to **Workflows** → **Import from File/URL**
3. Paste the JSON content and import

### Configure Triggers

#### 1. Telegram Bot (Optional)
- Create a bot via [@BotFather](https://t.me/BotFather)
- Add your bot token to n8n Telegram credentials
- Update the workflow with your credentials ID

#### 2. Webhook Trigger
```bash
# Test the webhook
curl -X POST http://your-n8n-instance/webhook/job-search \
  -H "Content-Type: application/json" \
  -d '{"message": "python jobs", "keywords": "python engineer"}'
```

#### 3. Scheduled Trigger
- Automatically runs at 9 AM and 5 PM on weekdays
- Modify the cron expression: `0 9,17 * * 1-5`

#### 4. Manual Trigger
- Click the "Test workflow" button in n8n
- Perfect for testing and one-off searches

### Workflow Variables

Set these in n8n **Settings** → **Variables**:

```
JOB_API_URL = http://your-api-host:5000
DEFAULT_CHAT_ID = your_telegram_chat_id
```

## 🤖 Usage Examples

### Via Telegram Bot
```
User: "python jobs"
Bot: 🔍 Searching for job opportunities...

📌 Senior Python Developer
🏢 Company: TechCorp Ltd.
📍 Location: Warsaw, Poland
💡 Tech: Python, Django, PostgreSQL
🔗 Link: https://example.com/job/123
⭐ Match: 95%
```

### Via Webhook
```bash
curl -X POST http://n8n-instance/webhook/job-search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "javascript developer", 
    "chat_id": "123456789"
  }'
```

### Via API Direct
```bash
curl "http://localhost:5000/jobs?keywords=python%20engineer&max_results=5"
```

## 🔍 Supported Job Sources

### Currently Available
- **Pracuj.pl** ✅ - Poland's largest job portal
  - Rate limited (2 seconds between requests)
  - Supports login for personalized results
  - Advanced job parsing with technology extraction

### Coming Soon
- **LinkedIn** 🚧 - Professional networking platform
- **Indeed** 🚧 - Global job search engine  
- **Glassdoor** 🚧 - Company reviews and salaries
- **Stack Overflow Jobs** 🚧 - Developer-focused positions

## 🐛 Troubleshooting

### Common Issues

#### 1. Chrome/ChromeDriver Issues
```bash
# Install Chrome dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver

# Set environment variable
export CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

#### 2. Permission Errors (Docker)
```bash
# Ensure proper permissions
sudo chown -R $USER:$USER /app/logs /app/data
```

#### 3. Rate Limiting
```bash
# Check logs for rate limiting messages
tail -f logs/job_scraper.log
```

#### 4. API Not Responding
```bash
# Test health endpoint
curl http://localhost:5000/health

# Check Docker logs
docker logs container-name
```

### Debug Mode

Enable debug logging:

```bash
# Set debug mode in config.yaml
api:
  debug: true
  
logging:
  level: "DEBUG"
```

## 📊 Monitoring & Logs

### Log Files
- **Application**: `logs/job_scraper.log`
- **Access**: Docker container logs
- **Health**: Available via `/health` endpoint

### Metrics Available
- Processing time per request
- Jobs found per source
- Success/failure rates
- Rate limiting status

### Health Checks
```bash
# Docker health check
docker ps  # Check HEALTHY status

# Manual health check  
curl http://localhost:5000/health
```

## 🚀 Deployment

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  job-scraper:
    build: .
    ports:
      - "5000:5000"
    environment:
      - EMAIL=your_email@example.com
      - PASSWORD=your_password
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Cloud Deployment

#### AWS ECS / Google Cloud Run
```bash
# Build for cloud
docker build -t job-scraper:latest .
docker tag job-scraper:latest your-registry/job-scraper:latest
docker push your-registry/job-scraper:latest
```

#### Heroku
```bash
# Install Heroku CLI and deploy
heroku create your-app-name
heroku container:push web
heroku container:release web
```

## 🔒 Security

### Best Practices Implemented
- ✅ Non-root Docker user
- ✅ Input validation and sanitization
- ✅ Rate limiting and request throttling
- ✅ Error handling without information leakage
- ✅ CORS configuration
- ✅ Health checks and monitoring

### Security Notes
- Never commit real credentials to version control
- Use environment variables or secrets management
- Regularly update dependencies for security patches
- Monitor logs for suspicious activity

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone https://github.com/joelfuller2016/enhanced-job-scraper-n8n.git
cd enhanced-job-scraper-n8n

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black src/
```

### Adding New Job Sources

1. Create a new scraper class in `src/scrapers/`
2. Implement the `BaseJobScraper` interface
3. Add configuration to `config/config.yaml`
4. Update the main scraper to include your source
5. Write tests and documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Selenium](https://selenium.dev/) - Web automation framework
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [n8n](https://n8n.io/) - Workflow automation
- [Loguru](https://loguru.readthedocs.io/) - Python logging

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/joelfuller2016/enhanced-job-scraper-n8n/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/joelfuller2016/enhanced-job-scraper-n8n/discussions)
- 📧 **Email**: Available in GitHub profile

---

**🎉 Happy job hunting! 🎉**
