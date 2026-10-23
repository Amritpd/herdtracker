#!/usr/bin/env python3
"""Herd Tracker — multi-page static site builder (v2 site split, Oct 23, 2026).

Replaces the single-file dashboard build (build_dashboard.py stays for the
legacy file). Generates site/ with one page per top-level tab, all sharing the
broadsheet template extracted from dashboard_template.html:

  index.html            Front Page
  trends/index.html     Trends (NEW — Thesis Waves, Graveyard, Hype Gap)
  regions/index.html    Regional editions (Americas/Europe/APAC/MEA sub-tabs)
  rounds/index.html     Round Explorer (filters + CSV)
  fresh-powder/index.html
  investors/index.html
  about|methodology|privacy|terms|contact/index.html
  robots.txt, ads.txt (placeholder), sitemap.txt (paths; set BASE_URL for XML)

Data honesty notes baked into pages:
- Historical waves are era CHECKPOINTS (2014/2017/2019 StrictlyVC mirror + 2026).
- Region tags cover a subset of rounds (see region.py) — coverage is printed.
Run: python3 build_site.py
"""
import json, os, re, statistics
from region import tag_rounds, clean_investors

BASE_URL = None  # set to the real domain before generating sitemap.xml for AdSense/SEO
OUT = "site"
REGIONS = ["Americas", "Europe", "APAC", "MEA"]

def money(v):
    if not v: return "—"
    if v >= 1e9: return f"${v/1e9:.2f}B"
    if v >= 1e6: return f"${v/1e6:.1f}M"
    return f"${v/1e3:.0f}K"

def load_css():
    tpl = open("dashboard_template.html").read()
    css = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
    return css + """
  nav.sections{display:flex;gap:24px;flex-wrap:wrap;border-bottom:2px solid var(--ink);margin-bottom:20px}
  nav.sections a{font-size:14.5px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;
    padding:10px 2px;color:var(--mut);border-bottom:4px solid transparent;margin-bottom:-2px}
  nav.sections a.on{color:var(--ink);border-bottom-color:var(--amber)}
  nav.sections a:hover{text-decoration:none;color:var(--ink)}
  .subtabs{display:flex;gap:20px;flex-wrap:wrap;margin:6px 0 16px}
  .subtab{background:none;border:1px solid var(--bord);border-radius:20px;font-family:inherit;
    font-size:13.5px;font-weight:700;padding:6px 14px;cursor:pointer;color:var(--sub)}
  .subtab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
  .note{color:var(--mut);font-size:13px;font-style:italic;margin:10px 0}
  .cow{display:block;margin:2px auto 0;height:150px;width:auto;mix-blend-mode:multiply;border-radius:18px}
  .tagpill{font-family:"Libre Franklin";font-weight:700;font-size:11.5px;letter-spacing:.8px;text-transform:uppercase;border:1.5px solid var(--ink);padding:3px 9px;border-radius:20px;background:#fdf6d8}
"""

CSS = None
def page(title, desc, active, body, depth=0, extra_head="", cow=False):
    p = "../" * depth
    nav_items = [("Front Page", f"{p}index.html", "front"),
                 ("Trends", f"{p}trends/", "trends"),
                 ("Regions", f"{p}regions/", "regions"),
                 ("Rounds", f"{p}rounds/", "rounds"),
                 ("Fresh Powder", f"{p}fresh-powder/", "funds"),
                 ("Investors", f"{p}investors/", "investors"),
                 ("Exits", f"{p}exits/", "exits"),
                 ("The Herd", f"{p}herd/", "herd")]
    nav = "".join(f'<a href="{href}" class="{"on" if key==active else ""}">{label}</a>'
                  for label, href, key in nav_items)
    COWIMG = f'<img class="cow" src="{p}assets/cow-256.webp" alt="The Herd Tracker cow — our proprietary herd mark">' if cow else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="{p}assets/favicon.png">
<title>{title} — The Herd Tracker</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title} — The Herd Tracker">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://amritpd.github.io/herdtracker/assets/herd.webp">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://amritpd.github.io/herdtracker/assets/herd.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,600&family=Libre+Franklin:wght@400;600;700;800&display=swap" rel="stylesheet">
<!-- AdSense: paste publisher script here after approval (see UPGRADE_PLAN.md) -->
<style>{CSS}</style>
{extra_head}
</head>
<body>
<div class="wrap">
  <header>
    <div class="mast-top">Vol. I · No. 1 — The Funding Weather</div>
    {COWIMG}
    <h1>The Herd Tracker</h1>
    <div class="tag"><i>The herd, measured.</i> Every round, every new fund, every stampede — extracted from the newsletters the herd reads about itself.</div>
    <div class="meta">Window: {WINDOW} · Sources: Finsmes, EU-Startups, Inc42, e27 (rounds), StrictlyVC archive, VCWire · Rule-based extraction (no paid APIs)</div>
  </header>
  <nav class="sections">{nav}</nav>
{body}
  <div class="ad">Advertisement — sponsorship enquiries via the Contact page</div>
  <footer>The Herd Tracker is built from public funding announcements and filings. Facts are extracted and re-summarised with links to sources; full text is never republished.
  See <a href="{p}methodology/">Methodology &amp; Sources</a> · <a href="{p}about/">About</a> · <a href="{p}privacy/">Privacy</a> · <a href="{p}terms/">Terms</a> · <a href="{p}contact/">Contact</a></footer>
