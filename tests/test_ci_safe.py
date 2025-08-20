#!/usr/bin/env python3
"""
CI-safe tests that don't require external dependencies
"""

import os
import sys


def test_python_version():
    """Test Python version compatibility"""
    assert sys.version_info >= (3, 7), "Python 3.7+ required"


def test_requirements_file_exists():
    """Test requirements.txt exists and is readable"""
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found"
    
    with open(req_path, 'r') as f:
        content = f.read()
        assert len(content) > 0, "requirements.txt is empty"
        assert "fastapi" in content, "FastAPI not in requirements"


def test_dockerfile_exists():
    """Test Dockerfile exists and has basic content"""
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile not found"
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
        assert "FROM python:" in content, "Dockerfile doesn't use Python base image"


def test_basic_imports():
    """Test basic Python standard library imports"""
    import json
    import logging
    import datetime
    import typing
    assert True  # If we get here, imports worked


def test_project_structure():
    """Test project has expected directory structure"""
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    
    expected_dirs = ["src", "api", "config", "tests"]
    for dir_name in expected_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        assert os.path.exists(dir_path), f"Directory {dir_name} not found"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])