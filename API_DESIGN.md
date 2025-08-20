# Amazon Insights API Design Documentation

## Overview

The Amazon Insights API is designed following REST principles with a focus on scalability, security, and developer experience. This document outlines the complete API design including authentication, rate limiting, error handling, and all endpoint specifications.

## API Design Principles

### 1. RESTful Design
- **Resource-based URLs**: Clear noun-based resource identification
- **HTTP Methods**: Proper use of GET, POST, PUT, DELETE, PATCH
- **Status Codes**: Meaningful HTTP status codes for all responses
- **Stateless**: No server-side session state

### 2. Consistency
- **Naming Convention**: snake_case for JSON fields, kebab-case for URLs
- **Response Format**: Standardized response structure across all endpoints
- **Error Format**: Consistent error response schema
- **Versioning**: URL-based versioning (v1, v2, etc.)

### 3. Security First
- **Authentication**: API Key authentication with Bearer tokens
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: Per-key rate limiting with different tiers
- **Data Validation**: Comprehensive input validation and sanitization

## Authentication & Authorization

### API Key Authentication

#### Authentication Flow
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Redis
    
    Client->>API: Request with Authorization header
    API->>Auth: Extract and validate API key
    Auth->>Redis: Check key validity and permissions
    Redis-->>Auth: Return key metadata
    Auth-->>API: Authentication result + user context
    API->>API: Process request with user context
    API-->>Client: Response with rate limit headers
```

#### Authentication Headers
```http
Authorization: Bearer sk_live_1234567890abcdef
X-API-Version: v1
Content-Type: application/json
```

#### API Key Types
- **Public Keys** (`pk_`): Read-only access to public endpoints
- **Secret Keys** (`sk_`): Full access to all endpoints
- **Admin Keys** (`ak_`): Administrative access including user management

### Role-Based Access Control

#### Permission Matrix
| Endpoint | Public Key | Secret Key | Admin Key |
|----------|------------|------------|-----------|
| GET /products/summary | ✅ | ✅ | ✅ |
| POST /products/track | ❌ | ✅ | ✅ |
| POST /competitive/analyze | ❌ | ✅ | ✅ |
| DELETE /competitive/groups | ❌ | ❌ | ✅ |
| GET /admin/users | ❌ | ❌ | ✅ |

#### Permission Scopes
- **read:products**: View product summaries and history
- **write:products**: Track and modify product data
- **read:competitive**: View competitive analysis results
- **write:competitive**: Create and manage competitive groups
- **admin:system**: System administration and user management

## Rate Limiting

### Rate Limiting Strategy

#### Tier-based Limits
```json
{
  "tiers": {
    "free": {
      "requests_per_minute": 60,
      "requests_per_hour": 1000,
      "requests_per_day": 10000,
      "concurrent_requests": 5
    },
    "pro": {
      "requests_per_minute": 300,
      "requests_per_hour": 10000,
      "requests_per_day": 100000,
      "concurrent_requests": 20
    },
    "enterprise": {
      "requests_per_minute": 1000,
      "requests_per_hour": 50000,
      "requests_per_day": 1000000,
      "concurrent_requests": 100
    }
  }
}
```

#### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
X-RateLimit-Tier: pro
Retry-After: 60
```

#### Rate Limiting Algorithm
- **Sliding Window Log**: Precise rate limiting with Redis sorted sets
- **Token Bucket**: Burst handling for enterprise customers
- **Distributed Counting**: Redis-based distributed rate limiting

### Endpoint-Specific Limits
```json
{
  "endpoint_limits": {
    "/api/v1/products/track/{asin}": {
      "weight": 10,
      "description": "Expensive operation due to external API calls"
    },
    "/api/v1/competitive/analyze": {
      "weight": 50,
      "description": "Heavy computational analysis"
    },
    "/api/v1/products/summary/{asin}": {
      "weight": 1,
      "description": "Lightweight read operation"
    }
  }
}
```

## Standard Response Format

