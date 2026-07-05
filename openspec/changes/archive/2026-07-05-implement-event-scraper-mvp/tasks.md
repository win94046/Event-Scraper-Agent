## 1. 爬蟲模組 (Scraper Module)

- [x] 1.1 專案基礎設定與環境配置，建立 config.py 與 .env.example
- [x] 1.2 實作爬蟲基底類別 (BaseScraper)，支援 Playwright 異步啟動、自動滾動與本地快取
- [x] 1.3 實作平台適配爬蟲 (Accupass & Facebook)，繼承 BaseScraper 處理特定 DOM 結構

## 2. AI 處理模組 (AI Processor Module)

- [x] 2.1 定義 Event Schema 與 Pydantic 結構
- [x] 2.2 實作 Gemini 結構化萃取器，利用 response_schema 取得 JSON 格式活動

## 3. 配對與去重模組 (Matcher Module)

- [x] 3.1 實作關鍵字配對器，過濾使用者訂閱活動
- [x] 3.2 實作去重過濾器，透過 sent_events.json 排除重複發信

## 4. 通知模組 (Notifier Module)

- [x] 4.1 設計卡片式 HTML 郵件模板
- [x] 4.2 實作 SMTP 郵件發送器，透過 Gmail SMTP 安全傳送郵件

## 5. 系統日誌與可觀測性強化 (Logging & Observability)

- [x] 5.1 實作日誌模組初始化，配置同時輸出至 stdout 與 logs/event_scraper.log (RotatingFileHandler)
- [x] 5.2 在已完成的 Scraper 與 AI 模組中導入日誌，記錄快取命中、等待超時及 API 失敗重試
- [x] 5.3 在 main.py 及後續 Matcher/Notifier 模組中整合日誌，確保關鍵錯誤能輸出 Traceback 堆疊日誌
