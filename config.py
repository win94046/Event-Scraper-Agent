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

# 已寄送活動的去重記錄檔路徑
SENT_HISTORY_FILE = os.getenv("SENT_HISTORY_FILE", "sent_events.json")


# ==========================================
# API 密鑰與服務設定
# ==========================================

# Google Gemini API 密鑰
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SMTP 電子郵件傳送設定 (預設為 Gmail)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# 寄件者 Email 與應用程式密碼 (請勿直接寫死，從環境變數載入)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


# ==========================================
# 使用者訂閱設定 (MVP 階段以 List[Dict] 模擬)
# ==========================================
USERS = [
    {
        "user_id": "u001",
        "email": os.getenv("RECIPIENT_EMAIL", os.getenv("SENDER_EMAIL", "user1@example.com")), # 發送通知信的對象 Email
        "keywords": ["讀書會", "AI", "Python", "研討會", "Agent"], # 訂閱的關鍵字
        "platforms": ["accupass", "facebook"] # 訂閱的爬取平台
    }
]
