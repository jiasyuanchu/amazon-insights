#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.competitive.manager import CompetitiveManager
from src.competitive.analyzer import CompetitiveAnalyzer
from src.competitive.llm_reporter import LLMReporter


def test_competitive_system():
    """Test competitive analysis system"""
    print("🚀 Testing Competitive Analysis Engine")
    print("=" * 50)

    try:
        # Initialize components
        manager = CompetitiveManager()
        analyzer = CompetitiveAnalyzer()
        llm_reporter = LLMReporter()

        print("✅ Components initialized successfully")

        # Test 1: Create competitive group
        print("\n📊 Test 1: Creating competitive group...")
        group = manager.create_competitive_group(
            name="Yoga Mats Competitive Analysis",
            main_product_asin="B07R7RMQF5",  # Our tracked yoga mat
            description="Analysis of yoga mat market competition",
        )
        print(f"✅ Created group: {group.name} (ID: {group.id})")

        # Test 2: Add competitors
        print("\n🎯 Test 2: Adding competitors...")
        competitors_to_add = [
            ("B092XMWXK7", "Competitor A - Premium Mat", 1),
            ("B0BVY8K28Q", "Competitor B - Budget Mat", 2),
            ("B0CSMV2DTV", "Competitor C - Eco Mat", 1),
        ]

        for asin, name, priority in competitors_to_add:
            competitor = manager.add_competitor(group.id, asin, name, priority)
            print(
                f"✅ Added competitor: {competitor.competitor_name} ({competitor.asin})"
            )

        # Test 3: Check tracking status
        print("\n🔍 Test 3: Checking tracking status...")
        tracking_status = manager.ensure_competitors_tracked(group.id)
        tracked_count = sum(1 for status in tracking_status.values() if status)
        print(
            f"✅ Tracking status: {tracked_count}/{len(tracking_status)} products tracked"
        )

        for asin, tracked in tracking_status.items():
            status = "✅ Tracked" if tracked else "❌ Not tracked"
            print(f"  {asin}: {status}")

        # Test 4: Competitive analysis
        print("\n📈 Test 4: Running competitive analysis...")
        analysis_result = analyzer.analyze_competitive_group(group.id)

        if "error" in analysis_result:
            print(f"❌ Analysis failed: {analysis_result['error']}")
        else:
            print("✅ Competitive analysis completed")

            # Show key results
            group_info = analysis_result.get("group_info", {})
            price_analysis = analysis_result.get("price_analysis", {})
            competitive_summary = analysis_result.get("competitive_summary", {})

            print(f"  Group: {group_info.get('name', 'N/A')}")
            print(
                f"  Main Product: {analysis_result.get('main_product', {}).get('title', 'N/A')[:50]}..."
            )
            print(f"  Competitors analyzed: {group_info.get('competitors_count', 0)}")
            print(
                f"  Price position: {price_analysis.get('price_position', 'unknown')}"
            )

            scores = competitive_summary.get("competitive_scores", {})
            if scores:
                print(
                    f"  Overall competitiveness: {scores.get('overall_competitiveness', 'N/A')}/100"
                )

        # Test 5: LLM Report
        print("\n🤖 Test 5: Generating LLM positioning report...")
        if "error" not in analysis_result:
            positioning_report = llm_reporter.generate_positioning_report(
                analysis_result
            )

            if "error" in positioning_report:
                print(f"❌ LLM report failed: {positioning_report['error']}")
            else:
                print("✅ LLM positioning report generated")
                print(
                    f"  Executive summary preview: {positioning_report.get('executive_summary', '')[:100]}..."
                )

        print("\n🎉 Competitive analysis system test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def demo_competitive_workflow():
    """Demonstrate the complete competitive analysis workflow"""
    print("\n🎭 Demo: Complete Competitive Analysis Workflow")
    print("=" * 60)

    try:
        manager = CompetitiveManager()

        # Show all groups
        groups = manager.get_all_competitive_groups()
        print(f"📊 Total competitive groups: {len(groups)}")

        for group in groups:
            print(f"\n📋 Group: {group.name} (ID: {group.id})")
            print(f"   Main Product: {group.main_product_asin}")

            if hasattr(group, "active_competitors"):
                print(f"   Competitors: {len(group.active_competitors)}")
                for comp in group.active_competitors:
                    print(
                        f"     - {comp.competitor_name} ({comp.asin}) [Priority: {comp.priority}]"
                    )

        if groups:
            print(f"\n🚀 This setup is ready for API testing!")
            print(f"   Use group ID {groups[0].id} for testing")

        return True

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_competitive_system()

    if success:
        demo_competitive_workflow()

    exit(0 if success else 1)
