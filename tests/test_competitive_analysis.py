#!/usr/bin/env python3
"""
Unit tests for competitive analysis engine
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.competitive.analyzer import CompetitiveAnalyzer, CompetitiveMetrics
from src.competitive.llm_reporter import LLMReporter
from src.competitive.manager import CompetitiveManager

class TestCompetitiveMetrics:
    """Test competitive metrics data structure"""
    
    def test_competitive_metrics_creation(self):
        """Test creating CompetitiveMetrics object"""
        metrics = CompetitiveMetrics(
            asin="B07R7RMQF5",
            title="Test Product",
            price=29.99,
            rating=4.5,
            review_count=1000,
            bsr_data={"Sports & Outdoors": 100},
            bullet_points=["Feature 1", "Feature 2"],
            key_features={"materials": ["cotton"], "colors": ["blue"]},
            availability="In Stock"
        )
        
        assert metrics.asin == "B07R7RMQF5"
        assert metrics.price == 29.99
        assert metrics.rating == 4.5
        assert "Sports & Outdoors" in metrics.bsr_data

class TestCompetitiveAnalyzer:
    """Test competitive analysis engine"""
    
    @pytest.fixture
    def analyzer(self):
        with patch('src.competitive.analyzer.CompetitiveManager'), \
             patch('src.competitive.analyzer.ProductTracker'):
            return CompetitiveAnalyzer()
    
    @pytest.fixture
    def sample_main_product(self):
        return CompetitiveMetrics(
            asin="B07R7RMQF5",
            title="Main Product",
            price=34.99,
            rating=4.7,
            review_count=5000,
            bsr_data={"Sports & Outdoors": 150, "Yoga Mats": 5},
            bullet_points=["High quality", "Durable"],
            key_features={"materials": ["eco-friendly"], "dimensions": ["72x24 inches"]},
            availability="In Stock"
        )
    
    @pytest.fixture
    def sample_competitors(self):
        return [
            CompetitiveMetrics(
                asin="B092XMWXK7",
                title="Competitor A",
                price=39.99,
                rating=4.5,
                review_count=3000,
                bsr_data={"Sports & Outdoors": 200, "Yoga Mats": 8},
                bullet_points=["Premium quality"],
                key_features={"materials": ["rubber"], "colors": ["black"]},
                availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="B0BVY8K28Q", 
                title="Competitor B",
                price=24.99,
                rating=4.2,
                review_count=8000,
                bsr_data={"Sports & Outdoors": 300, "Yoga Mats": 15},
                bullet_points=["Budget option"],
                key_features={"materials": ["foam"], "colors": ["blue", "red"]},
                availability="In Stock"
            )
        ]
    
    def test_analyze_price_positioning(self, analyzer, sample_main_product, sample_competitors):
        """Test price positioning analysis"""
        result = analyzer._analyze_price_positioning(sample_main_product, sample_competitors)
        
        assert "main_product_price" in result
        assert "price_position" in result
        assert "market_price_range" in result
        assert "competitors" in result
        
        assert result["main_product_price"] == 34.99
        assert result["price_position"] in ["lowest", "middle", "highest"]
        
        # Check market price range calculation
        price_range = result["market_price_range"]
        assert price_range["min"] == 24.99  # Lowest competitor price
        assert price_range["max"] == 39.99  # Highest competitor price
        assert 24.99 <= price_range["average"] <= 39.99
    
    def test_analyze_bsr_positioning(self, analyzer, sample_main_product, sample_competitors):
        """Test BSR positioning analysis"""
        result = analyzer._analyze_bsr_positioning(sample_main_product, sample_competitors)
        
        assert "Sports & Outdoors" in result
        assert "Yoga Mats" in result
        
        # Check Sports & Outdoors category analysis
        sports_analysis = result["Sports & Outdoors"]
        assert sports_analysis["main_product_rank"] == 150
        assert sports_analysis["position"] in ["best", "worst", "middle"]
        assert "competitors" in sports_analysis
        assert "rank_statistics" in sports_analysis
    
    def test_analyze_rating_positioning(self, analyzer, sample_main_product, sample_competitors):
        """Test rating positioning analysis"""
        result = analyzer._analyze_rating_positioning(sample_main_product, sample_competitors)
        
        assert "main_product" in result
        assert "competitors" in result
        assert "rating_statistics" in result
        assert "review_statistics" in result
        
        # Check main product data
        main_data = result["main_product"]
        assert main_data["rating"] == 4.7
        assert main_data["review_count"] == 5000
        
        # Check rating statistics
        rating_stats = result["rating_statistics"]
        assert "min" in rating_stats
        assert "max" in rating_stats
        assert "average" in rating_stats
        assert "main_product_position" in rating_stats
    
    def test_generate_competitive_summary(self, analyzer, sample_main_product, sample_competitors):
        """Test competitive summary generation"""
        result = analyzer._generate_competitive_summary(sample_main_product, sample_competitors)
        
        assert "competitive_scores" in result
        assert "position_summary" in result
        assert "total_competitors" in result
        
        # Check competitive scores
        scores = result["competitive_scores"]
        assert "price_competitiveness" in scores
        assert "quality_competitiveness" in scores
        assert "overall_competitiveness" in scores
        
        # All scores should be between 0 and 100
        for score_name, score_value in scores.items():
            assert 0 <= score_value <= 100, f"{score_name} score {score_value} not in valid range"
        
        # Check position summary
        positions = result["position_summary"]
        assert "price_position" in positions
        assert "quality_position" in positions
        assert "overall_position" in positions
    
    def test_metrics_to_dict(self, analyzer, sample_main_product):
        """Test metrics conversion to dictionary"""
        result = analyzer._metrics_to_dict(sample_main_product)
        
        assert result["asin"] == "B07R7RMQF5"
        assert result["title"] == "Main Product"
        assert result["price"] == 34.99
        assert result["rating"] == 4.7
        assert result["review_count"] == 5000
        assert result["bsr_data"] == {"Sports & Outdoors": 150, "Yoga Mats": 5}

class TestLLMReporter:
    """Test LLM report generation"""
    
    @pytest.fixture
    def llm_reporter(self):
        return LLMReporter()
    
    @pytest.fixture
    def sample_analysis_data(self):
        return {
            "main_product": {
                "asin": "B07R7RMQF5",
                "title": "Test Product",
                "price": 34.99,
                "rating": 4.7,
                "review_count": 5000
            },
            "competitors": [
                {
                    "asin": "B092XMWXK7",
                    "title": "Competitor A",
                    "price": 39.99,
                    "rating": 4.5,
                    "review_count": 3000
                }
            ],
            "competitive_summary": {
                "competitive_scores": {
                    "price_competitiveness": 75.0,
                    "quality_competitiveness": 94.0,
                    "overall_competitiveness": 84.5
                },
                "position_summary": {
                    "price_position": "competitive",
                    "quality_position": "superior",
                    "overall_position": "strong"
                },
                "total_competitors": 1
            },
            "price_analysis": {
                "price_position": "competitive",
                "price_advantage": True
            },
            "rating_analysis": {
                "quality_advantage": True
            },
            "feature_analysis": {
                "unique_to_main": {"materials": ["eco-friendly"]},
                "missing_from_main": {"colors": ["red"]}
            }
        }
    
    def test_generate_fallback_report(self, llm_reporter, sample_analysis_data):
        """Test fallback report generation"""
        result = llm_reporter._generate_fallback_report(sample_analysis_data)
        
        assert "executive_summary" in result
        assert "competitive_positioning" in result
        assert "strengths_weaknesses" in result
        assert "feature_differentiation" in result
        assert "strategic_recommendations" in result
        assert "market_insights" in result
        assert "report_metadata" in result
        
        # Check report metadata
        metadata = result["report_metadata"]
        assert metadata["llm_enabled"] is False
        assert metadata["model_used"] == "structured_analysis"
        assert "generated_at" in metadata
    
    def test_generate_executive_summary(self, llm_reporter, sample_analysis_data):
        """Test executive summary generation"""
        competitive_summary = sample_analysis_data["competitive_summary"]
        main_product = sample_analysis_data["main_product"]
        
        summary = llm_reporter._generate_executive_summary(competitive_summary, main_product)
        
        assert isinstance(summary, str)
        assert len(summary) > 50  # Should be meaningful summary
        assert "Test Product" in summary or "competitive" in summary.lower()
    
    def test_identify_strengths_weaknesses(self, llm_reporter, sample_analysis_data):
        """Test SWOT analysis generation"""
        result = llm_reporter._identify_strengths_weaknesses(sample_analysis_data)
        
        assert "strengths" in result
        assert "weaknesses" in result
        assert "opportunities" in result
        assert "threats" in result
        
        # Should identify price advantage as strength
        strengths = result["strengths"]
        assert any("price" in strength.lower() or "competitive" in strength.lower() 
                  for strength in strengths)
    
    def test_generate_recommendations(self, llm_reporter, sample_analysis_data):
        """Test strategic recommendations generation"""
        recommendations = llm_reporter._generate_recommendations(sample_analysis_data)
        
        assert isinstance(recommendations, list)
        
        if recommendations:  # May be empty based on analysis
            for rec in recommendations:
                assert "category" in rec
                assert "priority" in rec
                assert "action" in rec
                assert "rationale" in rec
                assert "expected_impact" in rec
                assert rec["priority"] in ["high", "medium", "low"]
    
    def test_create_analysis_prompt(self, llm_reporter, sample_analysis_data):
        """Test OpenAI prompt creation"""
        prompt = llm_reporter._create_analysis_prompt(sample_analysis_data)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial prompt
        assert "MAIN PRODUCT" in prompt
        assert "COMPETITORS" in prompt
        assert "B07R7RMQF5" in prompt  # Should include ASIN

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.competitive", "--cov=src.auth", "--cov-report=html"])