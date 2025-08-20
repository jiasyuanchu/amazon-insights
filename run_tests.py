#!/usr/bin/env python3
"""
Test runner script for Amazon Insights
Runs comprehensive test suite with coverage reporting
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_test_suite():
    """Run complete test suite with coverage reporting"""
    
    print("🧪 Running Amazon Insights Test Suite")
    print("=" * 60)
    
    # Test commands to run
    test_commands = [
        {
            "name": "Unit Tests - Authentication",
            "command": ["python", "-m", "pytest", "tests/test_auth.py", "-v", "--cov=src.auth"],
            "required": True
        },
        {
            "name": "Unit Tests - Competitive Analysis", 
            "command": ["python", "-m", "pytest", "tests/test_competitive_analysis.py", "-v", "--cov=src.competitive"],
            "required": True
        },
        {
            "name": "Integration Tests - API Endpoints",
            "command": ["python", "-m", "pytest", "tests/test_api_endpoints.py", "-v", "--cov=api"],
            "required": True
        },
        {
            "name": "Existing Tests - Cache System",
            "command": ["python", "-m", "pytest", "test_cache.py", "-v"],
            "required": False
        },
        {
            "name": "Existing Tests - Product Tracker",
            "command": ["python", "-m", "pytest", "test_tracker.py", "-v"],
            "required": False
        },
        {
            "name": "Existing Tests - Competitive System",
            "command": ["python", "-m", "pytest", "test_competitive.py", "-v"],
            "required": False
        }
    ]
    
    results = {
        "started_at": datetime.now().isoformat(),
        "tests_run": [],
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total_tests": 0,
        "coverage_percent": 0,
        "success": True
    }
    
    for test_config in test_commands:
        print(f"\n🔍 Running: {test_config['name']}")
        print("-" * 40)
        
        try:
            # Run test command
            result = subprocess.run(
                test_config["command"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test suite
            )
            
            test_result = {
                "name": test_config["name"],
                "command": " ".join(test_config["command"]),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "required": test_config["required"]
            }
            
            if result.returncode == 0:
                print(f"✅ {test_config['name']} - PASSED")
                results["passed"] += 1
                
                # Extract test count from output
                if "passed" in result.stdout:
                    import re
                    match = re.search(r'(\d+) passed', result.stdout)
                    if match:
                        results["total_tests"] += int(match.group(1))
                
            else:
                print(f"❌ {test_config['name']} - FAILED")
                print(f"   Error: {result.stderr}")
                results["failed"] += 1
                
                if test_config["required"]:
                    results["success"] = False
            
            results["tests_run"].append(test_result)
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_config['name']} - TIMEOUT")
            results["failed"] += 1
            if test_config["required"]:
                results["success"] = False
        
        except Exception as e:
            print(f"💥 {test_config['name']} - ERROR: {str(e)}")
            results["failed"] += 1
            if test_config["required"]:
                results["success"] = False
    
    # Run comprehensive coverage report
    print(f"\n📊 Generating Coverage Report")
    print("-" * 40)
    
    try:
        coverage_cmd = [
            "python", "-m", "pytest", 
            "tests/", 
            "--cov=src", 
            "--cov=api",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "--cov-fail-under=70"
        ]
        
        coverage_result = subprocess.run(
            coverage_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for full coverage
        )
        
        if coverage_result.returncode == 0:
            print("✅ Coverage report generated successfully")
            
            # Extract coverage percentage
            try:
                with open('coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                    results["coverage_percent"] = coverage_data.get("totals", {}).get("percent_covered", 0)
                    print(f"📈 Total Coverage: {results['coverage_percent']:.1f}%")
            except Exception as e:
                print(f"Warning: Could not parse coverage data: {e}")
        else:
            print("❌ Coverage report generation failed")
            print(f"   Error: {coverage_result.stderr}")
            results["coverage_percent"] = 0
            
    except Exception as e:
        print(f"💥 Coverage generation error: {str(e)}")
        results["coverage_percent"] = 0
    
    # Final summary
    print(f"\n📋 Test Summary")
    print("=" * 60)
    print(f"Total Test Suites: {len(test_commands)}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Coverage: {results['coverage_percent']:.1f}%")
    print(f"Overall Success: {'✅ PASS' if results['success'] else '❌ FAIL'}")
    
    # Coverage requirement check
    if results["coverage_percent"] >= 70:
        print("✅ Coverage requirement met (≥70%)")
    else:
        print(f"❌ Coverage requirement not met ({results['coverage_percent']:.1f}% < 70%)")
        results["success"] = False
    
    # Save detailed results
    results["completed_at"] = datetime.now().isoformat()
    
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: test_results.json")
    print(f"📊 Coverage report available at: htmlcov/index.html")
    
    return results["success"]

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)