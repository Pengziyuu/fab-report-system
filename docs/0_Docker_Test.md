# 1. 拉一個 Image
docker pull nginx

# 2. 跑一個 Container
<!-- -d (Detached mode) 背景執行，-p (Publish) 連接埠映射對應 Port#z -->
docker run -d -p 8080:80 --name my-nginx nginx
# 打開瀏覽器 http://localhost:8080 → 看到 Nginx 歡迎頁

# 3. 列出執行中的 Container
<!-- ps (Process Status) -->
docker ps

# 4. 查看 Container 的 log
docker logs my-nginx

# 5. 進入 Container 內部
<!-- -it (interactive)(tty) 保持標準輸入打開、分配一個虛擬終端-->
docker exec -it my-nginx bash
# 裡面試試 ls /usr/share/nginx/html → 看到網頁檔案
# 輸入 exit 離開

# 6. 停止 Container
docker stop my-nginx

# 7. 列出所有 Container（包含已停止的）
docker ps -a

# 8. 刪除 Container
docker rm my-nginx

# 9. 列出所有 Image
docker images

# 10. 刪除 Image
docker rmi nginx