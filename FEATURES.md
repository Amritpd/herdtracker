# Herd Tracker — Product Feature List
Drafted Oct 23, 2026. Organized by: foundation -> slices -> analytics -> personalization.
Tags: [FREE] / [PRO] per PRICING.md · Effort S (hours) / M (a day-ish) / L (multi-day)

## 0. Data foundation — everything below depends on this
Current state checked Oct 23: rounds.json has company/amount/date/stage/sector/investors/url,
but `location` is EMPTY on all 383 rounds and city strings sit in `desc` on 165/383 (43%)
(the known extract.py field mixup). Investor strings are messy (e.g. one entry reads
"CiRi Ventures with participation from...").

- **Region tag on every round + fund** [foundation, M]: Americas / Europe / APAC / MEA + country + city.
  Two signals, cheap first: (1) source-native region — EU-Startups = Europe, Inc42/e27 = APAC,
  LatamList = South America, MENAbytes = MEA, AlleyWatch/Pulse2 = Americas; (2) fix location
  extraction, then map city -> country -> region with a hub dictionary (SF/NYC/Austin...,
  London/Berlin/Paris..., Bangalore/Singapore/Tokyo...). Source signal covers new sources 100%;
  city mapping covers FinSMEs backlog.
- **Investor entity cleanup** [foundation, M]: split "lead with participation from X, Y",
  dedupe firms, canonical names. Leaderboard/graph accuracy depends on it.
- **Currency normalization** [foundation, S]: EUR/GBP/INR etc -> USD at round date, keep original
  displayed. Required before any cross-region $ comparison is honest (Fresh Powder already
  needed this by hand: Sprints €725M ~ $810M).
- **Stage + sector normalization** [foundation, S]: canonical stage ladder (Pre-seed/Seed/
  Series A/B/C+/Growth/Grant), keep sector taxonomy as-is, add sub-sector tags later.

## 1. Regional Editions — Amrit's slice (Oct 23)
Verdict: YES, with one addition. North + South America grouped is right (US volume dominates;
LatAm alone would look empty). But don't orphan the MEA sources we verified (MENAbytes,
Disrupt Africa) — they need a home. WSJ itself runs regional editions; this fits the broadsheet skin.

- **Four editions + Global home** [FREE teasers / PRO depth, M after foundation]:
  Global (all), **Americas**, **Europe**, **APAC**, **MEA**. Each edition gets its own:
  KPIs, Biggest Stampedes, Herd Leaderboard, Fresh Powder (funds by domicile/focus),
  sector mix donut/bars. Same template, filtered data — cheap once region tags exist.
- **Region vs Region comparison** [PRO, M]: same sector, three regions side by side —
  total raised, median round, round count, top investors. The killer question it answers:
  "where is this thesis herding in the US but NOT yet in Europe/APAC?" = arbitrage signal.
- **Thesis diffusion lag** [PRO, L]: when a keyword/sector wave starts in one region and
  appears in another — lag in months. Built on Buzzword Index per region. Signature chart,
  very screenshot-able.
- **Regional Herd Reports** [FREE, S]: the weekly report gets a one-paragraph edition
  variant per region (same data, filtered) — 4x the social/email surface for ~no extra work.

## 2. Round Explorer 2.0 — the core slice-and-dice
- **Full filter bar** [FREE basic / PRO all-time, M]: region, country, sector, stage,
  amount range, date range, investor, source. Sort by amount/date. This is the product's workbench.
- **CSV export** [PRO, S]: export exactly the filtered view. Founders/analysts pay for rows, not charts.
- **Entity pages** [FREE, M]: /company/<slug>, /investor/<slug>, /sector/<slug>, /region/<slug> —
  every slice becomes a page (also the AdSense/SEO build in UPGRADE_PLAN.md).
- **Saved views** [PRO, S after auth]: name a filter combo ("EU AI seeds >$2M") and re-run it
  on each weekly pull. Saved views -> alerts is the retention loop.

## 3. Herd analytics — the differentiator (from Oct 21 backlog, now placed)
- **Buzzword Index** [FREE chart / PRO depth, M]: term frequency by quarter, per region.
- **Stampede Score** [FREE, S]: per company/sector — how many near-identical raises in the
  last 90 days. One number, very Herd Tracker. "This is the 14th AI SDR tool funded this quarter."
- **Copycat Clusters** [PRO, M]: group similar companies raising in a window; cluster page per wave.
- **Déjà Vu Detector** [PRO, M]: dead theses resurfacing under new vocabulary (uses 2013-19 Archive).
- **Dry-Powder Clock** [PRO, S]: funds ranked by months since close (from Fresh Powder data).
- **Fund-Size Creep** [PRO, S]: median fund size by vintage year.
- **Stage-Inflation Index** [PRO, S]: median "seed" (and each stage) size by year/region —
  "a seed in APAC is not a seed in SF."
