from urllib.parse import quote

import aiohttp
import asyncio
import feedparser
from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib.parse import quote



def build_google_news_url(query, lang="pt", country="BR", start_date=None, end_date=None):
    encoded_query = quote(query)
    date_filter = ""
    if end_date:
        date_filter += f"%20before%3A{end_date.strftime('%Y-%m-%d')}"
    if start_date:
        date_filter += f"%20after%3A{start_date.strftime('%Y-%m-%d')}"
    return (
        f"https://news.google.com/rss/search?q={encoded_query}{date_filter}"
        f"&hl={lang}&gl={country}&ceid={country}:{lang}"
    )


def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text().replace("\xa0", " ").strip()


async def fetch_news(session, url, max_results=30):
    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
        if response.status != 200:
            print(f"Failed to fetch: {url}")
            return []

        text = await response.text()
        feed = feedparser.parse(text)

        articles = []
        for entry in feed.entries[:max_results]:
            articles.append({
                "title": entry.get("title", ""),
                "description": clean_html(entry.get("description", "")),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "")
            })
        return articles


async def get_news_async(query, start_date=None, end_date=None, lang="pt", country="BR", max_results=30):
    url = build_google_news_url(query, lang, country, start_date, end_date)
    async with aiohttp.ClientSession() as session:
        return await fetch_news(session, url, max_results)


# === Usage example
if __name__ == "__main__":
    async def main():
        brand = "Eletrobras"
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)
        articles = await get_news_async(brand, start, end)

        for art in articles:
            print(f"{art['published']} - {art['title']}")
            print(f"{art['url']} ({art['source']})\n")

    asyncio.run(main())