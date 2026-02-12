"""
Fetch article URLs and extract their content as Markdown.

Routes each URL to a source-specific handler based on domain.
Handlers that need special fetching (consent walls, sessions, etc.)
are self-contained. Everything else goes through the default handler.

To add a new source: write a handle_<source>(url) function,
add its domain to SOURCE_ROUTES.
"""

import threading

from curl_cffi import requests as curl_requests
from readability import Document
from bs4 import BeautifulSoup
import html2text
import re

MAX_ARTICLE_LENGTH = 15000  # characters

PAYWALLED_DOMAINS = [
    "wsj.com",
    "ft.com",
    "bloomberg.com",
    "barrons.com",
    "economist.com",
    "seekingalpha.com",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_h2t():
    """Create a fresh HTML2Text converter (not thread-safe, so one per call)."""
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = True
    h2t.ignore_emphasis = False
    h2t.body_width = 0  # no wrapping
    return h2t


def clean_markdown(md):
    """Normalize whitespace and truncate."""
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r" {2,}", " ", md)
    return md.strip()[:MAX_ARTICLE_LENGTH]


def html_to_markdown(html_fragment):
    """Convert an HTML fragment to clean Markdown."""
    md = _make_h2t().handle(html_fragment)
    return clean_markdown(md) if len(md.strip()) >= 50 else None


def extract_with_readability(html):
    """Use readability to isolate article HTML, then convert to Markdown."""
    try:
        doc = Document(html)
        article_html = doc.summary()
        return html_to_markdown(article_html)
    except Exception:
        return None


def extract_with_beautifulsoup(html):
    """Fallback: strip boilerplate, find article container, convert to Markdown."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                   "aside", "iframe", "noscript", "form"]):
            tag.decompose()

        article_el = (
            soup.find("article")
            or soup.find("div", class_=re.compile(r"article|post|entry|content|story", re.I))
            or soup.find("main")
        )
        target = article_el or soup.body
        if target is None:
            return None

        return html_to_markdown(str(target))
    except Exception:
        return None


def parse_generic(html):
    """Try readability first, then beautifulsoup."""
    return extract_with_readability(html) or extract_with_beautifulsoup(html)


def fetch_html(url, timeout=30):
    """Simple GET with Chrome TLS impersonation."""
    try:
        resp = curl_requests.get(url, timeout=timeout, impersonate="chrome",
                                 allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source handlers - each takes a URL, returns extracted Markdown or None
# ---------------------------------------------------------------------------

# Thread-local Yahoo session so concurrent threads each get their own.
_yahoo_local = threading.local()


def handle_yahoo(url):
    """
    Yahoo redirects to guce.yahoo.com/consent on first visit.
    We accept the consent form via POST, which sets cookies in the session.
    Subsequent Yahoo URLs in the same thread reuse the session.
    """
    if not hasattr(_yahoo_local, "session") or _yahoo_local.session is None:
        _yahoo_local.session = curl_requests.Session(impersonate="chrome")

    session = _yahoo_local.session

    try:
        resp = session.get(url, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return None

        # If consent wall appeared, accept it
        if "consent-page" in resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            csrf = soup.find("input", {"name": "csrfToken"})
            sid = soup.find("input", {"name": "sessionId"})
            if not csrf or not sid:
                return None

            resp = session.post(
                resp.url,  # guce.yahoo.com/consent?...
                data={"csrfToken": csrf["value"], "sessionId": sid["value"],
                      "agree": "agree"},
                timeout=30,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                return None

        html = resp.text
    except Exception:
        return None

    # Check for "Continue Reading" link - Yahoo sometimes only shows
    # the first paragraph and links out to the original source article.
    soup = BeautifulSoup(html, "html.parser")
    continue_link = soup.select_one("a.continue-reading-button")
    if continue_link and continue_link.get("href"):
        source_url = continue_link["href"]
        # Follow the link and extract from the actual source
        if not any(d in source_url for d in PAYWALLED_DOMAINS):
            source_text = handle_default(source_url)
            if source_text:
                return source_text

    # Yahoo-specific selectors first, then generic fallback
    return parse_yahoo(html) or parse_generic(html)


def parse_yahoo(html):
    """Extract Markdown from Yahoo Finance article containers."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        article_el = (
            soup.select_one("div.bodyItems-wrapper")
            or soup.select_one("div.caas-body-content")
            or soup.select_one("div.body-wrap")
        )
        if not article_el:
            return None

        for tag in article_el.find_all(["script", "style", "aside", "iframe",
                                         "noscript", "form"]):
            tag.decompose()

        return html_to_markdown(str(article_el))
    except Exception:
        return None


def handle_finviz(url):
    """Finviz blog/news articles store text in div.text-justify."""
    html = fetch_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    article_el = soup.select_one("div.text-justify")
    if article_el:
        md = html_to_markdown(str(article_el))
        if md:
            return md
    return parse_generic(html)


def handle_default(url):
    """Generic handler: simple GET + readability/beautifulsoup parse chain."""
    html = fetch_html(url)
    if not html:
        return None
    return parse_generic(html)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

# domain substring -> handler function
# First match wins. Anything not listed goes to handle_default.
SOURCE_ROUTES = {
    "yahoo.com": handle_yahoo,
    "finviz.com": handle_finviz,
}


def extract_article_text(url):
    """
    Main entry point. Routes URL to the right handler based on domain.
    Returns extracted Markdown string, or None if paywalled/unfetchable.
    """
    if any(d in url for d in PAYWALLED_DOMAINS):
        return None

    for domain, handler in SOURCE_ROUTES.items():
        if domain in url:
            return handler(url)

    return handle_default(url)
