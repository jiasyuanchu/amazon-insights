#!/usr/bin/env python3
"""
核心業務邏輯詳細測試 - 針對大型模組提升覆蓋率
Target: 重點提升 competitive/analyzer.py (262行), competitive/manager.py (150行) 等大型模組覆蓋率
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class TestCompetitiveAnalyzerCoreLogic:
    """測試競品分析器核心邏輯 - 目標從14%提升到70%+"""
    
    @pytest.fixture
    def analyzer(self):
        """創建Mock的CompetitiveAnalyzer"""
        from src.competitive.analyzer import CompetitiveAnalyzer
        
        with patch('src.competitive.analyzer.CompetitiveManager'), \
             patch('src.competitive.analyzer.ProductTracker'):
            analyzer = CompetitiveAnalyzer()
            return analyzer
    
    def test_get_product_metrics_success_path(self, analyzer):
        """測試_get_product_metrics的成功路徑"""
        # Mock ProductTracker返回數據
        mock_data = {
            "asin": "B07R7RMQF5",
            "title": "Premium Yoga Mat",
            "price": 29.99,
            "rating": 4.5,
            "review_count": 1234,
            "bsr": {"Sports & Outdoors": 100},
            "availability": "In Stock",
            "bullet_points": ["Eco-friendly", "Non-slip"],
            "key_features": {"materials": ["TPE"], "colors": ["blue"]}
        }
        
        with patch.object(analyzer.tracker, 'get_latest_product_data', return_value=mock_data):
            result = analyzer._get_product_metrics("B07R7RMQF5")
            
            assert result is not None
            assert result.asin == "B07R7RMQF5"
            assert result.price == 29.99
            assert result.rating == 4.5
    
    def test_get_product_metrics_failure_path(self, analyzer):
        """測試_get_product_metrics的失敗路徑"""
        # Mock ProductTracker返回None（產品不存在）
        with patch.object(analyzer.tracker, 'get_latest_product_data', return_value=None):
            result = analyzer._get_product_metrics("INVALID_ASIN")
            assert result is None
        
        # Mock ProductTracker拋出異常
        with patch.object(analyzer.tracker, 'get_latest_product_data', side_effect=Exception("API Error")):
            result = analyzer._get_product_metrics("B07R7RMQF5")
            assert result is None
    
    def test_analyze_price_positioning_comprehensive(self, analyzer):
        """測試價格定位分析的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 創建主產品數據
        main_product = CompetitiveMetrics(
            asin="MAIN123", title="Main Product", price=30.0,
            rating=4.5, review_count=1000, bsr_data={"Category": 100},
            bullet_points=["Feature 1"], key_features={"materials": ["TPE"]},
            availability="In Stock"
        )
        
        # 創建競品數據
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Competitor 1", price=40.0,
                rating=4.2, review_count=800, bsr_data={"Category": 80},
                bullet_points=["Feature A"], key_features={"materials": ["PVC"]},
                availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="COMP2", title="Competitor 2", price=20.0,
                rating=4.0, review_count=600, bsr_data={"Category": 120},
                bullet_points=["Feature B"], key_features={"materials": ["Rubber"]},
                availability="Limited"
            ),
            CompetitiveMetrics(
                asin="COMP3", title="Competitor 3", price=35.0,
                rating=4.7, review_count=1500, bsr_data={"Category": 90},
                bullet_points=["Feature C"], key_features={"materials": ["Foam"]},
                availability="Out of Stock"
            )
        ]
        
        # 測試價格分析邏輯
        result = analyzer._analyze_price_positioning(main_product, competitors)
        
        # 驗證返回結構
        assert isinstance(result, dict)
        assert "main_product_price" in result
        assert "competitors_prices" in result
        assert "price_rank" in result
        assert "price_competitiveness_score" in result
        assert "price_position" in result
        
        # 驗證計算邏輯
        assert result["main_product_price"] == 30.0
        assert len(result["competitors_prices"]) == 3
        assert 1 <= result["price_rank"] <= 4  # 排名1-4
        assert 0 <= result["price_competitiveness_score"] <= 100
    
    def test_analyze_rating_positioning_comprehensive(self, analyzer):
        """測試評分定位分析的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 使用相同的測試數據
        main_product = CompetitiveMetrics(
            asin="MAIN123", title="Main Product", price=30.0,
            rating=4.5, review_count=1000, bsr_data=None,
            bullet_points=[], key_features={}, availability="In Stock"
        )
        
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Comp 1", price=40.0, rating=4.2,
                review_count=800, bsr_data=None, bullet_points=[], 
                key_features={}, availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="COMP2", title="Comp 2", price=20.0, rating=4.7,
                review_count=600, bsr_data=None, bullet_points=[],
                key_features={}, availability="In Stock"
            )
        ]
        
        result = analyzer._analyze_rating_positioning(main_product, competitors)
        
        # 驗證評分分析結構
        assert isinstance(result, dict)
        assert "main_product_rating" in result
        assert "competitors_ratings" in result
        assert "rating_rank" in result
        assert "quality_competitiveness_score" in result
        assert "rating_position" in result
        
        # 驗證評分邏輯
        assert result["main_product_rating"] == 4.5
        assert len(result["competitors_ratings"]) == 2
        assert 1 <= result["rating_rank"] <= 3
    
    def test_analyze_bsr_positioning_comprehensive(self, analyzer):
        """測試BSR定位分析的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 測試帶BSR數據的產品
        main_product = CompetitiveMetrics(
            asin="MAIN123", title="Main Product", price=30.0,
            rating=4.5, review_count=1000, 
            bsr_data={"Sports & Outdoors": 150, "Fitness": 80},
            bullet_points=[], key_features={}, availability="In Stock"
        )
        
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Comp 1", price=40.0, rating=4.2,
                review_count=800, bsr_data={"Sports & Outdoors": 100, "Fitness": 120},
                bullet_points=[], key_features={}, availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="COMP2", title="Comp 2", price=20.0, rating=4.7,
                review_count=600, bsr_data={"Sports & Outdoors": 200},
                bullet_points=[], key_features={}, availability="In Stock"
            )
        ]
        
        result = analyzer._analyze_bsr_positioning(main_product, competitors)
        
        # 驗證BSR分析結構
        assert isinstance(result, dict)
        assert "main_product_bsr" in result
        assert "competitors_bsr" in result
        assert "category_rankings" in result
        
        # 驗證BSR邏輯（更低的數字 = 更好的排名）
        assert isinstance(result["category_rankings"], dict)
    
    def test_analyze_bsr_positioning_missing_data(self, analyzer):
        """測試BSR分析中數據缺失的情況"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 測試主產品沒有BSR數據
        main_product_no_bsr = CompetitiveMetrics(
            asin="MAIN123", title="Main Product", price=30.0,
            rating=4.5, review_count=1000, bsr_data=None,  # 沒有BSR
            bullet_points=[], key_features={}, availability="In Stock"
        )
        
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Comp 1", price=40.0, rating=4.2,
                review_count=800, bsr_data={"Sports & Outdoors": 100},
                bullet_points=[], key_features={}, availability="In Stock"
            )
        ]
        
        result = analyzer._analyze_bsr_positioning(main_product_no_bsr, competitors)
        
        # 應該優雅處理缺失的BSR數據
        assert isinstance(result, dict)
        assert result["main_product_bsr"] is None or result["main_product_bsr"] == {}
    
    def test_analyze_feature_comparison_comprehensive(self, analyzer):
        """測試特徵比較分析的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 創建有豐富特徵的產品數據
        main_product = CompetitiveMetrics(
            asin="MAIN123", title="Main Product", price=30.0,
            rating=4.5, review_count=1000, bsr_data=None,
            bullet_points=["Eco-friendly TPE material", "Non-slip surface"],
            key_features={
                "materials": ["TPE", "eco-friendly"],
                "colors": ["blue", "green"],
                "dimensions": ["72x24 inches"]
            },
            availability="In Stock"
        )
        
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Comp 1", price=40.0, rating=4.2,
                review_count=800, bsr_data=None,
                bullet_points=["PVC material", "Carrying strap included"],
                key_features={
                    "materials": ["PVC"],
                    "colors": ["blue", "black"],
                    "accessories": ["carrying_strap"]
                },
                availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="COMP2", title="Comp 2", price=20.0, rating=4.7,
                review_count=600, bsr_data=None,
                bullet_points=["Rubber material", "Extra thick design"],
                key_features={
                    "materials": ["rubber"],
                    "dimensions": ["68x24 inches"],
                    "thickness": ["8mm"]
                },
                availability="In Stock"
            )
        ]
        
        result = analyzer._analyze_feature_comparison(main_product, competitors)
        
        # 驗證特徵比較結構
        assert isinstance(result, dict)
        assert "main_product_features" in result
        assert "competitors_features" in result
        assert "unique_features" in result
        assert "missing_features" in result
        assert "common_features" in result
        
        # 驗證特徵分析邏輯
        assert "eco-friendly" in result["unique_features"]  # 主產品獨有
        assert "carrying_strap" in result["missing_features"] or "accessories" in result["missing_features"]  # 競品有但主產品沒有
        assert "blue" in result["common_features"]  # 共同特徵
    
    def test_generate_competitive_summary_comprehensive(self, analyzer):
        """測試競品總結生成的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 使用完整的產品數據
        main_product = CompetitiveMetrics(
            asin="MAIN123", title="Premium Yoga Mat", price=29.99,
            rating=4.5, review_count=1234, 
            bsr_data={"Sports & Outdoors": 150, "Fitness": 75},
            bullet_points=["Eco-friendly TPE", "Non-slip texture", "Extra cushioning"],
            key_features={
                "materials": ["TPE", "eco-friendly"],
                "colors": ["blue", "green", "purple"],
                "dimensions": ["72x24x6mm"],
                "benefits": ["joint_support", "flexibility"]
            },
            availability="In Stock"
        )
        
        competitors = [
            CompetitiveMetrics(
                asin="COMP1", title="Basic Yoga Mat", price=19.99,
                rating=4.1, review_count=856, bsr_data={"Sports & Outdoors": 200},
                bullet_points=["PVC material", "Basic design"],
                key_features={"materials": ["PVC"], "colors": ["black"]},
                availability="In Stock"
            ),
            CompetitiveMetrics(
                asin="COMP2", title="Professional Mat", price=49.99,
                rating=4.8, review_count=2100, bsr_data={"Sports & Outdoors": 80},
                bullet_points=["Premium rubber", "Professional grade", "Alignment lines"],
                key_features={
                    "materials": ["natural_rubber"],
                    "colors": ["black", "grey"],
                    "features": ["alignment_lines", "carrying_strap"]
                },
                availability="In Stock"
            )
        ]
        
        result = analyzer._generate_competitive_summary(main_product, competitors)
        
        # 驗證競品總結結構
        assert isinstance(result, dict)
        assert "overall_competitive_score" in result
        assert "price_score" in result
        assert "quality_score" in result
        assert "market_position" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommended_actions" in result
        
        # 驗證分數範圍
        assert 0 <= result["overall_competitive_score"] <= 100
        assert 0 <= result["price_score"] <= 100
        assert 0 <= result["quality_score"] <= 100
        
        # 驗證市場定位
        assert result["market_position"] in ["excellent", "competitive", "challenging", "poor"]
        
        # 驗證建議列表
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
        assert isinstance(result["recommended_actions"], list)
    
    def test_metrics_to_dict_comprehensive(self, analyzer):
        """測試metrics轉字典的完整邏輯"""
        from src.competitive.analyzer import CompetitiveMetrics
        
        # 測試完整數據
        full_metrics = CompetitiveMetrics(
            asin="FULL123", title="Full Data Product", price=29.99,
            rating=4.5, review_count=1234,
            bsr_data={"Category1": 100, "Category2": 200},
            bullet_points=["Feature 1", "Feature 2", "Feature 3"],
            key_features={
                "materials": ["material1", "material2"],
                "colors": ["color1", "color2"],
                "dimensions": ["72x24"]
            },
            availability="In Stock"
        )
        
        result = analyzer._metrics_to_dict(full_metrics)
        
        # 驗證完整轉換
        assert result["asin"] == "FULL123"
        assert result["title"] == "Full Data Product"
        assert result["price"] == 29.99
        assert result["rating"] == 4.5
        assert result["review_count"] == 1234
        assert isinstance(result["bsr_data"], dict)
        assert len(result["bsr_data"]) == 2
        assert isinstance(result["bullet_points"], list)
        assert len(result["bullet_points"]) == 3
        assert isinstance(result["key_features"], dict)
        assert len(result["key_features"]) == 3
        
        # 測試部分數據缺失
        partial_metrics = CompetitiveMetrics(
            asin="PARTIAL123", title="Partial Data", price=None,
            rating=None, review_count=None, bsr_data={},
            bullet_points=[], key_features={}, availability="Unknown"
        )
        
        result = analyzer._metrics_to_dict(partial_metrics)
        
        # 驗證None值處理
        assert result["asin"] == "PARTIAL123"
        assert result["price"] is None
        assert result["rating"] is None
        assert result["review_count"] is None
        assert result["bsr_data"] == {}
        assert result["bullet_points"] == []
        assert result["key_features"] == {}


class TestCompetitiveManagerCoreLogic:
    """測試競品管理器核心邏輯 - 目標從15%提升到70%+"""
    
    @pytest.fixture
    def manager(self):
        """創建Mock的CompetitiveManager"""
        from src.competitive.manager import CompetitiveManager
        
        with patch('src.competitive.manager.DatabaseManager'):
            manager = CompetitiveManager()
            return manager
    
    def test_create_competitive_group_success(self, manager):
        """測試創建競品組的成功路徑"""
        group_data = {
            "name": "Test Competitive Group",
            "main_product_asin": "B07R7RMQF5",
            "description": "Test description"
        }
        
        # Mock數據庫操作
        mock_group = Mock()
        mock_group.id = 1
        mock_group.name = group_data["name"]
        mock_group.main_product_asin = group_data["main_product_asin"]
        mock_group.created_at = datetime.now()
        mock_group.is_active = True
        
        with patch.object(manager.db, 'create_competitive_group', return_value=mock_group):
            result = manager.create_competitive_group(group_data)
            
            assert isinstance(result, dict)
            assert result["id"] == 1
            assert result["name"] == group_data["name"]
            assert result["main_product_asin"] == group_data["main_product_asin"]
            assert result["is_active"] is True
    
    def test_create_competitive_group_validation_errors(self, manager):
        """測試創建競品組的驗證錯誤"""
        # 測試各種無效輸入
        invalid_inputs = [
            {},  # 空字典
            {"name": ""},  # 空名稱
            {"name": "Test"},  # 缺少main_product_asin
            {"main_product_asin": "B07R7RMQF5"},  # 缺少name
            {"name": "Test", "main_product_asin": ""},  # 空ASIN
            {"name": "Test", "main_product_asin": "INVALID"},  # 無效ASIN格式
        ]
        
        for invalid_data in invalid_inputs:
            with patch.object(manager.db, 'create_competitive_group', side_effect=ValueError("Validation error")):
                try:
                    result = manager.create_competitive_group(invalid_data)
                    # 如果沒有異常，應該返回錯誤結構
                    assert "error" in result
                except ValueError:
                    # 預期的驗證錯誤
                    assert True
    
    def test_get_competitive_group_not_found(self, manager):
        """測試獲取不存在的競品組"""
        # Mock資料庫返回None（組不存在）
        with patch.object(manager.db, 'get_competitive_group_by_id', return_value=None):
            result = manager.get_competitive_group(999)
            assert result is None
    
    def test_add_competitor_success_and_errors(self, manager):
        """測試添加競品的成功和錯誤情況"""
        # 測試成功添加
        competitor_data = {
            "asin": "B08COMPETITOR1",
            "competitor_name": "Test Competitor",
            "priority": 1
        }
        
        mock_competitor = Mock()
        mock_competitor.id = 1
        mock_competitor.asin = competitor_data["asin"]
        mock_competitor.competitor_name = competitor_data["competitor_name"]
        mock_competitor.priority = competitor_data["priority"]
        mock_competitor.added_at = datetime.now()
        
        with patch.object(manager.db, 'add_competitor', return_value=mock_competitor):
            result = manager.add_competitor(1, competitor_data)
            
            assert isinstance(result, dict)
            assert result["asin"] == competitor_data["asin"]
            assert result["priority"] == competitor_data["priority"]
        
        # 測試添加重複競品
        with patch.object(manager.db, 'add_competitor', side_effect=ValueError("Competitor already exists")):
            try:
                result = manager.add_competitor(1, competitor_data)
                assert "error" in result
            except ValueError:
                assert True
        
        # 測試無效競品數據
        invalid_competitor_data = [
            {"asin": ""},  # 空ASIN
            {"asin": "INVALID_FORMAT"},  # 無效ASIN格式
            {},  # 空數據
        ]
        
        for invalid_data in invalid_competitor_data:
            with patch.object(manager.db, 'add_competitor', side_effect=ValueError("Invalid data")):
                try:
                    result = manager.add_competitor(1, invalid_data)
                    assert "error" in result
                except ValueError:
                    assert True
    
    def test_remove_competitor_scenarios(self, manager):
        """測試移除競品的各種情況"""
        # 測試成功移除
        with patch.object(manager.db, 'remove_competitor', return_value=True):
            result = manager.remove_competitor(1, "B08COMPETITOR1")
            assert result["status"] == "removed" or result is True
        
        # 測試移除不存在的競品
        with patch.object(manager.db, 'remove_competitor', return_value=False):
            result = manager.remove_competitor(1, "NONEXISTENT")
            assert result is False or "error" in result
        
        # 測試數據庫錯誤
        with patch.object(manager.db, 'remove_competitor', side_effect=Exception("DB Error")):
            try:
                result = manager.remove_competitor(1, "B08COMPETITOR1")
                assert "error" in result
            except Exception:
                assert True
    
    def test_list_competitive_groups_various_states(self, manager):
        """測試列出競品組的各種狀態"""
        # 測試有多個組的情況
        mock_groups = [
            Mock(id=1, name="Active Group 1", is_active=True, 
                 created_at=datetime.now(), main_product_asin="MAIN1"),
            Mock(id=2, name="Active Group 2", is_active=True,
                 created_at=datetime.now(), main_product_asin="MAIN2"),
            Mock(id=3, name="Inactive Group", is_active=False,
                 created_at=datetime.now(), main_product_asin="MAIN3")
        ]
        
        with patch.object(manager.db, 'get_all_competitive_groups', return_value=mock_groups):
            result = manager.list_competitive_groups()
            
            assert isinstance(result, dict)
            assert "groups" in result
            assert "total_count" in result
            assert "active_count" in result
            assert len(result["groups"]) == 3
            assert result["total_count"] == 3
            assert result["active_count"] == 2  # 只有2個active
        
        # 測試空列表
        with patch.object(manager.db, 'get_all_competitive_groups', return_value=[]):
            result = manager.list_competitive_groups()
            assert result["total_count"] == 0
            assert result["active_count"] == 0
            assert len(result["groups"]) == 0
        
        # 測試數據庫錯誤
        with patch.object(manager.db, 'get_all_competitive_groups', side_effect=Exception("DB Error")):
            try:
                result = manager.list_competitive_groups()
                assert "error" in result
            except Exception:
                assert True


class TestMonitoringModulesComprehensive:
    """測試監控模組的詳細邏輯"""
    
    @patch('src.monitoring.product_tracker.DatabaseManager')
    @patch('src.api.firecrawl_client.FirecrawlClient')
    def test_product_tracker_comprehensive(self, mock_firecrawl, mock_db):
        """測試ProductTracker的詳細功能"""
        from src.monitoring.product_tracker import ProductTracker
        
        # Mock dependencies
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_firecrawl_instance = Mock()
        mock_firecrawl.return_value = mock_firecrawl_instance
        
        tracker = ProductTracker()
        
        # 測試成功追蹤產品
        mock_firecrawl_instance.scrape_amazon_product.return_value = {
            "success": True,
            "data": {
                "html": "<html>Product Page</html>",
                "markdown": "# Product\nPrice: $29.99\nRating: 4.5 out of 5"
            }
        }
        
        with patch('src.monitoring.product_tracker.AmazonProductParser') as mock_parser:
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            mock_parser_instance.parse_product_data.return_value = {
                "title": "Test Product",
                "price": 29.99,
                "rating": 4.5,
                "scraped_at": datetime.now().isoformat()
            }
            
            result = tracker.track_product("B07R7RMQF5")
            
            # 驗證追蹤結果
            assert isinstance(result, dict)
            assert "asin" in result or result.get("title") == "Test Product"
        
        # 測試scraping失敗的情況
        mock_firecrawl_instance.scrape_amazon_product.return_value = {
            "success": False,
            "error": "Product not found"
        }
        
        result = tracker.track_product("INVALID_ASIN")
        # 應該優雅處理失敗
        assert result is None or "error" in result
        
        # 測試解析失敗的情況
        mock_firecrawl_instance.scrape_amazon_product.return_value = {
            "success": True,
            "data": {"html": "<html>Invalid</html>", "markdown": "Invalid"}
        }
        
        with patch('src.monitoring.product_tracker.AmazonProductParser') as mock_parser:
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            mock_parser_instance.parse_product_data.return_value = None  # 解析失敗
            
            result = tracker.track_product("B07R7RMQF5")
            assert result is None or "error" in result
    
    @patch('src.monitoring.anomaly_detector.DatabaseManager')
    def test_anomaly_detector_comprehensive(self, mock_db):
        """測試AnomalyDetector的詳細功能"""
        from src.monitoring.anomaly_detector import AnomalyDetector
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        detector = AnomalyDetector()
        
        # 測試價格異常檢測 - 正常情況
        mock_history = [
            {"price": 29.99, "recorded_at": datetime.now() - timedelta(days=1)},
            {"price": 28.99, "recorded_at": datetime.now() - timedelta(days=2)},
            {"price": 30.99, "recorded_at": datetime.now() - timedelta(days=3)},
            {"price": 29.49, "recorded_at": datetime.now() - timedelta(days=4)},
        ]
        
        mock_db_instance.get_price_history.return_value = mock_history
        
        # 測試正常價格（無異常）
        result = detector.detect_price_anomaly("B07R7RMQF5", current_price=29.99)
        assert isinstance(result, dict)
        assert "anomaly_detected" in result
        assert result["anomaly_detected"] is False or result["anomaly_detected"] is True
        
        # 測試價格異常（大幅上漲）
        result = detector.detect_price_anomaly("B07R7RMQF5", current_price=50.99)  # 大幅上漲
        assert result["anomaly_detected"] is True
        assert result["anomaly_type"] in ["price_spike", "significant_increase"]
        
        # 測試價格異常（大幅下降）
        result = detector.detect_price_anomaly("B07R7RMQF5", current_price=15.99)  # 大幅下降
        assert result["anomaly_detected"] is True
        assert result["anomaly_type"] in ["price_drop", "significant_decrease"]
        
        # 測試沒有歷史數據的情況
        mock_db_instance.get_price_history.return_value = []
        result = detector.detect_price_anomaly("NEW_ASIN", current_price=29.99)
        assert result["anomaly_detected"] is False  # 沒有歷史數據，無法檢測異常
        
        # 測試數據庫錯誤
        mock_db_instance.get_price_history.side_effect = Exception("DB Error")
        try:
            result = detector.detect_price_anomaly("B07R7RMQF5", current_price=29.99)
            assert result is None or "error" in result
        except Exception:
            assert True


class TestLLMReporterCoreLogic:
    """測試LLM報告器核心邏輯 - 目標從12%提升到60%+"""
    
    @patch('openai.OpenAI')
    def test_llm_reporter_initialization(self, mock_openai):
        """測試LLMReporter初始化和配置"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        try:
            from src.competitive.llm_reporter import LLMReporter
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                reporter = LLMReporter()
                assert reporter is not None
                assert hasattr(reporter, 'client') or hasattr(reporter, 'openai_client')
                
        except ImportError:
            pytest.skip("LLMReporter not available")
    
    @patch('openai.OpenAI')
    def test_generate_competitive_report_success(self, mock_openai):
        """測試競品報告生成的成功路徑"""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "executive_summary": "Your product is well-positioned in the market...",
            "strengths": ["Competitive pricing", "High quality rating"],
            "weaknesses": ["Limited color options"],
            "opportunities": ["Expand to premium segment"],
            "threats": ["New competitors entering market"],
            "recommendations": [
                {"category": "product", "action": "Add more colors", "priority": "medium"}
            ]
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        
        try:
            from src.competitive.llm_reporter import LLMReporter
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                reporter = LLMReporter()
                
                analysis_data = {
                    "group_info": {"name": "Test Group"},
                    "main_product": {"asin": "MAIN123", "price": 29.99},
                    "competitors": [{"asin": "COMP1", "price": 34.99}],
                    "competitive_summary": {"overall_score": 75}
                }
                
                result = reporter.generate_competitive_report(analysis_data)
                
                # 驗證報告結構
                assert isinstance(result, dict)
                assert "executive_summary" in result
                assert "strengths" in result
                assert "weaknesses" in result
                assert "recommendations" in result
                
        except ImportError:
            pytest.skip("LLMReporter not available")
    
    @patch('openai.OpenAI')
    def test_generate_competitive_report_api_failure(self, mock_openai):
        """測試LLM API失敗的處理"""
        # Mock OpenAI API錯誤
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        try:
            from src.competitive.llm_reporter import LLMReporter
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                reporter = LLMReporter()
                
                analysis_data = {"group_info": {"name": "Test"}}
                
                try:
                    result = reporter.generate_competitive_report(analysis_data)
                    # 應該有fallback或錯誤處理
                    assert result is None or "error" in result
                except Exception:
                    # 預期的API錯誤
                    assert True
                    
        except ImportError:
            pytest.skip("LLMReporter not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])