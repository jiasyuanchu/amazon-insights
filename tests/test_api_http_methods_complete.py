#!/usr/bin/env python3
"""
API HTTP方法完整測試 - 覆蓋所有GET/POST/PUT/DELETE端點
目標：深度測試API路由的所有HTTP方法和分支邏輯
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import asyncio

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class TestProductsAPIHTTPMethods:
    """測試Products API的所有HTTP方法"""
    
    @patch('src.monitoring.product_tracker.ProductTracker')
    def test_post_track_single_product_complete_flow(self, mock_tracker_class):
        """測試POST /track/{asin} 的完整流程"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # 測試成功場景
        mock_tracker.track_single_product.return_value = True
        mock_tracker.get_product_summary.return_value = {
            "asin": "B07R7RMQF5",
            "title": "Premium Yoga Mat",
            "current_price": 29.99,
            "current_rating": 4.5,
            "current_review_count": 1234,
            "bsr_data": {"Sports & Outdoors": 150},
            "availability": "In Stock",
            "price_trend": "stable",
            "last_updated": datetime.now().isoformat(),
            "history_count": 5
        }
        
        # 重新加載模組以使用mock
        import importlib
        import api.routes.products
        importlib.reload(api.routes.products)
        
        from api.routes.products import track_single_product
        
        # 執行POST請求邏輯
        async def test_success():
            result = await track_single_product("B07R7RMQF5")
            
            # 驗證TrackingResult結構
            assert hasattr(result, 'success')
            assert hasattr(result, 'message')
            assert hasattr(result, 'asin')
            assert hasattr(result, 'product_summary')
            
            assert result.success is True
            assert result.asin == "B07R7RMQF5"
            assert "Successfully tracked" in result.message
            assert result.product_summary is not None
            assert result.product_summary.title == "Premium Yoga Mat"
            
        asyncio.run(test_success())
        
        # 測試失敗場景
        mock_tracker.track_single_product.return_value = False
        
        async def test_failure():
            result = await track_single_product("FAILED_ASIN")
            
            assert result.success is False
            assert result.asin == "FAILED_ASIN"
            assert "Failed to track" in result.message
            assert result.product_summary is None
            
        asyncio.run(test_failure())
        
        # 測試摘要錯誤場景
        mock_tracker.track_single_product.return_value = True
        mock_tracker.get_product_summary.return_value = {"error": "Parsing failed"}
        
        async def test_summary_error():
            result = await track_single_product("B07R7RMQF5")
            
            assert result.success is False
            assert "Failed to get product summary" in result.message
            assert "Parsing failed" in result.message
            
        asyncio.run(test_summary_error())
    
    @patch('src.monitoring.product_tracker.ProductTracker')
    @patch('config.config.AMAZON_ASINS', ['B07R7RMQF5', 'B08XYZABC1'])
    def test_post_track_all_products_complete_flow(self, mock_tracker_class):
        """測試POST /track-all 的完整流程"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Mock批量追蹤結果
        mock_tracker.track_all_products.return_value = {
            "B07R7RMQF5": True,
            "B08XYZABC1": False
        }
        
        # Mock個別產品摘要
        def mock_get_summary(asin):
            if asin == "B07R7RMQF5":
                return {
                    "asin": asin,
                    "title": "Product 1",
                    "current_price": 29.99,
                    "current_rating": 4.5,
                    "current_review_count": 1234,
                    "bsr_data": {},
                    "availability": "In Stock", 
                    "price_trend": "stable",
                    "last_updated": datetime.now().isoformat(),
                    "history_count": 3
                }
            else:
                return {"error": "Failed to get summary"}
        
        mock_tracker.get_product_summary.side_effect = mock_get_summary
        
        import importlib
        import api.routes.products
        importlib.reload(api.routes.products)
        
        from api.routes.products import track_all_products
        
        async def test_batch_tracking():
            result = await track_all_products()
            
            # 驗證BatchTrackingResult結構
            assert hasattr(result, 'total_products')
            assert hasattr(result, 'successful_products')
            assert hasattr(result, 'failed_products')
            assert hasattr(result, 'results')
            
            assert result.total_products == 2
            assert result.successful_products == 1
            assert result.failed_products == 1
            assert len(result.results) == 2
            
            # 檢查成功的產品
            successful_results = [r for r in result.results if r.success]
            assert len(successful_results) == 1
            assert successful_results[0].asin == "B07R7RMQF5"
            assert successful_results[0].product_summary is not None
            
            # 檢查失敗的產品
            failed_results = [r for r in result.results if not r.success]
            assert len(failed_results) == 1
            assert failed_results[0].asin == "B08XYZABC1"
            assert failed_results[0].product_summary is None
            
        asyncio.run(test_batch_tracking())
    
    @patch('src.monitoring.product_tracker.ProductTracker')
    def test_get_product_history_complete_flow(self, mock_tracker_class):
        """測試GET /history/{asin} 的完整流程"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Mock歷史數據 - 成功場景
        mock_history_success = [
            {
                "asin": "B07R7RMQF5",
                "price": 29.99,
                "rating": 4.5,
                "review_count": 1230,
                "availability": "In Stock", 
                "recorded_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "asin": "B07R7RMQF5",
                "price": 27.99,
                "rating": 4.6,
                "review_count": 1234,
                "availability": "In Stock",
                "recorded_at": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "asin": "B07R7RMQF5",
                "price": 28.99,
                "rating": 4.6,
                "review_count": 1240,
                "availability": "In Stock",
                "recorded_at": datetime.now().isoformat()
            }
        ]
        
        mock_tracker.get_product_history.return_value = mock_history_success
        
        import importlib
        import api.routes.products
        importlib.reload(api.routes.products)
        
        from api.routes.products import get_product_history
        
        # 測試不同的days參數
        days_test_cases = [1, 7, 30, 90]
        
        for days in days_test_cases:
            async def test_history(test_days=days):
                result = await get_product_history("B07R7RMQF5", days=test_days)
                
                # 驗證PriceHistory結構
                assert hasattr(result, 'asin')
                assert hasattr(result, 'period_days')
                assert hasattr(result, 'history')
                
                assert result.asin == "B07R7RMQF5"
                assert result.period_days == test_days
                assert isinstance(result.history, list)
                assert len(result.history) == 3
                
                # 驗證歷史條目結構
                for entry in result.history:
                    assert hasattr(entry, 'price')
                    assert hasattr(entry, 'rating')
                    assert hasattr(entry, 'review_count')
                    assert hasattr(entry, 'availability')
                    assert hasattr(entry, 'recorded_at')
                
                return result
            
            result = asyncio.run(test_history())
            assert result.period_days == days
        
        # 測試無歷史數據場景
        mock_tracker.get_product_history.return_value = []
        
        async def test_no_history():
            result = await get_product_history("NEW_ASIN", days=30)
            
            assert result.asin == "NEW_ASIN"
            assert result.period_days == 30
            assert len(result.history) == 0
            
        asyncio.run(test_no_history())


