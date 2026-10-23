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

SECTION_PREFIXES = ("Top News", "Essential Reads", "Exits", "Data", "People", "Meanwhile", "Sponsored By")
def strip_section(name):
    if not name: return name
    if " " in name and name.split()[0].endswith("-based"):
        name = name.split(" ", 1)[1]
    changed = True
    while changed:
        changed = False
        for p in SECTION_PREFIXES:
            if name.startswith(p + " "):
                name = name[len(p) + 1:]; changed = True
    return name

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
    ("Shutdown", re.compile(CAP + r"(?:, [^,.]{0,60},)? (?:is shutting down|has shut down|shuts down|will shut down|is winding down|has ceased operations|ceased operations|closed its doors|is closing its doors)(?! its| the| a | an )")),
    ("Shutdown", re.compile(r"(?:the )?(?:shutdown|closure|demise) of " + CAP)),
    ("Bankruptcy", re.compile(CAP + r" (?:filed|files|filing) for (?:Chapter 11 |Chapter 7 )?bankruptcy")),
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
            company = strip_section(company.strip(" ,."))
            if acquirer: acquirer = strip_section(acquirer.strip(" ,."))
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
            PUBLIC_CO = {"Facebook", "Yahoo", "AOL", "CNN", "Adobe", "Coca-Cola", "Reddit", "Google",
                         "Apple", "Amazon", "Microsoft", "Twitter", "Samsung", "IBM", "Oracle", "Cisco",
                         "Netflix", "Disney", "Verizon", "Time Warner", "Uber", "Airbnb", "LinkedIn", "Uber"}
            if typ in ("Shutdown", "Bankruptcy") and company in PUBLIC_CO: continue
            if typ == "Bankruptcy": typ = "Shutdown"
            if ". " in company or (acquirer and ". " in acquirer): continue
            if "Exits" in company or (acquirer and "Exits" in acquirer): continue
            if not company_ok(company): continue
            key = (company.lower(), typ)
            if key in seen: continue
            seen.add(key)
            exits.append({"date": date, "company": company, "type": typ,
                          "acquirer": acquirer, "price": price,
                          "edition": title, "url": p["link"]})

# ---- shutdown sentence pass (StrictlyVC house style: "X , a four-year-old,
# City-based startup, is shutting down") + hand-verified extras ----
SENT_PATS = [
    re.compile(CAP + r"\s*, (?:a|an|the) [^,]{4,90}, (?:is shutting down|is closing|is winding down|has shut down|shut down)"),
    re.compile(CAP + r"\s*, which [^,]{4,90}, is (?:shutting down|closing)"),
    re.compile(CAP + r"\s*, which later shut down"),
]
DROP_SHUTDOWN = {"Top News Facebook", "CNN", "AOL", "Coca-Cola", "Facebook", "Reddit", "Adobe",
                 "Yahoo", "Singer Kanye West", "Supernova", "Yes", "Loom", "November", "Cent", "Uber",
                 "New Funds BBVA", "BBVA", "Ola", "Theranos", "IDG Capital"}
have_shut = {e["company"].lower() for e in exits if e["type"] == "Shutdown"}
for p in posts:
    text2 = clean_text(p["content"]["rendered"] if isinstance(p.get("content"), dict) else "")
    for s in re.split(r"(?<=[.!?])\s+", text2):
        if not re.search(r"shut|clos|wind", s, re.I):
            continue
        for pat in SENT_PATS:
            m = pat.search(s)
            if not m:
                continue
            nm = strip_section(m.group(1).strip(" ,."))
            if nm in DROP_SHUTDOWN or not company_ok(nm) or nm.lower() in have_shut:
                break
            if re.search(r"shut(?:ting|s)? down (?:its|the) (?:[A-Z][\w]+ )?(app|apps|section|program|incubator|feature|initiative|group)\\b", s, re.I):
                break
            have_shut.add(nm.lower())
            exits.append({"date": p["date"][:10], "company": nm, "type": "Shutdown",
                          "acquirer": None, "price": None,
                          "edition": p["title"]["rendered"] if isinstance(p.get("title"), dict) else "",
                          "url": p["link"]})
            break

VERIFIED_EXTRA = ["Shyp", "LittleThings", "Chorus", "New Matter", "Primary Data", "Lumoid",
                  "TechShop", "Mingbike", "Doppler Labs", "Teforia", "Atlas Informatics", "Jinn",
                  "FatWallet", "Lantern", "Aerosoles", "Takata"]
