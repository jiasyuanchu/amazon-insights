# Competitive Analysis Engine User Guide

## 🚀 Feature Overview

Amazon Insights Competitive Analysis Engine provides comprehensive multi-dimensional competitor comparison analysis:

### Core Features
- **Main Product Setup**: Set seller's own product as baseline
- **Competitor Management**: Add 3-5 competitors for comparative analysis
- **Multi-dimensional Analysis**:
  - Price difference analysis and positioning
  - BSR (Best Sellers Rank) ranking comparison
  - Rating and review count advantages/disadvantages
  - Product feature comparison (extracted from bullet points)
- **LLM Intelligent Reports**: Generate competitive positioning reports using OpenAI GPT
- **Complete API Support**: Provides comprehensive REST API interfaces

## 📋 Prerequisites

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API Key (optional, uses structured analysis if not provided)
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Tracking Setup
Ensure all products to be analyzed are in the tracking list:
```python
# config/config.py
AMAZON_ASINS = [
    "B07R7RMQF5",  # Main product
    "B092XMWXK7",  # Competitor 1
    "B0BVY8K28Q",  # Competitor 2
    "B0CSMV2DTV",  # Competitor 3
]
```

## 🔧 Usage Methods

### Method 1: API Quick Setup (Recommended)
```bash
curl -X POST "http://localhost:8001/api/v1/competitive/quick-setup" \
  -H "Content-Type: application/json" \
  -d '{
    "main_product_asin": "B07R7RMQF5",
    "competitor_asins": ["B092XMWXK7", "B0BVY8K28Q", "B0CSMV2DTV"],
    "group_name": "Yoga Mat Market Competitive Analysis",
    "description": "Analysis of yoga mat market competition"
  }'
```

### Method 2: Step-by-Step Setup

#### Step 1: Create Competitive Group
```bash
curl -X POST "http://localhost:8001/api/v1/competitive/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Yoga Mat Market Analysis",
    "main_product_asin": "B07R7RMQF5",
    "description": "Comprehensive yoga mat market competitive analysis"
  }'
```

#### Step 2: Add Competitors
```bash
# Add Competitor 1
curl -X POST "http://localhost:8001/api/v1/competitive/groups/1/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B092XMWXK7",
    "competitor_name": "Premium Yoga Mat",
    "priority": 1
  }'

# Add more competitors...
```

#### Step 3: Run Analysis
```bash
curl -X POST "http://localhost:8001/api/v1/competitive/groups/1/analyze?include_llm_report=true"
```

## 📊 Analysis Results

### Basic Analysis Data
```json
{
  "group_info": {
    "id": 1,
    "name": "Yoga Mat Market Analysis",
    "main_product_asin": "B07R7RMQF5"
  },
  "main_product": {
    "asin": "B07R7RMQF5",
    "title": "Yoga Mat 1-Inch Extra Thick...",
    "price": 34.99,
    "rating": 4.7,
    "review_count": 18451
  },
  "competitors": [...],
  "competitive_summary": {
    "competitive_scores": {
      "price_competitiveness": 75.2,
      "quality_competitiveness": 94.0,
      "popularity_competitiveness": 82.3,
      "overall_competitiveness": 83.8
    }
  }
}
```

### LLM Analysis Report
```json
{
  "positioning_report": {
    "executive_summary": "Your product shows strong market positioning...",
    "strengths_weaknesses": {
      "strengths": ["Superior customer satisfaction", "Competitive pricing"],
      "weaknesses": ["Limited feature differentiation"],
      "opportunities": ["Premium market segment expansion"],
      "threats": ["Increasing price competition"]
    },
    "strategic_recommendations": [
      {
        "category": "pricing",
        "priority": "high",
        "action": "Consider price optimization strategy",
        "rationale": "Current price positioning analysis suggests...",
        "expected_impact": "15-20% improvement in market competitiveness"
      }
    ]
  }
}
```

## 🎯 Competitive Scoring System

### Price Competitiveness (0-100)
- **100 points**: Lowest price in market
- **75-99 points**: Competitive pricing
- **50-74 points**: Average market pricing
- **25-49 points**: Above average pricing
- **0-24 points**: Premium pricing

**Formula**: `(2 - price_ratio) * 50`
Where `price_ratio = main_product_price / average_competitor_price`

### Quality Competitiveness (0-100)
- **100 points**: 5.0 star rating
- **80 points**: 4.0 star rating
- **60 points**: 3.0 star rating
- **40 points**: 2.0 star rating
- **20 points**: 1.0 star rating

**Formula**: `(rating / 5.0) * 100`