class TestCompetitiveAPIHTTPMethods:
    """測試Competitive API的所有HTTP方法"""
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_get_competitive_groups_complete_flow(self, mock_manager_class):
        """測試GET /groups 的完整流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock競品組列表
        mock_groups = [
            Mock(
                id=1,
                name="Yoga Mats Analysis",
                main_product_asin="B07R7RMQF5",
                description="Analysis of yoga mat competitors",
                created_at=datetime.now() - timedelta(days=5),
                is_active=True,
                competitors_count=3
            ),
            Mock(
                id=2,
                name="Fitness Equipment Analysis", 
                main_product_asin="B08FITNESS1",
                description="Fitness equipment competitive analysis",
                created_at=datetime.now() - timedelta(days=2),
                is_active=True,
                competitors_count=5
            )
        ]
        
        mock_manager.get_all_competitive_groups.return_value = mock_groups
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import get_competitive_groups
        
        async def test_get_groups():
            result = await get_competitive_groups()
            
            # 驗證群組列表結構
            assert isinstance(result, list)
            assert len(result) == 2
            
            # 驗證第一個群組
            group1 = result[0]
            assert group1.id == 1
            assert group1.name == "Yoga Mats Analysis"
            assert group1.main_product_asin == "B07R7RMQF5"
            assert group1.is_active is True
            assert group1.competitors_count == 3
            
            # 驗證第二個群組
            group2 = result[1]
            assert group2.id == 2
            assert group2.competitors_count == 5
            
            return result
        
        result = asyncio.run(test_get_groups())
        assert len(result) == 2
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_get_competitive_group_by_id_flow(self, mock_manager_class):
        """測試GET /groups/{group_id} 的流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # 測試成功獲取群組
        mock_group = Mock()
        mock_group.id = 1
        mock_group.name = "Test Group"
        mock_group.main_product_asin = "B07R7RMQF5"
        mock_group.description = "Test description"
        mock_group.created_at = datetime.now()
        mock_group.is_active = True
        mock_group.competitors = [
            Mock(asin="B08COMP1", competitor_name="Competitor 1", priority=1),
            Mock(asin="B08COMP2", competitor_name="Competitor 2", priority=2)
        ]
        
        mock_manager.get_competitive_group.return_value = mock_group
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import get_competitive_group
        
        async def test_get_group_success():
            result = await get_competitive_group(1)
            
            # 驗證群組詳情
            assert result.id == 1
            assert result.name == "Test Group"
            assert result.main_product_asin == "B07R7RMQF5"
            assert len(result.competitors) == 2
            
            return result
        
        result = asyncio.run(test_get_group_success())
        assert result.id == 1
        
        # 測試群組不存在場景
        mock_manager.get_competitive_group.return_value = None
        
        from fastapi import HTTPException
        
        async def test_group_not_found():
            try:
                result = await get_competitive_group(999)
                assert result is None
            except HTTPException as e:
                assert e.status_code == 404
                assert "not found" in str(e.detail).lower()
        
        asyncio.run(test_group_not_found())
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_put_update_competitive_group_flow(self, mock_manager_class):
        """測試PUT /groups/{group_id} 的流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock更新成功
        mock_updated_group = Mock()
        mock_updated_group.id = 1
        mock_updated_group.name = "Updated Group Name"
        mock_updated_group.description = "Updated description"
        mock_updated_group.updated_at = datetime.now()
        
        mock_manager.update_competitive_group.return_value = mock_updated_group
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import update_competitive_group
        
        async def test_update_success():
            update_data = {
                "name": "Updated Group Name",
                "description": "Updated description"
            }
            
            result = await update_competitive_group(1, update_data)
            
            # 驗證更新結果
            assert result.id == 1
            assert result.name == "Updated Group Name"
            assert result.description == "Updated description"
            assert hasattr(result, 'updated_at')
            
            return result
        
        result = asyncio.run(test_update_success())
        assert result.name == "Updated Group Name"
        
        # 測試更新不存在的群組
        mock_manager.update_competitive_group.side_effect = ValueError("Group not found")
        
        from fastapi import HTTPException
        
        async def test_update_not_found():
            try:
                result = await update_competitive_group(999, {"name": "New Name"})
                assert result is None
            except HTTPException as e:
                assert e.status_code in [400, 404]
        
        asyncio.run(test_update_not_found())
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_delete_competitive_group_flow(self, mock_manager_class):
        """測試DELETE /groups/{group_id} 的流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # 測試刪除成功
        mock_manager.delete_competitive_group.return_value = True
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import delete_competitive_group
        
        async def test_delete_success():
            result = await delete_competitive_group(1)
            
            # DELETE成功通常返回204 No Content或確認消息
            assert result is None or result["status"] == "deleted"
            
        asyncio.run(test_delete_success())
        
        # 測試刪除不存在的群組
        mock_manager.delete_competitive_group.return_value = False
        
        from fastapi import HTTPException
        
        async def test_delete_not_found():
            try:
                result = await delete_competitive_group(999)
                assert result is None
            except HTTPException as e:
                assert e.status_code == 404
        
        asyncio.run(test_delete_not_found())
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_post_add_competitor_complete_flow(self, mock_manager_class):
        """測試POST /groups/{group_id}/competitors 的完整流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock添加競品成功
        mock_competitor = Mock()
        mock_competitor.id = 1
        mock_competitor.group_id = 1
        mock_competitor.asin = "B08COMPETITOR1"
        mock_competitor.competitor_name = "Premium Competitor"
        mock_competitor.priority = 1
        mock_competitor.is_active = True
        mock_competitor.added_at = datetime.now()
        
        mock_manager.add_competitor.return_value = mock_competitor
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import add_competitor
        from api.models.competitive_schemas import AddCompetitorRequest
        
        # 測試完整數據添加
        async def test_add_full_data():
            request = AddCompetitorRequest(
                asin="B08COMPETITOR1",
                competitor_name="Premium Competitor",
                priority=1
            )
            
            result = await add_competitor(1, request)
            
            # 驗證CompetitorInfo結構
            assert result.id == 1
            assert result.group_id == 1
            assert result.asin == "B08COMPETITOR1"
            assert result.competitor_name == "Premium Competitor"
            assert result.priority == 1
            assert result.is_active is True
            
            return result
        
        result = asyncio.run(test_add_full_data())
        assert result.asin == "B08COMPETITOR1"
        
        # 測試最小數據添加
        async def test_add_minimal_data():
            request = AddCompetitorRequest(asin="B08MINIMAL")
            
            result = await add_competitor(1, request)
            
            # 應該使用默認值
            assert result.asin == "B08MINIMAL"
            assert result.priority == 1  # 默認優先級
            
        # 重置mock以避免衝突
        mock_competitor.asin = "B08MINIMAL"
        asyncio.run(test_add_minimal_data())
        
        # 測試添加重複競品
        mock_manager.add_competitor.side_effect = ValueError("Competitor already exists")
        
        from fastapi import HTTPException
        
        async def test_add_duplicate():
            request = AddCompetitorRequest(asin="B08EXISTING")
            
            try:
                result = await add_competitor(1, request)
                assert result is None
            except HTTPException as e:
                assert e.status_code in [400, 409]  # Bad Request或Conflict
                assert "already exists" in str(e.detail).lower()
        
        asyncio.run(test_add_duplicate())
    
    @patch('src.competitive.manager.CompetitiveManager')
    def test_delete_competitor_flow(self, mock_manager_class):
        """測試DELETE /groups/{group_id}/competitors/{asin} 的流程"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # 測試刪除成功
        mock_manager.remove_competitor.return_value = True
        
        import importlib
        import api.routes.competitive
        importlib.reload(api.routes.competitive)
        
        from api.routes.competitive import remove_competitor
        
        async def test_remove_success():
            result = await remove_competitor(1, "B08COMPETITOR1")
            
            # 驗證刪除結果
            assert result is None or result["status"] == "removed"
            
        asyncio.run(test_remove_success())
        
        # 測試刪除不存在的競品
        mock_manager.remove_competitor.return_value = False
        
        from fastapi import HTTPException
        
        async def test_remove_not_found():
            try:
                result = await remove_competitor(1, "NONEXISTENT")
                assert result is None
            except HTTPException as e:
                assert e.status_code == 404
        
        asyncio.run(test_remove_not_found())


