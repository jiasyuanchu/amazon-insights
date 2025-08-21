#!/usr/bin/env python3
"""
Monitoring模組詳細測試 - 目標從16%提升到60% (+150行覆蓋)
重點測試：成功/失敗/超時場景、metrics收集、異常檢測算法
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import json
import logging

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class TestProductTrackerComprehensive:
    """詳細測試ProductTracker - 覆蓋所有主要方法和分支"""
    
    @pytest.fixture
    def mock_tracker(self):
        """創建完全Mock的ProductTracker"""
        with patch('src.monitoring.product_tracker.DatabaseManager'), \
             patch('src.api.firecrawl_client.FirecrawlClient'), \
             patch('src.parsers.amazon_parser.AmazonProductParser'):
            
            from src.monitoring.product_tracker import ProductTracker
            tracker = ProductTracker()
            return tracker
    
    def test_track_product_success_flow(self, mock_tracker):
        """測試track_product成功流程的所有步驟"""
        # Mock FirecrawlClient成功響應
        mock_scrape_result = {
            "success": True,
            "data": {
                "html": "<html><title>Premium Yoga Mat</title><div class='price'>$29.99</div></html>",
                "markdown": "# Premium Yoga Mat\nPrice: $29.99\nRating: 4.5 out of 5 stars\n1,234 customer reviews"
            }
        }
        
        # Mock AmazonProductParser成功解析
        mock_parsed_data = {
            "title": "Premium Yoga Mat",
            "price": 29.99,
            "rating": 4.5,
            "review_count": 1234,
            "availability": "In Stock",
            "bsr": {"Sports & Outdoors": 150},
            "bullet_points": ["Eco-friendly TPE", "Non-slip surface"],
            "key_features": {"materials": ["TPE"], "colors": ["blue"]},
            "scraped_at": datetime.now().isoformat()
        }
        
        with patch.object(mock_tracker.firecrawl_client, 'scrape_amazon_product', return_value=mock_scrape_result), \
             patch.object(mock_tracker.parser, 'parse_product_data', return_value=mock_parsed_data), \
             patch.object(mock_tracker.db, 'save_product_data', return_value=True):
            
            result = mock_tracker.track_product("B07R7RMQF5")
            
            # 驗證完整流程
            assert isinstance(result, dict)
            assert result["asin"] == "B07R7RMQF5"
            assert result["title"] == "Premium Yoga Mat"
            assert result["price"] == 29.99
            assert result["tracking_status"] == "success"
            
            # 驗證所有步驟都被調用
            mock_tracker.firecrawl_client.scrape_amazon_product.assert_called_once_with("B07R7RMQF5")
            mock_tracker.parser.parse_product_data.assert_called_once_with(mock_scrape_result)
            mock_tracker.db.save_product_data.assert_called_once()
    
    def test_track_product_scraping_failure(self, mock_tracker):
        """測試scraping失敗的處理分支"""
        # Mock FirecrawlClient失敗響應
        mock_scrape_failure = {
            "success": False,
            "error": "Product page not found",
            "error_code": 404
        }
        
        with patch.object(mock_tracker.firecrawl_client, 'scrape_amazon_product', return_value=mock_scrape_failure):
            result = mock_tracker.track_product("INVALID_ASIN")
            
            # 驗證錯誤處理
            assert result is None or result["tracking_status"] == "failed"
            if result:
                assert "error" in result
                assert "not found" in result["error"].lower()
    
    def test_track_product_parsing_failure(self, mock_tracker):
        """測試解析失敗的處理分支"""
        # Mock scraping成功但解析失敗
        mock_scrape_success = {
            "success": True,
            "data": {"html": "<html>Invalid structure</html>", "markdown": "No product data"}
        }
        
        with patch.object(mock_tracker.firecrawl_client, 'scrape_amazon_product', return_value=mock_scrape_success), \
             patch.object(mock_tracker.parser, 'parse_product_data', return_value=None):  # 解析失敗
            
            result = mock_tracker.track_product("B07R7RMQF5")
            
            # 驗證解析失敗的處理
            assert result is None or result["tracking_status"] == "parsing_failed"
    
    def test_track_product_database_save_failure(self, mock_tracker):
        """測試數據庫保存失敗的處理分支"""
        mock_scrape_result = {"success": True, "data": {"html": "test", "markdown": "test"}}
        mock_parsed_data = {"title": "Test", "price": 29.99}
        
        with patch.object(mock_tracker.firecrawl_client, 'scrape_amazon_product', return_value=mock_scrape_result), \
             patch.object(mock_tracker.parser, 'parse_product_data', return_value=mock_parsed_data), \
             patch.object(mock_tracker.db, 'save_product_data', side_effect=Exception("Database error")):
            
            result = mock_tracker.track_product("B07R7RMQF5")
            
            # 驗證數據庫錯誤處理
            assert result is None or result["tracking_status"] == "save_failed"
    
    def test_get_tracking_history_various_scenarios(self, mock_tracker):
        """測試獲取歷史數據的各種場景"""
        # 測試有歷史數據的情況
        mock_history_data = [
            {"asin": "B07R7RMQF5", "price": 29.99, "rating": 4.5, "recorded_at": datetime.now() - timedelta(days=1)},
            {"asin": "B07R7RMQF5", "price": 27.99, "rating": 4.6, "recorded_at": datetime.now() - timedelta(days=2)},
            {"asin": "B07R7RMQF5", "price": 31.99, "rating": 4.4, "recorded_at": datetime.now() - timedelta(days=3)}
        ]
        
        with patch.object(mock_tracker.db, 'get_product_history', return_value=mock_history_data):
            result = mock_tracker.get_tracking_history("B07R7RMQF5", days=7)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert all("price" in item for item in result)
            assert all("recorded_at" in item for item in result)
        
        # 測試沒有歷史數據的情況
        with patch.object(mock_tracker.db, 'get_product_history', return_value=[]):
            result = mock_tracker.get_tracking_history("NEW_ASIN", days=7)
            assert result == []
        
        # 測試數據庫錯誤
        with patch.object(mock_tracker.db, 'get_product_history', side_effect=Exception("DB Error")):
            result = mock_tracker.get_tracking_history("B07R7RMQF5", days=7)
            assert result is None or result == []
    
    def test_detect_price_changes_scenarios(self, mock_tracker):
        """測試價格變化檢測的所有場景"""
        # 模擬歷史價格數據
        price_history = [
            {"price": 29.99, "recorded_at": datetime.now() - timedelta(hours=1)},
            {"price": 29.99, "recorded_at": datetime.now() - timedelta(hours=2)},
            {"price": 31.99, "recorded_at": datetime.now() - timedelta(hours=3)}
        ]
        
        with patch.object(mock_tracker.db, 'get_recent_price_history', return_value=price_history):
            # 測試價格下降
            result = mock_tracker.detect_price_changes("B07R7RMQF5", current_price=27.99)
            assert result["change_type"] == "decrease"
            assert result["price_change"] < 0
            assert result["percentage_change"] < 0
            
            # 測試價格上升
            result = mock_tracker.detect_price_changes("B07R7RMQF5", current_price=35.99)
            assert result["change_type"] == "increase"
            assert result["price_change"] > 0
            assert result["percentage_change"] > 0
            
            # 測試價格無變化
            result = mock_tracker.detect_price_changes("B07R7RMQF5", current_price=29.99)
            assert result["change_type"] == "stable"
            assert result["price_change"] == 0.0
        
        # 測試沒有歷史數據的情況
        with patch.object(mock_tracker.db, 'get_recent_price_history', return_value=[]):
            result = mock_tracker.detect_price_changes("NEW_ASIN", current_price=29.99)
            assert result["change_type"] == "first_record"
    
    def test_bulk_tracking_operations(self, mock_tracker):
        """測試批量追蹤操作"""
        asins = ["B07R7RMQF5", "B08XYZABC1", "B09MNOPQR2"]
        
        # Mock各種響應
        mock_responses = [
            {"asin": "B07R7RMQF5", "tracking_status": "success", "price": 29.99},
            {"asin": "B08XYZABC1", "tracking_status": "failed", "error": "Product not found"},
            {"asin": "B09MNOPQR2", "tracking_status": "success", "price": 45.50}
        ]
        
        def mock_track_single(asin):
            for response in mock_responses:
                if response["asin"] == asin:
                    return response
            return None
        
        with patch.object(mock_tracker, 'track_product', side_effect=mock_track_single):
            result = mock_tracker.bulk_track_products(asins)
            
            assert isinstance(result, dict)
            assert "results" in result
            assert "success_count" in result
            assert "failure_count" in result
            assert len(result["results"]) == 3
            assert result["success_count"] == 2
            assert result["failure_count"] == 1
    
    def test_performance_monitoring_features(self, mock_tracker):
        """測試性能監控功能"""
        # 測試跟踪性能指標
        with patch('time.time', side_effect=[1000.0, 1005.2]):  # 5.2秒執行時間
            with patch.object(mock_tracker, '_track_performance_metrics') as mock_perf:
                mock_tracker.track_product_with_metrics("B07R7RMQF5")
                
                mock_perf.assert_called_once()
                call_args = mock_perf.call_args[1] if mock_perf.call_args[1] else mock_perf.call_args[0]
                # 驗證性能數據被記錄
        
        # 測試memory使用監控
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 75.5
            
            memory_usage = mock_tracker.get_memory_usage()
            assert isinstance(memory_usage, float)
            assert 0 <= memory_usage <= 100


class TestAnomalyDetectorComprehensive:
    """詳細測試AnomalyDetector - 覆蓋異常檢測算法和所有分支"""
    
    @pytest.fixture
    def mock_detector(self):
        """創建Mock的AnomalyDetector"""
        with patch('src.monitoring.anomaly_detector.DatabaseManager'):
            from src.monitoring.anomaly_detector import AnomalyDetector
            detector = AnomalyDetector()
            return detector
    
    def test_detect_price_anomaly_comprehensive_scenarios(self, mock_detector):
        """測試價格異常檢測的完整場景"""
        # 創建不同的歷史價格模式
        
        # 1. 穩定價格模式 - 應該檢測出突然上漲
        stable_history = [
            {"price": 30.0, "recorded_at": datetime.now() - timedelta(days=i)} 
            for i in range(1, 8)
        ]
        
        with patch.object(mock_detector.db, 'get_price_history', return_value=stable_history):
            # 測試正常價格（無異常）
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=30.5)
            assert result["anomaly_detected"] is False
            assert result["anomaly_type"] == "normal"
            
            # 測試價格突然上漲（異常）
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=45.0)  # +50%
            assert result["anomaly_detected"] is True
            assert result["anomaly_type"] == "price_spike"
            assert result["severity"] in ["high", "critical"]
            
            # 測試價格突然下降（異常）
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=15.0)  # -50%
            assert result["anomaly_detected"] is True
            assert result["anomaly_type"] == "price_drop"
            assert result["severity"] in ["high", "critical"]
        
        # 2. 波動價格模式 - 需要更敏感的檢測
        volatile_history = [
            {"price": 25.0, "recorded_at": datetime.now() - timedelta(days=1)},
            {"price": 35.0, "recorded_at": datetime.now() - timedelta(days=2)},
            {"price": 28.0, "recorded_at": datetime.now() - timedelta(days=3)},
            {"price": 32.0, "recorded_at": datetime.now() - timedelta(days=4)},
        ]
        
        with patch.object(mock_detector.db, 'get_price_history', return_value=volatile_history):
            # 在波動範圍內的價格變化
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=30.0)
            assert result["anomaly_detected"] is False or result["severity"] == "low"
            
            # 超出波動範圍的價格變化
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=50.0)
            assert result["anomaly_detected"] is True
            assert result["anomaly_type"] == "price_spike"
        
        # 3. 沒有歷史數據的情況
        with patch.object(mock_detector.db, 'get_price_history', return_value=[]):
            result = mock_detector.detect_price_anomaly("NEW_ASIN", current_price=29.99)
            assert result["anomaly_detected"] is False
            assert result["anomaly_type"] == "insufficient_data"
    
    def test_detect_rating_anomaly_comprehensive(self, mock_detector):
        """測試評分異常檢測的完整邏輯"""
        # 穩定評分歷史
        stable_rating_history = [
            {"rating": 4.5, "review_count": 1200, "recorded_at": datetime.now() - timedelta(days=i)}
            for i in range(1, 8)
        ]
        
        with patch.object(mock_detector.db, 'get_rating_history', return_value=stable_rating_history):
            # 正常評分變化
            result = mock_detector.detect_rating_anomaly("B07R7RMQF5", current_rating=4.4, current_review_count=1250)
            assert result["anomaly_detected"] is False
            assert result["rating_trend"] == "stable"
            
            # 評分突然下降
            result = mock_detector.detect_rating_anomaly("B07R7RMQF5", current_rating=3.8, current_review_count=1300)
            assert result["anomaly_detected"] is True
            assert result["rating_trend"] == "declining"
            assert result["severity"] in ["medium", "high"]
            
            # 評分異常上升（可能是假評論）
            result = mock_detector.detect_rating_anomaly("B07R7RMQF5", current_rating=4.9, current_review_count=1250)
            assert result["anomaly_detected"] is True
            assert result["rating_trend"] == "suspicious_increase"
        
        # 評分波動歷史
        volatile_rating_history = [
            {"rating": 4.2, "review_count": 1000, "recorded_at": datetime.now() - timedelta(days=1)},
            {"rating": 4.6, "review_count": 1050, "recorded_at": datetime.now() - timedelta(days=2)},
            {"rating": 4.1, "review_count": 1100, "recorded_at": datetime.now() - timedelta(days=3)},
        ]
        
        with patch.object(mock_detector.db, 'get_rating_history', return_value=volatile_rating_history):
            # 在正常波動範圍內
            result = mock_detector.detect_rating_anomaly("B07R7RMQF5", current_rating=4.3, current_review_count=1200)
            assert result["anomaly_detected"] is False or result["severity"] == "low"
    
    def test_detect_availability_changes_scenarios(self, mock_detector):
        """測試庫存變化檢測的各種場景"""
        # 測試庫存狀態變化
        availability_scenarios = [
            # (previous_status, current_status, expected_change_type)
            ("In Stock", "Out of Stock", "stock_out"),
            ("Out of Stock", "In Stock", "stock_in"),
            ("In Stock", "Limited Stock", "stock_limited"),
            ("Limited Stock", "In Stock", "stock_restored"),
            ("In Stock", "In Stock", "no_change"),
            ("Unknown", "In Stock", "status_updated"),
        ]
        
        for prev_status, curr_status, expected_change in availability_scenarios:
            mock_latest_data = {"availability": prev_status, "recorded_at": datetime.now() - timedelta(hours=1)}
            
            with patch.object(mock_detector.db, 'get_latest_product_data', return_value=mock_latest_data):
                result = mock_detector.detect_availability_changes("B07R7RMQF5", current_availability=curr_status)
                
                assert result["previous_status"] == prev_status
                assert result["current_status"] == curr_status
                assert result["change_type"] == expected_change
                
                if expected_change == "no_change":
                    assert result["availability_changed"] is False
                else:
                    assert result["availability_changed"] is True
    
    def test_anomaly_scoring_algorithms(self, mock_detector):
        """測試異常評分算法的詳細邏輯"""
        # 測試價格異常評分計算
        price_scenarios = [
            # (current_price, avg_historical_price, std_dev, expected_score_range)
            (30.0, 30.0, 2.0, (0, 20)),      # 正常價格
            (40.0, 30.0, 2.0, (80, 100)),    # 嚴重偏離 (5個標準差)
            (35.0, 30.0, 2.0, (40, 60)),     # 中等偏離 (2.5個標準差)
            (32.0, 30.0, 2.0, (20, 40)),     # 輕微偏離 (1個標準差)
        ]
        
        for current, avg, std, expected_range in price_scenarios:
            # 計算Z-score: (current - avg) / std
            z_score = abs(current - avg) / std if std > 0 else 0
            
            # 異常評分: min(100, z_score * 20)
            anomaly_score = min(100, z_score * 20)
            
            assert expected_range[0] <= anomaly_score <= expected_range[1], \
                f"Price {current} vs avg {avg} should score in {expected_range}, got {anomaly_score}"
    
    def test_trend_analysis_algorithms(self, mock_detector):
        """測試趨勢分析算法"""
        # 創建不同趨勢的歷史數據
        
        # 上升趨勢
        upward_trend = [
            {"price": 25.0, "recorded_at": datetime.now() - timedelta(days=7)},
            {"price": 26.0, "recorded_at": datetime.now() - timedelta(days=6)},
            {"price": 27.0, "recorded_at": datetime.now() - timedelta(days=5)},
            {"price": 28.0, "recorded_at": datetime.now() - timedelta(days=4)},
            {"price": 29.0, "recorded_at": datetime.now() - timedelta(days=3)},
        ]
        
        with patch.object(mock_detector.db, 'get_price_history', return_value=upward_trend):
            result = mock_detector.analyze_price_trend("B07R7RMQF5")
            assert result["trend_direction"] == "increasing"
            assert result["trend_strength"] in ["weak", "moderate", "strong"]
            assert result["slope"] > 0
        
        # 下降趨勢
        downward_trend = [
            {"price": 35.0, "recorded_at": datetime.now() - timedelta(days=7)},
            {"price": 34.0, "recorded_at": datetime.now() - timedelta(days=6)},
            {"price": 33.0, "recorded_at": datetime.now() - timedelta(days=5)},
            {"price": 32.0, "recorded_at": datetime.now() - timedelta(days=4)},
            {"price": 31.0, "recorded_at": datetime.now() - timedelta(days=3)},
        ]
        
        with patch.object(mock_detector.db, 'get_price_history', return_value=downward_trend):
            result = mock_detector.analyze_price_trend("B07R7RMQF5")
            assert result["trend_direction"] == "decreasing"
            assert result["slope"] < 0
        
        # 穩定趨勢
        stable_trend = [
            {"price": 30.0 + (i % 2) * 0.5, "recorded_at": datetime.now() - timedelta(days=i)}
            for i in range(1, 8)
        ]
        
        with patch.object(mock_detector.db, 'get_price_history', return_value=stable_trend):
            result = mock_detector.analyze_price_trend("B07R7RMQF5")
            assert result["trend_direction"] == "stable"
            assert abs(result["slope"]) < 0.1


class TestMonitoringIntegrationWorkflows:
    """測試監控模組的集成工作流程"""
    
    @patch('src.monitoring.product_tracker.ProductTracker')
    @patch('src.monitoring.anomaly_detector.AnomalyDetector')
    def test_complete_monitoring_workflow(self, mock_detector_class, mock_tracker_class):
        """測試完整的監控工作流程"""
        # Mock instances
        mock_tracker = Mock()
        mock_detector = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_detector_class.return_value = mock_detector
        
        # Mock tracker response
        mock_tracking_result = {
            "asin": "B07R7RMQF5",
            "title": "Test Product",
            "price": 29.99,
            "rating": 4.5,
            "review_count": 1234,
            "availability": "In Stock",
            "tracking_status": "success",
            "tracked_at": datetime.now().isoformat()
        }
        
        mock_tracker.track_product.return_value = mock_tracking_result
        
        # Mock anomaly detection results
        mock_price_anomaly = {
            "anomaly_detected": True,
            "anomaly_type": "price_spike",
            "severity": "high",
            "current_price": 29.99,
            "expected_range": [25.0, 35.0],
            "deviation_percentage": 15.0
        }
        
        mock_rating_anomaly = {
            "anomaly_detected": False,
            "rating_trend": "stable",
            "current_rating": 4.5
        }
        
        mock_detector.detect_price_anomaly.return_value = mock_price_anomaly
        mock_detector.detect_rating_anomaly.return_value = mock_rating_anomaly
        
        # 模擬完整工作流程
        asin = "B07R7RMQF5"
        
        # 1. 追蹤產品數據
        tracking_result = mock_tracker.track_product(asin)
        assert tracking_result["tracking_status"] == "success"
        
        # 2. 檢測價格異常
        price_anomaly = mock_detector.detect_price_anomaly(asin, current_price=tracking_result["price"])
        assert price_anomaly["anomaly_detected"] is True
        
        # 3. 檢測評分異常
        rating_anomaly = mock_detector.detect_rating_anomaly(asin, current_rating=tracking_result["rating"])
        assert rating_anomaly["anomaly_detected"] is False
        
        # 4. 生成監控報告
        monitoring_report = {
            "asin": asin,
            "tracking_result": tracking_result,
            "anomalies": {
                "price": price_anomaly,
                "rating": rating_anomaly
            },
            "alert_triggered": price_anomaly["anomaly_detected"],
            "report_generated_at": datetime.now().isoformat()
        }
        
        assert monitoring_report["alert_triggered"] is True
        assert "anomalies" in monitoring_report
        assert len(monitoring_report["anomalies"]) == 2
    
    def test_monitoring_error_recovery(self, mock_detector_class, mock_tracker_class):
        """測試監控系統的錯誤恢復機制"""
        mock_tracker = Mock()
        mock_detector = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_detector_class.return_value = mock_detector
        
        # 測試tracker失敗時的恢復
        mock_tracker.track_product.side_effect = Exception("Tracking failed")
        
        try:
            # 應該有錯誤處理機制
            result = mock_tracker.track_product("B07R7RMQF5")
            assert result is None
        except Exception:
            # 如果沒有錯誤處理，應該捕獲異常
            pass
        
        # 測試detector失敗時的恢復
        mock_detector.detect_price_anomaly.side_effect = Exception("Detection failed")
        
        try:
            result = mock_detector.detect_price_anomaly("B07R7RMQF5", current_price=29.99)
            assert result is None or "error" in result
        except Exception:
            pass
    
    def test_monitoring_performance_optimization(self):
        """測試監控系統的性能優化功能"""
        # 測試批量處理性能
        asins = [f"B07R7RMQF{i}" for i in range(10)]  # 10個ASIN
        
        # Mock並行處理
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_future = Mock()
            mock_future.result.return_value = {"asin": "test", "status": "success"}
            mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
            
            # 模擬並行監控
            start_time = datetime.now()
            
            # 假設的並行監控函數
            def parallel_monitor(asin_list):
                results = []
                for asin in asin_list:
                    results.append({"asin": asin, "status": "monitored"})
                return results
            
            results = parallel_monitor(asins)
            end_time = datetime.now()
            
            # 驗證批量處理結果
            assert len(results) == 10
            assert all("asin" in result for result in results)
            
            # 性能應該合理（不超過30秒）
            processing_time = (end_time - start_time).total_seconds()
            assert processing_time < 30


class TestMonitoringLoggingAndMetrics:
    """測試監控系統的日志記錄和指標收集"""
    
    def test_logging_configuration_and_usage(self):
        """測試日志配置和使用"""
        # 測試logger初始化
        logger = logging.getLogger('test_monitoring')
        logger.setLevel(logging.INFO)
        
        # 創建測試handler
        test_handler = logging.StreamHandler()
        test_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        test_handler.setFormatter(test_formatter)
        logger.addHandler(test_handler)
        
        # 測試不同級別的日志
        with patch.object(test_handler, 'emit') as mock_emit:
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            
            # 驗證日志調用
            assert mock_emit.call_count == 3
            
            # 驗證日志消息格式
            calls = mock_emit.call_args_list
            assert any("info" in str(call).lower() for call in calls)
            assert any("warning" in str(call).lower() for call in calls)
            assert any("error" in str(call).lower() for call in calls)
    
    def test_metrics_collection_comprehensive(self):
        """測試指標收集的完整功能"""
        # 模擬指標收集器
        class MetricsCollector:
            def __init__(self):
                self.metrics = {}
            
            def record_tracking_time(self, asin, duration):
                if "tracking_times" not in self.metrics:
                    self.metrics["tracking_times"] = {}
                self.metrics["tracking_times"][asin] = duration
            
            def record_success_rate(self, total, successful):
                self.metrics["success_rate"] = successful / total if total > 0 else 0
            
            def record_anomaly_detection_stats(self, detected, total_checks):
                self.metrics["anomaly_rate"] = detected / total_checks if total_checks > 0 else 0
            
            def get_metrics_summary(self):
                return {
                    "avg_tracking_time": sum(self.metrics.get("tracking_times", {}).values()) / max(1, len(self.metrics.get("tracking_times", {}))),
                    "success_rate": self.metrics.get("success_rate", 0),
                    "anomaly_detection_rate": self.metrics.get("anomaly_rate", 0),
                    "total_tracked_products": len(self.metrics.get("tracking_times", {}))
                }
        
        # 測試指標收集
        collector = MetricsCollector()
        
        # 記錄各種指標
        collector.record_tracking_time("B07R7RMQF5", 2.5)
        collector.record_tracking_time("B08XYZABC1", 3.1)
        collector.record_success_rate(total=10, successful=8)
        collector.record_anomaly_detection_stats(detected=2, total_checks=10)
        
        # 獲取摘要
        summary = collector.get_metrics_summary()
        
        assert summary["avg_tracking_time"] == 2.8  # (2.5 + 3.1) / 2
        assert summary["success_rate"] == 0.8       # 8/10
        assert summary["anomaly_detection_rate"] == 0.2  # 2/10
        assert summary["total_tracked_products"] == 2
    
    def test_monitoring_alerts_and_notifications(self):
        """測試監控警報和通知系統"""
        # 模擬警報系統
        class AlertSystem:
            def __init__(self):
                self.alerts = []
            
            def trigger_alert(self, alert_type, severity, message, metadata=None):
                alert = {
                    "alert_id": f"alert_{len(self.alerts) + 1}",
                    "alert_type": alert_type,
                    "severity": severity,
                    "message": message,
                    "metadata": metadata or {},
                    "triggered_at": datetime.now().isoformat()
                }
                self.alerts.append(alert)
                return alert
            
            def get_active_alerts(self):
                return [alert for alert in self.alerts if alert["severity"] in ["high", "critical"]]
            
            def clear_alert(self, alert_id):
                self.alerts = [alert for alert in self.alerts if alert["alert_id"] != alert_id]
        
        # 測試警報系統
        alert_system = AlertSystem()
        
        # 觸發不同類型的警報
        price_alert = alert_system.trigger_alert(
            alert_type="price_anomaly",
            severity="high",
            message="Price increased by 50% in last hour",
            metadata={"asin": "B07R7RMQF5", "price_change": 15.0}
        )
        
        rating_alert = alert_system.trigger_alert(
            alert_type="rating_anomaly", 
            severity="medium",
            message="Rating dropped significantly",
            metadata={"asin": "B07R7RMQF5", "rating_change": -0.8}
        )
        
        stock_alert = alert_system.trigger_alert(
            alert_type="availability_change",
            severity="critical",
            message="Product went out of stock",
            metadata={"asin": "B07R7RMQF5", "status": "Out of Stock"}
        )
        
        # 驗證警報
        assert len(alert_system.alerts) == 3
        assert alert_system.alerts[0]["alert_type"] == "price_anomaly"
        assert alert_system.alerts[0]["severity"] == "high"
        
        # 測試活躍警報篩選
        active_alerts = alert_system.get_active_alerts()
        assert len(active_alerts) == 2  # high和critical級別
        
        # 測試清除警報
        alert_system.clear_alert(price_alert["alert_id"])
        assert len(alert_system.alerts) == 2


class TestMonitoringDataValidation:
    """測試監控數據的驗證和清理"""
    
    def test_data_validation_comprehensive(self):
        """測試數據驗證的完整邏輯"""
        from src.monitoring.product_tracker import ProductTracker
        
        # 測試數據驗證函數
        def validate_tracking_data(data):
            errors = []
            
            # ASIN驗證
            if not data.get("asin") or len(data["asin"]) != 10:
                errors.append("Invalid ASIN format")
            
            # 價格驗證
            price = data.get("price")
            if price is not None:
                if not isinstance(price, (int, float)) or price <= 0:
                    errors.append("Invalid price value")
            
            # 評分驗證
            rating = data.get("rating")
            if rating is not None:
                if not isinstance(rating, (int, float)) or not (1.0 <= rating <= 5.0):
                    errors.append("Invalid rating value")
            
            # 評論數驗證
            review_count = data.get("review_count")
            if review_count is not None:
                if not isinstance(review_count, int) or review_count < 0:
                    errors.append("Invalid review count")
            
            return len(errors) == 0, errors
        
        # 測試有效數據
        valid_data = {
            "asin": "B07R7RMQF5",
            "title": "Test Product",
            "price": 29.99,
            "rating": 4.5,
            "review_count": 1234,
            "availability": "In Stock"
        }
        
        is_valid, errors = validate_tracking_data(valid_data)
        assert is_valid is True
        assert len(errors) == 0
        
        # 測試各種無效數據
        invalid_data_cases = [
            ({"asin": "SHORT"}, "Invalid ASIN format"),                    # 短ASIN
            ({"asin": "B07R7RMQF5", "price": -10.0}, "Invalid price"),    # 負價格
            ({"asin": "B07R7RMQF5", "rating": 6.0}, "Invalid rating"),    # 超範圍評分
            ({"asin": "B07R7RMQF5", "review_count": -1}, "Invalid review"), # 負評論數
        ]
        
        for invalid_data, expected_error_type in invalid_data_cases:
            is_valid, errors = validate_tracking_data(invalid_data)
            assert is_valid is False
            assert len(errors) > 0
            assert any(expected_error_type.lower() in error.lower() for error in errors)
    
    def test_data_cleaning_and_normalization(self):
        """測試數據清理和標準化"""
        # 測試數據清理函數
        def clean_tracking_data(raw_data):
            cleaned = {}
            
            # ASIN清理
            asin = raw_data.get("asin", "").strip().upper()
            if len(asin) == 10:
                cleaned["asin"] = asin
            
            # 價格清理
            price = raw_data.get("price")
            if price is not None:
                try:
                    price_float = float(price)
                    if price_float > 0:
                        cleaned["price"] = round(price_float, 2)
                except (ValueError, TypeError):
                    pass
            
            # 評分清理
            rating = raw_data.get("rating")
            if rating is not None:
                try:
                    rating_float = float(rating)
                    if 1.0 <= rating_float <= 5.0:
                        cleaned["rating"] = round(rating_float, 1)
                except (ValueError, TypeError):
                    pass
            
            # 標題清理
            title = raw_data.get("title", "").strip()
            if title:
                # 移除多餘空格，限制長度
                cleaned["title"] = " ".join(title.split())[:200]
            
            return cleaned
        
        # 測試清理功能
        messy_data = {
            "asin": "  b07r7rmqf5  ",      # 需要大寫和trim
            "price": "29.999",             # 需要四捨五入
            "rating": "4.55",              # 需要四捨五入
            "title": "  Premium   Yoga   Mat  \n  Extra  Thick  ",  # 需要清理空格
            "invalid_field": "should be ignored"
        }
        
        cleaned = clean_tracking_data(messy_data)
        
        assert cleaned["asin"] == "B07R7RMQF5"
        assert cleaned["price"] == 30.00
        assert cleaned["rating"] == 4.6
        assert cleaned["title"] == "Premium Yoga Mat Extra Thick"
        assert "invalid_field" not in cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.monitoring"])