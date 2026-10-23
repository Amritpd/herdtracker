# Herd Tracker

A data product that funnels free startup / VC newsletters and wires into structured
funding data, to surface herd patterns: copycat clusters, theses recurring under
new vocabulary, and which firms pile into the same wave.

## Live dashboard (built output)
`dashboard.html` — single-file build, broadsheet-finance styling (Playfair Display /
Libre Franklin, warm paper, WSJ blue). Data embedded at build time.

Tabs:
- **The Latest** — recent rounds, Herd Signals, Fresh Powder (new fund closes),
  Herd Leaderboard, Biggest Stampedes, Round Explorer
- **The Archive · 2013–19 vs 2026** — Thesis Archaeology from the full StrictlyVC
  mirror (1,238 dated editions, Sep 2013–Nov 2019) vs 2026 keyword waves

V1 snapshot: 383 rounds / $28.1B (Sep 23–Oct 21, 2026) + 11 verified fresh funds / $3.74B

## Pipeline ($0 to run — rule-based, no paid APIs)
- `fetch.py` — pull source feeds/APIs into `raw/`
- `extract.py` — rule-based extraction of rounds (company, amount, stage, investors, thesis) → `rounds.json`
- `funds2.py` / `curate_funds.py` — Fresh Powder fund-close candidates → `funds.json`
- `backfill_svc.py` — resumable StrictlyVC WP-API archive backfill → `raw/svc_full/`
- `analyze_archive.py` — archive keyword-wave analysis → `archive.json`
- `build_dashboard.py` + `dashboard_template.html` — render `dashboard.html`

Re-run:
```bash
python3 fetch.py && python3 extract.py && python3 build_dashboard.py
```

## Sources
See `SOURCES_VERIFIED.md` — every source checked live (feed/API status, date).
Primary strategy: go upstream to wires (PR Newswire, BusinessWire) + SEC EDGAR
Form D + templated free sites (FinSMEs, AlleyWatch, Pulse 2.0, EU-Startups).
StrictlyVC is used for archive archaeology only, not as a live source.
Facts are extracted and re-summarized with links — full text is never republished.

## Monetization / paywall plan
See `PRICING.md` and `PAYWALL_PLAN.md`.
Launch free (audience + email list first); Pro subscription for Archive depth,
Fresh Powder, CSV export, and synced bookmarks/alerts; one-time sector dossiers
and founder raise-targeting packs. Paywall path: Firebase Hosting multisite
(reusing the Heirloom project) + Firebase Auth + Stripe Firebase Extension.

## Data note
`raw/` is committed deliberately as a backup in case upstream APIs shut off.
Known caveat: some `rounds.json` `desc` fields hold location strings (extract.py
field mixup) — text analysis should run on raw post text, not `desc`.