class TestSystemAPIHTTPMethods:
    """測試System API的所有HTTP方法"""
    
    @patch('redis.Redis')
    @patch('sqlalchemy.create_engine')
    @patch('requests.get')
    def test_get_health_check_comprehensive(self, mock_requests, mock_engine, mock_redis):
        """測試GET /health 的所有分支"""
        import importlib
        import api.routes.system
        importlib.reload(api.routes.system)
        
        from api.routes.system import health_check
        
        # 場景1：所有服務正常
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        mock_connection = Mock()
        mock_engine_instance.connect.return_value.__enter__.return_value = mock_connection
        
        mock_requests.return_value.status_code = 200
        
        async def test_all_healthy():
            result = await health_check()
            
            assert result["status"] == "healthy"
            assert result["checks"]["database"] is True
            assert result["checks"]["redis"] is True
            assert result["checks"]["external_apis"] is True
            
        asyncio.run(test_all_healthy())
        
        # 場景2：數據庫失敗
        mock_engine_instance.connect.side_effect = Exception("Database error")
        
        async def test_db_failure():
            result = await health_check()
            
            assert result["status"] in ["degraded", "unhealthy"]
            assert result["checks"]["database"] is False
            
        asyncio.run(test_db_failure())
        
        # 場景3：Redis失敗
        mock_engine_instance.connect.side_effect = None  # 重置數據庫
        mock_engine_instance.connect.return_value.__enter__.return_value = mock_connection
        mock_redis_instance.ping.side_effect = Exception("Redis error")
        
        async def test_redis_failure():
            result = await health_check()
            
            assert result["status"] in ["degraded", "unhealthy"]
            assert result["checks"]["redis"] is False
            
        asyncio.run(test_redis_failure())
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('time.time')
    def test_get_system_status_comprehensive(self, mock_time, mock_cpu, mock_memory):
        """測試GET /status 的完整系統狀態"""
        # Mock系統指標
        mock_memory.return_value.percent = 65.5
        mock_memory.return_value.total = 16 * 1024 * 1024 * 1024  # 16GB
        mock_memory.return_value.available = 5.5 * 1024 * 1024 * 1024  # 5.5GB
        
        mock_cpu.return_value = 45.2
        
        # Mock應用啟動時間
        app_start_time = 1640995200  # 2022-01-01 00:00:00
        current_time = app_start_time + 3600 * 24 * 2  # 2天後
        mock_time.return_value = current_time
        
        import importlib
        import api.routes.system
        importlib.reload(api.routes.system)
        
        from api.routes.system import get_system_status
        
        async def test_system_status():
            result = await get_system_status()
            
            # 驗證系統狀態結構
            assert "version" in result
            assert "uptime" in result
            assert "system_metrics" in result
            assert "api_metrics" in result
            
            # 驗證系統指標
            metrics = result["system_metrics"]
            assert "memory_usage_percent" in metrics
            assert "cpu_usage_percent" in metrics
            assert "memory_total_gb" in metrics
            assert "memory_available_gb" in metrics
            
            # 驗證數值範圍
            assert 0 <= metrics["memory_usage_percent"] <= 100
            assert 0 <= metrics["cpu_usage_percent"] <= 100
            assert metrics["memory_total_gb"] > 0
            
            return result
        
        result = asyncio.run(test_system_status())
        assert "system_metrics" in result
    
    @patch('src.monitoring.product_tracker.ProductTracker')
    @patch('src.cache.redis_service.cache')
    def test_post_system_test_comprehensive(self, mock_cache, mock_tracker_class):
        """測試POST /test 的完整系統測試"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Mock各種系統測試結果
        mock_tracker.test_tracking_functionality.return_value = {
            "status": "passed",
            "duration_ms": 150,
            "details": "Product tracking test completed successfully"
        }
        
        mock_cache.test_operations.return_value = {
            "status": "passed",
            "duration_ms": 50,
            "operations_tested": ["get", "set", "delete", "exists"],
            "details": "All cache operations working correctly"
        }
        
        import importlib
        import api.routes.system
        importlib.reload(api.routes.system)
        
        from api.routes.system import run_system_tests
        
        async def test_system_tests():
            result = await run_system_tests()
            
            # 驗證測試結果結構
            assert "test_id" in result
            assert "started_at" in result
            assert "tests" in result
            assert "overall_status" in result
            assert "total_duration_ms" in result
            
            # 驗證個別測試結果
            tests = result["tests"]
            assert "tracking_functionality" in tests
            assert "cache_operations" in tests
            
            # 驗證測試狀態
            assert tests["tracking_functionality"]["status"] == "passed"
            assert tests["cache_operations"]["status"] == "passed"
            assert result["overall_status"] == "all_passed"
            
            return result
        
        result = asyncio.run(test_system_tests())
        assert result["overall_status"] == "all_passed"


class TestCacheAPIHTTPMethods:
    """測試Cache API的所有HTTP方法"""
    
    @patch('src.cache.redis_service.cache')
    def test_get_cache_stats_detailed_flow(self, mock_cache):
        """測試GET /stats 的詳細流程"""
        # Mock詳細的緩存統計
        mock_stats = {
            "connection_info": {
                "connected": True,
                "redis_version": "7.0.0",
                "uptime_seconds": 86400
            },
            "memory_info": {
                "used_memory": "45.2MB",
                "used_memory_human": "45.2M",
                "max_memory": "512MB",
                "memory_fragmentation_ratio": 1.15
            },
            "performance_info": {
                "hit_rate": 0.85,
                "miss_rate": 0.15,
                "ops_per_sec": 120.5,
                "avg_response_time_ms": 2.3,
                "total_operations": 150000
            },
            "key_statistics": {
                "total_keys": 1250,
                "expired_keys": 45,
                "key_categories": {
                    "product:summary": 800,
                    "product:history": 250,
                    "competitive:analysis": 150,
                    "system:status": 50
                }
            }
        }
        
        mock_cache.get_detailed_stats.return_value = mock_stats
        
        import importlib
        import api.routes.cache
        importlib.reload(api.routes.cache)
        
        from api.routes.cache import get_cache_stats
        
        async def test_cache_stats():
            result = await get_cache_stats()
            
            # 驗證緩存統計結構
            assert "connection_info" in result
            assert "memory_info" in result
            assert "performance_info" in result
            assert "key_statistics" in result
            
            # 驗證連接信息
            conn_info = result["connection_info"]
            assert conn_info["connected"] is True
            assert "redis_version" in conn_info
            
            # 驗證性能信息
            perf_info = result["performance_info"]
            assert 0 <= perf_info["hit_rate"] <= 1
            assert 0 <= perf_info["miss_rate"] <= 1
            assert perf_info["ops_per_sec"] > 0
            
            # 驗證key統計
            key_stats = result["key_statistics"]
            assert key_stats["total_keys"] > 0
            assert isinstance(key_stats["key_categories"], dict)
            
            return result
        
        result = asyncio.run(test_cache_stats())
        assert result["performance_info"]["hit_rate"] == 0.85
    
    @patch('src.cache.redis_service.cache')
    def test_post_cache_operations_flow(self, mock_cache):
        """測試POST cache操作的各種流程"""
        import importlib
        import api.routes.cache
        importlib.reload(api.routes.cache)
        
        from api.routes.cache import clear_all_cache, clear_product_cache, warm_up_cache
        
        # 測試清理所有緩存
        mock_cache.flush_all.return_value = {"cleared_keys": 1250, "status": "success"}
        
        async def test_clear_all():
            result = await clear_all_cache()
            
            assert result["cleared_keys"] == 1250
            assert result["status"] == "success"
            assert "cleared_at" in result
            
        asyncio.run(test_clear_all())
        
        # 測試清理產品緩存
        mock_cache.clear_by_pattern.return_value = {"cleared_keys": 5, "pattern": "product:*:B07R7RMQF5"}
        
        async def test_clear_product():
            result = await clear_product_cache("B07R7RMQF5")
            
            assert result["cleared_keys"] == 5
            assert result["asin"] == "B07R7RMQF5"
            assert "cleared_at" in result
            
        asyncio.run(test_clear_product())
        
        # 測試緩存預熱
        mock_cache.warm_up.return_value = {
            "job_id": "warmup_001",
            "status": "started",
            "target_keys": 500,
            "estimated_duration": "5 minutes"
        }
        
        async def test_warm_up():
            warmup_request = {
                "categories": ["product:summary", "product:history"],
                "priority_asins": ["B07R7RMQF5", "B08XYZABC1"]
            }
            
            result = await warm_up_cache(warmup_request)
            
            assert "job_id" in result
            assert result["status"] == "started"
            assert result["target_keys"] == 500
            
        asyncio.run(test_warm_up())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.routes"])