#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.api.firecrawl_client import FirecrawlClient
from src.parsers.amazon_parser import AmazonProductParser
from src.models.product_models import DatabaseManager
from config.config import AMAZON_ASINS


def test_single_asin():
    """Test tracking a single ASIN"""
    test_asin = AMAZON_ASINS[0]  # Use first ASIN from config

    print(f"🧪 Testing with ASIN: {test_asin}")

    # Test Firecrawl API
    print("\n1. Testing Firecrawl API...")
    client = FirecrawlClient()
    raw_data = client.scrape_amazon_product(test_asin)

    if raw_data:
        print("✅ Firecrawl API successful")
        print(f"   Response keys: {list(raw_data.keys())}")
    else:
        print("❌ Firecrawl API failed")
        return False

    # Test Parser
    print("\n2. Testing Amazon Parser...")
    parser = AmazonProductParser()
    parsed_data = parser.parse_product_data(raw_data)

    if parsed_data:
        print("✅ Parser successful")
        print(f"   Title: {parsed_data.get('title', 'N/A')[:80]}...")
        print(f"   Price: ${parsed_data.get('price', 'N/A')}")
        print(f"   Rating: {parsed_data.get('rating', 'N/A')}")
        print(f"   Reviews: {parsed_data.get('review_count', 'N/A')}")
        print(f"   BSR: {parsed_data.get('bsr', 'N/A')}")
    else:
        print("❌ Parser failed")
        return False

    # Test Database
    print("\n3. Testing Database...")
    db_manager = DatabaseManager()
    snapshot = db_manager.save_product_snapshot(test_asin, parsed_data)

    if snapshot:
        print("✅ Database save successful")
        print(f"   Snapshot ID: {snapshot.id}")
    else:
        print("❌ Database save failed")
        return False

    return True


def test_all_components():
    """Test all system components"""
    print("🧪 Amazon Insights System Test")
    print("=" * 50)

    # Test environment
    print("\n📋 Checking Environment...")
    from config.config import FIRECRAWL_API_KEY

    if FIRECRAWL_API_KEY:
        print("✅ FIRECRAWL_API_KEY found")
    else:
        print("❌ FIRECRAWL_API_KEY not found")
        print("Please set up your .env file")
        return False

    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✅ Directories created")

    # Test single ASIN
    success = test_single_asin()

    if success:
        print("\n🎉 All tests passed!")
        print("\nYou can now run:")
        print("  python main.py track-single --asin B07R7RMQF5")
        print("  python main.py track-all")
        print("  python main.py monitor")
    else:
        print("\n❌ Some tests failed")

    return success


if __name__ == "__main__":
    test_all_components()
