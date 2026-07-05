import random
import logging
from playwright.async_api import async_playwright
from scraper.base_scraper import BaseScraper
import config
import urllib.parse
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import asyncio
import re

# 初始化此模組專屬的 Logger
logger = logging.getLogger("FacebookScraper")

class GoogleBlockException(Exception):
    """
    當爬蟲遭遇 Google 機器人驗證碼 (CAPTCHA)、429 異常流量限制或 API 額度用盡時拋出的例外，
    用以觸發系統熔斷，保護伺服器 IP 並中斷當前運作。
    """
    pass

class FacebookScraper(BaseScraper):
    """
    重構後的 Facebook 爬蟲。
    支援雙路徑運作：
    1. Google Custom Search JSON API (預設，穩定性高)
    2. Playwright 模擬瀏覽器 (備用，無金鑰或降級時可用)
    """
    def __init__(self, use_api: bool = None):
        super().__init__()
        # 若未傳入參數，則自 config 讀取預設值，預設為 True
        self.use_api = use_api if use_api is not None else getattr(config, "FACEBOOK_SCRAPER_USE_API", True)

    async def _scrape(self, url: str) -> str:
        """
        核心爬取實作。依據 use_api 布林值切換執行路徑。
        """
        if self.use_api:
            logger.info("Facebook Scraper: 使用 Google Custom Search JSON API 進行搜尋...")
            return await self._scrape_via_api(url)
        else:
            logger.info("Facebook Scraper: 使用 Playwright 模擬瀏覽器進行搜尋 (備用模式)...")
            return await self._scrape_via_playwright(url)

    async def _scrape_via_api(self, url: str) -> str:
        """
        使用 Google Custom Search JSON API 檢索資料。
        """
        # 1. 解析傳入 URL 中的 q 與 tbs 參數
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        raw_query = query_params.get("q", [""])[0]
        tbs = query_params.get("tbs", [""])[0]

        if not raw_query:
            logger.warning("Google Custom Search API 模式：未從 URL 解析出搜尋關鍵字 (q)")
            return ""

        # 2. 清理 Query：過濾掉 site:facebook.com 或 site:www.facebook.com，避免與 CSE 範圍限制衝突
        cleaned_query = re.sub(r'site:(www\.)?facebook\.com', '', raw_query).strip()
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query) # 清理多餘空格

        # 3. 取得 API Key 與 CX 設定
        api_key = getattr(config, "GOOGLE_CSE_API_KEY", None)
        cx = getattr(config, "GOOGLE_CSE_CX", None)

        if not api_key or not cx:
            logger.error("未設定 GOOGLE_CSE_API_KEY 或 GOOGLE_CSE_CX，無法使用 API 路線。請於環境變數中設定。")
            return ""

        # 4. 轉換 tbs 時間限制 -> dateRestrict (如 qdr:w -> w1)
        date_restrict = None
        if "qdr:w" in tbs:
            date_restrict = "w1"
        elif "qdr:m" in tbs:
            date_restrict = "m1"
        elif "qdr:d" in tbs:
            date_restrict = "d1"

        # 5. 準備 API 參數
        api_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": cleaned_query,
            "num": 10,
            "hl": "zh-TW",
            "gl": "tw"
        }
        if date_restrict:
            params["dateRestrict"] = date_restrict

        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{api_url}?{encoded_params}"

        # 遮蔽敏感資訊的 Log，避免金鑰流出
        logger.info("啟動 Google Custom Search API 搜尋...")
        logger.debug(f"API 請求參數 (遮蔽金鑰): cx={cx}&q={cleaned_query}&num=10&hl=zh-TW&gl=tw" + (f"&dateRestrict={date_restrict}" if date_restrict else ""))

        # 6. 使用 asyncio.to_thread 執行非同步防阻塞網路請求
        def _do_request():
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "EventScraperAgent/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.status, response.read().decode("utf-8")

        try:
            status_code, response_body = await asyncio.to_thread(_do_request)
            data = json.loads(response_body)

            if "items" not in data:
                logger.warning("Google Custom Search API 返回 0 筆搜尋結果。")
                return ""

            extracted_lines = []
            for item in data.get("items", []):
                title = item.get("title", "無標題").replace("\n", " ").strip()
                link = item.get("link", "無連結")
                snippet = item.get("snippet", "無摘要").replace("\n", " ").strip()

                extracted_lines.append(f"[Title]: {title}")
                extracted_lines.append(f"[Link]: {link}")
                extracted_lines.append(f"[Snippet]: {snippet}")
                extracted_lines.append("---")

            raw_text = "\n".join(extracted_lines)
            logger.info(f"成功透過 Google Custom Search API 取得 {len(data.get('items', []))} 筆格式化資料")
            return raw_text

        except urllib.error.HTTPError as http_err:
            code = http_err.code
            try:
                # 讀取 Google API 回傳的詳細錯誤 Response Body 內容
                err_body = http_err.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = json.dumps(err_json, indent=2, ensure_ascii=False)
            except Exception:
                err_msg = err_body if 'err_body' in locals() else str(http_err)

            logger.error(f"Google API 回傳 HTTP 錯誤代碼: {code}")
            logger.error(f"Google API 詳細錯誤回傳內容:\n{err_msg}")

            if code == 429:
                logger.critical("Google Custom Search API 遭遇 HTTP 429 Too Many Requests (可能是每日免費額度已用盡)！")
                raise GoogleBlockException(f"Google Custom Search API Rate Limit (429) triggered. Details: {err_msg}")
            elif code == 403:
                logger.critical("Google Custom Search API 遭遇 HTTP 403 Forbidden (可能是 API Key 或 CX 設定錯誤，或額度阻擋)！")
                raise GoogleBlockException(f"Google Custom Search API Access Denied (403). Details: {err_msg}")
            else:
                logger.error(f"Google Custom Search API 回傳未預期 HTTP 錯誤: {code}")
                return ""
        except Exception as e:
            logger.exception(f"Google Custom Search API 搜尋過程中發生未知錯誤: {e}")
            return ""

    async def _scrape_via_playwright(self, url: str) -> str:
        """
        使用 Playwright 模擬瀏覽器爬取 Google SERP (降級備用方案)。
        """
        is_headless = (config.ENVIRONMENT == "production")
        
        # 定義常見的 Desktop User-Agents 供隨機輪替，降低被偵測率
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        selected_ua = random.choice(user_agents)
        logger.info(f"啟動 Playwright (headless={is_headless}, User-Agent={selected_ua})...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=is_headless)
            try:
                context = await browser.new_context(
                    user_agent=selected_ua,
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()

                # 模擬人類的隨機載入延遲 (500ms ~ 1500ms)
                delay = random.randint(500, 1500)
                await page.wait_for_timeout(delay)

                logger.info(f"前往 Google 搜尋 URL: {url}")
                # 載入頁面，超時時間設定為 30 秒
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # 1. 偵測 Google CAPTCHA 與異常流量熔斷 (Circuit Breaker)
                current_url = page.url
                if "google.com/sorry" in current_url:
                    logger.critical("遭遇 Google 機器人驗證碼防護牆 (CAPTCHA)！")
                    raise GoogleBlockException("Google CAPTCHA block detected on sorry redirect.")
                
                if response and response.status == 429:
                    logger.critical("收到 HTTP 429 Too Many Requests 限制！")
                    raise GoogleBlockException("Google HTTP 429 Rate Limit triggered.")

                page_title = await page.title()
                if "Unusual traffic" in page_title or "阻擋" in page_title:
                    logger.critical("Google 偵測到來自此 IP 的異常流量並進行阻擋。")
                    raise GoogleBlockException("Google Unusual Traffic block detected in page title.")

                # 2. 定位 Google 搜尋結果節點
                # Google 的每一條搜尋結果皆在 class="g" 的 div 中
                result_nodes = page.locator("div.g")
                node_count = await result_nodes.count()
                logger.info(f"偵測到 Google 搜尋結果節點數量: {node_count}")

                if node_count == 0:
                    # 檢查是否頁面有其他表示找不到結果的提示
                    body_text = await page.locator("body").inner_text()
                    if "找不到符合的搜尋結果" in body_text or "did not match any documents" in body_text:
                        logger.warning("Google 搜尋返回 0 筆結果 (No results matched).")
                        return ""
                    else:
                        logger.warning("未偵測到 div.g 搜尋節點，可能 Google 頁面結構變動或被隱性阻擋")
                        return ""

                # 3. 提取搜尋結果資訊 (標題, 連結, 摘要)
                extracted_lines = []
                for i in range(node_count):
                    node = result_nodes.nth(i)
                    try:
                        # 3.1 提取標題 (通常在 h3 中)
                        title_loc = node.locator("h3")
                        title = await title_loc.first.inner_text(timeout=2000) if await title_loc.count() > 0 else "無標題"

                        # 3.2 提取連結
                        a_loc = node.locator("a")
                        link = await a_loc.first.get_attribute("href", timeout=2000) if await a_loc.count() > 0 else "無連結"

                        # 3.3 提取網頁摘要 (Google 摘要目前常用 class 為 VwiC3b, yDskLc 或含有 line-clamp)
                        snippet_loc = node.locator("div[style*='webkit-line-clamp'], div.VwiC3b, div.yDskLc")
                        snippet = await snippet_loc.first.inner_text(timeout=2000) if await snippet_loc.count() > 0 else "無摘要"

                        # 清除多餘換行符
                        title = title.replace("\n", " ").strip()
                        snippet = snippet.replace("\n", " ").strip()

                        # 拼接成格式化文字
                        extracted_lines.append(f"[Title]: {title}")
                        extracted_lines.append(f"[Link]: {link}")
                        extracted_lines.append(f"[Snippet]: {snippet}")
                        extracted_lines.append("---")
                    except Exception as node_err:
                        logger.debug(f"解析第 {i+1} 個搜尋結果節點時跳過: {node_err}")
                        continue

                raw_text = "\n".join(extracted_lines)
                logger.info(f"成功解析 Google SERP，共取得 {len(extracted_lines) // 4} 筆格式化資料")
                return raw_text

            except GoogleBlockException:
                # 重新拋出熔斷例外，交由 Orchestrator 中斷 Pipeline
                raise
            except Exception as e:
                logger.exception(f"Google 搜尋爬取過程中發生錯誤: {e}")
                return ""
            finally:
                await browser.close()
                logger.info("瀏覽器已關閉 (Graceful Shutdown)")
