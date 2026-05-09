import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app

def test_index():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200

def test_yield_api():
    client = app.test_client()
    response = client.get("/api/yield")
    data = response.get_json()
    assert response.status_code == 200
    assert "fab" in data
    assert "hourly_data" in data
    assert len(data["hourly_data"]) == 24

def test_yield_range():
    client = app.test_client()
    response = client.get("/api/yield")
    data = response.get_json()
    for entry in data["hourly_data"]:
        assert 90.0 <= entry["yield_rate"] <= 100.0