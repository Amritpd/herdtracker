#!/usr/bin/env python3
"""Regional source extractor — EU-Startups (Europe), Inc42 (India/APAC), e27 (SE Asia/APAC).

Why this exists (Oct 23, 2026): the FinSMEs-only snapshot tags just 160/383 rounds
by region and skews American. These sources are region-NATIVE — every round they
produce carries its region by construction, which completes the regional editions
(FEATURES.md section 0, signal 1) without any guessing.

Method: WordPress APIs (EU-Startups, Inc42) + RSS (e27), title-first rule-based
extraction in the same style as extract.py (sector/stage classifiers adapted
from it). Multi-currency amounts normalised to USD with rough Oct-2026 rates
below — original display string is kept alongside.

Outputs: rounds_regional.json, funds_regional.json (merged by build_site.py).
Run: python3 extract_regional.py
"""
import json, re, html, urllib.request, xml.etree.ElementTree as ET
from region import CITY_REGION

FX = {"€": 1.08, "EUR": 1.08, "$": 1.0, "USD": 1.0, "£": 1.27, "GBP": 1.27, "₹": 1/83, "INR": 1/83}
SKIP = re.compile(r"podcast|sponsored|webinar|conference|top \d+|ipo|shares (plunge|fall|rise)|layoff|report:|opinion|how to|why ", re.I)

SECTORS = [
    ("AI / ML", r"\b(AI|artificial intelligence|machine learning|LLM|generative|agentic)\b"),
    ("Cybersecurity", r"\b(cyber|security|threat|fraud|identity)\b"),
    ("Fintech", r"\b(fintech|payment|banking|lending|insurance|insurtech|wealth|trading)\b"),
    ("Crypto / Web3", r"\b(crypto|blockchain|web3|token|defi|nft)\b"),
    ("Health / Bio", r"\b(health|biotech|medical|clinical|therap|drug|pharma|patient|diagnostic)\b"),
    ("Climate / Energy", r"\b(climate|energy|solar|battery|carbon|ev|electric|hydrogen|sustainab)\b"),
    ("Robotics / Hardware", r"\b(robot|drone|hardware|sensor|semiconductor|chip)\b"),
    ("Space / Defense", r"\b(space|satellite|defense|defence|aerospace|drones for)\b"),
    ("SaaS / Enterprise", r"\b(SaaS|enterprise|workflow|productivity|CRM|platform)\b"),
    ("DevTools", r"\b(developer|devtool|api|open-source|open source|infrastructure)\b"),
    ("Legal", r"\b(legal|law|compliance|regulatory)\b"),
    ("Consumer", r"\b(consumer|e-?commerce|retail|fashion|beauty|gaming|marketplace|food delivery|brand)\b"),
    ("EdTech", r"\b(education|learning|edtech|student|teacher|school)\b"),
    ("Real Estate", r"\b(real estate|proptech|property|construction|housing)\b"),
]
def sector_of(text):
    for name, pat in SECTORS:
        if re.search(pat, text, re.I):
            return name
    return "Other"

def stage_of(text):
    m = re.search(r"Series ([A-F])", text, re.I)
    if m: return "Series " + m.group(1).upper()
    for s in ("Pre-Seed", "Seed", "Growth", "Debt", "Grant", "Venture", "Strategic"):
        if re.search(rf"\b{s}\b", text, re.I): return s.title()
    return "Undisclosed"

MONEY_RE = re.compile(
    r"(€|\$|£|₹|EUR|USD|GBP|INR|Rs\.?)\s*([\d,]+(?:\.\d+)?)\s*(million|billion|crore|cr|lakh|mn|bn|m|b|k)?", re.I)
def parse_money(text):
    m = MONEY_RE.search(text or "")
    if not m: return 0, ""
    cur, num, unit = m.group(1), float(m.group(2).replace(",", "")), (m.group(3) or "").lower()
    rate = FX.get(cur, FX.get(cur.upper(), 1.0))
    if unit in ("crore", "cr"): usd = num * 1e7 * rate if cur in ("₹", "INR", "Rs", "Rs.") else num * 1e7
    elif unit == "lakh": usd = num * 1e5 * rate
    elif unit.startswith("b"): usd = num * 1e9 * rate
    elif unit.startswith("m"): usd = num * 1e6 * rate
    elif unit == "k": usd = num * 1e3 * rate
    else: usd = num * rate
    return round(usd), m.group(0)

