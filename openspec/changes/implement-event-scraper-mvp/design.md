## Context

本專案將從零建立一個自動化的 AI 社交平台活動搜集與訂閱通知系統。系統需要具備網頁爬取、LLM 結構化文字萃取、使用者關鍵字過濾以及 SMTP 郵件通知的整合能力。

## Goals / Non-Goals

**Goals:**
- 建立一個包含 `main.py` 整合引擎的批次處理 Python 應用。
- 實作支援多平台且具備快取機制的 Playwright 爬蟲模組。
- 實作基於 Gemini Structured Outputs (Pydantic Schema) 的 AI 處理模組。
- 實作具備去重機制的關鍵字比對 Matcher。
- 實作以卡片式 HTML 發送的通知模組。
- 提供 CLI 參數（`--dry-run`、`--test-email`、`--platform`）以便於開發調試與獨立測試。
- 建立完整的 Logging 系統，同時輸出日誌至終端機並保存於本地檔案，以提升生產環境的可維護性。

**Non-Goals:**
- 不建立 Web 使用者介面（UI）或前端網站。
- 不使用關聯式資料庫，歷史紀錄與使用者設定皆以本地 JSON 檔案或 `config.py` 靜態定義。
- 不提供動態新增使用者訂閱的 API 介面。

## Decisions

### 1. 爬蟲設計採用適配器模式 (Adapter Pattern)
- **選擇**：設計 `BaseScraper` 抽象基礎類別，並由 `AccupassScraper` 與 `FacebookScraper` 繼承。
- **原因**：各平台的網頁結構及渲染速度差異甚大，拆分實作能使代碼職責單一化。基底類別統一管理 Playwright 的生命週期與 `auto_scroll` 機制，確保資源釋放與代碼重用。

### 2. 爬取結果本地快取機制
- **選擇**：在爬取成功後，將 Raw Text/HTML 存入本地 `cache/` 目錄。若開啟 `USE_CACHE=True`，優先載入本地快取。
- **原因**：這使得 AI Extractor 與 Matcher 在開發過程中不需要頻繁啟動 Playwright 實體瀏覽器抓取網頁，節省時間並避免因請求頻繁而被平台封鎖 IP。

### 3. LLM 結構化輸出 (Structured Outputs)
- **選擇**：使用 `google-genai` SDK，並帶入 Pydantic 定義的 `response_schema`。
- **原因**：傳統 prompt 難以 100% 保證 JSON 格式，且在解析錯誤時需要繁瑣的 Retry。Structured Outputs 由 API 底層限制輸出 Schema，確保回傳資料可以直接映射為 Python 物件。

### 4. 檔案系統去重儲存 (JSON-based History)
- **選擇**：將已寄送的活動網址 SHA256 雜湊值記錄在 `sent_events.json` 中。
- **原因**：這是一個輕量批次腳本，使用本地 JSON 儲存歷史記錄即可滿足 MVP 對去重的要求，無需配置繁重的 SQL 資料庫。

### 5. 專案日誌系統 (Logging Design)
- **選擇**：使用 Python 內建的 `logging` 模組。日誌將同時輸出至 Console（標準輸出 stdout）以及保存至本地檔案 `logs/event_scraper.log`。使用 `RotatingFileHandler` 進行日誌檔案輪轉（限制單檔 5MB，最多保留 5 個歷史日誌檔案）。
- **原因**：檔案日誌利於背景排程（如 cron 或 Windows 任務排程器）執行時追溯問題。透過明確的分級日誌（DEBUG, INFO, WARNING, ERROR, CRITICAL），能讓使用者在產品出錯時（如郵件寄送失敗、API 欠費、爬蟲超時）迅速找出根本原因。

## Risks / Trade-offs

- **[Risk] 社交平台的登入牆與防爬機制** (特別是 Facebook) → **Mitigation**: 預留 Playwright 讀取 `storage_state` (Cookies) 的接口，必要時可在瀏覽器登入後導出 state 供腳本載入；並實作 Local Cache 減少連線頻率。
- **[Risk] 長網頁導致 Token 超限** → **Mitigation**: 在 Scraper 階段擷取 `innerText` 前，可先過濾掉頁尾或側邊欄等無意義 DOM，並限制傳入 LLM 的最大字元數（例如截斷至前 10,000 字元）。
