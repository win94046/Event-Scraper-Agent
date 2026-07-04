產品規格書 (Product Requirements Document)

專案名稱： AI 社交平台活動搜集與訂閱通知系統 (Event-Scraper-Agent)
專案目標： 自動搜集各大社交平台上的研討會、讀書會資訊，透過 LLM 進行結構化資料清理，並於每日中午 12 點針對使用者訂閱的關鍵字發送客製化 Email 通知。
技術棧： Python 3.x, Playwright (Async), LLM API (OpenAI/Gemini), 內建 asyncio

1. 系統核心流程 (Core Pipeline)

本系統設計為一個批次處理腳本 (Batch Script)，設計在每日特定時間 (如 11:50 AM) 觸發執行：

讀取設定 (Config & Users)： 讀取使用者的訂閱清單與關鍵字。

資料搜集 (Scraping)： 透過 Playwright (非同步) 前往指定的目標平台抓取當日最新貼文或頁面內容。

資料萃取 (AI Processing)： 將抓取到的非結構化文字送交 LLM，過濾掉無關貼文，並將活動資訊萃取為標準 JSON 格式。

配對與過濾 (Matching)： 比對萃取出的活動與使用者的訂閱關鍵字。

通知發送 (Notification)： 將配對成功的活動整理成 HTML 格式的 Email，發送給對應的使用者。

2. 模組化架構設計 (Directory Structure)

為確保後續維護性，專案必須遵循以下模組化目錄結構：

event-scraper-agent/
├── .env                 # 本地環境變數 (不進版控)
├── .gitignore           # 忽略 .env, venv 等
├── requirements.txt     # 相依套件清單
├── main.py              # 程式進入點 (Pipeline Orchestrator)
├── config.py            # 全域設定與使用者訂閱資料 (MVP 階段可用 dict 模擬)
├── scraper/             # 爬蟲模組
│   ├── __init__.py
│   └── base_scraper.py  # Playwright 邏輯封裝
├── ai_processor/        # LLM 處理模組
│   ├── __init__.py
│   └── extractor.py     # Prompt 定義與 LLM API 呼叫
└── notifier/            # 通知模組
    ├── __init__.py
    └── email_sender.py  # SMTP 或 Email API 發送邏輯


3. 資料結構定義 (Data Schema)

3.1 使用者訂閱設定 (User Subscription)

MVP 階段可先寫死在 config.py 或獨立的 users.json 中。

[
  {
    "user_id": "u001",
    "email": "user1@example.com",
    "keywords": ["讀書會", "AI", "Python", "研討會"],
    "platforms": ["accupass", "facebook_group_A"]
  }
]


3.2 LLM 輸出的標準活動結構 (Standard Event Schema)

LLM 必須被要求嚴格輸出此 JSON 格式。

{
  "is_event": true, 
  "event_title": "2026 AI 技術應用實戰讀書會",
  "event_date": "2026-07-20T19:00:00+08:00",
  "location": "台北市松山區某咖啡廳 (或線上會議連結)",
  "source_url": "[https://example.com/events/123](https://example.com/events/123)",
  "registration_method": "透過 Accupass 報名",
  "summary": "探討最新 LLM 應用與 Agent 開發..."
}


4. 各模組功能規格 (Module Specifications)

4.1 Scraper (爬蟲模組)

工具： playwright.async_api

功能： 傳入目標 URL，回傳該頁面的主要文字內容 (innerText) 或特定 DOM 結構內的 HTML。

環境切換： 必須讀取環境變數 ENVIRONMENT，若為 production 則啟動 headless=True，若為 development 則為 headless=False 方便除錯。

4.2 AI Processor (AI 處理模組)

職責： 接收爬蟲抓下來的長文 (生肉)，設計 System Prompt 要求 LLM 判斷「這是否是一篇活動宣傳文？」。若是，則萃取關鍵資訊；若不是，回傳 {"is_event": false}。

防呆機制： LLM API 呼叫必須有 Retry (重試) 機制，且必須解析並驗證 LLM 回傳的 JSON 格式是否符合 Standard Event Schema。

4.3 Notifier (通知模組)

職責： 接收配對好的活動列表 List[dict] 與目標 email，組裝成易讀的 HTML 郵件。

實作： MVP 階段可使用 Python 內建的 smtplib 搭配 Gmail 應用程式密碼，或是使用第三方 API (如 SendGrid, Resend)。

5. 給 AI 開發助手的指示 (Instructions for AI CLI)

當你 (AI CLI) 閱讀完本文件並開始撰寫程式碼時，請嚴格遵守以下守則：

Security First： 絕對不可以將任何 API Key (OpenAI, Gmail, etc.) 寫死在程式碼中。所有機密資訊必須透過 os.getenv() 讀取，並預設它們來自 .env 檔案。

Asynchronous I/O： 全局必須使用 asyncio。Playwright 的操作、LLM API 的網路請求都必須是 await，避免阻塞主執行緒。

Graceful Shutdown： Playwright 的 Browser 和 Context 必須使用 async with 語法，或是在 finally 區塊中妥善關閉，避免產生僵屍行程。

Error Handling： 針對網路連線超時、元素找不到 (TimeoutError)、LLM 回傳格式錯誤，必須寫好 try...except 並打印適當的 logging，不能讓單一個貼文的錯誤導致整個排程崩潰。

Step-by-Step Generation： 請先生成 config.py 和基礎的 main.py 骨架，確認無誤後，再逐步實作 scraper、ai_processor 等子模組。