# Amazon Insights

Amazon Product Tracking System - Track price, BSR, ratings, and review count changes of Amazon products using Firecrawl API.

## Features

- 🔍 **Real Data Extraction**: Get authentic Amazon product data using Firecrawl API
- 📊 **Multi-dimensional Monitoring**: Track price, BSR, ratings, review count, Buy Box price
- 🚨 **Anomaly Detection**: Automatically detect significant changes and send alerts
- 📈 **Historical Trends**: Store and analyze historical product data changes
- ⏰ **Scheduled Monitoring**: Support daily automatic monitoring and real-time tracking

## Installation and Setup

1. **Install Redis**:
```bash
# macOS (using Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Check Redis status
redis-cli ping
```

2. **Install Python Dependencies**:
```bash
pip3 install -r requirements.txt
```

3. **Environment Variables Setup**:
Copy `.env.example` to `.env` and configure settings:
```bash
cp .env.example .env
# Edit .env and add your settings
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=True
```

4. **Test System**:
```bash
python3 test_tracker.py
python3 cache_manager.py test
```

## Usage

### CLI Mode

#### Track Single Product
```bash
python3 main.py track-single --asin B07R7RMQF5
```

#### Track All Configured Products
```bash
python3 main.py track-all
```

#### Start Continuous Monitoring
```bash
python3 main.py monitor
```

#### View Recent Alerts
```bash
python3 main.py alerts
```

#### View Product History
```bash
python3 main.py history --asin B07R7RMQF5
```

### RESTful API Mode

#### Start API Server
```bash
python3 start_api.py
```

API server will start at `http://localhost:8001`

#### API Documentation
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Postman Collection**: [postman_collection.json](postman_collection.json)
- **Postman Testing Guide**: [POSTMAN_TESTING_GUIDE.md](POSTMAN_TESTING_GUIDE.md)

#### Main API Endpoints
- `POST /api/v1/products/track/{asin}` - Track single product
- `POST /api/v1/products/track-all` - Track all products
- `GET /api/v1/products/summary/{asin}` - Get product summary
- `GET /api/v1/products/history/{asin}` - Get product history
- `GET /api/v1/alerts/` - Get alerts summary
- `GET /api/v1/system/status` - System status

## Monitored ASINs

The system monitors the following products by default (14 total):
- B07R7RMQF5, B092XMWXK7, B0BVY8K28Q, B0CSMV2DTV, B0D3XDR3NN
- B0CM22ZRTT, B08SLQ9LFD, B08VWJB2GZ, B0DHKCM18G, B07RKV9Z9D
- B08136DWMT, B01CI6SO1A, B092HVLSP5, B0016BWUGE

## Project Structure

```
amazon-insights/
├── src/
│   ├── api/              # Firecrawl API integration
│   ├── cache/            # Redis cache system
│   ├── parsers/          # Amazon data parsers
│   ├── models/           # Database models
│   └── monitoring/       # Monitoring and anomaly detection
├── api/
│   └── routes/           # FastAPI routes
├── config/               # Configuration files
├── data/                 # Database files
├── logs/                 # Log files
├── main.py               # CLI main program
├── app.py                # API main program
├── cache_manager.py      # Cache management tool
├── test_cache.py         # Cache testing
└── test_tracker.py       # System testing
```

## Data Tracking Items

- **Product Title**: Product name
- **Price Changes**: Current price and historical trends
- **BSR Trends**: Ranking changes across categories
- **Rating & Review Changes**: Star ratings and review count
- **Buy Box Price**: Main selling price
- **Stock Status**: Availability status

## Anomaly Detection

The system automatically detects the following anomalies:
- Significant price changes (default >10%)
- Notable BSR ranking changes (default >20%)
- Sudden rating changes (>0.5 stars)
- Review count spikes (>100 new reviews)
- Stock status changes

## Technical Architecture

- **Backend**: Python 3.7+
- **Database**: SQLAlchemy + SQLite
- **Cache System**: Redis (24-48 hour cache)
- **API**: Firecrawl API + FastAPI
- **Parsing**: BeautifulSoup + Regular Expressions
- **Monitoring**: Scheduled tasks + Anomaly detection algorithms

## Redis Cache System

The system uses Redis for high-performance caching, significantly improving query speed:

### Caching Strategy
- **Product Summary**: 24-hour TTL
- **Product History**: 48-hour TTL  
- **Alert Information**: 1-hour TTL
- **System Status**: 5-minute TTL

### Cache Management
```bash
# View cache information
python3 cache_manager.py info

# Clear all cache
python3 cache_manager.py clear-all

# Clear specific product cache
python3 cache_manager.py clear-product --asin B07R7RMQF5

# Warm up cache
python3 cache_manager.py warm-up

# Test cache functionality
python3 cache_manager.py test
```