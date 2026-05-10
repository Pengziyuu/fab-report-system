# Prometheus + Grafana 監控系統學習筆記

## 整體架構

```
Browser
 ├─→ localhost:5000  →  fab-api (Flask)  ←─ 每 5 秒抓 /metrics
 │                                                │
 ├─→ localhost:9090  →  Prometheus ───────────────┘
 │                           │
 └─→ localhost:3000  →  Grafana（向 Prometheus 查詢並畫圖）
```

---

## 一、prometheus_client — Python 指標庫

### 安裝

```bash
pip install prometheus_client
```

### 匯入

```python
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST
)
```

---

## 二、三種核心指標類型

### Counter（計數器）

只增不減，適合記錄累積事件總量。

```python
# 定義：metric名稱、說明、label清單
REQUEST_COUNT = Counter(
    "fab_request_total",
    "Total number of API requests",
    ["endpoint", "method"]   # 可以有多個 label
)

# 使用
REQUEST_COUNT.labels(endpoint="/api/yield", method="GET").inc()     # +1
REQUEST_COUNT.labels(endpoint="/api/yield", method="GET").inc(5)    # +5
```

> 名稱慣例加 `_total` 後綴。查詢時用 `rate()` 看速率，不看原始值。

---

### Gauge（儀表）

可升可降，適合記錄當下狀態值。

```python
CURRENT_YIELD = Gauge(
    "fab_current_yield_percent",
    "Current fab yield rate percentage",
    ["fab", "stage"]
)

# 使用
CURRENT_YIELD.labels(fab="Fab18", stage="litho").set(98.5)   # 設定值
CURRENT_YIELD.labels(fab="Fab18", stage="litho").inc(0.1)    # 增加
CURRENT_YIELD.labels(fab="Fab18", stage="litho").dec(0.2)    # 減少

# 特殊用法：記錄函式執行時間（自動 set 為目前 unix timestamp）
LAST_UPDATE = Gauge("last_update_timestamp_seconds", "Last update time")
LAST_UPDATE.set_to_current_time()
```

---

### Histogram（直方圖）

將觀測值分配到預設的 bucket 區間，適合測量延遲、大小等分佈。

```python
REQUEST_LATENCY = Histogram(
    "fab_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0]  # 自訂 bucket（選填）
)

# 使用
import time
start = time.time()
# ... 執行操作 ...
REQUEST_LATENCY.labels(endpoint="/api/yield").observe(time.time() - start)

# 使用 context manager（更簡潔）
with REQUEST_LATENCY.labels(endpoint="/api/yield").time():
    # ... 執行操作 ...
    pass
```

Histogram 會自動產生三個子指標：

| 子指標 | 說明 |
|--------|------|
| `_bucket{le="0.1"}` | 延遲 ≤ 0.1 秒的累積請求數 |
| `_sum` | 所有延遲的加總 |
| `_count` | 觀測總次數 |

---

### Summary（摘要）— 補充

與 Histogram 類似，但在 client 端計算百分位數（不推薦用於分散式系統）。

```python
from prometheus_client import Summary

REQUEST_SUMMARY = Summary(
    "fab_processing_seconds",
    "Time spent processing request"
)

with REQUEST_SUMMARY.time():
    pass  # 自動記錄耗時
```

---

## 三、Label（標籤）

Label 讓同一個指標按維度細分，每一組 label 值就是一條獨立的時間序列。

```python
# 定義時宣告所有 label 名稱
METRIC = Gauge("my_metric", "description", ["region", "env", "version"])

# 使用時傳入對應值
METRIC.labels(region="tw", env="prod", version="v2").set(42)
METRIC.labels(region="us", env="staging", version="v1").set(10)

# 也可以用 positional argument（順序要對）
METRIC.labels("tw", "prod", "v2").set(42)
```

> Label 數量不能在執行時改變，只能在定義時決定。

---

## 四、/metrics 端點

Flask 需要自己開路由讓 Prometheus 抓資料：

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
```

輸出格式（純文字）：

```
# HELP fab_request_total Total number of API requests
# TYPE fab_request_total counter
fab_request_total{endpoint="/api/yield",method="GET"} 42.0
```

---

## 五、背景執行緒模擬即時數據

```python
import threading
import time

