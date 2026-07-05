import os
import time
import hashlib
import logging
from abc import ABC, abstractmethod
import config

# 初始化此模組專屬的 Logger
logger = logging.getLogger("BaseScraper")

class BaseScraper(ABC):
    """
    爬蟲基底抽象類別，提供通用 Playwright 瀏覽器生命週期管理、
    本地快取讀寫邏輯，以及網頁自動滾動等功能。
    """
    def __init__(self):
        # 如果啟用快取，初始化時建立快取資料夾
        if config.USE_CACHE:
            os.makedirs(config.CACHE_DIR, exist_ok=True)

    def _get_cache_path(self, url: str) -> str:
        """
        將 URL 雜湊化 (MD5) 作為檔名，產出本地快取檔案路徑。
        """
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        return os.path.join(config.CACHE_DIR, f"{url_hash}.txt")

    async def fetch_content(self, url: str) -> str:
        """
        核心爬取進入點。
        若快取啟用且快取檔案在 TTL 內有效，則直接讀取快取；否則線上爬取並更新快取。
        """
        if config.USE_CACHE:
            cache_path = self._get_cache_path(url)
            if os.path.exists(cache_path):
                try:
                    # 取得快取檔案的最後修改時間並計算其存活時數
                    mtime = os.path.getmtime(cache_path)
                    cache_age_hours = (time.time() - mtime) / 3600
                    
                    if cache_age_hours < config.CACHE_TTL_HOURS:
                        logger.info(f"快取命中 (Cache Hit - 已存活 {cache_age_hours:.2f} 小時，限制上限 {config.CACHE_TTL_HOURS} 小時): {url}")
                        with open(cache_path, "r", encoding="utf-8") as f:
                            return f.read()
                    else:
                        logger.info(f"快取已過期 (Cache Expired - 已存活 {cache_age_hours:.2f} 小時，大於限制上限 {config.CACHE_TTL_HOURS} 小時): {url}")
                except Exception as e:
                    logger.warning(f"檢測或讀取快取檔案失敗: {e}，將改為線上抓取")

        logger.info(f"快取未命中 (Cache Miss)，啟動線上爬取: {url}")
        content = await self._scrape(url)

        # 爬取成功後，若有內容且開啟快取，則寫入本地
        if config.USE_CACHE and content:
            cache_path = self._get_cache_path(url)
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"成功將網頁內容存入快取: {cache_path}")
            except Exception as e:
                logger.error(f"寫入快取檔案失敗: {e}")

        return content

    @abstractmethod
    async def _scrape(self, url: str) -> str:
        """
        實際爬取邏輯。此方法必須由子適配器類別 (Sub-class Scrapers) 實作。
        """
        pass

    async def auto_scroll(
        self, 
        page, 
        max_scrolls: int = 10, 
        scroll_delay: int = 1500,
        target_selector: str = None,
        max_elements: int = 10
    ) -> None:
        """
        輔助方法：自動向下滑動頁面以載入動態加載的貼文或元素。
        page: Playwright Page 實例
        max_scrolls: 最大滾動次數
        scroll_delay: 每次滾動後等待頁面渲染的毫秒數
        target_selector: 用於計數的目標元素 CSS 選擇器。若網頁上該元素數量達到 max_elements，則停止滾動。
        max_elements: 目標元素數量的上限門檻
        """
        logger.info(f"啟動自動捲動頁面 (最大捲動 {max_scrolls} 次，目標數量限制 {max_elements} 個)...")
        for i in range(max_scrolls):
            # 檢查目前目標元素的數量
            if target_selector:
                element_count = await page.locator(target_selector).count()
                logger.debug(f"目前偵測到目標元素數量: {element_count} / {max_elements}")
                if element_count >= max_elements:
                    logger.info(f"目標元素數量已達上限 ({element_count} >= {max_elements})，提早停止滾動")
                    break

            # 取得目前網頁總高度
            last_height = await page.evaluate("document.body.scrollHeight")
            # 滾動至底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # 等待特定延遲時間
            await page.wait_for_timeout(scroll_delay)
            # 重新取得網頁總高度
            new_height = await page.evaluate("document.body.scrollHeight")
            # 若高度無變化，代表已無新內容載入，提早退出
            if new_height == last_height:
                logger.info(f"頁面已觸底，於第 {i+1} 次滾動停止")
                break
        logger.info("自動捲動結束")
