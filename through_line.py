"""Through line: for each exited company, count how often the StrictlyVC
archive mentioned it BEFORE its exit — did we watch them come in, too?
Single-pass alternation scan over the mirror. Also checks overlap with the
current (2026) rounds dataset."""
import gzip, glob, json, re, html as H

posts = []
for f in sorted(glob.glob("raw/svc_full/page-*.json.gz")):
    posts += json.load(gzip.open(f, "rt", encoding="utf-8"))
posts.sort(key=lambda p: p["date"])

def clean(raw):
    t = re.sub(r"<[^>]+>", " ", raw or "")
    t = H.unescape(t)
    return re.sub(r"\s+", " ", t)

exits = json.load(open("exits.json"))
names = sorted({e["company"] for e in exits}, key=len, reverse=True)
# skip ultra-generic single words that would match everything
names = [n for n in names if len(n) >= 4 or " " in n]
alt = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")

mentions = {n: [] for n in names}
for p in posts:
    txt = clean(p["content"]["rendered"] if isinstance(p.get("content"), dict) else "")
    seen_here = set()
    for m in alt.finditer(txt):
        nm = m.group(1)
        if nm not in seen_here:
            mentions[nm].append(p["date"][:10])
            seen_here.add(nm)

rows = []
for e in exits:
    ms = mentions.get(e["company"], [])
    pre = [d for d in ms if d < e["date"]]
    rows.append({"company": e["company"], "type": e["type"], "exit_date": e["date"],
                 "acquirer": e["acquirer"], "pre_mentions": len(pre),
                 "first_mention": pre[0] if pre else None})
rows.sort(key=lambda r: -r["pre_mentions"])
covered = sum(1 for r in rows if r["pre_mentions"] > 0)

rounds = json.load(open("rounds.json"))
try:
    rounds += json.load(open("rounds_regional.json"))
except FileNotFoundError:
    pass
round_names = {r["company"].lower() for r in rounds}
overlap = sorted({e["company"] for e in exits if e["company"].lower() in round_names})

out = {"exits_total": len(exits), "with_pre_mentions": covered,
       "top": [r for r in rows if r["pre_mentions"] >= 3][:12],
       "rounds_overlap": overlap}
json.dump(out, open("throughline.json", "w"), indent=1)
print(f"exits: {len(exits)} · mentioned pre-exit: {covered} ({round(100*covered/len(exits))}%)")
print("rounds(2026) overlap:", overlap)
for r in out["top"][:8]:
    print(f"  {r['company']}: {r['pre_mentions']} pre-exit mentions, first {r['first_mention']}, exit {r['exit_date']} ({r['type']})")
