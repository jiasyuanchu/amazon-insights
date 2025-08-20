# Postman Testing Guide

## Import Postman Collection

1. Open Postman
2. Click the "Import" button
3. Select the `postman_collection.json` file
4. After import, you'll see the "Amazon Insights API" collection

## Environment Variables

The collection is pre-configured with the `baseUrl` variable:
- **baseUrl**: `http://localhost:8001`

If you need to modify the port, adjust it in Postman's environment variables.

## Recommended Testing Order

### 1. Basic Health Check
```
GET {{baseUrl}}/health
```
Expected response:
```json
{
    "status": "healthy"
}
```

### 2. System Status Check
```
GET {{baseUrl}}/api/v1/system/status
```
Expected response: Contains system status, database connection status, Firecrawl availability, and other information

### 3. View Monitoring List
```
GET {{baseUrl}}/api/v1/products/list
```
Expected response: Returns 10 default monitored ASINs

### 4. Get Product Summary with Existing Data
```
GET {{baseUrl}}/api/v1/products/summary/B07R7RMQF5
```
This ASIN should have data since we've tested it before

### 5. View Product History
```
GET {{baseUrl}}/api/v1/products/history/B07R7RMQF5?limit=10
```
Expected response: Historical price data for the product

### 6. Get Alert Summary
```
GET {{baseUrl}}/api/v1/alerts/?hours=24
```
Expected response: Recent alert summary

### 7. Test Cache Information
```
GET {{baseUrl}}/api/v1/cache/info
```
Expected response: Redis cache status and information

### 8. Track Single Product (May take time)
```
POST {{baseUrl}}/api/v1/products/track/B07R7RMQF5
```
⚠️ Note: This request may take 30-60 seconds as it fetches real data from Amazon

### 9. Track All Products (Takes longest time)
```
POST {{baseUrl}}/api/v1/products/track-all
```
⚠️ Note: This will take several minutes as it tracks all configured products

### 10. System Test
```
POST {{baseUrl}}/api/v1/system/test
```
Expected response: Comprehensive system component test results

## Expected Response Formats

### Product Summary
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

### Tracking Result
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

## Error Scenarios to Test

### 1. Invalid ASIN
```
GET {{baseUrl}}/api/v1/products/summary/INVALIDASIN
```
Expected: 404 or 500 error

### 2. Non-existent Product History
```
GET {{baseUrl}}/api/v1/products/history/NONEXISTENT
```
Expected: Empty history or appropriate error message

### 3. Invalid Cache Pattern
```
POST {{baseUrl}}/api/v1/cache/clear/invalid-pattern-test
```
Expected: Appropriate error handling

## Performance Testing

### Expected Response Times
- Health check: < 100ms
- Product summary (cached): < 200ms
- Product summary (uncached): < 500ms
- Single product tracking: 30-60 seconds
- Batch tracking: 5-15 minutes

### Cache Testing Workflow
1. Clear specific product cache:
   ```
   POST {{baseUrl}}/api/v1/cache/clear/product/B07R7RMQF5
   ```

2. Request product summary (should be slow):
   ```
   GET {{baseUrl}}/api/v1/products/summary/B07R7RMQF5
   ```

3. Request same summary again (should be fast):
   ```
   GET {{baseUrl}}/api/v1/products/summary/B07R7RMQF5
   ```

## Troubleshooting

### Common Issues

1. **API Server Not Running**
   - Error: Connection refused
   - Solution: Start API server with `python3 start_api.py`

2. **Redis Not Available**
   - Error: Cache-related endpoints fail
   - Solution: Start Redis service

3. **Firecrawl API Issues**
   - Error: Tracking requests fail
   - Solution: Check FIRECRAWL_API_KEY environment variable

4. **Database Issues**
   - Error: Product summary endpoints fail
   - Solution: Check database file permissions

### Debug Information

Enable detailed logging by checking:
- API server console output
- `logs/` directory for log files
- System status endpoint for component health

## Advanced Testing

### Load Testing
Test concurrent requests using Postman's Collection Runner:
1. Select the collection
2. Set iterations to 10+
3. Add delay between requests
4. Monitor system performance

### Automation
Set up automated tests using Postman's testing scripts:
```javascript
// Example test script for product summary
pm.test("Product summary returns valid data", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property('asin');
    pm.expect(response).to.have.property('title');
    pm.expect(response.current_price).to.be.a('number');
});
```