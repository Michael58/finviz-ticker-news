# Stock News Scraper - Finviz

Get real-time stock and company news for any ticker symbol with **full article text as clean markdown**. Powered by [Finviz](https://finviz.com) data. Built for AI agents, sentiment analysis, and market research.

## **What is Finviz Ticker News Scraper?**

This actor extracts recent stock news from [Finviz](https://finviz.com) for any publicly traded ticker. It returns article headlines, source domains, timestamps, and optionally the **full article text converted to clean markdown**.

Finviz aggregates news from Reuters, Yahoo Finance, CNBC, MarketWatch, Benzinga, and dozens more. This actor gives you structured, API-accessible data from all of them in a single run. No browser needed, no API key required.

## **Why scrape stock news from Finviz?**

Finviz is one of the most popular financial research platforms, but it has **no public API for news data**. This actor solves that by delivering structured JSON with full article text, ready for AI pipelines, trading systems, or market research.

## **How to scrape stock news by ticker**

1. Go to the [Finviz Ticker News](https://apify.com/michael_b/finviz-ticker-news) actor page
2. Enter one or more ticker symbols (e.g. `TSLA, NVDA, AAPL`)
3. Set how many articles and how far back you want
4. Click **Start**
5. Download results as **JSON, CSV, or Excel**, or access via the Apify API

## **Input**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tickers` | string | *(required)* | Comma-separated ticker symbols, e.g. `AAPL, TSLA, MSFT` |
| `maxArticles` | integer | 50 | Max articles per ticker. `0` = no limit |
| `daysBack` | integer | 7 | Articles from the last N days. `0` = all available |
| `scrapeFullText` | boolean | true | Extract full article text as markdown. `false` = metadata only (faster) |

```json
{
    "tickers": "TSLA, NVDA",
    "maxArticles": 30,
    "daysBack": 7,
    "scrapeFullText": true
}
```

## **Output**

```json
{
    "ticker": "TSLA",
    "title": "Tesla Surges on Record Deliveries",
    "url": "https://www.reuters.com/business/autos/tesla-record-deliveries-2025",
    "source": "reuters.com",
    "publishedAt": "2025-02-05T14:30:00Z",
    "fullTextAvailable": true,
    "text": "# Tesla Surges on Record Deliveries\n\nTesla reported record quarterly deliveries of...",
    "wordCount": 847
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker symbol |
| `title` | string | Article headline |
| `url` | string | Original article URL |
| `source` | string | Source domain (e.g. `reuters.com`) |
| `publishedAt` | string | ISO 8601 UTC timestamp |
| `fullTextAvailable` | boolean | Whether full text was extracted |
| `text` | string/null | Article text as markdown, null if paywalled |
| `wordCount` | integer/null | Word count of extracted text |

## **Use cases for stock news data**

| Use Case | Description | Best For |
|----------|-------------|----------|
| **Sentiment analysis** | Process full article text to extract market signals and sentiment scores | Quant traders, analysts |
| **AI agent research** | Feed real-time company news into AI agents via Apify MCP | ChatGPT, Claude, custom agents |
| **LLM context** | Inject recent news into prompts for summarization or Q&A | RAG pipelines, chatbots |
| **Market monitoring** | Track news flow across a portfolio on a daily schedule | Portfolio managers |
| **Trading signals** | Detect breaking news from article frequency and sources | Algorithmic trading |
| **Newsletter automation** | Aggregate daily stock news into automated reports | Financial content creators |
| **Research datasets** | Build historical news datasets for backtesting or ML training | Data scientists |

## **How to scrape stock news with Python**

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")

run = client.actor("michael_b/finviz-ticker-news").call(run_input={
    "tickers": "TSLA, NVDA, AAPL",
    "maxArticles": 20,
    "scrapeFullText": True,
})

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"[{item['ticker']}] {item['source']} — {item['title']}")
```

## **How to scrape stock news with JavaScript**

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: 'YOUR_APIFY_TOKEN' });

const run = await client.actor('michael_b/finviz-ticker-news').call({
    tickers: 'TSLA, NVDA, AAPL',
    maxArticles: 20,
    scrapeFullText: true,
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
items.forEach(item => console.log(`[${item.ticker}] ${item.source} — ${item.title}`));
```

## **How much does it cost to scrape stock news?**

This actor uses raw HTTP requests with no browser, keeping costs minimal. Recommended memory: **512 MB**. Pricing: **$0.001 per article** plus a minimal actor start fee. Full text extraction doesn't cost extra.

| Scenario | Articles | Time | Cost |
|----------|----------|------|------|
| 1 ticker, metadata only | 100 | ~5s | ~$0.10 |
| 1 ticker, full text | 100 | ~30s | ~$0.10 |
| 5 tickers, full text | 500 | ~2 min | ~$0.50 |
| 10 tickers, full text | 1,000 | ~3 min | ~$1.00 |

## **Automate with Apify platform**

- **Schedule runs** daily, hourly, or at market open/close
- **Access results via API** for integration into trading systems
- **Connect to Make, n8n, or Zapier** for no-code workflows
- **Use with AI agents** through Apify's MCP server (Claude, ChatGPT, custom agents)
- **Export** as JSON, CSV, Excel, or stream to your database

## **FAQ**

**Is it legal to scrape news from Finviz?**
This actor only extracts publicly available headlines and visits original article URLs for publicly available content. No private data is accessed or authentication bypassed.

**How often is the data updated?**
Live data from Finviz on every run. Schedule as frequently as you need.

**Which news sources does Finviz aggregate?**
Reuters, Yahoo Finance, CNBC, MarketWatch, Benzinga, Investor's Business Daily, The Motley Fool, and many more.

**Can I use this with ChatGPT, Claude, or other AI agents?**
Yes. Fully compatible with Apify's MCP server. The markdown output is designed for LLM consumption.

**What happens with paywalled articles (WSJ, Bloomberg, FT)?**
Headline and metadata are still returned, but `text` will be `null`. You get the title, source, URL, and date regardless.

**How many articles are available per ticker?**
Finviz stores up to 100 recent articles per ticker. Use `daysBack: 0` to get all available.

**Can I scrape multiple tickers at once?**
Yes. Enter comma-separated tickers like `AAPL, TSLA, MSFT, NVDA` and the actor processes all of them in a single run.

## **Support**

Questions, feature requests, or bugs? Open an issue in the [Issues tab](https://apify.com/michael_b/finviz-ticker-news/issues). Feedback is always welcome.
