# Automotive Scraper System Documentation

## Overview

The Automotive Scraper System is a comprehensive web scraping solution designed to collect automotive data from GruppoAutoUno.it. The system includes robust scraping capabilities, data validation, compliance monitoring, automated scheduling, and a complete REST API for data access.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto Scouter System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)     │  Backend (FastAPI + SQLite) │
│  - Vehicle Search UI         │  - Original Scouting API    │
│  - Dashboard                 │  - Team Management          │
│  - Analytics                 │  - Match Tracking           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              Automotive Scraper System                     │
├─────────────────────────────────────────────────────────────┤
│  Web Scraper Engine          │  Data Management            │
│  - GruppoAutoUno Scraper     │  - Vehicle Database         │
│  - Rate Limiting             │  - Price History            │
│  - Compliance Monitoring     │  - Image Storage            │
│  - Error Handling            │  - Deduplication            │
├─────────────────────────────────────────────────────────────┤
│  Scheduling System           │  Monitoring & Health        │
│  - APScheduler               │  - System Metrics           │
│  - Automated Runs            │  - Data Quality Checks      │
│  - Maintenance Tasks         │  - Compliance Scoring       │
├─────────────────────────────────────────────────────────────┤
│  REST API                    │  Testing & Validation       │
│  - Vehicle Search            │  - Unit Tests               │
│  - Analytics                 │  - Integration Tests        │
│  - Scraper Management        │  - API Tests                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Web Scraper Engine (`app/scraper/`)

**Base Scraper (`base.py`)**
- Rate limiting and politeness delays
- User agent rotation
- Error handling and retries
- HTML parsing utilities
- Data cleaning and normalization

**Automotive Scraper (`automotive_scraper.py`)**
- GruppoAutoUno.it specific implementation
- Vehicle data extraction
- Image collection
- Pagination handling
- Data validation

**Configuration (`config.py`)**
- Scraper settings and parameters
- CSS selectors for data extraction
- Rate limiting configuration
- Compliance settings

### 2. Data Management (`app/models/`, `app/services/`)

**Database Models (`automotive.py`)**
- `VehicleListing`: Main vehicle data
- `VehicleImage`: Vehicle photos
- `PriceHistory`: Price change tracking
- `ScrapingLog`: Scraping activity logs
- `ScrapingSession`: Session summaries
- `DataQualityMetric`: Quality tracking

**Service Layer (`automotive_service.py`)**
- CRUD operations
- Duplicate detection
- Data validation
- Quality metrics calculation
- Historical data management

### 3. Scheduling System (`app/scraper/scheduler.py`)

**Features:**
- Automated scraping every 8 hours
- Maintenance tasks (cleanup, quality checks)
- Manual trigger capability
- Job monitoring and logging
- Failure handling and recovery

**Jobs:**
- Main scraping job
- Daily data cleanup
- Weekly quality checks
- Old listing deactivation

### 4. Compliance & Monitoring

**Compliance Manager (`compliance.py`)**
- Robots.txt compliance checking
- Rate limiting enforcement
- Ethical scraping guidelines
- URL blocking and allowlisting
- Compliance scoring

**Monitoring System (`monitoring.py`)**
- System health checks
- Performance metrics
- Data quality alerts
- Error tracking
- Resource usage monitoring

### 5. REST API (`app/routers/automotive.py`)

**Vehicle Endpoints:**
- `GET /vehicles` - Search and filter vehicles
- `GET /vehicles/{id}` - Get vehicle details
- `GET /makes` - Available makes
- `GET /models` - Available models
- `GET /analytics` - Data analytics

**Scraper Management:**
- `GET /scraper/status` - Scraper status
- `POST /scraper/trigger` - Manual scraping
- `GET /scraper/health` - Health checks
- `GET /scraper/sessions` - Scraping sessions
- `GET /scraper/logs` - Activity logs

**Maintenance:**
- `POST /maintenance/cleanup` - Data cleanup
- `GET /maintenance/quality` - Quality reports

## Data Flow

### 1. Scraping Process

```
1. Scheduler triggers scraping job
2. Scraper fetches main listing page
3. Extract vehicle links from listings
4. For each vehicle:
   a. Fetch detail page
   b. Extract vehicle data
   c. Download images (optional)
   d. Validate and clean data
   e. Check for duplicates
   f. Store or update in database
   g. Log activity
5. Update session statistics
6. Generate quality metrics
```

### 2. Data Storage

```
Vehicle Data → Validation → Deduplication → Database Storage
     ↓              ↓            ↓              ↓
Price History   Image URLs   Update Existing   Log Activity
```

### 3. API Access

