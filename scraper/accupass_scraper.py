from playwright.async_api import async_playwright
from scraper.accupass_preprocessor import preprocess_accupass_text
from scraper.base_scraper import BaseScraper
import config

class AccupassScraper(BaseScraper):
    """
    針對 Accupass 平台網頁進行活動資訊抓取的適配爬蟲。
    """
    async def _scrape(self, url: str) -> str:
        """
        實作爬取 Accupass 頁面內容的邏輯。
        """
        # 依據環境變數切換 headless 模式，方便在開發期間進行偵錯
        is_headless = (config.ENVIRONMENT == "production")
        print(f"[AccupassScraper] 啟動 Playwright (headless={is_headless})...")

        # 使用 async with 語法確保在任何異常下均能妥善關閉 Playwright
        async with async_playwright() as p:
            # 啟動 Chromium 瀏覽器
            browser = await p.chromium.launch(headless=is_headless)
            try:
                # 建立一個新的瀏覽上下文
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                print(f"[AccupassScraper] 前往網址: {url}")
                # 載入頁面，設定超時時間為 30 秒
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # 等待 Accupass 主要活動列表或活動詳細內容區域加載完成
                # 這裡設定等待 5 秒或直到特定元素出現
                try:
                    print("[AccupassScraper] 等待活動連結 a[href*='/event/'] 載入...")
                    await page.wait_for_selector("a[href*='/event/']", timeout=8000)
                except Exception as e:
                    print(f"[AccupassScraper] 警告：等待活動連結超時: {e}")

                # 模擬自動滾動以載入動態內容，限制最多抓取 8 個活動卡片連結
                await self.auto_scroll(page, max_scrolls=10, scroll_delay=1000, target_selector="a[href*='/event/']", max_elements=8)

                # 擷取整個 body 的 innerText 作為分析的「生肉資料」
                print("[AccupassScraper] 正在擷取頁面 innerText...")
                raw_text = await page.locator("body").inner_text()

                if not raw_text.strip():
                    print("[AccupassScraper] 警告：擷取到的文字內容為空")

                return raw_text

            except Exception as e:
                print(f"[AccupassScraper] 爬取過程中發生錯誤: {e}")
                # 發生錯誤時傳回空字串，使主排程不崩潰
                return ""
            finally:
                # 妥善關閉瀏覽器與上下文
                await browser.close()
                print("[AccupassScraper] 瀏覽器已關閉 (Graceful Shutdown)")

    def preprocess_content(self, content: str) -> str:
        return preprocess_accupass_text(content)
