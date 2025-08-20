import logging
import time
from typing import List, Dict
from datetime import datetime, timedelta

from src.api.firecrawl_client import FirecrawlClient
from src.parsers.amazon_parser import AmazonProductParser
from src.models.product_models import DatabaseManager
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_LONG_TTL, CACHE_DEFAULT_TTL
from config.config import AMAZON_ASINS, MONITORING_INTERVAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductTracker:
    def __init__(self):
        self.firecrawl_client = FirecrawlClient()
        self.parser = AmazonProductParser()
        self.db_manager = DatabaseManager()
        self.asins = AMAZON_ASINS
    
    def track_single_product(self, asin: str) -> bool:
        try:
            logger.info(f"Tracking product: {asin}")
            
            # Scrape product data
            raw_data = self.firecrawl_client.scrape_amazon_product(asin)
            if not raw_data:
                logger.error(f"Failed to scrape data for ASIN: {asin}")
                return False
            
            # Parse product data
            parsed_data = self.parser.parse_product_data(raw_data)
            if not parsed_data:
                logger.error(f"Failed to parse data for ASIN: {asin}")
                return False
            
            # Save to database
            snapshot = self.db_manager.save_product_snapshot(asin, parsed_data)
            logger.info(f"Saved snapshot for {asin}: {snapshot.title[:50]}...")
            
            # Clear related cache
            self._invalidate_product_cache(asin)
            
            # Check for alerts (will be implemented in anomaly detection)
            self._check_for_anomalies(asin, parsed_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking product {asin}: {str(e)}")
            return False
    
    def track_all_products(self) -> Dict[str, bool]:
        results = {}
        
        logger.info(f"Starting batch tracking for {len(self.asins)} products")
        
        for asin in self.asins:
            success = self.track_single_product(asin)
            results[asin] = success
            
            # Add delay between requests to be respectful
            time.sleep(2)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Batch tracking completed: {successful}/{len(self.asins)} successful")
        
        return results
    
    def get_product_summary(self, asin: str) -> Dict:
        # Try to get from cache
        cache_key = CacheKeyBuilder.product_summary(asin)
        cached_summary = cache.get(cache_key)
        if cached_summary:
            logger.debug(f"Product summary cache hit for {asin}")
            return cached_summary
        
        try:
            latest_snapshot = self.db_manager.get_latest_snapshot(asin)
            if not latest_snapshot:
                return {"error": "No data found for this ASIN"}
            
            price_history = self.db_manager.get_price_history(asin, limit=30)
            
            # Calculate price trends
            prices = [s.price for s in price_history if s.price]
            price_trend = "stable"
            if len(prices) >= 2:
                recent_avg = sum(prices[:5]) / min(5, len(prices))
                older_avg = sum(prices[-5:]) / min(5, len(prices[-5:]))
                
                if recent_avg > older_avg * 1.05:
                    price_trend = "increasing"
                elif recent_avg < older_avg * 0.95:
                    price_trend = "decreasing"
            
            summary = {
                "asin": asin,
                "title": latest_snapshot.title,
                "current_price": latest_snapshot.price,
                "current_rating": latest_snapshot.rating,
                "current_review_count": latest_snapshot.review_count,
                "bsr_data": latest_snapshot.bsr_data,
                "availability": latest_snapshot.availability,
                "price_trend": price_trend,
                "last_updated": latest_snapshot.scraped_at.isoformat(),
                "history_count": len(price_history)
            }
            
            # Cache result (24 hours)
            cache.set(cache_key, summary, CACHE_DEFAULT_TTL)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting product summary for {asin}: {str(e)}")
            return {"error": str(e)}
    
    def get_all_products_summary(self) -> List[Dict]:
        # Try to get from cache
        cache_key = CacheKeyBuilder.all_products_summary()
        cached_summaries = cache.get(cache_key)
        if cached_summaries:
            logger.debug("All products summary cache hit")
            return cached_summaries
        
        summaries = []
        for asin in self.asins:
            summary = self.get_product_summary(asin)
            summaries.append(summary)
        
        # Cache result (24 hours)
        cache.set(cache_key, summaries, CACHE_DEFAULT_TTL)
        
        return summaries
    
    def _invalidate_product_cache(self, asin: str):
        """Invalidate product related cache"""
        try:
            # Clear product summary cache
            cache.delete(CacheKeyBuilder.product_summary(asin))
            
            # Clear product history cache (various limit parameters)
            for limit in [10, 20, 30, 50, 100]:
                cache.delete(CacheKeyBuilder.product_history(asin, limit))
            
            # Clear all products summary cache
            cache.delete(CacheKeyBuilder.all_products_summary())
            
            logger.debug(f"Cache invalidated for product {asin}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {asin}: {str(e)}")
    
    def _check_for_anomalies(self, asin: str, current_data: Dict):
        try:
            # Get previous snapshot for comparison
            previous_snapshot = self.db_manager.get_latest_snapshot(asin)
            if not previous_snapshot:
                return  # No previous data to compare
            
            # This will be expanded in the anomaly detection module
            # For now, just log significant changes
            
            if current_data.get('price') and previous_snapshot.price:
                price_change = abs(current_data['price'] - previous_snapshot.price) / previous_snapshot.price
                if price_change > 0.1:  # 10% change
                    logger.warning(f"Significant price change for {asin}: {previous_snapshot.price} -> {current_data['price']}")
            
        except Exception as e:
            logger.error(f"Error checking anomalies for {asin}: {str(e)}")
    
    def continuous_monitoring(self):
        logger.info(f"Starting continuous monitoring with {MONITORING_INTERVAL} hour intervals")
        
        while True:
            try:
                start_time = datetime.now()
                logger.info(f"Starting monitoring cycle at {start_time}")
                
                results = self.track_all_products()
                
                end_time = datetime.now()
                duration = end_time - start_time
                
                logger.info(f"Monitoring cycle completed in {duration}. Next cycle in {MONITORING_INTERVAL} hours.")
                
                # Sleep until next monitoring cycle
                sleep_seconds = MONITORING_INTERVAL * 3600  # Convert hours to seconds
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                # Sleep for a shorter period on error
                time.sleep(300)  # 5 minutes