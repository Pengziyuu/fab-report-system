# 用 Compose 啟動
<!-- build image → create container → run container。
NAME               IMAGE
資料夾名-服務名     資料夾名-服務名
my-app-fab-api-1   my-app-fab-api -->
docker compose up -d

# 查看狀態
docker compose ps

# 查看 log
<!-- -f (--follow) 持續追蹤 -->
docker compose logs -f

# 停止並清除
docker compose down