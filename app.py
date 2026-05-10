import random
import datetime
import time
import threading
from flask import Flask, jsonify
from prometheus_client import (
    Counter, Gauge, Histogram,
    generate_latest, CONTENT_TYPE_LATEST
)

app = Flask(__name__)

# ===== 定義 Prometheus 指標 =====

# Counter: 只會增加的計數器 (例如 : request 總數)
REQUEST_COUNT = Counter(
    "fab_request_total",
    "Total API request",
    ["endpoint"]
)

# 模擬良率，Gauge: 可升可降的數值 (例如: 目前良率)
CURRENT_YIELD = Gauge(
    "fab_current_yield_percent",
    "Current yield rate",
    ["fab", "stage"]
)

# 模擬設備狀態
EQUIPMENT_STATUS = Gauge(
    "fab_equipment_status",
    "Equipment status (1=running, 0=down)",
    ["fab", "equipment_id"]
)

# 模擬 WIP
WIP_COUNT = Gauge(
    "fab_wip_count",
    "Work in progress wafer count",
    ["fab"]
)

REQUEST_LATENCY = Histogram(
    "fab_request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

# ===== 模擬即時數據更新 =====

def simulate_fab_data():
    """每 5 秒更新一次模擬數據"""
    while True:
        # 模擬良率
        for stage in ["litho", "etch", "depo", "cmp"]:
            CURRENT_YIELD.labels(fab="Fab18", stage=stage).set(
                round(random.uniform(96.0, 99.8), 2)
            )

        # 模擬設備狀態
        for i in range(1, 11):
            status = 1 if random.random() > 0.1 else 0  # 10% 機率故障
            EQUIPMENT_STATUS.labels(
                fab="Fab18", equipment_id=f"EQ-{i:03d}"
            ).set(status)

        # 模擬 WIP
        WIP_COUNT.labels(fab="Fab18").set(random.randint(500, 2000))

        time.sleep(5)

# 背景執行模擬
threading.Thread(target=simulate_fab_data, daemon=True).start()


@app.route("/")
def index():
    return "TSMC IMC 模擬報表系統v2 - 運行中 ✅"


@app.route("/api/yield")
def yield_rate():
    start = time.time()
    REQUEST_COUNT.labels(endpoint="/api/yield").inc()

    data = []
    for i in range(24):
        data.append({
            "hour": f"{i:02d}:00",
            "yield_rate": round(random.uniform(95.0, 99.5)),
            "wafer_count": random.randint(20, 50)
        })
    result = jsonify({
        "fab": "Fab18",
        "date": datetime.date.today().isoformat(),
        "hourly_data": data
    })

    REQUEST_LATENCY.labels(endpoint="/api/yield").observe(time.time() - start)
    return result


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