</div>
</body>
</html>"""

def kpis(items):
    cells = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in items)
    return f'<div class="kpis">{cells}</div>'

def table(headers, rows_html):
    th = "".join(f"<th>{h}</th>" for h in headers)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(rows_html)}</tbody></table>"

def bars(pairs, color="var(--blue)", maxv=None):
    maxv = maxv or max((v for _, v in pairs), default=1)
    out = []
    for label, v in pairs:
        pct = (v / maxv * 100) if maxv else 0
        out.append(f'<div class="bar-row"><div>{label}</div><div class="bar-track">'
                   f'<div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
                   f'<div class="bar-val">{money(v) if v>=10000 else v}</div></div>')
    return "".join(out)

# ---------------- data ----------------
rounds_raw = json.load(open("rounds.json"))
funds = json.load(open("funds.json"))
# Merge region-native extraction (extract_regional.py) when present — dedupe by name
for extra_file, target, key in (("rounds_regional.json", rounds_raw, "company"),
                                ("funds_regional.json", funds, "firm")):
    if os.path.exists(extra_file):
        have = {x[key].lower() for x in target}
        for x in json.load(open(extra_file)):
            if x[key].lower() not in have:
                target.append(x); have.add(x[key].lower())
def sanitize_company(name):
    """Drop editorial roundup articles misparsed as companies; strip descriptor prefixes."""
    n = name.strip()
    if (n.startswith("From ") and " To " in n) or "— Indian Startups" in n or n.endswith("Startups That Raised"):
        return None
    n = re.sub(r"^(D2C Brand|Fintech|Healthtech|Edtech Startup)\s+", "", n)
    m = re.match(r"^.+?-Owned\s+(.+)$", n)
    if m: n = m.group(1)
    return n

_cleaned = []
for _r in rounds_raw:
    _n = sanitize_company(_r["company"])
    if _n is None: continue
    _r["company"] = _n
    _cleaned.append(_r)
rounds_raw = _cleaned
archive = json.load(open("archive.json"))
exits = json.load(open("exits.json")) if os.path.exists("exits.json") else []
throughline = json.load(open("throughline.json")) if os.path.exists("throughline.json") else None
TY = json.load(open("trends_yearly.json")) if os.path.exists("trends_yearly.json") else None
try:
    raw_posts = json.load(open("raw/finsmes.json"))
except FileNotFoundError:
    raw_posts = None
rounds, rstats = tag_rounds(rounds_raw, raw_posts)
for r in rounds:
    r["investors_clean"] = clean_investors(r.get("investors"))
rounds.sort(key=lambda r: r["date"], reverse=True)
WINDOW = f'{rounds[-1]["date"]} → {rounds[0]["date"]}'
TOTAL = sum(r["amount"] for r in rounds if r["amount"])
TOP10 = sum(sorted((r["amount"] for r in rounds if r["amount"]), reverse=True)[:10])
REST = TOTAL - TOP10
MEDIAN = statistics.median([r["amount"] for r in rounds if r["amount"]])
FRESH = sum(f["amount"] for f in funds if f.get("amount"))

sector_tot, sector_cnt = {}, {}
for r in rounds:
    sector_tot[r["sector"]] = sector_tot.get(r["sector"], 0) + (r["amount"] or 0)
    sector_cnt[r["sector"]] = sector_cnt.get(r["sector"], 0) + 1
inv_cnt, inv_tot = {}, {}
for r in rounds:
    for inv in r["investors_clean"]:
        inv_cnt[inv] = inv_cnt.get(inv, 0) + 1
        inv_tot[inv] = inv_tot.get(inv, 0) + (r["amount"] or 0)
stage_med = {}
for st in sorted(set(r["stage"] for r in rounds)):
    vals = [r["amount"] for r in rounds if r["stage"] == st and r["amount"]]
    if vals:
        stage_med[st] = (len(vals), statistics.median(vals))

# ---------------- front page ----------------
def front_page():
    big = sorted(rounds, key=lambda r: r["amount"] or 0, reverse=True)[:8]
    big_rows = [f'<tr><td><a href="{r["url"]}" target="_blank" rel="noopener">{r["company"]}</a></td>'
                f'<td class="amt">{money(r["amount"])}</td><td>{r["stage"]}</td><td>{r["sector"]}</td></tr>' for r in big]
    fund_rows = [f'<tr><td>{f["firm"]}</td><td>{f["fund"]}</td><td class="amt">{f["display"]}</td><td>{f["focus"]}</td></tr>'
                 for f in sorted(funds, key=lambda f: f["date"], reverse=True)[:5]]
    lead = sorted(inv_cnt.items(), key=lambda kv: -kv[1])[:8]
    lead_rows = [f"<tr><td>{n}</td><td>{c}</td></tr>" for n, c in lead]
    rest_pct = REST / TOTAL * 100 if TOTAL else 0
    body = f"""
  {kpis([(str(len(rounds)), "rounds tracked"), (money(TOTAL), "total raised"),
          (money(FRESH), "fresh powder (disclosed)"), (money(MEDIAN), "median round")])}
  <h2>Herd Signals</h2>
  <p class="h2sub">What the herd is doing this window — before it knows it's doing it.</p>
  <div class="sig">
    <div class="panel"><div class="big">The Rest-of-Market is {rest_pct:.0f}% of the headline</div>
    <p>Strip the top 10 rounds ({money(TOP10)}) and the "record" {money(TOTAL)} window is really {money(REST)} spread across {len(rounds)-10} companies. The headline lies; the rest of the market is the market.</p></div>
    <div class="panel"><div class="big">{sector_cnt.get('AI / ML', 0)} of {len(rounds)} rounds are AI / ML</div>
    <p>AI took {money(sector_tot.get('AI / ML', 0))} of the window's dollars. See the <a href="trends/">Trends page</a> for how this wave compares to fintech's 2017 crest and cannabis's 2019 peak — and total disappearance.</p></div>
    <div class="panel"><div class="big">{money(FRESH)} of Fresh Powder needs a home</div>
    <p>{len(funds)} newly closed funds disclosed sizes this window. Every dollar of it has to be deployed in the next 2–4 years. <a href="fresh-powder/">The full table</a>.</p></div>
  </div>
  <h2>Biggest Stampedes</h2>
  <div class="panel">{table(["Company", "Amount", "Stage", "Sector"], big_rows)}</div>
  <div class="grid2">
    <div><h2>Fresh Powder — Latest</h2><div class="panel">{table(["Firm", "Fund", "Size", "Focus"], fund_rows)}</div></div>
    <div><h2>Herd Leaderboard</h2><div class="panel">{table(["Investor", "Rounds"], lead_rows)}</div></div>
  </div>
  <p class="note">Full slices: <a href="rounds/">every round, filterable</a> · <a href="regions/">regional editions</a> · <a href="investors/">investor leaderboard</a> · <a href="trends/">thesis waves since 2014</a>.</p>"""
    return page("Front Page", "VC funding rounds, new funds and thesis stampedes — measured weekly.", "front", body, cow=True)

# ---------------- trends ----------------
KW_SECTOR = {"Artificial intelligence": "AI / ML", "Fintech": "Fintech",
             "Crypto / blockchain": "Crypto / Web3", "Robotics": "Robotics / Hardware"}
SECTOR_COLORS = {
    "AI / ML": "#00598c", "Fintech": "#7a1f2b", "Crypto / Web3": "#a67c00",
    "Cannabis": "#4a7c59", "Health / Bio": "#5b7fa6", "SaaS / Enterprise": "#333333",
    "Consumer / E-comm": "#b3541e", "Mobility": "#6b4fa1", "Climate / Energy": "#2e7d6b",
    "Cybersecurity": "#8c2f39", "Robotics / Hardware": "#595959", "EdTech": "#946b00",
    "Food / AgTech": "#7d4c29", "PropTech": "#2f5d8a", "Media / Social": "#a03d63",
    "Quantum": "#1a5276", "Space": "#34495e", "DevTools / Infra": "#707070",
    "Other sectors": "#ddd6c4",
}
ROUND_SECTOR_MAP = {"Consumer": "Consumer / E-comm", "Real Estate": "PropTech",
                    "DevTools": "DevTools / Infra", "Space / Defense": "Space"}

def mix_stacks():
    """Return (sectors in display order, {year: {sector: pct}}) incl. a mapped 2026 bar."""
    years = TY["years"]
    order = sorted(TY["mix"].keys(), key=lambda s: -sum(TY["mix"][s][str(y)] for y in years))
    top, rest = order[:11], order[11:]
    data = {}
    for y in years:
        d = {s: TY["mix"][s][str(y)] for s in top}
        d["Other sectors"] = round(sum(TY["mix"][s][str(y)] for s in rest), 1)
        data[y] = d
    mapped = {}
    for rs, c in TY["rounds2026_by_count"].items():
        tgt = ROUND_SECTOR_MAP.get(rs, rs)
        if tgt in SECTOR_COLORS and tgt != "Other sectors":
            mapped[tgt] = mapped.get(tgt, 0) + c
    tot = sum(mapped.values()) or 1
    d26 = {s: round(100 * mapped.get(s, 0) / tot, 1) for s in top}
    d26["Other sectors"] = round(100 - sum(d26.values()), 1)
    data[2026] = d26
    return top + ["Other sectors"], data

def stacked_mix_svg():
    sectors, data = mix_stacks()
    years = TY["years"] + [2026]
    W, H, L, B, T = 1060, 400, 46, 30, 12
    iw, ih = W - L - 12, H - B - T
    bw = iw / len(years) * 0.62
    parts = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto" role="img" aria-label="Stacked bars: sector mix of VC coverage by year">']
    for gy in (0, 25, 50, 75, 100):
        y = T + ih - ih * gy / 100
        parts.append(f'<line x1="{L}" y1="{y:.0f}" x2="{W-12}" y2="{y:.0f}" stroke="#ddd6c4" stroke-width="1"/>'
                     f'<text x="{L-6}" y="{y+4:.0f}" font-size="11" text-anchor="end" fill="#666">{gy}%</text>')
    for i, yr in enumerate(years):
        cx = L + iw * (i + 0.5) / len(years)
        x = cx - bw / 2
        acc_px = 0.0
        for s in sectors:
            v = data[yr].get(s, 0)
            if v <= 0: continue
            h = ih * v / 100
            y = T + ih - acc_px - h
            parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{max(h-0.5,0.5):.0f}" fill="{SECTOR_COLORS[s]}"><title>{s} · {yr}: {v}%</title></rect>')
            acc_px += h
        lab = f"{yr}*" if yr == 2026 else str(yr)
        parts.append(f'<text x="{cx:.0f}" y="{H-8}" font-size="12.5" font-weight="700" text-anchor="middle" fill="#222">{lab}</text>')
    parts.append("</svg>")
    legend = "".join(
        f'<span style="display:inline-block;margin:2px 14px 2px 0;font-size:12.5px"><span style="display:inline-block;width:11px;height:11px;background:{SECTOR_COLORS[s]};margin-right:6px"></span>{s} · {data[2019].get(s, 0)}% (2019)</span>'
        for s in sectors)
    return "".join(parts), legend

def trend_lines_svg():
    years = TY["years"]
    W, H, L, B, T = 1060, 400, 46, 30, 16
    iw, ih = W - L - 130, H - B - T
    ymax = 90
    parts = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto" role="img" aria-label="Line chart: share of editions mentioning each sector, 2013-2019">']
    for gy in (0, 30, 60, 90):
        y = T + ih - ih * gy / ymax
        parts.append(f'<line x1="{L}" y1="{y:.0f}" x2="{L+iw}" y2="{y:.0f}" stroke="#ddd6c4"/>'
                     f'<text x="{L-6}" y="{y+4:.0f}" font-size="11" text-anchor="end" fill="#666">{gy}%</text>')
    for i, yr in enumerate(years):
        x = L + iw * i / (len(years) - 1)
        parts.append(f'<text x="{x:.0f}" y="{H-8}" font-size="12.5" font-weight="700" text-anchor="middle" fill="#222">{yr}</text>')
    default_on = {"AI / ML", "Fintech", "Crypto / Web3", "Cannabis"}
    for s, series in TY["raw_share"].items():
        pts, labels = [], []
        for i, yr in enumerate(years):
            x = L + iw * i / (len(years) - 1)
            y = T + ih - ih * float(series[str(yr)]) / ymax
            pts.append(f"{x:.0f},{y:.0f}")
            labels.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="{SECTOR_COLORS[s]}"/>'
                          f'<text x="{x:.0f}" y="{y-8:.0f}" font-size="10.5" font-weight="700" text-anchor="middle" fill="{SECTOR_COLORS[s]}">{series[str(yr)]}%</text>')
        last_y = T + ih - ih * float(series[str(years[-1])]) / ymax
        disp = "" if s in default_on else ' style="display:none"'
        parts.append(f'<g class="tline" data-sector="{s}"{disp}><polyline points="{" ".join(pts)}" fill="none" stroke="{SECTOR_COLORS[s]}" stroke-width="2.4"/>'
                     f'{"".join(labels)}'
                     f'<text x="{float(pts[-1].split(",")[0])+9:.0f}" y="{last_y+4:.0f}" font-size="12" font-weight="700" fill="{SECTOR_COLORS[s]}">{s} · {series[str(years[-1])]}%</text></g>')
    parts.append("</svg>")
    chips = "".join(
        f'<button class="subtab {"on" if s in default_on else ""}" data-line="{s}" onclick="toggleLine(this)">{s}</button>'
        for s in TY["raw_share"].keys())
    return "".join(parts), chips

def trends_page():
    kw = archive["keywords"]
    wave_blocks = []
    for k in kw:
        rows = []
        for yr in ("2014", "2017", "2019", "2026"):
            v = k[f"p{yr}"]
            rows.append(f'<div class="kw-line"><div class="kw-yr">{yr}</div><div class="bar-track">'
                        f'<div class="bar-fill" style="width:{v}%;background:var(--blue)"></div></div>'
                        f'<div class="kw-val">{v}%</div></div>')
        wave_blocks.append(f'<div class="kw-row"><div class="kw-name">{k["name"]}</div>{"".join(rows)}</div>')
    grave = []
    for k in sorted(kw, key=lambda k: -max(k["p2014"], k["p2017"], k["p2019"], k["p2026"])):
        vals = [(k[f"p{y}"], y) for y in ("2014", "2017", "2019", "2026")]
        peak, peakyr = max(vals)
        grave.append(f'<tr><td>{k["name"]}</td><td>{peakyr}</td><td>{peak}%</td><td>{k["p2026"]}%</td>'
                     f'<td>{"—" if peak == 0 else f"{peak - k["p2026"]} pts off peak"}</td></tr>')
    hype = []
    for name, sector in KW_SECTOR.items():
        k = next(x for x in kw if x["name"] == name)
        dshare = sector_tot.get(sector, 0) / TOTAL * 100 if TOTAL else 0
        gap = k["p2026"] - dshare
        verdict = "attention > money (hype)" if gap > 10 else ("money > attention (quiet)" if gap < -10 else "roughly matched")
        hype.append(f'<tr><td>{name}</td><td>{k["p2026"]}%</td><td>{dshare:.0f}%</td><td>{verdict}</td></tr>')
    hype.append(f'<tr><td>Cannabis</td><td>0%</td><td>0%</td><td>gone — 27% of coverage at its 2019 peak</td></tr>')
    sector_bars = bars(sorted(sector_tot.items(), key=lambda kv: -kv[1])[:8])
    waves_body = f"""
  <h2>Thesis Waves — The Herd, Over Time</h2>
  <p class="h2sub">Share of VC newsletter coverage by thesis, at era checkpoints: 2014 · 2017 · 2019 (StrictlyVC mirror, 1,238 editions) · 2026 (current pipeline).</p>
  <div class="panel">{''.join(wave_blocks)}
  <p class="note">Checkpoints, not a continuous series — labelled as such. From launch forward the weekly pipeline fills the line in. Cannabis: 27% of all coverage in 2019, 0% today. Every thesis has a half-life; this page dates the tombstones.</p></div>
  <h2>The Graveyard</h2>
  <div class="panel">{table(["Thesis", "Peak year", "Peak", "2026", "Status"], grave)}</div>
  <h2>Hype Gap — Attention vs Money (2026)</h2>
  <p class="h2sub">Coverage share (what the herd talks about) vs dollar share (where money actually landed this window).</p>
  <div class="panel">{table(["Thesis", "Coverage", "Dollars", "Read"], hype)}</div>
  <h2>Where the Money Went — This Window</h2>
  <div class="panel">{sector_bars}</div>
  <h2>Market Health</h2>
  {kpis([(money(REST), "rest-of-market (ex top 10)"), (f"{REST/TOTAL*100:.0f}%", "share outside the top 10"),
          (money(MEDIAN), "median round, this window"), (str(len(stage_med)), "stages tracked")])}
  <h2>Spotlight: Quantum — The Control Group</h2>
  <div class="panel"><ul class="tl">
    <li><b>Every era, 1–6%.</b> Quantum's coverage share never spiked and never died — the one thesis in the archive that never joined a stampede.</li>
    <li><b>2018–20 — the science project.</b> Cap tables were sovereign wealth, intelligence-community money (In-Q-Tel) and strategics. Generalist VC was absent.</li>
    <li><b>The pattern to sell:</b> knowing when a thesis peaked is worth money to anyone about to pitch into one. The archive is a graveyard with dates on the tombstones.</li>
  </ul></div>"""
    mix_svg, mix_legend = stacked_mix_svg()
    lines_svg, line_chips = trend_lines_svg()
    ed_note = " · ".join(f"{y}: {TY['editions'][str(y)]} editions" for y in TY["years"])
    body = f"""
  <h2>Trends — The Herd, Over Time</h2>
  <p class="h2sub">Three views of the same stampede: the full sector mix for every year of the archive, sector trend lines with time on the axis, and the original checkpoint analysis.</p>
  <div class="subtabs">
    <button class="subtab on" onclick="showTrend('mix', this)">Sector Mix — All Years</button>
    <button class="subtab" onclick="showTrend('lines', this)">Trend Lines</button>
    <button class="subtab" onclick="showTrend('waves', this)">Waves &amp; Archive</button>
  </div>
  <div id="trend-mix">
    <div class="panel">{mix_svg}<div style="margin-top:8px">{mix_legend}</div></div>
    <p class="note">Each bar is 100% of that year's sector-tagged coverage mentions (StrictlyVC mirror), so the mix shows where attention lived, not raw volume. *2026 is a different instrument — sector share of this window's {TY['rounds_total']} extracted rounds, mapped onto the same sector names — shown hatched by position, not blended into the series. 2013 is Sep–Dec only; archive coverage thins in 2018–19 ({ed_note}), so late years are indicative, not census.</p>
  </div>
  <div id="trend-lines" style="display:none">
    <div class="subtabs">{line_chips}</div>
    <div class="panel">{lines_svg}</div>
    <p class="note">Share of each year's editions mentioning the sector (an edition can mention several, so lines don't sum to 100). Crypto's 2018 spike is real in this corpus — that year's editions carried near-daily crypto coverage. Toggle sectors to compare trajectories: risers, fallers, and the flat line named Quantum.</p>
  </div>
  <div id="trend-waves" style="display:none">{waves_body}</div>
  <script>
  function showTrend(name, btn){{
    ['mix','lines','waves'].forEach(n => document.getElementById('trend-' + n).style.display = n === name ? '' : 'none');
    btn.parentElement.querySelectorAll('.subtab').forEach(b => b.classList.toggle('on', b === btn));
  }}
  function toggleLine(btn){{
    const s = btn.getAttribute('data-line');
    document.querySelectorAll('.tline').forEach(g => {{
      if (g.getAttribute('data-sector') === s) g.style.display = g.style.display === 'none' ? '' : 'none';
    }});
    btn.classList.toggle('on');
  }}
  </script>"""
    return page("Trends", "Thesis waves since 2014: AI, fintech's crest, cannabis 27% to 0%, and the quantum control group.", "trends", body, depth=1)

# ---------------- regions ----------------
FUND_REGION_HINTS = [("Europe", ("europe", "nordic", "london", "berlin", "paris")),
                     ("MEA", ("israel", "tel aviv", "dubai", "mena")),
                     ("APAC", ("singapore", "india", "tokyo", "australia", "asia")),
                     ("Americas", ("montreal", "toronto", "boston", "miami", "canada", "canadian", "us ", "u.s.", "new york", "chicago", "heartland"))]
def fund_region(f):
    s = (f.get("focus", "") + " " + f.get("firm", "")).lower()
    for region, hints in FUND_REGION_HINTS:
        if any(h in s for h in hints):
            return region
    return ""

def region_block(name, subset):
    if not subset:
        return f'<div class="panel"><p>No region-tagged rounds yet in this snapshot for {name}. Regional-native sources (see Methodology) fill this edition in as they are wired.</p></div>'
    total = sum(r["amount"] for r in subset if r["amount"])
    med = statistics.median([r["amount"] for r in subset if r["amount"]]) if any(r["amount"] for r in subset) else 0
    sec = {}
    for r in subset:
        sec[r["sector"]] = sec.get(r["sector"], 0) + (r["amount"] or 0)
    big = sorted(subset, key=lambda r: r["amount"] or 0, reverse=True)[:5]
    rows = [f'<tr><td><a href="{r["url"]}" target="_blank" rel="noopener">{r["company"]}</a></td><td class="amt">{money(r["amount"])}</td><td>{r["stage"]}</td><td>{r["city"].title() if r["city"] else ""}</td></tr>' for r in big]
    by_date = sorted(subset, key=lambda r: r["date"], reverse=True)
    allrows = [f'<tr><td>{r["date"]}</td><td><a href="{r["url"]}" target="_blank" rel="noopener">{r["company"]}</a></td><td class="amt">{money(r["amount"])}</td><td>{r["stage"]}</td><td>{r["sector"]}</td><td>{r["city"].title() if r["city"] else ""}</td></tr>' for r in by_date]
    return f"""{kpis([(str(len(subset)), "tagged rounds"), (money(total), "total raised"), (money(med), "median round")])}
  <h2>Top Sectors — {name}</h2><div class="panel">{bars(sorted(sec.items(), key=lambda kv: -kv[1])[:6])}</div>
  <h2>Biggest Rounds — {name}</h2><div class="panel">{table(["Company", "Amount", "Stage", "City"], rows)}</div>
  <h2>All Rounds — {name} ({len(subset)})</h2><div class="panel">{table(["Date", "Company", "Amount", "Stage", "Sector", "City"], allrows)}</div>"""

INDIA_HUBS = {"mumbai", "bengaluru", "bangalore", "delhi", "new delhi", "hyderabad", "chennai", "pune", "gurugram", "gurgaon", "noida", "kolkata", "ahmedabad", "jaipur", "kochi", "indore"}

def india_rounds():
    return [r for r in rounds if r.get("source") == "Inc42" or (r.get("city") or "").lower() in INDIA_HUBS]

def regions_page():
    tagged = [r for r in rounds if r["region"]]
    sections, buttons = [], []
    all_names = ["Global", "Americas", "Europe", "APAC", "India", "MEA"]
    for i, name in enumerate(all_names):
        if name == "Global":
            subset = rounds
        elif name == "India":
            subset = india_rounds()
        else:
            subset = [r for r in rounds if r["region"] == name]
        buttons.append(f'<button class="subtab {"on" if i == 0 else ""}" onclick="showRegion(\'{name}\')">{name}</button>')
        display = "" if i == 0 else "display:none"
        if name == "Global":
            inner = (kpis([(str(len(rounds)), "rounds, all regions"), (money(TOTAL), "total raised")]) +
                     '<p class="note">The Global view is the full window. Pick an edition above for its own board.</p>')
        elif name == "India":
            inner = ('<p class="note">Carved out of APAC — India out-produces the rest of the region combined in our window (Inc42 alone pulled as many rounds as all of EU-Startups), so it gets its own board. Indian rounds also remain counted inside APAC above.</p>' +
                     region_block(name, subset))
        else:
            inner = region_block(name, subset)
        sections.append(f'<div id="region-{name}" style="{display}">{inner}</div>')
    cov = f"{rstats['tagged']}/{len(rounds)}"
    body = f"""
  <h2>Regional Editions</h2>
  <p class="h2sub">The same herd, five pastures. North &amp; South America run as one edition (US volume dominates; LatAm alone would be an empty page). Europe, APAC and MEA stand alone — and India, APAC&rsquo;s engine, gets its own board.</p>
  <div class="subtabs">{''.join(buttons)}</div>
  {''.join(sections)}
  <p class="note">Coverage honesty: region was identified for {cov} rounds ({rstats['by_region']}) — FinSMEs states HQ cities inconsistently and skews American. Rounds are never guessed into a region. EU-Startups, Inc42 and e27 are now wired; coverage rises further as LatamList and MENAbytes come online. China is tracked on the watchlist only: English-language primary sources are thin and offshore access to Chinese private rounds is restricted, so a China edition would be coverage without access — noted, not faked.</p>
  <script>
  function showRegion(name){{
    {json.dumps(all_names)}.forEach(n => {{
      document.getElementById('region-' + n).style.display = n === name ? '' : 'none';
    }});
    document.querySelectorAll('.subtab').forEach(b => b.classList.toggle('on', b.textContent === name));
  }}
  </script>"""
    return page("Regions", "Regional editions of VC funding: Americas, Europe, APAC, MEA — plus region-vs-region signals.", "regions", body, depth=1)

# ---------------- rounds ----------------
def rounds_page():
    data = [{"company": r["company"], "amount": r["amount"] or 0, "date": r["date"], "stage": r["stage"],
             "sector": r["sector"], "region": r["region"] or "Untagged", "city": r["city"].title() if r["city"] else "",
             "investors": r["investors_clean"], "url": r["url"]} for r in rounds]
    sectors = sorted(set(r["sector"] for r in rounds))
    stages = sorted(set(r["stage"] for r in rounds))
    body = f"""
  <h2>Round Explorer</h2>
  <p class="h2sub">{len(rounds)} rounds, {WINDOW}. Filter by anything; export what's left.</p>
  <div class="controls">
    <input id="q" type="text" placeholder="Search company or investor…">
    <select id="fSector"><option value="">All sectors</option>{''.join(f'<option>{s}</option>' for s in sectors)}</select>
    <select id="fStage"><option value="">All stages</option>{''.join(f'<option>{s}</option>' for s in stages)}</select>
    <select id="fRegion"><option value="">All regions</option>{''.join(f'<option>{s}</option>' for s in REGIONS + ["Untagged"])}</select>
    <button class="subtab" onclick="exportCSV()">Export CSV</button>
  </div>
  <div class="scroll"><table id="roundTable"><thead><tr><th>Company</th><th>Amount</th><th>Date</th><th>Stage</th><th>Sector</th><th>Region</th><th>Investors</th></tr></thead><tbody></tbody></table></div>
  <p class="note" id="countLine"></p>
  <script>
  const DATA = {json.dumps(data)};
  const fmt = v => v >= 1e9 ? '$' + (v/1e9).toFixed(2) + 'B' : v >= 1e6 ? '$' + (v/1e6).toFixed(1) + 'M' : v > 0 ? '$' + Math.round(v/1e3) + 'K' : '—';
  let current = DATA;
  function render(){{
    const q = document.getElementById('q').value.toLowerCase();
    const fs = document.getElementById('fSector').value, ft = document.getElementById('fStage').value, fr = document.getElementById('fRegion').value;
    current = DATA.filter(r => (!q || r.company.toLowerCase().includes(q) || r.investors.join(' ').toLowerCase().includes(q))
      && (!fs || r.sector === fs) && (!ft || r.stage === ft) && (!fr || r.region === fr));
    document.querySelector('#roundTable tbody').innerHTML = current.map(r =>
      `<tr><td><a href="${{r.url}}" target="_blank" rel="noopener">${{r.company}}</a></td><td class="amt">${{fmt(r.amount)}}</td><td>${{r.date}}</td><td>${{r.stage}}</td><td>${{r.sector}}</td><td>${{r.region}}</td><td>${{r.investors.join(', ')}}</td></tr>`).join('');
    document.getElementById('countLine').textContent = current.length + ' of ' + DATA.length + ' rounds shown · $' + (current.reduce((s, r) => s + r.amount, 0)/1e9).toFixed(2) + 'B in view';
  }}
  function exportCSV(){{
    const rows = [['company','amount_usd','date','stage','sector','region','city','investors','url'],
      ...current.map(r => [r.company, r.amount, r.date, r.stage, r.sector, r.region, r.city, r.investors.join('; '), r.url])];
    const csv = rows.map(row => row.map(c => `"${{String(c).replaceAll('"','""')}}"`).join(',')).join('\\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], {{type: 'text/csv'}}));
    a.download = 'herd-tracker-rounds.csv'; a.click();
  }}
  ['q','fSector','fStage','fRegion'].forEach(id => document.getElementById(id).addEventListener('input', render));
  render();
  </script>"""
    return page("Rounds", "Every tracked VC funding round — filter by sector, stage, region, investor. CSV export.", "rounds", body, depth=1)

# ---------------- fresh powder ----------------
def funds_page():
    rows = [f'<tr><td>{f["firm"]}</td><td>{f["fund"]}</td><td class="amt">{f["display"]}</td><td>{f["date"]}</td><td>{f["focus"]}</td><td>{fund_region(f) or "—"}</td>'
            f'<td><a href="{f["url"]}" target="_blank" rel="noopener">source</a></td></tr>'
            for f in sorted(funds, key=lambda f: f["date"], reverse=True)]
    sized = sorted([f for f in funds if f.get("amount")], key=lambda f: -f["amount"])
    clock = [f'<tr><td>{f["firm"]} — {f["fund"]}</td><td class="amt">{f["display"]}</td><td>{f["date"]}</td></tr>' for f in sized[:5]]
    body = f"""
  {kpis([(str(len(funds)), "new funds this window"), (money(FRESH), "disclosed fresh powder")])}
  <h2>Fresh Powder — Funds That Just Closed</h2>
  <p class="h2sub">New dry powder has a 2–4 year deployment clock on it. This is the fuel table — who raised a fund, how big, and what it hunts.</p>
  <div class="panel">{table(["Firm", "Fund", "Size", "Closed", "Focus", "Region"], rows)}</div>
  <h2>Dry-Powder Clock — Largest First</h2>
  <div class="panel">{table(["Fund", "Size", "Closed"], clock)}
  <p class="note">Deployment pace tracking (close date → first visible deals) is in the feature backlog — see the repo's FEATURES.md.</p></div>"""
    return page("Fresh Powder", "Newly closed VC funds: sizes, close dates, focus — the dry powder that has to find a home.", "funds", body, depth=1)

# ---------------- investors ----------------
def investors_page():
    leaders = sorted(inv_cnt.items(), key=lambda kv: (-kv[1], -inv_tot[kv[0]]))[:30]
    rows = [f'<tr><td>{n}</td><td>{c}</td><td class="amt">{money(inv_tot[n])}</td><td class="amt">{money(inv_tot[n]//c if c else 0)}</td></tr>' for n, c in leaders]
    body = f"""
  <h2>Herd Leaderboard</h2>
  <p class="h2sub">Most active firms in the window, by rounds appeared in (lead and participation combined, names cleaned). "Associated $" counts the full round size for every round a firm appears in — a presence measure, not a check measure.</p>
  <div class="panel">{table(["Investor", "Rounds", "Associated $", "Avg round"], rows)}</div>
  <div class="panel"><div class="big" style="font-size:21px;font-weight:700;font-family:'Playfair Display',Georgia,serif">Coming: Early Money vs Herd Money</div>
  <p style="color:var(--sub);font-size:14.5px;line-height:1.55">Per firm — did they arrive in a thesis wave before its peak, or only at it? The leaderboard this page grows into, once the archive wave peaks are joined with firm timestamps. It's in FEATURES.md, and it's the chart VC Twitter will argue about.</p></div>"""
    return page("Investors", "The most active VC firms this window — rounds, associated dollars, and the road to Early Money vs Herd Money.", "investors", body, depth=1)

# ---------------- exits ----------------
def exits_page():
    import collections
    by_type = collections.Counter(e["type"] for e in exits)
    priced = [e for e in exits if e["price"]]
    acq = [e for e in exits if e["type"] == "Acquisition"]
    acq_priced = [e for e in acq if e["price"]]
    undisclosed_pct = round(100 * (len(acq) - len(acq_priced)) / max(len(acq), 1))
    years = sorted({e["date"][:4] for e in exits})
    yrows = []
    for y in years:
        yy = [e for e in exits if e["date"][:4] == y]
        c = collections.Counter(e["type"] for e in yy)
        yrows.append(f'<tr><td>{y}</td><td class="amt">{c.get("Acquisition", 0)}</td><td class="amt">{c.get("IPO", 0)}</td><td class="amt">{c.get("Merger", 0)}</td><td class="amt">{c.get("Shutdown", 0)}</td><td class="amt">{len(yy)}</td></tr>')
    big_paid = sorted(priced, key=lambda e: -e["price"])[:6]
    paid_rows = [f'<tr><td>{e["date"]}</td><td>{e["company"]}</td><td>{e["type"]}</td><td>{e["acquirer"] or "—"}</td><td class="amt">{money(e["price"])}</td></tr>' for e in big_paid]
    shut = [e for e in exits if e["type"] == "Shutdown"]
    shut_rows = [f'<tr><td>{e["date"]}</td><td>{e["company"]}</td><td>Shutdown</td></tr>' for e in shut]
    sample = exits[:20]
    def srclink(e):
        if e.get("source_url"):
            return f'<a href="{e["source_url"]}" target="_blank" rel="noopener">{e.get("source_name") or "source"}</a>'
        return "—"
    sample_rows = [f'<tr><td>{e["date"]}</td><td>{e["company"]}</td><td>{e["type"]}</td><td>{e["acquirer"] or "—"}</td><td class="amt">{money(e["price"]) if e["price"] else "undisclosed"}</td><td>{srclink(e)}</td></tr>' for e in sample]
    tl_html = ""
    if throughline:
        CURATED = ["LinkedIn", "Spotify", "WeWork", "Time Warner", "Fitbit", "Product Hunt", "Delivery Hero", "Cloudera"]
        byname = {r["company"]: r for r in throughline["top"]}
        tlrows = []
        for nm in CURATED:
            r = byname.get(nm)
            if not r: continue
            tlrows.append(f'<tr><td>{r["company"]}</td><td>{r["first_mention"]}</td><td>{r["exit_date"]}</td><td>{r["type"]}</td><td>{r["acquirer"] or "—"}</td><td class="amt">{r["pre_mentions"]}</td></tr>')
        pct = round(100 * throughline["with_pre_mentions"] / max(throughline["exits_total"], 1))
        tl_html = f"""
  <h2>The Through Line</h2>
  <p style="line-height:1.65;font-size:15.5px">Did the newsletter watch them come in, too? For <b>{pct}%</b> of these {throughline['exits_total']} exits, yes — the company appears in the archive <i>before</i> its exit, in raise coverage, in roundups, in the herd's field of vision. The most-covered names before they left:</p>
  <div class="panel">{table(["Company", "First covered", "Exit", "Type", "Acquirer", "Pre-exit mentions"], tlrows)}</div>
  <p class="note">And the current window? Zero of today's 2026 rounds have exited — of course. They're this year's herd; the through line for them gets written over the next decade, and the join key now exists so this dataset accrues it automatically. Check back in five years.</p>"""
    body = f"""
  <h2>The Exit Door <span style="font-size:13px;vertical-align:middle" class="tagpill">Analysis free · Full ledger = Pro</span></h2>
  <p class="h2sub">Every lifecycle ends somewhere. Raises get announced with confetti; exits are where the money is actually divided. Mined from the StrictlyVC archive mirror (2013–2019 editions): {len(exits)} exit events, classified as they were reported.</p>
  {kpis([(str(len(exits)), "exit events logged"), (str(by_type.get('Acquisition', 0)), "acquisitions"), (str(by_type.get('IPO', 0)), "IPOs / filings"), (str(by_type.get('Shutdown', 0)), "shutdowns")])}
  <h2>Exits by Type</h2><div class="panel">{bars([(t, by_type[t]) for t in ("Acquisition", "IPO", "Merger", "Shutdown")])}</div>
  <p class="note">Mergers barely register ({by_type.get('Merger', 0)}): in startup-land the "merger of equals" is mostly a polite fiction — one side almost always acquired the other. IPOs include filings (some, famously, never priced).</p>
  <h2>Exits by Year</h2><div class="panel">{table(["Year", "Acquisitions", "IPOs / filings", "Mergers", "Shutdowns", "Total"], yrows)}</div>
  <h2>Who Got Paid</h2>
  <p style="line-height:1.65;font-size:15.5px">The cleanest money: an IPO, or an acquisition with a number attached. Only {len(priced)} of {len(exits)} exits in the archive carried a reported figure — and when the figure is good, they print it. The biggest reported paydays in the ledger:</p>
  <div class="panel">{table(["Date", "Company", "Type", "Acquirer", "Reported $"], paid_rows)}</div>
  <h2>Who Got Screwed</h2>
  <p style="line-height:1.65;font-size:15.5px">Two ways to lose. The loud way: shutdown — {len(shut)} in the archive, every dollar of preference stack worthless. The quiet way: an acquisition with <b>undisclosed terms</b> — {undisclosed_pct}% of acquisitions here. Undisclosed occasionally means "too big to say"; far more often it means acqui-hire math, where the team lands softly and the investors' stack does not. The number they won't print is the number that tells the story.</p>
  <div class="panel">{table(["Date", "Company", "Outcome"], shut_rows)}</div>
  {tl_html}
  <h2>Latest in the Ledger</h2><div class="panel">{table(["Date", "Company", "Type", "Acquirer", "Reported $", "Source"], sample_rows)}</div>
  <div class="panel"><b>The full Exit Ledger is a Pro feature.</b> All {len(exits)} events with per-exit payout classification (paid / soft landing / wiped out), acquirer rollups (which platforms buy the herd, and at what reported prices), and exit-vs-last-round analysis — the survivorship counterweight to everything else on this site. Aggregates and this analysis stay free.</div>
  <p class="note">Method: rule-based extraction over newsletter text; prices are figures reported in the same item (deal-adjacent numbers can slip in — verify against the linked source). Source links point to the original reporting the newsletter itself cited (TechCrunch, WSJ, Bloomberg, …), never to the newsletter. Shutdowns are hand-verified in context — the naive pattern also flags giants closing products (Facebook's Parse, AOL Instant Messenger); those are excluded. An exit is de-duplicated per company and type, dated to its first mention.</p>"""
    return page("Exits", "The Exit Door: acquisitions, IPOs, mergers and shutdowns — who got paid, who got screwed.", "exits", body, depth=1)

# ---------------- the herd (troll page) ----------------
def herd_page():
    ai_share = round(100 * len([r for r in rounds if r["sector"] == "AI / ML"]) / max(len(rounds), 1))
    body = f"""
  <h2>The Herd</h2>
  <p class="h2sub">Our correspondents in the field. Live, unbothered, and entirely uninterested in your term sheet.</p>
  <img src="../assets/herd.webp" alt="The herd, grazing — a woodcut engraving of twelve cows in a field, two of them judging you" style="width:100%;border-radius:18px;mix-blend-mode:multiply;display:block">
  <p class="note" style="text-align:center">THE HERD, AT GRAZE — Twelve head. The two in the centre have seen your pitch deck. (Staff engraving)</p>
  {kpis([("12", "head counted"), ("10", "currently grazing"), ("2", "judging you"), (f"{ai_share}%", "of rounds are AI — stampede in progress")])}
  <h2>Field Notes</h2>
  <div class="panel">{table(["Observation", "Reading"], [
      "<tr><td>Heads down, eating</td><td>Normal market. Capital is chewing.</td></tr>",
      "<tr><td>Heads up, staring</td><td>A new thesis has been spotted on the horizon.</td></tr>",
      "<tr><td>All heads turn the same way at once</td><td>Stampede imminent. See <a href='../trends/'>Trends</a>.</td></tr>",
      "<tr><td>The field is empty</td><td>Everyone exited. See <a href='../exits/'>The Exit Door</a>.</td></tr>",
      "<tr><td>One cow stands apart, alone</td><td>Contrarian. Either early or wrong; the archive will decide. See <a href='../trends/'>Thesis Archaeology</a>.</td></tr>",
  ])}</div>
  <p style="line-height:1.65;font-size:15.5px">The Herd is the control group for everything else on this site. The rounds, the funds, the stampedes into AI and out of cannabis — all of it is what the herd does when it stops grazing and starts running. The cows above have never raised a round, never missed payroll, and have correctly ignored every bubble since 2014 by the simple expedient of eating grass. We check on them weekly. They have never once checked on us.</p>
  <p class="note">No cows were consulted in the making of this publication. The masthead cow is proprietary. Please do not feed the investors.</p>"""
    return page("The Herd", "The herd, grazing. Twelve head, unbothered.", "herd", body, depth=1)

# ---------------- utility ----------------
def utility(slug, title, body_md):
    paras = "".join(f"<p style='line-height:1.65;font-size:15.5px'>{p}</p>" for p in body_md)
    return page(title, title, "", f"<h2>{title}</h2>{paras}", depth=1)

ABOUT = ["The Herd Tracker measures the venture herd: every funding round and fund close we can extract from free public sources, organised so the stampedes become visible — copycat clusters, theses that peak and die, and the firms that pile in together.",
         "It is an independent, bootstrapped data publication. It costs almost nothing to run (rule-based extraction, no paid APIs), and it is styled like a finance broadsheet on purpose: the numbers are the story."]
METHOD = ["Rounds are extracted with rule-based parsing (no LLMs, no paid APIs) from free, public sources: FinSMEs, TechCrunch, AlleyWatch, Pulse 2.0, EU-Startups, PR Newswire, BusinessWire and regional feeds, with SEC EDGAR Form D filings as the ground-truth layer. The historical archive is the StrictlyVC mirror (2013–2019), used for thesis-wave archaeology only.",
          "Facts (company, amount, stage, investors, dates) are extracted and re-summarised in our own words with links to the original source. Full text is never republished. Region tags are assigned only when a source or article states a headquarters city — never guessed — and coverage is printed wherever it is partial.",
          "Known caveats: announcement-based sources over-report raises and under-report deaths (survivorship bias — our Exit Door backlog item exists to counterweight it); associated-dollar figures on the Investors page measure presence in rounds, not checks written."]
PRIVACY = ["This site collects no personal data beyond standard, anonymised analytics (if enabled) and advertising cookies if and when Google AdSense is enabled. AdSense uses cookies to serve personalised ads; visitors in the EEA/UK will be shown a consent message where required.",
           "If you email us, your address is used only to reply. We do not sell personal data. This policy will be updated before any account, subscription or payment features launch."]
TERMS = ["Content is provided for general information only and is not investment advice. Figures are as reported by their original sources and may contain extraction errors; verify against the linked source before acting on any number.",
         "You may quote figures with attribution and a link. Bulk scraping of this site's compiled datasets is not permitted; CSV export is provided on the Rounds page for personal use."]
CONTACT = ["Sponsorship, data licensing, corrections and tips: amritpd@gmail.com. Corrections are valued — the graveyard is only useful if the dates on the tombstones are right."]

# ---------------- build ----------------
def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
    open(full, "w").write(content)
    print("wrote", full, f"({len(content)//1024} KB)")

if __name__ == "__main__":
    CSS = load_css()
    pages = {
        "index.html": front_page(),
        "trends/index.html": trends_page(),
        "regions/index.html": regions_page(),
        "rounds/index.html": rounds_page(),
        "fresh-powder/index.html": funds_page(),
        "investors/index.html": investors_page(),
        "exits/index.html": exits_page(),
        "herd/index.html": herd_page(),
        "about/index.html": utility("about", "About", ABOUT),
        "methodology/index.html": utility("methodology", "Methodology & Sources", METHOD),
        "privacy/index.html": utility("privacy", "Privacy Policy", PRIVACY),
        "terms/index.html": utility("terms", "Terms", TERMS),
        "contact/index.html": utility("contact", "Contact", CONTACT),
        "404.html": page("404 — Left the Herd", "This page has left the herd.", "", """
  <div style="text-align:center;padding:26px 0">
    <img src="/herdtracker/assets/cow-256.webp" alt="The Herd Tracker cow" style="height:150px;border-radius:18px;mix-blend-mode:multiply">
    <h2>This page has left the herd.</h2>
    <p style="font-size:15.5px;line-height:1.65">It either never existed, or it exited — in which case it is in <a href="/herdtracker/exits/">The Exit Door</a>, probably with undisclosed terms.</p>
    <p><a href="/herdtracker/">← Back to the Front Page</a></p>
  </div>""", depth=0),
    }
    for path, content in pages.items():
        write(path, content)
    write("robots.txt", "User-agent: *\nAllow: /\n")
    write("ads.txt", "# ads.txt — replace with the real line after AdSense approval:\n# google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0\n")
    write("sitemap.txt", "\n".join("/" + p.replace("index.html", "") for p in pages) + "\n# Set BASE_URL in build_site.py and regenerate for sitemap.xml once the domain is live.\n")
    if BASE_URL:
        urls = "".join(f"<url><loc>{BASE_URL}/" + p.replace("index.html", "") + "</loc></url>" for p in pages)
        write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    print(f"\n{len(pages)} pages · window {WINDOW} · region coverage {rstats}")
    import shutil as _sh
    _sh.copytree("assets", os.path.join(OUT, "assets"), dirs_exist_ok=True)
    # GitHub Pages branch deploy only serves /(root) or /docs — mirror site/ into docs/
    import shutil
    if os.path.exists("docs"): shutil.rmtree("docs")
    shutil.copytree(OUT, "docs")
    print("mirrored site/ -> docs/ for GitHub Pages")
