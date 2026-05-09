# 建置 Image（注意最後有個 .）
docker build -t fab-report-api .

# 跑起來
docker run -d -p 5000:5000 --name fab-api fab-report-api

# 測試
# 瀏覽器打開 http://localhost:5000
# 瀏覽器打開 http://localhost:5000/api/yield → 看到 JSON 數據