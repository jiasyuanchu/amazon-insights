# 競品分析引擎使用指南

## 🚀 功能概述

Amazon Insights 競品分析引擎提供全面的多維度競品比較分析：

### 核心功能
- **主產品設定**: 設定賣家自己的產品作為基準
- **競品管理**: 添加 3-5 個競品進行對比分析
- **多維度分析**:
  - 價格差異分析與定位
  - BSR (Best Sellers Rank) 排名對比
  - 評分與評論數優劣勢
  - 產品特色對比 (從 bullet points 提取)
- **LLM 智能報告**: 使用 OpenAI GPT 生成競爭定位報告
- **API 完整支援**: 提供完整的 REST API 接口

## 📋 前置需求

### 1. 環境設定
```bash
# 安裝依賴
pip install -r requirements.txt

# 設定 OpenAI API Key (可選，沒有則使用結構化分析)
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. 追蹤設定
確保要分析的產品都在追蹤列表中：
```python
# config/config.py
AMAZON_ASINS = [
    "B07R7RMQF5",  # 主產品
    "B092XMWXK7",  # 競品1
    "B0BVY8K28Q",  # 競品2
    "B0CSMV2DTV",  # 競品3
]
```

## 🔧 使用方式

### 方式一：API 快速設定 (推薦)
```bash
curl -X POST "http://localhost:8000/api/v1/competitive/quick-setup" \
  -H "Content-Type: application/json" \
  -d '{
    "main_product_asin": "B07R7RMQF5",
    "competitor_asins": ["B092XMWXK7", "B0BVY8K28Q", "B0CSMV2DTV"],
    "group_name": "瑜伽墊市場競品分析",
    "description": "針對高端瑜伽墊市場的競爭對手分析"
  }'
```

### 方式二：逐步建立
```bash
# 1. 建立競品組
curl -X POST "http://localhost:8000/api/v1/competitive/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "瑜伽墊競品分析",
    "main_product_asin": "B07R7RMQF5",
    "description": "瑜伽墊市場競爭分析"
  }'

# 2. 添加競品 (使用返回的 group_id)
curl -X POST "http://localhost:8000/api/v1/competitive/groups/1/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B092XMWXK7",
    "competitor_name": "高端瑜伽墊 A",
    "priority": 1
  }'
```

### 方式三：Python 腳本
```bash
# 執行展示腳本
python demo_competitive_workflow.py
```

## 📊 執行分析

### 1. 基礎分析
```bash
curl -X POST "http://localhost:8000/api/v1/competitive/groups/1/analyze"
```

### 2. 包含 LLM 報告的完整分析
```bash
curl -X POST "http://localhost:8000/api/v1/competitive/groups/1/analyze?include_llm_report=true"
```

### 3. 獲取詳細定位報告
```bash
curl -X GET "http://localhost:8000/api/v1/competitive/groups/1/report"
```

## 📈 分析結果說明

### 價格分析 (Price Analysis)
- **價格定位**: lowest/middle/highest
- **價格優勢**: 是否具有價格競爭力
- **市場價格區間**: 最低價、最高價、平均價
- **競品價格差異**: 與各競品的價格差距百分比

### BSR 排名分析 (BSR Analysis)
- **各類別排名**: 在不同 Amazon 類別中的排名
- **排名定位**: best/middle/worst
- **排名統計**: 最佳排名、平均排名、排名分布

### 評分分析 (Rating Analysis)
- **質量定位**: 評分在市場中的相對位置
- **評分優勢**: 是否高於市場平均
- **評論數量**: 受歡迎程度指標
- **質量vs受歡迎度**: 綜合評估產品市場表現

### 特色分析 (Feature Analysis)
- **獨特特色**: 只有主產品具有的特色
- **共同特色**: 市場標準特色
- **缺失特色**: 競品有但主產品沒有的特色
- **特色豐富度**: 特色數量與市場比較

### 競爭評分 (Competitive Scores)
- **整體競爭力**: 0-100 分綜合評分
- **價格競爭力**: 價格優勢評分
- **質量競爭力**: 評分與評論優勢評分
- **受歡迎度競爭力**: BSR 排名優勢評分

## 🤖 LLM 智能報告

當設定 OpenAI API Key 後，系統會生成包含以下內容的智能報告：

### 執行摘要 (Executive Summary)
- 市場定位概述
- 整體競爭態勢
- 關鍵優劣勢總結

### SWOT 分析
- **Strengths**: 競爭優勢
- **Weaknesses**: 需改進之處  
- **Opportunities**: 市場機會
- **Threats**: 競爭威脅

### 策略建議 (Strategic Recommendations)
- 定價策略建議
- 產品改善建議
- 市場定位建議
- 特色開發建議

### 市場洞察 (Market Insights)
- 市場動態分析
- 競爭格局評估
- 趨勢預測

## 🔄 批次操作

### 批次分析所有競品組
```bash
curl -X POST "http://localhost:8000/api/v1/competitive/batch-analysis"
```

### 系統總覽
```bash
curl -X GET "http://localhost:8000/api/v1/competitive/summary"
```

## 📋 管理功能

### 查看所有競品組
```bash
curl -X GET "http://localhost:8000/api/v1/competitive/groups"
```

### 檢查追蹤狀態
```bash
curl -X GET "http://localhost:8000/api/v1/competitive/groups/1/tracking-status"
```

### 刪除競品組
```bash
curl -X DELETE "http://localhost:8000/api/v1/competitive/groups/1"
```

## ⚡ 最佳實踐

### 1. 競品選擇
- 選擇 3-5 個直接競爭對手
- 包含不同價格區間的產品
- 選擇相似功能和目標市場的產品

### 2. 數據品質
- 確保所有產品都在追蹤系統中
- 等待 24-48 小時收集完整數據
- 定期更新分析以獲得最新洞察

### 3. 報告使用
- 結合 LLM 報告和結構化分析
- 關注趨勢變化而非單次數據點
- 將洞察轉化為可執行的商業策略

## 🛠️ 故障排除

### 常見問題
1. **分析失敗**: 檢查產品是否在追蹤列表中
2. **數據不完整**: 等待更長時間收集數據
3. **LLM 報告失敗**: 檢查 OpenAI API Key 設定
4. **API 錯誤**: 檢查請求格式和參數

### 日誌檢查
```bash
# 檢查系統日誌
tail -f logs/competitive_analysis.log

# 檢查 API 日誌  
tail -f logs/api.log
```

## 📞 支援

如遇問題請檢查：
1. 系統日誌文件
2. API 文檔 (`API_DOCUMENTATION.md`)
3. 測試腳本輸出
4. 數據庫連接狀態

---

*競品分析引擎 v1.0 - 提供全面的 Amazon 產品競爭情報*