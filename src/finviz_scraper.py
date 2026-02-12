"""
Scrape the Finviz news table for a given stock ticker.
Returns a list of article metadata dicts.
"""

from datetime import datetime, timedelta
from urllib.parse import urlparse
import re

import pytz
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup


FINVIZ_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "referer": "https://finviz.com/news.ashx",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}

EST_TZ = pytz.timezone("US/Eastern")


def fetch_finviz_page(ticker, retries=3):
    """Fetch the Finviz quote page for a ticker. Returns HTML text or None."""
    url = f"https://finviz.com/quote.ashx?t={ticker}&ty=c&p=d&b=1"

    for attempt in range(retries):
        try:
            response = curl_requests.get(
                url, headers=FINVIZ_HEADERS, timeout=60, impersonate="chrome"
            )
            if response.status_code == 200:
                return response.text
        except Exception:
            pass

    return None


def parse_article_datetime(dt_str, last_dt):
    """
    Parse Finviz date strings into a timezone-aware UTC datetime.

    Finviz formats:
      - "Feb-04-26 10:30AM"  full date + time
      - "Today 10:30AM"      today's date + time
      - "10:30AM"            same date as previous row, just time
    """
    now_est = datetime.now(EST_TZ)

    if "Today" in dt_str:
        dt_str = dt_str.replace("Today", now_est.strftime("%b-%d-%y"))

    elif re.match(r"^\d{2}:\d{2}(AM|PM)$", dt_str):
        # time only - inherit date from the previous article row
        if last_dt is None:
            return None
        dt_str = last_dt.astimezone(EST_TZ).strftime("%b-%d-%y") + " " + dt_str

    try:
        naive = datetime.strptime(dt_str, "%b-%d-%y %I:%M%p")
        return EST_TZ.localize(naive).astimezone(pytz.UTC)
    except ValueError:
        return None


def extract_source_domain(url):
    """Extract a readable source domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def scrape_ticker_news(ticker, max_articles=20, days_back=7):
    """
    Scrape Finviz news table for a ticker.

    Returns a list of dicts:
      {ticker, title, url, source, publishedAt}
    """
    html = fetch_finviz_page(ticker)
    if not html:
        return []

    bs = BeautifulSoup(html, "html.parser")
    cutoff_dt = datetime.now(pytz.UTC) - timedelta(days=days_back) if days_back else None

    articles = []
    last_dt = None

    rows = bs.select('table#news-table tr[onclick*="trackAndOpenNews"]')
    if not rows:
        # fallback selector in case finviz changes markup
        rows = bs.select("table#news-table tr")

    for row in rows:
        date_cells = row.select('td[align="right"]')
        if not date_cells:
            continue
        dt_str = date_cells[0].text.strip()

        dt = parse_article_datetime(dt_str, last_dt)
        if dt is None:
            continue
        last_dt = dt

        if cutoff_dt and dt < cutoff_dt:
            break

        link_el = row.select_one("a.tab-link-news")
        if not link_el:
            continue

        article_link = link_el.get("href", "")
        if not article_link.startswith("http"):
            article_link = "https://finviz.com" + article_link

        title = link_el.text.strip()
        source = extract_source_domain(article_link)

        articles.append({
            "ticker": ticker.upper(),
            "title": title,
            "url": article_link,
            "source": source,
            "publishedAt": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

        if max_articles and len(articles) >= max_articles:
            break

    return articles