### Popularity Competitiveness (0-100)
Based on Amazon BSR (Best Seller Rank):
- **Higher scores**: Better (lower) BSR ranking
- **Calculation**: Relative ranking compared to competitors

## 🖥️ Dashboard Interface

### Starting the Dashboard
```bash
# Start API server
python3 start_api.py

# Start frontend server (separate terminal)
python3 frontend_server.py
```

Access dashboard at: `http://localhost:8080`

### Dashboard Features
- **Real-time Analysis**: Live competitive data updates
- **Interactive Charts**: Price trends and rating comparisons
- **SWOT Analysis Visualization**: AI-generated strategic insights
- **Export Capabilities**: PDF reports and data export

## 📈 Advanced Features

### Trend Analysis
```bash
curl "http://localhost:8001/api/v1/competitive/groups/1/trends?days=30"
```

### Batch Analysis
```bash
curl -X POST "http://localhost:8001/api/v1/competitive/batch-analysis"
```

### System Summary
```bash
curl "http://localhost:8001/api/v1/competitive/summary"
```

## 🔄 Workflow Examples

### Daily Competitive Monitoring
```bash
#!/bin/bash
# daily_competitive_check.sh

echo "Running daily competitive analysis..."

# Get all active groups
GROUPS=$(curl -s "http://localhost:8001/api/v1/competitive/groups" | jq '.[].id')

# Analyze each group
for group_id in $GROUPS; do
    echo "Analyzing group $group_id..."
    curl -X POST "http://localhost:8001/api/v1/competitive/groups/$group_id/analyze?include_llm_report=true" \
         > "reports/competitive_analysis_group_${group_id}_$(date +%Y%m%d).json"
done

echo "Analysis complete. Reports saved to reports/ directory."
```

### Price Alert Integration
```bash
# Check if main product loses price competitiveness
ANALYSIS=$(curl -s -X POST "http://localhost:8001/api/v1/competitive/groups/1/analyze")
PRICE_SCORE=$(echo $ANALYSIS | jq '.competitive_summary.competitive_scores.price_competitiveness')

if (( $(echo "$PRICE_SCORE < 50" | bc -l) )); then
    echo "Alert: Price competitiveness below 50%. Consider price adjustment."
fi
```

## 🎨 Customization

### Adding Custom Metrics
Extend the analyzer with custom competitive metrics:
```python
# src/competitive/analyzer.py
def _analyze_custom_metric(self, main_product, competitors):
    # Custom analysis logic
    return {
        "custom_score": calculated_score,
        "reasoning": "Analysis explanation"
    }
```

### Custom LLM Prompts
Modify AI analysis prompts in:
```python
# src/competitive/llm_reporter.py
def _create_analysis_prompt(self, analysis_data):
    # Customize prompt for specific industry/product type
    prompt = f"""
    Analyze the following {industry_type} market data:
    {analysis_data}
    
    Focus on {specific_analysis_aspects}...
    """
    return prompt
```

## ⚡ Performance Tips

### Caching Strategy
- Analysis results cached for 1 hour
- Use `refresh=true` parameter to force new analysis
- Clear cache for updated competitor data

### Batch Processing
- Use quick-setup for multiple groups
- Batch analysis for daily reports
- Schedule analysis during off-peak hours

## 🚨 Troubleshooting

### Common Issues

1. **No competitor data found**
   - Ensure ASINs are in tracking list
   - Run product tracking first: `POST /api/v1/products/track-all`

2. **LLM analysis fails**
   - Check OpenAI API key configuration
   - Fallback to structured analysis automatically

3. **Analysis takes too long**
   - Reduce number of competitors (3-5 optimal)
   - Check network connectivity to Amazon

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 start_api.py
```

## 📚 API Reference

### Complete Endpoint List
- `POST /api/v1/competitive/quick-setup` - One-click group setup
- `GET /api/v1/competitive/groups` - List all groups
- `POST /api/v1/competitive/groups/{id}/analyze` - Run analysis
- `GET /api/v1/competitive/groups/{id}/report` - Get LLM report
- `POST /api/v1/competitive/batch-analysis` - Analyze all groups
- `GET /api/v1/competitive/summary` - System overview

For complete API documentation, visit: `http://localhost:8001/docs`

## 🎯 Use Cases

### E-commerce Sellers
- Monitor competitor pricing strategies
- Identify market positioning opportunities
- Track product feature gaps
- Generate strategic action plans

### Market Researchers
- Analyze market dynamics
- Competitive landscape mapping
- Trend identification
- Performance benchmarking

### Product Managers
- Feature development prioritization
- Pricing strategy optimization
- Market entry analysis
- Competitive intelligence gathering