### Success Response Structure
```json
{
  "success": true,
  "data": {
    // Actual response data
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_1234567890",
    "execution_time_ms": 150,
    "version": "v1"
  },
  "pagination": {  // Only for paginated responses
    "page": 1,
    "per_page": 20,
    "total": 150,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzfQ=="
  }
}
```

### Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "asin",
        "message": "ASIN must be 10 characters long",
        "code": "INVALID_LENGTH"
      }
    ],
    "request_id": "req_1234567890",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Error Handling

### HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource successfully created
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate creation)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **502 Bad Gateway**: External service error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Codes
```json
{
  "error_codes": {
    "AUTHENTICATION_REQUIRED": "API key is required",
    "INVALID_API_KEY": "API key is invalid or expired",
    "PERMISSION_DENIED": "Insufficient permissions for this operation",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded for your tier",
    "VALIDATION_ERROR": "Request validation failed",
    "RESOURCE_NOT_FOUND": "Requested resource not found",
    "EXTERNAL_SERVICE_ERROR": "External service temporarily unavailable",
    "DUPLICATE_RESOURCE": "Resource already exists",
    "QUOTA_EXCEEDED": "Account quota exceeded"
  }
}
```

## API Endpoints Specification

### 1. Product Tracking Endpoints

#### Track Single Product
```http
POST /api/v1/products/track/{asin}
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Parameters:**
- `asin` (path): Amazon ASIN identifier

**Request Body:**
```json
{
  "priority": "high",  // high, normal, low
  "notify": true,      // Send notifications on completion
  "metadata": {
    "source": "manual",
    "campaign": "competitive_research"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tracking_id": "track_1234567890",
    "asin": "B07R7RMQF5",
    "status": "queued",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "product_summary": {
      // Product data if immediately available
    }
  }
}
```

#### Get Product Summary
```http
GET /api/v1/products/summary/{asin}
Authorization: Bearer {api_key}
```

**Query Parameters:**
- `include_history` (boolean): Include price history summary
- `include_competitors` (boolean): Include competitor information
- `cache_refresh` (boolean): Force cache refresh

**Response:**
```json
{
  "success": true,
  "data": {
    "asin": "B07R7RMQF5",
    "title": "Yoga Mat 1-Inch Extra Thick Pro Yoga Mat",
    "current_price": 34.99,
    "price_currency": "USD",
    "current_rating": 4.7,
    "current_review_count": 18451,
    "bsr_data": {
      "Sports & Outdoors": 1776,
      "[Exercise Mats]": 3,
      "[Yoga Mats]": 18
    },
    "availability": "In Stock",
    "brand": "BalanceFrom",
    "category": "Sports & Outdoors > Exercise & Fitness > Yoga",
    "price_trend": "stable",
    "last_updated": "2024-01-15T09:30:00Z",
    "data_freshness_hours": 2,
    "history_summary": {
      "price_range_30d": {"min": 29.99, "max": 39.99},
      "rating_change_30d": 0.1,
      "review_growth_30d": 234
    }
  }
}
```

### 2. Competitive Analysis Endpoints

#### Create Competitive Group
```http
POST /api/v1/competitive/groups
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Yoga Mat Market Analysis",
  "description": "Competitive analysis for premium yoga mat segment",
  "main_product_asin": "B07R7RMQF5",
  "competitors": [
    {
      "asin": "B092XMWXK7",
      "name": "Premium Yoga Mat A",
      "priority": 1
    },
    {
      "asin": "B0BVY8K28Q",
      "name": "Budget Alternative B",
      "priority": 2
    }
  ],
  "analysis_settings": {
    "include_ai_insights": true,
    "update_frequency": "daily",
    "alert_thresholds": {
      "price_change_percent": 5.0,
      "rating_change": 0.2,
      "rank_change_percent": 20.0
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Yoga Mat Market Analysis",
    "main_product_asin": "B07R7RMQF5",
    "competitors_count": 2,
    "created_at": "2024-01-15T10:30:00Z",
    "status": "active",
    "next_analysis": "2024-01-16T02:00:00Z"
  }
}
```

#### Run Competitive Analysis
```http
POST /api/v1/competitive/groups/{group_id}/analyze
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Query Parameters:**
- `include_llm_report` (boolean): Include AI-generated insights
- `refresh_data` (boolean): Force fresh data collection
- `analysis_depth` (string): basic, standard, comprehensive

