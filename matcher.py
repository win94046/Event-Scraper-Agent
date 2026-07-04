import os
import json
import hashlib
import logging
from typing import List, Set, Dict
import config

# 初始化此模組的 Logger
logger = logging.getLogger("Matcher")

def get_event_hash(event: Dict) -> str:
    """
    為單一活動計算唯一的 SHA-256 識別碼。
    優先使用活動報名 URL 作為識別依據；若 URL 為空，則使用活動標題加上活動日期作為識別。
    """
    source_url = event.get("source_url")
    if source_url and source_url.strip():
        unique_str = source_url.strip()
    else:
        # 當無 URL 時，以 標題_時間 組合進行雜湊
        event_title = event.get("event_title") or ""
        event_date = event.get("event_date") or ""
        unique_str = f"{event_title.strip()}_{event_date.strip()}"
        
    return hashlib.sha256(unique_str.encode("utf-8")).hexdigest()


def load_sent_history() -> Set[str]:
    """
    從本地 JSON 檔案中載入已經寄送過的活動 Hash 歷史記錄。
    回傳一個 Set[str]，便於 O(1) 複雜度快速檢索。
    """
    history_file = config.SENT_HISTORY_FILE
    if not os.path.exists(history_file):
        logger.info(f"去重歷史記錄檔 {history_file} 不存在，將初始化新的記錄")
        return set()

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # data 預設為 List[str]
            if isinstance(data, list):
                logger.debug(f"已從 {history_file} 載入 {len(data)} 筆已發送的活動歷史記錄")
                return set(data)
            else:
                logger.warning(f"歷史記錄檔格式不正確，將初始化空記錄")
                return set()
    except Exception as e:
        logger.error(f"讀取去重歷史記錄檔 {history_file} 失敗: {e}，將初始化空記錄")
        return set()


def save_sent_history(sent_history: Set[str]) -> bool:
    """
    將已寄送過的活動 Hash 集合寫回本地 JSON 檔案中保存。
    """
    history_file = config.SENT_HISTORY_FILE
    try:
        # 將 set 轉換為 list 進行 JSON 序列化
        history_list = sorted(list(sent_history))
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
        logger.debug(f"已成功將 {len(history_list)} 筆已發送記錄存回 {history_file}")
        return True
    except Exception as e:
        logger.error(f"儲存去重歷史記錄檔 {history_file} 失敗: {e}")
        return False


def filter_duplicates(events: List[Dict], sent_history: Set[str]) -> List[Dict]:
    """
    過濾掉已經存在於發送歷史 (sent_history) 中的重複活動。
    回傳過濾後的新活動列表。
    """
    unique_events = []
    skipped_count = 0
    
    for event in events:
        event_hash = get_event_hash(event)
        if event_hash in sent_history:
            logger.debug(f"發現重複活動，予以排除: 【{event.get('event_title')}】 (Hash: {event_hash[:8]})")
            skipped_count += 1
        else:
            unique_events.append(event)
            
    if skipped_count > 0:
        logger.info(f"去重過濾完成：已排除 {skipped_count} 個重複活動，剩餘 {len(unique_events)} 個全新活動。")
    else:
        logger.info(f"去重過濾完成：無發現重複活動，共 {len(events)} 個活動均為全新。")
        
    return unique_events


def match_user_interests(events: List[Dict], user_keywords: List[str]) -> List[Dict]:
    """
    比對活動列表與使用者的訂閱關鍵字。
    只要活動標題或活動摘要中包含任一關鍵字 (不區分大小寫，不計前後空格)，即視為配對成功。
    """
    matched_events = []
    
    # 清理並正規化使用者的關鍵字
    clean_keywords = [kw.strip().lower() for kw in user_keywords if kw and kw.strip()]
    
    if not clean_keywords:
        logger.warning("使用者未設定任何關鍵字，無法進行比對")
        return []

    for event in events:
        title = (event.get("event_title") or "").lower()
        summary = (event.get("summary") or "").lower()
        
        is_matched = False
        matched_kw = ""
        
        # 遍歷關鍵字，只要命中其中一個即可
        for kw in clean_keywords:
            if kw in title or kw in summary:
                is_matched = True
                matched_kw = kw
                break
                
        if is_matched:
            matched_events.append(event)
            logger.debug(f"配對成功! 活動: 【{event.get('event_title')}】 命中關鍵字: '{matched_kw}'")

    logger.info(f"關鍵字比對完成：篩選出 {len(matched_events)} / {len(events)} 個符合興趣的活動。")
    return matched_events
