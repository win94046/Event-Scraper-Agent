import os
import json
import logging
from playwright.async_api import async_playwright
from scraper.base_scraper import BaseScraper
import config

# 初始化此模組專屬的 Logger
logger = logging.getLogger("FacebookScraper")

class FacebookScraper(BaseScraper):
    """
    針對 Facebook 公開社團或粉絲專頁進行貼文抓取的適配爬蟲。
    支援載入 Cookie 以繞過登入牆。
    """
    async def _scrape(self, url: str) -> str:
        is_headless = (config.ENVIRONMENT == "production")
        logger.info(f"啟動 Playwright (headless={is_headless})...")

        async with async_playwright() as p:
            # 啟動 Chromium 瀏覽器
            browser = await p.chromium.launch(headless=is_headless)
            try:
                # 設定標準的使用者代理，避免被輕易識別為爬蟲
                context_args = {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                # 檢查本地是否具有匯出的 Facebook Cookies JSON 檔
                cookie_path = "facebook_cookies.json"
                if os.path.exists(cookie_path):
                    logger.info(f"偵測到 {cookie_path}，正在載入登入狀態...")
                    try:
                        with open(cookie_path, "r", encoding="utf-8") as f:
                            cookies = json.load(f)
                        context = await browser.new_context(**context_args)
                        await context.add_cookies(cookies)
                    except Exception as cookie_err:
                        logger.warning(f"載入 Cookie 失敗: {cookie_err}，改用訪客模式")
                        context = await browser.new_context(**context_args)
                else:
                    logger.info(f"未偵測到 {cookie_path}，將以訪客身份嘗試爬取公開頁面")
                    context = await browser.new_context(**context_args)

                page = await context.new_page()

                logger.info(f"前往網址: {url}")
                # 載入頁面，超時時間設定為 45 秒 (Facebook 有時載入較慢)
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")

                # 嘗試等待貼文核心容器加載 (Facebook 通常使用 role='feed' 或貼文 preview)
                try:
                    await page.wait_for_selector("div[role='feed'], div[data-ad-preview='message'], body", timeout=10000)
                except Exception:
                    logger.warning("等待貼文容器超時，可能頁面加載過慢或遭遇登入牆")

                # 自動滾動頁面，載入更多動態生成的貼文
                # 臉書貼文預設限制以滾動次數或特定貼文 container 作為 count
                await self.auto_scroll(page, max_scrolls=4, scroll_delay=2000, target_selector="div[data-ad-preview='message']", max_elements=5)

                # 擷取頁面 body 的 innerText
                logger.info("正在擷取頁面 innerText...")
                raw_text = await page.locator("body").inner_text()

                return raw_text

            except Exception as e:
                logger.exception(f"爬取過程中發生致命錯誤: {e}")
                return ""
            finally:
                await browser.close()
                logger.info("瀏覽器已關閉 (Graceful Shutdown)")
