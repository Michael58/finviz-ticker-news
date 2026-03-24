"""
Apify Actor entry point.

Reads input (tickers, maxArticles, daysBack, scrapeFullText),
scrapes Finviz news for each ticker, extracts full article text
concurrently, and pushes results to the Apify dataset.
"""

import asyncio
import time

from apify import Actor

from .finviz_scraper import scrape_ticker_news
from .article_extractor import extract_article_text, set_max_article_length

CONCURRENCY = 5


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        # support both "tickers" (single ticker or comma-separated)
        tickers_raw = actor_input.get("tickers", "") or actor_input.get("ticker", "")
        tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]

        max_articles = actor_input.get("maxArticles", 50)
        days_back = actor_input.get("daysBack", 7)
        scrape_full_text = actor_input.get("scrapeFullText", True)
        max_article_length = actor_input.get("maxArticleLength", 15000)

        set_max_article_length(max_article_length)

        if not tickers:
            Actor.log.error("No ticker symbols provided. Exiting.")
            await Actor.exit()
            return

        Actor.log.info(
            f"Tickers: {', '.join(tickers)} | "
            f"Max articles/ticker: {max_articles or 'unlimited'} | "
            f"Days back: {days_back or 'all'} | "
            f"Full text: {scrape_full_text}"
        )

        start_time = time.time()
        total_articles = 0
        total_full_text = 0
        sem = asyncio.Semaphore(CONCURRENCY)

        for ticker in tickers:
            Actor.log.info(f"--- Scraping {ticker} ---")

            articles = scrape_ticker_news(ticker, max_articles, days_back)
            Actor.log.info(f"Found {len(articles)} articles for {ticker}")

            if not articles:
                Actor.log.warning(
                    f"No articles found for {ticker}. "
                    f"The ticker may be invalid or have no recent news."
                )
                continue

            if scrape_full_text:
                async def process_article(article, idx, total, _ticker=ticker):
                    async with sem:
                        Actor.log.info(
                            f"[{_ticker} {idx + 1}/{total}] "
                            f"{article['source']} - {article['title'][:60]}"
                        )
                        text = await asyncio.to_thread(
                            extract_article_text, article["url"]
                        )
                        article["fullTextAvailable"] = text is not None
                        article["text"] = text
                        article["wordCount"] = len(text.split()) if text else None
                        await Actor.push_data(article)
                        return text is not None

                results = await asyncio.gather(
                    *[process_article(a, i, len(articles))
                      for i, a in enumerate(articles)]
                )
                full_text_count = sum(1 for r in results if r)
            else:
                full_text_count = 0
                for article in articles:
                    article["fullTextAvailable"] = False
                    article["text"] = None
                    article["wordCount"] = None
                    await Actor.push_data(article)

            total_articles += len(articles)
            total_full_text += full_text_count

        elapsed = round(time.time() - start_time, 1)
        Actor.log.info(
            f"Done in {elapsed}s. {total_articles} articles across "
            f"{len(tickers)} ticker(s), {total_full_text} with full text."
        )


if __name__ == "__main__":
    asyncio.run(main())
