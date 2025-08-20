#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Complete Competitive Analysis Workflow
This script demonstrates the full competitive analysis capabilities
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.competitive.manager import CompetitiveManager
from src.competitive.analyzer import CompetitiveAnalyzer
from src.competitive.llm_reporter import LLMReporter

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print subsection header"""
    print(f"\n📊 {title}")
    print("-" * 40)

def demo_competitive_workflow():
    """Demonstrate complete competitive analysis workflow"""
    
    print_section("Amazon Insights - Competitive Analysis Demo")
    
    try:
        # Initialize components
        manager = CompetitiveManager()
        analyzer = CompetitiveAnalyzer()
        llm_reporter = LLMReporter()
        
        print("✅ All components initialized successfully")
        print(f"   - CompetitiveManager: Ready")
        print(f"   - CompetitiveAnalyzer: Ready")
        print(f"   - LLMReporter: {'OpenAI enabled' if llm_reporter.use_openai else 'Fallback mode'}")
        
        # Step 1: Quick Setup - Create group with competitors
        print_section("Step 1: Quick Setup - Creating Competitive Group")
        
        main_asin = "B07R7RMQF5"  # Main product (should be in tracking)
        competitor_asins = [
            "B092XMWXK7",  # Competitor 1
            "B0BVY8K28Q",  # Competitor 2 
            "B0CSMV2DTV",  # Competitor 3
        ]
        
        print(f"Main Product ASIN: {main_asin}")
        print(f"Competitor ASINs: {', '.join(competitor_asins)}")
        
        # Create competitive group
        group = manager.create_competitive_group(
            name="Demo: Yoga Mats Competitive Analysis",
            main_product_asin=main_asin,
            description="Demonstration of competitive analysis features"
        )
        
        print(f"✅ Created group: '{group.name}' (ID: {group.id})")
        
        # Add competitors
        competitors_added = 0
        for i, asin in enumerate(competitor_asins, 1):
            try:
                competitor = manager.add_competitor(
                    group_id=group.id,
                    competitor_asin=asin,
                    competitor_name=f"Competitor {i} - Premium Yoga Mat",
                    priority=i
                )
                competitors_added += 1
                print(f"✅ Added {competitor.competitor_name} ({competitor.asin})")
            except Exception as e:
                print(f"⚠️  Failed to add {asin}: {str(e)}")
        
        print(f"📊 Successfully added {competitors_added} competitors")
        
        # Step 2: Check Tracking Status
        print_section("Step 2: Checking Tracking Status")
        
        tracking_status = manager.ensure_competitors_tracked(group.id)
        tracked_count = sum(1 for status in tracking_status.values() if status)
        
        print(f"Tracking Status: {tracked_count}/{len(tracking_status)} products tracked")
        
        for asin, tracked in tracking_status.items():
            status = "✅ Tracked" if tracked else "❌ Not tracked"
            print(f"  {asin}: {status}")
        
        if tracked_count < len(tracking_status):
            print("\n⚠️  RECOMMENDATIONS:")
            for asin, tracked in tracking_status.items():
                if not tracked:
                    print(f"   - Add '{asin}' to AMAZON_ASINS in config/config.py")
            print("   - Then restart the tracking system to collect data")
        
        # Step 3: Run Competitive Analysis
        print_section("Step 3: Running Competitive Analysis")
        
        analysis_result = analyzer.analyze_competitive_group(group.id)
        
        if "error" in analysis_result:
            print(f"❌ Analysis failed: {analysis_result['error']}")
            return False
        
        print("✅ Competitive analysis completed successfully!")
        
        # Display key results
        group_info = analysis_result.get("group_info", {})
        main_product = analysis_result.get("main_product", {})
        price_analysis = analysis_result.get("price_analysis", {})
        bsr_analysis = analysis_result.get("bsr_analysis", {})
        rating_analysis = analysis_result.get("rating_analysis", {})
        feature_analysis = analysis_result.get("feature_analysis", {})
        competitive_summary = analysis_result.get("competitive_summary", {})
        
        print_subsection("Analysis Overview")
        print(f"Group: {group_info.get('name', 'N/A')}")
        print(f"Main Product: {main_product.get('title', 'N/A')[:50]}...")
        print(f"Competitors Analyzed: {group_info.get('competitors_count', 0)}")
        print(f"Analysis Timestamp: {analysis_result.get('analysis_timestamp', 'N/A')}")
        
        print_subsection("Price Analysis")
        print(f"Main Product Price: ${price_analysis.get('main_product_price', 'N/A')}")
        print(f"Price Position: {price_analysis.get('price_position', 'unknown').title()}")
        
        market_range = price_analysis.get('market_price_range', {})
        if market_range:
            print(f"Market Range: ${market_range.get('min', 0):.2f} - ${market_range.get('max', 0):.2f}")
            print(f"Market Average: ${market_range.get('average', 0):.2f}")
        
        print(f"Price Advantage: {'Yes' if price_analysis.get('price_advantage') else 'No'}")
        print(f"Cheaper Competitors: {price_analysis.get('cheaper_competitors', 0)}")
        print(f"More Expensive Competitors: {price_analysis.get('more_expensive_competitors', 0)}")
        
        print_subsection("Rating Analysis") 
        main_rating_data = rating_analysis.get('main_product', {})
        print(f"Main Product Rating: {main_rating_data.get('rating', 'N/A')}/5.0")
        print(f"Main Product Reviews: {main_rating_data.get('review_count', 'N/A')}")
        
        rating_stats = rating_analysis.get('rating_statistics', {})
        if rating_stats:
            print(f"Market Rating Range: {rating_stats.get('min', 0):.1f} - {rating_stats.get('max', 0):.1f}")
            print(f"Average Market Rating: {rating_stats.get('average', 0):.1f}")
            print(f"Rating Position: {rating_stats.get('main_product_position', 'unknown').title()}")
        
        print(f"Quality Advantage: {'Yes' if rating_analysis.get('quality_advantage') else 'No'}")
        print(f"Popularity Advantage: {'Yes' if rating_analysis.get('popularity_advantage') else 'No'}")
        
        print_subsection("BSR Analysis")
        if bsr_analysis and not bsr_analysis.get("error"):
            for category, data in list(bsr_analysis.items())[:3]:  # Show top 3 categories
                if isinstance(data, dict):
                    print(f"{category}:")
                    print(f"  Main Product Rank: #{data.get('main_product_rank', 'N/A')}")
                    print(f"  Position: {data.get('position', 'unknown').title()}")
                    
                    stats = data.get('rank_statistics', {})
                    if stats:
                        print(f"  Best Rank: #{stats.get('best_rank', 'N/A')}")
                        print(f"  Average Rank: #{stats.get('average_rank', 'N/A')}")
        else:
            print("BSR data not available")
        
        print_subsection("Feature Analysis")
        unique_features = feature_analysis.get('unique_to_main', {})
        missing_features = feature_analysis.get('missing_from_main', {})
        
        unique_count = sum(len(features) for features in unique_features.values())
        missing_count = sum(len(features) for features in missing_features.values())
        
        print(f"Unique Features: {unique_count}")
        print(f"Missing Features: {missing_count}")
        
        diversity = feature_analysis.get('feature_diversity_score', {})
        if diversity:
            print(f"Feature Count: {diversity.get('main_product_features', 0)} vs Avg {diversity.get('average_competitor_features', 0)}")
            print(f"Feature Richness: {diversity.get('feature_richness', 'unknown').title()}")
        
        print_subsection("Competitive Summary")
        scores = competitive_summary.get('competitive_scores', {})
        if scores:
            print(f"Overall Competitiveness: {scores.get('overall_competitiveness', 'N/A')}/100")
            print(f"Price Competitiveness: {scores.get('price_competitiveness', 'N/A'):.1f}/100")
            print(f"Quality Competitiveness: {scores.get('quality_competitiveness', 'N/A'):.1f}/100")
            print(f"Popularity Competitiveness: {scores.get('popularity_competitiveness', 'N/A'):.1f}/100")
        
        position_summary = competitive_summary.get('position_summary', {})
        if position_summary:
            print(f"Overall Position: {position_summary.get('overall_position', 'unknown').title()}")
            print(f"Analysis Confidence: {competitive_summary.get('analysis_confidence', 'unknown').title()}")
        
        # Step 4: Generate LLM Positioning Report
        print_section("Step 4: Generating LLM Positioning Report")
        
        positioning_report = llm_reporter.generate_positioning_report(analysis_result)
        
        if "error" in positioning_report:
            print(f"❌ LLM report failed: {positioning_report['error']}")
        else:
            print("✅ LLM positioning report generated successfully!")
            
            metadata = positioning_report.get('report_metadata', {})
            print(f"Model Used: {metadata.get('model_used', 'N/A')}")
            print(f"LLM Enabled: {metadata.get('llm_enabled', False)}")
            print(f"Generated At: {metadata.get('generated_at', 'N/A')}")
            
            print_subsection("Executive Summary")
            exec_summary = positioning_report.get('executive_summary', '')
            print(exec_summary[:200] + "..." if len(exec_summary) > 200 else exec_summary)
            
            print_subsection("SWOT Analysis") 
            swot = positioning_report.get('strengths_weaknesses', {})
            
            strengths = swot.get('strengths', [])
            weaknesses = swot.get('weaknesses', [])
            opportunities = swot.get('opportunities', [])
            threats = swot.get('threats', [])
            
            if strengths:
                print("Strengths:")
                for strength in strengths[:3]:  # Show top 3
                    print(f"  • {strength}")
            
            if weaknesses:
                print("Weaknesses:")
                for weakness in weaknesses[:3]:  # Show top 3
                    print(f"  • {weakness}")
            
            if opportunities:
                print("Opportunities:")
                for opp in opportunities[:3]:  # Show top 3
                    print(f"  • {opp}")
            
            print_subsection("Strategic Recommendations")
            recommendations = positioning_report.get('strategic_recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                    print(f"{i}. {rec.get('action', 'N/A')}")
                    print(f"   Category: {rec.get('category', 'N/A')}")
                    print(f"   Priority: {rec.get('priority', 'N/A')}")
                    print(f"   Expected Impact: {rec.get('expected_impact', 'N/A')}")
                    print()
            else:
                print("No specific recommendations generated")
        
        # Step 5: Summary & Next Steps
        print_section("Summary & Next Steps")
        
        print("✅ Demo completed successfully!")
        print(f"   - Created competitive group: ID {group.id}")
        print(f"   - Added {competitors_added} competitors")
        print(f"   - Analyzed {group_info.get('competitors_count', 0)} products")
        print(f"   - Generated {'LLM-powered' if not positioning_report.get('error') else 'structured'} positioning report")
        
        print("\n🔄 Next Steps:")
        print("   1. Add missing ASINs to tracking configuration if needed")
        print("   2. Wait for data collection (24-48 hours for full data)")
        print("   3. Re-run analysis for updated insights")
        print("   4. Use API endpoints for programmatic access:")
        print(f"      • GET /api/v1/competitive/groups/{group.id}")
        print(f"      • POST /api/v1/competitive/groups/{group.id}/analyze")
        print(f"      • GET /api/v1/competitive/groups/{group.id}/report")
        
        print("\n🌟 API Features Available:")
        print("   • Quick setup with multiple competitors")
        print("   • Batch analysis for all groups")
        print("   • Tracking status monitoring")
        print("   • Comprehensive positioning reports")
        print("   • Real-time competitive intelligence")
        
        # Cleanup suggestion
        print(f"\n🧹 To clean up this demo:")
        print(f"   Run: DELETE /api/v1/competitive/groups/{group.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_api_examples():
    """Show API usage examples"""
    print_section("API Usage Examples")
    
    examples = {
        "Quick Setup": {
            "method": "POST",
            "endpoint": "/api/v1/competitive/quick-setup",
            "body": {
                "main_product_asin": "B07R7RMQF5",
                "competitor_asins": ["B092XMWXK7", "B0BVY8K28Q", "B0CSMV2DTV"],
                "group_name": "My Yoga Mat Analysis",
                "description": "Competitive analysis for yoga mat market"
            }
        },
        "Run Analysis": {
            "method": "POST", 
            "endpoint": "/api/v1/competitive/groups/{group_id}/analyze",
            "params": {"include_llm_report": True}
        },
        "Get Report": {
            "method": "GET",
            "endpoint": "/api/v1/competitive/groups/{group_id}/report"
        },
        "Batch Analysis": {
            "method": "POST",
            "endpoint": "/api/v1/competitive/batch-analysis"
        },
        "System Summary": {
            "method": "GET",
            "endpoint": "/api/v1/competitive/summary"
        }
    }
    
    for name, example in examples.items():
        print(f"\n📡 {name}:")
        print(f"   {example['method']} {example['endpoint']}")
        
        if 'body' in example:
            print("   Body:")
            print(f"   {json.dumps(example['body'], indent=6)}")
        
        if 'params' in example:
            print("   Params:")
            for key, value in example['params'].items():
                print(f"   {key}: {value}")

if __name__ == '__main__':
    success = demo_competitive_workflow()
    
    if success:
        show_api_examples()
    
    exit(0 if success else 1)