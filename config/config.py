import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://amazon_insights:password@localhost:5432/amazon_insights",
)
DATABASE_URL_REPLICA = os.getenv("DATABASE_URL_REPLICA")  # Read replica URL
SQLITE_FALLBACK = (
    os.getenv("SQLITE_FALLBACK", "True").lower() == "true"
)  # Fallback to SQLite in dev

# If PostgreSQL not available and fallback enabled, use SQLite
if SQLITE_FALLBACK:
    try:
        import psycopg2

        # Test PostgreSQL connection
        import sqlalchemy

        engine = sqlalchemy.create_engine(DATABASE_URL)
        engine.connect().close()
    except (ImportError, Exception):
        DATABASE_URL = "sqlite:///data/amazon_insights.db"
        print("PostgreSQL not available, using SQLite fallback")

# Application Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MONITORING_INTERVAL = int(os.getenv("MONITORING_INTERVAL", "24"))
ALERT_THRESHOLD_PRICE_CHANGE = float(os.getenv("ALERT_THRESHOLD_PRICE_CHANGE", "0.1"))
ALERT_THRESHOLD_BSR_CHANGE = float(os.getenv("ALERT_THRESHOLD_BSR_CHANGE", "0.2"))

# Authentication Configuration
API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "False").lower() == "true"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Cache Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "86400"))  # 24 hours
CACHE_LONG_TTL = int(os.getenv("CACHE_LONG_TTL", "172800"))  # 48 hours
CACHE_SHORT_TTL = int(os.getenv("CACHE_SHORT_TTL", "3600"))  # 1 hour

AMAZON_ASINS = [
    "B07R7RMQF5",
    "B092XMWXK7",
    "B0BVY8K28Q",
    "B0CSMV2DTV",
    "B0D3XDR3NN",
    "B0CM22ZRTT",
    "B08SLQ9LFD",
    "B08VWJB2GZ",
    "B0DHKCM18G",
    "B07RKV9Z9D",
    "B08136DWMT",
    "B01CI6SO1A",
    "B092HVLSP5",
    "B0016BWUGE",
]
