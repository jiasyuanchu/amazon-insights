#!/usr/bin/env python3
"""
Simple tests for CI/CD pipeline validation
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_imports():
    """Test that all main modules can be imported"""
    try:
        # Test config import
        from config.config import FIRECRAWL_API_KEY, DATABASE_URL

        # Test app import
        from app import app

        # Test main modules exist
        import src.competitive.analyzer
        import src.auth.authentication
        import src.models.product_models

        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_database_url_format():
    """Test database URL configuration"""
    from config.config import DATABASE_URL

    # Should be PostgreSQL URL or SQLite fallback
    assert DATABASE_URL.startswith(("postgresql://", "sqlite:///"))


def test_basic_api_structure():
    """Test FastAPI app structure"""
    from app import app

    # Check app is created
    assert app is not None
    assert hasattr(app, "routes")


def test_competitive_analyzer_exists():
    """Test competitive analyzer can be imported"""
    from src.competitive.analyzer import CompetitiveAnalyzer

    # Should be able to create instance
    analyzer = CompetitiveAnalyzer()
    assert analyzer is not None


def test_auth_system_exists():
    """Test authentication system can be imported"""
    from src.auth.authentication import APIKeyManager

    # Should be able to create instance
    manager = APIKeyManager()
    assert manager is not None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
