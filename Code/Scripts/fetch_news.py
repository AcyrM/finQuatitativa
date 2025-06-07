import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

def google_news_search_with_date(brand, start_date, end_date, max_pages=2, delay=2):
    query = f"{brand} after:{start_date} before:{end_date}"
    base_url = "https://www.google.com/search"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    all_articles = []

    for page in range(max_pages):
        params = {
            "q": query,
            "tbm": "nws",
            "start": page * 10
        }

        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: status code {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.dbsr")

        if not results:
            print(" more results.")
            break

        for result in results:
            link = result.a["href"]
            title = result.select_one("div.JheGif.nDgy9d").text
            source = result.select_one("div.CEMjEf span.xQ82C.e8fRJf")
            time_tag = result.select_one("span.WG9SHc span")

            all_articles.append({
                "title": title,
                "link": link,
                "source": source.text if source else ne,
                "time": time_tag.text if time_tag else ne
            })

        time.sleep(delay)

    return all_articles

# === Example ===
if __name__ == "__main__":
    articles = google_news_search_with_date("Eletrobras", "2020-01-01", "2020-12-31")
    for art in articles:
        print(f"{art['time'] or 'N/A'} - {art['title']}")
        print(f"{art['link']} ({art['source']})\n")
        