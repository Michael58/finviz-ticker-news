# Finviz Ticker News Scraper

Apify actor that scrapes stock news from [Finviz](https://finviz.com) by ticker symbol. Returns headlines, sources, timestamps, and full article text as clean Markdown.

Published on the Apify platform: [apify.com/michael_b/finviz-ticker-news](https://apify.com/michael_b/finviz-ticker-news)

## How it works

1. Fetches the Finviz news table for each ticker using `curl_cffi` (Chrome TLS impersonation)
2. Parses article metadata (title, source, date, URL)
3. Optionally follows each article link to extract full text as Markdown
4. Source-specific handlers for Yahoo Finance (consent wall bypass), Finviz blog, and a generic readability fallback
5. Skips paywalled sources (WSJ, Bloomberg, FT, Barron's, Economist, SeekingAlpha)

## Run on Apify

The easiest way to use this is through the [Apify platform](https://apify.com/michael_b/finviz-ticker-news). No setup needed.

## Run locally

### Prerequisites

- Python 3.11+

### Setup

```bash
git clone https://github.com/Michael58/finviz-ticker-news.git
cd finviz-ticker-news
pip install -r requirements.txt
```

### Run with Apify CLI

```bash
apify run -i '{"tickers": "AAPL, TSLA", "maxArticles": 10, "daysBack": 7, "scrapeFullText": true}'
```

Results are saved to `storage/datasets/default/`.

### Run without Apify

The scraper and article extractor work standalone:

```python
from src.finviz_scraper import scrape_ticker_news
from src.article_extractor import extract_article_text

articles = scrape_ticker_news("AAPL", max_articles=10, days_back=7)

for article in articles:
    text = extract_article_text(article["url"])
    print(f"{article['source']} - {article['title']}")
    print(text[:200] if text else "(paywalled or unavailable)")
    print()
```

## Project structure

```
src/
  main.py               # Apify Actor entry point
  finviz_scraper.py     # Finviz news table scraper
  article_extractor.py  # Full text extraction with source-specific handlers
.actor/
  actor.json            # Apify actor configuration
  input_schema.json     # Input parameters schema
  README.md             # Apify actor page documentation
```

## Tech stack

- **curl_cffi** - HTTP requests with Chrome TLS fingerprint impersonation
- **BeautifulSoup** - HTML parsing
- **readability-lxml** - Article content extraction
- **html2text** - HTML to Markdown conversion
- **Apify SDK** - Actor framework, dataset storage, scheduling

## License

MIT
