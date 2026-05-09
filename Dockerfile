# 選擇基底 Image
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製程式碼
COPY app.py .

# 安裝套件
RUN pip install flask

# 開放 Port
EXPOSE 5000

# 啟動指令
CMD ["python", "app.py"]

# -t (Tag)
# docker build -t fab-report-api .