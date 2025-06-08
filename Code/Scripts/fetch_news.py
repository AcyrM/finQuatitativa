from urllib.parse import quote

import aiohttp
import asyncio
import feedparser
from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib.parse import quote
from newspaper import Article
from googlenewsdecoder import gnewsdecoder
import pandas as pd
from tqdm import tqdm

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "joeddav/xlm-roberta-large-xnli"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

# === Define intent categories
INTENT_LABELS = [
    "positive_finance",
    "negative_finance",
    "regulation_policy",
    "merger_movement",
    "operational_event",
    "macro_crisis",
    "reputation_risk",
    "neutral_info"
]

# === Fetch news articles from Google News RSS feed and extract full content
async def extract_full_content(url):
    def _parse_article():
        article = Article(url)
        article.download()
        article.parse()
        return article.text

    try:
        text = await asyncio.to_thread(_parse_article)
        return text
    except Exception as e:
        print(f"Error extracting article from {url}: {e}")
        return ""


async def fetch_news(session, url, max_results=30):


    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
        if response.status != 200:
            print(f"Failed to fetch: {url}")
            return []

        text = await response.text()
        feed = feedparser.parse(text)
        

        articles = []
        for entry in feed.entries[:max_results]:
            google_link = entry.get("link", "")
            real_url = gnewsdecoder(google_link)['decoded_url']
            full_text = await extract_full_content(real_url)

            articles.append({
                "title": entry.get("title", ""),
                "description": BeautifulSoup((entry.get("description", "")), "html.parser").get_text().replace("\xa0", " ").strip(),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", ""),
                "full_text": full_text
            })
        return articles


async def get_news_async(query, start_date=None, end_date=None, lang="pt", country="BR", max_results=30):
    
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
    
    url = build_google_news_url(query, lang, country, start_date, end_date)
    async with aiohttp.ClientSession() as session:
        return await fetch_news(session, url, max_results)

# === Process a list of articles into time-series DataFrame
def classify_article(text):



    try:
        result = classifier(text, INTENT_LABELS)
        return result["labels"][0]
    except Exception as e:
        print(f"Error in classification: {e}")
        return "unknown"
    
def classify_articles_to_timeseries(articles):
    """
    articles: list of dicts, each must have:
        - 'published': date string (or datetime)
        - 'title': str
        - 'full_text': str
    """
    rows = []
    print("Classifying article intents...")

    for article in tqdm(articles):
        text = f"{article['title']} {article['full_text']}"
        intent = classify_article(text)

        # Normalize date
        try:
            date = pd.to_datetime(article["published"]).date()
        except Exception:
            continue

        rows.append({
            "date": date,
            "intent": intent
        })

    df = pd.DataFrame(rows)

    # Pivot to time-series counts
    timeseries_df = df.pivot_table(index="date", columns="intent", aggfunc="size", fill_value=0).sort_index()

    return timeseries_df


# === Usage example
if __name__ == "__main__":
    async def main():
        brand = "Taesa"
        start = date(2020, 10, 1)
        end = date(2020, 12, 31)
        articles = await get_news_async(brand, start, end)

        for art in articles:
            print(f"{art['published']} - {art['title']}")
            # print(f"{art['url']} ({art['source']})\n")
            # print(f"{art['full_text']}\n")

        
        df = classify_articles_to_timeseries(articles)
        print(df)

    asyncio.run(main())