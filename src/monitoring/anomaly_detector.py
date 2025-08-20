import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from statistics import mean, stdev

from src.models.product_models import DatabaseManager, ProductSnapshot
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_DEFAULT_TTL, CACHE_SHORT_TTL
from config.config import ALERT_THRESHOLD_PRICE_CHANGE, ALERT_THRESHOLD_BSR_CHANGE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.price_change_threshold = ALERT_THRESHOLD_PRICE_CHANGE
        self.bsr_change_threshold = ALERT_THRESHOLD_BSR_CHANGE
    
    def detect_price_anomalies(self, asin: str, current_data: Dict) -> List[Dict]:
        anomalies = []
        
        try:
            # Get recent price history
            recent_snapshots = self.db_manager.get_price_history(asin, limit=30)
            
            if len(recent_snapshots) < 2:
                return anomalies
            
            current_price = current_data.get('price')
            if not current_price:
                return anomalies
            
            # Compare with most recent price
            latest_snapshot = recent_snapshots[0] if recent_snapshots[0].asin != asin else recent_snapshots[1]
            if latest_snapshot and latest_snapshot.price:
                price_change = abs(current_price - latest_snapshot.price) / latest_snapshot.price
                
                if price_change > self.price_change_threshold:
                    direction = "increased" if current_price > latest_snapshot.price else "decreased"
                    anomaly = {
                        "type": "price_change",
                        "severity": self._get_severity(price_change),
                        "message": f"Price {direction} by {price_change:.2%}",
                        "old_value": latest_snapshot.price,
                        "new_value": current_price,
                        "change_percentage": price_change * 100,
                        "detected_at": datetime.now().isoformat()
                    }
                    anomalies.append(anomaly)
                    
                    # Save alert to database
                    self.db_manager.save_alert(
                        asin, "price_change", latest_snapshot.price, 
                        current_price, anomaly["message"]
                    )
            
            # Check for unusual price patterns
            prices = [s.price for s in recent_snapshots[-14:] if s.price]  # Last 14 data points
            if len(prices) >= 7:
                price_volatility_anomaly = self._detect_price_volatility(asin, current_price, prices)
                if price_volatility_anomaly:
                    anomalies.append(price_volatility_anomaly)
            
        except Exception as e:
            logger.error(f"Error detecting price anomalies for {asin}: {str(e)}")
        
        return anomalies
    
    def detect_rating_anomalies(self, asin: str, current_data: Dict) -> List[Dict]:
        anomalies = []
        
        try:
            recent_snapshots = self.db_manager.get_price_history(asin, limit=10)
            
            current_rating = current_data.get('rating')
            current_review_count = current_data.get('review_count')
            
            if not current_rating or len(recent_snapshots) < 2:
                return anomalies
            
            # Find the most recent snapshot with rating data
            previous_snapshot = None
            for snapshot in recent_snapshots:
                if snapshot.rating and snapshot.asin != asin:
                    previous_snapshot = snapshot
                    break
            
            if not previous_snapshot:
                return anomalies
            
            # Check for significant rating change
            if previous_snapshot.rating:
                rating_change = abs(current_rating - previous_snapshot.rating)
                if rating_change > 0.5:  # Rating changed by more than 0.5 stars
                    direction = "increased" if current_rating > previous_snapshot.rating else "decreased"
                    anomaly = {
                        "type": "rating_change",
                        "severity": "high" if rating_change > 1.0 else "medium",
                        "message": f"Rating {direction} by {rating_change:.1f} stars",
                        "old_value": previous_snapshot.rating,
                        "new_value": current_rating,
                        "detected_at": datetime.now().isoformat()
                    }
                    anomalies.append(anomaly)
                    
                    self.db_manager.save_alert(
                        asin, "rating_change", previous_snapshot.rating,
                        current_rating, anomaly["message"]
                    )
            
            # Check for sudden spike in reviews
            if current_review_count and previous_snapshot.review_count:
                review_increase = current_review_count - previous_snapshot.review_count
                if review_increase > 100:  # More than 100 new reviews
                    anomaly = {
                        "type": "review_spike",
                        "severity": "high" if review_increase > 500 else "medium",
                        "message": f"Review count increased by {review_increase}",
                        "old_value": previous_snapshot.review_count,
                        "new_value": current_review_count,
                        "detected_at": datetime.now().isoformat()
                    }
                    anomalies.append(anomaly)
                    
                    self.db_manager.save_alert(
                        asin, "review_spike", previous_snapshot.review_count,
                        current_review_count, anomaly["message"]
                    )
        
        except Exception as e:
            logger.error(f"Error detecting rating anomalies for {asin}: {str(e)}")
        
        return anomalies
    
    def detect_bsr_anomalies(self, asin: str, current_data: Dict) -> List[Dict]:
        anomalies = []
        
        try:
            current_bsr = current_data.get('bsr')
            if not current_bsr:
                return anomalies
            
            recent_snapshots = self.db_manager.get_price_history(asin, limit=10)
            
            # Find previous BSR data
            previous_bsr = None
            for snapshot in recent_snapshots:
                if snapshot.bsr_data and snapshot.asin != asin:
                    previous_bsr = snapshot.bsr_data
                    break
            
            if not previous_bsr:
                return anomalies
            
            # Compare BSR changes for each category
            for category, current_rank in current_bsr.items():
                if category in previous_bsr:
                    previous_rank = previous_bsr[category]
                    
                    # Calculate percentage change (lower rank is better)
                    if previous_rank > 0:
                        rank_change = (current_rank - previous_rank) / previous_rank
                        
                        # Significant improvement (rank went down significantly)
                        if rank_change < -self.bsr_change_threshold:
                            anomaly = {
                                "type": "bsr_improvement",
                                "severity": self._get_bsr_severity(abs(rank_change)),
                                "message": f"BSR improved in {category}: #{previous_rank} -> #{current_rank}",
                                "category": category,
                                "old_value": previous_rank,
                                "new_value": current_rank,
                                "change_percentage": rank_change * 100,
                                "detected_at": datetime.now().isoformat()
                            }
                            anomalies.append(anomaly)
                        
                        # Significant decline (rank went up significantly)
                        elif rank_change > self.bsr_change_threshold:
                            anomaly = {
                                "type": "bsr_decline",
                                "severity": self._get_bsr_severity(abs(rank_change)),
                                "message": f"BSR declined in {category}: #{previous_rank} -> #{current_rank}",
                                "category": category,
                                "old_value": previous_rank,
                                "new_value": current_rank,
                                "change_percentage": rank_change * 100,
                                "detected_at": datetime.now().isoformat()
                            }
                            anomalies.append(anomaly)
                            
                            self.db_manager.save_alert(
                                asin, f"bsr_change_{category}", previous_rank,
                                current_rank, anomaly["message"]
                            )
        
        except Exception as e:
            logger.error(f"Error detecting BSR anomalies for {asin}: {str(e)}")
        
        return anomalies
    
    def detect_availability_anomalies(self, asin: str, current_data: Dict) -> List[Dict]:
        anomalies = []
        
        try:
            current_availability = current_data.get('availability', '').lower()
            
            recent_snapshots = self.db_manager.get_price_history(asin, limit=5)
            
            # Check for stock status changes
            if recent_snapshots:
                previous_availability = recent_snapshots[0].availability
                if previous_availability:
                    previous_availability = previous_availability.lower()
                    
                    # Detect out of stock
                    if 'in stock' in previous_availability and 'out of stock' in current_availability:
                        anomaly = {
                            "type": "out_of_stock",
                            "severity": "high",
                            "message": f"Product went out of stock",
                            "old_value": previous_availability,
                            "new_value": current_availability,
                            "detected_at": datetime.now().isoformat()
                        }
                        anomalies.append(anomaly)
                        
                        self.db_manager.save_alert(
                            asin, "out_of_stock", 0, 1, anomaly["message"]
                        )
                    
                    # Detect back in stock
                    elif 'out of stock' in previous_availability and 'in stock' in current_availability:
                        anomaly = {
                            "type": "back_in_stock",
                            "severity": "medium",
                            "message": f"Product back in stock",
                            "old_value": previous_availability,
                            "new_value": current_availability,
                            "detected_at": datetime.now().isoformat()
                        }
                        anomalies.append(anomaly)
        
        except Exception as e:
            logger.error(f"Error detecting availability anomalies for {asin}: {str(e)}")
        
        return anomalies
    
    def detect_all_anomalies(self, asin: str, current_data: Dict) -> List[Dict]:
        all_anomalies = []
        
        # Detect different types of anomalies
        all_anomalies.extend(self.detect_price_anomalies(asin, current_data))
        all_anomalies.extend(self.detect_rating_anomalies(asin, current_data))
        all_anomalies.extend(self.detect_bsr_anomalies(asin, current_data))
        all_anomalies.extend(self.detect_availability_anomalies(asin, current_data))
        
        if all_anomalies:
            logger.info(f"Detected {len(all_anomalies)} anomalies for ASIN {asin}")
            for anomaly in all_anomalies:
                logger.warning(f"Anomaly: {anomaly['message']}")
        
        return all_anomalies
    
    def _detect_price_volatility(self, asin: str, current_price: float, price_history: List[float]) -> Optional[Dict]:
        try:
            if len(price_history) < 7:
                return None
            
            # Calculate standard deviation of recent prices
            price_mean = mean(price_history)
            price_std = stdev(price_history)
            
            # Check if current price is significantly different from recent trend
            if abs(current_price - price_mean) > 2 * price_std:
                return {
                    "type": "price_volatility",
                    "severity": "high",
                    "message": f"Price shows high volatility (σ={price_std:.2f})",
                    "current_price": current_price,
                    "mean_price": price_mean,
                    "std_deviation": price_std,
                    "detected_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error detecting price volatility for {asin}: {str(e)}")
        
        return None
    
    def _get_severity(self, change_percentage: float) -> str:
        if change_percentage > 0.5:  # 50%
            return "critical"
        elif change_percentage > 0.3:  # 30%
            return "high"
        elif change_percentage > 0.1:  # 10%
            return "medium"
        else:
            return "low"
    
    def _get_bsr_severity(self, change_percentage: float) -> str:
        if change_percentage > 2.0:  # 200%
            return "critical"
        elif change_percentage > 1.0:  # 100%
            return "high"
        elif change_percentage > 0.5:  # 50%
            return "medium"
        else:
            return "low"
    
    def get_recent_alerts_summary(self, hours: int = 24) -> Dict:
        # Try to get from cache
        cache_key = CacheKeyBuilder.alerts_summary(hours)
        cached_summary = cache.get(cache_key)
        if cached_summary:
            logger.debug(f"Alerts summary cache hit for {hours} hours")
            return cached_summary
        
        try:
            recent_alerts = self.db_manager.get_recent_alerts(hours)
            
            # Group alerts by type and severity
            alert_summary = {
                "total_alerts": len(recent_alerts),
                "by_type": {},
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_asin": {}
            }
            
            for alert in recent_alerts:
                # Group by type
                if alert.alert_type not in alert_summary["by_type"]:
                    alert_summary["by_type"][alert.alert_type] = 0
                alert_summary["by_type"][alert.alert_type] += 1
                
                # Group by ASIN
                if alert.asin not in alert_summary["by_asin"]:
                    alert_summary["by_asin"][alert.asin] = 0
                alert_summary["by_asin"][alert.asin] += 1
            
            # Cache result (1 hour, because alerts change frequently)
            cache.set(cache_key, alert_summary, CACHE_SHORT_TTL)
            
            return alert_summary
        
        except Exception as e:
            logger.error(f"Error getting alerts summary: {str(e)}")
            return {"error": str(e)}