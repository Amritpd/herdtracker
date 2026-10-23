"""Region tagging for Herd Tracker rounds.

Strategy (see FEATURES.md section 0):
1. Source-native region (EU-Startups=Europe, Inc42/e27=APAC, etc.) — added when
   those extractors land. FinSMEs is global, so it falls through to (2).
2. Location text mined from the article itself: FinSMEs posts describe the
   company as "a <City>-based ..." in the opening lines, and rounds.json's
   `desc` field (the known field mixup) often holds the city or an
   "NYC-based provider of ..." string. We extract a city token from both,
   then map city -> country -> region with the dictionary below.
3. Anything unmatched is region=None ("Untagged") — shown honestly in the UI,
   never guessed.
"""
import json, re, html

CITY_REGION = {}
def _add(region, cities):
    for c in cities:
        CITY_REGION[c.lower()] = region

_add("Americas", [
    # US hubs (observed + common)
    "san francisco","new york","new york city","nyc","los angeles","mountain view",
    "el segundo","washington","redwood city","wilmington","emeryville","pittsburgh",
    "sacramento","santa clara","menlo park","broomfield","scottsdale","minneapolis",
    "delray beach","avon-by-the-sea","louisville","south san francisco","altamonte springs",
    "east palo alto","palo alto","sunnyvale","san jose","san diego","austin","houston",
    "dallas","denver","boulder","seattle","bellevue","portland","chicago","boston",
    "cambridge","atlanta","miami","nashville","phoenix","salt lake city","las vegas",
    "detroit","ann arbor","raleigh","durham","charlotte","deerfield beach","ponte vedra beach",
    "santa monica","culver city","irvine","oakland","berkeley","alameda",
    # Canada / Mexico
    "toronto","vancouver","montreal","waterloo","calgary","ottawa","mexico city",
    # South America (grouped into Americas per product decision, Oct 23)
    "buenos aires","montevideo","sao paulo","são paulo","santiago","bogota","bogotá",
    "lima","rio de janeiro","medellin","medellín",
])
_add("Europe", [
    "london","berlin","paris","amsterdam","stockholm","dublin","madrid","barcelona",
    "zurich","zürich","munich","munich","dusseldorf","düsseldorf","bratislava",
    "kongens lyngby","copenhagen","brétigny-sur-orge","bretigny-sur-orge","haywards heath",
    "luxembourg","vienna","warsaw","lisbon","helsinki","oslo","tallinn","riga","vilnius",
    "prague","budapest","athens","milan","rome","hamburg","frankfurt","cologne","oxford",
    "edinburgh","manchester","bristol","geneva","lausanne","reykjavik","ghent","antwerp",
    "rotterdam","the hague","lyon","marseille",
])
_add("APAC", [
    "singapore","bangalore","bengaluru","mumbai","delhi","new delhi","hyderabad","chennai",
    "pune","tokyo","osaka","sydney","melbourne","brisbane","perth","hong kong","seoul",
    "beijing","shanghai","shenzhen","taipei","jakarta","kuala lumpur","bangkok","hanoi",
    "ho chi minh city","manila","auckland","wellington","gurgaon","noida","kolkata",
])
_add("MEA", [
    "tel aviv","jerusalem","dubai","abu dhabi","riyadh","doha","cairo","lagos","abuja",
    "nairobi","cape town","johannesburg","accra","addis ababa","casablanca","tunis",
    "beirut","amman","manama","kuwait city",
])

ALIASES = {"nyc": "new york city", "nyc-based": "new york city"}

def _clean_text(raw_html):
    t = re.sub(r"<[^>]+>", " ", raw_html or "")
    return html.unescape(re.sub(r"\s+", " ", t)).strip()

