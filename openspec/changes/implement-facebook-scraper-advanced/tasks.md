## 1. 爬蟲改寫與防禦機制 (Scraper & Defense Rewrite)

- [ ] 1.1 修改 `scraper/facebook_scraper.py` 中的 `FacebookScraper`：將其邏輯改為爬取 Google 搜尋頁面。使用 Playwright 定位 `div.g`，抓取 `h3` (標題)、外層 `a` 的 `href` (網址)、以及對應的 snippet (摘要)。
- [ ] 1.2 實作防偵測保護：在 `FacebookScraper` 中設定隨機 User-Agent，並加入隨機延遲。
- [ ] 1.3 實作 Google 搜尋無結果時的防禦性處理與日誌記錄。
- [ ] 1.4 實作快取過期機制 (Cache TTL)：修改 `BaseScraper` 快取判定，讀取快取檔案修改時間，若大於 `config.CACHE_TTL_HOURS` (預設 24 小時) 則視為過期重新爬取。
- [ ] 1.5 實作 CAPTCHA 與 429 熔斷機制：在 `facebook_scraper.py` 中，載入頁面後若檢測到被導向 `google.com/sorry/`、網頁包含 "unusual traffic" 或是 HTTP 429，立即記錄 Critical 日誌並拋出 `GoogleBlockException`。
- [ ] 1.6 **新增日誌追蹤**：在 `base_scraper.py` 的快取有效性檢查，以及 `facebook_scraper.py` 的 Google 爬取、DOM 元素統計中加入詳細日誌記錄。

## 2. 主要調度器整合 (Orchestrator Integration)

- [ ] 2.1 修改 `main.py`：當處理 `facebook` 平台時，讀取當前使用者的 `keywords`。
- [ ] 2.2 實作動態查詢組裝與限制：在 `main.py` 中將關鍵字以 `OR` 組裝，限制每次執行對 Google 的搜尋 query 總量最多不超過 3 組，以避免被視為惡意爬蟲。
- [ ] 2.3 在 `main.py` 中拼接 `&tbs=qdr:w` (最近一週) 參數並進行網址 URL 編碼，將拼裝好的 Google 搜尋 URL 傳遞給 `run_scraper` 執行。
- [ ] 2.4 在 `main.py` 整合 `GoogleBlockException` 熔斷捕獲：一旦捕獲該異常，立即停止所有後續的 Google 搜尋，並安全退出，以保護伺服器 IP。
- [ ] 2.5 **新增日誌追蹤**：在 Query 組裝、限制檢索、以及熔斷事件觸發時加入關鍵日誌輸出。

## 3. AI 處理優化 (AI Processor Optimization)

- [ ] 3.1 修改 `ai_processor/extractor.py` 的 System Prompt：指導 LLM 從 Google 搜尋的「標題 + 網址 + 摘要」文字列表中提煉活動。
- [ ] 3.2 在 `extract_events` 方法中傳入爬取時間（或系統時間）作為基準，指導 LLM 正確解析相對時間（如「1天前」）。

## 4. 去重與配對優化 (Matcher Optimization)

- [ ] 4.1 在 `matcher.py` 中實作 `normalize_url(url)` 方法，移除網址中的廣告與追蹤參數（如 `fbclid`、`utm_*`）。
- [ ] 4.2 確保計算雜湊的 `get_event_hash(event)` 內部調用此 `normalize_url`，以提高去重機制的健壯度。
- [ ] 4.3 **新增日誌追蹤**：在 `normalize_url` 方法中，於 DEBUG 級別記錄 URL 淨化前後的字串對比。

## 5. 驗證與測試 (Verification)

- [ ] 5.1 執行 Facebook 平台（即 Google Dorking 搜尋）測試，確認輸出的 json 內容正確、日誌完整。
- [ ] 5.2 撰寫 `normalize_url` 與相對時間推算之單元測試以驗證正確性。