**Request Body:**
```json
{
  "analysis_options": {
    "include_price_trends": true,
    "include_feature_analysis": true,
    "include_sentiment_analysis": false,
    "historical_period_days": 30
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_1234567890",
    "group_id": 123,
    "status": "completed",
    "generated_at": "2024-01-15T10:35:00Z",
    "execution_time_seconds": 45.2,
    "competitive_summary": {
      "competitive_scores": {
        "price_competitiveness": 75.2,
        "quality_competitiveness": 94.0,
        "popularity_competitiveness": 82.3,
        "overall_competitiveness": 83.8
      },
      "position_summary": {
        "price_position": "competitive",
        "quality_position": "superior",
        "popularity_position": "leading",
        "overall_position": "strong"
      },
      "market_insights": {
        "total_competitors": 4,
        "market_size_indicator": "large",
        "price_volatility": "low",
        "competitive_intensity": "high"
      }
    },
    "detailed_analysis": {
      "main_product": {
        // Product details
      },
      "competitors": [
        // Competitor details
      ],
      "price_analysis": {
        // Price positioning analysis
      },
      "rating_analysis": {
        // Quality analysis
      },
      "feature_comparison": {
        // Feature differentiation
      }
    },
    "ai_insights": {
      "executive_summary": "Your product demonstrates strong market positioning...",
      "swot_analysis": {
        "strengths": ["Superior customer satisfaction", "Competitive pricing"],
        "weaknesses": ["Limited color options"],
        "opportunities": ["Premium market expansion", "International markets"],
        "threats": ["New competitor entry", "Price competition"]
      },
      "strategic_recommendations": [
        {
          "category": "pricing",
          "priority": "high",
          "action": "Consider 5% price reduction to improve competitiveness",
          "rationale": "Analysis shows price sensitivity in target market",
          "expected_impact": "10-15% market share improvement",
          "implementation_timeline": "immediate"
        }
      ],
      "market_trends": [
        "Increasing demand for eco-friendly materials",
        "Premium segment showing 15% growth",
        "Color variety becoming key differentiator"
      ]
    }
  }
}
```

### 3. Alert Management Endpoints

#### Get Alert Summary
```http
GET /api/v1/alerts/summary
Authorization: Bearer {api_key}
```

