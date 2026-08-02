#!/usr/bin/env python3
"""Repair blank/fragmentary titles from article H1 and document-title metadata."""

import csv
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "catalog.csv"
OUTPUT = ROOT / "data" / "catalog_titled.csv"


def fetch_title(row):
    try:
        req = Request(row["url"], headers={"User-Agent": "slashfilm-gilligan-investigation/0.1"})
        page = urlopen(req, timeout=30).read().decode("utf-8", "replace")
        patterns = [r'<h1[^>]*class="[^"]*title-gallery[^"]*"[^>]*>(.*?)</h1>', r'<h1[^>]*>(.*?)</h1>', r'<title>(.*?)</title>']
        for pattern in patterns:
            match = re.search(pattern, page, re.I | re.S)
            if match:
                value = re.sub(r"<[^>]+>", "", match.group(1))
                value = html.unescape(re.sub(r"\s+", " ", value)).strip()
                value = re.sub(r"\s+-\s+SlashFilm$", "", value, flags=re.I)
                if value:
                    row["title"] = value
                    row["notes"] = "Title repaired from article metadata; subject still requires review."
                    break
    except Exception:
        pass
    return row


def main():
    with INPUT.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    targets = [row for row in rows if not row["title"] or len(row["title"]) < 60]
    print(f"Repairing {len(targets)} titles.")
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(fetch_title, row) for row in targets]
        for future in as_completed(futures):
            future.result()
    fields = list(rows[0])
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
