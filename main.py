import argparse
import asyncio
import os
import json
import sys
import logging

# 導入自定義日誌配置
import logger
from scraper.accupass_scraper import AccupassScraper
from scraper.facebook_scraper import FacebookScraper
from ai_processor.extractor import EventExtractor
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
        parser.add_argument("--dry-run", action="store_true", help="只進行爬取與 AI 萃取，不寄送通知信")
        parser.add_argument("--test-email", action="store_true", help="單獨測試 SMTP 信箱寄信功能")
        args = parser.parse_args()

        # 確保快取與歷史記錄目錄存在
        os.makedirs(config.CACHE_DIR, exist_ok=True)

        if args.test_email:
            log.info("觸發發送測試郵件 (Notifier 模組開發中，暫無動作)")
            return

        # MVP 測試用 URL
        target_urls = {
            "accupass": "https://www.accupass.com/search?q=AI",
            "facebook": "https://www.facebook.com/groups/pythontw"
        }

        # 初始化 AI 處理模組
        extractor = EventExtractor()

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
            
            # 3. 印出分析結果
            log.info(f"AI 萃取結果 (共 {len(events)} 個活動):")
            # 同時也輸出明細至日誌中方便 Debug
            log.debug(json.dumps(events, indent=2, ensure_ascii=False))

            # 4. 存入本地 JSON 檔案
            output_path = os.path.join(config.CACHE_DIR, "extracted_events.json")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2, ensure_ascii=False)
                log.info(f"已成功將 AI 結構化資料存檔至: {output_path}")
            except Exception as save_err:
                log.error(f"存檔失敗: {save_err}")
            return

        # 情境二：完整 Pipeline (目前僅串接 Scraper 與 AI Processor)
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
            
            log.info(f"使用者 {user['user_id']} 爬取與 AI 萃取結束，累計取得 {len(all_extracted_events)} 個活動")
            
            # 在 dry-run 模式下，將完整 Pipeline 結果也寫入本地檔案
            if args.dry-run and all_extracted_events:
                output_path = os.path.join(config.CACHE_DIR, f"extracted_events_{user['user_id']}.json")
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(all_extracted_events, f, indent=2, ensure_ascii=False)
                    log.info(f"[Dry-run] 已成功將使用者 {user['user_id']} 的所有活動資料存檔至: {output_path}")
                except Exception as save_err:
                    log.error(f"存檔失敗: {save_err}")

    except Exception as pipeline_err:
        # 全域異常捕捉，在日誌中詳細印出崩潰軌跡 (Traceback) 供使用者 debug
        log.exception(f"系統在執行 Pipeline 過程中遭遇致命錯誤: {pipeline_err}")
        sys.exit(1)

if __name__ == "__main__":
    # 使用 Python 3.8+ 建議的 asyncio.run 啟動異步主迴圈
    asyncio.run(main())
