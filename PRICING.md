# Herd Tracker — Pricing Recommendation
Decided in discussion Oct 22, 2026 (Amrit asked: should we charge at all? / $5 per month of past data?)

## Verdict
Build the paywall ready, launch FREE. Do not hard-gate day 1.
Charge for depth / convenience / personalization, not for raw access.
Hybrid structure below, not per-month unlocks.

## Why not $5 per month of past data
- Entitlement complexity: tracking which user bought which months is a matrix — the hardest paywall to build, for the smallest ticket.
- It fragments the product: Thesis Archaeology only works as a full timeline (2013-19 vs 2026). One month alone is near-useless.
- Math breaks at scale: 72 archive months x $5 = $360 (absurd vs a subscription) — or users buy 2-3 recent months for $15 and churn forever.
- Stripe fee drag: $5 charge = $0.30 + 2.9% = ~9% gone.
- Price signal: $5 says the data is a commodity. To a founder mid-raise, a filtered Fresh Powder list is worth 10-50x that.
- One-time has no renewal logic: our best premium features (fresh funds, alerts on bookmarks) arrive continuously — subscription matches the value delivery.

## Recommended structure
### Free (forever, launch default)
- Latest 30 days rounds, Herd Signals, Herd Leaderboard, Biggest Stampedes
- Weekly Herd Report (screenshot-bait — distribution engine)
- Bookmarks: local only, capped (e.g. 5)
- Goal at launch: audience + email list. Per Amrit Oct 21: a publication VCs read manufactures the network that is his #1 bottleneck. Ads/sponsorship to this audience is the first money, not $5 unlocks.

### Pro — subscription (flip on after traffic signal, or soft-gate from day 1)
- Placeholder: $12/mo or $99/yr
- Full Archive (2013-19 vs 2026), full Fresh Powder table, all-time Round Explorer + filters, CSV export, unlimited synced bookmarks + raise alerts

### One-time packs — where one-time pricing DOES work (no subscription needed)
- Sector Dossier: e.g. Quantum / AI Seed / Fintech wave pack, 2018-2026 — $29-49
- Founder Raise Targeting Pack: Fresh Powder filtered to founder's sector / stage / geography — $29-49
- Rationale: a founder fundraising NOW has a one-time job and high willingness to pay; they will not subscribe for a year for it. This was already in the Oct 21 monetization shape.

## When to flip the gate
Signal, not date: repeat visitors, email signups, clicks on locked teasers, inbound asks for CSV / older data. Build in Stripe test mode now so flipping is a config change, not a build.
