from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class ASINRequest(BaseModel):
    asin: str = Field(..., description="Amazon ASIN", example="B07R7RMQF5")


class ProductSummary(BaseModel):
    asin: str
    title: Optional[str] = None
    current_price: Optional[float] = None
    current_rating: Optional[float] = None
    current_review_count: Optional[int] = None
    bsr_data: Optional[Dict[str, int]] = None
    availability: Optional[str] = None
    price_trend: str = "stable"
    last_updated: str
    history_count: int = 0


class TrackingResult(BaseModel):
    success: bool
    message: str
    asin: str
    product_summary: Optional[ProductSummary] = None


class BatchTrackingResult(BaseModel):
    total_products: int
    successful: int
    failed: int
    results: Dict[str, bool]
    summaries: List[ProductSummary] = []


class PriceHistoryEntry(BaseModel):
    date: str
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class PriceHistory(BaseModel):
    asin: str
    history: List[PriceHistoryEntry]


class Alert(BaseModel):
    id: int
    asin: str
    alert_type: str
    old_value: Optional[float] = None
    new_value: Optional[float] = None
    change_percentage: Optional[float] = None
    message: str
    triggered_at: str


class AlertsSummary(BaseModel):
    total_alerts: int
    by_type: Dict[str, int] = {}
    by_asin: Dict[str, int] = {}
    recent_alerts: List[Alert] = []


class SystemStatus(BaseModel):
    status: str
    database_connected: bool
    firecrawl_available: bool
    monitored_asins: List[str]
    last_check: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[str] = None
