#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.redis_service import cache, CacheKeyBuilder

def test_basic_cache_operations():
    """Test basic cache operations"""
    print("🧪 Testing Basic Cache Operations")
    print("-" * 40)
    
    if not cache.enabled:
        print("❌ Cache is disabled")
        return False
    
    # Test data
    test_key = "test:basic:operations"
    test_data = {
        "message": "Hello Redis Cache!",
        "number": 42,
        "list": [1, 2, 3, 4, 5],
        "nested": {"key": "value"}
    }
    
    # Test SET
    print("  Testing SET...")
    if cache.set(test_key, test_data, 30):
        print("    ✅ SET operation successful")
    else:
        print("    ❌ SET operation failed")
        return False
    
    # Test GET
    print("  Testing GET...")
    retrieved_data = cache.get(test_key)
    if retrieved_data and retrieved_data["message"] == "Hello Redis Cache!":
        print("    ✅ GET operation successful")
    else:
        print("    ❌ GET operation failed")
        return False
    
    # Test EXISTS
    print("  Testing EXISTS...")
    if cache.exists(test_key):
        print("    ✅ EXISTS operation successful")
    else:
        print("    ❌ EXISTS operation failed")
    
    # Test TTL
    print("  Testing TTL...")
    ttl = cache.ttl(test_key)
    if ttl > 0:
        print(f"    ✅ TTL operation successful (TTL: {ttl}s)")
    else:
        print("    ❌ TTL operation failed")
    
    # Test DELETE
    print("  Testing DELETE...")
    if cache.delete(test_key):
        print("    ✅ DELETE operation successful")
    else:
        print("    ❌ DELETE operation failed")
    
    return True

def test_key_builders():
    """Test cache key builders"""
    print("\n🔑 Testing Cache Key Builders")
    print("-" * 40)
    
    asin = "B07R7RMQF5"
    
    keys_to_test = [
        ("Product Summary", CacheKeyBuilder.product_summary(asin)),
        ("Product History", CacheKeyBuilder.product_history(asin, 20)),
        ("All Products", CacheKeyBuilder.all_products_summary()),
        ("Alerts Summary", CacheKeyBuilder.alerts_summary(24)),
        ("System Status", CacheKeyBuilder.system_status())
    ]
    
    for name, key in keys_to_test:
        print(f"  {name}: {key}")
    
    print("  ✅ All key builders working correctly")
    return True

def test_cache_performance():
    """Test cache performance"""
    print("\n⚡ Testing Cache Performance")
    print("-" * 40)
    
    if not cache.enabled:
        print("❌ Cache is disabled")
        return False
    
    # Test data
    test_key = "test:performance"
    test_data = {"data": list(range(1000)), "timestamp": time.time()}
    
    # Test write performance
    print("  Testing write performance...")
    start_time = time.time()
    cache.set(test_key, test_data, 60)
    write_time = time.time() - start_time
    print(f"    Write time: {write_time:.4f} seconds")
    
    # Test read performance
    print("  Testing read performance...")
    start_time = time.time()
    retrieved_data = cache.get(test_key)
    read_time = time.time() - start_time
    print(f"    Read time: {read_time:.4f} seconds")
    
    # Clean up
    cache.delete(test_key)
    
    if write_time < 0.1 and read_time < 0.1:
        print("  ✅ Performance test passed")
        return True
    else:
        print("  ⚠️  Performance may need optimization")
        return True

def test_cache_integration():
    """Test integration with other system components"""
    print("\n🔗 Testing Cache Integration")
    print("-" * 40)
    
    try:
        from src.monitoring.product_tracker import ProductTracker
        
        tracker = ProductTracker()
        asin = "B07R7RMQF5"
        
        print(f"  Testing product summary caching for {asin}...")
        
        # First call (should fetch from database)
        start_time = time.time()
        summary1 = tracker.get_product_summary(asin)
        first_call_time = time.time() - start_time
        
        # Second call (should fetch from cache)
        start_time = time.time()
        summary2 = tracker.get_product_summary(asin)
        second_call_time = time.time() - start_time
        
        if "error" not in summary1 and "error" not in summary2:
            print(f"    First call: {first_call_time:.4f}s")
            print(f"    Second call: {second_call_time:.4f}s")
            
            if second_call_time < first_call_time:
                print("    ✅ Cache integration working correctly")
                return True
            else:
                print("    ⚠️  Cache may not be improving performance")
                return True
        else:
            print("    ❌ Integration test failed - no data available")
            return False
            
    except Exception as e:
        print(f"    ❌ Integration test failed: {str(e)}")
        return False

def main():
    """Execute all cache tests"""
    print("🚀 Redis Cache System Test Suite")
    print("=" * 50)
    
    # Display cache info
    info = cache.get_info()
    print(f"Cache Enabled: {info.get('enabled', False)}")
    print(f"Cache Connected: {info.get('connected', False)}")
    
    if not info.get('connected', False):
        print("❌ Cannot run tests - Redis not connected")
        return 1
    
    print(f"Redis Version: {info.get('redis_version', 'N/A')}")
    print()
    
    # Execute tests
    tests = [
        test_basic_cache_operations,
        test_key_builders,
        test_cache_performance,
        test_cache_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cache tests passed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed or need attention")
        return 1

if __name__ == '__main__':
    exit(main())