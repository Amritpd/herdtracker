# Herd Tracker — Stripe Paywall: Weekend Plan
Scoped Oct 22, 2026. Architecture assumption: reuse Amrit's existing Heirloom Firebase project (multisite), do NOT build a custom Next.js/Stripe backend.

## Why the current file can't just get a paywall button
Current dashboard is a single static HTML file with ALL data embedded.
View Source = premium data free. A real paywall requires:
1. Split data: free data ships in the page, premium data lives behind auth
2. Auth (who paid?) — Firebase Auth
3. Subscription state (did they pay, still current?) — Stripe webhook -> Firestore

## The lean path (weekend-feasible)
Use the official Firebase Extension: "Run Subscription Payments with Stripe"
(same project as Heirloom). It creates Checkout Sessions, handles webhooks,
writes subscription status to Firestore, and gives a Customer Portal link
for cancel/update card. No custom webhook code to write/maintain.

### Day 1 (~4-6 hrs build)
- [ ] Firebase Hosting multisite target for Herd Tracker in Heirloom project, deploy current dashboard there (free web.app subdomain)
- [ ] Split build_dashboard.py output: public.json (Latest: last 30d rounds, Herd Signals, Leaderboard teaser) vs premium data in Firestore/Storage with security rules (Archive full, Fresh Powder full, all-time Round Explorer)
- [ ] Firebase Auth: email link + Google, login/logout UI in masthead (broadsheet style)
- [ ] Install/configure Stripe Firebase Extension in TEST mode; create 2 prices in Stripe dashboard (manual, Amrit): Monthly + Annual
- [ ] Gate UI: locked tabs/sections show blurred teaser + Upgrade card, unlock on active subscription doc in Firestore

### Day 2 (~3-5 hrs build + QA)
- [ ] Bookmarks (see below) — piggybacks on Auth+Firestore, ~2-3 hrs
- [ ] Stripe Customer Portal link (cancel/manage) + cancel_at_period_end behaviour (same downgrade policy as Heirloom: no proration/refunds)
- [ ] Test-mode end-to-end QA: checkout with test card, webhook lands, unlock, cancel, re-lock at period end, failed card
- [ ] Go-live checklist (NOT code): Stripe live-mode activation / business details, live prices + webhook secret, taxes decision (Stripe Tax or manual), refund/support email

Total: ~8-11 hrs focused build for a test-mode-proven, live-ready MVP.
Custom backend route (Heirloom-style chunks 3-5) = ~a week. Not needed here.

### Pricing placeholder (Amrit's call)
Indie positioning discussed Oct 21. Placeholder to test: $12/mo or $99/yr.
Price in Stripe dashboard only — changing it later is a new Price, not code.

## Premium features ranked: effort (after Auth exists) vs perceived value
1. Bookmarks / Watchlist — STAR companies, investors, sectors; "My Herd" tab.
   Free prototype in localStorage: ~1 hr, no auth, doesn't persist/sync.
   Premium version in Firestore: ~2-3 hrs. Persists, syncs, and is the hook for alerts.
   Natural upsell: "Get alerted when a bookmarked company/investor raises again" (v1.1, needs weekly-pull diff + email via Resend — half a day more).
2. Unlock Archive (2013-19 vs 2026 Thesis Archaeology) — already built, just gate it. ~0 hrs extra.
3. Unlock Fresh Powder full table — already built, just gate it. ~0 hrs extra.
4. Full Round Explorer: all-time search/filter by company/investor/sector/stage/date + CSV export — filters ~2 hrs, CSV ~30 lines. Free = last 30 days only. This is the cleanest free/premium split.
5. Buzzword Index / thesis-wave depth charts — aggregations on data already in hand, ~2-3 hrs per chart.
6. Backlog already scoped Oct 21 (each an aggregation, few hrs): dry-powder clock, stage-inflation index, co-herd graph, fund-size creep, déjà vu detector.

## NOT in a weekend
- Team/seats billing, per-founder raise-targeting packs, API/data subscriptions, automated Fresh Powder extraction (current table is curated — regex alone produced garbage firm names Oct 21)
