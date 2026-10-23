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
"""

CSS = None
def page(title, desc, active, body, depth=0, extra_head="", cow=False):
    p = "../" * depth
    nav_items = [("Front Page", f"{p}index.html", "front"),
                 ("Trends", f"{p}trends/", "trends"),
                 ("Regions", f"{p}regions/", "regions"),
                 ("Rounds", f"{p}rounds/", "rounds"),
                 ("Fresh Powder", f"{p}fresh-powder/", "funds"),
                 ("Investors", f"{p}investors/", "investors")]
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
    body = f"""
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
        "about/index.html": utility("about", "About", ABOUT),
        "methodology/index.html": utility("methodology", "Methodology & Sources", METHOD),
        "privacy/index.html": utility("privacy", "Privacy Policy", PRIVACY),
        "terms/index.html": utility("terms", "Terms", TERMS),
        "contact/index.html": utility("contact", "Contact", CONTACT),
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
