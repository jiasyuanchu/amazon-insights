# Amazon Insights

Amazon Product Tracking System - Track price, BSR, ratings, and review count changes of Amazon products using Firecrawl API.

## Features

### Core Product Tracking
- 🔍 **Real Data Extraction**: Get authentic Amazon product data using Firecrawl API
- 📊 **Multi-dimensional Monitoring**: Track price, BSR, ratings, review count, Buy Box price
- 🚨 **Anomaly Detection**: Automatically detect significant changes and send alerts
- 📈 **Historical Trends**: Store and analyze historical product data changes
- ⏰ **Scheduled Monitoring**: Support daily automatic monitoring and real-time tracking

### Competitive Analysis Engine
- 🏆 **Multi-dimensional Comparison**: Price, quality, popularity, and overall competitiveness analysis
- 🤖 **AI-Powered Insights**: OpenAI GPT-generated SWOT analysis and strategic recommendations
- 📋 **Interactive Dashboard**: Professional web interface for competitive visualization
- 📊 **Advanced Analytics**: BSR ranking analysis, feature comparison, market positioning
- 🎯 **Strategic Planning**: Actionable business recommendations with priority scoring

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
OPENAI_API_KEY=your_openai_api_key_here  # Optional: for AI-powered competitive analysis
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=True
```

**Note**: OpenAI API key is optional. If not provided, the competitive analysis will use structured analysis as fallback.

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

### Competitive Analysis Dashboard

#### Start Dashboard Interface
```bash
# Start API server (required)
python3 start_api.py

# Start frontend dashboard server (in another terminal)
python3 frontend_server.py
```

Dashboard will be available at: `http://localhost:8080`

#### Dashboard Features
- **Real-time Competitive Analysis**: Interactive visualization of competitive positioning
- **Multi-dimensional Comparison**: Price, quality, popularity, and overall competitiveness
- **AI-Powered Insights**: SWOT analysis and strategic recommendations
- **Interactive Charts**: Price comparison and rating bubble charts
- **Professional Interface**: Responsive design with modern UI/UX

#### Quick Dashboard Test
1. **Setup Competitive Group**:
```bash
curl -X POST "http://localhost:8001/api/v1/competitive/quick-setup" \
  -H "Content-Type: application/json" \
  -d '{
    "main_product_asin": "B07R7RMQF5",
    "competitor_asins": ["B092XMWXK7", "B0BVY8K28Q", "B0CSMV2DTV"],
    "group_name": "Demo Competitive Analysis",
    "description": "Demo competitive analysis for testing"
  }'
```

2. **Access Dashboard**: Open http://localhost:8080
3. **Select Group**: Choose "Demo Competitive Analysis" from dropdown
4. **Run Analysis**: Click "Refresh Analysis" button
5. **View Results**: Explore competitive insights, charts, and AI recommendations

#### Dashboard Components
- **Overview Cards**: Key competitive metrics (0-100 scoring)
- **Price Chart**: Bar chart comparing product prices
- **Rating Chart**: Bubble chart showing rating vs review count
- **BSR Analysis**: Amazon ranking performance by category
- **AI Reports**: Executive summary, SWOT, and strategic recommendations

For detailed dashboard usage, see: [DASHBOARD_README.md](DASHBOARD_README.md)

#### API Documentation
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Postman Collection**: [postman_collection.json](postman_collection.json)
- **Postman Testing Guide**: [POSTMAN_TESTING_GUIDE.md](POSTMAN_TESTING_GUIDE.md)

#### Main API Endpoints

##### Product Tracking
- `POST /api/v1/products/track/{asin}` - Track single product
- `POST /api/v1/products/track-all` - Track all products
- `GET /api/v1/products/summary/{asin}` - Get product summary
- `GET /api/v1/products/history/{asin}` - Get product history
- `GET /api/v1/products/list` - Get monitored products list

##### Competitive Analysis
- `POST /api/v1/competitive/quick-setup` - Quick competitive group setup
- `GET /api/v1/competitive/groups` - Get all competitive groups
- `GET /api/v1/competitive/groups/{id}` - Get specific competitive group
- `POST /api/v1/competitive/groups` - Create competitive group
- `DELETE /api/v1/competitive/groups/{id}` - Delete competitive group
- `POST /api/v1/competitive/groups/{id}/competitors` - Add competitor
- `DELETE /api/v1/competitive/groups/{id}/competitors/{asin}` - Remove competitor
- `POST /api/v1/competitive/groups/{id}/analyze` - Run competitive analysis
- `GET /api/v1/competitive/groups/{id}/report` - Get AI positioning report
- `GET /api/v1/competitive/groups/{id}/trends` - Get trend analysis
- `POST /api/v1/competitive/batch-analysis` - Batch analyze all groups
- `GET /api/v1/competitive/summary` - System competitive overview

##### Alerts & System
- `GET /api/v1/alerts/` - Get alerts summary
- `GET /api/v1/alerts/recent` - Get recent alerts
- `GET /api/v1/alerts/{asin}` - Get product-specific alerts
- `GET /api/v1/system/status` - System status
- `GET /api/v1/system/health` - Health check
- `POST /api/v1/system/test` - System components test

##### Cache Management
- `GET /api/v1/cache/info` - Cache system information
- `GET /api/v1/cache/stats` - Cache statistics
- `POST /api/v1/cache/clear/all` - Clear all cache
- `POST /api/v1/cache/clear/product/{asin}` - Clear product cache

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
│   ├── monitoring/       # Monitoring and anomaly detection
│   └── competitive/      # Competitive analysis engine
│       ├── analyzer.py   # Multi-dimensional competitive analysis
│       ├── manager.py    # Competitive group management
│       └── llm_reporter.py # AI-powered report generation
├── api/
│   ├── routes/           # FastAPI routes
│   └── models/           # API data schemas
├── frontend/             # Competitive analysis dashboard
│   ├── index.html        # Dashboard interface
│   ├── script.js         # Interactive functionality
│   ├── styles.css        # Professional styling
│   └── chart-fallback.js # Chart fallback system
├── config/               # Configuration files
├── data/                 # Database files
├── logs/                 # Log files
├── main.py               # CLI main program
├── app.py                # API main program
├── frontend_server.py    # Dashboard server
├── cache_manager.py      # Cache management tool
├── test_cache.py         # Cache testing
├── test_tracker.py       # System testing
└── test_competitive.py   # Competitive analysis testing
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

### Core System
- **Backend**: Python 3.7+
- **Database**: SQLAlchemy + SQLite
- **Cache System**: Redis (24-48 hour cache)
- **API**: Firecrawl API + FastAPI
- **Parsing**: BeautifulSoup + Regular Expressions
- **Monitoring**: Scheduled tasks + Anomaly detection algorithms

### Competitive Analysis
- **Analysis Engine**: Multi-dimensional competitive algorithms
- **AI Integration**: OpenAI GPT-4 for intelligent insights
- **Frontend**: Modern HTML5/CSS3/JavaScript dashboard
- **Visualization**: Chart.js with fallback systems
- **Scoring System**: 0-100 competitive metrics
- **Task Processing**: Celery for parallel data extraction

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