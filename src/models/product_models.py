from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config.config import DATABASE_URL
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_LONG_TTL

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    asin = Column(String(20), nullable=False, index=True)
    title = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProductSnapshot(Base):
    __tablename__ = 'product_snapshots'
    
    id = Column(Integer, primary_key=True)
    asin = Column(String(20), nullable=False, index=True)
    scraped_at = Column(DateTime, nullable=False, index=True)
    
    # Product Info
    title = Column(Text)
    
    # Price Data
    price = Column(Float)
    buybox_price = Column(Float)
    
    # Rating Data
    rating = Column(Float)
    review_count = Column(Integer)
    
    # BSR Data (stored as JSON)
    bsr_data = Column(JSON)
    
    # Availability
    availability = Column(String(100))
    
    # Raw data for debugging
    raw_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceAlert(Base):
    __tablename__ = 'price_alerts'
    
    id = Column(Integer, primary_key=True)
    asin = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # 'price_increase', 'price_decrease', 'bsr_change', etc.
    old_value = Column(Float)
    new_value = Column(Float)
    change_percentage = Column(Float)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)

class DatabaseManager:
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def save_product_snapshot(self, asin: str, product_data: dict) -> ProductSnapshot:
        with self.get_session() as session:
            snapshot = ProductSnapshot(
                asin=asin,
                scraped_at=datetime.fromisoformat(product_data.get('scraped_at', datetime.now().isoformat())),
                title=product_data.get('title'),
                price=product_data.get('price'),
                buybox_price=product_data.get('buybox_price'),
                rating=product_data.get('rating'),
                review_count=product_data.get('review_count'),
                bsr_data=product_data.get('bsr'),
                availability=product_data.get('availability'),
                raw_data=product_data
            )
            
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot
    
    def get_latest_snapshot(self, asin: str) -> ProductSnapshot:
        with self.get_session() as session:
            return session.query(ProductSnapshot).filter(
                ProductSnapshot.asin == asin
            ).order_by(ProductSnapshot.scraped_at.desc()).first()
    
    def get_price_history(self, asin: str, limit: int = 100):
        # Try to get from cache
        cache_key = CacheKeyBuilder.product_history(asin, limit)
        cached_history = cache.get(cache_key)
        if cached_history:
            return cached_history
        
        with self.get_session() as session:
            history = session.query(ProductSnapshot).filter(
                ProductSnapshot.asin == asin
            ).order_by(ProductSnapshot.scraped_at.desc()).limit(limit).all()
            
            # Cache result (48 hours, historical data changes less frequently)
            cache.set(cache_key, history, CACHE_LONG_TTL)
            
            return history
    
    def save_alert(self, asin: str, alert_type: str, old_value: float, 
                   new_value: float, message: str) -> PriceAlert:
        with self.get_session() as session:
            change_percentage = 0
            if old_value and old_value != 0:
                change_percentage = ((new_value - old_value) / old_value) * 100
            
            alert = PriceAlert(
                asin=asin,
                alert_type=alert_type,
                old_value=old_value,
                new_value=new_value,
                change_percentage=change_percentage,
                message=message
            )
            
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
    
    def get_recent_alerts(self, hours: int = 24):
        from datetime import timedelta
        
        with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return session.query(PriceAlert).filter(
                PriceAlert.triggered_at >= cutoff_time
            ).order_by(PriceAlert.triggered_at.desc()).all()