- **Co-Herd Graph** [PRO, L]: firms that only ever appear together (co-investor clustering).
- **Zombie Watch** [PRO, M]: companies that raised big and never reappear (no follow-on, no exit).
- **The Exit Door** [FREE/PRO, M]: acquisitions + shutdowns as the survivorship counterweight.
- **Lonely Lanes** [PRO, M]: sectors/regions with Fresh Powder (capital raised to deploy)
  but few recent rounds — the inverse-stampede view founders actually act on.

## 4. Fresh Powder features
- **Fund pages + full table** [FREE teaser / PRO full, S]: firm, size, close date, focus, domicile/region.
- **"Who just raised and hunts in my lane?"** [PRO, M]: filter funds by focus + region + vintage
  -> the data layer under the one-time Raise Targeting Pack ($29-49, PRICING.md).
- **Sector Dossiers** [ONE-TIME pack, M]: auto-generated pack per sector (waves, top funds,
  median rounds, archive history) — the one-time product.

## 5. Personalization (scoped in PAYWALL_PLAN.md)
- **Bookmarks / My Herd watchlist** [FREE local capped / PRO synced, S-M]
- **Raise alerts** [PRO, M]: bookmarked company/investor/sector/region raises again -> email digest.
- **Follow a region edition** [FREE email / PRO alerts, S]: subscribe to Americas/Europe/APAC/MEA digest only.

## 6. Insights added Oct 23 (second pass — the ones not in the original list)
Ranked by impact. All computable from data in hand + Form D layer; none need paid data.

- **Hype Gap Index** [PRO, M]: coverage share (Archive keyword %) vs dollars share (rounds $)
  per sector. Over-covered/under-funded = hype; under-covered/heavily funded = quiet money.
  Only possible because we hold BOTH datasets. Signature insight.
- **Rest-of-Market Index** [FREE, S]: headline totals minus the top 10 rounds. When 5 mega
  AI rounds are 60% of "$ raised," everyone else is in a drought — this number says so.
  Publish next to every headline total, permanently.
- **Early Money vs Herd Money** [PRO, M]: per firm — does it first appear in a thesis wave
  BEFORE the peak (early/smart) or only AT the peak (tourist)? Leaderboard of firms timed
  against cluster peaks. Nobody free publishes this; it's pure timestamp math.
- **Raise Window Radar** [PRO, M]: companies 18-30 months since last raise (the window where
  follow-ons statistically happen) by sector/region. Founders benchmark against it;
  B2B buyers sell into it; funds source from it.
- **Graduation Rate** [PRO, L]: % of a seed cohort reaching Series A within 24 months,
  by sector/region/vintage. "Is the seed->A bridge broken in your sector?" — the metric
  founders actually lose sleep over.
- **Stealth Raises (Form D scoops)** [PRO, M]: EDGAR Form D filed with NO press announcement.
  Newsletters can't see these (they live on announcements). Ground-truth layer = exclusives.
- **Extension / Bridge Index** [FREE chart, S]: share of rounds that are extensions/bridges
  over time. Rising = ecosystem distress before any headline admits it. A stress barometer.
- **Deployment Pace + Use-It-Or-Lose-It** [PRO, S-M]: per Fresh Powder fund — time from close
  to first visible deals, and funds entering year 3-4 of their investment period that must
  deploy. Turns the fund table into a targeting calendar.
- **Same Thesis, New Costume** [FREE/PRO, M]: paired buzzword succession — term A dies as
  near-synonym term B rises (web3 -> AI agents). Stronger than single-term déjà vu.
- **Capital Flow Matrix** [PRO, M]: investor domicile region x company region. Where money
  sleeps vs where it lands (US funds -> APAC startups, etc.). Needs investor-HQ dictionary
  for top firms — a one-time static mapping.
- **Fundable Benchmark Cards** [ONE-TIME pack fuel, S]: per sector x region — median round,
  typical stage sizes, most common leads this quarter. Auto-generated dossier content.

## Suggested build order
1. Foundation: region tags + investor cleanup + currency (unblocks everything; also fixes known data bugs)
2. Wire Tier A regional sources (AlleyWatch, Pulse 2.0, EU-Startups, Inc42, e27) — editions need volume
3. Regional Editions + Explorer filters (one build, two features)
4. Entity pages (doubles as the SEO/AdSense upgrade)
5. Stampede Score + Buzzword Index per region (first signature analytics)
6. Bookmarks/alerts + Pro gate (PAYWALL_PLAN) once traffic exists
