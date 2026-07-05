import unittest
from matcher import normalize_url, get_event_hash

class MatcherAdvancedTest(unittest.TestCase):
    def test_normalize_url_strips_tracking_params(self):
        """
        測試常見的 Facebook fbclid 以及 Google UTM 廣告追蹤參數，
        是否能被 normalize_url 成功移除，回傳乾淨的主網址。
        """
        url_with_tracking = "https://www.accupass.com/event/123456789?fbclid=IwAR0ABC123&utm_source=facebook&utm_medium=social&utm_campaign=ai_camp"
        expected = "https://www.accupass.com/event/123456789"
        self.assertEqual(normalize_url(url_with_tracking), expected)

    def test_normalize_url_keeps_valuable_params(self):
        """
        測試實用的業務 Query 參數 (如 search q 與 category)
        是否能被正常保留，不被誤傷。
        """
        url_with_valuable = "https://www.google.com/search?q=Python&category=tech&fbclid=xyz"
        expected = "https://www.google.com/search?q=Python&category=tech"
        self.assertEqual(normalize_url(url_with_valuable), expected)

    def test_get_event_hash_deduplication(self):
        """
        測試兩個相同的活動，若其 source_url 帶有不同的追蹤參數，
        計算出來的 hash 仍須完全一致，以保證去重機制能成功運作。
        """
        evt1 = {
            "source_url": "https://www.accupass.com/event/987?fbclid=userA_click",
            "event_title": "AI 研討會",
            "event_date": "2026-07-20"
        }
        evt2 = {
            "source_url": "https://www.accupass.com/event/987?fbclid=userB_click&utm_source=ad",
            "event_title": "AI 研討會",
            "event_date": "2026-07-20"
        }
        
        hash1 = get_event_hash(evt1)
        hash2 = get_event_hash(evt2)
        self.assertEqual(hash1, hash2)

if __name__ == "__main__":
    unittest.main()
