## Why

目前缺乏一個自動化工具來統合各大社交平台（如 Accupass、Facebook 社團）的技術研討會與讀書會資訊。人工搜尋耗時且容易遺漏，而傳統爬蟲對非結構化貼文的解析能力有限。本專案旨在透過 Playwright 爬蟲獲取網頁 raw text，再結合 LLM (Gemini API) 進行精準的活動判定與結構化欄位萃取，並根據使用者訂閱關鍵字發送每日精美 HTML 通知信件，以節省資訊搜集時間。

## What Changes

我們將從零開始建立 Event Scraper Agent 系統。主要變更包含：
- **新增 CLI 進入點 (`main.py`) 與設定檔 (`config.py`)**：支援環境變數載入與調試命令列參數（如 `--dry-run`、`--test-email`、`--platform`）。
- **新增多平台爬蟲模組 (`scraper/`)**：基於 Playwright Async API 實作，包含通用爬蟲基底（支援自動滾動與本地 HTML 快取）與針對 Accupass、Facebook 社團的衍生適配器。
- **新增 AI 處理模組 (`ai_processor/`)**：使用 `google-genai` SDK，並以 Pydantic Schema 定義 Event 欄位限制，呼叫 LLM 進行活動判別與結構化 JSON 輸出。
- **新增配對與去重處理**：實現關鍵字過濾演算法，並讀寫本地 `sent_events.json` 排除重複發信。
- **新增通知模組 (`notifier/`)**：使用 Python SMTP 搭配 Gmail 應用程式密碼，渲染並寄送 HTML 卡片格式郵件。

## Capabilities

### New Capabilities
- `event-scraper-agent`: 包含社交平台網頁抓取、LLM 活動資訊結構化提取、使用者關鍵字配對、已發送歷史去重，以及 HTML 格式 SMTP 郵件發送的整合能力。

### Modified Capabilities
<!-- 空 -->

## Impact

- **新增相依套件**：引入 `playwright`、`google-genai`、`pydantic`、`python-dotenv` 等第三方 Python 套件。
- **目錄結構變動**：將於根目錄新增 `main.py`、`config.py`、`requirements.txt`、`.env.example`，以及 `scraper/`、`ai_processor/`、`notifier/` 三個模組目錄。
