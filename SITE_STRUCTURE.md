# Herd Tracker — Site Structure / Tab Map
Drafted Oct 23, 2026. Current dashboard has 2 tabs (The Latest / The Archive).
This replaces them with 6 top-level sections, like newspaper sections.

## How tabs work in the upgrade (important)
- NOW: tabs are JS show/hide inside ONE html file (showTab() toggles display:none).
  Nothing is linkable, searchable, or separately crawlable.
- UPGRADED: each top-level tab = its own generated page (its own URL) sharing the
  same masthead + nav template, active section underlined (same .tabbtn.on style).
  Deep-linkable, shareable, indexable, AdSense can review/crawl each page.
- Sub-tabs INSIDE a page (e.g. region editions, era toggle) stay as JS toggles —
  they're views of the same page's data, not separate destinations.
- Charts are rendered at build time as inline SVG/bars (as the Archive chart
  already is) — no chart library, pages stay fast and print/screenshot clean.

## The 6 tabs

### 1. Front Page — /  (was "The Latest")
KPIs, Herd Signals, Biggest Stampedes, Fresh Powder teaser, Leaderboard teaser,
Weekly Herd Report signup. The hook page; everything below is depth.

### 2. Trends — /trends  **NEW — the high-level page (Amrit, Oct 23)**
The 30,000-ft page. Built for the "cannabis was ~30% of coverage, now it's 0%"
moment — every chart here is screenshot-first.
- HEADLINE: Thesis Waves — mention share by era (2014/2017/2019/2026):
  AI 18->63->73->59% · fintech 2->30->23->4% (peaked 2017) · cannabis 2->9->27->0% · quantum 1-6% always
- The Graveyard table: thesis / peak year / peak % / now % / half-life
- Coverage share vs Dollars share (Hype Gap) — same sectors, attention vs money
- Sector share of $ over time (from rounds pipeline, rolling forward)
- Rest-of-Market Index (headline total minus top 10 rounds) + Extension Index
- Stage-Inflation mini-chart (median seed, then vs now)
- Thesis Archaeology (the old Archive tab folds in here, bottom half) +
  rotating Spotlight (Quantum first)
- Era toggle [2013-19 | 2020s | All] as JS sub-tab
- DATA HONESTY: historical waves are era CHECKPOINTS from the StrictlyVC mirror
  (2014/2017/2019) + 2026 — not a continuous line. The page labels them as
  checkpoints. From launch forward, our own weekly pipeline makes the series
  continuous — the chart literally gets better every week we run it.

### 3. Regions — /regions  (editions as sub-tabs)
[Global | Americas | Europe | APAC | MEA] JS sub-tabs, one template filtered
per edition: KPIs, biggest rounds, leaderboard, sector mix, fresh powder.
Region-vs-Region comparison block at the bottom [PRO].

### 4. Rounds — /rounds  (Round Explorer 2.0)
Full filter bar (region/sector/stage/amount/date/investor), sortable table,
company rows link to /company/<slug>. CSV export [PRO].

### 5. Fresh Powder — /fresh-powder
Fund table (firm, fund, size, close, focus, region), Dry-Powder Clock,
Deployment Pace. Teaser free, full table [PRO].

### 6. Investors — /investors
Herd Leaderboard (most active), Early Money vs Herd Money, Co-Herd pairs,
per-firm pages at /investor/<slug> [PRO depth].

### Utility pages (not tabs)
About · Methodology & Sources · Privacy · Terms · Contact — AdSense/trust
requirements (see UPGRADE_PLAN.md). My Herd (bookmarks) lives in the
masthead, right side, once auth/bookmarks ship.

## Build order for the split
1. Extract shared masthead/nav into the builder template (mechanical)
2. Trends page (NEW content, highest share-value — build first, prototype-able
   TODAY inside the current single file as a third tab using archive.json)
3. Front Page + Rounds split (content exists, just moves)
4. Regions (needs region-tag foundation from FEATURES.md §0)
5. Fresh Powder + Investors split (content exists, moves)
