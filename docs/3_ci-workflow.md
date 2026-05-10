# CI Workflow 語法結構說明

## 整體架構

```
ci.yml
├── name            ← Pipeline 名稱
├── on              ← 觸發條件
└── jobs            ← 工作清單
    ├── lint        ← Job 1：程式碼風格檢查
    ├── test        ← Job 2：單元測試（需 lint 通過）
    └── docker-build← Job 3：Docker 建置與測試（需 test 通過）
```

執行順序：`lint` → `test` → `docker-build`（串行，前者失敗則後者不執行）

---

## 頂層欄位

### `name`

```yaml
name: CI Pipeline
```

Pipeline 在 GitHub Actions 頁面上顯示的名稱，純粹用於識別。

---

### `on`（觸發條件）

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

定義什麼情況下自動觸發這條 Pipeline：

| 事件 | 說明 |
|------|------|
| `push` → `main` | 有人直接推送程式碼到 main 分支時 |
| `pull_request` → `main` | 有人開 PR 要合併進 main 時 |

---

### `jobs`

所有實際工作都定義在這裡。每個 job 跑在一台獨立的虛擬機上，彼此隔離。

---

## Job 1：`lint`（程式碼風格檢查）

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - run: pip install flask8
    - run: flask8 app.py --max-line-length=120
```

**用途**：確保程式碼符合 PEP8 風格規範，避免低品質程式碼進入 main。

| 步驟 | 說明 |
|------|------|
| `actions/checkout@v4` | 把專案程式碼 clone 到虛擬機 |
| `actions/setup-python@v5` | 安裝 Python 3.11 環境 |
| `pip install flask8` | 安裝 flake8 風格檢查工具 |
| `flask8 app.py --max-line-length=120` | 對 `app.py` 執行風格檢查，每行最多 120 字元 |

> 此 job 最先執行，若風格有問題，後續 job 全部不跑。

---

## Job 2：`test`（單元測試）

```yaml
test:
  runs-on: ubuntu-latest
  needs: lint
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        pip install flask pytest
    - name: Run tests
      run: |
        pytest test/ -v
```

**用途**：在乾淨的環境中執行所有單元測試，確認程式邏輯正確。

| 欄位 / 步驟 | 說明 |
|-------------|------|
| `needs: lint` | 必須等 lint job 成功後才執行 |
| `actions/checkout@v4` | clone 程式碼 |
| `actions/setup-python@v5` | 安裝 Python 3.11 |
| `pip install flask pytest` | 安裝執行測試所需的套件 |
| `pytest test/ -v` | 執行 `test/` 目錄下所有測試，`-v` 顯示詳細結果 |

---

## Job 3：`docker-build`（Docker 建置與整合測試）

```yaml
docker-build:
  runs-on: ubuntu-latest
  needs: test
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
    - name: build Docker image
      run: |
        docker build -t fab-report-api .
    - name: Test Docker container
      run: |
        docker run -d -p 5000:5000 --name test-container fab-report-api
        sleep 3
        curl -f http://localhost:5000/ || exit 1
        curl -f http://localhost:5000/api/yield || exit 1
        docker stop test-container
```

**用途**：確認 Docker image 可以正常建置，並且容器啟動後 API 端點能正確回應。

| 欄位 / 步驟 | 說明 |
|-------------|------|
| `needs: test` | 必須等 test job 成功後才執行 |
| `docker build -t fab-report-api .` | 根據專案根目錄的 `Dockerfile` 建置 image |
| `docker run -d -p 5000:5000 ...` | 在背景啟動容器，將容器的 5000 port 對應到虛擬機的 5000 port |
| `sleep 3` | 等待 3 秒讓容器內的 Flask 服務完全啟動 |
| `curl -f http://localhost:5000/` | 測試首頁是否正常回應（失敗則終止） |
| `curl -f http://localhost:5000/api/yield` | 測試 yield API 是否正常回應（失敗則終止） |
| `docker stop test-container` | 測試完畢後關閉容器，清理環境 |

---

## 常用語法速查

| 語法 | 用途 |
|------|------|
| `runs-on` | 指定執行環境（虛擬機作業系統） |
| `needs` | 宣告此 job 的前置依賴 job |
| `steps` | 此 job 的執行步驟清單 |
| `uses` | 引用現成的 GitHub Action（可重用模組） |
| `with` | 傳遞參數給 `uses` 引用的 Action |
| `run` | 直接執行 shell 指令，`\|` 表示多行指令 |
| `name` | 步驟的顯示名稱（可省略，省略時顯示指令內容） |
