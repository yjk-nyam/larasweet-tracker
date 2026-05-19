import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime

CLIENT_ID = os.environ["NAVER_CLIENT_ID"]
CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]

KEYWORDS = [
    "라라스윗요거트바",
    "라라스윗망고요거트바",
    "라라스윗듬뿍바",
    "라라스윗딸기듬뿍바",
    "라라스윗제로바",
    "애플망고생요거트바",
]

def search(query, stype):
    url = f"https://openapi.naver.com/v1/search/{stype}.json?query={urllib.parse.quote(query)}&display=50&sort=date"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode("utf-8")).get("items", [])
    except Exception as e:
        print(f"오류: {stype}/{query}: {e}")
        return []

def clean(t):
    return re.sub(r"<[^>]+>", "", t)

def parse_date(d):
    for fmt in ["%a, %d %b %Y %H:%M:%S +0900", "%Y%m%d"]:
        try:
            return datetime.strptime(d, fmt).strftime("%Y-%m-%d")
        except:
            pass
    return d

existing = []
if os.path.exists("data.json"):
    with open("data.json", "r", encoding="utf-8") as f:
        existing = json.load(f)

seen = set(d["link"] for d in existing)
new_items = []

for kw in KEYWORDS:
    print(f"검색 중: {kw}")
    for stype, label in [("blog", "네이버 블로그"), ("cafearticle", "네이버 카페")]:
        for item in search(kw, stype):
            link = item.get("link", "")
            if link in seen:
                continue
            seen.add(link)
            new_items.append({
                "title": clean(item.get("title", "")),
                "link": link,
                "platform": label,
                "keyword": kw,
                "source": clean(item.get("bloggername") or item.get("cafename", "")),
                "date": parse_date(item.get("postdate", "")),
                "content": clean(item.get("description", "")),
                "collected": datetime.now().strftime("%Y-%m-%d"),
            })

all_data = new_items + existing
all_data.sort(key=lambda x: x["date"], reverse=True)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"완료! 신규 {len(new_items)}건 / 전체 {len(all_data)}건")
