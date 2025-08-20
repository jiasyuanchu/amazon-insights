#!/usr/bin/env python3
"""
Unit tests for authentication and authorization system
"""

import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.auth.authentication import (
    APIKey, APIKeyManager, AuthenticationService, 
    KeyType, Permission, RateLimitTier
)
from src.auth.rate_limiter import RateLimiter, RateLimitWindow, RateLimitConfig

class TestAPIKeyManager:
    """Test API key management functionality"""
    
    @pytest.fixture
    def key_manager(self):
        with patch('src.auth.authentication.redis_client') as mock_redis:
            mock_redis.setex = Mock()
            mock_redis.get = Mock(return_value=None)
            mock_redis.incr = Mock()
            mock_redis.expire = Mock()
            manager = APIKeyManager()
            manager.redis = mock_redis
            return manager
    
    def test_generate_api_key_public(self, key_manager):
        """Test public API key generation"""
        key_id = key_manager.generate_api_key(KeyType.PUBLIC, "Test Public Key")
        
        assert key_id.startswith("pk_live_")
        assert len(key_id) > 20
        key_manager.redis.setex.assert_called_once()
    
    def test_generate_api_key_secret(self, key_manager):
        """Test secret API key generation"""
        key_id = key_manager.generate_api_key(KeyType.SECRET, "Test Secret Key")
        
        assert key_id.startswith("sk_live_")
        assert len(key_id) > 20
    
    def test_generate_api_key_admin(self, key_manager):
        """Test admin API key generation"""
        key_id = key_manager.generate_api_key(KeyType.ADMIN, "Test Admin Key")
        
        assert key_id.startswith("ak_live_")
        assert len(key_id) > 20
    
    def test_default_permissions_public(self, key_manager):
        """Test default permissions for public keys"""
        permissions = key_manager._get_default_permissions(KeyType.PUBLIC)
        
        assert Permission.READ_PRODUCTS in permissions
        assert Permission.READ_COMPETITIVE in permissions
        assert Permission.WRITE_PRODUCTS not in permissions
        assert Permission.ADMIN_SYSTEM not in permissions
    
    def test_default_permissions_secret(self, key_manager):
        """Test default permissions for secret keys"""
        permissions = key_manager._get_default_permissions(KeyType.SECRET)
        
        assert Permission.READ_PRODUCTS in permissions
        assert Permission.WRITE_PRODUCTS in permissions
        assert Permission.READ_COMPETITIVE in permissions
        assert Permission.WRITE_COMPETITIVE in permissions
        assert Permission.ADMIN_SYSTEM not in permissions
    
    def test_default_permissions_admin(self, key_manager):
        """Test default permissions for admin keys"""
        permissions = key_manager._get_default_permissions(KeyType.ADMIN)
        
        assert Permission.ADMIN_SYSTEM in permissions
        assert Permission.ADMIN_USERS in permissions
        assert len(permissions) == len(Permission)  # All permissions
    
    def test_validate_api_key_cached(self, key_manager):
        """Test API key validation with cached data"""
        # Mock cached data
        cached_data = {
            "key_type": "secret",
            "permissions": ["read:products", "write:products"],
            "tier": "pro",
            "metadata": {"name": "Test Key"},
            "is_active": True,
            "hash": "testhash"
        }
        key_manager.redis.get.return_value = key_manager._serialize_cache_data(cached_data)
        
        result = key_manager.validate_api_key("sk_live_testkey123")
        
        assert result is not None
        assert result.key_type == KeyType.SECRET
        assert result.tier == RateLimitTier.PRO
        assert Permission.READ_PRODUCTS in result.permissions
    
    def test_validate_api_key_invalid(self, key_manager):
        """Test validation of invalid API key"""
        key_manager.redis.get.return_value = None
        
        result = key_manager.validate_api_key("invalid_key")
        
        assert result is None
    
    def test_check_permission_allowed(self, key_manager):
        """Test permission check for allowed permission"""
        api_key = APIKey(
            key_id="test_key",
            key_type=KeyType.SECRET,
            permissions=[Permission.READ_PRODUCTS, Permission.WRITE_PRODUCTS],
            tier=RateLimitTier.PRO
        )
        
        result = key_manager.check_permission(api_key, Permission.READ_PRODUCTS)
        assert result is True
    
    def test_check_permission_denied(self, key_manager):
        """Test permission check for denied permission"""
        api_key = APIKey(
            key_id="test_key",
            key_type=KeyType.PUBLIC,
            permissions=[Permission.READ_PRODUCTS],
            tier=RateLimitTier.FREE
        )
        
        result = key_manager.check_permission(api_key, Permission.WRITE_PRODUCTS)
        assert result is False

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.fixture
    def rate_limiter(self):
        with patch('src.auth.rate_limiter.redis') as mock_redis:
            mock_redis.from_url.return_value = Mock()
            limiter = RateLimiter()
            limiter.redis = Mock()
            return limiter
    
    def test_endpoint_weight_expensive(self, rate_limiter):
        """Test endpoint weight for expensive operations"""
        weight = rate_limiter._get_endpoint_weight("/api/v1/products/track")
        assert weight == 10
    
    def test_endpoint_weight_very_expensive(self, rate_limiter):
        """Test endpoint weight for very expensive operations"""
        weight = rate_limiter._get_endpoint_weight("/api/v1/competitive/analyze")
        assert weight == 50
    
    def test_endpoint_weight_cheap(self, rate_limiter):
        """Test endpoint weight for cheap operations"""
        weight = rate_limiter._get_endpoint_weight("/api/v1/products/summary")
        assert weight == 1
    
    def test_endpoint_weight_default(self, rate_limiter):
        """Test default endpoint weight"""
        weight = rate_limiter._get_endpoint_weight("/api/v1/unknown/endpoint")
        assert weight == 1.0
    
    def test_window_seconds(self, rate_limiter):
        """Test time window calculations"""
        assert rate_limiter._get_window_seconds(RateLimitWindow.MINUTE) == 60
        assert rate_limiter._get_window_seconds(RateLimitWindow.HOUR) == 3600
        assert rate_limiter._get_window_seconds(RateLimitWindow.DAY) == 86400
    
    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, rate_limiter):
        """Test rate limit check when within limits"""
        # Mock Redis pipeline
        mock_pipe = Mock()
        mock_pipe.execute.return_value = [0, 5, True, True]  # Simulated pipeline results
        rate_limiter.redis.pipeline.return_value = mock_pipe
        
        api_key = APIKey(
            key_id="test_key",
            key_type=KeyType.PRO,
            permissions=[Permission.READ_PRODUCTS],
            tier=RateLimitTier.PRO
        )
        
        result = await rate_limiter.check_rate_limit(
            api_key, "/api/v1/products/summary", Mock()
        )
        
        assert result["allowed"] is True
        assert "limits" in result
        assert "usage" in result
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, rate_limiter):
        """Test getting rate limit status"""
        rate_limiter.redis.zcard.return_value = 50
        
        api_key = APIKey(
            key_id="test_key_12345",
            key_type=KeyType.PRO,
            permissions=[Permission.READ_PRODUCTS],
            tier=RateLimitTier.PRO
        )
        
        status = await rate_limiter.get_rate_limit_status(api_key)
        
        assert "key_id" in status
        assert status["key_id"] == "test_key_12345..."  # Masked
        assert status["tier"] == "pro"
        assert "windows" in status
        assert "minute" in status["windows"]
        assert "hour" in status["windows"]
        assert "day" in status["windows"]

