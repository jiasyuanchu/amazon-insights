# Amazon Insights

Amazon 產品資料追蹤系統 - 使用 Firecrawl API 追蹤 Amazon 產品的價格、BSR、評分和評論數變化。

## 功能特色

- 🔍 **真實資料擷取**: 使用 Firecrawl API 獲取真實 Amazon 產品資料
- 📊 **多維度監控**: 追蹤價格、BSR、評分、評論數、Buy Box 價格
- 🚨 **異常偵測**: 自動偵測顯著變化並發送警報
- 📈 **歷史趨勢**: 儲存和分析產品資料的歷史變化
- ⏰ **定時監控**: 支援每日自動監控和即時追蹤

## 安裝和設定

1. **安裝 Redis**:
```bash
# macOS (using Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# 檢查 Redis 狀態
redis-cli ping
```

2. **安裝 Python 依賴**:
```bash
pip3 install -r requirements.txt
```

3. **環境變數設定**:
複製 `.env.example` 為 `.env` 並設定配置:
```bash
cp .env.example .env
# 編輯 .env 並加入你的設定
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=True
```

4. **測試系統**:
```bash
python3 test_tracker.py
python3 cache_manager.py test
```

## 使用方法

### CLI 模式

#### 追蹤單一產品
```bash
python3 main.py track-single --asin B07R7RMQF5
```

#### 追蹤所有配置的產品
```bash
python3 main.py track-all
```

#### 開始持續監控
```bash
python3 main.py monitor
```

#### 查看最近的警報
```bash
python3 main.py alerts
```

#### 查看產品歷史
```bash
python3 main.py history --asin B07R7RMQF5
```

### RESTful API 模式

#### 啟動 API 服務器
```bash
python3 start_api.py
```

API 服務器將在 `http://localhost:8001` 啟動

#### API 文件
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **API 文件**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Postman 集合**: [postman_collection.json](postman_collection.json)
- **Postman 測試指南**: [POSTMAN_TESTING_GUIDE.md](POSTMAN_TESTING_GUIDE.md)

#### 主要 API 端點
- `POST /api/v1/products/track/{asin}` - 追蹤單一產品
- `POST /api/v1/products/track-all` - 追蹤所有產品
- `GET /api/v1/products/summary/{asin}` - 取得產品摘要
- `GET /api/v1/products/history/{asin}` - 取得產品歷史
- `GET /api/v1/alerts/` - 取得警報摘要
- `GET /api/v1/system/status` - 系統狀態

## 監控的 ASIN

系統預設監控以下產品（共 14 個）:
- B07R7RMQF5, B092XMWXK7, B0BVY8K28Q, B0CSMV2DTV, B0D3XDR3NN
- B0CM22ZRTT, B08SLQ9LFD, B08VWJB2GZ, B0DHKCM18G, B07RKV9Z9D
- B08136DWMT, B01CI6SO1A, B092HVLSP5, B0016BWUGE

## 專案結構

```
amazon-insights/
├── src/
│   ├── api/              # Firecrawl API 整合
│   ├── cache/            # Redis 快取系統
│   ├── parsers/          # Amazon 資料解析器
│   ├── models/           # 資料庫模型
│   └── monitoring/       # 監控和異常偵測
├── api/
│   └── routes/           # FastAPI 路由
├── config/               # 配置檔案
├── data/                 # 資料庫檔案
├── logs/                 # 日誌檔案
├── main.py               # CLI 主程式
├── app.py                # API 主程式
├── cache_manager.py      # 快取管理工具
├── test_cache.py         # 快取測試
└── test_tracker.py       # 系統測試
```

## 資料追蹤項目

- **品名**: 產品標題
- **價格變化**: 目前價格和歷史趨勢
- **BSR 趨勢**: 各類別的排名變化
- **評分與評論數變化**: 星級評分和評論數量
- **Buy Box 價格**: 主要銷售價格
- **庫存狀態**: 是否有貨

## 異常偵測

系統自動偵測以下異常:
- 價格大幅變動 (預設 >10%)
- BSR 排名顯著變化 (預設 >20%)
- 評分突然變化 (>0.5 星)
- 評論數激增 (>100 則新評論)
- 庫存狀態變化

## 技術架構

- **後端**: Python 3.7+
- **資料庫**: SQLAlchemy + SQLite
- **快取系統**: Redis (24-48 小時快取)
- **API**: Firecrawl API + FastAPI
- **解析**: BeautifulSoup + 正則表達式
- **監控**: 定時任務 + 異常偵測算法

## Redis 快取系統

系統使用 Redis 提供高效能快取，大幅提升查詢速度：

### 快取策略
- **產品摘要**: 24 小時 TTL
- **產品歷史**: 48 小時 TTL  
- **警報資訊**: 1 小時 TTL
- **系統狀態**: 5 分鐘 TTL

### 快取管理
```bash
# 查看快取資訊
python3 cache_manager.py info

# 清空所有快取
python3 cache_manager.py clear-all

# 清空特定產品快取
python3 cache_manager.py clear-product --asin B07R7RMQF5

# 預熱快取
python3 cache_manager.py warm-up

# 測試快取功能
python3 cache_manager.py test
```