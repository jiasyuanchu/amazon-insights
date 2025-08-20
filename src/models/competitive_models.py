from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.product_models import Base

class CompetitiveGroup(Base):
    __tablename__ = 'competitive_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)  # e.g., "Yoga Mats Competitive Analysis"
    description = Column(Text)
    main_product_asin = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    competitors = relationship("Competitor", back_populates="group")
    analysis_reports = relationship("CompetitiveAnalysisReport", back_populates="group")

class Competitor(Base):
    __tablename__ = 'competitors'
    
    id = Column(Integer, primary_key=True)
    competitive_group_id = Column(Integer, ForeignKey('competitive_groups.id'), nullable=False)
    asin = Column(String(20), nullable=False, index=True)
    competitor_name = Column(String(200))  # Custom name for the competitor
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    group = relationship("CompetitiveGroup", back_populates="competitors")

class ProductFeatures(Base):
    __tablename__ = 'product_features'
    
    id = Column(Integer, primary_key=True)
    asin = Column(String(20), nullable=False, index=True)
    bullet_points = Column(JSON)  # List of product bullet points
    product_description = Column(Text)
    key_features = Column(JSON)  # Extracted key features
    feature_categories = Column(JSON)  # Categorized features
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
class CompetitiveAnalysisReport(Base):
    __tablename__ = 'competitive_analysis_reports'
    
    id = Column(Integer, primary_key=True)
    competitive_group_id = Column(Integer, ForeignKey('competitive_groups.id'), nullable=False)
    
    # Analysis data
    price_analysis = Column(JSON)  # Price comparison data
    bsr_analysis = Column(JSON)    # BSR ranking analysis
    rating_analysis = Column(JSON) # Rating comparison
    feature_analysis = Column(JSON) # Feature comparison
    
    # LLM generated content
    positioning_report = Column(Text)  # Generated competitive positioning report
    recommendations = Column(JSON)     # Action recommendations
    strengths_weaknesses = Column(JSON) # SWOT-like analysis
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    llm_model_used = Column(String(100))
    analysis_version = Column(String(50), default="1.0")
    
    # Relationship
    group = relationship("CompetitiveGroup", back_populates="analysis_reports")

class CompetitiveTrend(Base):
    __tablename__ = 'competitive_trends'
    
    id = Column(Integer, primary_key=True)
    competitive_group_id = Column(Integer, ForeignKey('competitive_groups.id'), nullable=False)
    
    # Trend data
    date = Column(DateTime, nullable=False, index=True)
    main_product_data = Column(JSON)    # Main product metrics
    competitors_data = Column(JSON)     # All competitors metrics
    
    # Calculated metrics
    price_position = Column(String(20))     # "lowest", "middle", "highest"
    bsr_position = Column(String(20))       # "best", "middle", "worst"
    rating_position = Column(String(20))    # "highest", "middle", "lowest"
    
    # Competitive scores (0-100)
    overall_competitiveness = Column(Float)
    price_competitiveness = Column(Float)
    quality_competitiveness = Column(Float)  # Based on ratings
    popularity_competitiveness = Column(Float)  # Based on BSR