# Amazon Insights RESTful API

## Starting API Server

```bash
python3 start_api.py
```

API server will start at `http://localhost:8001`

## API Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health
- **Postman Collection**: [postman_collection.json](postman_collection.json)

## API Endpoints

### 1. Product Tracking (Products)

#### Track Single Product
- **URL**: `POST /api/v1/products/track/{asin}`
- **Description**: Track a specific product by ASIN
- **Parameters**: 
  - `asin` (path): Amazon ASIN (e.g.: B07R7RMQF5)
- **Response**: TrackingResult

```bash
# Example
POST http://localhost:8001/api/v1/products/track/B07R7RMQF5
```

#### Track All Products
- **URL**: `POST /api/v1/products/track-all`
- **Description**: Track all configured products
- **Response**: BatchTrackingResult

```bash
POST http://localhost:8001/api/v1/products/track-all
```

#### Get Product Summary
- **URL**: `GET /api/v1/products/summary/{asin}`
- **Description**: Get summary information for a specific product
- **Parameters**: 
  - `asin` (path): Amazon ASIN
- **Response**: ProductSummary

```bash
GET http://localhost:8001/api/v1/products/summary/B07R7RMQF5
```

#### Get All Product Summaries
- **URL**: `GET /api/v1/products/summary`
- **Description**: Get summary information for all products
- **Response**: List[ProductSummary]

```bash
GET http://localhost:8001/api/v1/products/summary
```

#### Get Product History
- **URL**: `GET /api/v1/products/history/{asin}`
- **Description**: Get price history for a specific product
- **Parameters**: 
  - `asin` (path): Amazon ASIN
  - `limit` (query, optional): Limit number of records (default: 20)
- **Response**: PriceHistory

```bash
GET http://localhost:8001/api/v1/products/history/B07R7RMQF5?limit=10
```

#### Get Monitoring List
- **URL**: `GET /api/v1/products/list`
- **Description**: Get list of all monitored ASINs
- **Response**: List[str]

```bash
GET http://localhost:8001/api/v1/products/list
```

### 2. Alerts

#### Get Alert Summary
- **URL**: `GET /api/v1/alerts/`
- **Description**: Get recent alert summary
- **Parameters**: 
  - `hours` (query, optional): Time range in hours (default: 24)
- **Response**: AlertsSummary

```bash
GET http://localhost:8001/api/v1/alerts/?hours=48
```

#### Get Recent Alerts
- **URL**: `GET /api/v1/alerts/recent`
- **Description**: Get list of recent alerts
- **Parameters**: 
  - `hours` (query, optional): Time range in hours (default: 24)
  - `limit` (query, optional): Limit number of records (default: 50)
- **Response**: List[Alert]

```bash
GET http://localhost:8001/api/v1/alerts/recent?hours=24&limit=10
```

#### Get Product-Specific Alerts
- **URL**: `GET /api/v1/alerts/{asin}`
- **Description**: Get alerts for a specific ASIN
- **Parameters**: 
  - `asin` (path): Amazon ASIN
  - `hours` (query, optional): Time range in hours (default: 24)
- **Response**: List[Alert]

```bash
GET http://localhost:8001/api/v1/alerts/B07R7RMQF5?hours=24
```

### 3. System

#### System Status
- **URL**: `GET /api/v1/system/status`
- **Description**: Get system status
- **Response**: SystemStatus

```bash
GET http://localhost:8001/api/v1/system/status
```

#### Health Check
- **URL**: `GET /api/v1/system/health`
- **Description**: Simple health check
- **Response**: JSON

```bash
GET http://localhost:8001/api/v1/system/health
```

#### System Test
- **URL**: `POST /api/v1/system/test`
- **Description**: Test system components
- **Response**: JSON

```bash
POST http://localhost:8001/api/v1/system/test
```

### 4. Cache Management

#### View Cache Information
- **URL**: `GET /api/v1/cache/info`
- **Description**: Get Redis cache system information
- **Response**: JSON

```bash
GET http://localhost:8001/api/v1/cache/info
```

#### Cache Statistics
- **URL**: `GET /api/v1/cache/stats`
- **Description**: Get detailed cache statistics
- **Response**: JSON

```bash
GET http://localhost:8001/api/v1/cache/stats
```

#### Clear All Cache
- **URL**: `POST /api/v1/cache/clear/all`
- **Description**: Clear all cache data
- **Response**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/all
```

#### Clear Product-Specific Cache
- **URL**: `POST /api/v1/cache/clear/product/{asin}`
- **Description**: Clear all cache related to a specific product
- **Parameters**: 
  - `asin` (path): Amazon ASIN
- **Response**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/product/B07R7RMQF5
```

#### Clear Pattern-Based Cache
- **URL**: `POST /api/v1/cache/clear/{pattern}`
- **Description**: Clear cache keys matching a pattern
- **Parameters**: 
  - `pattern` (path): Search pattern
- **Response**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/product
```

## Data Structures

### ProductSummary
```json
{
  "asin": "B07R7RMQF5",
  "title": "Yoga Mat 1-Inch Extra Thick...",
  "current_price": 34.99,
  "current_rating": 4.7,
  "current_review_count": 18451,
  "bsr_data": {
    "Sports & Outdoors": 1776,
    "[Exercise Mats]": 3,
    "[Yoga Mats]": 18
  },
  "availability": "In Stock",
  "price_trend": "stable",
  "last_updated": "2025-08-20T16:56:40.305805",
  "history_count": 2
}
```

### TrackingResult
```json
{
  "success": true,
  "message": "Successfully tracked product B07R7RMQF5",
  "asin": "B07R7RMQF5",
  "product_summary": {
    // ProductSummary object
  }
}
```

### Alert
```json
{
  "id": 1,
  "asin": "B07R7RMQF5",
  "alert_type": "price_change",
  "old_value": 34.0,
  "new_value": 34.99,
  "change_percentage": 2.91,
  "message": "Price increased by 2.91%",
  "triggered_at": "2025-08-20T16:56:40.305805"
}
```

## Postman Test Collection

Recommended Postman requests to create:

1. **Health Check**
   - GET http://localhost:8001/health

2. **System Status**
   - GET http://localhost:8001/api/v1/system/status

3. **Track Single Product**
   - POST http://localhost:8001/api/v1/products/track/B07R7RMQF5

4. **Get Product Summary**
   - GET http://localhost:8001/api/v1/products/summary/B07R7RMQF5

5. **Get Product History**
   - GET http://localhost:8001/api/v1/products/history/B07R7RMQF5

6. **Get Alert Summary**
   - GET http://localhost:8001/api/v1/alerts/

7. **Track All Products**
   - POST http://localhost:8001/api/v1/products/track-all

## Error Handling

API uses standard HTTP status codes:

- `200`: Success
- `404`: Resource not found
- `500`: Internal server error

Error response format:
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "details": "Specific error information"
}
```

## CORS Configuration

The API is configured to allow cross-origin requests from all origins, suitable for development environment. In production, allowed origins should be restricted.