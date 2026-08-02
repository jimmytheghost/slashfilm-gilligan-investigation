#!/usr/bin/env python3
"""Build the reproducible SlashFilm / Gilligan's Island analysis packet."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from PIL import Image as PILImage

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

DISPLAY_FONT = "RobotoBlack"
TEXT_FONT = "RobotoSerif"
LABEL_FONT = "RobotoMedium"

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
    property_counts["Gilligan Universe"] = sum(annual[y]["expanded"] for y in FOCAL_YEARS)
    current_counts = {name: count_aliases(focal_rows, aliases) for name, aliases in CURRENT_TV.items()}
    current_counts["Gilligan Universe"] = property_counts["Gilligan Universe"]
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


def register_fonts():
    pdfmetrics.registerFont(TTFont(DISPLAY_FONT, str(ROOT / "assets" / "fonts" / "Roboto-Black.ttf")))
    pdfmetrics.registerFont(TTFont(TEXT_FONT, str(ROOT / "assets" / "fonts" / "RobotoSerif-Regular.ttf")))
    pdfmetrics.registerFont(TTFont(LABEL_FONT, str(ROOT / "assets" / "fonts" / "Roboto-Medium.ttf")))
    for name in ("Roboto-Regular.ttf", "Roboto-Medium.ttf", "Roboto-Black.ttf"):
        font_manager.fontManager.addfont(str(ROOT / "assets" / "fonts" / name))
    plt.rcParams.update({"font.family": "Roboto", "axes.titleweight": "normal"})


def roboto(weight="regular"):
    names = {"regular": "Roboto-Regular.ttf", "medium": "Roboto-Medium.ttf", "black": "Roboto-Black.ttf"}
    return font_manager.FontProperties(fname=str(ROOT / "assets" / "fonts" / names[weight]))


def finish_chart(ax, title, ylabel=None):
    """Give every chart the same deliberate typographic hierarchy."""
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontproperties=roboto("medium"), labelpad=10)
    ax.set_title(title, loc="left", color=INK, fontproperties=roboto("black"), fontsize=14, pad=12)
    for label in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        label.set_fontproperties(roboto("regular"))
        label.set_color(INK)


def chart_annual(metrics):
    years = YEARS
    values = [metrics["annual"][y]["expanded"] for y in years]
    fig, ax = plt.subplots(figsize=(10, 3.51), facecolor=CREAM)
    ax.set_facecolor(CREAM)
    bars = ax.bar(years, values, color=[MUTED if y < 2024 else CORAL for y in years], width=.62)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, value+max(values)*.025, str(value), ha="center", color=INK, fontproperties=roboto("black"))
    ax.set_ylim(0, max(values)*1.22)
    ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="y", alpha=.16)
    ax.tick_params(colors=INK); finish_chart(ax, "The pattern is recent, not six years old", "Gilligan-related stories")
    return save_chart(fig, "annual_gilligan")


def chart_scoreboard(metrics):
    selected = {k:v for k,v in metrics["properties"].items() if k != "Marvel"}
    selected["Marvel"] = metrics["properties"]["Marvel"]
    pairs = sorted(selected.items(), key=lambda x:x[1], reverse=True)
    names, values = zip(*pairs)
    fig, ax = plt.subplots(figsize=(10, 4.77), facecolor=CREAM); ax.set_facecolor(CREAM)
    colors = [CORAL if n == "Gilligan Universe" else SEA for n in names]
    ax.barh(range(len(names)), values, color=colors)
    ax.set_yticks(range(len(names)), names, color=INK); ax.invert_yaxis()
    for i,v in enumerate(values): ax.text(v+max(values)*.01, i, str(v), va="center", color=INK, fontproperties=roboto("black"), fontsize=9)
    ax.spines[["top","right","bottom","left"]].set_visible(False); ax.tick_params(left=False, bottom=False, labelbottom=False)
    finish_chart(ax, "SlashFilm property mentions, 2024-2026")
    return save_chart(fig, "franchise_scoreboard")


def chart_monthly(metrics):
    vals = metrics["monthly"]
    months = list(vals); counts = list(vals.values())
    fig, ax = plt.subplots(figsize=(10, 3.61), facecolor=CREAM); ax.set_facecolor(CREAM)
    ax.plot(range(len(months)), counts, color=CORAL, linewidth=2.8, marker="o", markersize=4)
    # Evenly space four labels; do not let the partial-year endpoint collide with January.
    tick_indices = sorted({round(i * (len(months) - 1) / 3) for i in range(4)})
    ax.set_xticks(tick_indices, [months[i] for i in tick_indices], rotation=0)
    ax.set_ylim(0, max(counts)*1.2); ax.grid(axis="y", alpha=.16); ax.spines[["top","right","left"]].set_visible(False)
    ax.tick_params(colors=INK); finish_chart(ax, "Gilligan coverage arrives in clusters, not as a one-day fluke", "Stories")
    return save_chart(fig, "monthly_gilligan")


def chart_cast(metrics):
    cast = metrics["cast"]
    order = ["Gilligan's Island"] + GILLIGAN_CAST
    names = [name for name in order if cast.get(name, 0)]
    values = [cast[name] for name in names]
    fig, ax = plt.subplots(figsize=(10, 3.93), facecolor=CREAM); ax.set_facecolor(CREAM)
    colors = [CORAL] + [GOLD, SEA, "#89A7B0", "#BA8C78", "#8DB36F", "#9873A5", "#6B9EA4"]
    bars=ax.bar(names, values, color=colors[:len(names)])
    for b,v in zip(bars,values): ax.text(b.get_x()+b.get_width()/2,v+2,str(v),ha="center",color=INK,fontproperties=roboto("black"))
    ax.set_ylim(0,max(values)*1.25); ax.spines[["top","right","left"]].set_visible(False); ax.grid(axis="y",alpha=.16)
    ax.tick_params(colors=INK); ax.tick_params(axis="x", rotation=20)
    finish_chart(ax, "It is not only the island: SlashFilm repeatedly returns to the cast", "Stories")
    return save_chart(fig, "cast_breakdown")


def chart_current_tv(metrics):
    pairs=sorted(metrics["current_tv"].items(),key=lambda x:x[1],reverse=True)
    names,values=zip(*pairs)
    fig,ax=plt.subplots(figsize=(10,4.77),facecolor=CREAM); ax.set_facecolor(CREAM)
    colors=[CORAL if n=="Gilligan Universe" else "#6FC7BE" for n in names]
    ax.barh(range(len(names)),values,color=colors); ax.set_yticks(range(len(names)),names,color=INK); ax.invert_yaxis()
    for i,v in enumerate(values): ax.text(v+max(values)*.01,i,str(v),va="center",color=INK,fontproperties=roboto("black"),fontsize=9)
    ax.spines[["top","right","bottom","left"]].set_visible(False);ax.tick_params(left=False,bottom=False,labelbottom=False)
    finish_chart(ax, "Gilligan versus recent prestige and popular TV")
    return save_chart(fig,"current_tv")


def styles():
    base=getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle("kicker", parent=base["Normal"], fontName=LABEL_FONT, fontSize=10, leading=11, textColor=HexColor(CORAL), spaceAfter=9, uppercase=True, tracking=1.8),
        "h1": ParagraphStyle("h1", parent=base["Normal"], fontName=DISPLAY_FONT, fontSize=34, leading=37, textColor=HexColor(NAVY), spaceAfter=15),
        "h2": ParagraphStyle("h2", parent=base["Normal"], fontName=DISPLAY_FONT, fontSize=23, leading=26, textColor=HexColor(NAVY), spaceBefore=2, spaceAfter=12),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName=TEXT_FONT, fontSize=14, leading=18.5, textColor=HexColor(INK), spaceAfter=11),
        "small": ParagraphStyle("small", parent=base["Normal"], fontName=TEXT_FONT, fontSize=11.5, leading=14.5, textColor=HexColor(MUTED), spaceAfter=7),
        "callout": ParagraphStyle("callout", parent=base["Normal"], fontName=DISPLAY_FONT, fontSize=18, leading=22, textColor=HexColor(NAVY), backColor=HexColor(SAND), borderPadding=18, spaceAfter=14),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(HexColor(NAVY)); canvas.rect(0, 0, 11*inch, 8.5*inch, stroke=0, fill=1)
        canvas.setFillColor(HexColor(CORAL)); canvas.rect(0, 8.12*inch, 11*inch, .38*inch, stroke=0, fill=1)
    if doc.page > 1:
        canvas.setStrokeColor(HexColor(SEA)); canvas.setLineWidth(1.2); canvas.line(.62*inch, .42*inch, 10.38*inch, .42*inch)
        canvas.setFont(LABEL_FONT, 8.5); canvas.setFillColor(HexColor(NAVY)); canvas.drawString(.64*inch, .22*inch, "SLASHFILM COVERAGE PATTERN INVESTIGATION")
        canvas.drawRightString(10.36*inch, .22*inch, f"PAGE {doc.page}")
    canvas.restoreState()


def p(text, style): return Paragraph(text, style)


def chart_image(path, max_width, max_height):
    """Fit rendered charts without ever stretching them."""
    with PILImage.open(path) as image:
        width, height = image.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def chart_card(path, max_width, max_height):
    """A restrained chart frame with an offset, low-contrast shadow."""
    image = chart_image(path, max_width - 12, max_height - 12)
    card = Table([[image]], colWidths=[image.drawWidth + 12], rowHeights=[image.drawHeight + 12])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor(CREAM)),
        ('BOX', (0, 0), (-1, -1), .7, HexColor(SEA)),
        # Bottom and right rules create a soft, intentional paper-shadow edge.
        ('LINEBELOW', (0, 0), (-1, -1), 3, HexColor('#DDE7E3')),
        ('LINEAFTER', (0, 0), (-1, -1), 3, HexColor('#DDE7E3')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return card


def text_card(text, style):
    """Generous internal padding makes narrative evidence feel placed, not floating."""
    card = Table([[Paragraph(text, style)]], colWidths=[9.46 * inch])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F8F4E8')),
        ('BOX', (0, 0), (-1, -1), .45, HexColor('#D7CBA5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return card


def report(metrics, charts):
    OUT.parent.mkdir(parents=True, exist_ok=True); TABLES.parent.mkdir(parents=True, exist_ok=True)
    TABLES.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    doc=SimpleDocTemplate(str(OUT),pagesize=landscape(letter),rightMargin=.78*inch,leftMargin=.78*inch,topMargin=.68*inch,bottomMargin=.66*inch)
    s=styles(); story=[]
    expanded=sum(metrics['annual'][y]['expanded'] for y in FOCAL_YEARS)
    direct=sum(metrics['direct'][y] for y in FOCAL_YEARS)
    focal_total=metrics['focal_total']
    shares=expanded/focal_total*100
    top_current=sorted(metrics['current_tv'].items(),key=lambda x:x[1],reverse=True)[:5]
    
    # Cover
    cover_title=Paragraph("Is SlashFilm really obsessed with<br/>Gilligan's Island?", ParagraphStyle("cover", parent=s['h1'], textColor=HexColor(CREAM), fontSize=43, leading=46, spaceAfter=18))
    cover_body=Paragraph("A curiosity-driven audit of 68,000+ SlashFilm stories,<br/>built to test a simple question: did a 1960s sitcom<br/>genuinely become a recurring modern coverage subject,<br/>or did it merely become memorable enough to create a<br/>frequency illusion?", ParagraphStyle("coverbody", parent=s['body'], textColor=HexColor('#D5E5E0'), fontSize=12.2, leading=17, spaceAfter=16))
    cover_stat=Paragraph(f"<b>{expanded}</b><br/>Gilligan-related stories<br/>from 2024 through Aug. 2, 2026", ParagraphStyle("coverstat", parent=s['h2'], textColor=HexColor(NAVY), backColor=HexColor(SAND), fontSize=23, leading=27, borderPadding=18))
    cover_meta=Paragraph(f"{shares:.2f}% of all {focal_total:,} focal-period stories.\nThe spike is real, recent, and measurable.", ParagraphStyle("covermeta", parent=s['small'], textColor=HexColor('#D5E5E0'), fontSize=10.2, leading=14))
    cover_left = [p("A DATA INVESTIGATION", ParagraphStyle("coverkick", parent=s['kicker'], textColor=HexColor(CORAL))), cover_title, cover_body, cover_meta]
    cover_right = [Spacer(1, 1.15*inch), cover_stat, Spacer(1, .18*inch), p("OBSERVED PATTERN<br/>2024-2026", ParagraphStyle("coverlabel", parent=s['kicker'], textColor=HexColor(SEA), alignment=1))]
    cover_table = Table([[cover_left, cover_right]], colWidths=[6.55*inch,3.15*inch])
    cover_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),.65*inch),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story += [cover_table, Spacer(1,.1*inch), p("Prepared from SlashFilm article metadata and headline-level subject classification. August 2026 data is year-to-date.", ParagraphStyle("coverfoot",parent=s['small'],textColor=HexColor('#AFC9C3'))), PageBreak()]
    # Framing and method
    story += [p("01 / The question",s['kicker']),p("Pattern or frequency illusion?",s['h2']),
              p("The premise is not that SlashFilm should cover one show instead of another. It is a narrower question: does Gilligan's Island appear often enough in the site's output to qualify as an unusual editorial pattern?",s['body']),
              p("Two measurements keep the test fair. <b>Direct Gilligan's Island</b> means stories centered on the show. <b>Expanded Gilligan Universe</b> includes those stories plus articles centered on the seven principal cast members. The expanded count answers the original observation; the direct count prevents cast coverage from being hidden inside a single show label.",s['body']),
              p("The report treats 2024-2026 as the comparison window because those years have the most complete headline-based subject normalization. 2020-2023 appears only as historical context for the Gilligan trend.",s['body']),
              p("Headline classification is intentionally transparent: the title and URL determine the primary subject; ambiguous rows use an auditable headline fallback. Exact aliases, not broad subject buckets, drive the selected-franchise comparisons.",s['small']), Spacer(1,.18*inch)]
    evidence = Table([[p("68,398", ParagraphStyle("metric", parent=s['h2'], fontSize=24, leading=25)), p("21,932", ParagraphStyle("metric2", parent=s['h2'], fontSize=24, leading=25)), p("2024-2026", ParagraphStyle("metric3", parent=s['h2'], fontSize=24, leading=25))],
                      [p("Catalogued stories", s['small']), p("Stories in the focal window", s['small']), p("Primary comparison period", s['small'])]], colWidths=[3.15*inch,3.15*inch,3.15*inch])
    evidence.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#F6F0DF')),('BOX',(0,0),(-1,-1),.4,HexColor('#D7CBA5')),('INNERGRID',(0,0),(-1,-1),.3,HexColor('#D7CBA5')),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    story += [evidence, PageBreak()]
    # Timeline
    story += [p("02 / Exhibit A",s['kicker']),p("The Gilligan spike is recent",s['h2']),chart_card(charts['annual'],9.55*inch,3.35*inch), Spacer(1,.12*inch),
              text_card("The six-year time series does not support a steady, background level of Gilligan coverage. It instead shows a sharp emergence in 2024, followed by sustained coverage in 2025 and 2026 year-to-date.",s['body']),
              p("The raw annual counts are: 0 (2020), 2 (2021), 0 (2022), 1 (2023), 110 (2024), 50 (2025), and 44 through Aug. 2, 2026.",s['small']),PageBreak()]
    # Scoreboard
    story += [p("03 / The scoreboard",s['kicker']),p("Gilligan is not Marvel. That is not the point.",s['h2']),chart_card(charts['scoreboard'],9.55*inch,4.55*inch), Spacer(1,.12*inch),
              text_card("Broad ecosystems such as Marvel, Star Trek, and Star Wars naturally dominate SlashFilm's output. The useful comparison is with individual shows and franchises. In that company, the expanded Gilligan Universe is not a trivial tail event.",s['body']),PageBreak()]
    # direct expanded
    table_data=[["Metric","2024","2025","2026 YTD","Focal total"], ["Direct Gilligan's Island",*[metrics['direct'][y] for y in FOCAL_YEARS],direct], ["Expanded Gilligan Universe",*[metrics['annual'][y]['expanded'] for y in FOCAL_YEARS],expanded]]
    t=Table(table_data,colWidths=[3.4*inch,1.55*inch,1.55*inch,1.55*inch,1.55*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),DISPLAY_FONT),('FONTNAME',(0,1),(0,-1),LABEL_FONT),('FONTNAME',(1,1),(-1,-1),LABEL_FONT),('BACKGROUND',(0,2),(-1,2),HexColor(SAND)),('GRID',(0,0),(-1,-1),.35,HexColor('#C4D5D0')),('ALIGN',(1,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [p("04 / Two ways to count it",s['kicker']),p("The island alone, and the island plus its orbit",s['h2']),t,Spacer(1,.18*inch),
              text_card("The difference between these lines is the story. In 2026, Alan Hale Jr. becomes the largest single Gilligan-related subject, even when the article is about <i>The Love Boat</i>, a Western, or a forgotten movie role. That is why the expanded measure belongs in the report - but it is displayed separately from direct show coverage.",s['body']),Spacer(1,.18*inch)]
    orbit = Table([[p("105", ParagraphStyle("orbitnum", parent=s['h2'], fontSize=27, leading=29, textColor=HexColor(CORAL))), p("99", ParagraphStyle("orbitnum2", parent=s['h2'], fontSize=27, leading=29, textColor=HexColor(CORAL)))],
                   [p("direct-show stories", s['small']), p("cast-led stories added by the expanded measure", s['small'])]], colWidths=[4.7*inch,4.7*inch])
    orbit.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#EDF5F2')),('BOX',(0,0),(-1,-1),.55,HexColor(SEA)),('INNERGRID',(0,0),(-1,-1),.35,HexColor('#B9DDD7')),('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),11)]))
    story += [orbit, PageBreak()]
    # cadence
    story += [p("05 / Cadence",s['kicker']),p("This is recurring coverage, not one nostalgia package",s['h2']),chart_card(charts['monthly'],9.55*inch,3.45*inch), Spacer(1,.12*inch),
              text_card("The monthly series shows repeated coverage across many months rather than a single anniversary or reboot event. The 2024 surge is particularly concentrated from July through December; 2026 reaches 15 stories in June alone.",s['body']),PageBreak()]
    # cast
    story += [p("06 / Who is actually being covered?",s['kicker']),p("Gilligan is a show, but the cast is the engine",s['h2']),chart_card(charts['cast'],9.55*inch,3.75*inch), Spacer(1,.12*inch),
              text_card("The direct-show label is the biggest single bucket, but cast-member articles turn the property into a much wider content reservoir. The report keeps those two forms of coverage visible rather than treating them as interchangeable.",s['body']),PageBreak()]
    # Current TV
    story += [p("07 / The control group",s['kicker']),p("Where are the big current shows?",s['h2']),chart_card(charts['current_tv'],9.55*inch,3.88*inch), Spacer(1,.1*inch),
              text_card("Gilligan Universe is covered more often than every current show here except <i>Stranger Things</i>: <i>The Pitt</i>, <i>Severance</i>, <i>The Last of Us</i>, <i>Euphoria</i>, <i>Outer Banks</i>, and every award-season title. That is not a cultural-ranking claim. It is strong evidence that something unusual is happening in SlashFilm's editorial mix.",s['body']),
              p("The control group includes 2024 Emmy winners such as <i>Shogun</i>, <i>Hacks</i>, and <i>Baby Reindeer</i>, plus 2025 winners <i>The Pitt</i>, <i>The Studio</i>, and <i>Adolescence</i>. Popular-series controls include <i>Euphoria</i>, <i>Outer Banks</i>, <i>Bridgerton</i>, <i>The Last of Us</i>, <i>Stranger Things</i>, <i>The White Lotus</i>, <i>Severance</i>, and <i>The Bear</i>.",s['small']),PageBreak()]
    # Findings
    verdict_metric = Paragraph("<font size=31><b>110</b></font><br/><font size=10>GILLIGAN-RELATED<br/>STORIES IN 2024</font>", ParagraphStyle("verdictmetric", parent=s['small'], fontName=DISPLAY_FONT, textColor=HexColor(CORAL), leading=12))
    verdict_copy = Paragraph("<b>One memorable subject can stick in your head. It cannot produce 110 stories in a single year.</b><br/><br/>That count is the cleanest reason to reject frequency illusion as the whole explanation.", ParagraphStyle("verdictcopy", parent=s['body'], fontSize=14, leading=18, spaceAfter=0))
    verdict_card = Table([[verdict_metric, verdict_copy]], colWidths=[2.15*inch,7.3*inch])
    verdict_card.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),HexColor(SAND)), ('BOX',(0,0),(-1,-1),.6,HexColor('#D7CBA5')),
        ('LINEAFTER',(0,0),(0,0),.45,HexColor('#D7CBA5')), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),18), ('RIGHTPADDING',(0,0),(-1,-1),18),
        ('TOPPADDING',(0,0),(-1,-1),15), ('BOTTOMPADDING',(0,0),(-1,-1),15),
    ]))
    story += [p("08 / Verdict",s['kicker']),p("So: did you notice a real pattern?",s['h2']),
              p("<b>Yes, with an asterisk.</b> Gilligan's Island is not one of SlashFilm's largest content ecosystems. But Gilligan-related coverage became a surprisingly persistent legacy-TV pattern after 2023, visible beside contemporary and award-winning television properties.",s['body']),
              Spacer(1, .08*inch), verdict_card, Spacer(1, .16*inch),
              text_card("The careful conclusion: SlashFilm has a real, recent Gilligan-related coverage pattern. The surprise is not that it outpublishes every modern franchise. It is that a 1960s sitcom and its cast receive recurring attention at a level that surpasses most of the current-TV group.",s['body']),
              Spacer(1, .08*inch), p("This packet does not attempt to explain why SlashFilm publishes these stories or infer traffic performance. It documents frequency, timing, and comparability - no more, no less.",s['small']),PageBreak()]
    # Appendix
    story += [p("09 / Notes on method",s['kicker']),p("How to read the evidence",s['h2']),
              p("Source: SlashFilm article pages indexed through the site's XML sitemaps and collected into year-specific CSVs. The catalog includes title, publication time, URL, primary subject, and Gilligan-related flag. The analysis includes 68,398 total articles from 2020 through Aug. 2, 2026.",s['body']),
              p("Selected-property counts use transparent title/URL aliases. This avoids treating platform names such as HBO, Netflix, or streaming as subjects. It also means the comparison is reproducible, but not a claim that every possible mention in body text has been counted.",s['body']),
              p("External context references: Television Academy, 2024 and 2025 Emmy Awards nominees and winners; Nielsen annual streaming rankings/ARTEY awards. These sources select the current-TV control group; the coverage counts themselves come from SlashFilm.",s['body']),
              p("Limitations: 2020-2023 have less complete subject normalization, so they are used only for the historical Gilligan trend. 2026 is a partial year. Article frequency measures editorial output, not clicks, cultural importance, or audience size.",s['body']),
              Spacer(1,.18*inch),p("The data has spoken. It brought a coconut radio.",s['callout'])]
    doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)


def main():
    register_fonts()
    metrics=compute()
    charts={"annual":chart_annual(metrics),"scoreboard":chart_scoreboard(metrics),"monthly":chart_monthly(metrics),"cast":chart_cast(metrics),"current_tv":chart_current_tv(metrics)}
    report(metrics,charts)
    print(OUT)


if __name__ == "__main__":
    main()
