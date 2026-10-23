"""Year-by-year sector attention series from the full StrictlyVC mirror.
Method (same spirit as the checkpoint analysis, now every year):
- Edition year parsed from the edition TITLE when present (post 'date'
  fields are migration artifacts for some 2019 editions).
- raw_share[sector][year] = % of that year's editions mentioning the sector.
- mix[sector][year] = sector's share of all sector-tagged mentions (sums 100).
- rounds2026 = sector share of the current rounds window, by count."""
import gzip, glob, json, re, html as H

SECTORS = {
    "AI / ML": [r"artificial intelligence", r"machine learning", r"deep learning", r"neural net", r"generative ai", r"\bai startup"],
    "Fintech": [r"fintech", r"insurtech", r"neobank", r"payments startup", r"lending platform"],
    "Crypto / Web3": [r"bitcoin", r"cryptocurrenc", r"blockchain", r"ethereum", r"\bico\b", r"web3"],
    "Cannabis": [r"cannabis", r"marijuana"],
    "Health / Bio": [r"biotech", r"digital health", r"therapeutics", r"genom", r"telemedicine", r"healthtech"],
    "SaaS / Enterprise": [r"\bsaas\b", r"enterprise software"],
    "Consumer / E-comm": [r"e-commerce", r"ecommerce", r"direct-to-consumer", r"\bd2c\b", r"marketplace"],
    "Mobility": [r"self-driving", r"autonomous vehicle", r"ride-hailing", r"ridesharing", r"electric vehicle", r"\bev startup"],
    "Climate / Energy": [r"cleantech", r"solar", r"climate tech", r"renewable", r"carbon capture"],
    "Cybersecurity": [r"cybersecurity", r"information security", r"security startup"],
    "Robotics / Hardware": [r"\brobot", r"\bdrone", r"3d print"],
    "EdTech": [r"edtech", r"education startup", r"learning platform"],
    "Food / AgTech": [r"food delivery", r"meal kit", r"agtech", r"grocery delivery"],
    "PropTech": [r"proptech", r"real estate startup", r"mortgage startup"],
    "Media / Social": [r"social network", r"streaming", r"podcast", r"media startup"],
    "Quantum": [r"quantum"],
    "Space": [r"space startup", r"\brocket", r"satellite", r"spacex"],
    "DevTools / Infra": [r"developer tool", r"devops", r"open source"],
}
PATS = {s: [re.compile(p, re.I) for p in ps] for s, ps in SECTORS.items()}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}

def edition_year(p):
    title = p["title"]["rendered"] if isinstance(p.get("title"), dict) else p.get("title", "")
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(20\d{2})", title, re.I)
    if m:
        return int(m.group(2))
    return int(p["date"][:4])

posts = []
for f in sorted(glob.glob("raw/svc_full/page-*.json.gz")):
    posts += json.load(gzip.open(f, "rt", encoding="utf-8"))

def clean(raw):
    t = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", H.unescape(t))

years = list(range(2013, 2020))
editions = {y: 0 for y in years}
hits = {s: {y: 0 for y in years} for s in SECTORS}
for p in posts:
    y = edition_year(p)
    if y not in editions:
        continue
    editions[y] += 1
    txt = clean(p["content"]["rendered"] if isinstance(p.get("content"), dict) else "")
    for s, ps in PATS.items():
        if any(pat.search(txt) for pat in ps):
            hits[s][y] += 1

raw_share = {s: {y: round(100 * hits[s][y] / editions[y], 1) if editions[y] else 0 for y in years} for s in SECTORS}
tot_by_year = {y: sum(hits[s][y] for s in SECTORS) for y in years}
mix = {s: {y: round(100 * hits[s][y] / tot_by_year[y], 1) if tot_by_year[y] else 0 for y in years} for s in SECTORS}

rounds = json.load(open("rounds.json"))
try:
    rounds += json.load(open("rounds_regional.json"))
except FileNotFoundError:
    pass
import collections
rc = collections.Counter(r["sector"] for r in rounds)
rounds2026 = {s: round(100 * c / len(rounds), 1) for s, c in rc.most_common()}

out = {"years": years, "editions": editions, "raw_share": raw_share, "mix": mix,
       "rounds2026_by_count": rounds2026, "rounds_total": len(rounds)}
json.dump(out, open("trends_yearly.json", "w"), indent=1)
print("editions per year:", editions)
for s in ("AI / ML", "Fintech", "Crypto / Web3", "Cannabis", "Quantum"):
    print(f"{s}: raw% {[raw_share[s][y] for y in years]} · mix% {[mix[s][y] for y in years]}")
print("sectors:", len(SECTORS), "· rounds2026:", rounds2026)
