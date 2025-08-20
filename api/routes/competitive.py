import sys
import os
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logger = logging.getLogger(__name__)

from api.models.competitive_schemas import (
    CreateCompetitiveGroupRequest, AddCompetitorRequest, CompetitiveGroupInfo,
    CompetitorInfo, CompetitiveAnalysisResult, TrendAnalysis, PositioningReport
)
from src.competitive.manager import CompetitiveManager
from src.competitive.analyzer import CompetitiveAnalyzer
from src.competitive.llm_reporter import LLMReporter

router = APIRouter(prefix="/api/v1/competitive", tags=["Competitive Analysis"])

# Initialize components
manager = CompetitiveManager()
analyzer = CompetitiveAnalyzer()
llm_reporter = LLMReporter()

@router.post("/groups", response_model=CompetitiveGroupInfo)
async def create_competitive_group(request: CreateCompetitiveGroupRequest):
    """
    Create a new competitive analysis group
    """
    try:
        group = manager.create_competitive_group(
            name=request.name,
            main_product_asin=request.main_product_asin,
            description=request.description
        )
        
        return CompetitiveGroupInfo(
            id=group.id,
            name=group.name,
            description=group.description,
            main_product_asin=group.main_product_asin,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat(),
            is_active=group.is_active,
            competitors=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups", response_model=List[CompetitiveGroupInfo])
async def get_all_competitive_groups():
    """
    Get all competitive analysis groups
    """
    try:
        groups = manager.get_all_competitive_groups()
        
        result = []
        for group in groups:
            competitors = []
            if hasattr(group, 'active_competitors'):
                competitors = [
                    CompetitorInfo(
                        id=comp.id,
                        asin=comp.asin,
                        competitor_name=comp.competitor_name,
                        priority=comp.priority,
                        is_active=comp.is_active,
                        added_at=comp.added_at.isoformat()
                    ) for comp in group.active_competitors
                ]
            
            result.append(CompetitiveGroupInfo(
                id=group.id,
                name=group.name,
                description=group.description,
                main_product_asin=group.main_product_asin,
                created_at=group.created_at.isoformat(),
                updated_at=group.updated_at.isoformat(),
                is_active=group.is_active,
                competitors=competitors
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}", response_model=CompetitiveGroupInfo)
async def get_competitive_group(group_id: int):
    """
    Get specific competitive group
    """
    try:
        group = manager.get_competitive_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Competitive group not found")
        
        competitors = []
        if hasattr(group, 'active_competitors'):
            competitors = [
                CompetitorInfo(
                    id=comp.id,
                    asin=comp.asin,
                    competitor_name=comp.competitor_name,
                    priority=comp.priority,
                    is_active=comp.is_active,
                    added_at=comp.added_at.isoformat()
                ) for comp in group.active_competitors
            ]
        
        return CompetitiveGroupInfo(
            id=group.id,
            name=group.name,
            description=group.description,
            main_product_asin=group.main_product_asin,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat(),
            is_active=group.is_active,
            competitors=competitors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/competitors", response_model=CompetitorInfo)
async def add_competitor(group_id: int, request: AddCompetitorRequest):
    """
    Add competitor to competitive group
    """
    try:
        competitor = manager.add_competitor(
            group_id=group_id,
            competitor_asin=request.asin,
            competitor_name=request.competitor_name,
            priority=request.priority
        )
        
        return CompetitorInfo(
            id=competitor.id,
            asin=competitor.asin,
            competitor_name=competitor.competitor_name,
            priority=competitor.priority,
            is_active=competitor.is_active,
            added_at=competitor.added_at.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/groups/{group_id}/competitors/{asin}")
async def remove_competitor(group_id: int, asin: str):
    """
    Remove competitor from group
    """
    try:
        success = manager.remove_competitor(group_id, asin)
        if not success:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        return {"message": f"Competitor {asin} removed from group {group_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/analyze")
async def analyze_competitive_group(group_id: int, include_llm_report: bool = False):
    """
    Perform competitive analysis for a group
    """
    try:
        # Perform competitive analysis
        analysis_result = analyzer.analyze_competitive_group(group_id)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=400, detail=analysis_result["error"])
        
        # Add LLM report if requested
        if include_llm_report:
            try:
                positioning_report = llm_reporter.generate_positioning_report(analysis_result)
                analysis_result["positioning_report"] = positioning_report
            except Exception as e:
                logger.warning(f"LLM report generation failed: {str(e)}")
                analysis_result["positioning_report"] = {"error": str(e)}
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/trends")
async def get_competitive_trends(group_id: int, days: int = 30):
    """
    Get competitive trends analysis
    """
    try:
        trends = analyzer.get_trend_analysis(group_id, days)
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/tracking-status")
async def get_tracking_status(group_id: int):
    """
    Check if all products in group are being tracked
    """
    try:
        tracking_status = manager.ensure_competitors_tracked(group_id)
        
        tracked_count = sum(1 for status in tracking_status.values() if status)
        total_count = len(tracking_status)
        
        return {
            "group_id": group_id,
            "tracking_status": tracking_status,
            "summary": {
                "tracked_products": tracked_count,
                "total_products": total_count,
                "all_tracked": tracked_count == total_count
            },
            "recommendations": [
                f"Add {asin} to AMAZON_ASINS in config.py" 
                for asin, tracked in tracking_status.items() if not tracked
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/groups/{group_id}")
async def delete_competitive_group(group_id: int):
    """
    Delete competitive group
    """
    try:
        success = manager.delete_group(group_id)
        if not success:
            raise HTTPException(status_code=404, detail="Competitive group not found")
        
        return {"message": f"Competitive group {group_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/report", response_model=PositioningReport)
async def get_positioning_report(group_id: int):
    """
    Get detailed positioning report for competitive group
    """
    try:
        # First get the analysis
        analysis_result = analyzer.analyze_competitive_group(group_id)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=400, detail=analysis_result["error"])
        
        # Generate LLM report
        positioning_report = llm_reporter.generate_positioning_report(analysis_result)
        
        if "error" in positioning_report:
            raise HTTPException(status_code=500, detail=positioning_report["error"])
        
        return positioning_report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class QuickSetupRequest(BaseModel):
    main_product_asin: str
    competitor_asins: List[str]
    group_name: Optional[str] = None
    description: Optional[str] = None

@router.post("/quick-setup")
async def quick_competitive_setup(request: QuickSetupRequest):
    """
    Quick setup: Create group and add multiple competitors at once
    """
    try:
        # Default group name if not provided
        group_name = request.group_name
        if not group_name:
            group_name = f"Competitive Analysis for {request.main_product_asin}"
        
        description = request.description
        if not description:
            description = f"Auto-generated competitive analysis group"
        
        # Create group
        group = manager.create_competitive_group(
            name=group_name,
            main_product_asin=request.main_product_asin,
            description=description
        )
        
        # Add competitors
        competitors = []
        for i, asin in enumerate(request.competitor_asins, 1):
            try:
                competitor = manager.add_competitor(
                    group_id=group.id,
                    competitor_asin=asin,
                    competitor_name=f"Competitor {i}",
                    priority=i
                )
                competitors.append(CompetitorInfo(
                    id=competitor.id,
                    asin=competitor.asin,
                    competitor_name=competitor.competitor_name,
                    priority=competitor.priority,
                    is_active=competitor.is_active,
                    added_at=competitor.added_at.isoformat()
                ))
            except Exception as e:
                logger.warning(f"Failed to add competitor {asin}: {str(e)}")
        
        # Check tracking status
        tracking_status = manager.ensure_competitors_tracked(group.id)
        tracked_count = sum(1 for status in tracking_status.values() if status)
        
        return {
            "group": CompetitiveGroupInfo(
                id=group.id,
                name=group.name,
                description=group.description,
                main_product_asin=group.main_product_asin,
                created_at=group.created_at.isoformat(),
                updated_at=group.updated_at.isoformat(),
                is_active=group.is_active,
                competitors=competitors
            ),
            "tracking_status": {
                "tracked_products": tracked_count,
                "total_products": len(tracking_status),
                "all_tracked": tracked_count == len(tracking_status),
                "recommendations": [
                    f"Add {asin} to AMAZON_ASINS in config.py" 
                    for asin, tracked in tracking_status.items() if not tracked
                ]
            },
            "next_steps": [
                f"Run analysis: POST /api/v1/competitive/groups/{group.id}/analyze",
                f"Get report: GET /api/v1/competitive/groups/{group.id}/report"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analysis")
async def batch_competitive_analysis():
    """
    Run analysis for all active competitive groups
    """
    try:
        groups = manager.get_all_competitive_groups()
        results = []
        
        for group in groups:
            if group.is_active:
                try:
                    analysis_result = analyzer.analyze_competitive_group(group.id)
                    results.append({
                        "group_id": group.id,
                        "group_name": group.name,
                        "status": "success" if "error" not in analysis_result else "failed",
                        "analysis": analysis_result if "error" not in analysis_result else None,
                        "error": analysis_result.get("error") if "error" in analysis_result else None
                    })
                except Exception as e:
                    results.append({
                        "group_id": group.id,
                        "group_name": group.name,
                        "status": "failed",
                        "analysis": None,
                        "error": str(e)
                    })
        
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "failed"])
        
        return {
            "summary": {
                "total_groups": len(results),
                "successful_analyses": successful,
                "failed_analyses": failed,
                "success_rate": f"{(successful / len(results) * 100):.1f}%" if results else "0%"
            },
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def competitive_analysis_summary():
    """
    Get overall competitive analysis summary
    """
    try:
        groups = manager.get_all_competitive_groups()
        
        total_groups = len(groups)
        active_groups = len([g for g in groups if g.is_active])
        
        # Count total competitors
        total_competitors = 0
        for group in groups:
            if hasattr(group, 'active_competitors'):
                total_competitors += len(group.active_competitors)
        
        # Get tracking status for all groups
        tracking_summary = {"tracked": 0, "not_tracked": 0}
        for group in groups:
            if group.is_active:
                try:
                    tracking_status = manager.ensure_competitors_tracked(group.id)
                    for tracked in tracking_status.values():
                        if tracked:
                            tracking_summary["tracked"] += 1
                        else:
                            tracking_summary["not_tracked"] += 1
                except:
                    pass
        
        return {
            "competitive_groups": {
                "total": total_groups,
                "active": active_groups,
                "inactive": total_groups - active_groups
            },
            "competitors": {
                "total_tracked": total_competitors
            },
            "tracking_status": tracking_summary,
            "system_health": {
                "tracking_coverage": f"{(tracking_summary['tracked'] / (tracking_summary['tracked'] + tracking_summary['not_tracked']) * 100):.1f}%" if (tracking_summary['tracked'] + tracking_summary['not_tracked']) > 0 else "0%",
                "recommendations": []
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))