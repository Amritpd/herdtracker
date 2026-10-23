"""Strict fund-raise extraction: the object must be a fund vehicle, not 'funding'."""
import json, re, html, os, urllib.request

BASE = os.path.expanduser("~/workspace/herd-tracker")
HDR = {"User-Agent": "Mozilla/5.0 (HerdTracker research)"}

def get(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def clean(t):
    t = html.unescape(t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def money(num, unit):
    v = float(num.replace(",", ""))
    return v * (1e9 if unit.lower().startswith("b") else 1e6)

M = r"\$([\d,]+(?:\.\d+)?)\s*(million|billion)"
PATTERNS = [
    re.compile(r"([A-Z][\w&.]*(?:\s+[A-Z][\w&.]+){0,3})\s+(?:has\s+)?(?:closed|raised|announced|launched)\s+(?:a\s+|its\s+|an\s+|their\s+)?(?:new\s+)?" + M + r"\s+(?:[a-z]+\s+){0,2}?fund\b(?!ing)", re.I),
    re.compile(r"([A-Z][\w&.]*(?:\s+[A-Z][\w&.]+){0,3})[^.]{0,60}?" + M + r"\s+for its\s+(?:\w+\s+)?fund\b", re.I),
    re.compile(r"([A-Z][\w&.]*(?:\s+[A-Z][\w&.]+){0,3})[^.]{0,40}?" + M + r"\s+debut fund\b", re.I),
    re.compile(r"([A-Z][\w&.]*(?:\s+[A-Z][\w&.]+){0,3})[^.]{0,40}?closed\s+(?:its\s+|a\s+)?" + M + r"\s+fund\b", re.I),
]

funds, seen = [], set()
def scan(text, date, url, source):
    for rx in PATTERNS:
        for m in rx.finditer(text):
            firm = m.group(1).strip(" ,.-")
            firm = re.sub(r"^(The|A|An)\s+", "", firm)
            amt = money(m.group(2), m.group(3))
            if amt < 5e6 or amt > 3e10 or len(firm) < 3: continue
            roman = re.search(r"fund\s+(I{1,3}|IV|V|VI|\d+)\b", text[m.start():m.end() + 30], re.I)
            k = (firm.lower(), round(amt))
            if k in seen: continue
            seen.add(k)
            funds.append({"firm": firm, "amount": amt, "date": date,
                          "fund_no": roman.group(1) if roman else "",
                          "url": url, "source": source})

# TechCrunch: wider pull, 2026 only
for page in (1, 2, 3):
    posts = get(f"https://techcrunch.com/wp-json/wp/v2/posts?per_page=100&page={page}"
                f"&search=fund&after=2026-01-01T00:00:00&orderby=date&order=desc&_fields=date,title,link,excerpt")
    for p in posts:
        scan(clean(p["title"]["rendered"]) + " " + clean(p["excerpt"]["rendered"]), p["date"][:10], p["link"], "TechCrunch")

# StrictlyVC archive (2018-19 editions)
for p in json.load(open(f"{BASE}/raw/strictlyvc.json")):
    t = clean(p["title"]["rendered"])
    dm = re.match(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", t)
    if dm:
        import datetime
        date = datetime.datetime.strptime(dm.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
    else:
        date = p["date"][:10]
    scan(clean(p["content"]["rendered"]), date, p["link"], "StrictlyVC archive")

funds.sort(key=lambda f: f["date"], reverse=True)
json.dump(funds, open(f"{BASE}/funds.json", "w"), indent=1)
print("FUNDS:", len(funds))
for f in funds:
    print(" ", f["date"], "|", f["firm"], "|", round(f["amount"] / 1e6), "M |", f["fund_no"], "|", f["source"])