def city_from_text(text):
    """Find a '<City>-based' or 'based in <City>' token in opening text."""
    if not text:
        return None
    head = text[:600]
    m = re.search(r"([A-Z][A-Za-zÀ-ÿ.'\-, ]{1,42}?)-based", head)
    if m:
        cand = m.group(1).strip().lower()
        cand = re.sub(r"^(a|an|the)\s+", "", cand)
        cand = cand.split(",")[0].strip()  # "san francisco, ca" -> "san francisco"
        # strings like "nyc- and miami" or "new york city and amsterdam": take first known city
        parts = re.split(r"\s+and\s+|\s*&\s*|,\s*", cand)
        for p in parts:
            p = p.strip(" -")
            if p in CITY_REGION:
                return p
        if cand in CITY_REGION:
            return cand
    m = re.search(r"based in ([A-Z][A-Za-zÀ-ÿ.'\- ]{1,30}?)[,.]", head)
    if m:
        cand = m.group(1).strip().lower()
        if cand in CITY_REGION:
            return cand
    # FinSMEs 'About' boilerplate: "headquartered in X" / "based in X" anywhere
    for pat in (r"headquartered in ([A-Z][A-Za-zÀ-ÿ.'\- ]{1,30}?)[,.]",
                r"based in ([A-Z][A-Za-zÀ-ÿ.'\- ]{1,30}?)[,.]"):
        m = re.search(pat, text)
        if m:
            cand = m.group(1).strip().lower().split(",")[0].strip()
            if cand in CITY_REGION:
                return cand
    return None

def city_from_desc(desc):
    if not desc:
        return None
    d = desc.strip()
    low = d.lower()
    if low in CITY_REGION:
        return low
    if len(d) <= 40:  # "NYC- and Miami", "New York City and Amsterdam"
        parts = re.split(r"\s+and\s+|\s*&\s*|,\s*|-\s+and\s+", low)
        for p in parts:
            p = p.strip(" -")
            if p in CITY_REGION:
                return p
    m = re.search(r"([A-Za-z.'\- ]{2,25}?)-based", low)
    if m:
        cand = m.group(1).strip()
        if cand in CITY_REGION:
            return cand
    if low.startswith("nyc"):
        return "new york city"
    return None

def tag_rounds(rounds, raw_posts=None):
    """Mutates copies: adds city/region. Returns (tagged_rounds, stats)."""
    by_link = {}
    if raw_posts:
        for p in raw_posts:
            by_link[p.get("link", "")] = _clean_text(p.get("content", {}).get("rendered", ""))
    out, stats = [], {"tagged": 0, "by_region": {}}
    for r in rounds:
        r = dict(r)
        if r.get("region"):  # region-native sources (extract_regional.py) — keep as-is
            stats["tagged"] += 1
            stats["by_region"][r["region"]] = stats["by_region"].get(r["region"], 0) + 1
            r.setdefault("city", r.get("city") or "")
            out.append(r)
            continue
        city = city_from_desc(r.get("desc")) or city_from_text(by_link.get(r.get("url", "")))
        r["city"] = city or ""
        r["region"] = CITY_REGION.get(city, "") if city else ""
        if r["region"]:
            stats["tagged"] += 1
            stats["by_region"][r["region"]] = stats["by_region"].get(r["region"], 0) + 1
        out.append(r)
    return out, stats

def clean_investors(investors):
    """Split 'Lead with participation from X, Y' strings into a clean, deduped list."""
    out = []
    for inv in investors or []:
        parts = re.split(r"\s+with participation from\s+|\s+and participation from\s+", inv)
        for part in parts:
            for token in re.split(r",\s*|\s+and\s+", part):
                t = token.strip().strip(".")
                if not t or len(t) > 45 or len(t) < 2:
                    continue
                if any(w in t.lower() for w in ("participation", "existing investors", "others", "undisclosed")):
                    continue
                if t not in out:
                    out.append(t)
    return out

if __name__ == "__main__":
    rounds = json.load(open("rounds.json"))
    try:
        raw = json.load(open("raw/finsmes.json"))
    except FileNotFoundError:
        raw = None
    tagged, stats = tag_rounds(rounds, raw)
    print(f"tagged {stats['tagged']}/{len(tagged)} rounds")
    print(stats["by_region"])
    cities = {}
    for r in tagged:
        if r["city"]:
            cities[r["city"]] = cities.get(r["city"], 0) + 1
    print("top cities:", sorted(cities.items(), key=lambda kv: -kv[1])[:15])