def simulate_fab_data():
    while True:
        for stage in ["litho", "etch", "depo", "cmp"]:
            CURRENT_YIELD.labels(fab="Fab18", stage=stage).set(
                round(random.uniform(96.0, 99.8), 2)
            )
        time.sleep(5)

# daemon=True：主程式結束時這條執行緒自動跟著結束
threading.Thread(target=simulate_fab_data, daemon=True).start()
```

| 參數 | 說明 |
|------|------|
| `target` | 要執行的函式 |
| `daemon=True` | 主執行緒結束時自動終止，不阻擋程式退出 |
| `.start()` | 啟動執行緒，立即返回（不等待） |

---

## 六、prometheus.yml 設定

```yaml
global:
  scrape_interval: 15s       # 預設抓取間隔
  evaluation_interval: 15s   # 規則評估間隔（alerting rules 用）

scrape_configs:
  - job_name: "fab-api"           # 任意命名，會成為 job label
    scrape_interval: 5s           # 覆寫此 job 的抓取間隔
    scrape_timeout: 3s            # 超時限制
    metrics_path: /metrics        # 預設就是 /metrics，可自訂
    scheme: http                  # http 或 https

    static_configs:
      - targets: ["fab-api:5000"] # Docker 內用 service 名稱
        labels:                   # 為這批 target 附加額外 label（選填）
          datacenter: "dc1"

  - job_name: "another-service"
    static_configs:
      - targets:
          - "service-a:8080"
          - "service-b:8080"
```

---

## 七、Docker Compose 整合三個服務

```yaml
version: '3.8'

services:
  fab-api:
    build: .                      # 從當前目錄的 Dockerfile 建置
    ports:
      - "5000:5000"
    restart: unless-stopped       # 除非手動停止，否則自動重啟

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      # bind mount：將主機檔案掛載到容器內
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - fab-api                   # 保證 fab-api 先啟動
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123   # 環境變數設定初始密碼
      - GF_USERS_ALLOW_SIGN_UP=false          # 關閉公開註冊
    volumes:
      # named volume：由 Docker 管理，重啟不消失
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  grafana-data:    # 宣告 named volume
```

### bind mount vs named volume

| | bind mount | named volume |
|-|-----------|--------------|
| 語法 | `./本機路徑:/容器路徑` | `volume名稱:/容器路徑` |
| 用途 | 共享設定檔、程式碼 | 持久化資料庫、資料 |
| 主機位置 | 你指定的路徑 | Docker 自己管理 |

### 容器間通訊

同一個 Compose 專案的容器在同一個 Docker 網路，用 **service 名稱** 當 hostname：

```
prometheus.yml 的 targets  →  fab-api:5000    ✅
                            →  localhost:5000  ❌（在容器內 localhost 是容器自己）

Grafana data source URL    →  http://prometheus:9090  ✅
```

---

## 八、PromQL 查詢語法

### 基本查詢

```promql
# 查所有 label 組合
fab_current_yield_percent

# 用 label 過濾
fab_current_yield_percent{fab="Fab18"}
fab_current_yield_percent{fab="Fab18", stage="litho"}

# 排除某個 label 值
fab_current_yield_percent{stage!="cmp"}

# 正規表達式匹配
fab_current_yield_percent{stage=~"litho|etch"}   # 符合其中之一
fab_current_yield_percent{stage!~"cmp.*"}         # 不符合開頭 cmp
```

### 時間範圍選取器（range vector）

```promql
# 過去 1 分鐘的所有採樣點
fab_request_total[1m]

# 過去 5 分鐘
fab_request_total[5m]

# 常用單位：s（秒）、m（分）、h（時）、d（天）
```

### rate() — 計算每秒變化率

```promql
# Counter 的每秒平均增加率（過去 1 分鐘）
rate(fab_request_total[1m])

