#!/usr/bin/env python3
"""Collect SlashFilm 2026 article metadata from the site's XML sitemaps."""

import csv
import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE = "https://www.slashfilm.com"
INDEX = f"{BASE}/sitemap_index.xml"
OUT = Path(__file__).resolve().parents[1] / "data" / "catalog.csv"
GILLIGAN_TERMS = (
    "gilligans-island", "alan-hale", "bob-denver", "natalie-schafer", "jim-backus",
    "tina-louise", "russell-johnson", "dawn-wells", "skipper",
)


def fetch(url):
    request = Request(url, headers={"User-Agent": "slashfilm-gilligan-investigation/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def xml_text(root, suffix):
    for element in root.iter():
        if element.tag.endswith(suffix):
            return (element.text or "").strip()
    return ""


def sitemap_urls():
    root = ET.fromstring(fetch(INDEX))
    return [xml_text(node, "loc") for node in root.iter() if node.tag.endswith("sitemap")]


def articles_from_sitemap(url, target_years):
    root = ET.fromstring(fetch(url))
    rows = []
    for node in root.iter():
        if not node.tag.endswith("url"):
            continue
        article_url = xml_text(node, "loc")
        lastmod = xml_text(node, "lastmod")
        if not article_url or not lastmod:
            continue
        published = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
        if published.year in target_years:
            rows.append((article_url, published.isoformat()))
    return rows


def meta_value(html, key):
    pattern = rf'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)' \
              rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']'
    match = re.search(pattern, html, re.I)
    return unescape(next((value for value in match.groups() if value), "")).strip() if match else ""


def article_row(item):
    url, sitemap_date = item
    try:
        html = fetch(url).decode("utf-8", "replace")
        title = meta_value(html, "og:title") or meta_value(html, "twitter:title")
        published = meta_value(html, "article:published_time") or sitemap_date
        author = meta_value(html, "author")
        slug = url.rstrip("/").rsplit("/", 1)[-1].lower()
        likely = "yes" if any(term in slug for term in GILLIGAN_TERMS) else "review"
        return {
            "title": title,
            "date": published,
            "subject": "",
            "gilligan_related": likely,
            "url": url,
            "author": author,
            "section": "",
            "subject_type": "",
            "notes": "Automated collection; review subject and Gilligan flag manually." if likely == "review" else "Likely Gilligan-related; confirm manually.",
        }
    except Exception as exc:
        return {"title": "", "date": sitemap_date, "subject": "", "gilligan_related": "review", "url": url,
                "author": "", "section": "", "subject_type": "", "notes": f"Fetch error: {exc}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2026])
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    target_years = set(args.years)
    sitemap_list = [url for url in sitemap_urls() if "post-sitemap" in url]
    article_items = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(lambda url: articles_from_sitemap(url, target_years), sitemap_list):
            article_items.extend(result)
    unique = {url: date for url, date in article_items}
    print(f"Found {len(unique)} 2026 sitemap entries.", file=sys.stderr)
    rows = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(article_row, item) for item in unique.items()]
        for index, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if index % 100 == 0:
                print(f"Fetched {index}/{len(futures)} pages.", file=sys.stderr)
    rows.sort(key=lambda row: row["date"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["title", "date", "subject", "gilligan_related", "url", "author", "section", "subject_type", "notes"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
