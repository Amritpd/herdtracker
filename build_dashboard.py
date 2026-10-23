"""Compute aggregates and inject data into the dashboard template."""
import json, os, statistics
from collections import Counter, defaultdict
import datetime

BASE = os.path.expanduser("~/workspace/herd-tracker")
rounds = json.load(open(f"{BASE}/rounds.json"))
funds = json.load(open(f"{BASE}/funds.json"))

total_amt = sum(r["amount"] for r in rounds)
median_amt = statistics.median(r["amount"] for r in rounds)
ai_n = sum(1 for r in rounds if r["sector"] == "AI / ML")

def wk(d):
    dt = datetime.date.fromisoformat(d)
    return (dt - datetime.timedelta(days=dt.weekday())).isoformat()

weeks = defaultdict(lambda: {"n": 0, "amt": 0})
for r in rounds:
    w = wk(r["date"]); weeks[w]["n"] += 1; weeks[w]["amt"] += r["amount"]

sec_n, sec_amt = Counter(), Counter()
for r in rounds:
    sec_n[r["sector"]] += 1; sec_amt[r["sector"]] += r["amount"]
sectors = [{"name": k, "n": sec_n[k], "amt": sec_amt[k]} for k in sec_n]
sectors.sort(key=lambda s: -s["n"])

stages = Counter(r["stage"] for r in rounds)
inv = Counter()
for r in rounds:
    for i in r["investors"]: inv[i] += 1
locs = Counter()
for r in rounds:
    if r["location"]:
        locs[r["location"].split(",")[0].strip()] += 1

agg = {
    "n_rounds": len(rounds), "total_amt": total_amt, "median": median_amt,
    "ai_share": round(100 * ai_n / len(rounds)),
    "weeks": [{"w": k, "n": v["n"], "amt": v["amt"]} for k, v in sorted(weeks.items())],
    "sectors": sectors,
    "stages": [{"name": k, "n": v} for k, v in stages.most_common()],
    "investors": [{"name": k, "n": v} for k, v in inv.most_common(12)],
    "locations": [{"name": k, "n": v} for k, v in locs.most_common(8)],
    "biggest": sorted(rounds, key=lambda r: -r["amount"])[:10],
    "fresh_total": sum(f["amount"] for f in funds if f["amount"]),
    "span": [rounds[-1]["date"], rounds[0]["date"]],
}
archive = json.load(open(f"{BASE}/archive.json"))
data = {"agg": agg, "rounds": rounds, "funds": funds, "archive": archive}
tpl = open(f"{BASE}/dashboard_template.html").read()
out = tpl.replace("__DATA_JSON__", json.dumps(data))
dest = os.path.expanduser("~/workspace/your_files/herd-tracker.html")
os.makedirs(os.path.dirname(dest), exist_ok=True)
open(dest, "w").write(out)
print("wrote", dest, len(out), "bytes")
print("weeks:", agg["weeks"])
print("ai_share:", agg["ai_share"], "median:", median_amt)