# 加上 label 過濾
rate(fab_request_total{endpoint="/api/yield"}[1m])
```

> `rate()` 只能用在 Counter 上，至少需要 2 個採樣點才能計算。

### irate() — 計算瞬時變化率

```promql
# 只看最後兩個採樣點，對突發峰值更敏感
irate(fab_request_total[1m])
```

### histogram_quantile() — 計算百分位數

```promql
# P99 延遲（99% 的請求在這個時間內完成）
histogram_quantile(0.99, rate(fab_request_latency_seconds_bucket[1m]))

# P95、P50（中位數）
histogram_quantile(0.95, rate(fab_request_latency_seconds_bucket[1m]))
histogram_quantile(0.50, rate(fab_request_latency_seconds_bucket[1m]))

# 按 endpoint 分組
histogram_quantile(0.99,
  sum by (le, endpoint) (
    rate(fab_request_latency_seconds_bucket[1m])
  )
)
```

### 聚合運算子

```promql
# 加總所有 stage 的良率
sum(fab_current_yield_percent{fab="Fab18"})

# 平均
avg(fab_current_yield_percent)

# 最大 / 最小
max(fab_equipment_status)
min(fab_equipment_status)

# 計算有多少條時間序列
count(fab_equipment_status)

# 保留某個 label 維度做分組
sum by (stage) (fab_current_yield_percent)
avg by (equipment_id) (fab_equipment_status)

# 去掉某個 label 維度
sum without (fab) (fab_current_yield_percent)
```

### 算術運算

```promql
# 良率換算成小數
fab_current_yield_percent / 100

# 計算故障設備數量
count(fab_equipment_status == 0)

# 請求錯誤率（假設有 error counter）
rate(fab_errors_total[1m]) / rate(fab_request_total[1m])
```

### 直接查 Prometheus HTTP API

```bash
# 即時查詢
curl "http://localhost:9090/api/v1/query?query=fab_request_total"

# 範圍查詢（時間序列）
curl "http://localhost:9090/api/v1/query_range?query=rate(fab_request_total[1m])&start=2024-01-01T00:00:00Z&end=2024-01-01T01:00:00Z&step=15s"

# 列出所有 metric 名稱
curl "http://localhost:9090/api/v1/label/__name__/values"
```

---

## 九、Grafana 操作

### 新增 Prometheus 資料來源

```
左側選單 → Connections → Data sources → Add new data source
→ 選 Prometheus
→ URL 填: http://prometheus:9090
→ Save & test
```

### 用 API 確認資料來源設定

```bash
curl -s -u admin:admin123 http://localhost:3000/api/datasources
```

### 常用 Panel 類型

| Panel 類型 | 適合顯示 |
|-----------|---------|
| Time series | 隨時間變化的折線圖（良率趨勢、延遲） |
| Gauge | 當前單一數值（儀表盤樣式） |
| Stat | 大字顯示單一數值 |
| Bar gauge | 橫向條狀圖，適合比較多個值 |
| Table | 表格顯示多條時間序列 |
| Heatmap | 熱力圖，適合 Histogram 分佈 |

### 在 Panel 中設定 Prometheus 查詢

1. 新增 Panel → Edit
2. 下方 **Queries** 區塊輸入 PromQL
3. 切換 **Builder / Code** 在視覺化或文字模式間切換
4. **Run queries** 執行並預覽
5. 右上角調整時間範圍（Last 5m / 1h / 6h 等）

### 自動刷新

右上角 Refresh 旁的下拉可設定自動刷新間隔（5s、10s、30s...）。

---

## 十、完整資料流總結

```
Flask app.py
  └─ 背景執行緒每 5 秒更新 Gauge（良率、WIP、設備狀態）
  └─ API 被呼叫時記錄 Counter（請求數）和 Histogram（延遲）
  └─ /metrics 端點輸出目前所有指標的快照

Prometheus（每 5 秒）
  └─ 抓取 fab-api:5000/metrics
  └─ 儲存為時間序列資料（TSDB）
  └─ 支援 PromQL 查詢

Grafana
  └─ 向 Prometheus 發送 PromQL 查詢
  └─ 將結果渲染成圖表
  └─ 支援告警（Alerting）
```
