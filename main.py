import argparse
import asyncio
import os
import json
import sys
import logging

# 導入自定義日誌與核心模組
import logger
import matcher
from scraper.accupass_scraper import AccupassScraper
from scraper.facebook_scraper import FacebookScraper
from ai_processor.extractor import EventExtractor
from notifier.email_sender import EmailSender
import config

# 強制終端機以 UTF-8 編碼輸出，防止 Windows CP950 無法解析 Emoji 🔥 導致崩潰
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


async def run_scraper(platform: str, url: str) -> str:
    """
    根據平台名稱，初始化並執行對應的 Scraper 實例。
    """
    log = logging.getLogger("Orchestrator")
    if platform.lower() == "accupass":
        scraper = AccupassScraper()
    elif platform.lower() == "facebook":
        scraper = FacebookScraper()
    else:
        log.error(f"不支援的平台: {platform}")
        return ""
        
    return await scraper.fetch_content(url)

async def main():
    # 初始化全域日誌系統 (同時輸出至終端機與 logs/event_scraper.log 檔案)
    logger.setup_logging()
    log = logging.getLogger("Orchestrator")

    try:
        # 設定 CLI 命令列參數解析器
        parser = argparse.ArgumentParser(description="AI 社交平台活動搜集與訂閱通知系統 (Event-Scraper-Agent)")
        parser.add_argument("--platform", type=str, choices=["accupass", "facebook"], help="指定要單獨爬取與測試的平台")
        parser.add_argument("--dry-run", action="store_true", help="只進行爬取與 AI 萃取，不寄送通知信，也不寫入去重歷史")
        parser.add_argument("--test-email", action="store_true", help="單獨測試 SMTP 信箱寄信功能")
        args = parser.parse_args()

        # 確保快取與歷史記錄目錄存在
        os.makedirs(config.CACHE_DIR, exist_ok=True)

        # 初始化 AI 處理、去重與郵件通知模組
        extractor = EventExtractor()
        notifier = EmailSender()
        sent_history = matcher.load_sent_history()

        # 測試模式：發送測試信件
        if args.test_email:
            log.info("觸發發送測試郵件，正在組裝測試資料...")
            mock_events = [
                {
                    "is_event": True,
                    "event_title": "【測試】AI 應用與 Agent 自動化實戰技術研討會",
                    "event_date": "2026-07-20T19:00:00+08:00",
                    "location": "線上會議 (Zoom)",
                    "source_url": "https://www.accupass.com",
                    "registration_method": "線上註冊",
                    "summary": "本信件由 Event Scraper Agent 系統自動發送，用於驗證您的 SMTP (Gmail) 發信服務是否運作正常。"
                }
            ]
            recipient = config.USERS[0]["email"]
            log.info(f"將向預設測試收件人發信: {recipient}")
            success = await notifier.send_notification(recipient, mock_events)
            if success:
                log.info("測試郵件發送成功！請檢查收件箱。")
            else:
                log.error("測試郵件發送失敗。請檢視上方日誌與設定。")
            return

        # MVP 測試用 URL
        target_urls = {
            "accupass": "https://www.accupass.com/search?q=AI",
            "facebook": "https://www.facebook.com/groups/pythontw"
        }

        # 情境一：使用者指定單獨測試某平台
        if args.platform:
            url = target_urls.get(args.platform)
            log.info(f"開始單一平台測試: {args.platform} -> {url}")
            
            # 1. 爬取原始文字 (具備快取功能)
            raw_text = await run_scraper(args.platform, url)
            log.info(f"成功擷取到 {len(raw_text)} 個字元的原始文字內容")
            
            # 2. 呼叫 LLM 進行活動萃取
            log.info("開始呼叫 AI 模組進行活動分析...")
            events = await extractor.extract_events(raw_text)
            
            # 3. 執行去重過濾 (Matcher)
            log.info("開始進行去重歷史過濾 (De-duplication)...")
            unique_events = matcher.filter_duplicates(events, sent_history)

            # 4. 對預設的使用者關鍵字進行興趣比對 (以 config 中的第一個使用者 u001 為例)
            test_user = config.USERS[0]
            log.info(f"正在針對測試使用者 {test_user['user_id']} 的訂閱關鍵字 {test_user['keywords']} 進行興趣配對...")
            matched_events = matcher.match_user_interests(unique_events, test_user["keywords"])

            # 5. 印出最終分析與配對結果
            log.info(f"【單一平台測試報告】:")
            log.info(f"  - LLM 原始萃取數: {len(events)} 個")
            log.info(f"  - 排除已寄送重複: {len(events) - len(unique_events)} 個")
            log.info(f"  - 使用者關鍵字命中: {len(matched_events)} 個")
            log.debug(json.dumps(matched_events, indent=2, ensure_ascii=False))

            # 6. 存入本地 JSON 檔案
            output_path = os.path.join(config.CACHE_DIR, "extracted_events.json")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(matched_events, f, indent=2, ensure_ascii=False)
                log.info(f"已成功將最終配對後的活動存檔至: {output_path}")
            except Exception as save_err:
                log.error(f"存檔失敗: {save_err}")
                
            # 若不是 dry-run，模擬進行通知寄送與歷史寫入
            if not args.dry_run and matched_events:
                log.info(f"非 Dry-run 模式，開始向測試使用者 {test_user['email']} 傳送通知郵件...")
                send_success = await notifier.send_notification(test_user["email"], matched_events)
                
                if send_success:
                    log.info("郵件發送成功，將本次活動寫入去重歷史記錄...")
                    for evt in matched_events:
                        evt_hash = matcher.get_event_hash(evt)
                        sent_history.add(evt_hash)
                    matcher.save_sent_history(sent_history)
                else:
                    log.warning("郵件發送失敗，本次活動暫不寫入歷史，下次運行時將會重新發送。")
            return

        # 情境二：完整 Pipeline
        log.info("啟動系統 Pipeline...")
        for user in config.USERS:
            log.info(f"處理使用者 {user['user_id']} ({user['email']}) 的訂閱清單...")
            all_extracted_events = []
            
            # 爬取使用者訂閱的所有平台
            for platform in user["platforms"]:
                url = target_urls.get(platform)
                if url:
                    log.info(f"正在爬取 {platform} -> {url}")
                    raw_text = await run_scraper(platform, url)
                    
                    # 萃取活動
                    events = await extractor.extract_events(raw_text)
                    all_extracted_events.extend(events)
            
            log.info(f"使用者 {user['user_id']} 爬取與 AI 萃取結束，共取得 {len(all_extracted_events)} 個原始活動")
            
            # 進行去重
            log.info("開始進行已寄送去重過濾...")
            unique_events = matcher.filter_duplicates(all_extracted_events, sent_history)

            # 進行興趣配對
            log.info(f"開始為使用者進行興趣配對...")
            matched_events = matcher.match_user_interests(unique_events, user["keywords"])
            
            log.info(f"使用者 {user['user_id']} 最終獲得 {len(matched_events)} 個全新且符合興趣的活動通知")

            # 在 dry-run 模式下，將完整 Pipeline 結果寫入本地檔案，方便查閱
            if args.dry_run:
                if matched_events:
                    output_path = os.path.join(config.CACHE_DIR, f"extracted_events_{user['user_id']}.json")
                    try:
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(matched_events, f, indent=2, ensure_ascii=False)
                        log.info(f"[Dry-run] 已成功將使用者 {user['user_id']} 的配對結果存檔至: {output_path}")
                    except Exception as save_err:
                        log.error(f"存檔失敗: {save_err}")
            else:
                # 正式執行：寄信且更新去重歷史記錄
                if matched_events:
                    log.info(f"正在向使用者 {user['user_id']} ({user['email']}) 傳送 HTML 訂閱通知信...")
                    send_success = await notifier.send_notification(user["email"], matched_events)
                    
                    if send_success:
                        log.info("通知信寄送成功，將本次活動寫入去重歷史記錄...")
                        for evt in matched_events:
                            evt_hash = matcher.get_event_hash(evt)
                            sent_history.add(evt_hash)
                        matcher.save_sent_history(sent_history)
                    else:
                        log.error(f"使用者 {user['user_id']} 的郵件寄送失敗，暫不寫入去重歷史。")

    except Exception as pipeline_err:
        log.exception(f"系統在執行 Pipeline 過程中遭遇致命錯誤: {pipeline_err}")
        sys.exit(1)

if __name__ == "__main__":
    # 使用 Python 3.8+ 建議的 asyncio.run 啟動異步主迴圈
    asyncio.run(main())