def clean(t):
    t = html.unescape(t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

TITLE_RE = re.compile(
    r"^(?:([A-Z][A-Za-zÀ-ÿ]+)(?:'s|’s)\s+)?(.{2,45}?)\s+(?:raises|raised|secures|secured|bags|closes|closed|gets|lands|snags|rakes in|completes)\b", re.I)

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 HerdTracker"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())

def wp_posts(base, search=None, per_page=50):
    url = f"{base}/wp-json/wp/v2/posts?per_page={per_page}&_fields=date,link,title,excerpt"
    if search: url += f"&search={urllib.parse.quote(search)}"
    return fetch_json(url)

import urllib.parse
def process(posts, source, region):
    rounds, funds = [], []
    for p in posts:
        title = clean(p["title"]["rendered"] if isinstance(p.get("title"), dict) else p.get("title", ""))
        if SKIP.search(title): continue
        m = TITLE_RE.match(title)
        if not m: continue
        city_tok, company = (m.group(1) or "").lower(), m.group(2).strip(" -")
        company = re.sub(r"^(Spanish|Portuguese|German|French|Indian|Singapore-based|Amsterdam-based|London-based|Berlin-based)\s+", "", company)
        company = re.sub(r"^\[Update\]\s+", "", company)
        company = re.sub(r"^[A-Z][A-Za-zÀ-ÿ]+-based\s+", "", company)  # "Eindhoven-based Photon Bridge"
        company = re.sub(r"^(EdTech|Fintech|FinTech|HealthTech|Healthtech|AI|Insurtech|Proptech|Foodtech)\s+(?=[A-Z])", "", company)
        company = re.sub(r"^VC\s+", "", company)  # fund firm names: "VC Seaya" -> "Seaya"
        excerpt = clean(p.get("excerpt", {}).get("rendered", "") if isinstance(p.get("excerpt"), dict) else p.get("excerpt", ""))
        amt, disp = parse_money(title + " " + excerpt[:200])
        if not amt: continue
        date = (p.get("date") or "")[:10]
        url = p.get("link", "")
        low = title.lower()
        is_fund = ("fund" in low and any(w in low for w in ("vc", "venture", "capital", "new fund", "fund i", "fund v", "fund x"))) or "closes new fund" in low
        if is_fund:
            funds.append({"firm": company, "fund": "New fund (see source)", "amount": amt,
                          "display": disp, "date": date, "focus": title, "source": source, "url": url,
                          "region": region})
        else:
            rounds.append({"company": company, "amount": amt, "date": date,
                           "stage": stage_of(title + " " + excerpt), "sector": sector_of(title + " " + excerpt),
                           "location": "", "investors": [], "desc": city_tok if city_tok in CITY_REGION else "",
                           "url": url, "source": source, "region": region,
                           "city": city_tok if city_tok in CITY_REGION else ""})
    return rounds, funds

def rss_items(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 HerdTracker"})
    with urllib.request.urlopen(req, timeout=25) as r:
        root = ET.fromstring(r.read())
    out = []
    from email.utils import parsedate
    for it in root.findall(".//item"):
        pd = parsedate(it.findtext("pubDate", "") or "")
        iso = f"{pd[0]:04d}-{pd[1]:02d}-{pd[2]:02d}" if pd else ""
        out.append({"title": {"rendered": it.findtext("title", "")},
                    "excerpt": {"rendered": it.findtext("description", "")},
                    "link": it.findtext("link", ""), "date": iso})
    return out

if __name__ == "__main__":
    all_rounds, all_funds = [], []
    jobs = []
    try:
        jobs.append(("EU-Startups", "Europe", wp_posts("https://www.eu-startups.com", search="raises")))
        jobs.append(("EU-Startups", "Europe", wp_posts("https://www.eu-startups.com", search="funding")))
    except Exception as e: print("EU-Startups FAIL", e)
    try:
        jobs.append(("Inc42", "APAC", wp_posts("https://inc42.com", search="funding")))
        jobs.append(("Inc42", "APAC", wp_posts("https://inc42.com", search="raises")))
    except Exception as e: print("Inc42 FAIL", e)
    try:
        jobs.append(("e27", "APAC", rss_items("https://e27.co/feed")))
    except Exception as e: print("e27 FAIL", e)

    seen = set()
    for source, region, posts in jobs:
        rs, fs = process(posts, source, region)
        for r in rs:
            key = r["company"].lower()
            if key not in seen:
                seen.add(key); all_rounds.append(r)
        for f in fs:
            key = f["firm"].lower()
            if key not in seen:
                seen.add(key); all_funds.append(f)
        print(f"{source}: +{len(rs)} rounds, +{len(fs)} funds from this pull")
    all_rounds.sort(key=lambda r: r["date"], reverse=True)
    json.dump(all_rounds, open("rounds_regional.json", "w"), indent=1)
    json.dump(all_funds, open("funds_regional.json", "w"), indent=1)
    from collections import Counter
    print("\nTOTAL regional rounds:", len(all_rounds), Counter(r["region"] for r in all_rounds), Counter(r["source"] for r in all_rounds))
    print("TOTAL regional funds:", len(all_funds))
    for r in all_rounds[:12]:
        print(f"  {r['date']}  {r['company'][:34]:34s} ${r['amount']/1e6:7.1f}M  {r['stage']:11s} {r['sector']:18s} {r['source']}")
    for f in all_funds[:6]:
        print(f"  FUND {f['date']}  {f['firm'][:34]:34s} {f['display']}  {f['source']}")
