import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.product_models import DatabaseManager
from src.models.competitive_models import CompetitiveGroup, Competitor, ProductFeatures
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_DEFAULT_TTL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompetitiveManager:
    """Competitive Analysis Management System"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def create_competitive_group(self, name: str, main_product_asin: str, 
                               description: str = None) -> CompetitiveGroup:
        """Create a new competitive analysis group"""
        try:
            with self.db_manager.get_session() as session:
                # Check if main product exists in our tracking system
                from config.config import AMAZON_ASINS
                if main_product_asin not in AMAZON_ASINS:
                    logger.warning(f"Main product {main_product_asin} not in tracking list")
                
                group = CompetitiveGroup(
                    name=name,
                    main_product_asin=main_product_asin,
                    description=description
                )
                
                session.add(group)
                session.commit()
                session.refresh(group)
                
                logger.info(f"Created competitive group: {name} with main product {main_product_asin}")
                return group
                
        except Exception as e:
            logger.error(f"Error creating competitive group: {str(e)}")
            raise
    
    def add_competitor(self, group_id: int, competitor_asin: str, 
                      competitor_name: str = None, priority: int = 1) -> Competitor:
        """Add a competitor to a competitive group"""
        try:
            with self.db_manager.get_session() as session:
                # Check if group exists
                group = session.query(CompetitiveGroup).filter(
                    CompetitiveGroup.id == group_id
                ).first()
                
                if not group:
                    raise ValueError(f"Competitive group {group_id} not found")
                
                # Check if competitor already exists
                existing = session.query(Competitor).filter(
                    Competitor.competitive_group_id == group_id,
                    Competitor.asin == competitor_asin
                ).first()
                
                if existing:
                    logger.warning(f"Competitor {competitor_asin} already exists in group {group_id}")
                    return existing
                
                competitor = Competitor(
                    competitive_group_id=group_id,
                    asin=competitor_asin,
                    competitor_name=competitor_name or f"Competitor {competitor_asin}",
                    priority=priority
                )
                
                session.add(competitor)
                session.commit()
                session.refresh(competitor)
                
                # Clear related cache
                self._invalidate_group_cache(group_id)
                
                logger.info(f"Added competitor {competitor_asin} to group {group_id}")
                return competitor
                
        except Exception as e:
            logger.error(f"Error adding competitor: {str(e)}")
            raise
    
    def get_competitive_group(self, group_id: int) -> Optional[CompetitiveGroup]:
        """Get competitive group with all competitors"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(CompetitiveGroup).filter(
                    CompetitiveGroup.id == group_id,
                    CompetitiveGroup.is_active == True
                ).first()
                
                if group:
                    # Load competitors
                    competitors = session.query(Competitor).filter(
                        Competitor.competitive_group_id == group_id,
                        Competitor.is_active == True
                    ).order_by(Competitor.priority).all()
                    
                    # Attach competitors to group for easy access
                    group.active_competitors = competitors
                
                return group
                
        except Exception as e:
            logger.error(f"Error getting competitive group {group_id}: {str(e)}")
            return None
    
    def get_all_competitive_groups(self) -> List[CompetitiveGroup]:
        """Get all active competitive groups"""
        try:
            with self.db_manager.get_session() as session:
                groups = session.query(CompetitiveGroup).filter(
                    CompetitiveGroup.is_active == True
                ).order_by(CompetitiveGroup.updated_at.desc()).all()
                
                # Load competitors for each group
                for group in groups:
                    competitors = session.query(Competitor).filter(
                        Competitor.competitive_group_id == group.id,
                        Competitor.is_active == True
                    ).order_by(Competitor.priority).all()
                    group.active_competitors = competitors
                
                return groups
                
        except Exception as e:
            logger.error(f"Error getting competitive groups: {str(e)}")
            return []
    
    def remove_competitor(self, group_id: int, competitor_asin: str) -> bool:
        """Remove competitor from group (soft delete)"""
        try:
            with self.db_manager.get_session() as session:
                competitor = session.query(Competitor).filter(
                    Competitor.competitive_group_id == group_id,
                    Competitor.asin == competitor_asin
                ).first()
                
                if competitor:
                    competitor.is_active = False
                    session.commit()
                    
                    # Clear related cache
                    self._invalidate_group_cache(group_id)
                    
                    logger.info(f"Removed competitor {competitor_asin} from group {group_id}")
                    return True
                else:
                    logger.warning(f"Competitor {competitor_asin} not found in group {group_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing competitor: {str(e)}")
            return False
    
    def update_group(self, group_id: int, **kwargs) -> bool:
        """Update competitive group information"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(CompetitiveGroup).filter(
                    CompetitiveGroup.id == group_id
                ).first()
                
                if not group:
                    return False
                
                # Update allowed fields
                allowed_fields = ['name', 'description', 'main_product_asin']
                for field, value in kwargs.items():
                    if field in allowed_fields and hasattr(group, field):
                        setattr(group, field, value)
                
                group.updated_at = datetime.utcnow()
                session.commit()
                
                # Clear related cache
                self._invalidate_group_cache(group_id)
                
                logger.info(f"Updated competitive group {group_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating competitive group {group_id}: {str(e)}")
            return False
    
    def delete_group(self, group_id: int) -> bool:
        """Delete competitive group (soft delete)"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(CompetitiveGroup).filter(
                    CompetitiveGroup.id == group_id
                ).first()
                
                if group:
                    group.is_active = False
                    
                    # Also deactivate all competitors
                    session.query(Competitor).filter(
                        Competitor.competitive_group_id == group_id
                    ).update({"is_active": False})
                    
                    session.commit()
                    
                    # Clear related cache
                    self._invalidate_group_cache(group_id)
                    
                    logger.info(f"Deleted competitive group {group_id}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting competitive group {group_id}: {str(e)}")
            return False
    
    def get_group_asins(self, group_id: int) -> Dict[str, List[str]]:
        """Get all ASINs (main + competitors) for a group"""
        try:
            group = self.get_competitive_group(group_id)
            if not group:
                return {"main": [], "competitors": []}
            
            competitor_asins = [comp.asin for comp in group.active_competitors]
            
            return {
                "main": [group.main_product_asin],
                "competitors": competitor_asins,
                "all": [group.main_product_asin] + competitor_asins
            }
            
        except Exception as e:
            logger.error(f"Error getting group ASINs for {group_id}: {str(e)}")
            return {"main": [], "competitors": []}
    
    def _invalidate_group_cache(self, group_id: int):
        """Invalidate cache related to competitive group"""
        try:
            # Clear group-specific cache
            cache.delete_pattern(f"competitive:group:{group_id}:*")
            cache.delete_pattern(f"competitive:analysis:{group_id}:*")
            
            # Clear general competitive cache
            cache.delete("competitive:groups:all")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for group {group_id}: {str(e)}")
    
    def ensure_competitors_tracked(self, group_id: int) -> Dict[str, bool]:
        """Ensure all competitors in group are being tracked"""
        try:
            from config.config import AMAZON_ASINS
            
            asins_data = self.get_group_asins(group_id)
            all_asins = asins_data["all"]
            
            # Check which ASINs are not in the tracking list
            not_tracked = [asin for asin in all_asins if asin not in AMAZON_ASINS]
            
            if not_tracked:
                logger.warning(f"ASINs not in tracking list: {not_tracked}")
                logger.info("Consider adding them to AMAZON_ASINS in config.py")
            
            # Return tracking status for each ASIN
            tracking_status = {}
            for asin in all_asins:
                tracking_status[asin] = asin in AMAZON_ASINS
            
            return tracking_status
            
        except Exception as e:
            logger.error(f"Error checking tracking status for group {group_id}: {str(e)}")
            return {}