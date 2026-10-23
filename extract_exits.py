"""Extract exit events (acquisitions, IPOs, mergers, shutdowns) from the
StrictlyVC archive mirror (raw/svc_full). Rule-based, $0.

StrictlyVC newsletters are upstream-aggregated facts; we store the fact
(company, exit type, acquirer, price when stated, date) + a link back to
the edition, never the newsletter text itself beyond a short headline
fragment used as evidence.
"""
import gzip, glob, json, re, html as htmllib

posts = []
for f in sorted(glob.glob("raw/svc_full/page-*.json.gz")):
    posts += json.load(gzip.open(f, "rt", encoding="utf-8"))
posts.sort(key=lambda p: p["date"])

def clean_text(raw):
    t = re.sub(r"<[^>]+>", " ", raw or "")
    t = htmllib.unescape(t)
    return re.sub(r"\s+", " ", t).strip()

STOP_START = {"The", "A", "An", "This", "That", "It", "In", "On", "At", "And", "But",
              "Meanwhile", "Also", "Plus", "We", "He", "She", "They", "One", "Two",
              "First", "Last", "Next", "Today", "Yesterday", "Tomorrow", "Here", "There"}

def company_ok(name):
    if not name or len(name) < 2 or len(name) > 45: return False
    first = name.split()[0].strip(",.")
    if first in STOP_START: return False
    if not re.search(r"[A-Za-z]", name): return False
    if re.search(r"\b(says|said|will|would|has|have|is|are|was|were|the|and|for|with)\b", name): return False
    return True

CAP = r"([A-Z][A-Za-z0-9&.\-]*(?: [A-Z][A-Za-z0-9&.\-]*){0,3})"
PRICE = r"(?: for (?:about |roughly |nearly )?\$([\d.]+)\s*(billion|million|B|M)\b)?"

PATTERNS = [
    ("Acquisition", re.compile(CAP + r"(?:, [^,.]{0,40},)? (?:has been|is being|was|will be) acquired by " + CAP + PRICE)),
    ("Acquisition", re.compile(CAP + r" (?:is acquiring|has acquired|acquired|is buying|to acquire|to buy) " + CAP + PRICE)),
    ("Acquisition", re.compile(CAP + r" (?:announced|announces) (?:its |the )?acquisition of " + CAP + PRICE)),
    ("IPO", re.compile(CAP + r" (?:files|filed) (?:to go public|for (?:an |its )?IPO|its S-1)")),
    ("IPO", re.compile(CAP + r"(?:'s| priced its| made its| will make its| shares (?:rose|surged|jumped) in its) (?:IPO|public (?:debut|offering))")),
    ("IPO", re.compile(CAP + r" (?:goes public|went public|began trading|starts trading)")),
    ("Merger", re.compile(CAP + r" (?:and|&) " + CAP + r" (?:are merging|have merged|announced a merger|to merge)")),
    ("Shutdown", re.compile(CAP + r" (?:is shutting down|has shut down|shuts down|is closing down|will shut down)")),
]

def price_usd(num, unit):
    if not num: return None
    v = float(num)
    return int(v * (1e9 if unit.lower().startswith("b") else 1e6))

exits, seen = [], set()
for p in posts:
    date = p["date"][:10]
    if date < "2013-06-01": continue
    text = clean_text(p["content"]["rendered"] if isinstance(p.get("content"), dict) else "")
    title = p["title"]["rendered"] if isinstance(p.get("title"), dict) else p.get("title", "")
    for typ, pat in PATTERNS:
        for m in pat.finditer(text):
            g = m.groups()
            if typ == "Acquisition" and len(g) >= 2 and pat.pattern.count("acquir") and "acquired by" in pat.pattern:
                company, acquirer = g[0], g[1]
                price = price_usd(g[2], g[3]) if len(g) > 3 else None
            elif typ == "Acquisition" and len(g) >= 2:
                # "X is acquiring Y" form: acquirer first
                acquirer, company = g[0], g[1]
                price = price_usd(g[2], g[3]) if len(g) > 3 else None
            elif typ == "Merger":
                company, acquirer, price = g[0], g[1], None
            else:
                company, acquirer, price = g[0], None, None
            company = company.strip(" ,.")
            if acquirer: acquirer = acquirer.strip(" ,.")
            for nm in ("company", "acquirer"):
                v = locals()[nm]
                if v and v.startswith("Exits "): v = v[6:]
                if nm == "company": company = v
                else: acquirer = v
            if typ == "IPO" and company in {"Amazon", "Google", "Facebook", "Apple", "Microsoft", "Alphabet", "Netflix"}:
                continue
            if price is None:
                win = text[m.start():m.end() + 160]
                pm = re.search(r"\$([\d.]+)\s*(billion|million)\b", win)
                if pm: price = price_usd(pm.group(1), pm.group(2))
            if company == "Exits" or acquirer == "Exits": continue
            if ". " in company or (acquirer and ". " in acquirer): continue
            if "Exits" in company or (acquirer and "Exits" in acquirer): continue
            if not company_ok(company): continue
            key = (company.lower(), typ)
            if key in seen: continue
            seen.add(key)
            exits.append({"date": date, "company": company, "type": typ,
                          "acquirer": acquirer, "price": price,
                          "edition": title, "url": p["link"]})

exits.sort(key=lambda e: e["date"], reverse=True)
json.dump(exits, open("exits.json", "w"), indent=1)
import collections
print("exits:", len(exits))
print("by type:", dict(collections.Counter(e["type"] for e in exits)))
print("by year:", dict(sorted(collections.Counter(e["date"][:4] for e in exits).items())))
print("with price:", sum(1 for e in exits if e["price"]))
for e in exits[:12]:
    print(" ", e["date"], e["type"], e["company"], "->", e["acquirer"], e["price"])
