#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.monitoring.product_tracker import ProductTracker
from src.monitoring.anomaly_detector import AnomalyDetector
from src.models.product_models import DatabaseManager
from config.config import AMAZON_ASINS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Check if environment is properly configured"""
    from config.config import FIRECRAWL_API_KEY

    if not FIRECRAWL_API_KEY:
        print("❌ FIRECRAWL_API_KEY not found in environment variables")
        print("Please create a .env file with your Firecrawl API key:")
        print("FIRECRAWL_API_KEY=your_api_key_here")
        return False

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    return True


def track_single_product(asin: str):
    """Track a single product"""
    tracker = ProductTracker()
    detector = AnomalyDetector()

    print(f"\n📊 Tracking product: {asin}")
    success = tracker.track_single_product(asin)

    if success:
        print("✅ Product tracked successfully")

        # Get product summary
        summary = tracker.get_product_summary(asin)
        if "error" not in summary:
            print("\n📈 Product Summary:")
            print(f"Title: {summary['title'][:80]}...")
            print(
                f"Price: ${summary['current_price']}"
                if summary["current_price"]
                else "Price: N/A"
            )
            print(
                f"Rating: {summary['current_rating']}/5"
                if summary["current_rating"]
                else "Rating: N/A"
            )
            print(
                f"Reviews: {summary['current_review_count']}"
                if summary["current_review_count"]
                else "Reviews: N/A"
            )
            print(f"Availability: {summary['availability']}")
            print(f"Price Trend: {summary['price_trend']}")
            print(f"Last Updated: {summary['last_updated']}")

            if summary["bsr_data"]:
                print("\n🏆 Best Seller Ranks:")
                for category, rank in summary["bsr_data"].items():
                    print(f"  {category}: #{rank:,}")

    else:
        print("❌ Failed to track product")


def track_all_products():
    """Track all configured products"""
    tracker = ProductTracker()

    print(f"\n📊 Tracking {len(AMAZON_ASINS)} products...")
    results = tracker.track_all_products()

    successful = sum(1 for success in results.values() if success)
    print(
        f"\n✅ Completed: {successful}/{len(AMAZON_ASINS)} products tracked successfully"
    )

    # Show summary
    summaries = tracker.get_all_products_summary()
    print("\n📈 Products Summary:")
    print("-" * 100)

    for summary in summaries:
        if "error" not in summary:
            title = summary["title"][:50] if summary["title"] else "N/A"
            price = (
                f"${summary['current_price']}" if summary["current_price"] else "N/A"
            )
            rating = (
                f"{summary['current_rating']}/5" if summary["current_rating"] else "N/A"
            )
            print(
                f"{summary['asin']} | {title:50} | {price:10} | {rating:8} | {summary['price_trend']:10}"
            )


def show_alerts():
    """Show recent alerts"""
    detector = AnomalyDetector()

    print("\n🚨 Recent Alerts (Last 24 hours)")
    print("-" * 80)

    summary = detector.get_recent_alerts_summary(24)

    if "error" in summary:
        print(f"❌ Error getting alerts: {summary['error']}")
        return

    print(f"Total Alerts: {summary['total_alerts']}")

    if summary["by_type"]:
        print("\nBy Type:")
        for alert_type, count in summary["by_type"].items():
            print(f"  {alert_type}: {count}")

    if summary["by_asin"]:
        print("\nBy Product:")
        for asin, count in summary["by_asin"].items():
            print(f"  {asin}: {count} alerts")


def show_product_history(asin: str):
    """Show price history for a product"""
    db_manager = DatabaseManager()

    print(f"\n📊 Price History for {asin}")
    print("-" * 80)

    history = db_manager.get_price_history(asin, limit=20)

    if not history:
        print("No historical data found for this product")
        return

    print(f"{'Date':20} | {'Price':10} | {'Rating':8} | {'Reviews':10}")
    print("-" * 60)

    for snapshot in history:
        date_str = snapshot.scraped_at.strftime("%Y-%m-%d %H:%M")
        price_str = f"${snapshot.price:.2f}" if snapshot.price else "N/A"
        rating_str = f"{snapshot.rating:.1f}" if snapshot.rating else "N/A"
        reviews_str = f"{snapshot.review_count:,}" if snapshot.review_count else "N/A"

        print(f"{date_str:20} | {price_str:10} | {rating_str:8} | {reviews_str:10}")


def continuous_monitoring():
    """Start continuous monitoring"""
    tracker = ProductTracker()

    print("🔄 Starting continuous monitoring...")
    print("Press Ctrl+C to stop")

    try:
        tracker.continuous_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")


def main():
    parser = argparse.ArgumentParser(description="Amazon Product Insights Tracker")
    parser.add_argument(
        "command",
        choices=["track-single", "track-all", "monitor", "alerts", "history", "test"],
        help="Command to execute",
    )
    parser.add_argument("--asin", help="ASIN for single product tracking or history")
    parser.add_argument("--hours", type=int, default=24, help="Hours for alert history")

    args = parser.parse_args()

    # Check environment setup
    if not setup_environment():
        return 1

    try:
        if args.command == "track-single":
            if not args.asin:
                print("❌ --asin required for single product tracking")
                return 1
            track_single_product(args.asin)

        elif args.command == "track-all":
            track_all_products()

        elif args.command == "monitor":
            continuous_monitoring()

        elif args.command == "alerts":
            show_alerts()

        elif args.command == "history":
            if not args.asin:
                print("❌ --asin required for history")
                return 1
            show_product_history(args.asin)

        elif args.command == "test":
            print("🧪 Testing system components...")

            # Test database connection
            try:
                db_manager = DatabaseManager()
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return 1

            # Test Firecrawl API
            try:
                from src.api.firecrawl_client import FirecrawlClient

                client = FirecrawlClient()
                print("✅ Firecrawl client initialized")
            except Exception as e:
                print(f"❌ Firecrawl client failed: {e}")
                return 1

            print("✅ All components tested successfully")

        return 0

    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
