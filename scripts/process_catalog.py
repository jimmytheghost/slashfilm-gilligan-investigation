#!/usr/bin/env python3
"""Create a normalized working catalog without altering the collected source data."""

import csv
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "catalog.csv"
OUTPUT = ROOT / "data" / "catalog_processed.csv"
EASTERN = ZoneInfo("America/New_York")

GILLIGAN_TERMS = (
    "gilligan's island", "gilligans island", "gilligans-island", "alan hale",
    "alan-hale", "bob denver", "bob-denver", "natalie schafer", "natalie-schafer",
    "jim backus", "jim-backus", "tina louise", "tina-louise", "russell johnson",
    "russell-johnson", "dawn wells", "dawn-wells",
)

SUBJECTS = [
    ("Batman", ("batman", "bruce wayne")),
    ("Breaking Bad", ("breaking bad", "better call saul", "vince gilligan")),
    ("Star Wars", ("star wars", "star-wars", "mandalorian", "ahsoka", "luke skywalker")),
    ("Marvel", ("marvel", "mcu", "avengers", "spider-man", "spiderman", "x-men", "deadpool")),
    ("DC", ("dc comics", "dceu", "superman", "wonder woman", "joker")),
    ("Star Trek", ("star trek", "star-trek")),
    ("James Bond", ("james bond", "007", "james-bond")),
    ("Horror Films", ("horror", "slasher", "scariest", "ghost", "haunted")),
    ("Science Fiction", ("sci-fi", "science fiction", "sci fi", "alien", "dystopian")),
    ("Western Films", ("western", "westerns")),
    ("Animated Films", ("animated", "animation", "pixar", "dreamworks")),
    ("Streaming TV", ("netflix", "hbo", "apple tv", "prime video", "disney+", "hulu")),
]


def eastern_timestamp(value):
    try:
        return datetime.fromisoformat(value).astimezone(EASTERN).isoformat()
    except (TypeError, ValueError):
        return value


def classify(row):
    haystack = f"{row['title']} {row['url']}".lower()
    is_gilligan = any(term in haystack for term in GILLIGAN_TERMS)
    if is_gilligan:
        if "alan" in haystack:
            subject = "Alan Hale Jr."
        elif "bob denver" in haystack:
            subject = "Bob Denver"
        elif "russell johnson" in haystack:
            subject = "Russell Johnson"
        elif "jim backus" in haystack:
            subject = "Jim Backus"
        elif "natalie schafer" in haystack:
            subject = "Natalie Schafer"
        elif "tina louise" in haystack:
            subject = "Tina Louise"
        elif "dawn wells" in haystack:
            subject = "Dawn Wells"
        else:
            subject = "Gilligan's Island"
        return subject, "yes", "heuristic; manually verify"
    for subject, terms in SUBJECTS:
        if any(term in haystack for term in terms):
            return subject, "no", "heuristic; review if comparison category matters"
    return "", "no", "subject requires review"


def main():
    with INPUT.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = ["title", "date", "subject", "gilligan_related", "url", "author", "section", "subject_type", "notes"]
    for row in rows:
        row["date"] = eastern_timestamp(row["date"])
        row["subject"], row["gilligan_related"], note = classify(row)
        row["notes"] = note
    rows.sort(key=lambda row: row["date"])
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Processed {len(rows)} rows into {OUTPUT}")


if __name__ == "__main__":
    main()
