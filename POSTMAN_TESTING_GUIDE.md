# Postman 測試指南

## 匯入 Postman 集合

1. 開啟 Postman
2. 點選 "Import" 按鈕
3. 選擇 `postman_collection.json` 檔案
4. 匯入完成後，你會看到 "Amazon Insights API" 集合

## 環境變數

集合已經預設配置了 `baseUrl` 變數：
- **baseUrl**: `http://localhost:8001`

如果需要修改端口，可以在 Postman 的環境變數中調整。

## 建議的測試順序

### 1. 基本健康檢查
```
GET {{baseUrl}}/health
```
預期回應：
```json
{
    "status": "healthy"
}
```

### 2. 系統狀態檢查
```
GET {{baseUrl}}/api/v1/system/status
```
預期回應：包含系統狀態、資料庫連線狀態、Firecrawl 可用性等資訊

### 3. 查看監控清單
```
GET {{baseUrl}}/api/v1/products/list
```
預期回應：返回 10 個預設監控的 ASIN

### 4. 取得已有資料的產品摘要
```
GET {{baseUrl}}/api/v1/products/summary/B07R7RMQF5
```
這個 ASIN 應該已經有資料，因為我們之前測試過

### 5. 查看產品歷史
```
GET {{baseUrl}}/api/v1/products/history/B07R7RMQF5?limit=10
```
顯示該產品的價格歷史記錄

### 6. 追蹤單一產品
```
POST {{baseUrl}}/api/v1/products/track/B07R7RMQF5
```
重新追蹤已知的產品（較快成功）

### 7. 查看警報摘要
```
GET {{baseUrl}}/api/v1/alerts/?hours=24
```
查看最近 24 小時的警報

### 8. 查看所有產品摘要
```
GET {{baseUrl}}/api/v1/products/summary
```
取得所有產品的摘要資訊

## 注意事項

1. **API 限制**: Firecrawl API 在免費方案下有限制，可能會遇到超時
2. **追蹤新產品**: 第一次追蹤新的 ASIN 可能需要較長時間或失敗
3. **已有資料**: B07R7RMQF5 已經有歷史資料，測試時較為穩定

## 常見回應格式

### 成功的產品摘要
```json
{
    "asin": "B07R7RMQF5",
    "title": "Product summary presents key product information",
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
    "last_updated": "2025-08-20T16:58:33.548102",
    "history_count": 3
}
```

### 追蹤結果
```json
{
    "success": true,
    "message": "Successfully tracked product B07R7RMQF5",
    "asin": "B07R7RMQF5",
    "product_summary": {
        // ProductSummary 物件
    }
}
```

### 系統狀態
```json
{
    "status": "healthy",
    "database_connected": true,
    "firecrawl_available": true,
    "monitored_asins": ["B07R7RMQF5", "B092XMWXK7", ...],
    "last_check": "2025-08-20T17:09:51.589730"
}
```

## 故障排除

1. **連接錯誤**: 確認 API 服務器正在運行 (`python3 start_api.py`)
2. **404 錯誤**: 檢查 URL 路徑是否正確
3. **500 錯誤**: 查看服務器日誌以了解詳細錯誤資訊
4. **超時錯誤**: Firecrawl API 限制，稍後再試

## API 文件

完整的 API 文件可在以下位置查看：
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc