#!/usr/bin/env python3
"""Build the reproducible SlashFilm / Gilligan's Island analysis packet."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TMP = ROOT / "tmp" / "pdfs" / "gilligan-report"
OUT = ROOT / "output" / "pdf" / "slashfilm-gilligans-island-coverage-report.pdf"
TABLES = ROOT / "reports" / "gilligan_report_metrics.json"
YEARS = list(range(2020, 2027))
FOCAL_YEARS = [2024, 2025, 2026]

NAVY = "#12313B"
SEA = "#6FC7BE"
CORAL = "#EF6A5B"
SAND = "#F5EACB"
CREAM = "#FFFDF5"
INK = "#14252B"
GOLD = "#E3AD40"
MUTED = "#60747A"

GILLIGAN_CAST = ["Alan Hale Jr.", "Bob Denver", "Russell Johnson", "Tina Louise", "Jim Backus", "Natalie Schafer", "Dawn Wells"]

# Exact title/url aliases used only for specific-show comparisons.
COMPARATORS = {
    "Batman": ["batman", "bruce wayne", "dark knight"],
    "Breaking Bad": ["breaking bad", "better call saul"],
    "The Simpsons": ["the simpsons", "simpsons"],
    "Stranger Things": ["stranger things"],
    "Yellowstone": ["yellowstone"],
    "The Pitt": ["the pitt"],
    "Landman": ["landman"],
    "Harry Potter": ["harry potter", "hogwarts"],
    "Game of Thrones": ["game of thrones", "house of the dragon", "knight of the seven kingdoms"],
    "Star Wars": ["star wars", "andor", "mandalorian", "ahsoka"],
    "Star Trek": ["star trek"],
    "Marvel": ["marvel", "avengers"],
}

CURRENT_TV = {
    "Euphoria": ["euphoria"],
    "Outer Banks": ["outer banks"],
    "Bridgerton": ["bridgerton"],
    "The Last of Us": ["the last of us"],
    "Stranger Things": ["stranger things"],
    "The White Lotus": ["white lotus"],
    "Severance": ["severance"],
    "The Bear": ["the bear"],
    "Shogun": ["shogun", "shōgun"],
    "Hacks": ["hacks"],
    "Baby Reindeer": ["baby reindeer"],
    "The Pitt": ["the pitt"],
    "The Studio": ["the studio"],
    "Adolescence": ["adolescence"],
}


def load_rows(year):
    with (DATA / f"catalog_processed_{year}.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def hits(row, aliases):
    text = f"{row['title']} {row['url']}".lower()
    return any(alias.lower() in text for alias in aliases)


def count_aliases(rows, aliases):
    return sum(hits(row, aliases) for row in rows)


def compute():
    by_year = {year: load_rows(year) for year in YEARS}
    annual = {}
    monthly = Counter()
    cast = Counter()
    direct = {}
    for year, rows in by_year.items():
        gilligan = [row for row in rows if row["gilligan_related"] == "yes"]
        annual[year] = {"articles": len(rows), "expanded": len(gilligan)}
        direct[year] = sum(row["subject"] == "Gilligan's Island" for row in gilligan)
        for row in gilligan:
            monthly[row["date"][:7]] += 1
            cast[row["subject"]] += 1
    focal_rows = [row for year in FOCAL_YEARS for row in by_year[year]]
    property_counts = {name: count_aliases(focal_rows, aliases) for name, aliases in COMPARATORS.items()}
    property_counts["Gilligan universe"] = sum(annual[y]["expanded"] for y in FOCAL_YEARS)
    current_counts = {name: count_aliases(focal_rows, aliases) for name, aliases in CURRENT_TV.items()}
    current_counts["Gilligan universe"] = property_counts["Gilligan universe"]
    ranks = {}
    for year in FOCAL_YEARS:
        subjects = Counter(row["subject"] for row in by_year[year] if row["subject"])
        g_count = annual[year]["expanded"]
        ranks[year] = 1 + sum(count > g_count for count in subjects.values())
    return {
        "annual": annual, "direct": direct, "monthly": dict(sorted(monthly.items())),
        "cast": dict(cast), "properties": property_counts, "current_tv": current_counts,
        "ranks": ranks, "focal_total": len(focal_rows),
    }


def save_chart(fig, name):
    TMP.mkdir(parents=True, exist_ok=True)
    path = TMP / f"{name}.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor=CREAM)
    plt.close(fig)
    return path


def chart_annual(metrics):
    years = YEARS
    values = [metrics["annual"][y]["expanded"] for y in years]
    fig, ax = plt.subplots(figsize=(8.6, 3.5), facecolor=CREAM)
    ax.set_facecolor(CREAM)
    bars = ax.bar(years, values, color=[MUTED if y < 2024 else CORAL for y in years], width=.62)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, value+max(values)*.025, str(value), ha="center", color=INK, weight="bold")
    ax.set_ylim(0, max(values)*1.22); ax.set_ylabel("Gilligan-related stories", color=INK)
    ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="y", alpha=.16)
    ax.tick_params(colors=INK); ax.set_title("The pattern is recent, not six years old", loc="left", color=INK, weight="bold", fontsize=14)
    return save_chart(fig, "annual_gilligan")


def chart_scoreboard(metrics):
    selected = {k:v for k,v in metrics["properties"].items() if k != "Marvel"}
    selected["Marvel"] = metrics["properties"]["Marvel"]
    pairs = sorted(selected.items(), key=lambda x:x[1], reverse=True)
    names, values = zip(*pairs)
    fig, ax = plt.subplots(figsize=(8.6, 5.1), facecolor=CREAM); ax.set_facecolor(CREAM)
    colors = [CORAL if n == "Gilligan universe" else SEA for n in names]
    ax.barh(range(len(names)), values, color=colors)
    ax.set_yticks(range(len(names)), names, color=INK); ax.invert_yaxis()
    for i,v in enumerate(values): ax.text(v+max(values)*.01, i, str(v), va="center", color=INK, weight="bold", fontsize=9)
    ax.spines[["top","right","bottom","left"]].set_visible(False); ax.tick_params(left=False, bottom=False, labelbottom=False)
    ax.set_title("SlashFilm property mentions, 2024-2026", loc="left", color=INK, weight="bold", fontsize=14)
    return save_chart(fig, "franchise_scoreboard")


def chart_monthly(metrics):
    vals = metrics["monthly"]
    months = list(vals); counts = list(vals.values())
    fig, ax = plt.subplots(figsize=(8.6, 3.4), facecolor=CREAM); ax.set_facecolor(CREAM)
    ax.plot(range(len(months)), counts, color=CORAL, linewidth=2.8, marker="o", markersize=4)
    tick_indices = [i for i,m in enumerate(months) if m.endswith("-01") or m.endswith("-07") or i==len(months)-1]
    ax.set_xticks(tick_indices, [months[i] for i in tick_indices], rotation=0)
    ax.set_ylim(0, max(counts)*1.2); ax.grid(axis="y", alpha=.16); ax.spines[["top","right","left"]].set_visible(False)
    ax.tick_params(colors=INK); ax.set_ylabel("Stories", color=INK)
    ax.set_title("Gilligan coverage arrives in clusters, not as a one-day fluke", loc="left", color=INK, weight="bold", fontsize=14)
    return save_chart(fig, "monthly_gilligan")


def chart_cast(metrics):
    cast = metrics["cast"]
    order = ["Gilligan's Island"] + GILLIGAN_CAST
    names = [name for name in order if cast.get(name, 0)]
    values = [cast[name] for name in names]
    fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor=CREAM); ax.set_facecolor(CREAM)
    colors = [CORAL] + [GOLD, SEA, "#89A7B0", "#BA8C78", "#8DB36F", "#9873A5", "#6B9EA4"]
    bars=ax.bar(names, values, color=colors[:len(names)])
    for b,v in zip(bars,values): ax.text(b.get_x()+b.get_width()/2,v+2,str(v),ha="center",weight="bold",color=INK)
    ax.set_ylim(0,max(values)*1.25); ax.spines[["top","right","left"]].set_visible(False); ax.grid(axis="y",alpha=.16)
    ax.tick_params(colors=INK); ax.set_ylabel("Stories", color=INK); ax.tick_params(axis="x", rotation=20)
    ax.set_title("It is not only the island: SlashFilm repeatedly returns to the cast", loc="left", color=INK, weight="bold", fontsize=14)
    return save_chart(fig, "cast_breakdown")


def chart_current_tv(metrics):
    pairs=sorted(metrics["current_tv"].items(),key=lambda x:x[1],reverse=True)
    names,values=zip(*pairs)
    fig,ax=plt.subplots(figsize=(8.6,5.1),facecolor=CREAM); ax.set_facecolor(CREAM)
    colors=[CORAL if n=="Gilligan universe" else "#6FC7BE" for n in names]
    ax.barh(range(len(names)),values,color=colors); ax.set_yticks(range(len(names)),names,color=INK); ax.invert_yaxis()
    for i,v in enumerate(values): ax.text(v+max(values)*.01,i,str(v),va="center",color=INK,weight="bold",fontsize=9)
    ax.spines[["top","right","bottom","left"]].set_visible(False);ax.tick_params(left=False,bottom=False,labelbottom=False)
    ax.set_title("Gilligan versus recent prestige and popular TV",loc="left",color=INK,weight="bold",fontsize=14)
    return save_chart(fig,"current_tv")


def styles():
    base=getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle("kicker", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10, textColor=HexColor(CORAL), spaceAfter=7, uppercase=True),
        "h1": ParagraphStyle("h1", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=28, leading=31, textColor=HexColor(NAVY), spaceAfter=12),
        "h2": ParagraphStyle("h2", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=HexColor(NAVY), spaceBefore=3, spaceAfter=8),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=10.2, leading=14.2, textColor=HexColor(INK), spaceAfter=8),
        "small": ParagraphStyle("small", parent=base["Normal"], fontName="Helvetica", fontSize=8.1, leading=10.5, textColor=HexColor(MUTED), spaceAfter=5),
        "callout": ParagraphStyle("callout", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=HexColor(NAVY), backColor=HexColor(SAND), borderPadding=12, spaceAfter=12),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        # Original, simple island emblem: sun, palm, island, and water.
        canvas.setFillColor(HexColor(CORAL)); canvas.circle(6.98*inch, 8.88*inch, .45*inch, stroke=0, fill=1)
        canvas.setFillColor(HexColor(SAND)); canvas.ellipse(6.15*inch, 8.02*inch, 7.85*inch, 8.34*inch, stroke=0, fill=1)
        canvas.setStrokeColor(HexColor(NAVY)); canvas.setLineWidth(3)
        canvas.line(6.95*inch, 8.13*inch, 7.12*inch, 8.70*inch)
        canvas.setLineWidth(2)
        for dx, dy in [(-.23,.10), (-.15,.22), (.16,.19), (.24,.06)]:
            canvas.line(7.11*inch, 8.67*inch, (7.11+dx)*inch, (8.67+dy)*inch)
        canvas.setStrokeColor(HexColor(SEA)); canvas.setLineWidth(2)
        for y in [7.78, 7.65, 7.52]:
            canvas.arc(6.12*inch, y*inch, 7.88*inch, (y+.20)*inch, 200, 135)
    if doc.page > 1:
        canvas.setStrokeColor(HexColor(SEA)); canvas.setLineWidth(1.2); canvas.line(.58*inch, .48*inch, 7.92*inch, .48*inch)
        canvas.setFont("Helvetica-Bold", 7.5); canvas.setFillColor(HexColor(NAVY)); canvas.drawString(.62*inch, .30*inch, "SLASHFILM COVERAGE PATTERN INVESTIGATION")
        canvas.drawRightString(7.88*inch, .30*inch, f"PAGE {doc.page}")
    canvas.restoreState()


def p(text, style): return Paragraph(text, style)


def report(metrics, charts):
    OUT.parent.mkdir(parents=True, exist_ok=True); TABLES.parent.mkdir(parents=True, exist_ok=True)
    TABLES.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    doc=SimpleDocTemplate(str(OUT),pagesize=letter,rightMargin=.63*inch,leftMargin=.63*inch,topMargin=.62*inch,bottomMargin=.65*inch)
    s=styles(); story=[]
    expanded=sum(metrics['annual'][y]['expanded'] for y in FOCAL_YEARS)
    direct=sum(metrics['direct'][y] for y in FOCAL_YEARS)
    focal_total=metrics['focal_total']
    shares=expanded/focal_total*100
    top_current=sorted(metrics['current_tv'].items(),key=lambda x:x[1],reverse=True)[:5]
    
    # Cover
    story += [Spacer(1,.5*inch), p("A DATA INVESTIGATION",s['kicker']), p("Is SlashFilm really obsessed with Gilligan's Island?",s['h1']),
              p("A curiosity-driven audit of 68,000+ SlashFilm stories, built to test a simple question: did a 1960s sitcom genuinely become a recurring modern coverage subject, or did it merely become memorable enough to create a frequency illusion?",s['body']),
              Spacer(1,.15*inch), p("THE SHORT VERSION",s['kicker']), p(f"<b>{expanded} Gilligan-related stories</b> appeared from 2024 through Aug. 2, 2026 - {shares:.2f}% of all {focal_total:,} stories in the focal period. The surge is real, recent, and largely driven by 2024-2026 coverage.",s['callout']),
              Spacer(1,.2*inch), p("Prepared from SlashFilm article metadata and headline-level subject classification. August 2026 data is year-to-date.",s['small']), PageBreak()]
    # Framing and method
    story += [p("01 / The question",s['kicker']),p("Pattern or frequency illusion?",s['h2']),
              p("The premise is not that SlashFilm should cover one show instead of another. It is a narrower question: does Gilligan's Island appear often enough in the site's output to qualify as an unusual editorial pattern?",s['body']),
              p("Two measurements keep the test fair. <b>Direct Gilligan's Island</b> means stories centered on the show. <b>Expanded Gilligan universe</b> includes those stories plus articles centered on the seven principal cast members. The expanded count answers the original observation; the direct count prevents cast coverage from being hidden inside a single show label.",s['body']),
              p("The report treats 2024-2026 as the comparison window because those years have the most complete headline-based subject normalization. 2020-2023 appears only as historical context for the Gilligan trend.",s['body']),
              p("Headline classification is intentionally transparent: the title and URL determine the primary subject; ambiguous rows use an auditable headline fallback. Exact aliases, not broad subject buckets, drive the selected-franchise comparisons.",s['small']), PageBreak()]
    # Timeline
    story += [p("02 / Exhibit A",s['kicker']),p("The Gilligan spike is recent",s['h2']),Image(str(charts['annual']),width=7.1*inch,height=2.9*inch),
              p("The six-year time series does not support a steady, background level of Gilligan coverage. It instead shows a sharp emergence in 2024, followed by sustained coverage in 2025 and 2026 year-to-date.",s['body']),
              p("The raw annual counts are: 0 (2020), 2 (2021), 0 (2022), 1 (2023), 110 (2024), 50 (2025), and 44 through Aug. 2, 2026.",s['small']),PageBreak()]
    # Scoreboard
    story += [p("03 / The scoreboard",s['kicker']),p("Gilligan is not Marvel. That is not the point.",s['h2']),Image(str(charts['scoreboard']),width=7.15*inch,height=4.25*inch),
              p("Broad ecosystems such as Marvel, Star Trek, and Star Wars naturally dominate SlashFilm's output. The useful comparison is with individual shows and franchises. In that company, the expanded Gilligan universe is not a trivial tail event.",s['body']),PageBreak()]
    # direct expanded
    table_data=[["Metric","2024","2025","2026 YTD","Focal total"], ["Direct Gilligan's Island",*[metrics['direct'][y] for y in FOCAL_YEARS],direct], ["Expanded Gilligan universe",*[metrics['annual'][y]['expanded'] for y in FOCAL_YEARS],expanded]]
    t=Table(table_data,colWidths=[2.3*inch,1.1*inch,1.1*inch,1.1*inch,1.15*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),('BACKGROUND',(0,2),(-1,2),HexColor(SAND)),('GRID',(0,0),(-1,-1),.35,HexColor('#C4D5D0')),('ALIGN',(1,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [p("04 / Two ways to count it",s['kicker']),p("The island alone, and the island plus its orbit",s['h2']),t,Spacer(1,.18*inch),
              p("The difference between these lines is the story. In 2026, Alan Hale Jr. becomes the largest single Gilligan-related subject, even when the article is about The Love Boat, a Western, or a forgotten movie role. That is why the expanded measure belongs in the report - but it is displayed separately from direct show coverage.",s['body']),PageBreak()]
    # cadence
    story += [p("05 / Cadence",s['kicker']),p("This is recurring coverage, not one nostalgia package",s['h2']),Image(str(charts['monthly']),width=7.15*inch,height=2.85*inch),
              p("The monthly series shows repeated coverage across many months rather than a single anniversary or reboot event. The 2024 surge is particularly concentrated from July through December; 2026 reaches 15 stories in June alone.",s['body']),PageBreak()]
    # cast
    story += [p("06 / Who is actually being covered?",s['kicker']),p("Gilligan is a show, but the cast is the engine",s['h2']),Image(str(charts['cast']),width=7.15*inch,height=3.05*inch),
              p("The direct-show label is the biggest single bucket, but cast-member articles turn the property into a much wider content reservoir. The report keeps those two forms of coverage visible rather than treating them as interchangeable.",s['body']),PageBreak()]
    # Current TV
    story += [p("07 / The control group",s['kicker']),p("Where are the big current shows?",s['h2']),Image(str(charts['current_tv']),width=7.15*inch,height=4.25*inch),
              p("This chart compares Gilligan with a deliberately mixed group of award-recognized and culturally visible recent TV. It is not a measure of popularity; it measures SlashFilm article frequency. That distinction matters: coverage volume reflects editorial and search strategy, not audience quality or cultural worth.",s['body']),
              p("The control group includes 2024 Emmy winners such as <i>Shogun</i>, <i>Hacks</i>, and <i>Baby Reindeer</i>, plus 2025 winners <i>The Pitt</i>, <i>The Studio</i>, and <i>Adolescence</i>. Popular-series controls include <i>Euphoria</i>, <i>Outer Banks</i>, <i>Bridgerton</i>, <i>The Last of Us</i>, <i>Stranger Things</i>, <i>The White Lotus</i>, <i>Severance</i>, and <i>The Bear</i>.",s['small']),PageBreak()]
    # Findngs
    story += [p("08 / Verdict",s['kicker']),p("So: did you notice a real pattern?",s['h2']),
              p("<b>Yes, with an asterisk.</b> The data does not show that Gilligan's Island is one of SlashFilm's largest overall content ecosystems. It does show that Gilligan-related coverage became a surprisingly persistent legacy-TV pattern after 2023, large enough to be visible beside contemporary and award-winning television properties.",s['body']),
              p("The frequency-illusion explanation is not enough on its own. A memorable topic can stand out, but it cannot create 110 Gilligan-related stories in a single year. The better interpretation is that a real coverage pattern exists, and its unusualness comes from the age and apparent cultural distance of the property rather than from it defeating every modern franchise.",s['callout']),
              p("This packet does not attempt to explain why SlashFilm publishes these stories or infer traffic performance. It documents frequency, timing, and comparability - no more, no less.",s['body']),PageBreak()]
    # Appendix
    story += [p("09 / Notes on method",s['kicker']),p("How to read the evidence",s['h2']),
              p("Source: SlashFilm article pages indexed through the site's XML sitemaps and collected into year-specific CSVs. The catalog includes title, publication time, URL, primary subject, and Gilligan-related flag. The analysis includes 68,398 total articles from 2020 through Aug. 2, 2026.",s['body']),
              p("Selected-property counts use transparent title/URL aliases. This avoids treating platform names such as HBO, Netflix, or streaming as subjects. It also means the comparison is reproducible, but not a claim that every possible mention in body text has been counted.",s['body']),
              p("External context references: Television Academy, 2024 and 2025 Emmy Awards nominees and winners; Nielsen annual streaming rankings/ARTEY awards. These sources select the current-TV control group; the coverage counts themselves come from SlashFilm.",s['body']),
              p("Limitations: 2020-2023 have less complete subject normalization, so they are used only for the historical Gilligan trend. 2026 is a partial year. Article frequency measures editorial output, not clicks, cultural importance, or audience size.",s['body']),
              Spacer(1,.18*inch),p("The data has spoken. It brought a coconut radio.",s['callout'])]
    doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)


def main():
    metrics=compute()
    charts={"annual":chart_annual(metrics),"scoreboard":chart_scoreboard(metrics),"monthly":chart_monthly(metrics),"cast":chart_cast(metrics),"current_tv":chart_current_tv(metrics)}
    report(metrics,charts)
    print(OUT)


if __name__ == "__main__":
    main()
