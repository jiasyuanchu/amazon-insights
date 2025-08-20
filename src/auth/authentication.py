#!/usr/bin/env python3
"""
Authentication and Authorization System for Amazon Insights API
Implements API key authentication with role-based access control
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
import redis

from config.config import JWT_SECRET_KEY, API_KEY_REQUIRED, REDIS_URL

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis client for API key caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class KeyType(str, Enum):
    PUBLIC = "public"  # pk_ - Read-only access
    SECRET = "secret"  # sk_ - Full application access
    ADMIN = "admin"  # ak_ - Administrative access


class Permission(str, Enum):
    READ_PRODUCTS = "read:products"
    WRITE_PRODUCTS = "write:products"
    READ_COMPETITIVE = "read:competitive"
    WRITE_COMPETITIVE = "write:competitive"
    READ_ALERTS = "read:alerts"
    WRITE_ALERTS = "write:alerts"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_USERS = "admin:users"


class RateLimitTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class APIKey:
    """API Key data model"""

    def __init__(
        self,
        key_id: str,
        key_type: KeyType,
        permissions: List[Permission],
        tier: RateLimitTier,
        metadata: Dict[str, Any] = None,
    ):
        self.key_id = key_id
        self.key_type = key_type
        self.permissions = permissions
        self.tier = tier
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_used_at = None
        self.usage_count = 0
        self.is_active = True


class APIKeyManager:
    """Manages API key creation, validation, and permissions"""

    def __init__(self):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour cache for API key data

    def generate_api_key(
        self,
        key_type: KeyType,
        name: str = None,
        custom_permissions: List[Permission] = None,
    ) -> str:
        """Generate a new API key"""

        # Generate key with appropriate prefix
        prefix_map = {
            KeyType.PUBLIC: "pk_live_",
            KeyType.SECRET: "sk_live_",
            KeyType.ADMIN: "ak_live_",
        }

        prefix = prefix_map[key_type]
        key_id = f"{prefix}{secrets.token_urlsafe(32)}"

        # Default permissions based on key type
        if custom_permissions:
            permissions = custom_permissions
        else:
            permissions = self._get_default_permissions(key_type)

        # Default tier based on key type
        tier = RateLimitTier.FREE if key_type == KeyType.PUBLIC else RateLimitTier.PRO

        # Create API key object
        api_key = APIKey(
            key_id=key_id,
            key_type=key_type,
            permissions=permissions,
            tier=tier,
            metadata={"name": name or f"Generated {key_type} key"},
        )

        # Store in cache and database
        self._store_api_key(api_key)

        logger.info(f"Generated new API key: {key_id[:15]}... (type: {key_type})")
        return key_id

    def _get_default_permissions(self, key_type: KeyType) -> List[Permission]:
        """Get default permissions for key type"""
        permission_map = {
            KeyType.PUBLIC: [
                Permission.READ_PRODUCTS,
                Permission.READ_COMPETITIVE,
                Permission.READ_ALERTS,
            ],
            KeyType.SECRET: [
                Permission.READ_PRODUCTS,
                Permission.WRITE_PRODUCTS,
                Permission.READ_COMPETITIVE,
                Permission.WRITE_COMPETITIVE,
                Permission.READ_ALERTS,
            ],
            KeyType.ADMIN: [
                Permission.READ_PRODUCTS,
                Permission.WRITE_PRODUCTS,
                Permission.READ_COMPETITIVE,
                Permission.WRITE_COMPETITIVE,
                Permission.READ_ALERTS,
                Permission.WRITE_ALERTS,
                Permission.ADMIN_SYSTEM,
                Permission.ADMIN_USERS,
            ],
        }
        return permission_map[key_type]

    def _store_api_key(self, api_key: APIKey):
        """Store API key in cache and database"""

        # Hash the key for database storage
        key_hash = hashlib.sha256(api_key.key_id.encode()).hexdigest()

        # Cache the key data
        cache_key = f"api_key:{api_key.key_id}"
        cache_data = {
            "key_type": api_key.key_type.value,
            "permissions": [p.value for p in api_key.permissions],
            "tier": api_key.tier.value,
            "metadata": api_key.metadata,
            "is_active": api_key.is_active,
            "hash": key_hash,
        }

        self.redis.setex(
            cache_key, self.cache_ttl, self._serialize_cache_data(cache_data)
        )

    def validate_api_key(self, key_id: str) -> Optional[APIKey]:
        """Validate API key and return key object"""

        if not key_id:
            return None

        # Check cache first
        cache_key = f"api_key:{key_id}"
        cached_data = self.redis.get(cache_key)

        if cached_data:
            data = self._deserialize_cache_data(cached_data)
            if data.get("is_active"):
                # Update usage stats
                self._update_key_usage(key_id)

                return APIKey(
                    key_id=key_id,
                    key_type=KeyType(data["key_type"]),
                    permissions=[Permission(p) for p in data["permissions"]],
                    tier=RateLimitTier(data["tier"]),
                    metadata=data.get("metadata", {}),
                )

        # If not in cache, check database (would implement database lookup here)
        # For now, return None for unknown keys
        return None

    def check_permission(
        self, api_key: APIKey, required_permission: Permission
    ) -> bool:
        """Check if API key has required permission"""
        return required_permission in api_key.permissions

    def _update_key_usage(self, key_id: str):
        """Update API key usage statistics"""
        usage_key = f"api_usage:{key_id}"

        # Increment usage count
        self.redis.incr(usage_key)
        self.redis.expire(usage_key, 86400)  # 24 hour TTL

        # Update last used timestamp
        last_used_key = f"api_last_used:{key_id}"
        self.redis.setex(last_used_key, 86400, datetime.now().isoformat())

    def _serialize_cache_data(self, data: Dict) -> str:
        """Serialize cache data"""
        import json

        return json.dumps(data)

    def _deserialize_cache_data(self, data: str) -> Dict:
        """Deserialize cache data"""
        import json

        return json.loads(data)


class AuthenticationService:
    """Main authentication service"""

    def __init__(self):
        self.key_manager = APIKeyManager()
        self.security = HTTPBearer(auto_error=False)

    async def authenticate_request(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(
            HTTPBearer(auto_error=False)
        ),
        request: Request = None,
    ) -> Optional[APIKey]:
        """Authenticate API request"""

        # Skip authentication if not required (development mode)
        if not API_KEY_REQUIRED:
            return self._create_development_key()

        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please provide API key in Authorization header.",
            )

        # Extract and validate API key
        api_key = self.key_manager.validate_api_key(credentials.credentials)

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please check your credentials.",
            )

        # Log API usage for monitoring
        if request:
            self._log_api_usage(api_key, request)

        return api_key

    def require_permission(self, required_permission: Permission):
        """Decorator factory for permission checking"""

        def permission_checker(api_key: APIKey = Depends(self.authenticate_request)):
            if not self.key_manager.check_permission(api_key, required_permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {required_permission.value}",
                )
            return api_key

        return permission_checker

    def _create_development_key(self) -> APIKey:
        """Create a development key when authentication is disabled"""
        return APIKey(
            key_id="dev_key_local",
            key_type=KeyType.ADMIN,
            permissions=[p for p in Permission],  # All permissions
            tier=RateLimitTier.ENTERPRISE,
        )

    def _log_api_usage(self, api_key: APIKey, request: Request):
        """Log API usage for monitoring and analytics"""
        usage_data = {
            "key_id": api_key.key_id,
            "key_type": api_key.key_type.value,
            "endpoint": str(request.url.path),
            "method": request.method,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.now().isoformat(),
        }

        # Store in Redis for real-time monitoring
        usage_key = f"api_log:{datetime.now().strftime('%Y%m%d%H')}:{api_key.key_id}"
        self.key_manager.redis.lpush(
            usage_key, self.key_manager._serialize_cache_data(usage_data)
        )
        self.key_manager.redis.expire(usage_key, 86400)  # 24 hour retention


# Global authentication service instance
auth_service = AuthenticationService()


# Dependency functions for FastAPI
async def get_current_api_key(
    api_key: APIKey = Depends(auth_service.authenticate_request),
) -> APIKey:
    """Get current authenticated API key"""
    return api_key


def require_read_products():
    """Require read:products permission"""
    return auth_service.require_permission(Permission.READ_PRODUCTS)


def require_write_products():
    """Require write:products permission"""
    return auth_service.require_permission(Permission.WRITE_PRODUCTS)


def require_read_competitive():
    """Require read:competitive permission"""
    return auth_service.require_permission(Permission.READ_COMPETITIVE)


def require_write_competitive():
    """Require write:competitive permission"""
    return auth_service.require_permission(Permission.WRITE_COMPETITIVE)


def require_admin():
    """Require admin permissions"""
    return auth_service.require_permission(Permission.ADMIN_SYSTEM)


# Utility functions
def create_development_api_key() -> str:
    """Create a development API key for testing"""
    key_manager = APIKeyManager()
    return key_manager.generate_api_key(
        key_type=KeyType.SECRET,
        name="Development Testing Key",
        custom_permissions=[p for p in Permission],  # All permissions
    )
