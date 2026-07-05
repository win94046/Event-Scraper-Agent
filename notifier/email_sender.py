import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict
import config

# 初始化此模組專屬的 Logger
logger = logging.getLogger("EmailSender")

class EmailSender:
    """
    負責組裝 HTML 郵件模板，並透過 SMTP 發送活動通知信的模組。
    """
    def __init__(self):
        # 讀取並驗證 SMTP 配置，將屬性對齊 config.py 定義之變數
        self.server = config.SMTP_SERVER
        self.port = config.SMTP_PORT
        self.user = config.SENDER_EMAIL       # 載入寄件者 Email 作為登入帳號
        self.password = config.SENDER_PASSWORD # 載入應用程式密碼
        self.sender_email = config.SENDER_EMAIL # 預設以登入帳號作為發信人

        # 檢測 SMTP 配置是否齊備，若是預設提示值或空值，給予警告並停用實體發信功能
        if not all([self.server, self.port, self.user, self.password]) or self.password == "your_gmail_app_password_here":
            logger.warning("未偵測到完整的 SMTP 發信設定。請在根目錄的 .env 檔案中配置 SMTP 金鑰，否則無法實體發信。")
            self.is_configured = False
        else:
            self.is_configured = True

    def _build_html_content(self, matched_events: List[Dict]) -> str:
        """
        將活動資料動態渲染進精美的卡片式 HTML 郵件模板中。
        採用符合現代化設計美學的 CSS (圓角、陰影、豐富漸層按鈕)。
        """
        # 生成活動卡片的 HTML
        event_cards_html = ""
        for event in matched_events:
            title = event.get("event_title") or "未命名活動"
            date_str = event.get("event_date") or "時間未定"
            location = event.get("location") or "地點未定"
            summary = event.get("summary") or "無活動摘要"
            url = event.get("source_url") or "#"
            
            # 若 source_url 為空，按鈕顯示 "詳情請見平台"
            btn_text = "立即報名 / 查看詳情" if url != "#" else "暫無報名網址"
            btn_style = "background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); cursor: pointer;"
            if url == "#":
                btn_style = "background: #9ca3af; cursor: default;"

            event_cards_html += f"""
            <div class="event-card">
                <div class="event-title">{title}</div>
                <div class="event-meta">
                    <span class="meta-item">📅 <strong>時間：</strong>{date_str}</span>
                    <span class="meta-item">📍 <strong>地點：</strong>{location}</span>
                </div>
                <div class="event-summary">
                    {summary}
                </div>
                <div style="text-align: right; margin-top: 15px;">
                    <a href="{url}" class="action-button" style="{btn_style}">{btn_text}</a>
                </div>
            </div>
            """

        # 主模板
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f3f4f6;
                    margin: 0;
                    padding: 0;
                    color: #1f2937;
                }}
                .container {{
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                    padding: 30px 20px;
                    text-align: center;
                    color: #ffffff;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px 25px;
                }}
                .welcome-text {{
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 25px;
                    color: #4b5563;
                }}
                .event-card {{
                    background-color: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                    transition: transform 0.2s ease;
                }}
                .event-title {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #1e1b4b;
                    margin-bottom: 10px;
                    line-height: 1.4;
                }}
                .event-meta {{
                    font-size: 13px;
                    color: #6b7280;
                    margin-bottom: 12px;
                }}
                .meta-item {{
                    display: block;
                    margin-bottom: 4px;
                }}
                .event-summary {{
                    font-size: 14px;
                    line-height: 1.6;
                    color: #374151;
                    background-color: #f9fafb;
                    padding: 12px 15px;
                    border-left: 4px solid #6366f1;
                    border-radius: 4px;
                }}
                .action-button {{
                    display: inline-block;
                    padding: 10px 20px;
                    color: #ffffff !important;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 13px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                }}
                .footer a {{
                    color: #6366f1;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 Event Scraper Agent</h1>
                    <p>您的專屬 AI 社群活動訂閱通知</p>
                </div>
                <div class="content">
                    <div class="welcome-text">
                        您好！根據您所訂閱的關鍵字，系統今天為您發現了以下 <strong>{len(matched_events)}</strong> 個與您興趣相符的全新活動：
                    </div>
                    {event_cards_html}
                </div>
                <div class="footer">
                    此電子郵件由 Event Scraper Agent 自動整理發送。<br>
                    若您希望修改訂閱關鍵字，請聯絡系統管理員。
                </div>
            </div>
        </body>
        </html>
        """
        return html_template

    async def send_notification(self, recipient_email: str, matched_events: List[Dict]) -> bool:
        """
        組裝 HTML 信件，建立與 SMTP 伺服器的連線，並寄出郵件。
        """
        if not self.is_configured:
            logger.warning(f"由於 SMTP 尚未設定，已跳過寄信流程至 {recipient_email}。")
            return False

        if not matched_events:
            logger.info(f"無配對活動，跳過寄送郵件給 {recipient_email}。")
            return False

        # 1. 建立 MIME 複合信件物件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔔 AI 精選活動通知：今日為您挑選了 {len(matched_events)} 個全新活動！"
        msg["From"] = f"Event Scraper Agent <{self.sender_email}>"
        msg["To"] = recipient_email

        # 2. 渲染並附加 HTML 內容
        html_body = self._build_html_content(matched_events)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 3. 連線 SMTP 伺服器並發送
        try:
            logger.info(f"正在連線至 SMTP 伺服器 {self.server}:{self.port} ...")
            # 建立 SMTP 連線
            # 對於常見的 SSL (465) 或 TLS (587)，做相容處理
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.server, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.server, self.port, timeout=15)
                # 若為一般埠口，開啟 TLS 加密
                server.ehlo()
                server.starttls()
                server.ehlo()

            logger.info(f"正在登入發信帳號: {self.user} ...")
            server.login(self.user, self.password)

            logger.info(f"正在傳送郵件給 {recipient_email} ...")
            server.sendmail(self.sender_email, recipient_email, msg.as_string())
            
            # 關閉連線
            server.quit()
            logger.info(f"郵件已成功寄送至: {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError as auth_err:
            # 捕獲認證失敗 (如密碼錯誤，應用程式金鑰未開)
            logger.error(f"SMTP 登入驗證失敗！請檢查您的應用程式密碼設定是否正確。錯誤原因: {auth_err}")
            return False
        except Exception as e:
            # 全域異常捕捉，詳細記錄發信崩潰原因 (如連線拒絕、超時、IP封鎖)，提供 Stack Trace
            logger.exception(f"透過 SMTP 發送郵件至 {recipient_email} 過程中發生錯誤: {e}")
            return False
