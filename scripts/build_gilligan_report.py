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
    cover_title=Paragraph("Is Slashfilm Actually Obsessed With<br/>Gilligan's Island?", ParagraphStyle("cover", parent=s['h1'], textColor=HexColor(CREAM), fontSize=43, leading=46, spaceAfter=18))
    cover_body=Paragraph("A few years ago, I started noticing something weird:<br/>SlashFilm kept publishing stories about Gilligan's Island.<br/>The show. The cast. The whole Gilligan Universe.<br/>So I had an AI catalogue six years of headlines<br/>to find out whether I was imagining it.", ParagraphStyle("coverbody", parent=s['body'], textColor=HexColor('#D5E5E0'), fontSize=12.2, leading=17, spaceAfter=16))
    cover_date = Paragraph("FROM 2024 THROUGH<br/>AUG. 2, 2026, THERE WERE", ParagraphStyle("coverdate", parent=s['kicker'], fontName=LABEL_FONT, fontSize=12, leading=16, textColor=HexColor(NAVY), spaceAfter=0))
    cover_number = Paragraph(str(expanded), ParagraphStyle("covernumber", parent=s['h1'], fontName=DISPLAY_FONT, fontSize=54, leading=54, textColor=HexColor(NAVY), spaceAfter=0))
    cover_label = Paragraph("GILLIGAN-RELATED STORIES", ParagraphStyle("coverlabelstat", parent=s['kicker'], fontName=LABEL_FONT, fontSize=16, leading=19, textColor=HexColor(NAVY), spaceAfter=0))
    cover_stat = Table([[cover_date], [cover_number], [cover_label]], colWidths=[3.15*inch])
    cover_stat.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),HexColor(SAND)),
        ('LEFTPADDING',(0,0),(-1,-1),20), ('RIGHTPADDING',(0,0),(-1,-1),14),
        ('TOPPADDING',(0,0),(0,0),18), ('BOTTOMPADDING',(0,0),(0,0),7),
        ('TOPPADDING',(0,1),(0,1),0), ('BOTTOMPADDING',(0,1),(0,1),6),
        ('TOPPADDING',(0,2),(0,2),0), ('BOTTOMPADDING',(0,2),(0,2),18),
    ]))
    cover_meta=Paragraph(f"{shares:.2f}% of all {focal_total:,} stories from 2024 through Aug. 2, 2026.\n68,398 headlines later: I was not imagining it.", ParagraphStyle("covermeta", parent=s['small'], textColor=HexColor('#D5E5E0'), fontSize=10.2, leading=14))
    cover_left = [p("A DATA INVESTIGATION", ParagraphStyle("coverkick", parent=s['kicker'], textColor=HexColor(CORAL))), cover_title, cover_body, cover_meta]
    cover_right = [Spacer(1, 1.15*inch), cover_stat, Spacer(1, .18*inch), p("OBSERVED PATTERN<br/>2024-2026", ParagraphStyle("coverlabel", parent=s['kicker'], textColor=HexColor(SEA), alignment=1))]
    cover_table = Table([[cover_left, cover_right]], colWidths=[6.55*inch,3.15*inch])
    cover_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),.65*inch),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story += [cover_table, Spacer(1,.1*inch), p("Built from SlashFilm headlines, publication dates, and a frankly excessive amount of categorizing. August 2026 is year-to-date.", ParagraphStyle("coverfoot",parent=s['small'],textColor=HexColor('#AFC9C3'))), PageBreak()]
    # Framing and method
    story += [p("01 / The Question",s['kicker']),p("Was I Imagining This?",s['h2']),
              p("At first, this felt like one of those brain tricks. You notice a thing once, then suddenly it seems to be everywhere. But Gilligan stories kept showing up. Not just the island itself, either. Alan Hale Jr. Bob Denver. Natalie Schafer. The whole cast.",s['body']),
              p("So I had an AI agent catalogue 68,398 SlashFilm stories published from 2020 through Aug. 2, 2026. I counted stories directly about <b>Gilligan's Island</b>, then counted the larger <b>Gilligan Universe</b>: the show plus its seven main cast members.",s['body']),
              p("This is not a complaint that SlashFilm should cover <i>Euphoria</i> or <i>Outer Banks</i> instead. I do not have a preferred show in this fight. I just wanted to know whether a weird hunch had receipts.",s['body']),
              p("For the franchise comparisons, I used the headline and URL. When a headline was vague, I checked the story quickly. The point is simple: count what SlashFilm chose to publish, then see where Gilligan lands.",s['small']), Spacer(1,.18*inch)]
    evidence = Table([[p("68,398", ParagraphStyle("metric", parent=s['h2'], fontSize=24, leading=25)), p("21,932", ParagraphStyle("metric2", parent=s['h2'], fontSize=24, leading=25)), p("2024-2026", ParagraphStyle("metric3", parent=s['h2'], fontSize=24, leading=25))],
                      [p("SlashFilm stories catalogued", s['small']), p("Stories compared most closely", s['small']), p("Where the Gilligan spike happens", s['small'])]], colWidths=[3.15*inch,3.15*inch,3.15*inch])
    evidence.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#F6F0DF')),('BOX',(0,0),(-1,-1),.4,HexColor('#D7CBA5')),('INNERGRID',(0,0),(-1,-1),.3,HexColor('#D7CBA5')),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    story += [evidence, PageBreak()]
    # Timeline
    story += [p("02 / Exhibit A",s['kicker']),p("The Gilligan Spike Is Recent",s['h2']),chart_card(charts['annual'],9.55*inch,3.35*inch), Spacer(1,.12*inch),
              text_card("For four years, this was basically nothing. Then SlashFilm published 110 Gilligan-related stories in 2024. The number dropped in 2025, but it did not disappear. And by Aug. 2, 2026, the site had already run 44 more.",s['body']),
              p("The raw annual counts: 0 (2020), 2 (2021), 0 (2022), 1 (2023), 110 (2024), 50 (2025), and 44 through Aug. 2, 2026.",s['small']),PageBreak()]
    # Scoreboard
    story += [p("03 / The Scoreboard",s['kicker']),p("Gilligan Is Not Marvel. That Is Not the Point.",s['h2']),chart_card(charts['scoreboard'],9.55*inch,4.55*inch), Spacer(1,.12*inch),
              text_card("Marvel, Star Trek, and Star Wars are huge machines. Of course they get more coverage. The funny part is lower on the list: Gilligan Universe lands above <i>The Simpsons</i>, <i>Stranger Things</i>, <i>Harry Potter</i>, <i>The Pitt</i>, <i>Landman</i>, and <i>Breaking Bad</i> in this stretch of SlashFilm history.",s['body']),PageBreak()]
    # direct expanded
    table_data=[["Metric","2024","2025","2026 YTD","Focal total"], ["Direct Gilligan's Island",*[metrics['direct'][y] for y in FOCAL_YEARS],direct], ["Expanded Gilligan Universe",*[metrics['annual'][y]['expanded'] for y in FOCAL_YEARS],expanded]]
    t=Table(table_data,colWidths=[3.4*inch,1.55*inch,1.55*inch,1.55*inch,1.55*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),DISPLAY_FONT),('FONTNAME',(0,1),(0,-1),LABEL_FONT),('FONTNAME',(1,1),(-1,-1),LABEL_FONT),('BACKGROUND',(0,2),(-1,2),HexColor(SAND)),('GRID',(0,0),(-1,-1),.35,HexColor('#C4D5D0')),('ALIGN',(1,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [p("04 / Two Ways to Count It",s['kicker']),p("The Island Alone, and the Island Plus Its Orbit",s['h2']),t,Spacer(1,.18*inch),
              text_card("Here is the wrinkle: a Gilligan story is not always about Gilligan's Island. In 2026, Alan Hale Jr. is the biggest Gilligan-related subject even when the story is actually about <i>The Love Boat</i>, a Western, or some forgotten movie role. That is why both counts are on the page.",s['body']),Spacer(1,.18*inch)]
    orbit = Table([[p("105", ParagraphStyle("orbitnum", parent=s['h2'], fontSize=27, leading=29, textColor=HexColor(CORAL))), p("99", ParagraphStyle("orbitnum2", parent=s['h2'], fontSize=27, leading=29, textColor=HexColor(CORAL)))],
                   [p("direct-show stories", s['small']), p("cast-led stories added by the expanded measure", s['small'])]], colWidths=[4.7*inch,4.7*inch])
    orbit.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#EDF5F2')),('BOX',(0,0),(-1,-1),.55,HexColor(SEA)),('INNERGRID',(0,0),(-1,-1),.35,HexColor('#B9DDD7')),('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),11)]))
    story += [orbit, PageBreak()]
    # cadence
    story += [p("05 / Cadence",s['kicker']),p("This Is Recurring Coverage, Not One Nostalgia Package",s['h2']),chart_card(charts['monthly'],9.55*inch,3.45*inch), Spacer(1,.12*inch),
              text_card("This is not one anniversary package, one reboot announcement, or one editor going through a phase for a week. Gilligan coverage keeps coming back month after month. June 2026 alone had 15 stories.",s['body']),PageBreak()]
    # cast
    story += [p("06 / Who Is Actually Being Covered?",s['kicker']),p("Gilligan Is a Show, but the Cast Is the Engine",s['h2']),chart_card(charts['cast'],9.55*inch,3.75*inch), Spacer(1,.12*inch),
              text_card("The island is the biggest bucket. But the cast is what turns it into a deep well of stories: old TV roles, behind-the-scenes trivia, forgotten movies, other sitcoms. The Gilligan Universe is doing a lot of work here.",s['body']),PageBreak()]
    # Current TV
    story += [p("07 / The Control Group",s['kicker']),p("Where Are the Big Current Shows?",s['h2']),chart_card(charts['current_tv'],9.55*inch,3.88*inch), Spacer(1,.1*inch),
              text_card("Gilligan Universe has more SlashFilm stories in this window than <i>Stranger Things</i>: 204 to 163. Read that again. <i>Stranger Things</i> is a real cultural phenomenon. Gilligan is a 1960s sitcom about seven people stuck on an island. That does not make Gilligan bigger than <i>Stranger Things</i>, obviously. It means SlashFilm has published a truly mind-boggling amount of Gilligan material.",s['body']),
              p("The control group includes 2024 Emmy winners such as <i>Shogun</i>, <i>Hacks</i>, and <i>Baby Reindeer</i>, plus 2025 winners <i>The Pitt</i>, <i>The Studio</i>, and <i>Adolescence</i>. Popular-series controls include <i>Euphoria</i>, <i>Outer Banks</i>, <i>Bridgerton</i>, <i>The Last of Us</i>, <i>Stranger Things</i>, <i>The White Lotus</i>, <i>Severance</i>, and <i>The Bear</i>.",s['small']),PageBreak()]
    # Findings
    verdict_metric = Paragraph("<font size=31><b>110</b></font><br/><font size=10>GILLIGAN-RELATED<br/>STORIES IN 2024</font>", ParagraphStyle("verdictmetric", parent=s['small'], fontName=DISPLAY_FONT, textColor=HexColor(CORAL), leading=12))
    verdict_copy = Paragraph("<b>One memorable subject can stick in your head. It cannot make a site publish 110 stories in one year.</b><br/><br/>That is the part I needed the spreadsheet to settle.", ParagraphStyle("verdictcopy", parent=s['body'], fontSize=14, leading=18, spaceAfter=0))
    verdict_card = Table([[verdict_metric, verdict_copy]], colWidths=[2.15*inch,7.3*inch])
    verdict_card.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),HexColor(SAND)), ('BOX',(0,0),(-1,-1),.6,HexColor('#D7CBA5')),
        ('LINEAFTER',(0,0),(0,0),.45,HexColor('#D7CBA5')), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),18), ('RIGHTPADDING',(0,0),(-1,-1),18),
        ('TOPPADDING',(0,0),(-1,-1),15), ('BOTTOMPADDING',(0,0),(-1,-1),15),
    ]))
    story += [p("08 / Verdict",s['kicker']),p("So: Did You Notice a Real Pattern?",s['h2']),
              p("<b>Yes, with an asterisk.</b> Gilligan's Island is not one of SlashFilm's biggest franchises. But since 2024, the site has written about the show and its cast often enough that it belongs next to shows people are actually talking about right now.",s['body']),
              Spacer(1, .08*inch), verdict_card, Spacer(1, .16*inch),
              text_card("So yes: SlashFilm really does have a recent Gilligan thing. It is not bigger than every modern franchise. It is just bizarrely present for a 1960s sitcom and its cast, especially next to most of the current-TV group.",s['body']),
              Spacer(1, .08*inch), p("What I cannot tell you is why SlashFilm keeps publishing them or whether they perform well. This only answers the first question: the pattern is real.",s['small']),PageBreak()]
    # Appendix
    story += [p("09 / Notes on Method",s['kicker']),p("How to Read the Evidence",s['h2']),
              p("To build this, I pulled SlashFilm article pages from the site's XML sitemaps and put them into year-by-year CSVs. Each row has a title, publication time, URL, primary subject, and Gilligan-related flag. Altogether, that is 68,398 articles from 2020 through Aug. 2, 2026.",s['body']),
              p("For the show and franchise comparisons, I used titles and URLs. That keeps the count focused on what a story is actually about. An article about <i>Task</i> does not become a story about “streaming” just because it is on HBO. And these are article counts, not every possible body-text mention.",s['body']),
              p("I picked the current-TV comparison group from recent Emmy winners and nominees, plus Nielsen's annual streaming lists. Those sources helped choose the shows. The actual story counts all come from SlashFilm.",s['body']),
              p("A few caveats. The older 2020-2023 rows have less complete subject labeling, so I only use them to show the big historical Gilligan swing. 2026 is a partial year. And a high article count does not prove clicks, cultural importance, or audience size. It only shows what SlashFilm published, and how often.",s['body']),
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
