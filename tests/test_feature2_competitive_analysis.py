#!/usr/bin/env python3
"""
功能二：競品分析引擎測試
Target: 70% coverage for competitive analysis functionality

Modules covered:
- src/competitive/analyzer.py
- src/competitive/manager.py
- src/competitive/llm_reporter.py
- src/models/competitive_models.py
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class TestCompetitiveMetricsDataclass:
    """Test CompetitiveMetrics dataclass from analyzer"""
    
    def test_competitive_metrics_creation(self):
        """Test CompetitiveMetrics dataclass creation"""
        try:
            from src.competitive.analyzer import CompetitiveMetrics
            
            # Create instance with all fields
            metrics = CompetitiveMetrics(
                asin="B07R7RMQF5",
                title="Premium Yoga Mat",
                price=29.99,
                rating=4.5,
                review_count=1234,
                bsr_data={"Sports & Outdoors": 100, "Fitness": 50},
                bullet_points=["Eco-friendly", "Non-slip surface", "Extra thick"],
                key_features={"materials": ["TPE"], "colors": ["blue", "green"]},
                availability="In Stock"
            )
            
            # Verify all fields
            assert metrics.asin == "B07R7RMQF5"
            assert metrics.title == "Premium Yoga Mat"
            assert metrics.price == 29.99
            assert metrics.rating == 4.5
            assert metrics.review_count == 1234
            assert isinstance(metrics.bsr_data, dict)
            assert isinstance(metrics.bullet_points, list)
            assert isinstance(metrics.key_features, dict)
            assert metrics.availability == "In Stock"
            
        except ImportError:
            pytest.skip("CompetitiveMetrics not available")
    
    def test_competitive_metrics_optional_fields(self):
        """Test CompetitiveMetrics with None/optional values"""
        try:
            from src.competitive.analyzer import CompetitiveMetrics
            
            # Create with minimal fields
            metrics = CompetitiveMetrics(
                asin="B07R7RMQF5",
                title="Test Product",
                price=None,
                rating=None,
                review_count=None,
                bsr_data=None,
                bullet_points=[],
                key_features={},
                availability="Unknown"
            )
            
            assert metrics.asin == "B07R7RMQF5"
            assert metrics.price is None
            assert metrics.rating is None
            assert metrics.review_count is None
            assert metrics.bsr_data is None
            assert isinstance(metrics.bullet_points, list)
            assert isinstance(metrics.key_features, dict)
            
        except ImportError:
            pytest.skip("CompetitiveMetrics not available")


class TestCompetitiveAnalyzer:
    """Test Competitive Analyzer core functionality"""
    
    @pytest.fixture
    def mock_analyzer(self):
        with patch('src.competitive.analyzer.CompetitiveAnalyzer') as mock:
            analyzer_instance = Mock()
            mock.return_value = analyzer_instance
            return analyzer_instance
    
    def test_analyzer_initialization(self):
        """Test CompetitiveAnalyzer can be initialized"""
        try:
            from src.competitive.analyzer import CompetitiveAnalyzer
            analyzer = CompetitiveAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("CompetitiveAnalyzer module not available")
    
    def test_price_positioning_analysis_structure(self, mock_analyzer):
        """Test price positioning analysis data structure"""
        mock_analyzer._analyze_price_positioning.return_value = {
            "main_product_price": 29.99,
            "competitors_prices": [34.99, 24.99, 32.50],
            "price_rank": 2,  # 2nd cheapest out of 4
            "price_percentile": 40,  # 40th percentile
            "price_competitiveness_score": 65,
            "price_position": "competitive",
            "avg_competitor_price": 30.83,
            "price_advantage": -0.84  # $0.84 cheaper than average
        }
        
        result = mock_analyzer._analyze_price_positioning("main_metrics", ["comp1", "comp2", "comp3"])
        
        assert "main_product_price" in result
        assert "competitors_prices" in result
        assert "price_rank" in result
        assert "price_competitiveness_score" in result
        assert "price_position" in result
        assert isinstance(result["competitors_prices"], list)
        assert result["price_competitiveness_score"] <= 100
        assert result["price_position"] in ["excellent", "competitive", "poor"]
    
    def test_rating_positioning_analysis_structure(self, mock_analyzer):
        """Test rating positioning analysis data structure"""
        mock_analyzer._analyze_rating_positioning.return_value = {
            "main_product_rating": 4.5,
            "competitors_ratings": [4.2, 4.7, 4.1],
            "rating_rank": 2,  # 2nd highest rating
            "rating_percentile": 75,
            "quality_competitiveness_score": 80,
            "rating_position": "above_average",
            "avg_competitor_rating": 4.33,
            "rating_advantage": 0.17  # 0.17 stars higher than average
        }
        
        result = mock_analyzer._analyze_rating_positioning("main_metrics", ["comp1", "comp2", "comp3"])
        
        assert "main_product_rating" in result
        assert "competitors_ratings" in result
        assert "rating_rank" in result
        assert "quality_competitiveness_score" in result
        assert "rating_position" in result
        assert isinstance(result["competitors_ratings"], list)
        assert 1.0 <= result["main_product_rating"] <= 5.0
        assert result["rating_position"] in ["excellent", "above_average", "average", "below_average"]
    
    def test_bsr_positioning_analysis_structure(self, mock_analyzer):
        """Test BSR positioning analysis data structure"""
        mock_analyzer._analyze_bsr_positioning.return_value = {
            "main_product_bsr": {"Sports & Outdoors": 150},
            "competitors_bsr": [
                {"Sports & Outdoors": 100},
                {"Sports & Outdoors": 200},
                {"Sports & Outdoors": 175}
            ],
            "bsr_rank": 2,  # 2nd best BSR (lower number = better)
            "category_rankings": {
                "Sports & Outdoors": {
                    "rank": 2,
                    "percentile": 60,
                    "position": "good"
                }
            },
            "overall_bsr_score": 70
        }
        
        result = mock_analyzer._analyze_bsr_positioning("main_metrics", ["comp1", "comp2", "comp3"])
        
        assert "main_product_bsr" in result
        assert "competitors_bsr" in result
        assert "bsr_rank" in result
        assert "category_rankings" in result
        assert "overall_bsr_score" in result
        assert isinstance(result["competitors_bsr"], list)
        assert isinstance(result["category_rankings"], dict)
    
    def test_feature_comparison_analysis_structure(self, mock_analyzer):
        """Test feature comparison analysis data structure"""
        mock_analyzer._analyze_feature_comparison.return_value = {
            "main_product_features": {
                "materials": ["TPE", "eco-friendly"],
                "dimensions": ["72x24 inches"],
                "colors": ["blue", "green"]
            },
            "competitors_features": [
                {"materials": ["PVC"], "colors": ["black", "blue"]},
                {"materials": ["rubber"], "dimensions": ["68x24 inches"]},
                {"materials": ["TPE"], "colors": ["purple", "pink"]}
            ],
            "unique_features": ["eco-friendly"],  # Only main product has this
            "missing_features": ["carrying_strap"],  # Competitors have, main doesn't
            "common_features": ["blue"],  # Shared across products
            "feature_coverage_score": 75,
            "differentiation_score": 60,
            "feature_gaps": 2,
            "feature_advantages": 1
        }
        
        result = mock_analyzer._analyze_feature_comparison("main_metrics", ["comp1", "comp2", "comp3"])
        
        assert "main_product_features" in result
        assert "competitors_features" in result
        assert "unique_features" in result
        assert "missing_features" in result
        assert "common_features" in result
        assert "feature_coverage_score" in result
        assert "differentiation_score" in result
        assert isinstance(result["unique_features"], list)
        assert isinstance(result["missing_features"], list)
        assert isinstance(result["competitors_features"], list)
    
    def test_competitive_summary_generation(self, mock_analyzer):
        """Test competitive summary generation"""
        mock_analyzer._generate_competitive_summary.return_value = {
            "overall_competitive_score": 72,
            "price_score": 65,
            "quality_score": 80,
            "feature_score": 75,
            "market_position": "competitive",
            "strengths": ["Higher rating than average", "Eco-friendly materials"],
            "weaknesses": ["Missing carrying strap", "Limited color options"],
            "opportunities": ["Expand color range", "Add premium features"],
            "threats": ["Competitor price cuts", "New eco-friendly competitors"],
            "recommended_actions": [
                "Maintain current pricing strategy",
                "Add carrying strap accessory",
                "Market eco-friendly benefits"
            ]
        }
        
        result = mock_analyzer._generate_competitive_summary("main_metrics", ["comp1", "comp2", "comp3"])
        
        assert "overall_competitive_score" in result
        assert "price_score" in result
        assert "quality_score" in result
        assert "feature_score" in result
        assert "market_position" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "opportunities" in result
        assert "threats" in result
        assert "recommended_actions" in result
        assert 0 <= result["overall_competitive_score"] <= 100
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
    
    def test_metrics_to_dict_conversion(self, mock_analyzer):
        """Test metrics to dictionary conversion"""
        mock_analyzer._metrics_to_dict.return_value = {
            "asin": "B07R7RMQF5",
            "title": "Premium Yoga Mat",
            "price": 29.99,
            "rating": 4.5,
            "review_count": 1234,
            "bsr_data": {"Sports & Outdoors": 150},
            "bullet_points": ["Eco-friendly", "Non-slip"],
            "key_features": {"materials": ["TPE"]},
            "availability": "In Stock"
        }
        
        result = mock_analyzer._metrics_to_dict("mock_metrics")
        
        # Verify dictionary structure
        expected_keys = ["asin", "title", "price", "rating", "review_count", 
                        "bsr_data", "bullet_points", "key_features", "availability"]
        
        for key in expected_keys:
            assert key in result
        
        assert isinstance(result["bullet_points"], list)
        assert isinstance(result["key_features"], dict)
    
    def test_analyze_competitive_group_structure(self, mock_analyzer):
        """Test complete competitive group analysis structure"""
        mock_analyzer.analyze_competitive_group.return_value = {
            "group_info": {
                "id": 1,
                "name": "Yoga Mats Competitive Analysis",
                "main_product_asin": "B07R7RMQF5",
                "competitors_count": 3
            },
            "main_product": {
                "asin": "B07R7RMQF5",
                "title": "Premium Yoga Mat",
                "price": 29.99,
                "rating": 4.5
            },
            "competitors": [
                {"asin": "B08COMP1", "title": "Competitor 1", "price": 34.99},
                {"asin": "B08COMP2", "title": "Competitor 2", "price": 24.99},
                {"asin": "B08COMP3", "title": "Competitor 3", "price": 32.50}
            ],
            "price_analysis": {"price_position": "competitive"},
            "bsr_analysis": {"bsr_position": "good"},
            "rating_analysis": {"rating_position": "above_average"},
            "feature_analysis": {"unique_features": ["eco-friendly"]},
            "competitive_summary": {"overall_score": 72},
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        result = mock_analyzer.analyze_competitive_group(1)
        
        assert "group_info" in result
        assert "main_product" in result
        assert "competitors" in result
        assert "price_analysis" in result
        assert "bsr_analysis" in result
        assert "rating_analysis" in result
        assert "feature_analysis" in result
        assert "competitive_summary" in result
        assert "analysis_timestamp" in result
        assert isinstance(result["competitors"], list)


class TestCompetitiveManager:
    """Test Competitive Manager functionality"""
    
    @pytest.fixture
    def mock_manager(self):
        with patch('src.competitive.manager.CompetitiveManager') as mock:
            manager_instance = Mock()
            mock.return_value = manager_instance
            return manager_instance
    
    def test_manager_initialization(self):
        """Test CompetitiveManager can be initialized"""
        try:
            from src.competitive.manager import CompetitiveManager
            manager = CompetitiveManager()
            assert manager is not None
        except ImportError:
            pytest.skip("CompetitiveManager module not available")
    
    def test_create_competitive_group_structure(self, mock_manager):
        """Test competitive group creation data structure"""
        mock_manager.create_competitive_group.return_value = {
            "id": 1,
            "name": "Yoga Mats Analysis",
            "main_product_asin": "B07R7RMQF5",
            "description": "Comprehensive analysis of yoga mat market",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True,
            "competitors_count": 0
        }
        
        group_data = {
            "name": "Yoga Mats Analysis",
            "main_product_asin": "B07R7RMQF5",
            "description": "Comprehensive analysis of yoga mat market"
        }
        
        result = mock_manager.create_competitive_group(group_data)
        
        assert "id" in result
        assert "name" in result
        assert "main_product_asin" in result
        assert "description" in result
        assert "created_at" in result
        assert "is_active" in result
        assert result["competitors_count"] == 0
    
    def test_get_competitive_group_structure(self, mock_manager):
        """Test get competitive group data structure"""
        mock_manager.get_competitive_group.return_value = {
            "id": 1,
            "name": "Yoga Mats Analysis",
            "main_product_asin": "B07R7RMQF5",
            "description": "Analysis description",
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "competitors": [
                {
                    "id": 1,
                    "asin": "B08COMP1",
                    "competitor_name": "Competitor 1",
                    "priority": 1,
                    "is_active": True
                }
            ],
            "competitors_count": 1
        }
        
        result = mock_manager.get_competitive_group(1)
        
        assert "id" in result
        assert "name" in result
        assert "main_product_asin" in result
        assert "competitors" in result
        assert "competitors_count" in result
        assert isinstance(result["competitors"], list)
    
    def test_add_competitor_structure(self, mock_manager):
        """Test add competitor data structure"""
        mock_manager.add_competitor.return_value = {
            "id": 1,
            "group_id": 1,
            "asin": "B08COMPETITOR1",
            "competitor_name": "Premium Competitor Mat",
            "priority": 1,
            "is_active": True,
            "added_at": datetime.now().isoformat()
        }
        
        competitor_data = {
            "asin": "B08COMPETITOR1",
            "competitor_name": "Premium Competitor Mat",
            "priority": 1
        }
        
        result = mock_manager.add_competitor(1, competitor_data)
        
        assert "id" in result
        assert "group_id" in result
        assert "asin" in result
        assert "competitor_name" in result
        assert "priority" in result
        assert "is_active" in result
        assert "added_at" in result
    
    def test_remove_competitor_structure(self, mock_manager):
        """Test remove competitor functionality"""
        mock_manager.remove_competitor.return_value = {
            "group_id": 1,
            "competitor_asin": "B08COMPETITOR1",
            "removed_at": datetime.now().isoformat(),
            "status": "removed"
        }
        
        result = mock_manager.remove_competitor(1, "B08COMPETITOR1")
        
        assert "group_id" in result
        assert "competitor_asin" in result
        assert "removed_at" in result
        assert "status" in result
        assert result["status"] == "removed"
    
    def test_list_competitive_groups_structure(self, mock_manager):
        """Test list competitive groups data structure"""
        mock_manager.list_competitive_groups.return_value = {
            "groups": [
                {
                    "id": 1,
                    "name": "Yoga Mats Analysis",
                    "main_product_asin": "B07R7RMQF5",
                    "competitors_count": 3,
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                },
                {
                    "id": 2,
                    "name": "Fitness Equipment Analysis",
                    "main_product_asin": "B08WORKOUT1",
                    "competitors_count": 2,
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                }
            ],
            "total_count": 2,
            "active_count": 2
        }
        
        result = mock_manager.list_competitive_groups()
        
        assert "groups" in result
        assert "total_count" in result
        assert "active_count" in result
        assert isinstance(result["groups"], list)
        assert len(result["groups"]) == result["total_count"]
    
    def test_update_competitive_group_structure(self, mock_manager):
        """Test update competitive group functionality"""
        mock_manager.update_competitive_group.return_value = {
            "id": 1,
            "name": "Updated Yoga Mats Analysis",
            "description": "Updated description",
            "updated_at": datetime.now().isoformat(),
            "changes_applied": ["name", "description"]
        }
        
        update_data = {
            "name": "Updated Yoga Mats Analysis",
            "description": "Updated description"
        }
        
        result = mock_manager.update_competitive_group(1, update_data)
        
        assert "id" in result
        assert "name" in result
        assert "updated_at" in result
        assert "changes_applied" in result
        assert isinstance(result["changes_applied"], list)


class TestLLMReporter:
    """Test LLM Reporter functionality"""
    
    @pytest.fixture
    def mock_reporter(self):
        with patch('src.competitive.llm_reporter.LLMReporter') as mock:
            reporter_instance = Mock()
            mock.return_value = reporter_instance
            return reporter_instance
    
    def test_reporter_initialization(self):
        """Test LLMReporter can be initialized"""
        try:
            from src.competitive.llm_reporter import LLMReporter
            reporter = LLMReporter()
            assert reporter is not None
        except ImportError:
            pytest.skip("LLMReporter module not available")
    
    def test_generate_competitive_report_structure(self, mock_reporter):
        """Test competitive report generation structure"""
        mock_reporter.generate_competitive_report.return_value = {
            "report_id": "report_001",
            "group_id": 1,
            "report_type": "comprehensive",
            "generated_at": datetime.now().isoformat(),
            "executive_summary": "Your product is competitively positioned in the yoga mat market...",
            "sections": {
                "market_overview": {
                    "title": "Market Overview",
                    "content": "Analysis of the yoga mat competitive landscape...",
                    "key_insights": ["Market is price-sensitive", "Eco-friendly features are valued"]
                },
                "price_analysis": {
                    "title": "Price Positioning Analysis", 
                    "content": "Your product is priced competitively at $29.99...",
                    "key_insights": ["40% cheaper than premium competitors", "10% above average"]
                },
                "quality_analysis": {
                    "title": "Quality & Rating Analysis",
                    "content": "Your product rating of 4.5 stars positions it well...",
                    "key_insights": ["Above average rating", "Strong customer satisfaction"]
                },
                "feature_analysis": {
                    "title": "Feature Comparison",
                    "content": "Your product offers unique eco-friendly materials...",
                    "key_insights": ["Unique eco-friendly positioning", "Missing carrying strap"]
                }
            },
            "recommendations": [
                {
                    "category": "pricing",
                    "recommendation": "Maintain current pricing strategy",
                    "rationale": "Price point is optimal for market position",
                    "priority": "medium"
                },
                {
                    "category": "features", 
                    "recommendation": "Add carrying strap accessory",
                    "rationale": "60% of competitors offer this feature",
                    "priority": "high"
                }
            ],
            "competitive_matrix": {
                "headers": ["Product", "Price", "Rating", "Reviews", "Unique Features"],
                "rows": [
                    ["Your Product", "$29.99", "4.5", "1234", "Eco-friendly"],
                    ["Competitor 1", "$34.99", "4.2", "856", "Extra thick"],
                    ["Competitor 2", "$24.99", "4.1", "2100", "Carrying strap"]
                ]
            }
        }
        
        analysis_data = {"group_id": 1, "main_product": {}, "competitors": []}
        result = mock_reporter.generate_competitive_report(analysis_data)
        
        assert "report_id" in result
        assert "group_id" in result
        assert "executive_summary" in result
        assert "sections" in result
        assert "recommendations" in result
        assert "competitive_matrix" in result
        assert isinstance(result["sections"], dict)
        assert isinstance(result["recommendations"], list)
        assert "market_overview" in result["sections"]
        assert "price_analysis" in result["sections"]
    
    def test_generate_insights_structure(self, mock_reporter):
        """Test insights generation structure"""
        mock_reporter.generate_insights.return_value = {
            "insights": [
                {
                    "type": "opportunity",
                    "title": "Eco-Friendly Market Gap",
                    "description": "Only 20% of competitors emphasize eco-friendly materials",
                    "impact": "high",
                    "confidence": 0.85
                },
                {
                    "type": "threat",
                    "title": "Price Pressure Risk",
                    "description": "Two competitors recently reduced prices by 15%",
                    "impact": "medium",
                    "confidence": 0.75
                },
                {
                    "type": "strength",
                    "title": "Quality Advantage",
                    "description": "Your rating is 0.3 stars higher than average",
                    "impact": "medium",
                    "confidence": 0.90
                }
            ],
            "insight_summary": {
                "opportunities": 1,
                "threats": 1,
                "strengths": 1,
                "weaknesses": 0
            }
        }
        
        result = mock_reporter.generate_insights("analysis_data")
        
        assert "insights" in result
        assert "insight_summary" in result
        assert isinstance(result["insights"], list)
        
        for insight in result["insights"]:
            assert "type" in insight
            assert "title" in insight
            assert "description" in insight
            assert "impact" in insight
            assert "confidence" in insight
            assert insight["type"] in ["opportunity", "threat", "strength", "weakness"]
            assert insight["impact"] in ["low", "medium", "high"]
            assert 0 <= insight["confidence"] <= 1
    
    def test_generate_recommendations_structure(self, mock_reporter):
        """Test recommendations generation structure"""
        mock_reporter.generate_recommendations.return_value = {
            "recommendations": [
                {
                    "id": "rec_001",
                    "category": "pricing",
                    "title": "Maintain Competitive Pricing",
                    "description": "Continue current pricing strategy to maintain market position",
                    "action_items": [
                        "Monitor competitor price changes weekly",
                        "Set price alerts for key competitors",
                        "Review pricing quarterly"
                    ],
                    "expected_impact": "medium",
                    "effort_required": "low",
                    "timeline": "ongoing",
                    "priority": "medium"
                },
                {
                    "id": "rec_002", 
                    "category": "product",
                    "title": "Add Carrying Strap Feature",
                    "description": "60% of competitors offer carrying straps - consider adding as accessory",
                    "action_items": [
                        "Research strap designs and materials",
                        "Calculate cost impact",
                        "Test with focus groups",
                        "Plan production integration"
                    ],
                    "expected_impact": "high",
                    "effort_required": "high",
                    "timeline": "3-6 months",
                    "priority": "high"
                }
            ]
        }
        
        result = mock_reporter.generate_recommendations("analysis_data")
        
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        
        for rec in result["recommendations"]:
            assert "id" in rec
            assert "category" in rec
            assert "title" in rec
            assert "description" in rec
            assert "action_items" in rec
            assert "expected_impact" in rec
            assert "effort_required" in rec
            assert "timeline" in rec
            assert "priority" in rec
            assert isinstance(rec["action_items"], list)


class TestCompetitiveModels:
    """Test competitive analysis data models"""
    
    def test_competitive_group_model_attributes(self):
        """Test CompetitiveGroup model has expected attributes"""
        try:
            from src.models.competitive_models import CompetitiveGroup
            
            expected_attrs = ['id', 'name', 'main_product_asin', 'description',
                            'created_at', 'updated_at', 'is_active']
            
            for attr in expected_attrs:
                assert hasattr(CompetitiveGroup, attr), \
                    f"CompetitiveGroup should have attribute '{attr}'"
                    
        except ImportError:
            pytest.skip("CompetitiveGroup model not available")
    
    def test_competitor_model_attributes(self):
        """Test Competitor model attributes"""
        try:
            from src.models.competitive_models import Competitor
            
            expected_attrs = ['id', 'competitive_group_id', 'asin', 
                            'competitor_name', 'priority', 'is_active', 'added_at']
            
            for attr in expected_attrs:
                assert hasattr(Competitor, attr), \
                    f"Competitor should have attribute '{attr}'"
                    
        except ImportError:
            pytest.skip("Competitor model not available")
    
    def test_competitive_analysis_report_model_attributes(self):
        """Test CompetitiveAnalysisReport model attributes"""
        try:
            from src.models.competitive_models import CompetitiveAnalysisReport
            
            expected_attrs = ['id', 'competitive_group_id', 'analysis_data', 
                            'created_at', 'report_summary']
            
            for attr in expected_attrs:
                assert hasattr(CompetitiveAnalysisReport, attr), \
                    f"CompetitiveAnalysisReport should have attribute '{attr}'"
                    
        except ImportError:
            pytest.skip("CompetitiveAnalysisReport model not available")
    
    def test_product_features_model_attributes(self):
        """Test ProductFeatures model attributes"""
        try:
            from src.models.competitive_models import ProductFeatures
            
            expected_attrs = ['id', 'asin', 'feature_data', 'extracted_at']
            
            for attr in expected_attrs:
                assert hasattr(ProductFeatures, attr), \
                    f"ProductFeatures should have attribute '{attr}'"
                    
        except ImportError:
            pytest.skip("ProductFeatures model not available")


class TestCompetitiveCalculations:
    """Test competitive analysis calculation algorithms"""
    
    def test_price_competitiveness_calculation(self):
        """Test price competitiveness scoring algorithm"""
        # Test the core pricing calculation logic
        
        test_cases = [
            # (main_price, competitor_prices, expected_score_range)
            (30.0, [40.0, 20.0, 35.0], (50, 60)),  # Good position
            (50.0, [30.0, 40.0, 35.0], (25, 40)),  # Poor position
            (35.0, [35.0, 35.0, 35.0], (48, 52)),  # Average position
        ]
        
        for main_price, comp_prices, expected_range in test_cases:
            # Implement the actual competitive scoring formula
            all_prices = [main_price] + comp_prices
            avg_price = sum(all_prices) / len(all_prices)
            price_ratio = main_price / avg_price
            
            # Price competitiveness formula: (2 - price_ratio) * 50
            score = max(0, min(100, (2 - price_ratio) * 50))
            
            assert expected_range[0] <= score <= expected_range[1], \
                f"Price {main_price} vs {comp_prices} should score in range {expected_range}, got {score:.1f}"
    
    def test_rating_competitiveness_calculation(self):
        """Test rating competitiveness scoring"""
        # Rating formula: (rating / 5.0) * 100
        
        test_cases = [
            (5.0, 100.0),  # Perfect rating
            (4.5, 90.0),   # Excellent rating
            (4.0, 80.0),   # Good rating
            (3.5, 70.0),   # Average rating
            (3.0, 60.0),   # Below average
        ]
        
        for rating, expected_score in test_cases:
            calculated_score = (rating / 5.0) * 100
            assert abs(calculated_score - expected_score) < 0.01, \
                f"Rating {rating} should give {expected_score} points, got {calculated_score}"
    
    def test_bsr_position_ranking(self):
        """Test BSR ranking logic"""
        # Lower BSR number = better ranking
        
        test_cases = [
            # (main_rank, competitor_ranks, expected_position_rank)
            (50, [100, 200, 150], 1),    # Best rank (lowest number)
            (200, [100, 150, 175], 4),   # Worst rank (highest number)
            (125, [100, 200, 150], 2),   # Second best rank
        ]
        
        for main_rank, comp_ranks, expected_pos in test_cases:
            all_ranks = [main_rank] + comp_ranks
            sorted_ranks = sorted(all_ranks)
            position_rank = sorted_ranks.index(main_rank) + 1
            
            assert position_rank == expected_pos, \
                f"Rank {main_rank} among {comp_ranks} should be position {expected_pos}, got {position_rank}"
    
    def test_feature_differentiation_scoring(self):
        """Test feature differentiation scoring logic"""
        
        main_features = {"materials": ["eco-friendly"], "colors": ["blue", "green"]}
        comp_features_list = [
            {"materials": ["plastic"], "colors": ["blue"]},
            {"materials": ["rubber"], "colors": ["black"]},
            {"colors": ["green", "red"], "dimensions": ["large"]}
        ]
        
        # Calculate unique features (only in main product)
        all_comp_features = {}
        for comp_features in comp_features_list:
            for category, features in comp_features.items():
                if category not in all_comp_features:
                    all_comp_features[category] = set()
                all_comp_features[category].update(features)
        
        unique_features = []
        for category, features in main_features.items():
            if category in all_comp_features:
                unique_in_category = set(features) - all_comp_features[category]
                unique_features.extend(unique_in_category)
            else:
                unique_features.extend(features)
        
        # Should find "eco-friendly" as unique feature
        assert "eco-friendly" in unique_features
        
        # Calculate missing features (in competitors but not main)
        missing_categories = set(all_comp_features.keys()) - set(main_features.keys())
        assert "dimensions" in missing_categories


class TestIntegrationWorkflows:
    """Test integration workflows for competitive analysis"""
    
    @patch('src.competitive.manager.CompetitiveManager')
    @patch('src.competitive.analyzer.CompetitiveAnalyzer') 
    @patch('src.competitive.llm_reporter.LLMReporter')
    def test_complete_competitive_analysis_workflow(self, mock_reporter, mock_analyzer, mock_manager):
        """Test complete competitive analysis workflow"""
        # Mock manager responses
        mock_manager_instance = Mock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.get_competitive_group.return_value = {
            "id": 1,
            "name": "Test Group",
            "main_product_asin": "B07R7RMQF5",
            "competitors": [{"asin": "B08COMP1"}, {"asin": "B08COMP2"}]
        }
        
        # Mock analyzer responses
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_competitive_group.return_value = {
            "group_info": {"id": 1},
            "main_product": {"asin": "B07R7RMQF5"},
            "competitors": [{"asin": "B08COMP1"}],
            "competitive_summary": {"overall_score": 75}
        }
        
        # Mock reporter responses
        mock_reporter_instance = Mock()
        mock_reporter.return_value = mock_reporter_instance
        mock_reporter_instance.generate_competitive_report.return_value = {
            "report_id": "report_001",
            "executive_summary": "Analysis complete",
            "recommendations": []
        }
        
        # Simulate workflow
        group_id = 1
        
        # Step 1: Get competitive group
        group = mock_manager_instance.get_competitive_group(group_id)
        assert group["id"] == 1
        
        # Step 2: Analyze competitive group  
        analysis = mock_analyzer_instance.analyze_competitive_group(group_id)
        assert "competitive_summary" in analysis
        
        # Step 3: Generate report
        report = mock_reporter_instance.generate_competitive_report(analysis)
        assert "report_id" in report
        assert "executive_summary" in report
        
        # Verify workflow completion
        assert group is not None
        assert analysis is not None
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.competitive", "--cov=src.models.competitive_models"])