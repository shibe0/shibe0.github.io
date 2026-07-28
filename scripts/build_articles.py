#!/usr/bin/env python3
"""SubstackのRSSフィードから articles.json を生成する。

GitHub Actionsが毎日実行し、新しい記事が出ていれば articles.json を更新してコミットする。
ローカルでも実行可能: python3 scripts/build_articles.py
(macOSローカルでSSL証明書エラーが出る場合は、curlで /tmp/shibe-feed.xml に落としてから実行すると
 そちらを優先して読む)
"""
import html
import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED_URL = "https://shibe0.substack.com/feed"
OUT = Path(__file__).resolve().parent.parent / "articles.json"
LOCAL_FALLBACK = Path("/tmp/shibe-feed.xml")


def fetch_feed():
    if LOCAL_FALLBACK.exists():
        return LOCAL_FALLBACK.read_text(encoding="utf-8")
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0 (shibe-site)"})
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except urllib.error.URLError:
        # ローカルMacの証明書問題への保険(CI上では通常ここに来ない)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=30, context=ctx).read().decode("utf-8")


def parse_articles(xml_text):
    root = ET.fromstring(xml_text)
    articles = []
    for item in root.findall(".//item"):
        def text_of(tag):
            return html.unescape((item.findtext(tag) or "").strip())

        enclosure = item.find("enclosure")
        articles.append(
            {
                "title": text_of("title"),
                "subtitle": text_of("description"),
                "link": text_of("link").split("?")[0],
                "pubDate": text_of("pubDate"),
                "image": enclosure.get("url") if enclosure is not None else None,
            }
        )
    if not articles:
        raise SystemExit("ERROR: フィードから記事が1本も取れませんでした(サイトを壊さないため更新中止)")
    return articles


def main():
    articles = parse_articles(fetch_feed())
    OUT.write_text(
        json.dumps(articles, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"OK: {len(articles)}本を {OUT.name} に書き出しました")


if __name__ == "__main__":
    main()
