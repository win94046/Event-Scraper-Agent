import os
import hashlib

# 1. 取得本次 GCP 搜尋對應的 Google 搜尋 URL
url = 'https://www.google.com/search?q=site%3Afacebook.com%20%28%22google%20cloud%22%20OR%20%22gcp%22%29%20%28%22%E7%A0%94%E8%A8%8E%E6%9C%83%22%20OR%20%22%E8%AE%80%E6%9B%B8%E6%9C%83%22%20OR%20%22%E8%AC%9B%E5%BA%A7%22%20OR%20%22%E6%B4%BB%E5%8B%95%22%20OR%20%22workshop%22%20OR%20%22seminar%22%29%20%22%E5%8F%B0%E5%8C%97%22&tbs=qdr:m2'

# 2. 計算 MD5 雜湊
url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
cache_path = os.path.join('cache', f'{url_hash}.txt')

# 3. 準備模擬最近兩個月 Google Cloud (GCP) 台北研討會的 Google 搜尋結果內容
mock_content = """[Title]: 【實體】GCP UG Taiwan 台北小聚：Google Cloud 技術實務分享
[Link]: https://www.facebook.com/events/88998877?fbclid=tracking456
[Snippet]: 2026-08-15T19:00:00+08:00。在台北市中山區舉辦。本小聚將邀請 Google Cloud 專家分享企業自動化實務，使用 Google Cloud BigQuery 以及 Gemini 進行大數據分析，現場名額有限...
---
[Title]: 【實體】Google Cloud 雲端安全與權限防禦技術工作坊 (Workshop)
[Link]: https://www.facebook.com/events/55443388?fbclid=tracking789&utm_source=fb
[Snippet]: 2026-07-28T14:00:00+08:00。在台北市信義區舉辦。本技術工作坊專注於 Google Cloud (GCP) IAM 安全設定、VPC 防火牆架構以及 Google Cloud Platform 的資安防禦技術演練...
---
[Title]: 閒聊：大家在 gcp 上開 vm 都是怎麼做流量控制的？
[Link]: https://www.facebook.com/groups/gcpug/posts/112233
[Snippet]: 最近因為工作需要，在 Google Cloud Platform 上開了幾台 Compute Engine，想請教大家在 GCP 上都是怎麼規劃 VPC 與 Subnet 流量的...
---"""

# 4. 寫入快取
os.makedirs('cache', exist_ok=True)
with open(cache_path, 'w', encoding='utf-8') as f:
    f.write(mock_content)

print(f"成功建立 Google Cloud 測試的 Mock 快取檔案：{cache_path} (MD5: {url_hash})")
