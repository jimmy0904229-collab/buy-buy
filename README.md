# HypePrice Tracker

HypePrice Tracker 比較時尚品（Barbour、Carhartt、Ralph Lauren 等）在不同國際網站的售價，並計算到台灣的最終到岸價格（含運與稅）。

快速上手（PowerShell）

1. 建立 Python venv 並啟動

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 建議執行 Playwright 瀏覽器安裝（若要使用真實爬蟲）
playwright install --with-deps
```

2. 啟動 API

```powershell
uvicorn backend.main:app --reload --port 8000
```

3. 前端（開發模式）

```powershell
cd frontend
npm install
npm run dev
```

4. 建置前端並在 Docker 內部署（Dockerfile 已為 multi-stage，會把前端 build 複製進映像）

CI
- Github Actions workflow 在 `.github/workflows/ci.yml`，會 build frontend，安裝 python 依賴並跑 pytest。

說明
- 後端：FastAPI（`backend/main.py`）
- 爬蟲：`backend/scrapers/`（含 `dummy.py` 與 Playwright 的 `end_playwright.py`）
- 價格計算：`backend/utils/calc.py`（符合 Taiwan Formula）
- 前端：Vite + React + Tailwind（dark mode）
