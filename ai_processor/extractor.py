import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import config

# 初始化此模組專屬的 Logger
logger = logging.getLogger("EventExtractor")

# ==========================================
# 定義 Pydantic 結構 (Structured Outputs)
# ==========================================

class EventDetail(BaseModel):
    """
    單一活動的標準資訊欄位結構。
    """
    is_event: bool = Field(
        ..., 
        description="這篇貼文或段落是否屬於活動宣傳（如讀書會、研討會、課程、論壇、分享會）"
    )
    event_title: Optional[str] = Field(
        None, 
        description="活動的主標題，例如：2026 AI 技術應用實戰讀書會"
    )
    event_date: Optional[str] = Field(
        None, 
        description="活動日期與時間，請儘可能轉換為 ISO 8601 格式，例如：2026-07-20T19:00:00+08:00"
    )
    location: Optional[str] = Field(
        None, 
        description="活動舉辦地點，可以是實體地址、線上會議連結（如 Zoom、Google Meet）或 '線上'"
    )
    source_url: Optional[str] = Field(
        None, 
        description="本活動的報名頁面 URL，或者是貼文來源網址"
    )
    registration_method: Optional[str] = Field(
        None, 
        description="報名方式，例如：'透過 Accupass 報名'、'填寫 Google 表單'、'直接於貼文留言'"
    )
    summary: Optional[str] = Field(
        None, 
        description="本活動的簡短大綱與摘要，重點說明這項活動會探討什麼主題"
    )

class ExtractedEvents(BaseModel):
    """
    一次萃取任務中，從網頁文字中解析出的所有活動列表包裹類別。
    """
    events: List[EventDetail] = Field(
        default=[], 
        description="從傳入文本中解析出來的活動資訊列表"
    )


# ==========================================
# 實作 AI Extractor 類別
# ==========================================

class EventExtractor:
    """
    使用 Google Gemini API 從非結構化文字中提取結構化活動資料的處理器。
    """
    def __init__(self):
        # 檢查 API Key 是否存在且非預設佔位符
        if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            logger.warning("未設定有效的 GEMINI_API_KEY。請先在根目錄的 .env 檔案中填入真實的金鑰。")
            self.client = None
        else:
            # 初始化 Gemini API 用戶端
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    async def extract_events(self, raw_text: str) -> List[dict]:
        """
        接收 Raw Text 原始文字，限制文字長度，呼叫 Gemini API 進行結構化萃取。
        內建自動退避重試 (Backoff Retry) 與異常捕獲機制。
        """
        if not self.client:
            logger.warning("由於 GEMINI_API_KEY 未正確設定，已跳過 AI 萃取流程，回傳空列表。")
            return []

        if not raw_text or not raw_text.strip():
            logger.info("傳入的文字內容為空，跳過處理。")
            return []

        # 防呆機制：限制文字長度 (例如 25000 字元) 避免超出 Token 限制
        max_chars = 25000
        if len(raw_text) > max_chars:
            logger.warning(f"偵測到文字長度過長 ({len(raw_text)} 字元)，將自動截斷至前 {max_chars} 字元")
            raw_text = raw_text[:max_chars]

        # 組合 System Prompt 與使用者輸入
        system_instruction = (
            "你是一個專業的活動資訊整理助理。你的任務是分析傳入的非結構化網頁文字內容（生肉資料），"
            "過濾掉無關的個人閒聊、廣告或非活動宣傳貼文。將所有屬於『研討會、讀書會、課程、論壇、分享會、技術沙龍』的活動資訊"
            "精確地萃取出來，並完全符合規定的 JSON 格式。"
            "如果貼文中有提及多個活動，請全部提取。如果完全沒有任何活動，請回傳空的 events 列表。"
        )

        prompt = f"請分析以下網頁文字內容，並從中萃取出所有活動：\n\n--- 網頁內容開始 ---\n{raw_text}\n--- 網頁內容結束 ---"

        import asyncio
        import json

        max_retries = 3
        backoff_factor = 2.0  # 重試秒數退避係數

        for attempt in range(max_retries):
            try:
                logger.info(f"正在傳送請求至 Gemini API (第 {attempt + 1} 次嘗試)...")
                # 異步呼叫 Gemini API
                response = await self.client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedEvents,
                        system_instruction=system_instruction,
                        temperature=0.1
                    )
                )

                # 解析回傳的 JSON 結構
                result_json = json.loads(response.text)
                
                extracted_list = []
                for item in result_json.get("events", []):
                    # 僅保留 is_event 判定為 True 且具有活動標題的活動
                    if item.get("is_event") and item.get("event_title"):
                        extracted_list.append(item)

                logger.info(f"萃取完成！成功從中提取出 {len(extracted_list)} 個有效活動。")
                return extracted_list

            except Exception as e:
                # 遇到錯誤，計算等待時間進行重試
                wait_time = backoff_factor ** attempt
                logger.warning(f"呼叫 Gemini API 發生異常: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"將於 {wait_time} 秒後進行第 {attempt + 2} 次重試...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("已達最大重試次數，宣告失敗，回傳空列表。")
                    return []
        
        return []
