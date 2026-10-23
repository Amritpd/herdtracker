# Herd Tracker — Verified Free Sources
Checked live: Oct 22, 2026 (HTTP 200 = feed/API open, free, no login)

## Already in pipeline
- FinSMEs — WP-API 200 — 1 templated post per round, ideal extraction
- TechCrunch — WP-API 200 — noisy for rounds, good signal filter
- VCWire (vcwire.tech) — WP-API 200 — dedicated fund-close wire, Fresh Powder source
- StrictlyVC — WP-API archive only to Nov 2019 (live site moved CMS). KEEP for Archive archaeology only, NOT as live source.
- SEC EDGAR Form D — full-text search open — primary source / ground truth, public domain

## Tier A — Add next: free, templated, programmatic (same shape as FinSMEs)
- AlleyWatch — RSS + WP-API 200 — NYC funding, 1 post per round; sister network TechWatch/LA TechWatch
- Pulse 2.0 — RSS + WP-API 200 — US funding announcements, templated
- EU-Startups — RSS + WP-API 200 — European rounds, templated
- Tech Funding News — RSS 200 — UK/global rounds
- Inc42 — RSS 200 — India rounds
- e27 — RSS 200 — SE Asia rounds
- Disrupt Africa — RSS 200 — Africa rounds

## Tier B — Primary sources (what StrictlyVC itself aggregates — zero middleman risk)
- PR Newswire (financial services RSS) — 200
- BusinessWire — RSS 200 confirmed Oct 22 (second sweep)
- GlobeNewswire wires — GlobeNewswire RSS returned 403 in Oct 22 check, needs re-check / UA handling
- Company press releases + SEC Form D filings

## Tier C — Free editorial RSS, useful but noisy (filter for "raises / closes / fund")
- Crunchbase News — RSS 200
- GeekWire — RSS 200
- SiliconANGLE — RSS 200
- Tech.eu — RSS 200
- UKTN (UK Tech News) — RSS 200
- VentureBeat — RSS returned 429 in Oct 22 check, rate-limited

## Regional / other RSS confirmed Oct 22 (second sweep)
- LA TechWatch (AlleyWatch sister) — RSS 200; Technical.ly — 200; MENAbytes — 200; LatamList — 200; Sifted — 200
- Hypepotamus — /feed/ returned 404 Oct 22, do NOT count as verified (needs alternate feed URL)
- Fortune general RSS — 200; Axios general RSS — 200 (general feeds, not a structured Term Sheet / Pro Rata feed)

## Email-only / walled — do not rely on programmatically
- Fortune Term Sheet, Axios Pro Rata — free email, no public structured feed for those specific newsletters (email-route only); their general site RSS above is separate and noisy
- PE Hub — walled
- The Information, PitchBook, Newcomer (full) — paid

## Legal note shaping the pipeline
Facts (company, amount, stage, investors, date) are not copyrightable; the wording/expression summarizing them is. Pipeline model stays: extract facts, write own summaries, link to source. Do not republish StrictlyVC (or any source) full text.
Safest live strategy: drop StrictlyVC as a live source, go upstream to wires + Form D + Tier A templated sites.
