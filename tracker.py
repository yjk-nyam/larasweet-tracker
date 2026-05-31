import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime

NAVER_CLIENT_ID = os.environ["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

BRAND = "라라스윗"

KEYWORDS = [
    "라라스윗요거트바",
    "라라스윗망고요거트바",
    "라라스윗듬뿍바",
    "라라스윗딸기듬뿍바",
    "라라스윗제로바",
    "애플망고생요거트바",
]

def get_search_params(keyword):
    """검색어와 필수 포함 단어 목록 반환"""
    if keyword.startswith(BRAND):
        product = keyword[len(BRAND):]
        return product, [BRAND, product]  # 라라스윗 + 제품명 둘 다 포함
    return keyword, [keyword]

def should_include(text_fields, must_contain):
    """must_contain 단어들이 모두 포함된 경우만 True"""
    combined = " ".join(text_fields).lower()
    return all(word.lower() in combined for word in must_contain)

def naver_search(query, stype):
    url = f"https://openapi.naver.com/v1/search/{stype}.json?query={urllib.parse.quote(query)}&display=50&sort=date"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode("utf-8")).get("items", [])
    except Exception as e:
        print(f"네이버 오류: {stype}/{query}: {e}")
        return []

def youtube_search(query):
    if not YOUTUBE_API_KEY:
        return []
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&order=date&maxResults=50&key={YOUTUBE_API_KEY}"
    try:
        res = urllib.request.urlopen(url)
        data = json.loads(res.read().decode("utf-8"))
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item["snippet"]["title"],
                "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "platform": "유튜브",
                "source": item["snippet"]["channelTitle"],
                "date": item["snippet"]["publishedAt"][:10],
                "content": item["snippet"]["description"],
            })
        return results
    except Exception as e:
        print(f"유튜브 오류: {query}: {e}")
        return []

def clean(t):
    return re.sub(r"<[^>]+>", "", t or "")

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
    search_query, must_contain = get_search_params(kw)
    print(f"검색 중: {kw} → '{search_query}' 검색, 필수포함: {must_contain}")

    # 네이버 블로그 + 카페
    for stype, label in [("blog", "네이버 블로그"), ("cafearticle", "네이버 카페")]:
        for item in naver_search(search_query, stype):
            title = clean(item.get("title", ""))
            desc = clean(item.get("description", ""))
            source = clean(item.get("bloggername") or item.get("cafename", ""))
            if not should_include([title, desc, source], must_contain):
                continue
            link = item.get("link", "")
            if link in seen:
                continue
            seen.add(link)
            new_items.append({
                "title": title,
                "link": link,
                "platform": label,
                "keyword": kw,
                "source": source,
                "date": parse_date(item.get("postdate", "")),
                "content": desc,
                "collected": datetime.now().strftime("%Y-%m-%d"),
            })

    # 유튜브
    for item in youtube_search(search_query):
        title = item.get("title", "")
        content = item.get("content", "")
        source = item.get("source", "")
        if not should_include([title, content, source], must_contain):
            continue
        link = item.get("link", "")
        if link in seen:
            continue
        seen.add(link)
        new_items.append({
            "title": title,
            "link": link,
            "platform": "유튜브",
            "keyword": kw,
            "source": source,
            "date": item.get("date", ""),
            "content": content,
            "collected": datetime.now().strftime("%Y-%m-%d"),
        })

all_data = new_items + existing
all_data.sort(key=lambda x: x["date"], reverse=True)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"완료! 신규 {len(new_items)}건 / 전체 {len(all_data)}건")
