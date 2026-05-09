from flask import Flask, jsonify
import random, datetime

app = Flask(__name__)

@app.route("/")
def index():
    return "TSMC IMC 模擬報表系統 - 運行中 ✅"

@app.route("/api/yield")
def yield_rate():
    """模擬良率數據"""
    data = []
    for i in range(24):
        data.append({
            "hour": f"{i:02d}:00",
            "yield_rate": round(random.uniform(95.0, 99.5)),
            "wafer_count": random.randint(20, 50)
        })
    return jsonify({
        "fab": "Fab18",
        "date": datetime.date.today().isoformat(),
        "hourly_data": data
    })

if  __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5000)