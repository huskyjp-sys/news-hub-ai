import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

categories = {
    "国内": "日本 国内 ニュース",
    "テクノロジー": "テクノロジー 最新",
    "AI": "人工知能 AI 最新",
    "エンタメ": "エンタメ 最新",
    "科学": "科学 最新",
    "医療": "医療 最新",
    "株式": "日本 株式市場",
    "投資": "投資 経済"
}

articles = []

for category, query in categories.items():
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=ja&gl=JP&ceid=JP:ja"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())

        for item in root.findall(".//item")[:8]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            source = item.findtext("source", "Google News")
            pub_date = item.findtext("pubDate", "")

            articles.append({
                "category": category,
                "title": title,
                "source": source,
                "published_at": pub_date,
                "summary": "記事の詳細は配信元で確認できます。",
                "points": "",
                "url": link
            })

    except Exception as error:
        print(category, error)

data = {
    "updated_at": datetime.now(
        timezone.utc
    ).astimezone().isoformat(),
    "articles": articles
}

with open("data/news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"{len(articles)}件のニュースを取得しました")
