# Herd Tracker — Upgrade Plan: Static File → AdSense-Ready Site
Scoped Oct 22, 2026

## Key distinction
AdSense does NOT require a dynamic app. It requires a public, crawlable,
content-rich site on a domain you own.
- The paywall upgrade (Auth + Firestore + Stripe) and the AdSense upgrade
  (multi-page static site + editorial pages + own domain) share only the
  hosting/domain step. They are different builds.
- Premium pages should be ad-free (that's a Pro selling point). Ads live on
  the free public pages.

## Level 1 — Deploy what exists (1-2 hrs)
- Put current dashboard.html on Firebase Hosting (separate hosting config in
  this repo targeting the existing Heirloom project — do not touch Heirloom's
  App Hosting config) or GitHub Pages from this repo
- Result: a live URL. NOT AdSense-ready: web.app / github.io are subdomains
  of domains Amrit doesn't own (AdSense in practice requires your own TLD),
  and one JS-heavy page with embedded data is thin/copied-looking to reviewers.

## Level 2 — The actual upgrade: multi-page static site (1 weekend, ~8-10 hrs)
Still $0 hosting, still no backend. build_dashboard.py becomes a site builder:
- Pages: / (Latest), /archive, /fresh-powder, plus generated entity pages:
  /company/<slug> (~383), /investor/<slug>, /sector/<slug> from rounds.json/funds.json
  -> programmatic SEO: each "X raises $Y" page is searchable and linkable
- Per-page <title>/meta/OpenGraph, sitemap.xml, robots.txt, clean URLs
- Editorial layer (REQUIRED for AdSense, this is content work not code):
  Herd Signals commentary and Thesis Archaeology as real text articles,
  a weekly Herd Report post. Raw aggregated tables alone get rejected as
  "low value content" — original analysis/voice is the approval asset.
- Trust pages: About, Contact, Privacy Policy (must disclose ad cookies), Terms
- Analytics: GA4 + Search Console (~30 min)
- Automation: GitHub Actions weekly cron (fetch -> extract -> build -> deploy)
  — Amrit's established free-scheduler pattern from Heirloom. This is what
  makes it "locked and loaded" instead of a manual rerun.

## AdSense integration itself (the easy part)
- Custom domain required in practice: ~$12/yr (e.g. herdtracker.com or similar
  — availability/TBD by Amrit). Connect in Firebase Hosting (free SSL).
- Amrit-only steps: create AdSense account (his Google account, tax/payment
  details), add site, paste verification code.
- Code: 1 script tag in <head> of the template + manual ad units replacing
  the existing print-style "Advertisement" slots (manual units preserve the
  broadsheet look vs Auto Ads) + ads.txt at domain root. ~30-60 min total.
- Approval clock is Google's: typically days to ~2 weeks after submission,
  assuming the editorial/domain/trust-page boxes above are ticked.

## Money reality check
- Finance/VC is a high-RPM niche, but AdSense at low traffic is pennies.
  Earnings scale with pageviews; the entity-page SEO build is what creates
  pageviews. Early money is still more likely a direct sponsorship slot in
  the weekly Herd Report (already in PRICING.md) than AdSense.
- Do Level 2 for distribution/SEO first; AdSense rides on top for free.

## Level 3 — NOT needed for ads
Next.js rewrite / dynamic app: only needed for the paywall + bookmarks
(see PAYWALL_PLAN.md). Don't conflate the two upgrades.
