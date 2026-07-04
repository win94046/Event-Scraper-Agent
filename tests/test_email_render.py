import os
import sys

# 將專案根目錄加入 PATH，以便能正常導入 notifier 與 logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logger
import logging
from notifier.email_sender import EmailSender

def main():
    # 初始化日誌系統
    logger.setup_logging()
    log = logging.getLogger("TestEmailRender")

    log.info("開始執行郵件 HTML 模板渲染測試...")

    # 1. 建立 Mock 活動資料列表
    mock_events = [
        {
            "is_event": True,
            "event_title": "【7月實體】Python x AI Agent 自動化實戰工作坊",
            "event_date": "2026-07-19T13:30:00+08:00",
            "location": "台北市大安區新生南路三段 (實體教室)",
            "source_url": "https://www.accupass.com/event/12345",
            "registration_method": "透過 Accupass 線上報名",
            "summary": "本實戰工作坊將帶您從零開始使用 Python 串接 Gemini 3.5 與 Claude API，動態打造個人專屬的 AI Agent 工作流，包含自動化排程與信件通知。"
        },
        {
            "is_event": True,
            "event_title": "n8n 自動化大師班：3 小時打造 AI 網站客服助理",
            "event_date": "2026-07-25T14:00:00+08:00",
            "location": "線上會議 (Google Meet 連結將於報名後提供)",
            "source_url": "https://www.accupass.com/event/67890",
            "registration_method": "填寫 Google 表單完成報名",
            "summary": "教導如何使用開源自動化工具 n8n，無痛整合 Line / Slack 機器人與向量資料庫，3 小時內快速讓 AI 成為您的網站客服助理！"
        },
        {
            "is_event": True,
            "event_title": "【免費技術沙龍】Edge AI 邊緣運算晶片應用研討會",
            "event_date": "2026-08-01T10:00:00+08:00",
            "location": "高雄市軟體科學園區 A 棟",
            "source_url": None,  # 測試當沒有報名網址時的 UI 容錯排版
            "registration_method": "直接於社團貼文下方留言 +1 報名",
            "summary": "由耐能智慧專家分享最新的 Edge AI pi 開發板實作體驗，展示低功耗物件辨識與聲音感應晶片的工業物聯網實際案例。"
        }
    ]

    # 2. 初始化發信器並生成 HTML 內容
    sender = EmailSender()
    html_content = sender._build_html_content(mock_events)

    # 3. 寫入本地 HTML 檔案供瀏覽器檢視
    os.makedirs("cache", exist_ok=True)
    output_path = os.path.join("cache", "test_email.html")
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        log.info("--- 渲染測試成功 ---")
        log.info(f"已成功將 HTML 郵件模板寫入至本機檔案: {output_path}")
        log.info("提示：您現在可以直接在瀏覽器中雙擊開啟該 HTML 檔案，確認排版與按鈕美觀無跑版。")
    except Exception as e:
        log.exception(f"將渲染 HTML 寫入檔案失敗: {e}")

if __name__ == "__main__":
    main()