**Query Parameters:**
- `time_range` (string): 1h, 24h, 7d, 30d
- `severity` (string): low, medium, high, critical
- `alert_type` (string): price_change, rating_change, rank_change, stock_change

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_alerts": 156,
      "critical_alerts": 3,
      "high_priority_alerts": 12,
      "unread_alerts": 45,
      "time_range": "24h"
    },
    "alert_breakdown": {
      "price_changes": 89,
      "rating_changes": 23,
      "rank_changes": 34,
      "stock_changes": 10
    },
    "trending_products": [
      {
        "asin": "B07R7RMQF5",
        "alert_count": 5,
        "latest_alert": "price_increase",
        "severity": "medium"
      }
    ],
    "recent_critical_alerts": [
      {
        "id": "alert_1234567890",
        "asin": "B092XMWXK7",
        "type": "significant_price_drop",
        "message": "Price dropped by 25% to $22.99",
        "severity": "critical",
        "triggered_at": "2024-01-15T09:45:00Z"
      }
    ]
  }
}
```

### 4. System & Health Endpoints

#### System Health Check
```http
GET /api/v1/system/health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.2.3",
    "uptime_seconds": 86400,
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 12,
        "connections_active": 15,
        "connections_max": 100
      },
      "redis_cache": {
        "status": "healthy",
        "memory_usage_mb": 256,
        "memory_max_mb": 1024,
        "hit_rate_percent": 94.5
      },
      "task_queue": {
        "status": "healthy",
        "pending_tasks": 23,
        "active_workers": 5,
        "failed_tasks_24h": 2
      },
      "external_apis": {
        "firecrawl": {
          "status": "healthy",
          "last_success": "2024-01-15T10:29:00Z",
          "success_rate_24h": 98.5
        },
        "openai": {
          "status": "healthy",
          "last_success": "2024-01-15T10:25:00Z",
          "success_rate_24h": 99.2
        }
      }
    },
    "performance_metrics": {
      "avg_response_time_ms": 185,
      "requests_per_minute": 450,
      "error_rate_percent": 0.05
    }
  }
}
```

## Pagination

### Cursor-based Pagination
```http
GET /api/v1/products/history/B07R7RMQF5?limit=20&cursor=eyJpZCI6MTIzLCJ0aW1lIjoxNjA5NDU5MjAwfQ==
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      // Historical data points
    ]
  },
  "pagination": {
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTAzLCJ0aW1lIjoxNjA5NDU4ODAwfQ==",
    "prev_cursor": "eyJpZCI6MTQzLCJ0aW1lIjoxNjA5NDU5NjAwfQ=="
  }
}
```

### Offset-based Pagination
```http
GET /api/v1/competitive/groups?page=2&per_page=25
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      // Competitive groups
    ]
  },
  "pagination": {
    "page": 2,
    "per_page": 25,
    "total_items": 150,
    "total_pages": 6,
    "has_next": true,
    "has_prev": true
  }
}
```

## Webhooks

### Webhook Configuration
```http
POST /api/v1/webhooks
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/amazon-insights",
  "events": [
    "product.tracking.completed",
    "competitive.analysis.completed",
    "alert.critical.triggered"
  ],
  "secret": "whsec_1234567890abcdef",
  "active": true,
  "metadata": {
    "description": "Production webhook for critical alerts"
  }
}
```

### Webhook Payload Example
```json
{
  "id": "evt_1234567890",
  "type": "product.tracking.completed",
  "created": 1609459200,
  "data": {
    "object": {
      "id": "track_1234567890",
      "asin": "B07R7RMQF5",
      "status": "completed",
      "changes_detected": [
        {
          "field": "price",
          "old_value": 34.99,
          "new_value": 32.99,
          "change_percent": -5.7
        }
      ]
    }
  }
}
```

## API Versioning

### Version Strategy
- **URL-based versioning**: `/api/v1/`, `/api/v2/`
- **Header-based override**: `X-API-Version: v2`
- **Backward compatibility**: Maintain v1 for 12 months after v2 release
- **Deprecation notices**: 6-month advance notice in response headers

### Version Lifecycle
```
v1 (Current) -> v1 (Deprecated) -> v1 (Sunset)
     |               |                 |
     v2 (Beta) -> v2 (Current) -> v2 (Deprecated)
```

## SDK Integration

### Official SDKs
- **Python SDK**: `pip install amazon-insights-sdk`
- **Node.js SDK**: `npm install amazon-insights`
- **Go SDK**: `go get github.com/amazon-insights/go-sdk`

### SDK Example Usage
```python
import amazon_insights

client = amazon_insights.Client(api_key='sk_live_...')

# Track a product
result = client.products.track('B07R7RMQF5')

# Run competitive analysis
analysis = client.competitive.analyze(group_id=123, include_ai=True)
```

## OpenAPI Specification

The complete API is documented using OpenAPI 3.0 specification, available at:
- **Interactive Documentation**: `https://api.amazon-insights.com/docs`
- **OpenAPI JSON**: `https://api.amazon-insights.com/openapi.json`
- **Redoc Documentation**: `https://api.amazon-insights.com/redoc`

## Performance Considerations

### Response Time Targets
- **Read Operations**: < 200ms (95th percentile)
- **Write Operations**: < 500ms (95th percentile)
- **Analysis Operations**: < 2 minutes (95th percentile)

### Optimization Strategies
- **Caching**: Multi-layer caching strategy
- **Database Optimization**: Query optimization and indexing
- **CDN**: Static asset delivery via CDN
- **Compression**: Gzip compression for all responses

### Rate Limiting Best Practices
- **Exponential Backoff**: Implement client-side retry with exponential backoff
- **Batch Operations**: Use batch endpoints when available
- **Caching**: Cache responses on client side when appropriate