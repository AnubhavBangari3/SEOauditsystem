import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 SEOAuditBot/1.0 "
        "(compatible; AsyncSEOAuditSystem)"
    )
}


def scrape_seo_data(url: str) -> dict:
    """
    Fetch webpage and extract SEO data.

    Returns:
    {
        title,
        meta_description,
        h1_count,
        word_count
    }
    """

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    title = ""

    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_description = ""

    meta_tag = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta_tag:
        meta_description = meta_tag.get(
            "content",
            ""
        ).strip()

    h1_count = len(
        soup.find_all("h1")
    )

    text_content = soup.get_text(
        separator=" ",
        strip=True
    )

    word_count = len(
        text_content.split()
    )

    logger.info(
        "Scraped SEO data successfully for url=%s",
        url
    )

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_count": h1_count,
        "word_count": word_count,
    }


def calculate_seo_score(
    title: str,
    meta_description: str,
    h1_count: int,
    word_count: int,
) -> int:
    """
    Mock SEO scoring logic.

    Score breakdown:
    - Title exists: 25
    - Meta description exists: 25
    - At least one H1 exists: 20
    - Word count:
        >= 300 words: 30
        >= 100 words: 15
        < 100 words: 0

    Max score = 100
    """

    score = 0

    if title and title.strip():
        score += 25

    if meta_description and meta_description.strip():
        score += 25

    if h1_count >= 1:
        score += 20

    if word_count >= 300:
        score += 30
    elif word_count >= 100:
        score += 15

    return min(max(score, 0), 100)