
import urllib.error
import json
import os
import re
import time
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "openai/gpt-oss-20b"

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


def ai_summary(title, description):
    if not API_KEY:
        return description or "AI要約は未設定です。", ""

    prompt = f"""
次のニュースを日本語で簡潔に整理してください。

タイトル：{title}
記事概要：{description}

必ず次の形式で回答してください。

要約：
ニュースの内容を100文字程度で説明

ポイント：
・重要ポイント1
・重要ポイント2
・重要ポイント3

JSONやコードブロックは使わないでください。
記事概要にない事実は追加しないでください。
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "あなたは正確性を重視する日本語ニュース編集者です。指定された形式で簡潔に回答してください。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_completion_tokens": 500
    }

    request_data = json.dumps(payload).encode("utf-8")

    for attempt in range(3):
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=request_data,
            headers={
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
                "User-Agent": "NEWS-HUB-AI/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            content = result["choices"][0]["message"]["content"].strip()
            print("AI生回答:", repr(content))

            summary_match = re.search(
                r"要約[：:]\s*(.*?)(?=ポイント[：:]|$)",
                content,
                re.S
            )

            points_match = re.search(
                r"ポイント[：:]\s*(.*)",
                content,
                re.S
            )

            if summary_match:
                summary = summary_match.group(1).strip()
            else:
                summary = content

            points = (
                points_match.group(1).strip()
                if points_match else ""
            )

            summary = summary.replace("```", "").strip()
            points = points.replace("```", "").strip()

            if not summary:
                raise ValueError("AIの要約が空でした")

            return summary, points

        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")

            if error.code == 429 and attempt < 2:
                print("利用上限に到達。15秒待って再試行します")
                time.sleep(15)
                continue

            print("AI要約エラー:", error.code, detail)
            return description or "要約を取得できませんでした。", ""

        except Exception as error:
            print("AI要約エラー:", error)
            return description or "要約を取得できませんでした。", ""

    return description or "要約を取得できませんでした。", ""


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

        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            source = item.findtext("source", "Google News")
            pub_date = item.findtext("pubDate", "")

            description = item.findtext("description", "")
            description = re.sub(
                r"<[^>]+>", " ", description
            )
            description = html.unescape(description).strip()

            if API_KEY:
                summary, points = ai_summary(
                    title, description
                )
                time.sleep(8)
            else:
                summary = description or "概要なし"
                points = ""

            articles.append({
                "category": category,
                "title": title,
                "source": source,
                "published_at": pub_date,
                "summary": summary,
                "points": points,
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

os.makedirs("data", exist_ok=True)

with open("data/news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"{len(articles)}件のニュースを取得しました")
print("AI要約処理が完了しました")
