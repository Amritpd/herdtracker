"""Rule-based extraction: rounds from Finsmes, funds from all sources. Free NLP only."""
import json, re, html, os
from collections import Counter

BASE = os.path.expanduser("~/workspace/herd-tracker")
raw = lambda n: json.load(open(f"{BASE}/raw/{n}.json"))

def clean(t):
    t = html.unescape(t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def money(num, unit):
    v = float(num)
    u = (unit or "").lower()
    if u.startswith("b"): return v * 1e9
    if u.startswith("m"): return v * 1e6
    if u.startswith("k"): return v * 1e3
    return v

MONEY = r"\$([\d,]+(?:\.\d+)?)\s*(million|billion|M|B|K)?"

SECTORS = [
    ("AI / ML", r"\b(AI|artificial intelligence|machine learning|LLM|generative|agentic|AI-powered|AI powered)\b"),
    ("Cybersecurity", r"\b(cyber|security|threat|fraud prevention|identity)\b"),
    ("Fintech", r"\b(fintech|payment|banking|lending|insurance|insurtech|wealth|trading|crypto exchange)\b"),
    ("Crypto / Web3", r"\b(crypto|blockchain|web3|token|DeFi|NFT)\b"),
    ("Health / Bio", r"\b(health|biotech|medical|clinical|therap|drug|pharma|genom|patient|hospital|diagnostic)\b"),
    ("Climate / Energy", r"\b(climate|energy|solar|battery|carbon|EV|electric|hydrogen|sustainab|nuclear)\b"),
    ("Robotics / Hardware", r"\b(robot|drone|hardware|sensor|semiconductor|chip|autonomous vehicle)\b"),
    ("Space / Defense", r"\b(space|satellite|defense|defence|aerospace|aviation)\b"),
    ("SaaS / Enterprise", r"\b(SaaS|enterprise software|workflow|productivity|CRM|HR tech|platform for business)\b"),
    ("DevTools", r"\b(developer|devtool|API platform|open-source|open source|infrastructure|observability)\b"),
    ("Legal", r"\b(legal|law firm|attorney|compliance|regulatory)\b"),
    ("Consumer", r"\b(consumer|e-commerce|ecommerce|retail|fashion|beauty|gaming|social app|marketplace)\b"),
    ("Food / Ag", r"\b(food|agriculture|agtech|restaurant|grocery|farming)\b"),
    ("EdTech", r"\b(education|learning|edtech|student|tutoring)\b"),
    ("Real Estate", r"\b(real estate|proptech|property|construction|housing)\b"),
]

def sector_of(text):
    hits = []
    for name, pat in SECTORS:
        if re.search(pat, text, re.I): hits.append(name)
    return hits[0] if hits else "Other"

STAGES = [r"Series [A-F]", r"Pre-Seed", r"Seed", r"Growth", r"Debt", r"Grant", r"Venture", r"Strategic", r"IPO"]

def stage_of(text):
    for s in STAGES:
        m = re.search(s, text, re.I)
        if m: return m.group(0).title() if "Series" not in s else "Series " + m.group(0)[-1].upper()
    return "Undisclosed"

# ---------- ROUNDS from Finsmes ----------
rounds, seen = [], set()
title_re = re.compile(
    r"^(.+?)\s+(?:Raises|Closes|Secures|Receives|Announces|Lands|Bags|Completes|Gets)\s+" + MONEY, re.I)
for p in raw("finsmes"):
    title = clean(p["title"]["rendered"])
    body = clean(p["content"]["rendered"])
    m = title_re.match(title)
    if not m:
        if re.search(r"valuation", title, re.I):
            bm = re.search(r"raised\s+" + MONEY, body, re.I)
            if not bm: continue
            company = re.split(r"\s+(?:Receives|Raises|Gets|Secures)", title)[0].strip()
            amt = money(bm.group(1).replace(",", ""), bm.group(2))
        else:
            mm = re.search(MONEY, title)
            if not mm: continue
            company, amt = title.split(" Raise")[0].split(" Secure")[0].strip(), money(mm.group(1).replace(",", ""), mm.group(2))
    else:
        company, amt = m.group(1).strip(), money(m.group(2).replace(",", ""), m.group(3))
    key = (company.lower(), p["date"][:10])
    if key in seen or amt < 10000 or amt > 5e10: continue
    seen.add(key)
    first = body[:600]
    loc = re.search(r"based in ([A-Z][A-Za-z .]+?)(?:,|\s+?(?:has|raised|is|announces))", first)
    lead = re.search(r"led by ([^.]+)", body)
    part = re.search(r"participation from ([^.]+)", body)
    investors = []
    if lead: investors += [x.strip() for x in re.split(r",| and ", lead.group(1)) if 1 < len(x.strip()) < 60]
    if part: investors += [x.strip() for x in re.split(r",| and ", part.group(1)) if 1 < len(x.strip()) < 60]
    STOP = {"others", "existing investors", "angel investors", "other investors", "existing backers", "new investors"}
    def norm_inv(x):
        x = re.sub(r"\s*\(.*?\)\s*", "", x).strip()
        if "Andreessen Horowitz" in x: return "a16z"
        if x.lower() == "andreessen horowitz": return "a16z"
        return x
    investors = [norm_inv(i) for i in investors if i.lower() not in STOP]
    desc = re.search(re.escape(company) + r"[^,]*,\s*(?:a|an|the)\s+([^,.]{10,120})", first)
    rounds.append({
        "company": company, "amount": amt, "date": p["date"][:10],
        "stage": stage_of(title + " " + body[:300]),
        "sector": sector_of(title + " " + first),
        "location": loc.group(1).strip() if loc else "",
        "investors": investors[:6], "desc": (desc.group(1).strip() if desc else "")[:120],
        "url": p["link"], "source": "Finsmes",
    })
rounds.sort(key=lambda r: r["date"], reverse=True)

# ---------- FUNDS: candidate mining (agent curates after) ----------
cands = []
fund_rx = re.compile(
    r"([A-Z][\w&.]*(?:\s+[A-Z][\w&.]+){0,3})\s+(?:has\s+)?(closed|raised|announced|launched|is raising|plans to raise)\s+"
    r"(?:a\s+|its\s+|an\s+|their\s+)?(?:new\s+)?" + MONEY + r"\s*(?:[a-z]+\s+){0,3}?fund", re.I)
def scan_c(text, date, url, source):
    for m in fund_rx.finditer(text):
        firm = m.group(1).strip(" ,.-")
        amt = money(m.group(3).replace(",", ""), m.group(4))
        if amt < 5e6 or amt > 3e10 or len(firm) < 3: continue
        s = max(0, m.start() - 40)
        cands.append({"firm_guess": firm, "amount": amt, "date": date, "url": url, "source": source,
                      "snippet": text[s:m.end() + 60]})
for p in raw("techcrunch_fund"):
    scan_c(clean(p["title"]["rendered"]) + " " + clean(p["excerpt"]["rendered"]), p["date"][:10], p["link"], "TechCrunch")
for p in raw("strictlyvc"):
    t = clean(p["title"]["rendered"])
    dm = re.match(r"([A-Z][a-z]+ \d{1,2}, \d{4})", t)
    scan_c(clean(p["content"]["rendered"]), dm.group(1) if dm else p["date"][:10], p["link"], "StrictlyVC archive")
json.dump(cands, open(f"{BASE}/funds_candidates.json", "w"), indent=1)
print("fund candidates:", len(cands))
funds = []

json.dump(rounds, open(f"{BASE}/rounds.json", "w"), indent=1)
json.dump(funds, open(f"{BASE}/funds.json", "w"), indent=1)

# ---------- ANALYTICS ----------
tot = sum(r["amount"] for r in rounds)
by_sector = Counter(r["sector"] for r in rounds)
sec_money = Counter()
for r in rounds: sec_money[r["sector"]] += r["amount"]
inv = Counter()
for r in rounds:
    for i in r["investors"]: inv[i] += 1
by_stage = Counter(r["stage"] for r in rounds)
by_week = Counter(r["date"][:8] + "x" for r in rounds)
week_money = Counter()
for r in rounds: week_money[r["date"][:8] + "x"] += r["amount"]
print(f"ROUNDS: {len(rounds)}  TOTAL: ${tot/1e9:.2f}B  span {rounds[-1]['date']} -> {rounds[0]['date']}")
print("sectors by count:", by_sector.most_common(8))
print("sectors by $:", [(k, f'${v/1e9:.2f}B') for k, v in sec_money.most_common(5)])
print("stages:", by_stage.most_common(8))
print("top investors:", inv.most_common(10))
big = sorted(rounds, key=lambda x: -x["amount"])[:6]
print("biggest:", [(r["company"], round(r["amount"] / 1e6)) for r in big])
print(f"FUNDS: {len(funds)}")
for f in funds[:15]: print("  ", f["date"], f["firm"], f"${f['amount']/1e6:.0f}M", f["source"])
