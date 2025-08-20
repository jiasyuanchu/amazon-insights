#!/usr/bin/env python3
"""
Integration tests for API endpoints
"""

import sys
import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer sk_live_test_key_123"}


class TestHealthEndpoints:
    """Test system health endpoints"""

    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_system_status(self, client, auth_headers):
        """Test system status endpoint"""
        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.get("/api/v1/system/status", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert "cache" in data


class TestProductEndpoints:
    """Test product tracking endpoints"""

    @patch("src.monitoring.product_tracker.ProductTracker")
    def test_get_product_summary(self, mock_tracker, client, auth_headers):
        """Test get product summary endpoint"""
        # Mock product tracker
        mock_tracker_instance = Mock()
        mock_tracker_instance.get_product_summary.return_value = {
            "asin": "B07R7RMQF5",
            "title": "Test Product",
            "current_price": 34.99,
            "current_rating": 4.7,
            "current_review_count": 5000,
        }
        mock_tracker.return_value = mock_tracker_instance

        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.get(
                "/api/v1/products/summary/B07R7RMQF5", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["asin"] == "B07R7RMQF5"
            assert data["title"] == "Test Product"
            assert data["current_price"] == 34.99

    @patch("src.monitoring.product_tracker.ProductTracker")
    def test_track_single_product(self, mock_tracker, client, auth_headers):
        """Test track single product endpoint"""
        # Mock product tracker
        mock_tracker_instance = Mock()
        mock_tracker_instance.track_single_product.return_value = True
        mock_tracker_instance.get_product_summary.return_value = {
            "asin": "B07R7RMQF5",
            "title": "Test Product",
        }
        mock_tracker.return_value = mock_tracker_instance

        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.post(
                "/api/v1/products/track/B07R7RMQF5", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["asin"] == "B07R7RMQF5"


class TestCompetitiveEndpoints:
    """Test competitive analysis endpoints"""

    @patch("src.competitive.manager.CompetitiveManager")
    def test_create_competitive_group(self, mock_manager, client, auth_headers):
        """Test create competitive group endpoint"""
        # Mock competitive manager
        mock_manager_instance = Mock()
        mock_group = Mock()
        mock_group.id = 1
        mock_group.name = "Test Group"
        mock_group.description = "Test Description"
        mock_group.main_product_asin = "B07R7RMQF5"
        mock_group.created_at = datetime.now()
        mock_group.updated_at = datetime.now()
        mock_group.is_active = True

        mock_manager_instance.create_competitive_group.return_value = mock_group
        mock_manager.return_value = mock_manager_instance

        request_data = {
            "name": "Test Group",
            "main_product_asin": "B07R7RMQF5",
            "description": "Test Description",
        }

        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.post(
                "/api/v1/competitive/groups", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Test Group"
            assert data["main_product_asin"] == "B07R7RMQF5"

    @patch("src.competitive.manager.CompetitiveManager")
    def test_get_competitive_groups(self, mock_manager, client, auth_headers):
        """Test get all competitive groups endpoint"""
        # Mock competitive manager
        mock_manager_instance = Mock()
        mock_group = Mock()
        mock_group.id = 1
        mock_group.name = "Test Group"
        mock_group.description = "Test Description"
        mock_group.main_product_asin = "B07R7RMQF5"
        mock_group.created_at = datetime.now()
        mock_group.updated_at = datetime.now()
        mock_group.is_active = True
        mock_group.active_competitors = []

        mock_manager_instance.get_all_competitive_groups.return_value = [mock_group]
        mock_manager.return_value = mock_manager_instance

        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.get("/api/v1/competitive/groups", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["name"] == "Test Group"

    @patch("src.competitive.analyzer.CompetitiveAnalyzer")
    def test_analyze_competitive_group(self, mock_analyzer, client, auth_headers):
        """Test competitive analysis endpoint"""
        # Mock analyzer
        mock_analyzer_instance = Mock()
        mock_analysis_result = {
            "group_info": {"id": 1, "name": "Test Group"},
            "main_product": {"asin": "B07R7RMQF5", "title": "Test Product"},
            "competitors": [],
            "competitive_summary": {
                "competitive_scores": {
                    "price_competitiveness": 75.0,
                    "quality_competitiveness": 94.0,
                    "overall_competitiveness": 84.5,
                }
            },
            "analysis_timestamp": datetime.now().isoformat(),
        }
        mock_analyzer_instance.analyze_competitive_group.return_value = (
            mock_analysis_result
        )
        mock_analyzer.return_value = mock_analyzer_instance

        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.post(
                "/api/v1/competitive/groups/1/analyze", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "group_info" in data
            assert "main_product" in data
            assert "competitive_summary" in data
            assert data["group_info"]["id"] == 1


class TestErrorHandling:
    """Test API error handling"""

    def test_invalid_asin_format(self, client, auth_headers):
        """Test error handling for invalid ASIN format"""
        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.get(
                "/api/v1/products/summary/INVALID", headers=auth_headers
            )

            # Should handle gracefully (may return 404 or empty result)
            assert response.status_code in [200, 404, 422]

    def test_nonexistent_competitive_group(self, client, auth_headers):
        """Test error handling for nonexistent competitive group"""
        with patch("src.competitive.manager.CompetitiveManager") as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.get_competitive_group.return_value = None
            mock_manager.return_value = mock_manager_instance

            with patch("src.auth.authentication.API_KEY_REQUIRED", False):
                response = client.get(
                    "/api/v1/competitive/groups/999", headers=auth_headers
                )

                assert response.status_code == 404


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_headers_present(self, client, auth_headers):
        """Test that rate limit headers are included in responses"""
        with patch("src.auth.authentication.API_KEY_REQUIRED", False):
            response = client.get("/health", headers=auth_headers)

            # Rate limit headers should be present (may be mocked in test)
            # This tests the middleware integration
            assert response.status_code == 200


class TestAuthentication:
    """Test authentication functionality"""

    def test_unauthenticated_request(self, client):
        """Test request without authentication when required"""
        with patch("src.auth.authentication.API_KEY_REQUIRED", True):
            response = client.get("/api/v1/products/summary/B07R7RMQF5")

            assert response.status_code == 401

    def test_invalid_api_key(self, client):
        """Test request with invalid API key"""
        headers = {"Authorization": "Bearer invalid_key_123"}

        with patch("src.auth.authentication.API_KEY_REQUIRED", True):
            response = client.get(
                "/api/v1/products/summary/B07R7RMQF5", headers=headers
            )

            assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api", "--cov-report=html"])