for nm in VERIFIED_EXTRA:
    if nm.lower() in have_shut:
        continue
    for p in posts:
        body = clean_text(p["content"]["rendered"] if isinstance(p.get("content"), dict) else "")
        if nm in body and re.search(r"shut|bankrupt|winding down", body, re.I):
            exits.append({"date": p["date"][:10], "company": nm, "type": "Shutdown",
                          "acquirer": None, "price": None,
                          "edition": p["title"]["rendered"] if isinstance(p.get("title"), dict) else "",
                          "url": p["link"]})
            have_shut.add(nm.lower())
            break

COMPANY_DENY = {"New York", "San Francisco-based", "San Francisco", "Austin", "Cambridge",
                "Germany", "London", "Berlin", "Paris", "Boston", "Seattle", "Toronto",
                "Chicago", "Los Angeles", "Silicon Valley", "China", "India", "Europe",
                "Israel", "Canada", "France", "Japan", "Australia", "Singapore", "California"}
PAIR_DENY = {("Uber", "IPO"), ("Lyft", "Acquisition"), ("Uber", "Shutdown"),
             ("Nest", "Acquisition"), ("Skype", "Acquisition"),
             ("Third Rock Ventures", "IPO"), ("Workday", "IPO")}
COMPANY_DENY |= {"French", "Russian", "German", "British", "Chinese", "Japanese", "Indian",
                 "Best", "Oakland", "Calif", "Korea", "Redwood City", "Tel Aviv", "Palo Alto", "Mountain View", "Menlo Park",
                 "Sunnyvale", "San Jose", "San Mateo", "Brooklyn", "Washington", "Denver",
                 "Atlanta", "Miami", "Dallas", "Houston", "Portland", "Vancouver"}
exits = [e for e in exits if e["company"] not in COMPANY_DENY and not e["company"].endswith("-based") and (e["company"], e["type"]) not in PAIR_DENY]
exits = [e for e in exits if not (e["type"] == "Shutdown" and e["company"] in DROP_SHUTDOWN)]
# resolve original sources from edition HTML chunks
from urllib.parse import urlparse
posts_by_link = {p["link"]: p for p in posts}
def chunk_sources(raw_html):
    chunks = re.split(r"</?(?:p|li|h\d)[^>]*>", raw_html or "")
    out = []
    for c in chunks:
        hrefs = [h for h in re.findall(r'href="(https?://[^"]+)"', c)
                 if "strictlyvc.com" not in h and "wp-content" not in h and "gravatar" not in h]
        out.append((clean_text(c), hrefs))
    return out
for e in exits:
    e["source_url"], e["source_name"] = None, None
    p = posts_by_link.get(e["url"])
    if not p:
        continue
    raw = p["content"]["rendered"] if isinstance(p.get("content"), dict) else ""
    chunks = chunk_sources(raw)
    name_full = e["company"].lower()
    scored = []
    for ci, (txt, hrefs) in enumerate(chunks):
        if not hrefs or name_full not in txt.lower():
            continue
        tl = txt.lower()
        score = (2 if re.search(r"acquir|shut|ipo|merger|bankrupt", tl) else 0) + (1 if "more here" in tl else 0)
        scored.append((score, ci, hrefs[0]))
    best = None
    if scored:
        scored.sort(key=lambda t: (-t[0], t[1]))
        if scored[0][0] >= 2:
            best = scored[0][2]
    if best:
        e["source_url"] = best
        host = urlparse(best).netloc.replace("www.", "")
        e["source_name"] = {"techcrunch.com": "TechCrunch", "wsj.com": "WSJ", "nytimes.com": "NYT",
                             "bloomberg.com": "Bloomberg", "axios.com": "Axios", "venturebeat.com": "VentureBeat",
                             "recode.net": "Recode", "theverge.com": "The Verge", "wired.com": "Wired",
                             "forbes.com": "Forbes", "businessinsider.com": "Business Insider",
                             "cnbc.com": "CNBC", "reuters.com": "Reuters", "ft.com": "FT"}.get(host, host)

exits.sort(key=lambda e: e["date"], reverse=True)
json.dump(exits, open("exits.json", "w"), indent=1)
resolved = sum(1 for e in exits if e["source_url"])
print(f"source links resolved: {resolved}/{len(exits)}")
import collections
print("exits:", len(exits))
print("by type:", dict(collections.Counter(e["type"] for e in exits)))
print("by year:", dict(sorted(collections.Counter(e["date"][:4] for e in exits).items())))
print("with price:", sum(1 for e in exits if e["price"]))
for e in exits[:12]:
    print(" ", e["date"], e["type"], e["company"], "->", e["acquirer"], e["price"])
