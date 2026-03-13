#!/usr/bin/env python3
"""Bootstrap dashboard with pre-extracted, source-cited facts."""
import json
from pathlib import Path
from dashboard import generate_html

results = [
  # ══════════════════════════════════════════════════════════════
  # DEAL 1 — Paramount Skydance / Warner Bros. Discovery
  # ══════════════════════════════════════════════════════════════
  {
    "deal": {
      "id": "paramount-wbd",
      "name": "Paramount Skydance / Warner Bros. Discovery",
      "buyer": "Paramount Skydance",
      "target": "Warner Bros. Discovery",
      "deal_value": "$110B enterprise · $31/share cash",
      "announced_date": "Feb 27, 2026",
      "sector": "Media & Entertainment",
      "search_queries": [
        "Paramount Skydance Warner Bros Discovery acquisition merger 2026",
        "WBD Paramount Skydance regulatory antitrust 2026",
        "Warner Bros Discovery closing timeline shareholder vote"
      ]
    },

    # ── KPIs ───────────────────────────────────────────────────
    "kpis": {
      "deal_value": "$110B enterprise",
      "expected_close": "Q3 2026",
      "deal_type": "All-Cash · $31.00/share"
    },

    # ── FINANCING STRUCTURE ─────────────────────────────────────
    # Source: NBC News (Feb 27, 2026) + Reuters (Mar 2, 2026)
    # % split per bank not publicly disclosed.
    "financing_structure": {
      "total_label": "$110B enterprise value",
      "bank_pct_disclosed": False,
      "components": [
        {
          "label": "Equity",
          "sublabel": "New Class B Shares @ $16.02/share · no financing conditions",
          "amount": "$47B",
          "pct": 43,
          "color": "#2563eb",
          "parties": ["Ellison Family", "RedBird Capital Partners"],
          "notes": (
            "New Class B shares issued to Ellison Family and RedBird Capital Partners. "
            "No financing conditions attached. (NBC News, Feb 27, 2026)"
          )
        },
        {
          "label": "Debt",
          "sublabel": "$39B new debt + $15B WBD existing bridge refinancing",
          "amount": "$54B",
          "pct": 57,
          "color": "#1e3a5f",
          "banks": [
            {"name": "Bank of America", "pct": None, "role": "Lender"},
            {"name": "Citigroup",       "pct": None, "role": "Lender"},
            {"name": "Apollo",          "pct": None, "role": "Lender"}
          ],
          "notes": (
            "Fully committed debt package. No financing conditions. "
            "$39B in new debt + $15B to refinance WBD's existing bridge facility. "
            "% split among lenders not publicly disclosed. "
            "Combined entity carries ~$79B net debt post-close. "
            "Credit agencies downgraded to 'junk' status. (Reuters, Mar 2, 2026)"
          )
        }
      ]
    },

    # ── REGULATORY TRACKER ──────────────────────────────────────
    # Sources: Reuters (Mar 2), CNBC (Mar 3), The Guardian (Mar 5)
    # Note: DOJ, FCC, State AGs confirmed by name in sources.
    # EU Commission and CMA: requirement confirmed in sources; specific body names
    # are standard for this deal type — not named in available sources.
    "regulatory_tracker": [
      {
        "jurisdiction": "United States",
        "body": "DOJ / HSR Act",
        "status": "favorable",
        "notes": (
          "HSR 10-day waiting period expired after DOJ second request. Company stated: 'there is no statutory "
          "impediment in the U.S. to closing.' However, per Bloomberg (Mar 2), deal 'remains under active review "
          "by US antitrust officials' though odds of a legal challenge are described as 'low.' Netflix CLO stated "
          "HSR expiration 'does not signal DOJ approval' and Paramount is 'a long way' from securing all needed approvals."
        ),
        "source_url": "https://www.bloomberg.com/news/articles/2026-03-02/paramount-deal-still-under-us-review-with-challenge-unlikely",
        "source_date": "Mar 2–3, 2026"
      },
      {
        "jurisdiction": "United States",
        "body": "FCC",
        "status": "favorable",
        "notes": (
          "FCC Chairman Brendan Carr told CNBC the deal is 'cleaner' than Netflix's proposal and will be approved "
          "'pretty quickly.' Carr said Netflix 'would have a very difficult path' getting regulatory approval compared "
          "to Paramount's deal."
        ),
        "source_url": "https://www.cnbc.com/2026/03/03/fcc-chair-brendan-carr-wbd-paramount-merger-deal-netflix.html",
        "source_date": "Mar 3, 2026"
      },
      {
        "jurisdiction": "United States — State AGs",
        "body": "Multi-State Attorneys General",
        "status": "risk",
        "notes": (
          "California AG Rob Bonta confirmed open California DOJ investigation: 'Paramount/Warner Bros is not a done deal' (X post). "
          "Bonta stated deal has 'many regulatory hurdles' and he 'wouldn't be surprised if multiple states working together.' "
          "Coalition of 28 public interest groups (led by Center for American Progress Action Fund) wrote open letter to state AGs "
          "calling for legal challenge, arguing merger reduces major film studios from 5 to 4. "
          "Democratic Attorneys General Association hired Rohit Chopra (former CFPB director, former FTC commissioner) to coordinate "
          "state-level consumer protection and antitrust enforcement strategy. "
          "Congressional Democrats escalated opposition: Sen. Elizabeth Warren (D-MA) called deal 'an antitrust disaster threatening "
          "higher prices and fewer choices for American families'; Sen. Cory Booker (D-NJ) notified Ellison to preserve communications "
          "with President Trump. Former DOJ antitrust chief Bill Baer: 'a combined lawsuit by state attorneys general presents a real "
          "threat.' Paramount retained Makan Delrahim (former DOJ Antitrust Division chief) to lead its federal regulatory strategy."
        ),
        "source_url": "https://deadline.com/2026/03/california-attorney-general-antitrust-paramount-warner-deal-1236745088/",
        "source_date": "Mar 6–13, 2026"
      },
      {
        "jurisdiction": "European Union",
        "body": "European Commission (DG COMP)",
        "status": "pending",
        "notes": "EU regulatory approval confirmed as required in sources. Reviewing body (European Commission, DG COMP) is standard for EU merger control; not named by name in available sources. No timeline or status reported.",
        "source_url": "https://www.theguardian.com/media/2026/mar/05/paramount-warner-bros-mega-merger-antitrust-threats",
        "source_date": "Mar 5, 2026",
        "not_in_sources": True
      },
      {
        "jurisdiction": "United Kingdom",
        "body": "CMA",
        "status": "pending",
        "notes": "UK regulatory approval confirmed as required in sources. Reviewing body (Competition and Markets Authority) is standard for UK merger control; not named by name in available sources. No timeline or status reported.",
        "source_url": "https://www.theguardian.com/media/2026/mar/05/paramount-warner-bros-mega-merger-antitrust-threats",
        "source_date": "Mar 5, 2026",
        "not_in_sources": True
      }
    ],

    # ── TIMELINE ────────────────────────────────────────────────
    "timeline_milestones": [
      {"label": "Deal Signed",       "date": "Feb 27, 2026",       "status": "completed"},
      {"label": "Shareholder Vote",  "date": "Mar 20, 2026",       "status": "upcoming"},
      {"label": "Regulatory Close",  "date": "TBD",                "status": "future"},
      {"label": "Expected Close",    "date": "Q3 2026",            "status": "future"}
    ],

    # ── RAW FACTS (for reference / automated update fallback) ───
    "facts": {
      "regulatory": [],
      "closing_timeline": [
        {
          "fact": "Transaction expected to close Q3 2026. Shareholder vote expected in early spring 2026.",
          "hedged": False,
          "article_source": "NBC News",
          "article_url": "https://www.nbcnews.com/business/media/warner-bros-discovery-signs-merger-agreement-paramount-skydance-rcna261035",
          "published_date": "Fri, 27 Feb 2026"
        },
        {
          "fact": "If not closed by September 30, 2026, WBD shareholders receive a $0.25 per share quarterly 'ticking fee.' Paramount Skydance included a $7 billion reverse termination fee if regulators block the deal.",
          "hedged": False,
          "article_source": "NBC News",
          "article_url": "https://www.nbcnews.com/business/media/warner-bros-discovery-signs-merger-agreement-paramount-skydance-rcna261035",
          "published_date": "Fri, 27 Feb 2026"
        }
      ],
      "financing": [],
      "latest_news": [
        {
          "fact": (
            "Mar 12, 2026 — CA AG Bonta posted on X: 'Paramount/Warner Bros is not a done deal. The California Department "
            "of Justice has an open investigation, and we intend to be vigorous in our review.' Democratic Attorneys General "
            "Association hired Rohit Chopra (former CFPB director, former FTC commissioner) to lead its new Consumer "
            "Protection and Affordability Working Group — coordinating multi-state antitrust enforcement strategy."
          ),
          "hedged": False,
          "article_source": "Deadline (CA AG exclusive) · American Banker (Chopra hire)",
          "article_url": "https://deadline.com/2026/03/california-attorney-general-antitrust-paramount-warner-deal-1236745088/",
          "published_date": "Thu, 12 Mar 2026"
        },
        {
          "fact": (
            "Early Mar 2026 — Congressional Democrats escalated opposition. Sen. Elizabeth Warren (D-MA) called the deal "
            "'an antitrust disaster threatening higher prices and fewer choices for American families.' "
            "Sen. Cory Booker (D-NJ) notified Ellison to preserve communications with President Trump. "
            "Democratic legislators called for scrutiny of Skydance's ownership of CBS News and CNN under the same company."
          ),
          "hedged": False,
          "article_source": "Time / NBC News",
          "article_url": "https://time.com/7381536/paramount-warner-netflix-larry-david-ellison-donald-trump-democrats-reactions/",
          "published_date": "Fri, 27 Feb 2026"
        },
        {
          "fact": (
            "Mar 10–11, 2026 — WBD shareholder vote on the Paramount merger confirmed for March 20, 2026 at 8:00 a.m. ET "
            "(date originally announced Feb 17 in official WBD press release; retained for Paramount vote after deal "
            "signed Feb 27). Paramount CEO David Ellison described the deal as 'pro-competitive, pro-consumer, and good "
            "for the overall creative economy,' citing a combined subscriber base of 'over 200 million basically gross "
            "subscribers.' Paramount retained Makan Delrahim — former head of the DOJ Antitrust Division under President "
            "Trump — to lead the company's federal regulatory strategy."
          ),
          "hedged": False,
          "article_source": "PRNewswire / WBD IR (Feb 17, 2026) · Variety (Mar 10, 2026)",
          "article_url": "https://www.prnewswire.com/news-releases/warner-bros-discovery-sets-special-meeting-date-of-march-20-2026-and-unanimously-recommends-shareholders-vote-for-netflix-merger-warner-bros-discovery-to-initiate-discussions-with-paramount-skydance-for-their-best-and-final-o-302689237.html",
          "published_date": "Tue, 10 Mar 2026"
        },
        {
          "fact": (
            "Mar 6, 2026 — Coalition of 28 public interest groups led by Center for American Progress Action Fund wrote "
            "open letter to state AGs calling for legal challenge to the merger. Letter argues the combination reduces "
            "major film studios from 5 to 4. California AG Rob Bonta confirmed California's independent antitrust review; "
            "stated deal has 'many regulatory hurdles' and he 'wouldn't be surprised if multiple states working together.'"
          ),
          "hedged": False,
          "article_source": "Deadline",
          "article_url": "https://deadline.com/2026/03/paramount-warner-bros-state-attorneys-general-1236746176/",
          "published_date": "Fri, 06 Mar 2026"
        },
        {
          "fact": (
            "Mar 5, 2026 — A March 4 Senate antitrust subcommittee hearing on the merger was canceled by Sen. Mike Lee (R-UT). "
            "Former DOJ antitrust chief Bill Baer warned 'a combined lawsuit by state attorneys general presents a real threat.'"
          ),
          "hedged": False,
          "article_source": "The Guardian",
          "article_url": "https://www.theguardian.com/media/2026/mar/05/paramount-warner-bros-mega-merger-antitrust-threats",
          "published_date": "Thu, 05 Mar 2026"
        },
        {
          "fact": (
            "Mar 3, 2026 — FCC Chairman Brendan Carr told CNBC Paramount's deal is 'cleaner' than Netflix's and will be "
            "approved 'pretty quickly.' HSR 10-day waiting period expired; company stated 'there is no statutory impediment "
            "in the U.S. to closing.' Netflix CLO responded that HSR expiration 'does not signal DOJ approval' and Paramount "
            "is 'a long way' from securing all needed approvals."
          ),
          "hedged": False,
          "article_source": "CNBC / Bloomberg",
          "article_url": "https://www.cnbc.com/2026/03/03/fcc-chair-brendan-carr-wbd-paramount-merger-deal-netflix.html",
          "published_date": "Tue, 03 Mar 2026"
        },
        {
          "fact": (
            "Mar 2, 2026 — Bloomberg: deal 'remains under active review by US antitrust officials,' though odds of legal "
            "challenge described as 'low.' Reuters confirmed combined entity will carry ~$79B net debt; credit agencies "
            "downgraded to 'junk' status."
          ),
          "hedged": True,
          "article_source": "Bloomberg / Reuters",
          "article_url": "https://www.bloomberg.com/news/articles/2026-03-02/paramount-deal-still-under-us-review-with-challenge-unlikely",
          "published_date": "Mon, 02 Mar 2026"
        },
        {
          "fact": (
            "Feb 27, 2026 — Warner Bros. Discovery signed merger agreement with Paramount Skydance. WBD's board determined "
            "Paramount's $110.9B revised offer was a superior proposal to Netflix's prior bid (Feb 26). WBD paid Netflix "
            "a $2.8B termination fee after Netflix declined to match. Deal includes $7B reverse termination fee if "
            "regulators block the merger, and a $0.25/share/quarter ticking fee if not closed by Sep 30, 2026."
          ),
          "hedged": False,
          "article_source": "NBC News",
          "article_url": "https://www.nbcnews.com/business/media/warner-bros-discovery-signs-merger-agreement-paramount-skydance-rcna261035",
          "published_date": "Fri, 27 Feb 2026"
        }
      ]
    },

    "articles": [
      {"title": "California AG Cites Antitrust Concerns Over Paramount-WBD Merger: EXCLU", "link": "https://deadline.com/2026/03/california-attorney-general-antitrust-paramount-warner-deal-1236745088/", "source": "Deadline", "published": "Thu, 12 Mar 2026"},
      {"title": "'An Antitrust Disaster': Democrats Decry Path Clearing for WBD Merger With Trump-Allied Paramount", "link": "https://time.com/7381536/paramount-warner-netflix-larry-david-ellison-donald-trump-democrats-reactions/", "source": "Time", "published": "Fri, 27 Feb 2026"},
      {"title": "Warner Bros to Engage With Paramount but Recommends Netflix Deal at March 20 Shareholder Vote", "link": "https://variety.com/2026/film/news/warner-bros-discovery-paramount-talks-netflix-shareholder-vote-1236665083/", "source": "Variety", "published": "Tue, 17 Feb 2026"},
      {"title": "Public Interest Groups Call For State AGs To Challenge Paramount-WBD", "link": "https://deadline.com/2026/03/paramount-warner-bros-state-attorneys-general-1236746176/", "source": "Deadline", "published": "Fri, 06 Mar 2026"},
      {"title": "Paramount-Warner Bros mega-merger could still face 'real threats'", "link": "https://www.theguardian.com/media/2026/mar/05/paramount-warner-bros-mega-merger-antitrust-threats", "source": "The Guardian", "published": "Thu, 05 Mar 2026"},
      {"title": "Fears mount at CNN and CBS News over merger", "link": "https://www.latimes.com/entertainment-arts/business/story/2026-03-05/fears-mount-cnn-cbs-news-paramount-wbd-merger", "source": "Los Angeles Times", "published": "Thu, 05 Mar 2026"},
      {"title": "FCC Chair: WBD-Paramount deal is 'cleaner' than Netflix's, will be approved 'quickly'", "link": "https://www.cnbc.com/2026/03/03/fcc-chair-brendan-carr-wbd-paramount-merger-deal-netflix.html", "source": "CNBC", "published": "Tue, 03 Mar 2026"},
      {"title": "Paramount's $110B Warner Bros. Deal Still Under US Antitrust Review", "link": "https://www.bloomberg.com/news/articles/2026-03-02/paramount-deal-still-under-us-review-with-challenge-unlikely", "source": "Bloomberg", "published": "Mon, 02 Mar 2026"},
      {"title": "Warner Bros. Discovery signs merger agreement with Paramount Skydance", "link": "https://www.nbcnews.com/business/media/warner-bros-discovery-signs-merger-agreement-paramount-skydance-rcna261035", "source": "NBC News", "published": "Fri, 27 Feb 2026"},
    ],
    "last_updated": "2026-03-13T12:00:00Z"
  },

  # ══════════════════════════════════════════════════════════════
  # DEAL 2 — ENGIE / UK Power Networks
  # ══════════════════════════════════════════════════════════════
  {
    "deal": {
      "id": "engie-ukpn",
      "name": "ENGIE / UK Power Networks",
      "buyer": "ENGIE",
      "target": "UK Power Networks",
      "deal_value": "£10.5B equity · £15.8B enterprise",
      "announced_date": "Feb 25, 2026",
      "sector": "Energy / Electricity Distribution",
      "search_queries": [
        "ENGIE UK Power Networks acquisition regulatory 2026",
        "ENGIE UKPN deal closing CMA Ofgem approval",
        "ENGIE UK Power Networks financing ABB"
      ]
    },

    # ── KPIs ───────────────────────────────────────────────────
    "kpis": {
      "deal_value": "£10.5B equity",
      "expected_close": "Mid-2026",
      "deal_type": "All-Cash Acquisition"
    },

    # ── FINANCING STRUCTURE ─────────────────────────────────────
    # Sources: ENGIE press release (Feb 25) + MarketScreener (Mar 2)
    # Note: all amounts in EUR. % split per bank not publicly disclosed.
    #
    # HOW THE BRIDGE WORKS:
    # At signing (Feb 25), ENGIE drew a full acquisition bridge from BofA + BNP Paribas
    # covering the entire £10.5B (~€12.6B) purchase price.
    # The bridge is then progressively refinanced by 3 tranches:
    #   1. ABB equity €3B — DONE (Feb 27, 2026)
    #   2. Debt/hybrid €5B — pending issuance
    #   3. Asset disposals €4B — repay residual debt by 2028
    "financing_structure": {
      "total_label": "~€12B permanent financing · Bridge: BofA + BNP Paribas",
      "bank_pct_disclosed": False,
      "bridge_note": (
        "Bridge loan mechanics: At signing (Feb 25, 2026), ENGIE drew a full acquisition bridge "
        "from Bank of America and BNP Paribas covering the entire purchase price (~€12.6B). "
        "This bridge is being progressively refinanced via three tranches: (1) €3B ABB equity — "
        "completed Feb 27, 2026; (2) ~€5B debt & hybrid issuance — pending; "
        "(3) ~€4B asset disposal proceeds by 2028, which will repay the residual bridge/debt. "
        "M&A financial advisors: Rothschild & Co and BNP Paribas advised ENGIE. "
        "Source: ENGIE press release + MarketScreener (Feb 25–Mar 2, 2026)."
      ),
      "components": [
        {
          "label": "Equity — ABB ✓ Completed",
          "sublabel": "Accelerated bookbuilding · €28/share · 4.4% dilution · Feb 27, 2026",
          "amount": "€3B",
          "pct": 25,
          "color": "#16a34a",
          "parties": ["Institutional investors (private placement)"],
          "banks": [
            {"name": "BofA Securities",   "pct": None, "role": "Global Coordinator"},
            {"name": "BNP Paribas",        "pct": None, "role": "Global Coordinator"},
            {"name": "Barclays",           "pct": None, "role": "Co-Bookrunner"},
            {"name": "Crédit Agricole",    "pct": None, "role": "Co-Bookrunner"},
            {"name": "J.P. Morgan",        "pct": None, "role": "Co-Bookrunner"},
            {"name": "Société Générale",   "pct": None, "role": "Co-Bookrunner"}
          ],
          "notes": (
            "French State (Agence des Participations de l'État) held 23.6% and did not participate; "
            "stake reduced to ~22.7%. 180-day lock-up on new shares. Described as 'one of the largest "
            "share capital increases of a French issuer in recent years.' (MarketScreener, Mar 2, 2026)"
          )
        },
        {
          "label": "Debt & Hybrid — Pending",
          "sublabel": "~€5B debt + hybrid issuance · replaces bridge tranche",
          "amount": "€5B",
          "pct": 42,
          "color": "#1e3a5f",
          "banks": [
            {"name": "Bank of America", "pct": None, "role": "Bridge / Lead"},
            {"name": "BNP Paribas",     "pct": None, "role": "Bridge / Lead"}
          ],
          "notes": (
            "Bridge arranged by BofA + BNP Paribas at signing. Permanent debt & hybrid "
            "issuance pending. % split between debt and hybrid instruments not disclosed. "
            "ENGIE stated financing 'will help maintain its strong investment grade credit rating.' "
            "(ENGIE press release + MarketScreener)"
          )
        },
        {
          "label": "Asset Disposals — Future",
          "sublabel": "ENGIE portfolio asset sales · target completion by 2028",
          "amount": "€4B",
          "pct": 33,
          "color": "#64748b",
          "parties": ["ENGIE asset disposal program"],
          "notes": (
            "Disposal proceeds (~€4B by 2028) will repay the residual acquisition bridge/debt, "
            "permanently reducing leverage. Specific assets to be sold not disclosed. "
            "This tranche is a future cash inflow, not upfront financing — the bridge covers "
            "this gap until disposals are completed. (ENGIE press release, Feb 25, 2026)"
          )
        }
      ]
    },

    # ── REGULATORY TRACKER ──────────────────────────────────────
    # Source: ENGIE press release (Feb 25, 2026) + Reuters (Feb 26, 2026)
    # Note: ENGIE press release states deal is "subject to regulatory approvals"
    # but does not name specific UK bodies. Ofgem, CMA, and NSIA are the standard
    # regulatory approvals required for this deal type — added with disclaimer.
    # HKEx shareholder vote is confirmed in sources (mandatory under HKEx Listing Rules).
    "regulatory_tracker": [
      {
        "jurisdiction": "United Kingdom",
        "body": "Ofgem",
        "status": "pending",
        "notes": "Change of control of an electricity distribution licence requires Ofgem consent under the Electricity Act 1989 and the Distribution Licence (Standard Condition 19). Mandatory for any acquisition of a UK licensed electricity distributor. Not named in available sources — standard regulatory requirement for this deal type.",
        "source_url": None,
        "source_date": None,
        "not_in_sources": True
      },
      {
        "jurisdiction": "United Kingdom",
        "body": "CMA",
        "status": "pending",
        "notes": "UK merger control review under the Enterprise Act 2002. UKPN UK revenues exceed the £70M jurisdictional threshold. CMA has public interest powers for regulated utility acquisitions. Not named in available sources — standard regulatory requirement for this deal type.",
        "source_url": None,
        "source_date": None,
        "not_in_sources": True
      },
      {
        "jurisdiction": "United Kingdom",
        "body": "NSIA (Investment Security Unit)",
        "status": "pending",
        "notes": "Mandatory notification under the National Security and Investment Act 2021. Energy is a mandatory notification sector; electricity distribution qualifies. The Secretary of State must clear or call in the acquisition within 30 working days. Not named in available sources — standard regulatory requirement for foreign acquisitions of UK energy infrastructure.",
        "source_url": None,
        "source_date": None,
        "not_in_sources": True
      },
      {
        "jurisdiction": "Hong Kong",
        "body": "HKEx Listing Rules (SFC)",
        "status": "required",
        "notes": "Independent shareholder approval required at seller entities per HKEx Listing Rules (very substantial disposal): CK Infrastructure Holdings (40%), Power Assets Holdings (40%), CK Asset Holdings (20%). Confirmed in ENGIE press release as a closing condition.",
        "source_url": "https://en.newsroom.engie.com/news/engie-announces-the-acquisition-of-uk-power-networks-uk-s-best-in-class-electricity-distribution-network-42503-314df.html",
        "source_date": "Feb 25, 2026"
      }
    ],

    # ── TIMELINE ────────────────────────────────────────────────
    "timeline_milestones": [
      {"label": "Deal Announced",    "date": "Feb 25, 2026",  "status": "completed"},
      {"label": "ABB Completed",     "date": "Feb 27, 2026",  "status": "completed"},
      {"label": "HK Shareholder Vote","date": "TBD",          "status": "upcoming"},
      {"label": "Expected Close",    "date": "Mid-2026",      "status": "future"}
    ],

    # ── RAW FACTS ───────────────────────────────────────────────
    "facts": {
      "regulatory": [],
      "closing_timeline": [
        {
          "fact": "The acquisition is expected to close mid-2026, subject to regulatory approvals and approval by independent shareholders of Hong Kong-listed parent companies.",
          "hedged": False,
          "article_source": "Reuters / ENGIE Newsroom",
          "article_url": "https://www.reuters.com/business/engie-shares-surge-14-billion-uk-power-grid-deal-2026-02-26/",
          "published_date": "Thu, 26 Feb 2026"
        }
      ],
      "financing": [],
      "latest_news": [
        {
          "fact": "Mar 2, 2026 — ENGIE completed its ~€3B accelerated bookbuilding (ABB) capital increase. Issued 107,142,857 new shares at €28/share (3.2% discount to Feb 26 close). Described as 'one of the largest share capital increases of a French issuer in recent years.' French State stake reduced from 23.6% to ~22.7% (did not participate).",
          "hedged": False,
          "article_source": "MarketScreener",
          "article_url": "https://www.marketscreener.com/news/engie-raises-3-billion-euros-to-finalize-uk-power-networks-acquisition-ce7e5cdcdd8cf620",
          "published_date": "Mon, 02 Mar 2026"
        },
        {
          "fact": "Feb 26, 2026 — ENGIE shares rose as much as 7.6% to €29.49 on announcement day — highest since September 2009 and biggest single-day rise since March 2022.",
          "hedged": False,
          "article_source": "Reuters / Bloomberg",
          "article_url": "https://www.reuters.com/business/engie-shares-surge-14-billion-uk-power-grid-deal-2026-02-26/",
          "published_date": "Thu, 26 Feb 2026"
        },
        {
          "fact": "Feb 25, 2026 — ENGIE announced acquisition of UK Power Networks for £10.5B equity (£15.8B enterprise). ENGIE stated this is its largest-ever acquisition and UK will become its second-largest country of activity. UKPN serves 8.5 million customers and delivers approximately 28% of Britain's distributed electricity. Seller CK Group bypassed major investment banks, using law firm Linklaters LLP internally.",
          "hedged": False,
          "article_source": "ENGIE Newsroom / Bloomberg",
          "article_url": "https://en.newsroom.engie.com/news/engie-announces-the-acquisition-of-uk-power-networks-uk-s-best-in-class-electricity-distribution-network-42503-314df.html",
          "published_date": "Wed, 25 Feb 2026"
        }
      ]
    },

    "articles": [
      {"title": "Engie to Buy UK Power Networks for $14.2 Billion From Hong Kong's CK Group", "link": "https://www.wsj.com/business/deals/engie-to-buy-uk-power-networks-for-14-2-billion-from-hong-kongs-ck-group-96c282d4", "source": "WSJ", "published": "Thu, 26 Feb 2026"},
      {"title": "Engie shares surge on $14 billion UK power grid deal", "link": "https://www.reuters.com/business/engie-shares-surge-14-billion-uk-power-grid-deal-2026-02-26/", "source": "Reuters", "published": "Thu, 26 Feb 2026"},
      {"title": "Engie Jumps After £10.5 Billion Deal to Buy UK Power Networks", "link": "https://www.bloomberg.com/news/articles/2026-02-25/france-s-engie-to-buy-uk-power-networks-for-10-5-billion", "source": "Bloomberg", "published": "Thu, 26 Feb 2026"},
      {"title": "Engie Raises 3 Billion Euros to Finalize UK Power Networks Acquisition", "link": "https://www.marketscreener.com/news/engie-raises-3-billion-euros-to-finalize-uk-power-networks-acquisition-ce7e5cdcdd8cf620", "source": "MarketScreener", "published": "Mon, 02 Mar 2026"},
      {"title": "ENGIE announces acquisition of UK Power Networks (press release)", "link": "https://en.newsroom.engie.com/news/engie-announces-the-acquisition-of-uk-power-networks-uk-s-best-in-class-electricity-distribution-network-42503-314df.html", "source": "ENGIE Newsroom", "published": "Wed, 25 Feb 2026"},
    ],
    "last_updated": "2026-03-13T12:00:00Z"
  }
]

# Update deals.json
deals_path = Path(__file__).parent / "deals.json"
deals_data = {"deals": [r["deal"] for r in results]}
with open(deals_path, "w", encoding="utf-8") as f:
    json.dump(deals_data, f, indent=2, ensure_ascii=False)
print("deals.json updated.")

out = generate_html(results, Path(__file__).parent / "index.html")
print(f"Dashboard generated: {out}")

import webbrowser
webbrowser.open(f"file://{out.resolve()}")
print("Opened in browser.")
