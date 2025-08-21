# Amazon Insights

[![CI Pipeline](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/ci.yml/badge.svg)](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/cd.yml/badge.svg)](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/cd.yml)
[![Security Audit](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/dependency-update.yml/badge.svg)](https://github.com/jiasyuanchu/amazon-insights/actions/workflows/dependency-update.yml)
[![codecov](https://codecov.io/gh/jiasyuanchu/amazon-insights/branch/main/graph/badge.svg)](https://codecov.io/gh/jiasyuanchu/amazon-insights)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

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
python3 scripts/test_tracker.py
python3 cache_manager.py test
python3 scripts/run_tests.py  # Complete test suite
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

#### Option 1: GitHub Pages Deployment (Recommended for Demo)
**🌐 Live Demo**: [https://jiasyuanchu.github.io/amazon-insights/](https://jiasyuanchu.github.io/amazon-insights/)

The dashboard is automatically deployed to GitHub Pages via GitHub Actions:
- ✅ **Automatic Deployment**: Every push to `main` triggers deployment
- ✅ **Free Hosting**: No server costs or maintenance required
- ✅ **Global CDN**: Fast loading worldwide with HTTPS
- ✅ **Professional URL**: Clean, shareable link for demos

#### Option 2: Local Development
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
├── scripts/              # Development and testing tools
│   ├── test_cache.py     # Cache testing
│   ├── test_tracker.py   # System testing
│   ├── test_competitive.py # Competitive analysis testing
│   ├── run_tests.py      # Test suite runner
│   └── coverage_report.py # 動態測試覆蓋率報告生成器
│   └── demo_competitive_workflow.py # Demo workflow
├── deployment/           # Deployment configurations
│   ├── docker-compose.yml # Multi-service deployment
│   ├── Dockerfile        # Application container
│   └── database_migration.py # Database migration tools
└── tests/                # CI/CD test suites
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

## CI/CD Pipeline

The project includes comprehensive GitHub Actions workflows for continuous integration and deployment.

### Automated Workflows

#### CI Pipeline (`.github/workflows/ci.yml`)
Triggered on every push and pull request:

- **Environment Setup**: Python 3.11 with dependency installation
- **Project Validation**: File structure and configuration checks
- **Import Testing**: Core module import validation
- **Basic Functionality**: Essential component testing

#### CD Pipeline (`.github/workflows/deploy-pages.yml`)
Triggered on main branch pushes:

- **Frontend Deployment**: Automatic deployment to GitHub Pages
- **Live Demo**: Updates [https://jiasyuanchu.github.io/amazon-insights/](https://jiasyuanchu.github.io/amazon-insights/)
- **Zero Configuration**: No server setup or maintenance required
- **Global CDN**: Fast loading with automatic HTTPS
- **Release Creation**: Automatic GitHub releases for version tags
- **Notifications**: Deployment status notifications

#### Dependency Management (`.github/workflows/dependency-update.yml`)
Weekly automated dependency updates:

- **Security Audits**: Weekly dependency vulnerability scanning
- **Update PRs**: Automated pull requests for dependency updates
- **Testing**: Validation of updated dependencies

### Running CI/CD Locally

#### Code Quality Checks
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/
```

#### Test Execution
```bash
# Run complete test suite
python run_tests.py

# Run specific test categories
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_competitive_analysis.py -v
python -m pytest tests/test_api_endpoints.py -v

# Generate coverage report
python -m pytest --cov=src --cov-report=html
```

## 📊 測試覆蓋率報告

該項目提供動態測試覆蓋率報告系統，讓開發團隊隨時了解代碼覆蓋率狀況。

### 🚀 快速查看覆蓋率

```bash
# 一鍵生成並顯示覆蓋率報告
./coverage

# 或者使用完整路徑
python3 scripts/coverage_report.py
```

### 📈 報告內容

覆蓋率報告包含以下信息：

- **📊 整體覆蓋率摘要**: 總覆蓋率、代碼行數、測試數量
- **🎯 功能模組分析**: 各功能區塊的覆蓋率狀況
  - 功能一：產品資料追蹤系統
  - API層：介面和數據模型
  - 功能二：競品分析引擎  
  - 共同基礎設施：配置、緩存、任務
- **🏆 高覆蓋率文件**: 覆蓋率 ≥70% 的文件列表
- **⚠️ 需改善文件**: 覆蓋率 <50% 需要改善的文件
- **💡 改善建議**: 針對當前覆蓋率狀況的具體建議

### 📋 報告示例輸出

```
================================================================================
📊 AMAZON INSIGHTS - 測試覆蓋率報告
================================================================================
⏰ 生成時間: 2024-01-15 14:30:25

🎯 整體覆蓋率摘要
----------------------------------------
總覆蓋率:     🟡 33.2% (B+)
總代碼行數:   📄 2,644 行
已覆蓋行數:   ✅ 876 行
測試總數:     🧪 94 個

📈 各功能模組覆蓋率
--------------------------------------------------
模組                 覆蓋率       狀態     文件數
--------------------------------------------------
功能一：產品追蹤       45.0% (C+)  🟠       4個
API層               33.0% (C )  🔴       6個
功能二：競品分析       21.0% (C )  🔴       4個
共同基礎設施          38.0% (C+)  🟠       4個

🏆 高覆蓋率文件 (≥70%)
----------------------------------------------------------------------
文件                                        覆蓋率       狀態
----------------------------------------------------------------------
competitive_models.py                     100.0% (A+) 🟢
schemas.py                               100.0% (A+) 🟢
amazon_parser.py                          80.0% (A ) 🟢
app.py                                    81.0% (A ) 🟢
config.py                                 91.0% (A ) 🟢
```

### 🔧 高級覆蓋率命令

```bash
# 生成 HTML 詳細報告
python3 -m pytest tests/ --cov=src --cov=api --cov-report=html
open htmlcov/index.html

# 針對特定功能模組測試
python3 -m pytest tests/test_feature1_* --cov=src.parsers --cov=src.monitoring
python3 -m pytest tests/test_api_* --cov=api --cov-report=term-missing

# 設定覆蓋率門檻
python3 -m pytest tests/ --cov=src --cov-fail-under=70
```

### 🎯 覆蓋率目標

| 模組類型 | 目標覆蓋率 | 當前狀況 |
|----------|------------|----------|
| **數據模型** | 90%+ | ✅ 已達標 |
| **核心業務邏輯** | 80%+ | 🟡 進行中 |
| **API介面** | 70%+ | 🔴 需改善 |
| **基礎設施** | 60%+ | 🟡 接近目標 |

### 📝 覆蓋率改善指南

1. **優先級順序**：
   - 🥇 核心業務邏輯（parsers, competitive）
   - 🥈 數據模型和API schemas
   - 🥉 基礎設施和工具函數

2. **測試策略**：
   - 📋 使用 Mock 避免外部依賴
   - 🎯 專注純函數和業務邏輯
   - 📊 優先測試高複雜度模組

3. **持續改善**：
   - 🔄 定期執行 `./coverage` 檢查進度
   - 📈 設定團隊覆蓋率目標
   - 🚀 在 CI/CD 中集成覆蓋率檢查

#### Build Testing
```bash
# Test Docker builds
docker build -f deployment/Dockerfile -t amazon-insights-api --target production .
docker build -f deployment/Dockerfile.frontend -t amazon-insights-frontend .

# Test Docker Compose
docker-compose -f deployment/docker-compose.yml config --quiet
```

### Status Badges

The badges at the top of this README show:
- **CI Pipeline**: Code quality, testing, and build status
- **CD Pipeline**: Deployment and release status
- **Security Audit**: Dependency security status
- **Code Coverage**: Test coverage percentage
- **License**: MIT license
- **Python Version**: Minimum Python version requirement
- **PostgreSQL**: Database version requirement
- **Docker**: Container deployment ready

### Development Workflow

1. **Feature Development**:
   ```bash
   git checkout -b feature/new-feature
   # Develop your feature
   black .  # Format code
   flake8 . # Check linting
   python run_tests.py  # Run tests
   ```

2. **Create Pull Request**:
   - CI pipeline automatically runs on PR creation
   - All checks must pass before merge
   - Code review required for main branch

3. **Release Process**:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   # CD pipeline automatically creates GitHub release
   ```

### Monitoring CI/CD

- **GitHub Actions**: View workflow runs at `https://github.com/jiasyuanchu/amazon-insights/actions`
- **Coverage Reports**: Available in CI artifacts and Codecov integration
- **Security Reports**: Uploaded as artifacts in each workflow run
- **Docker Images**: Available at GitHub Container Registry