#!/usr/bin/env python3
"""Classify one repaired yearly catalog into a year-specific processed CSV."""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GILLIGAN = ("gilligan's island", "gilligans island", "gilligans-island", "alan hale", "alan-hale", "bob denver", "bob-denver", "natalie schafer", "natalie-schafer", "jim backus", "jim-backus", "tina louise", "tina-louise", "russell johnson", "russell-johnson", "dawn wells", "dawn-wells")
SUBJECTS = [("Batman", ("batman", "bruce wayne")), ("Breaking Bad", ("breaking bad", "better call saul")), ("Star Wars", ("star wars", "star-wars", "mandalorian", "ahsoka")), ("Marvel", ("marvel", "mcu", "avengers", "spider-man", "spiderman", "x-men", "deadpool")), ("DC", ("dc comics", "superman", "wonder woman", "joker")), ("Star Trek", ("star trek", "star-trek")), ("James Bond", ("james bond", "007", "james-bond")), ("Horror", ("horror", "slasher", "scariest", "haunted")), ("Science Fiction", ("sci-fi", "science fiction", "sci fi")), ("Western", ("western", "westerns")), ("Animation", ("animated", "animation", "pixar", "dreamworks"))]


def classify(row):
    hay = f"{row['title']} {row['url']}".lower()
    if any(term in hay for term in GILLIGAN):
        for person in ("Alan Hale Jr.", "Bob Denver", "Russell Johnson", "Jim Backus", "Natalie Schafer", "Tina Louise", "Dawn Wells"):
            if person.lower() in hay or person.lower().replace(" ", "-") in hay:
                return person, "yes", "Gilligan-related; manual review required"
        return "Gilligan's Island", "yes", "Gilligan-related; manual review required"
    for subject, terms in SUBJECTS:
        if any(term in hay for term in terms):
            return subject, "no", "Heuristic subject; review if used for comparison"
    return "", "no", "Subject requires review"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    args = parser.parse_args()
    source = ROOT / "data" / f"catalog_titled_{args.year}.csv"
    output = ROOT / "data" / f"catalog_processed_{args.year}.csv"
    review = ROOT / "data" / f"gilligan_review_{args.year}.csv"
    with source.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    for row in rows:
        row["subject"], row["gilligan_related"], row["notes"] = classify(row)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    positives = [row for row in rows if row["gilligan_related"] == "yes"]
    with review.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(positives)
    print(f"Processed {len(rows)} rows; {len(positives)} Gilligan candidates")


if __name__ == "__main__":
    main()