```
Client Request → Authentication → Validation → Database Query → Response
     ↓              ↓              ↓              ↓              ↓
Rate Limiting   Permission     Parameter      Filtering      JSON/XML
                Check          Validation     & Sorting      Response
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./auto_scouter.db

# Scraper Settings
SCRAPER_BASE_URL=https://gruppoautouno.it
SCRAPER_REQUEST_DELAY=2.0
SCRAPER_MAX_RETRIES=3
SCRAPER_REQUESTS_PER_MINUTE=30
SCRAPER_REQUESTS_PER_HOUR=1000

# Scheduling
SCRAPER_SCRAPING_ENABLED=true
SCRAPER_SCRAPING_INTERVAL_HOURS=8
SCRAPER_DATA_RETENTION_DAYS=365

# Compliance
SCRAPER_RESPECT_ROBOTS_TXT=true
SCRAPER_ENABLE_POLITENESS_DELAY=true

# Monitoring
SCRAPER_ENABLE_METRICS=true
SCRAPER_LOG_LEVEL=INFO
```

### Key Settings

- **Request Delay**: 2 seconds between requests
- **Rate Limits**: 30 requests/minute, 1000 requests/hour
- **Scraping Interval**: Every 8 hours
- **Data Retention**: 365 days
- **Robots.txt**: Fully compliant
- **User Agents**: Rotated for diversity

## Deployment

### Quick Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Run setup script
python setup_scraper.py

# 3. Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python -c "from app.models.base import engine, Base; from app.models.automotive import *; Base.metadata.create_all(bind=engine)"

# 3. Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Start scheduler (optional)
python -c "from app.scraper.scheduler import scraper_scheduler; scraper_scheduler.start(); input('Press Enter to stop...')"
```

### Testing

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python -m pytest tests/test_automotive_service.py -v
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_integration.py -v
```

## Monitoring & Maintenance

### Health Checks

- **System Health**: CPU, memory, disk usage
- **Network Connectivity**: Target website availability
- **Database Health**: Connection and query performance
- **Scraper Status**: Active jobs and recent activity

### Data Quality Metrics

- **Completeness**: Percentage of fields populated
- **Accuracy**: Data validation scores
- **Freshness**: Time since last update
- **Consistency**: Format and value consistency

### Compliance Monitoring

- **Robots.txt Compliance**: Automatic checking
- **Rate Limiting**: Request frequency monitoring
- **Error Rates**: Failed request tracking
- **Compliance Score**: Overall ethical rating

### Maintenance Tasks

- **Daily**: Data cleanup, old listing deactivation
- **Weekly**: Data quality assessment
- **Monthly**: Performance optimization
- **Quarterly**: Compliance review

## Best Practices

### Ethical Scraping

1. **Respect robots.txt** - Always check and follow directives
2. **Use reasonable delays** - Minimum 2 seconds between requests
3. **Monitor server load** - Reduce frequency if errors increase
4. **Identify your bot** - Use descriptive User-Agent strings
5. **Handle errors gracefully** - Implement exponential backoff

### Data Quality

1. **Validate all inputs** - Check data types and ranges
2. **Implement deduplication** - Prevent duplicate entries
3. **Track changes** - Maintain price and data history
4. **Monitor completeness** - Track missing fields
5. **Regular cleanup** - Remove stale data

### Performance

1. **Use connection pooling** - Reuse HTTP connections
2. **Implement caching** - Cache static data
3. **Optimize queries** - Use proper database indexes
4. **Monitor resources** - Track CPU and memory usage
5. **Scale horizontally** - Add workers as needed

### Security

1. **Validate inputs** - Prevent injection attacks
2. **Use HTTPS** - Encrypt data in transit
3. **Implement rate limiting** - Prevent abuse
4. **Log activities** - Maintain audit trails
5. **Regular updates** - Keep dependencies current

## Troubleshooting

### Common Issues

**Scraper Not Running**
- Check scheduler status: `GET /api/v1/automotive/scraper/status`
- Verify configuration: `python -c "from app.scraper.config import scraper_settings; print(scraper_settings)"`
- Check logs: `GET /api/v1/automotive/scraper/logs`

**No Data Being Scraped**
- Test network connectivity: `GET /api/v1/automotive/scraper/health`
- Check robots.txt compliance: `GET /api/v1/automotive/scraper/compliance`
- Verify CSS selectors are still valid

**High Error Rates**
- Reduce request frequency
- Check target website for changes
- Verify User-Agent strings
- Review error logs for patterns

**Database Issues**
- Check disk space
- Verify database permissions
- Run data quality checks
- Consider database optimization

### Support

For issues and questions:
1. Check the logs: `/api/v1/automotive/scraper/logs`
2. Review health status: `/api/v1/automotive/scraper/health`
3. Run diagnostics: `python setup_scraper.py`
4. Consult documentation: `docs/`

## Future Enhancements

- **Multi-site Support**: Extend to other automotive websites
- **Machine Learning**: Automated data quality improvement
- **Real-time Updates**: WebSocket-based live data
- **Advanced Analytics**: Predictive pricing models
- **Mobile App**: Native mobile interface
- **API Authentication**: Secure access control
- **Docker Deployment**: Containerized deployment
- **Cloud Integration**: AWS/GCP deployment options
