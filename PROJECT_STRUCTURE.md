# Project Structure

## Core Application Files

```
amazon-insights/
├── src/                          # Core application code
│   ├── competitive/              # Competitive analysis engine
│   │   ├── analyzer.py           # Multi-dimensional analysis algorithms
│   │   ├── manager.py            # Group and competitor management
│   │   └── llm_reporter.py       # AI-powered report generation
│   ├── auth/                     # Authentication & authorization
│   │   ├── authentication.py     # API key authentication system
│   │   └── rate_limiter.py       # Redis-based rate limiting
│   ├── monitoring/               # Product tracking and alerts
│   │   ├── product_tracker.py    # Product data tracking
│   │   └── anomaly_detector.py   # Alert system
│   ├── models/                   # Database models
│   │   ├── product_models.py     # Product data models
│   │   └── competitive_models.py # Competitive analysis models
│   ├── parsers/                  # Data parsing
│   │   └── amazon_parser.py      # Amazon product data parser
│   ├── cache/                    # Caching system
│   │   └── redis_service.py      # Redis cache implementation
│   └── api/                      # External API clients
│       └── firecrawl_client.py   # Firecrawl API integration
├── api/                          # FastAPI routes and schemas
│   ├── routes/                   # API endpoint definitions
│   │   ├── products.py           # Product tracking endpoints
│   │   ├── competitive.py        # Competitive analysis endpoints
│   │   ├── alerts.py             # Alert management endpoints
│   │   ├── cache.py              # Cache management endpoints
│   │   └── system.py             # System status endpoints
│   └── models/                   # API data schemas
│       ├── schemas.py            # Core API schemas
│       └── competitive_schemas.py # Competitive analysis schemas
├── frontend/                     # Dashboard interface
│   ├── index.html                # Main dashboard interface
│   ├── script.js                 # Interactive functionality
│   ├── styles.css                # Professional styling
│   └── chart-fallback.js         # Chart backup system
├── config/                       # Configuration
│   └── config.py                 # Environment configuration
└── tests/                        # Test suites
    ├── test_basic.py              # Basic functionality tests
    └── test_ci_safe.py            # CI-safe tests
```

## Development & Deployment Tools

```
├── scripts/                      # Development and testing scripts
│   ├── test_cache.py             # Cache system testing
│   ├── test_tracker.py           # Product tracking testing
│   ├── test_competitive.py       # Competitive analysis testing
│   ├── demo_competitive_workflow.py # Demo workflow script
│   ├── run_tests.py              # Comprehensive test runner
│   ├── task_manager.py           # Task queue management
│   ├── beat.py                   # Celery beat scheduler
│   ├── worker.py                 # Celery worker process
│   ├── start_celery.sh           # Celery startup script
│   └── stop_celery.sh            # Celery shutdown script
└── deployment/                   # Deployment configurations
    ├── docker-compose.yml        # Multi-service deployment
    ├── Dockerfile                # Main application container
    ├── Dockerfile.frontend       # Frontend container
    └── database_migration.py     # SQLite to PostgreSQL migration
```

## Documentation Files

```
├── README.md                     # Main project documentation
├── ARCHITECTURE.md               # System architecture design
├── API_DESIGN.md                 # API specification
├── DATABASE_DESIGN.md            # Database design
├── DESIGN_DECISIONS.md           # Technical decisions
├── DEPLOYMENT_GUIDE.md           # Deployment instructions
├── COMPETITIVE_ANALYSIS_GUIDE.md # User guide
├── DASHBOARD_README.md           # Dashboard documentation
├── API_DOCUMENTATION.md          # API reference
└── POSTMAN_TESTING_GUIDE.md      # Testing guide
```

## Configuration Files

```
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore patterns
├── .flake8                       # Code linting configuration
├── mypy.ini                      # Type checking configuration
├── pytest.ini                   # Test configuration
├── requirements.txt              # Python dependencies
├── LICENSE                       # MIT license
├── postman_collection.json       # API test collection
└── competitive_analysis_postman.json # Competitive analysis tests
```

## Entry Points

```
├── app.py                        # Main API server
├── main.py                       # CLI interface
├── start_api.py                  # API server launcher
├── frontend_server.py            # Development frontend server
├── celery_config.py              # Celery configuration
└── tasks.py                      # Background task definitions
```

## Benefits of This Structure

### Clean Separation
- **Core Code**: `src/` contains only production code
- **API Layer**: `api/` contains only FastAPI-specific code
- **Development Tools**: `scripts/` contains testing and development utilities
- **Deployment**: `deployment/` contains all deployment configurations

### Production Ready
- **Docker Support**: All containers defined in `deployment/`
- **Configuration Management**: Clear environment variable handling
- **Testing Framework**: Organized in `tests/` and `scripts/`
- **Documentation**: Complete technical documentation

### Maintainability
- **Clear Responsibilities**: Each directory has a specific purpose
- **Easy Navigation**: Developers can quickly find relevant files
- **Scalable Structure**: Easy to add new modules or services
- **Clean Git History**: No unnecessary files cluttering commits