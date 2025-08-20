import sys
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from api.models.schemas import (
    ASINRequest,
    ProductSummary,
    TrackingResult,
    BatchTrackingResult,
    PriceHistory,
    PriceHistoryEntry,
    ErrorResponse,
)
from src.monitoring.product_tracker import ProductTracker
from src.monitoring.anomaly_detector import AnomalyDetector
from src.models.product_models import DatabaseManager
from config.config import AMAZON_ASINS

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

# Initialize components
tracker = ProductTracker()
detector = AnomalyDetector()
db_manager = DatabaseManager()


@router.post("/track/{asin}", response_model=TrackingResult)
async def track_single_product(asin: str):
    """
    Track a single product
    """
    try:
        success = tracker.track_single_product(asin)

        if success:
            summary = tracker.get_product_summary(asin)
            if "error" not in summary:
                product_summary = ProductSummary(
                    asin=summary["asin"],
                    title=summary["title"],
                    current_price=summary["current_price"],
                    current_rating=summary["current_rating"],
                    current_review_count=summary["current_review_count"],
                    bsr_data=summary["bsr_data"],
                    availability=summary["availability"],
                    price_trend=summary["price_trend"],
                    last_updated=summary["last_updated"],
                    history_count=summary["history_count"],
                )

                return TrackingResult(
                    success=True,
                    message=f"Successfully tracked product {asin}",
                    asin=asin,
                    product_summary=product_summary,
                )
            else:
                return TrackingResult(
                    success=False,
                    message=f"Failed to get product summary: {summary['error']}",
                    asin=asin,
                )
        else:
            return TrackingResult(
                success=False, message=f"Failed to track product {asin}", asin=asin
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-all", response_model=BatchTrackingResult)
async def track_all_products():
    """
    Track all configured products
    """
    try:
        results = tracker.track_all_products()
        summaries = tracker.get_all_products_summary()

        successful = sum(1 for success in results.values() if success)

        product_summaries = []
        for summary in summaries:
            if "error" not in summary:
                product_summaries.append(
                    ProductSummary(
                        asin=summary["asin"],
                        title=summary["title"],
                        current_price=summary["current_price"],
                        current_rating=summary["current_rating"],
                        current_review_count=summary["current_review_count"],
                        bsr_data=summary["bsr_data"],
                        availability=summary["availability"],
                        price_trend=summary["price_trend"],
                        last_updated=summary["last_updated"],
                        history_count=summary["history_count"],
                    )
                )

        return BatchTrackingResult(
            total_products=len(AMAZON_ASINS),
            successful=successful,
            failed=len(AMAZON_ASINS) - successful,
            results=results,
            summaries=product_summaries,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{asin}", response_model=ProductSummary)
async def get_product_summary(asin: str):
    """
    Get product summary information
    """
    try:
        summary = tracker.get_product_summary(asin)

        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])

        return ProductSummary(
            asin=summary["asin"],
            title=summary["title"],
            current_price=summary["current_price"],
            current_rating=summary["current_rating"],
            current_review_count=summary["current_review_count"],
            bsr_data=summary["bsr_data"],
            availability=summary["availability"],
            price_trend=summary["price_trend"],
            last_updated=summary["last_updated"],
            history_count=summary["history_count"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=List[ProductSummary])
async def get_all_products_summary():
    """
    Get summary information for all products
    """
    try:
        summaries = tracker.get_all_products_summary()

        product_summaries = []
        for summary in summaries:
            if "error" not in summary:
                product_summaries.append(
                    ProductSummary(
                        asin=summary["asin"],
                        title=summary["title"],
                        current_price=summary["current_price"],
                        current_rating=summary["current_rating"],
                        current_review_count=summary["current_review_count"],
                        bsr_data=summary["bsr_data"],
                        availability=summary["availability"],
                        price_trend=summary["price_trend"],
                        last_updated=summary["last_updated"],
                        history_count=summary["history_count"],
                    )
                )

        return product_summaries

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{asin}", response_model=PriceHistory)
async def get_product_history(asin: str, limit: int = 20):
    """
    Get product price history
    """
    try:
        history = db_manager.get_price_history(asin, limit=limit)

        if not history:
            raise HTTPException(
                status_code=404, detail=f"No history found for ASIN: {asin}"
            )

        history_entries = []
        for snapshot in history:
            history_entries.append(
                PriceHistoryEntry(
                    date=snapshot.scraped_at.isoformat(),
                    price=snapshot.price,
                    rating=snapshot.rating,
                    review_count=snapshot.review_count,
                )
            )

        return PriceHistory(asin=asin, history=history_entries)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[str])
async def get_monitored_asins():
    """
    Get list of all monitored ASINs
    """
    return AMAZON_ASINS
