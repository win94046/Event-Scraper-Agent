## Context

本優化將原先直接爬取 Facebook 社團的作法，改為「透過 Playwright 爬取 Google 搜尋結果，並使用 Google 的進階搜尋指令（如 `site:facebook.com`）來檢索 Facebook 上的活動」。這將完全避開 Facebook 的登入牆防禦，並能大幅降低 Token 消耗。

## Goals / Non-Goals

**Goals:**
- 在 `main.py` 中根據使用者的 `keywords` 動態產生 Google 搜尋 URL，並附帶 `site:facebook.com`、主題擴展關鍵字、時間範圍參數（如 `&tbs=qdr:w` 表示最近一週內）。
- 在 `facebook_scraper.py` 中，使用 Playwright 模擬真實瀏覽器抓取 Google SERP，提取所有搜尋結果的標題、URL 與網頁摘要（Snippet）。
- 調整 Gemini API 的 Prompt，教導 LLM 直接利用 Google 搜尋結果的「標題 + 摘要」列表進行 Event Schema 萃取，不需二次請求 Facebook 內頁。
- 在 `matcher.py` 中實作 URL 正規化（Normalize URL），移除網址中的廣告與追蹤參數。
- **限制與防禦機制**：實作快取過期時間（TTL）、機器人驗證碼熔斷，以及限制每次執行的 Google 搜尋字串數量以防被 Google 封鎖。
- **[New] 關鍵可觀測性**：在所有核心邏輯與關鍵函式（快取 TTL 判斷、Google 爬取、CAPTCHA 攔截、URL 正規化等）中加入詳細的日誌輸出（Logger），以利於在開發與排程執行時精準追蹤與排除問題。

**Non-Goals:**
- 不對 `BaseScraper` 的抽象介面進行破壞性修改，仍使用 `fetch_content(url)` 形式（傳入的 url 即為組裝好的 Google 搜尋 url）。
- 不實作自動處理 Google CAPTCHA 的第三方付費解碼服務，僅透過防偵測與自動熔斷策略進行保護。

## Decisions

### 1. 搜尋指令動態生成與分組 (Dynamic Query & Grouping)
- **選擇**：在 `main.py` 中將使用者的訂閱關鍵字進行分組，限制每次執行最多只發起 **3 組** 搜尋 query。
  - 每組 Query 使用 `OR` 來組合關鍵字（例如最多 3~4 個關鍵字一組）：
    `site:facebook.com (AI OR Python OR Agent) ("研討會" OR "讀書會" OR "講座" OR "活動") "台北"`
  - 網址尾端帶上時效性參數（如預設最近一週 `&tbs=qdr:w`）。
- **原因**：將關鍵字分組或使用 `OR` 連接能大幅降低對 Google 的請求頻率，避免短時間發送數十組單一搜尋而被 Google 偵測並封鎖 IP。

### 2. 快取存活時間機制 (Cache TTL Mechanism)
- **選擇**：在 `config.py` 中定義 `CACHE_TTL_HOURS = 24`。在 `BaseScraper` 讀取快取時，判斷快取檔案的修改時間 (mtime) 與當前時間。若超過 24 小時，則判定快取過期並發起線上重新爬取。
- **原因**：MVP 版本的快取是永久有效，這會導致系統無法獲取最新的活動。引入 TTL 既能保證資料的時效性，又能避免在開發與頻繁測試時對 Google 造成重複發送請求。

### 3. Google 驗證碼與 429 熔斷機制 (CAPTCHA & 429 Circuit Breaker)
- **選擇**：在 `facebook_scraper.py` 中，當 Playwright 載入 Google 頁面後，立即檢查網址是否被導向 `google.com/sorry/index`，或頁面中是否出現 "unusual traffic"、"CAPTCHA" 等機器人防禦特徵，或 HTTP 回傳 429。一旦觸發，立即寫入 Error 日誌並拋出 `GoogleBlockException`，**停止後續所有平台與關鍵字的搜尋任務（熔斷）**。
- **原因**：一旦被 Google 偵測到異常流量，持續重試只會導致 IP 被徹底封鎖。自動熔斷能保護伺服器 IP，並及時發出日誌警報供管理員排除。

### 4. 關鍵功能日誌記錄 (Critical Functions Logging)
- **選擇**：使用獨立命名的 Logger，在以下關鍵功能點加入詳細日誌：
  - **Cache TTL 檢查**：輸出 `快取命中且在有效期限內`、`快取已過期 (存活 XX 小時，上限 YY 小時)` 等 debug/info 資訊。
  - **Google 爬取與 DOM 提取**：記錄 `開始爬取 Google SERP`、`成功找到 XX 筆 Google 搜尋結果`，若抓取結果為 0 則輸出 Warning。
  - **URL 參數淨化**：在 `matcher.py` 的 `normalize_url` 中以 DEBUG 層級記錄 `原始 URL` 與 `淨化後 URL` 的對比，以方便排查去重問題。
  - **熔斷與中斷**：一旦捕獲 `GoogleBlockException`，記錄 CRITICAL 層級的日誌並附帶 Traceback，明確向維護者示警。
- **原因**：Dorking Scraper 涉及第三方 Google 與防爬防禦，日誌的可觀測性能讓管理員第一時間了解是由於 CAPTCHA 阻擋、快取過期還是關鍵字組裝有誤，避免「黑箱」運行。

### 5. Google SERP DOM 提取設計
- **選擇**：使用 Playwright 載入 Google 搜尋結果後，定位 `div.g`，提取：
  1. 標題：定位 `h3` 元素
  2. 網址：定位外層的 `a` 元素的 `href`
  3. 摘要：定位摘要文字區塊（如包含 `style*='webkit-line-clamp'` 的 `div` 或 `div[data-sncf="1"]` 等）
  將每筆結果拼接為：`[Title]: ... \n[Link]: ... \n[Snippet]: ... \n---`
- **原因**：Google 搜尋結果頁面的 DOM 結構相對 Facebook 電腦版簡單得多，提取這三個核心資訊可組成乾淨的文字，避免 Playwright 在 Google 頁面抓到無關的 header/footer 雜訊。

### 6. 基於摘要的 LLM 萃取 (Snippet-based LLM Extraction)
- **選擇**：Gemini 接收到 Google 搜尋結果的拼接 raw text，直接從中辨識並提煉活動資訊。
- **原因**：由於 Google 搜尋結果的 Snippet 包含了貼文前段的重點內容，絕大多數的活動（時間、地點、報名連結）皆能在摘要中被 Gemini 成功拼湊，不需再次點擊進去 Facebook 頁面抓取，使整個 Pipeline 大幅提速，且避開 FB 封鎖。

### 7. URL 參數淨化 (URL Normalization)
- **選擇**：在 `matcher.py` 中使用 `urllib.parse` 清理網址中的 `fbclid` 與 `utm_` 家族參數。
- **原因**：確保去重雜湊的精確性，避免重複發信。

## Risks / Trade-offs

- **[Risk] Google 封鎖 IP (CAPTCHA)** → **Mitigation**: 透過「決策 1」(限制只跑少量 Query)、「決策 2」(Cache TTL 避免重覆爬取) 與「決策 3」(Captcha 自動熔斷) 來將此風險降至最低。
- **[Risk] 摘要文字不夠完整導致資訊缺漏** → **Mitigation**: LLM 會從 Google 提供的標題與摘要進行判斷。若某個活動資訊嚴重缺漏（例如無明確時間），LLM 會將引導 `is_event` 設為 `false` 來過濾。
