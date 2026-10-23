"""Hand-verified fresh funds (Sep-Oct 2026), from published reports found Oct 21, 2026."""
import json, os

BASE = os.path.expanduser("~/workspace/herd-tracker")
funds = [
    {"firm": "BackingMinds", "fund": "Fund III (first close)", "amount": 58e6, "display": "\u20ac50M",
     "date": "2026-10-21", "focus": "Nordic early-stage", "source": "Bebeez via AlphaMaven",
     "url": "https://alpha-maven.com/story/venture-capital/backingminds-raises-eur50-million-in-first-close-of-third-fund-to-invest-in-nordic-startups-bebeez-international"},
    {"firm": "Inovia Capital", "fund": "Venture Fund 6 (first close)", "amount": 200e6, "display": "$200M",
     "date": "2026-10-20", "focus": "AI-native & frontier tech (Montreal)", "source": "VCWire",
     "url": "https://vcwire.tech/2026/10/20/inovia-capital-holds-first-close-of-inovia-venture-fund-6-at-usd200m/"},
    {"firm": "Genesys Capital", "fund": "University Seed Fund (2nd close)", "amount": None, "display": "Undisclosed",
     "date": "2026-10-14", "focus": "Canadian university life sciences (Toronto)", "source": "VCWire",
     "url": "https://vcwire.tech/2026/10/14/genesys-capital-holds-second-close-of-genesys-university-seed-fund/"},
    {"firm": "Sprints", "fund": "Fund V", "amount": 810e6, "display": "\u20ac725M",
     "date": "2026-10-13", "focus": "European growth-stage tech", "source": "Phemex News",
     "url": "https://phemex.com/news/article/european-vc-sprints-closes-725m-fifth-fund-with-over-half-already-deployed-99671"},
    {"firm": "Bain Capital Ventures", "fund": "Fund XI", "amount": 1.6e9, "display": "$1.6B",
     "date": "2026-10-11", "focus": "Early-stage AI", "source": "Connect Money",
     "url": "https://www.connectmoney.com/stories/bain-capital-ventures-raises-1-6b-for-ai-focused-early-stage-fund/"},
    {"firm": "Anti Fund", "fund": "Fund II (opened)", "amount": None, "display": "Undisclosed",
     "date": "2026-10-01", "focus": "Consumer, creator economy (Miami)", "source": "AngelLinx",
     "url": "https://angellinx.ai/marketinsights/which-vc-firms-just-opened-a-new-raise-and-how-founders-can-use-the-window-301"},
    {"firm": "Protego Ventures", "fund": "Fund I", "amount": 125e6, "display": "$125M",
     "date": "2026-09-29", "focus": "Defense tech (Israel)", "source": "TechStartups",
     "url": "https://techstartups.com/2026/09/29/israels-largest-defense-vc-protego-ventures-closes-125m-fund-to-back-ai-drones-and-autonomous-systems/"},
    {"firm": "IVP", "fund": "Fund XIX (opened)", "amount": None, "display": "Undisclosed",
     "date": "2026-09-29", "focus": "Later-stage tech (Series C+)", "source": "AngelLinx",
     "url": "https://angellinx.ai/marketinsights/which-vc-firms-just-opened-a-new-raise-and-how-founders-can-use-the-window-301"},
    {"firm": "Narya Capital", "fund": "Fund III (opened)", "amount": None, "display": "Undisclosed",
     "date": "2026-09-29", "focus": "Defense, manufacturing, healthcare (US heartland)", "source": "AngelLinx",
     "url": "https://angellinx.ai/marketinsights/which-vc-firms-just-opened-a-new-raise-and-how-founders-can-use-the-window-301"},
    {"firm": "8VC", "fund": "AI Fund X (opened)", "amount": None, "display": "Undisclosed",
     "date": "2026-09-25", "focus": "AI, defense, manufacturing, health", "source": "AngelLinx",
     "url": "https://angellinx.ai/marketinsights/which-vc-firms-just-opened-a-new-raise-and-how-founders-can-use-the-window-301"},
    {"firm": "Volition Capital", "fund": "Fund VI (final close)", "amount": 950e6, "display": "$950M",
     "date": "2026-09-11", "focus": "Bootstrapped software, growth equity (Boston)", "source": "Angel Investors Network",
     "url": "https://angelinvestorsnetwork.com/venture-capital/volition-capital-fund-vi-950-million-close"},
]
json.dump(funds, open(f"{BASE}/funds.json", "w"), indent=1)
tot = sum(f["amount"] for f in funds if f["amount"])
print("funds:", len(funds), "disclosed total: $%.2fB" % (tot / 1e9))
