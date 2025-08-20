from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class CreateCompetitiveGroupRequest(BaseModel):
    name: str = Field(
        ..., description="Competitive group name", example="Yoga Mats Analysis"
    )
    main_product_asin: str = Field(
        ..., description="Main product ASIN", example="B07R7RMQF5"
    )
    description: Optional[str] = Field(None, description="Group description")


class AddCompetitorRequest(BaseModel):
    asin: str = Field(..., description="Competitor ASIN", example="B092XMWXK7")
    competitor_name: Optional[str] = Field(None, description="Custom competitor name")
    priority: int = Field(1, description="Priority level (1=high, 2=medium, 3=low)")


class CompetitorInfo(BaseModel):
    id: int
    asin: str
    competitor_name: Optional[str] = None
    priority: int
    is_active: bool
    added_at: str


class CompetitiveGroupInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    main_product_asin: str
    created_at: str
    updated_at: str
    is_active: bool
    competitors: List[CompetitorInfo] = []


class ProductMetrics(BaseModel):
    asin: str
    title: str
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    bsr_data: Optional[Dict[str, int]] = None
    bullet_points: List[str] = []
    key_features: Dict[str, List[str]] = {}
    availability: str = "Unknown"


class PriceAnalysis(BaseModel):
    main_product_price: Optional[float] = None
    price_position: str = "unknown"
    market_price_range: Dict[str, float] = {}
    competitors: List[Dict] = []
    price_advantage: Optional[bool] = None
    cheaper_competitors: int = 0
    more_expensive_competitors: int = 0


class BSRAnalysis(BaseModel):
    # Dynamic structure based on categories
    pass


class RatingAnalysis(BaseModel):
    main_product: Dict = {}
    competitors: List[Dict] = []
    rating_statistics: Dict = {}
    review_statistics: Dict = {}
    quality_advantage: Optional[bool] = None
    popularity_advantage: Optional[bool] = None


class FeatureAnalysis(BaseModel):
    feature_categories: List[str] = []
    unique_to_main: Dict[str, List[str]] = {}
    common_features: Dict[str, List[str]] = {}
    missing_from_main: Dict[str, List[str]] = {}
    feature_diversity_score: Dict = {}
    detailed_comparison: Dict = {}


class CompetitiveSummary(BaseModel):
    competitive_scores: Dict[str, float] = {}
    position_summary: Dict[str, str] = {}
    total_competitors: int = 0
    analysis_confidence: str = "medium"


class PositioningReport(BaseModel):
    executive_summary: str
    competitive_positioning: Dict = {}
    strengths_weaknesses: Dict = {}
    feature_differentiation: Dict = {}
    strategic_recommendations: List[Dict] = []
    market_insights: Dict = {}
    report_metadata: Dict = {}


class CompetitiveAnalysisResult(BaseModel):
    group_info: Dict
    main_product: ProductMetrics
    competitors: List[ProductMetrics]
    price_analysis: PriceAnalysis
    bsr_analysis: Dict  # Dynamic based on categories
    rating_analysis: RatingAnalysis
    feature_analysis: FeatureAnalysis
    competitive_summary: CompetitiveSummary
    positioning_report: Optional[PositioningReport] = None
    analysis_timestamp: str


class TrendAnalysis(BaseModel):
    group_id: int
    trend_period_days: int
    trends: Dict = {}
    note: Optional[str] = None
