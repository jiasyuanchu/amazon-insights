import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import statistics
from dataclasses import dataclass

from src.competitive.manager import CompetitiveManager
from src.monitoring.product_tracker import ProductTracker
from src.models.competitive_models import CompetitiveAnalysisReport, ProductFeatures
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_DEFAULT_TTL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CompetitiveMetrics:
    asin: str
    title: str
    price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    bsr_data: Optional[Dict]
    bullet_points: List[str]
    key_features: Dict[str, List[str]]
    availability: str

class CompetitiveAnalyzer:
    """Multi-dimensional competitive analysis engine"""
    
    def __init__(self):
        self.manager = CompetitiveManager()
        self.tracker = ProductTracker()
    
    def analyze_competitive_group(self, group_id: int) -> Dict:
        """Perform comprehensive competitive analysis for a group"""
        try:
            # Get competitive group
            group = self.manager.get_competitive_group(group_id)
            if not group:
                return {"error": "Competitive group not found"}
            
            logger.info(f"Starting competitive analysis for group: {group.name}")
            
            # Get all product data
            main_product_data = self._get_product_metrics(group.main_product_asin)
            if not main_product_data:
                return {"error": f"Main product data not available for {group.main_product_asin}"}
            
            competitors_data = []
            for competitor in group.active_competitors:
                comp_data = self._get_product_metrics(competitor.asin)
                if comp_data:
                    comp_data.competitor_name = competitor.competitor_name
                    comp_data.priority = competitor.priority
                    competitors_data.append(comp_data)
            
            if not competitors_data:
                return {"error": "No competitor data available"}
            
            # Perform multi-dimensional analysis
            analysis_result = {
                "group_info": {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "main_product_asin": group.main_product_asin,
                    "competitors_count": len(competitors_data)
                },
                "main_product": self._metrics_to_dict(main_product_data),
                "competitors": [self._metrics_to_dict(comp) for comp in competitors_data],
                "price_analysis": self._analyze_price_positioning(main_product_data, competitors_data),
                "bsr_analysis": self._analyze_bsr_positioning(main_product_data, competitors_data),
                "rating_analysis": self._analyze_rating_positioning(main_product_data, competitors_data),
                "feature_analysis": self._analyze_feature_comparison(main_product_data, competitors_data),
                "competitive_summary": self._generate_competitive_summary(main_product_data, competitors_data),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Cache the analysis result
            cache_key = f"competitive:analysis:{group_id}"
            cache.set(cache_key, analysis_result, CACHE_DEFAULT_TTL)
            
            logger.info(f"Competitive analysis completed for group {group.name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in competitive analysis for group {group_id}: {str(e)}")
            return {"error": str(e)}
    
    def _get_product_metrics(self, asin: str) -> Optional[CompetitiveMetrics]:
        """Get comprehensive product metrics for competitive analysis"""
        try:
            # Get basic product summary
            summary = self.tracker.get_product_summary(asin)
            if "error" in summary:
                logger.warning(f"No summary data for {asin}: {summary['error']}")
                return None
            
            # Get latest snapshot for detailed features
            latest_snapshot = self.tracker.db_manager.get_latest_snapshot(asin)
            if not latest_snapshot:
                logger.warning(f"No snapshot data for {asin}")
                return None
            
            # Extract features from raw data if available
            bullet_points = []
            key_features = {}
            
            if latest_snapshot.raw_data:
                from src.parsers.amazon_parser import AmazonProductParser
                parser = AmazonProductParser()
                
                if isinstance(latest_snapshot.raw_data, dict):
                    bullet_points = latest_snapshot.raw_data.get('bullet_points', [])
                    key_features = latest_snapshot.raw_data.get('key_features', {})
            
            return CompetitiveMetrics(
                asin=asin,
                title=summary['title'] or "Unknown Product",
                price=summary['current_price'],
                rating=summary['current_rating'],
                review_count=summary['current_review_count'],
                bsr_data=summary['bsr_data'],
                bullet_points=bullet_points,
                key_features=key_features,
                availability=summary['availability']
            )
            
        except Exception as e:
            logger.error(f"Error getting product metrics for {asin}: {str(e)}")
            return None
    
    def _metrics_to_dict(self, metrics: CompetitiveMetrics) -> Dict:
        """Convert CompetitiveMetrics to dictionary"""
        result = {
            "asin": metrics.asin,
            "title": metrics.title,
            "price": metrics.price,
            "rating": metrics.rating,
            "review_count": metrics.review_count,
            "bsr_data": metrics.bsr_data,
            "bullet_points": metrics.bullet_points,
            "key_features": metrics.key_features,
            "availability": metrics.availability
        }
        
        # Add competitor-specific fields if they exist
        if hasattr(metrics, 'competitor_name'):
            result["competitor_name"] = metrics.competitor_name
        if hasattr(metrics, 'priority'):
            result["priority"] = metrics.priority
            
        return result
    
    def _analyze_price_positioning(self, main_product: CompetitiveMetrics, 
                                 competitors: List[CompetitiveMetrics]) -> Dict:
        """Analyze price positioning against competitors"""
        try:
            # Collect all prices
            all_prices = []
            main_price = main_product.price
            
            if main_price:
                all_prices.append(main_price)
            
            competitor_prices = []
            for comp in competitors:
                if comp.price:
                    all_prices.append(comp.price)
                    competitor_prices.append({
                        "asin": comp.asin,
                        "title": comp.title[:50] + "...",
                        "price": comp.price,
                        "price_difference": comp.price - main_price if main_price else None,
                        "price_difference_percent": ((comp.price - main_price) / main_price * 100) if main_price else None
                    })
            
            if not all_prices:
                return {"error": "No price data available"}
            
            # Calculate price statistics
            min_price = min(all_prices)
            max_price = max(all_prices)
            avg_price = statistics.mean(all_prices)
            
            # Determine price position
            price_position = "unknown"
            if main_price:
                if main_price == min_price:
                    price_position = "lowest"
                elif main_price == max_price:
                    price_position = "highest"
                else:
                    price_position = "middle"
            
            return {
                "main_product_price": main_price,
                "price_position": price_position,
                "market_price_range": {
                    "min": min_price,
                    "max": max_price,
                    "average": round(avg_price, 2),
                    "spread": round(max_price - min_price, 2)
                },
                "competitors": competitor_prices,
                "price_advantage": main_price <= avg_price if main_price else None,
                "cheaper_competitors": len([p for p in competitor_prices if p["price"] < main_price]) if main_price else 0,
                "more_expensive_competitors": len([p for p in competitor_prices if p["price"] > main_price]) if main_price else 0
            }
            
        except Exception as e:
            logger.error(f"Error in price analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_bsr_positioning(self, main_product: CompetitiveMetrics, 
                               competitors: List[CompetitiveMetrics]) -> Dict:
        """Analyze BSR (Best Sellers Rank) positioning"""
        try:
            if not main_product.bsr_data:
                return {"error": "No BSR data for main product"}
            
            bsr_analysis = {}
            
            # Analyze each BSR category
            for category, main_rank in main_product.bsr_data.items():
                category_analysis = {
                    "main_product_rank": main_rank,
                    "competitors": [],
                    "position": "unknown"
                }
                
                competitor_ranks = []
                for comp in competitors:
                    if comp.bsr_data and category in comp.bsr_data:
                        comp_rank = comp.bsr_data[category]
                        competitor_ranks.append(comp_rank)
                        category_analysis["competitors"].append({
                            "asin": comp.asin,
                            "title": comp.title[:50] + "...",
                            "rank": comp_rank,
                            "rank_difference": comp_rank - main_rank,
                            "better_rank": comp_rank < main_rank  # Lower rank is better
                        })
                
                if competitor_ranks:
                    all_ranks = [main_rank] + competitor_ranks
                    best_rank = min(all_ranks)
                    worst_rank = max(all_ranks)
                    
                    # Determine position
                    if main_rank == best_rank:
                        category_analysis["position"] = "best"
                    elif main_rank == worst_rank:
                        category_analysis["position"] = "worst"
                    else:
                        category_analysis["position"] = "middle"
                    
                    category_analysis["rank_statistics"] = {
                        "best_rank": best_rank,
                        "worst_rank": worst_rank,
                        "average_rank": round(statistics.mean(all_ranks), 0),
                        "competitors_with_better_rank": len([r for r in competitor_ranks if r < main_rank]),
                        "competitors_with_worse_rank": len([r for r in competitor_ranks if r > main_rank])
                    }
                
                bsr_analysis[category] = category_analysis
            
            return bsr_analysis
            
        except Exception as e:
            logger.error(f"Error in BSR analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_rating_positioning(self, main_product: CompetitiveMetrics, 
                                  competitors: List[CompetitiveMetrics]) -> Dict:
        """Analyze rating and review positioning"""
        try:
            all_ratings = []
            all_review_counts = []
            
            main_rating = main_product.rating
            main_reviews = main_product.review_count
            
            if main_rating:
                all_ratings.append(main_rating)
            if main_reviews:
                all_review_counts.append(main_reviews)
            
            competitor_ratings = []
            for comp in competitors:
                comp_data = {
                    "asin": comp.asin,
                    "title": comp.title[:50] + "...",
                    "rating": comp.rating,
                    "review_count": comp.review_count
                }
                
                if comp.rating:
                    all_ratings.append(comp.rating)
                    comp_data["rating_difference"] = comp.rating - main_rating if main_rating else None
                
                if comp.review_count:
                    all_review_counts.append(comp.review_count)
                    comp_data["review_count_difference"] = comp.review_count - main_reviews if main_reviews else None
                
                competitor_ratings.append(comp_data)
            
            # Calculate statistics
            rating_stats = {}
            if all_ratings:
                rating_stats = {
                    "min": min(all_ratings),
                    "max": max(all_ratings),
                    "average": round(statistics.mean(all_ratings), 2),
                    "main_product_position": "highest" if main_rating == max(all_ratings) else 
                                           "lowest" if main_rating == min(all_ratings) else "middle"
                }
            
            review_stats = {}
            if all_review_counts:
                review_stats = {
                    "min": min(all_review_counts),
                    "max": max(all_review_counts),
                    "average": round(statistics.mean(all_review_counts), 0),
                    "main_product_position": "highest" if main_reviews == max(all_review_counts) else 
                                           "lowest" if main_reviews == min(all_review_counts) else "middle"
                }
            
            return {
                "main_product": {
                    "rating": main_rating,
                    "review_count": main_reviews
                },
                "competitors": competitor_ratings,
                "rating_statistics": rating_stats,
                "review_statistics": review_stats,
                "quality_advantage": main_rating >= statistics.mean(all_ratings) if all_ratings and main_rating else None,
                "popularity_advantage": main_reviews >= statistics.mean(all_review_counts) if all_review_counts and main_reviews else None
            }
            
        except Exception as e:
            logger.error(f"Error in rating analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_feature_comparison(self, main_product: CompetitiveMetrics, 
                                  competitors: List[CompetitiveMetrics]) -> Dict:
        """Analyze feature comparison across products"""
        try:
            # Collect all features
            all_features = {}
            feature_frequency = {}
            
            # Process main product features
            main_features = main_product.key_features
            for category, features in main_features.items():
                if category not in all_features:
                    all_features[category] = {"main": features, "competitors": {}}
                    feature_frequency[category] = {}
                
                for feature in features:
                    if feature not in feature_frequency[category]:
                        feature_frequency[category][feature] = {"main": True, "competitors": []}
            
            # Process competitor features
            for comp in competitors:
                comp_features = comp.key_features
                for category, features in comp_features.items():
                    if category not in all_features:
                        all_features[category] = {"main": [], "competitors": {}}
                        feature_frequency[category] = {}
                    
                    all_features[category]["competitors"][comp.asin] = features
                    
                    for feature in features:
                        if feature not in feature_frequency[category]:
                            feature_frequency[category][feature] = {"main": False, "competitors": []}
                        feature_frequency[category][feature]["competitors"].append(comp.asin)
            
            # Find unique features and common features
            unique_features = {}
            common_features = {}
            missing_features = {}
            
            for category, features in feature_frequency.items():
                unique_features[category] = []
                common_features[category] = []
                missing_features[category] = []
                
                for feature, presence in features.items():
                    competitor_count = len(presence["competitors"])
                    total_products = len(competitors) + 1
                    
                    if presence["main"] and competitor_count == 0:
                        unique_features[category].append(feature)
                    elif competitor_count >= len(competitors) * 0.7:  # 70% of competitors have it
                        common_features[category].append(feature)
                    elif not presence["main"] and competitor_count > 0:
                        missing_features[category].append(feature)
            
            return {
                "feature_categories": list(all_features.keys()),
                "unique_to_main": unique_features,
                "common_features": common_features,
                "missing_from_main": missing_features,
                "feature_diversity_score": self._calculate_feature_diversity(main_product, competitors),
                "detailed_comparison": all_features
            }
            
        except Exception as e:
            logger.error(f"Error in feature analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_feature_diversity(self, main_product: CompetitiveMetrics, 
                                   competitors: List[CompetitiveMetrics]) -> Dict:
        """Calculate feature diversity metrics"""
        try:
            # Count total features for each product
            main_feature_count = sum(len(features) for features in main_product.key_features.values())
            
            competitor_feature_counts = []
            for comp in competitors:
                comp_count = sum(len(features) for features in comp.key_features.values())
                competitor_feature_counts.append(comp_count)
            
            avg_competitor_features = statistics.mean(competitor_feature_counts) if competitor_feature_counts else 0
            
            return {
                "main_product_features": main_feature_count,
                "average_competitor_features": round(avg_competitor_features, 1),
                "feature_richness": "above_average" if main_feature_count > avg_competitor_features else "below_average",
                "feature_count_comparison": main_feature_count - avg_competitor_features
            }
            
        except Exception as e:
            logger.error(f"Error calculating feature diversity: {str(e)}")
            return {}
    
    def _generate_competitive_summary(self, main_product: CompetitiveMetrics, 
                                    competitors: List[CompetitiveMetrics]) -> Dict:
        """Generate overall competitive summary"""
        try:
            # Calculate competitive scores (0-100)
            scores = {}
            
            # Price competitiveness (lower price = higher score)
            if main_product.price:
                competitor_prices = [c.price for c in competitors if c.price]
                if competitor_prices:
                    avg_comp_price = statistics.mean(competitor_prices)
                    # Score: 100 if cheapest, 0 if most expensive
                    price_ratio = main_product.price / avg_comp_price
                    scores["price_competitiveness"] = max(0, min(100, (2 - price_ratio) * 50))
            
            # Quality competitiveness (higher rating = higher score)
            if main_product.rating:
                competitor_ratings = [c.rating for c in competitors if c.rating]
                if competitor_ratings:
                    avg_comp_rating = statistics.mean(competitor_ratings)
                    max_rating = 5.0
                    scores["quality_competitiveness"] = (main_product.rating / max_rating) * 100
            
            # Popularity competitiveness (better BSR = higher score)
            if main_product.bsr_data:
                # Use the best (lowest) BSR rank as reference
                main_best_rank = min(main_product.bsr_data.values()) if main_product.bsr_data else float('inf')
                
                competitor_best_ranks = []
                for comp in competitors:
                    if comp.bsr_data:
                        comp_best_rank = min(comp.bsr_data.values())
                        competitor_best_ranks.append(comp_best_rank)
                
                if competitor_best_ranks:
                    avg_comp_rank = statistics.mean(competitor_best_ranks)
                    # Score: higher if rank is better (lower number)
                    if main_best_rank < avg_comp_rank:
                        scores["popularity_competitiveness"] = min(100, (avg_comp_rank - main_best_rank) / avg_comp_rank * 100)
                    else:
                        scores["popularity_competitiveness"] = max(0, 50 - (main_best_rank - avg_comp_rank) / avg_comp_rank * 50)
            
            # Overall competitiveness (average of all scores)
            if scores:
                scores["overall_competitiveness"] = round(statistics.mean(scores.values()), 1)
            
            # Competitive position summary
            position_summary = {
                "price_position": "competitive" if scores.get("price_competitiveness", 0) > 50 else "expensive",
                "quality_position": "superior" if scores.get("quality_competitiveness", 0) > 70 else "average",
                "popularity_position": "leading" if scores.get("popularity_competitiveness", 0) > 60 else "following",
                "overall_position": "strong" if scores.get("overall_competitiveness", 0) > 60 else "weak"
            }
            
            return {
                "competitive_scores": scores,
                "position_summary": position_summary,
                "total_competitors": len(competitors),
                "analysis_confidence": "high" if len(competitors) >= 3 else "medium"
            }
            
        except Exception as e:
            logger.error(f"Error generating competitive summary: {str(e)}")
            return {"error": str(e)}
    
    def get_trend_analysis(self, group_id: int, days: int = 30) -> Dict:
        """Get competitive trend analysis over time"""
        try:
            # This would require historical competitive data
            # For now, return a placeholder structure
            
            logger.info(f"Generating trend analysis for group {group_id} over {days} days")
            
            return {
                "group_id": group_id,
                "trend_period_days": days,
                "trends": {
                    "price_trends": {},
                    "bsr_trends": {},
                    "rating_trends": {}
                },
                "note": "Trend analysis requires historical data collection over time"
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return {"error": str(e)}