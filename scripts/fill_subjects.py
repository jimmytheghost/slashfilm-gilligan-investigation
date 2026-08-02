#!/usr/bin/env python3
"""Fill primary subjects from SlashFilm headlines and URLs for the yearly catalogs."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Canonical subject names. More-specific entries must come before broad entries.
KNOWN = [
    ("Gilligan's Island", ["gilligan's island", "gilligans island"]),
    ("A Knight of the Seven Kingdoms", ["knight of the seven kingdoms"]),
    ("House of the Dragon", ["house of the dragon"]),
    ("Game of Thrones", ["game of thrones", "westeros"]),
    ("Stranger Things", ["stranger things"]), ("Fallout", ["fallout"]),
    ("The Pitt", ["the pitt"]), ("Landman", ["landman"]),
    ("Avatar", ["avatar"]), ("The Lord of the Rings", ["lord of the rings", "middle-earth"]),
    ("Harry Potter", ["harry potter", "hogwarts", "draco malfoy"]),
    ("Star Wars", ["star wars", "andor", "mandalorian", "ahsoka", "darth vader"]),
    ("Star Trek", ["star trek"]), ("Marvel", ["marvel", "avengers"]),
    ("Spider-Man", ["spider-man", "spiderman", "spider-noir"]),
    ("Batman", ["batman", "dark knight", "bruce wayne"]),
    ("Superman", ["superman", "clark kent"]), ("Supergirl", ["supergirl"]),
    ("Daredevil", ["daredevil"]), ("Wonder Man", ["wonder man"]),
    ("DC", ["dc universe", "dc comics", "james gunn"]),
    ("The Simpsons", ["the simpsons", "simpsons"]),
    ("The Witcher", ["the witcher"]), ("One Piece", ["one piece"]),
    ("Dragon Ball", ["dragon ball"]), ("Pokémon", ["pokémon", "pokemon"]),
    ("God of War", ["god of war"]), ("The Last of Us", ["the last of us"]),
    ("Jurassic Park", ["jurassic park", "jurassic world"]),
    ("Fast & Furious", ["fast and furious"]), ("28 Years Later", ["28 years later"]),
    ("The Conjuring", ["the conjuring"]), ("Scream", ["scream"]),
    ("Silent Hill", ["silent hill"]), ("M3GAN", ["m3gan"]),
    ("The Beatles", ["the beatles"]), ("KPop Demon Hunters", ["kpop demon hunters"]),
    ("Heated Rivalry", ["heated rivalry"]), ("Tell Me Lies", ["tell me lies"]),
    ("The Housemaid", ["the housemaid"]), ("Pluribus", ["pluribus"]),
    ("Foundation", ["foundation"]), ("Monarch: Legacy of Monsters", ["monarch"]),
    ("Yellowstone", ["yellowstone"]), ("Peaky Blinders", ["peaky blinders"]),
    ("The Rip", ["the rip"]), ("Task", ["task season", "task "]),
    ("Wuthering Heights", ["wuthering heights"]), ("Marty Supreme", ["marty supreme"]),
    ("The Moment", ["the moment"]), ("Project Hail Mary", ["project hail mary"]),
    ("The Super Mario Bros. Movie", ["super mario"]), ("Zootopia", ["zootopia"]),
    ("Toy Story", ["toy story"]), ("The Muppets", ["muppet"]),
    ("The Twilight Zone", ["twilight zone"]), ("The Office", ["the office"]),
    ("The Love Boat", ["love boat"]), ("The Flash", ["the flash"]),
    ("The Godfather", ["the godfather"]), ("The Godfather Part III", ["godfather part iii"]),
    ("The Shawshank Redemption", ["shawshank redemption"]),
    ("The Breakfast Club", ["breakfast club"]), ("The Wizard of Oz", ["wizard of oz"]),
    ("The Princess Bride", ["princess bride"]), ("The Thing", ["the thing"]),
    ("The Pitt", ["dr. robby"]), ("The Orville", ["the orville"]),
    ("NCIS", ["ncis"]), ("CSI", ["csi"]), ("SNL", ["snl", "saturday night live"]),
    ("Oscars", ["oscar", "academy award"]), ("Box Office", ["box office"]),
]

GENERIC_PREFIX = re.compile(r"^(?:Why|How|What|Who|Where|When|Is|Did|Does|Can|Could|Should|Will|Here'?s|The Real Reason|Everything|All|Every|Best|Worst|Top|\d+)[,:]?\s+", re.I)
BREAK = re.compile(r"\s+(?:Season|Episode|Series|Movie|Film|Trailer|Review|Cast|Ending|Finale|Premiere|Star|Director|Creator|Writer|Actor|Actress|Author|Fans|Box Office|Streaming|Is|Was|Will|Has|Had|Gets|Brings|Returns|Explained|Ranks|Ranked|Guide|Release)\b", re.I)


def infer_subject(title, url):
    haystack = f"{title} {url}".lower()
    for canonical, terms in KNOWN:
        if any(term in haystack for term in terms):
            return canonical, "Headline classification."
    cleaned = re.sub(r"\s+-\s+SlashFilm$", "", title, flags=re.I).strip()
    cleaned = GENERIC_PREFIX.sub("", cleaned)
    # Headlines such as "Task Season 2 ..." and "The Simpsons Cast ...".
    match = BREAK.search(cleaned)
    if match and match.start() >= 3:
        candidate = cleaned[:match.start()].strip(" :,-")
        if 2 <= len(candidate) <= 70:
            return candidate, "Headline-derived primary subject; review if needed."
    # Person-led stories are still usefully grouped by their named lead.
    possessive = re.match(r"^([A-Z][A-Za-z.'’\-]+(?:\s+[A-Z][A-Za-z.'’\-]+){0,3})['’]s\b", cleaned)
    if possessive:
        return possessive.group(1), "Headline-derived primary subject; review if needed."
    # Do not leave blanks: retain a concise, auditable headline fallback.
    return cleaned[:120].strip(), "Headline fallback subject; review if needed."


def main():
    for year in (2024, 2025, 2026):
        path = ROOT / "data" / f"catalog_processed_{year}.csv"
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        fields = list(rows[0])
        filled = 0
        for row in rows:
            if not row["subject"] and row["gilligan_related"] == "no":
                row["subject"], row["notes"] = infer_subject(row["title"], row["url"])
                filled += 1
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        review = ROOT / "data" / f"subject_review_{year}.csv"
        unresolved = [row for row in rows if not row["subject"] and row["gilligan_related"] == "no"]
        with review.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(unresolved)
        print(f"{year}: filled {filled}; unresolved {len(unresolved)}")


if __name__ == "__main__":
    main()
