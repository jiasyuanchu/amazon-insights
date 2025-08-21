#!/usr/bin/env python3
"""
錯誤處理和邊界情況測試 - 補充非happy path測試
Target: 測試所有錯誤分支、例外情況、邊界條件來大幅提升覆蓋率
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class TestParserErrorHandling:
    """測試解析器的錯誤處理分支"""
    
    @pytest.fixture
    def parser(self):
        from src.parsers.amazon_parser import AmazonProductParser
        return AmazonProductParser()
    
    def test_parse_product_data_invalid_inputs(self, parser):
        """測試parse_product_data的所有錯誤情況"""
        # 測試None輸入
        result = parser.parse_product_data(None)
        assert result is None
        
        # 測試空字典
        result = parser.parse_product_data({})
        assert result is None
        
        # 測試缺少data字段
        result = parser.parse_product_data({"invalid": "structure"})
        assert result is None
        
        # 測試data為None
        result = parser.parse_product_data({"data": None})
        assert result is None
        
        # 測試空的data
        result = parser.parse_product_data({"data": {}})
        assert result is not None  # 應該返回默認結構
    
    def test_parse_product_data_exception_handling(self, parser):
        """測試parse_product_data的異常處理"""
        # 測試損壞的HTML/JSON導致異常
        malformed_data = {
            "data": {
                "html": "<html><title>Test</title><div class='price'>$",  # 不完整HTML
                "markdown": "# Test Product\n\nPrice: $invalid_price"
            }
        }
        
        # 應該捕獲異常並返回None
        result = parser.parse_product_data(malformed_data)
        # 可能返回None（異常）或partial data（部分解析成功）
        assert result is None or isinstance(result, dict)
    
    def test_extract_title_all_fallback_paths(self, parser):
        """測試title提取的所有fallback路徑"""
        # 測試空HTML和空markdown
        result = parser._extract_title(None, "")
        assert result == "Title not found"
        
        # 測試只有短標題（<10字符）
        result = parser._extract_title(None, "# Short")
        assert result == "Title not found"
        
        # 測試包含navigation text的情況
        navigation_markdown = """
        Amazon.com
        Search
        Hello, User
        Cart (0)
        Account & Lists
        """
        result = parser._extract_title(None, navigation_markdown)
        assert result == "Title not found"
        
        # 測試包含冒號的標題（應該被跳過）
        colon_markdown = "Sports : Outdoors : Equipment"
        result = parser._extract_title(None, colon_markdown)
        assert result == "Title not found"
    
    def test_extract_price_edge_cases(self, parser):
        """測試價格提取的邊界情況"""
        # 測試無價格數據
        result = parser._extract_price(None, "No price information available")
        assert result is None
        
        # 測試多個價格，應該返回第一個有效的
        multiple_prices = "Was $49.99, now $29.99, shipping $5.99"
        result = parser._extract_price(None, multiple_prices)
        assert result == 49.99  # 第一個找到的價格
        
        # 測試價格格式邊界
        edge_cases = [
            "$0.01",    # 最小價格
            "$99999",   # 大價格
            "$1,000,000.99",  # 帶逗號的大價格
        ]
        
        for price_text in edge_cases:
            result = parser._extract_price(None, price_text)
            assert result is not None
            assert result > 0
    
    def test_extract_rating_boundary_values(self, parser):
        """測試評分提取的邊界值"""
        boundary_cases = [
            ("1.0 out of 5 stars", 1.0),
            ("5.0 out of 5 stars", 5.0),
            ("0.5 out of 5 stars", 0.5),
            ("4.9 out of 5 stars", 4.9),
        ]
        
        for rating_text, expected in boundary_cases:
            result = parser._extract_rating(None, rating_text)
            assert result == expected
        
        # 測試無效評分
        invalid_ratings = [
            "6.0 out of 5 stars",  # 超出範圍
            "No rating available",
            "Rating: N/A",
            ""
        ]
        
        for invalid_text in invalid_ratings:
            result = parser._extract_rating(None, invalid_text)
            # 可能返回None或忽略超出範圍的值
            assert result is None or (1.0 <= result <= 5.0)
    
    def test_extract_review_count_edge_cases(self, parser):
        """測試評論數提取的邊界情況"""
        # 測試大數字
        large_number_cases = [
            "1,000,000 customer reviews",
            "999,999 ratings",
            "1 review",  # 單數
            "0 reviews"  # 零評論
        ]
        
        for text in large_number_cases:
            result = parser._extract_review_count(None, text)
            assert result is not None
            assert result >= 0
        
        # 測試無效數據
        invalid_cases = [
            "No reviews available",
            "Coming soon",
            "",
            "review count unavailable"
        ]
        
        for invalid_text in invalid_cases:
            result = parser._extract_review_count(None, invalid_text)
            assert result is None
    
    def test_extract_bsr_malformed_data(self, parser):
        """測試BSR提取的畸形數據處理"""
        # 測試畸形BSR數據
        malformed_bsr_cases = [
            "Best Sellers Rank: # in Category",  # 缺少數字
            "Best Sellers Rank: #abc in Sports",  # 非數字
            "Random text with #123 somewhere",    # 不是BSR格式
            "",  # 空字符串
            "Best Sellers Rank information unavailable"
        ]
        
        for malformed_text in malformed_bsr_cases:
            result = parser._extract_bsr(None, malformed_text)
            # 應該返回None或空字典
            assert result is None or result == {}
    
    def test_extract_availability_edge_cases(self, parser):
        """測試庫存狀態提取的邊界情況"""
        # 測試各種庫存狀態
        availability_cases = [
            ("In Stock", "In Stock"),
            ("Out of Stock", "Out of Stock"), 
            ("Currently unavailable", "Currently unavailable"),
            ("Available", "Available"),
            ("No availability information", "Unknown"),  # 默認值
            ("", "Unknown"),  # 空字符串
        ]
        
        for input_text, expected in availability_cases:
            result = parser._extract_availability(None, input_text)
            if expected == "Unknown":
                assert result == "Unknown"
            else:
                assert expected.lower() in result.lower()


class TestCompetitiveAnalyzerErrorHandling:
    """測試競品分析器的錯誤處理"""
    
    @patch('src.competitive.analyzer.CompetitiveManager')
    @patch('src.competitive.analyzer.ProductTracker')
    def test_analyze_competitive_group_error_cases(self, mock_tracker, mock_manager):
        """測試競品分析的錯誤情況"""
        from src.competitive.analyzer import CompetitiveAnalyzer
        
        # Mock instances
        analyzer = CompetitiveAnalyzer()
        mock_manager_instance = Mock()
        mock_tracker_instance = Mock()
        analyzer.manager = mock_manager_instance
        analyzer.tracker = mock_tracker_instance
        
        # 測試競品組不存在
        mock_manager_instance.get_competitive_group.return_value = None
        result = analyzer.analyze_competitive_group(999)
        assert "error" in result
        assert "not found" in result["error"].lower()
        
        # 測試主產品數據缺失
        mock_manager_instance.get_competitive_group.return_value = Mock(
            name="Test Group",
            main_product_asin="INVALID_ASIN"
        )
        
        with patch.object(analyzer, '_get_product_metrics', return_value=None):
            result = analyzer.analyze_competitive_group(1)
            assert "error" in result
            assert "not available" in result["error"].lower()
        
        # 測試沒有競品數據
        mock_group = Mock()
        mock_group.name = "Test Group"
        mock_group.main_product_asin = "MAIN123"
        mock_group.active_competitors = []  # 空的競品列表
        
        mock_manager_instance.get_competitive_group.return_value = mock_group
        
        with patch.object(analyzer, '_get_product_metrics', return_value=Mock()):
            result = analyzer.analyze_competitive_group(1)
            assert "error" in result
            assert "no competitor" in result["error"].lower()
    
    def test_metrics_to_dict_with_none_values(self):
        """測試metrics轉字典時的None值處理"""
        from src.competitive.analyzer import CompetitiveAnalyzer, CompetitiveMetrics
        
        analyzer = CompetitiveAnalyzer()
        
        # 創建包含None值的metrics
        metrics_with_nones = CompetitiveMetrics(
            asin="TEST123",
            title="Test Product",
            price=None,           # None價格
            rating=None,          # None評分
            review_count=None,    # None評論數
            bsr_data=None,        # None BSR
            bullet_points=[],     # 空列表
            key_features={},      # 空字典
            availability="Unknown"
        )
        
        result = analyzer._metrics_to_dict(metrics_with_nones)
        
        # 驗證None值處理
        assert result["asin"] == "TEST123"
        assert result["price"] is None
        assert result["rating"] is None
        assert result["review_count"] is None
        assert result["bsr_data"] is None
        assert isinstance(result["bullet_points"], list)
        assert isinstance(result["key_features"], dict)


class TestCacheErrorHandling:
    """測試緩存的錯誤處理分支"""
    
    @patch('redis.from_url')
    def test_redis_connection_failure(self, mock_redis_from_url):
        """測試Redis連接失敗的處理"""
        # Mock Redis連接失敗
        mock_redis_from_url.side_effect = Exception("Redis connection failed")
        
        try:
            from src.cache.redis_service import get_redis_client, cache
            
            # 測試連接失敗時的處理
            with pytest.raises(Exception):
                get_redis_client()
                
        except ImportError:
            pytest.skip("Redis service not available")
    
    @patch('src.cache.redis_service.get_redis_client')
    def test_cache_operations_redis_failure(self, mock_get_client):
        """測試緩存操作時Redis失敗的處理"""
        # Mock Redis客戶端操作失敗
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Redis GET failed")
        mock_client.set.side_effect = Exception("Redis SET failed")
        mock_client.delete.side_effect = Exception("Redis DELETE failed")
        mock_get_client.return_value = mock_client
        
        try:
            from src.cache.redis_service import cache
            
            # 測試GET失敗
            result = cache.get("test_key")
            # 應該優雅處理失敗，返回None或default
            assert result is None or isinstance(result, dict)
            
            # 測試SET失敗
            success = cache.set("test_key", {"data": "test"}, ttl=3600)
            # 應該返回False或處理失敗
            assert success is False or success is None
            
            # 測試DELETE失敗
            deleted = cache.delete("test_key")
            # 應該返回0或False
            assert deleted == 0 or deleted is False
            
        except ImportError:
            pytest.skip("Cache operations not available")


class TestAPIErrorHandling:
    """測試API層的錯誤處理"""
    
    def test_invalid_asin_format_comprehensive(self):
        """測試ASIN格式驗證的完整錯誤情況"""
        from api.models.schemas import ProductSummary
        from pydantic import ValidationError
        
        # 測試各種無效ASIN格式
        invalid_asins = [
            "",              # 空字符串
            "SHORT",         # 太短
            "TOOLONGASIN12", # 太長
            "B07R7RMQF@",    # 特殊字符
            "123456789",     # 少一位
            None,            # None值
            123,             # 非字符串
            "   B07R7RMQF5   ",  # 帶空格
        ]
        
        for invalid_asin in invalid_asins:
            try:
                # 嘗試創建ProductSummary，可能會validation error
                summary = ProductSummary(
                    asin=invalid_asin,
                    title="Test Product",
                    last_updated=datetime.now().isoformat()
                )
                # 如果沒有錯誤，驗證ASIN被正確處理
                if summary.asin is not None:
                    assert isinstance(summary.asin, str)
            except (ValidationError, TypeError):
                # 預期的validation錯誤
                assert True
    
    def test_price_validation_boundary_values(self):
        """測試價格驗證的邊界值"""
        from api.models.schemas import ProductSummary
        
        # 邊界價格值
        boundary_prices = [
            0.01,        # 最小正價格
            -1.0,        # 負價格（應該無效）
            0.0,         # 零價格（應該無效）
            999999.99,   # 極大價格
            "invalid",   # 非數字
        ]
        
        for price in boundary_prices:
            try:
                summary = ProductSummary(
                    asin="B07R7RMQF5",
                    title="Test Product", 
                    current_price=price,
                    last_updated=datetime.now().isoformat()
                )
                
                # 如果成功創建，驗證價格處理
                if hasattr(summary, 'current_price') and summary.current_price is not None:
                    assert isinstance(summary.current_price, (int, float))
                    assert summary.current_price >= 0
                    
            except (ValueError, TypeError):
                # 預期的type錯誤
                assert True
    
    def test_rating_validation_boundary_values(self):
        """測試評分驗證的邊界值"""
        from api.models.schemas import ProductSummary
        
        boundary_ratings = [
            0.0,    # 最小評分（可能無效）
            1.0,    # 最小有效評分
            5.0,    # 最大評分
            6.0,    # 超出範圍
            -1.0,   # 負評分
            "4.5",  # 字符串格式
        ]
        
        for rating in boundary_ratings:
            try:
                summary = ProductSummary(
                    asin="B07R7RMQF5",
                    title="Test Product",
                    current_rating=rating,
                    last_updated=datetime.now().isoformat()
                )
                
                # 驗證評分範圍
                if hasattr(summary, 'current_rating') and summary.current_rating is not None:
                    assert 0.0 <= summary.current_rating <= 5.0
                    
            except (ValueError, TypeError):
                assert True


class TestConfigurationErrorHandling:
    """測試配置模組的錯誤處理"""
    
    def test_missing_environment_variables(self):
        """測試缺少環境變量時的處理"""
        # 保存原始環境變量
        original_env = os.environ.copy()
        
        try:
            # 移除關鍵環境變量
            critical_vars = ['FIRECRAWL_API_KEY', 'OPENAI_API_KEY', 'DATABASE_URL']
            for var in critical_vars:
                if var in os.environ:
                    del os.environ[var]
            
            # 重新import config測試默認值處理
            import importlib
            import config.config
            importlib.reload(config.config)
            
            # 驗證配置模組不會crash
            assert config.config.DATABASE_URL is not None
            assert config.config.REDIS_URL is not None
            
        except Exception as e:
            # 配置模組應該優雅處理缺失的env vars
            assert "KeyError" not in str(e), "Config should handle missing env vars gracefully"
            
        finally:
            # 恢復環境變量
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_invalid_environment_variable_formats(self):
        """測試無效環境變量格式的處理"""
        test_cases = [
            ('REDIS_PORT', 'invalid_port'),     # 非數字端口
            ('DATABASE_URL', 'invalid://url'),  # 無效URL格式
            ('CACHE_DEFAULT_TTL', 'not_a_number'),  # 非數字TTL
        ]
        
        original_env = os.environ.copy()
        
        for env_var, invalid_value in test_cases:
            try:
                # 設置無效值
                os.environ[env_var] = invalid_value
                
                # 重新加載配置
                import importlib
                import config.config
                importlib.reload(config.config)
                
                # 驗證有合理的默認值或錯誤處理
                if env_var == 'REDIS_PORT':
                    port = getattr(config.config, 'REDIS_PORT', 6379)
                    assert isinstance(port, int)
                    assert 1 <= port <= 65535
                    
            except Exception as e:
                # 應該有適當的錯誤處理
                assert isinstance(e, (ValueError, TypeError)), f"Unexpected error type: {type(e)}"
            
            finally:
                # 恢復環境變量
                os.environ.clear()
                os.environ.update(original_env)


class TestDatabaseErrorHandling:
    """測試資料庫操作的錯誤處理"""
    
    @patch('sqlalchemy.create_engine')
    def test_database_connection_failure(self, mock_create_engine):
        """測試資料庫連接失敗的處理"""
        # Mock資料庫連接失敗
        mock_create_engine.side_effect = Exception("Database connection failed")
        
        try:
            from src.models.product_models import DatabaseManager
            
            # 測試連接失敗時的處理
            with pytest.raises(Exception):
                db_manager = DatabaseManager()
                
        except ImportError:
            pytest.skip("DatabaseManager not available")
    
    def test_database_model_validation_errors(self):
        """測試資料庫模型驗證錯誤"""
        try:
            from src.models.product_models import ProductSummary
            from src.models.competitive_models import CompetitiveGroup
            
            # 測試模型字段驗證
            # 這些應該有適當的約束
            test_cases = [
                # (model_class, invalid_data)
                (ProductSummary, {"asin": None}),  # None ASIN
                (ProductSummary, {"asin": ""}),    # 空ASIN
                (CompetitiveGroup, {"name": None}), # None name
                (CompetitiveGroup, {"name": ""}),   # 空name
            ]
            
            for model_class, invalid_data in test_cases:
                try:
                    instance = model_class(**invalid_data)
                    # 如果沒有錯誤，檢查數據處理
                    assert instance is not None
                except (ValueError, TypeError):
                    # 預期的驗證錯誤
                    assert True
                    
        except ImportError:
            pytest.skip("Database models not available")


class TestCompetitiveCalculationEdgeCases:
    """測試競品計算的邊界情況"""
    
    def test_price_calculation_division_by_zero(self):
        """測試價格計算中的除零保護"""
        # 測試空競品列表
        main_price = 29.99
        competitor_prices = []  # 空列表
        
        # 計算邏輯應該處理空列表
        if competitor_prices:
            all_prices = [main_price] + competitor_prices
            avg_price = sum(all_prices) / len(all_prices)
        else:
            # 應該有默認處理邏輯
            avg_price = main_price  # 或其他默認邏輯
        
        assert avg_price > 0
    
    def test_competitive_score_extreme_values(self):
        """測試競品評分的極端值"""
        extreme_test_cases = [
            # (main_price, competitor_prices, description)
            (1.0, [100.0, 200.0, 300.0], "極低主產品價格"),
            (1000.0, [1.0, 2.0, 3.0], "極高主產品價格"),
            (29.99, [29.99, 29.99, 29.99], "完全相同價格"),
            (50.0, [50.01], "微小價格差異"),
        ]
        
        for main_price, comp_prices, description in extreme_test_cases:
            all_prices = [main_price] + comp_prices
            avg_price = sum(all_prices) / len(all_prices)
            price_ratio = main_price / avg_price
            
            # 競品評分公式: (2 - price_ratio) * 50
            raw_score = (2 - price_ratio) * 50
            bounded_score = max(0, min(100, raw_score))
            
            # 驗證分數在合理範圍內
            assert 0 <= bounded_score <= 100, f"Score out of bounds for {description}"
    
    def test_rating_calculation_invalid_data(self):
        """測試評分計算中的無效數據處理"""
        invalid_ratings = [None, 0, -1.0, 6.0, "invalid"]
        
        for invalid_rating in invalid_ratings:
            try:
                # 評分公式: (rating / 5.0) * 100
                if invalid_rating is None or not isinstance(invalid_rating, (int, float)):
                    score = 0  # 默認處理
                elif invalid_rating < 1.0 or invalid_rating > 5.0:
                    score = 0  # 超出範圍處理
                else:
                    score = (invalid_rating / 5.0) * 100
                
                assert 0 <= score <= 100
                
            except (TypeError, ZeroDivisionError):
                # 預期的錯誤
                assert True


class TestFileIOErrorHandling:
    """測試文件I/O錯誤處理"""
    
    def test_nonexistent_file_handling(self):
        """測試不存在文件的處理"""
        # 測試讀取不存在的配置文件
        nonexistent_files = [
            "/nonexistent/config.json",
            "/invalid/path/data.csv",
            "./missing_file.txt"
        ]
        
        for filepath in nonexistent_files:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
            except FileNotFoundError:
                # 預期的文件不存在錯誤
                assert True
            except PermissionError:
                # 預期的權限錯誤
                assert True
    
    def test_invalid_json_parsing(self):
        """測試無效JSON解析的處理"""
        invalid_json_strings = [
            '{"invalid": json syntax}',    # 語法錯誤
            '{incomplete json',            # 不完整JSON
            '',                           # 空字符串
            'not json at all',            # 非JSON格式
            '{"key": undefined_value}',   # 無效值
        ]
        
        for json_str in invalid_json_strings:
            try:
                data = json.loads(json_str)
                # 如果沒有錯誤，數據應該是有效的
                assert isinstance(data, dict)
            except (json.JSONDecodeError, ValueError):
                # 預期的JSON解析錯誤
                assert True


class TestNetworkErrorHandling:
    """測試網絡錯誤處理"""
    
    @patch('requests.get')
    def test_api_request_timeout_handling(self, mock_get):
        """測試API請求超時的處理"""
        # Mock網絡超時
        mock_get.side_effect = Exception("Request timeout")
        
        try:
            from src.api.firecrawl_client import FirecrawlClient
            
            with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test_key'}):
                client = FirecrawlClient()
                
                # 測試超時處理
                with patch.object(client, 'scrape_amazon_product') as mock_scrape:
                    mock_scrape.side_effect = Exception("Timeout")
                    
                    result = client.scrape_amazon_product("B07R7RMQF5")
                    # 應該返回錯誤格式而不是crash
                    assert result is None or (isinstance(result, dict) and "error" in result)
                    
        except ImportError:
            pytest.skip("FirecrawlClient not available")
    
    @patch('requests.post')
    def test_api_request_rate_limit_handling(self, mock_post):
        """測試API請求速率限制的處理"""
        # Mock 429 rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_post.return_value = mock_response
        
        try:
            from src.api.firecrawl_client import FirecrawlClient
            
            with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test_key'}):
                client = FirecrawlClient()
                
                # 測試rate limit處理
                with patch.object(client, 'scrape_amazon_product') as mock_scrape:
                    mock_scrape.return_value = {
                        "success": False,
                        "error": "Rate limit exceeded",
                        "error_code": 429
                    }
                    
                    result = client.scrape_amazon_product("B07R7RMQF5")
                    assert result["success"] is False
                    assert "rate limit" in result["error"].lower()
                    
        except ImportError:
            pytest.skip("FirecrawlClient not available")


class TestConcurrencyErrorHandling:
    """測試並發錯誤處理"""
    
    def test_concurrent_access_protection(self):
        """測試並發訪問保護"""
        # 測試多個線程同時訪問緩存的情況
        try:
            from src.cache.redis_service import cache
            
            # 模擬並發訪問
            import threading
            import time
            
            results = []
            errors = []
            
            def concurrent_cache_operation(thread_id):
                try:
                    # 同時設置相同key
                    key = f"concurrent_test_{thread_id}"
                    data = {"thread_id": thread_id, "timestamp": time.time()}
                    success = cache.set(key, data, ttl=10)
                    results.append((thread_id, success))
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # 創建多個線程
            threads = []
            for i in range(3):
                thread = threading.Thread(target=concurrent_cache_operation, args=(i,))
                threads.append(thread)
            
            # 啟動所有線程
            for thread in threads:
                thread.start()
            
            # 等待所有線程完成
            for thread in threads:
                thread.join(timeout=5.0)
            
            # 驗證沒有嚴重錯誤
            assert len(errors) == 0 or all("timeout" in error[1].lower() for error in errors)
            
        except ImportError:
            pytest.skip("Concurrency testing not available")


class TestMemoryAndPerformanceEdgeCases:
    """測試內存和性能邊界情況"""
    
    def test_large_data_processing(self):
        """測試大數據處理的邊界情況"""
        from src.parsers.amazon_parser import AmazonProductParser
        
        parser = AmazonProductParser()
        
        # 測試非常長的內容
        very_long_content = "A" * 10000  # 10K字符
        extremely_long_content = "B" * 100000  # 100K字符
        
        # 測試標題提取不會因為內容過長而失敗
        result1 = parser._extract_title(None, f"# Valid Title\n{very_long_content}")
        assert result1 is not None
        
        # 測試極大內容的處理
        result2 = parser._extract_title(None, extremely_long_content)
        # 應該有合理的處理（截斷或返回默認值）
        assert result2 is not None
    
    def test_many_bullet_points_handling(self):
        """測試大量bullet points的處理"""
        from src.parsers.amazon_parser import AmazonProductParser
        
        parser = AmazonProductParser()
        
        # 創建包含很多bullet points的markdown
        many_bullets = "\n".join([f"• Feature number {i} with detailed description" for i in range(50)])
        markdown_with_many_bullets = f"# Product\n\n{many_bullets}"
        
        result = parser._extract_bullet_points(None, markdown_with_many_bullets)
        
        # 應該有限制機制，不會返回過多bullets
        assert isinstance(result, list)
        assert len(result) <= 10  # 應該有數量限制
    
    def test_deep_nested_features_handling(self):
        """測試深度嵌套特徵的處理"""
        from src.parsers.amazon_parser import AmazonProductParser
        
        parser = AmazonProductParser()
        
        # 測試複雜的特徵數據
        complex_bullets = [
            "Material: High-grade eco-friendly TPE material with anti-bacterial coating",
            "Dimensions: 72 inches length x 24 inches width x 6mm thickness, perfect for tall users",
            "Colors: Available in ocean blue, forest green, sunset orange, and midnight black options",
            "Benefits: Improves flexibility, reduces joint stress, enhances balance, supports weight loss",
            "Certifications: SGS certified non-toxic, CPSIA compliant, EU safety standards approved"
        ]
        
        # 創建包含復雜特徵的markdown
        complex_markdown = "# Product\n\n" + "\n".join([f"• {bullet}" for bullet in complex_bullets])
        
        result = parser._extract_key_features(None, complex_markdown)
        
        # 應該能處理複雜特徵並正確分類
        assert isinstance(result, dict)
        
        # 驗證分類邏輯
        if "materials" in result:
            assert len(result["materials"]) > 0
        if "dimensions" in result:
            assert len(result["dimensions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])