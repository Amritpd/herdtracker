"""Keyword-wave analysis on the FULL StrictlyVC mirror (2013-2019) vs 2026 Finsmes posts."""
import json, os, re, html, gzip, glob
from collections import defaultdict

BASE = os.path.expanduser("~/workspace/herd-tracker")

def edition_year(title):
    t = title.get("rendered", "") if isinstance(title, dict) else str(title)
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(20\d\d)", t)
    return int(m.group(2)) if m else None

def clean(content):
    c = content.get("rendered", "") if isinstance(content, dict) else str(content)
    c = re.sub(r"<[^>]+>", " ", c)
    return html.unescape(c).lower()

KEYWORDS = {
    "Artificial intelligence": r"artificial intelligence|\bai\b|machine learning",
    "Crypto / blockchain": r"blockchain|crypto|bitcoin|web3",
    "Fintech": r"fintech|neobank|digital bank",
    "Cybersecurity": r"cyber\s?security|infosec",
    "Robotics": r"\brobot",
    "Cannabis": r"cannabis|marijuana|\bcbd\b",
    "Autonomous vehicles": r"self-driving|autonomous vehicle|autonomous driving",
    "Space / rockets": r"rocket|satellite|orbital|spacex",
    "Gene editing / biotech": r"crispr|gene editing|gene therapy",
    "Plant-based food": r"plant-based|plant based|impossible foods|beyond meat",
    "Scooters / micromobility": r"scooter|micromobility",
    "Quantum": r"\bquantum\b",
}
YEARS = [2014, 2017, 2019]

editions = defaultdict(list)
for f in sorted(glob.glob(f"{BASE}/raw/svc_full/page-*.json.gz")):
    for p in json.load(gzip.open(f, "rt")):
        y = edition_year(p.get("title", {}))
        if y: editions[y].append(clean(p.get("content", "")))
print("editions by year:", {y: len(v) for y, v in sorted(editions.items())})

rtext = []
for p in json.load(open(f"{BASE}/raw/finsmes.json")):
    t = p.get("title", {})
    t = t.get("rendered", "") if isinstance(t, dict) else str(t)
    rtext.append((t + " " + clean(p.get("content", ""))))

rows = []
for name, pat in KEYWORDS.items():
    rx = re.compile(pat)
    row = {"name": name}
    for y in YEARS:
        texts = editions.get(y, [])
        hits = sum(1 for t in texts if rx.search(t))
        row[f"n{y}"] = hits; row[f"N{y}"] = len(texts)
        row[f"p{y}"] = round(100 * hits / len(texts)) if texts else 0
    hits26 = sum(1 for t in rtext if rx.search(t))
    row["n2026"] = hits26; row["N2026"] = len(rtext)
    row["p2026"] = round(100 * hits26 / len(rtext))
    rows.append(row)

rows.sort(key=lambda r: -r["p2019"])
out = {"keywords": rows,
       "editions": {str(y): len(v) for y, v in sorted(editions.items())},
       "posts2026": len(rtext)}
json.dump(out, open(f"{BASE}/archive.json", "w"), indent=1)
for r in rows:
    print(f"{r['name']:26s} 2014: {r['p2014']:3d}%  2017: {r['p2017']:3d}%  2019: {r['p2019']:3d}%  2026: {r['p2026']:3d}%")
