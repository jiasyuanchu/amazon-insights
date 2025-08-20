#!/usr/bin/env python3
"""
Basic CI/CD validation tests - Minimal and reliable
"""

def test_basic_imports():
    """Test basic Python imports work"""
    try:
        import json
        import os
        import sys
        assert True
    except ImportError:
        assert False, "Basic imports failed"


def test_app_import():
    """Test main app can be imported"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from app import app
        assert app is not None
    except Exception as e:
        assert False, f"App import failed: {e}"


def test_config_import():
    """Test config can be imported"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from config.config import DATABASE_URL
        assert DATABASE_URL is not None
    except Exception as e:
        assert False, f"Config import failed: {e}"


def test_requirements_exist():
    """Test requirements.txt exists"""
    import os
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found"


def test_dockerfile_exists():
    """Test Dockerfile exists"""
    import os
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile not found"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])