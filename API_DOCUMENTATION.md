# Amazon Insights RESTful API

## 啟動 API 服務器

```bash
python3 start_api.py
```

API 服務器將在 `http://localhost:8001` 啟動

## API 文件

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health
- **Postman Collection**: [postman_collection.json](postman_collection.json)

## API 端點

### 1. 產品追蹤 (Products)

#### 追蹤單一產品
- **URL**: `POST /api/v1/products/track/{asin}`
- **描述**: 追蹤指定 ASIN 的產品
- **參數**: 
  - `asin` (path): Amazon ASIN (例如: B07R7RMQF5)
- **回應**: TrackingResult

```bash
# 範例
POST http://localhost:8001/api/v1/products/track/B07R7RMQF5
```

#### 追蹤所有產品
- **URL**: `POST /api/v1/products/track-all`
- **描述**: 追蹤所有配置的產品
- **回應**: BatchTrackingResult

```bash
POST http://localhost:8001/api/v1/products/track-all
```

#### 取得產品摘要
- **URL**: `GET /api/v1/products/summary/{asin}`
- **描述**: 取得指定產品的摘要資訊
- **參數**: 
  - `asin` (path): Amazon ASIN
- **回應**: ProductSummary

```bash
GET http://localhost:8001/api/v1/products/summary/B07R7RMQF5
```

#### 取得所有產品摘要
- **URL**: `GET /api/v1/products/summary`
- **描述**: 取得所有產品的摘要資訊
- **回應**: List[ProductSummary]

```bash
GET http://localhost:8001/api/v1/products/summary
```

#### 取得產品歷史
- **URL**: `GET /api/v1/products/history/{asin}`
- **描述**: 取得指定產品的價格歷史
- **參數**: 
  - `asin` (path): Amazon ASIN
  - `limit` (query, optional): 限制回傳筆數 (預設: 20)
- **回應**: PriceHistory

```bash
GET http://localhost:8001/api/v1/products/history/B07R7RMQF5?limit=10
```

#### 取得監控清單
- **URL**: `GET /api/v1/products/list`
- **描述**: 取得所有監控的 ASIN 清單
- **回應**: List[str]

```bash
GET http://localhost:8001/api/v1/products/list
```

### 2. 警報 (Alerts)

#### 取得警報摘要
- **URL**: `GET /api/v1/alerts/`
- **描述**: 取得最近的警報摘要
- **參數**: 
  - `hours` (query, optional): 時間範圍 (預設: 24)
- **回應**: AlertsSummary

```bash
GET http://localhost:8001/api/v1/alerts/?hours=48
```

#### 取得最近警報
- **URL**: `GET /api/v1/alerts/recent`
- **描述**: 取得最近的警報清單
- **參數**: 
  - `hours` (query, optional): 時間範圍 (預設: 24)
  - `limit` (query, optional): 限制回傳筆數 (預設: 50)
- **回應**: List[Alert]

```bash
GET http://localhost:8001/api/v1/alerts/recent?hours=24&limit=10
```

#### 取得特定產品警報
- **URL**: `GET /api/v1/alerts/{asin}`
- **描述**: 取得指定 ASIN 的警報
- **參數**: 
  - `asin` (path): Amazon ASIN
  - `hours` (query, optional): 時間範圍 (預設: 24)
- **回應**: List[Alert]

```bash
GET http://localhost:8001/api/v1/alerts/B07R7RMQF5?hours=24
```

### 3. 系統 (System)

#### 系統狀態
- **URL**: `GET /api/v1/system/status`
- **描述**: 取得系統狀態
- **回應**: SystemStatus

```bash
GET http://localhost:8001/api/v1/system/status
```

#### 健康檢查
- **URL**: `GET /api/v1/system/health`
- **描述**: 簡單的健康檢查
- **回應**: JSON

```bash
GET http://localhost:8001/api/v1/system/health
```

#### 系統測試
- **URL**: `POST /api/v1/system/test`
- **描述**: 測試系統各個組件
- **回應**: JSON

```bash
POST http://localhost:8001/api/v1/system/test
```

### 4. 快取管理 (Cache)

#### 查看快取資訊
- **URL**: `GET /api/v1/cache/info`
- **描述**: 取得 Redis 快取系統資訊
- **回應**: JSON

```bash
GET http://localhost:8001/api/v1/cache/info
```

#### 快取統計
- **URL**: `GET /api/v1/cache/stats`
- **描述**: 取得詳細快取統計資訊
- **回應**: JSON

```bash
GET http://localhost:8001/api/v1/cache/stats
```

#### 清除所有快取
- **URL**: `POST /api/v1/cache/clear/all`
- **描述**: 清除所有快取資料
- **回應**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/all
```

#### 清除特定產品快取
- **URL**: `POST /api/v1/cache/clear/product/{asin}`
- **描述**: 清除指定產品的所有相關快取
- **參數**: 
  - `asin` (path): Amazon ASIN
- **回應**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/product/B07R7RMQF5
```

#### 清除模式快取
- **URL**: `POST /api/v1/cache/clear/{pattern}`
- **描述**: 清除符合模式的快取鍵
- **參數**: 
  - `pattern` (path): 搜尋模式
- **回應**: JSON

```bash
POST http://localhost:8001/api/v1/cache/clear/product
```

## 資料結構

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

## Postman 測試集合

建議建立以下 Postman 請求：

1. **Health Check**
   - GET http://localhost:8001/health

2. **系統狀態**
   - GET http://localhost:8001/api/v1/system/status

3. **追蹤單一產品**
   - POST http://localhost:8001/api/v1/products/track/B07R7RMQF5

4. **取得產品摘要**
   - GET http://localhost:8001/api/v1/products/summary/B07R7RMQF5

5. **取得產品歷史**
   - GET http://localhost:8001/api/v1/products/history/B07R7RMQF5

6. **取得警報摘要**
   - GET http://localhost:8001/api/v1/alerts/

7. **追蹤所有產品**
   - POST http://localhost:8001/api/v1/products/track-all

## 錯誤處理

API 使用標準的 HTTP 狀態碼：

- `200`: 成功
- `404`: 資源未找到
- `500`: 內部服務器錯誤

錯誤回應格式：
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "details": "具體錯誤信息"
}
```

## CORS 設定

API 已設定允許所有來源的跨域請求，適合開發環境使用。在生產環境中應該限制允許的來源。