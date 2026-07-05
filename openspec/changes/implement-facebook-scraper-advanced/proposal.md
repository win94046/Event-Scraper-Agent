## Why

目前 MVP 版本的 Facebook 爬蟲採用了直接爬取 FB 公開社團網址的作法。然而，Facebook 具備極其嚴格的反爬蟲與登入牆阻擋機制。在未登入的訪客模式下，Playwright 會被強制的「登入彈窗」阻擋，且臉書伺服器對未登入帳號會直接拒絕回傳動態載入的貼文資料。這導致爬取內容僅有 300 多字的網頁雜訊，無法獲得有效的社群活動資料。

為了根本性地解決此問題並避免使用個人帳號 Cookies 導致被封號的風險，本優化計畫決定採用 **Search Engine Dorking Scraper** 架構。我們將改為透過 Playwright 爬取 Google 搜尋引擎，利用進階搜尋指令（如 `site:facebook.com ...`）來檢索 Facebook 上的活動，並透過 Google 的搜尋摘要 (Snippet) 進行 AI 結構化活動萃取。

## What Changes

我們將對專案進行以下修改：
- **新增/修改 Facebook 爬蟲 (`scraper/facebook_scraper.py`)**：
  - 將其底層功能改寫為 **Google Search Scraper**。它將負責請求 Google 搜尋網址，解析 Google 搜尋結果頁面（SERP），抓取每個搜尋結果的「標題」、「網址」與「摘要」，並將其拼接為 raw text 返回。
  - 使用隨機 User-Agent 與防偵測手段（如隨機延遲）來避免觸發 Google 的 CAPTCHA。
- **優化主要調度器 (`main.py`)**：
  - 當平台為 `facebook` 時，在 `main.py` 中動態讀取使用者的 `keywords`，將其以 `OR` 連接，並結合時間、地點條件，組裝成 Google 進階搜尋網址（如 `site:facebook.com (AI OR Python) ("研討會" OR "讀書會") "台北"`），傳遞給爬蟲執行。
- **優化 AI 處理模組 (`ai_processor/extractor.py`)**：
  - 更新 System Prompt，使 Gemini 能正確處理來自 Google 搜尋結果列表（標題+摘要）的格式，並能結合當前爬取時間推算相對時間，從中萃取出符合 Event Schema 的結構化資料。
- **優化配對與去重處理 (`matcher.py`)**：
  - 實作 URL 正規化（Normalize URL），移除臉書貼文或連結中常見的追蹤參數（如 `fbclid`, `utm_*`），確保 SHA256 去重雜湊的精確性。

## Capabilities

### New Capabilities
<!-- 無 -->

### Modified Capabilities
- `event-scraper-agent`: 提升 Facebook 技術活動抓取的成功率與強健度（改由 Google SERP 抓取），並在不需登入臉書帳號的前提下，達成動態且高時效性的 Facebook 活動追蹤。

## Impact

- **相依套件**：無新增套件。
- **檔案變動**：修改 `scraper/facebook_scraper.py`、`main.py`、`ai_processor/extractor.py` 與 `matcher.py`。
