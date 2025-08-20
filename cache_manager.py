#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.redis_service import cache, CacheKeyBuilder
from config.config import AMAZON_ASINS

def show_cache_info():
    """Display cache information"""
    print("🔍 Redis Cache Information")
    print("-" * 50)
    
    info = cache.get_info()
    print(f"Enabled: {info.get('enabled', False)}")
    print(f"Connected: {info.get('connected', False)}")
    
    if info.get('connected'):
        print(f"Memory Used: {info.get('memory_used', 'N/A')}")
        print(f"Total Keys: {info.get('total_keys', 0)}")
        print(f"Redis Version: {info.get('redis_version', 'N/A')}")
    else:
        print(f"Error: {info.get('error', 'Unknown error')}")

def show_cache_keys():
    """Display cache keys status"""
    print("\n🔑 Cache Keys Status")
    print("-" * 50)
    
    if not cache.enabled or not cache.client:
        print("Cache not available")
        return
    
    # Check various cache keys
    key_categories = {
        "Product Summaries": [CacheKeyBuilder.product_summary(asin) for asin in AMAZON_ASINS[:3]],
        "System Status": [CacheKeyBuilder.system_status()],
        "All Products": [CacheKeyBuilder.all_products_summary()],
        "Alerts": [CacheKeyBuilder.alerts_summary(24), CacheKeyBuilder.alerts_summary(48)]
    }
    
    for category, keys in key_categories.items():
        print(f"\n{category}:")
        for key in keys:
            exists = cache.exists(key)
            ttl = cache.ttl(key) if exists else -1
            status = "✅ Cached" if exists else "❌ Not cached"
            ttl_info = f"(TTL: {ttl}s)" if ttl > 0 else f"(TTL: {ttl})" if ttl == -1 else ""
            print(f"  {key}: {status} {ttl_info}")

def clear_all_cache():
    """Clear all cache"""
    print("🗑️  Clearing all cache...")
    
    if cache.flush_all():
        print("✅ All cache cleared successfully")
    else:
        print("❌ Failed to clear cache")

def clear_product_cache(asin: str):
    """Clear cache for specific product"""
    print(f"🗑️  Clearing cache for product {asin}...")
    
    keys_cleared = []
    
    # Clear product summary
    if cache.delete(CacheKeyBuilder.product_summary(asin)):
        keys_cleared.append("product_summary")
    
    # Clear product history
    for limit in [10, 20, 30, 50, 100]:
        if cache.delete(CacheKeyBuilder.product_history(asin, limit)):
            keys_cleared.append(f"history_{limit}")
    
    # Clear related alerts
    for hours in [24, 48]:
        if cache.delete(CacheKeyBuilder.alerts_by_asin(asin, hours)):
            keys_cleared.append(f"alerts_{hours}h")
    
    # Clear global cache
    if cache.delete(CacheKeyBuilder.all_products_summary()):
        keys_cleared.append("all_products_summary")
    
    if keys_cleared:
        print(f"✅ Cleared {len(keys_cleared)} cache entries: {', '.join(keys_cleared)}")
    else:
        print("❌ No cache entries found to clear")

def clear_pattern_cache(pattern: str):
    """Clear cache matching pattern"""
    print(f"🗑️  Clearing cache pattern: {pattern}")
    
    deleted_count = cache.delete_pattern(f"*{pattern}*")
    if deleted_count > 0:
        print(f"✅ Cleared {deleted_count} cache entries")
    else:
        print("❌ No cache entries found matching the pattern")

def warm_up_cache():
    """Warm up cache"""
    print("🔥 Warming up cache...")
    
    try:
        # Pre-load some commonly used data into cache
        from src.monitoring.product_tracker import ProductTracker
        
        tracker = ProductTracker()
        
        # Warm up some product summaries
        for asin in AMAZON_ASINS[:3]:
            print(f"  Warming up {asin}...")
            summary = tracker.get_product_summary(asin)
            if "error" not in summary:
                print(f"    ✅ {asin} cached")
            else:
                print(f"    ❌ {asin} failed: {summary['error']}")
        
        # Warm up all products summary
        print("  Warming up all products summary...")
        all_summaries = tracker.get_all_products_summary()
        if all_summaries:
            print("    ✅ All products summary cached")
        
        print("🔥 Cache warm-up completed")
        
    except Exception as e:
        print(f"❌ Cache warm-up failed: {str(e)}")

def test_cache():
    """Test cache functionality"""
    print("🧪 Testing cache functionality...")
    
    if not cache.enabled:
        print("❌ Cache is disabled")
        return
    
    # Test basic operations
    test_key = "test:cache:functionality"
    test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
    
    print("  Testing cache set...")
    if cache.set(test_key, test_value, 60):
        print("    ✅ Cache set successful")
    else:
        print("    ❌ Cache set failed")
        return
    
    print("  Testing cache get...")
    retrieved_value = cache.get(test_key)
    if retrieved_value and retrieved_value["test"] == "data":
        print("    ✅ Cache get successful")
    else:
        print("    ❌ Cache get failed")
    
    print("  Testing cache exists...")
    if cache.exists(test_key):
        print("    ✅ Cache exists check successful")
    else:
        print("    ❌ Cache exists check failed")
    
    print("  Testing cache delete...")
    if cache.delete(test_key):
        print("    ✅ Cache delete successful")
    else:
        print("    ❌ Cache delete failed")
    
    print("🧪 Cache testing completed")

def main():
    parser = argparse.ArgumentParser(description='Amazon Insights Cache Manager')
    parser.add_argument('command', choices=[
        'info', 'keys', 'clear-all', 'clear-product', 'clear-pattern', 
        'warm-up', 'test'
    ], help='Cache management command')
    parser.add_argument('--asin', help='ASIN for product-specific operations')
    parser.add_argument('--pattern', help='Pattern for pattern-based clearing')
    
    args = parser.parse_args()
    
    print(f"🚀 Amazon Insights Cache Manager")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.command == 'info':
        show_cache_info()
        
    elif args.command == 'keys':
        show_cache_keys()
        
    elif args.command == 'clear-all':
        clear_all_cache()
        
    elif args.command == 'clear-product':
        if not args.asin:
            print("❌ --asin required for clear-product command")
            return 1
        clear_product_cache(args.asin)
        
    elif args.command == 'clear-pattern':
        if not args.pattern:
            print("❌ --pattern required for clear-pattern command")
            return 1
        clear_pattern_cache(args.pattern)
        
    elif args.command == 'warm-up':
        warm_up_cache()
        
    elif args.command == 'test':
        test_cache()
    
    return 0

if __name__ == '__main__':
    exit(main())