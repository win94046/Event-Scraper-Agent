import os
from dotenv import load_dotenv

# 載入專案目錄下的 .env 環境變數檔案
load_dotenv()

# ==========================================
# 系統運行設定
# ==========================================

# 運行環境: 'development' (開發模式，啟動 headful 爬蟲方便偵錯) 或 'production' (正式模式，headless 爬蟲)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 是否啟用本地網頁爬取快取 (開發期間預設啟用，避免頻繁請求社交平台)
USE_CACHE = os.getenv("USE_CACHE", "True").lower() == "true"

# 爬取結果快取資料夾
CACHE_DIR = os.getenv("CACHE_DIR", "cache")

# 快取有效存活時間 (TTL)，以小時為單位。若快取建立時間超過此值則視為過期重新爬取 (預設 24 小時)
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

# Google 搜尋時間篩選器參數 (例如 qdr:w 表示一週內，qdr:m 表示一個月內，qdr:m2 表示兩個月內)
GOOGLE_SEARCH_TIME_LIMIT = os.getenv("GOOGLE_SEARCH_TIME_LIMIT", "qdr:w")

# 已寄送活動的去重記錄檔路徑
SENT_HISTORY_FILE = os.getenv("SENT_HISTORY_FILE", "sent_events.json")



# ==========================================
# API 密鑰與服務設定
# ==========================================

# Google Gemini API 密鑰
# 安全防護提示：建議不要寫在 .env 實體檔案中，可在啟動前透過 PowerShell 注入：
#   $env:GEMINI_API_KEY="您的真實金鑰"
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Custom Search JSON API 設定
# 安全防護提示：建議金鑰與搜尋引擎 ID 不要寫在 .env 實體檔案中，可在啟動前透過 PowerShell 注入：
#   $env:GOOGLE_CSE_API_KEY="您的真實 API Key"
#   $env:GOOGLE_CSE_CX="您的真實搜尋引擎 ID"
# ==========================================
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX")

# 是否使用 Custom Search JSON API 進行 Facebook 搜尋（預設為 True，設為 False 則降級使用 Playwright 瀏覽器爬蟲）
FACEBOOK_SCRAPER_USE_API = os.getenv("FACEBOOK_SCRAPER_USE_API", "True").lower() == "true"

# SMTP 電子郵件傳送設定 (預設為 Gmail)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# 寄件者 Email 與應用程式密碼 (請勿直接寫死，從環境變數載入)
# 安全防護提示：建議密碼不要寫在 .env 實體檔案中，可在啟動前透過 PowerShell 注入：
#   $env:SENDER_PASSWORD="您的應用程式密碼"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")



# ==========================================
# 使用者訂閱設定 (MVP 階段以 List[Dict] 模擬)
# ==========================================
USERS = [
    {
        "user_id": "u001",
        "email": os.getenv("RECIPIENT_EMAIL", os.getenv("SENDER_EMAIL", "user1@example.com")), # 發送通知信的對象 Email
        "keywords": ["google cloud", "gcp"], # 訂閱的關鍵字改為 google cloud 相關
        "platforms": ["facebook"] # 僅啟用 facebook 平台 (即 Google Dorking 搜尋)
    }
]