class TestAuthenticationService:
    """Test authentication service functionality"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('src.auth.authentication.redis_client'):
            service = AuthenticationService()
            service.key_manager = Mock()
            return service
    
    @pytest.mark.asyncio
    async def test_authenticate_request_valid(self, auth_service):
        """Test successful authentication"""
        # Mock valid API key
        mock_api_key = APIKey(
            key_id="sk_live_testkey",
            key_type=KeyType.SECRET,
            permissions=[Permission.READ_PRODUCTS],
            tier=RateLimitTier.PRO
        )
        auth_service.key_manager.validate_api_key.return_value = mock_api_key
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = "sk_live_testkey"
        
        with patch('src.auth.authentication.API_KEY_REQUIRED', True):
            result = await auth_service.authenticate_request(credentials)
            
            assert result == mock_api_key
            auth_service.key_manager.validate_api_key.assert_called_once_with("sk_live_testkey")
    
    @pytest.mark.asyncio
    async def test_authenticate_request_invalid(self, auth_service):
        """Test authentication with invalid key"""
        auth_service.key_manager.validate_api_key.return_value = None
        
        credentials = Mock()
        credentials.credentials = "invalid_key"
        
        with patch('src.auth.authentication.API_KEY_REQUIRED', True):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_request(credentials)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_authenticate_request_no_credentials(self, auth_service):
        """Test authentication without credentials"""
        with patch('src.auth.authentication.API_KEY_REQUIRED', True):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_request(None)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_authenticate_request_development_mode(self, auth_service):
        """Test authentication in development mode"""
        with patch('src.auth.authentication.API_KEY_REQUIRED', False):
            result = await auth_service.authenticate_request(None)
            
            assert result is not None
            assert result.key_type == KeyType.ADMIN
            assert Permission.ADMIN_SYSTEM in result.permissions

class TestRateLimitConfig:
    """Test rate limit configuration"""
    
    def test_tier_limits_structure(self):
        """Test rate limit tier configuration structure"""
        config = RateLimitConfig()
        
        # Check all tiers exist
        assert RateLimitTier.FREE in config.TIER_LIMITS
        assert RateLimitTier.PRO in config.TIER_LIMITS
        assert RateLimitTier.ENTERPRISE in config.TIER_LIMITS
        
        # Check all windows exist for each tier
        for tier in RateLimitTier:
            tier_config = config.TIER_LIMITS[tier]
            assert RateLimitWindow.MINUTE in tier_config
            assert RateLimitWindow.HOUR in tier_config
            assert RateLimitWindow.DAY in tier_config
    
    def test_tier_limits_progression(self):
        """Test that higher tiers have higher limits"""
        config = RateLimitConfig()
        
        free_limits = config.TIER_LIMITS[RateLimitTier.FREE]
        pro_limits = config.TIER_LIMITS[RateLimitTier.PRO]
        enterprise_limits = config.TIER_LIMITS[RateLimitTier.ENTERPRISE]
        
        # Pro should have higher limits than free
        assert pro_limits[RateLimitWindow.MINUTE] > free_limits[RateLimitWindow.MINUTE]
        assert pro_limits[RateLimitWindow.HOUR] > free_limits[RateLimitWindow.HOUR]
        assert pro_limits[RateLimitWindow.DAY] > free_limits[RateLimitWindow.DAY]
        
        # Enterprise should have higher limits than pro
        assert enterprise_limits[RateLimitWindow.MINUTE] > pro_limits[RateLimitWindow.MINUTE]
        assert enterprise_limits[RateLimitWindow.HOUR] > pro_limits[RateLimitWindow.HOUR]
        assert enterprise_limits[RateLimitWindow.DAY] > pro_limits[RateLimitWindow.DAY]
    
    def test_endpoint_weights(self):
        """Test endpoint weight configuration"""
        config = RateLimitConfig()
        
        # Expensive endpoints should have higher weights
        assert config.ENDPOINT_WEIGHTS["/api/v1/products/track"] > config.ENDPOINT_WEIGHTS["/api/v1/products/summary"]
        assert config.ENDPOINT_WEIGHTS["/api/v1/competitive/analyze"] > config.ENDPOINT_WEIGHTS["/api/v1/products/track"]
        
        # Health check should be nearly free
        assert config.ENDPOINT_WEIGHTS["/api/v1/system/health"] < 1

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for auth + rate limiting"""
    
    async def test_auth_and_rate_limit_flow(self):
        """Test complete authentication and rate limiting flow"""
        with patch('src.auth.authentication.redis_client'), \
             patch('src.auth.rate_limiter.redis'):
            
            # Create services
            auth_service = AuthenticationService()
            rate_limiter = RateLimiter()
            
            # Mock API key validation
            mock_api_key = APIKey(
                key_id="sk_live_testkey",
                key_type=KeyType.SECRET,
                permissions=[Permission.READ_PRODUCTS, Permission.WRITE_PRODUCTS],
                tier=RateLimitTier.PRO
            )
            auth_service.key_manager.validate_api_key = Mock(return_value=mock_api_key)
            
            # Mock rate limiting (allowed)
            rate_limiter.redis.pipeline = Mock()
            mock_pipe = Mock()
            mock_pipe.execute.return_value = [0, 10, True, True]
            rate_limiter.redis.pipeline.return_value = mock_pipe
            
            # Test authentication
            credentials = Mock()
            credentials.credentials = "sk_live_testkey"
            
            with patch('src.auth.authentication.API_KEY_REQUIRED', True):
                api_key = await auth_service.authenticate_request(credentials)
                assert api_key == mock_api_key
            
            # Test rate limiting
            mock_request = Mock()
            mock_request.url.path = "/api/v1/products/summary"
            
            rate_limit_result = await rate_limiter.check_rate_limit(
                api_key, "/api/v1/products/summary", mock_request
            )
            
            assert rate_limit_result["allowed"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.auth", "--cov-report=html"])