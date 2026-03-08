#!/usr/bin/env python3
"""
M&A Deal Tracker Dashboard
Fetches news via Google News RSS, extracts facts with Claude (facts only, no inference),
and generates an interactive HTML dashboard.

Commands:
  python dashboard.py update    Fetch latest news and regenerate dashboard
  python dashboard.py add       Add a new deal (interactive)
  python dashboard.py delete    Delete a deal (interactive)
  python dashboard.py list      List all configured deals
"""

import json
import os
import re
import sys
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
DEALS_FILE = SCRIPT_DIR / "deals.json"
OUTPUT_FILE = SCRIPT_DIR / "index.html"
MAX_ARTICLES_PER_DEAL = 7
MAX_ARTICLE_CHARS = 4000

# --- Claude Fact Extraction Prompt ---
SYSTEM_PROMPT = """You are a strict M&A fact extractor. Your only job is to extract explicitly stated facts from news articles.

ABSOLUTE RULES:
1. Extract ONLY information explicitly stated in the provided articles. Never infer, speculate, or add context.
2. If an article uses uncertain language ("expected", "could", "may", "likely", "reportedly") — preserve that exact hedging in the fact text and set "hedged": true.
3. Never combine facts from different articles to draw new conclusions.
4. If specific information is not reported, return an empty array for that category.
5. Do not assess, evaluate, or comment on the facts — only extract them.
6. Accuracy is paramount. When in doubt, omit."""


# ────────────────────────────────────────────────
# Deal Management
# ────────────────────────────────────────────────

def load_deals():
    if not DEALS_FILE.exists():
        return {"deals": []}
    with open(DEALS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_deals(data):
    with open(DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ────────────────────────────────────────────────
# News Fetching
# ────────────────────────────────────────────────

def _ensure_pkg(pkg, import_name=None):
    name = import_name or pkg
    try:
        return __import__(name)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                       check=True, capture_output=True)
        return __import__(name)


def fetch_google_news(query, max_results=5):
    feedparser = _ensure_pkg("feedparser")
    encoded = urllib.parse.quote(query)
    url = (f"https://news.google.com/rss/search"
           f"?q={encoded}&hl=en-US&gl=US&ceid=US:en")
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            # Google News appends " - Source Name" to titles
            title_clean = re.sub(r"\s+-\s+\S.*$", "", title).strip()
            articles.append({
                "title": title_clean or title,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": re.sub(r"<[^>]+>", "", entry.get("summary", "")),
                "source": entry.get("source", {}).get("title", "Unknown"),
            })
        return articles
    except Exception as e:
        print(f"  Warning: RSS fetch failed for '{query}': {e}")
        return []


def fetch_article_content(url):
    """Try to scrape article body text. Returns None on failure or paywall."""
    try:
        requests = _ensure_pkg("requests")
        bs4 = _ensure_pkg("beautifulsoup4", "bs4")
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        soup = BeautifulSoup(resp.content, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "button", "noscript"]):
            tag.decompose()

        # Prefer semantic article/main containers
        container = (soup.find("article") or
                     soup.find("main") or
                     soup.find(class_=re.compile(r"article|content|story|body", re.I)) or
                     soup.find("body"))

        if not container:
            return None

        lines = []
        for p in container.find_all(["p", "h2", "h3", "li"]):
            text = p.get_text(separator=" ", strip=True)
            if len(text) > 40:
                lines.append(text)

        result = "\n".join(lines)
        if len(result) < 150:
            return None
        return result[:MAX_ARTICLE_CHARS]

    except Exception:
        return None


def collect_articles_for_deal(deal):
    """Fetch, deduplicate, and enrich articles for a deal."""
    all_articles = []
    seen_urls, seen_titles = set(), set()

    for query in deal.get("search_queries", []):
        print(f"    Searching: {query}")
        for art in fetch_google_news(query):
            key = art["title"][:60].lower()
            if art["link"] not in seen_urls and key not in seen_titles:
                seen_urls.add(art["link"])
                seen_titles.add(key)
                all_articles.append(art)

    print(f"    Found {len(all_articles)} unique articles. Fetching content...")
    for art in all_articles[:6]:
        content = fetch_article_content(art["link"])
        art["full_content"] = content
        status = "ok" if content else "summary only"
        print(f"      [{status}] {art['title'][:65]}")

    return all_articles[:MAX_ARTICLES_PER_DEAL]


# ────────────────────────────────────────────────
# Claude Fact Extraction
# ────────────────────────────────────────────────

def extract_facts(deal_name, articles, client):
    """Call Claude to extract structured facts. Returns dict or None."""
    if not articles:
        return None

    articles_text = ""
    for i, art in enumerate(articles, 1):
        body = art.get("full_content") or art.get("summary", "(no content available)")
        articles_text += (
            f"\n=== ARTICLE {i} ===\n"
            f"Title: {art['title']}\n"
            f"Source: {art['source']}\n"
            f"Published: {art['published']}\n"
            f"URL: {art['link']}\n"
            f"Content:\n{body}\n"
        )

    user_msg = f"""Extract facts from these articles about the M&A deal: {deal_name}

Return ONLY a JSON object with this exact structure:
{{
  "regulatory": [
    {{
      "fact": "verbatim or near-verbatim fact text",
      "hedged": false,
      "article_num": 1,
      "article_title": "...",
      "article_url": "...",
      "article_source": "...",
      "published_date": "..."
    }}
  ],
  "closing_timeline": [ /* same shape */ ],
  "financing": [ /* same shape */ ],
  "latest_news": [ /* same shape, max 6 items */ ]
}}

EXTRACTION GUIDE:
- regulatory: Which bodies are reviewing (DOJ, FTC, EU Commission, CMA, etc.), current status, stated deadlines, stated conditions or remedies requested. Only include if explicitly named.
- closing_timeline: Announced or expected closing date/quarter stated in articles. Any stated conditions to closing or delays.
- financing: Deal value/consideration, payment structure (cash/stock/debt split), named banks or advisors, bond issuances, bridge loans, credit facilities. Only if explicitly stated with specifics.
- latest_news: The most recent significant developments reported across all articles, in chronological order (newest first).
- Set "hedged": true if the article uses uncertain language for that specific fact.
- If no facts are available for a category, return an empty array [].
- Do NOT invent or infer anything not explicitly written in the sources.

ARTICLES:
{articles_text}

Return ONLY the JSON object."""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=3000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    Warning: Could not parse Claude response as JSON: {e}")
        return None
    except Exception as e:
        print(f"    Warning: Claude API error: {e}")
        return None


# ────────────────────────────────────────────────
# HTML Generation
# ────────────────────────────────────────────────

def generate_html(results, output_path=OUTPUT_FILE):
    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")
    data_json = json.dumps(results, ensure_ascii=False, indent=2)
    data_json = data_json.replace("</script>", "<\\/script>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>M&A Deal Tracker</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    *{{font-family:'Inter',sans-serif;}}
    body{{background:#f0f2f5;}}
    .deal-card{{animation:fadeUp .35s ease;}}
    @keyframes fadeUp{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
    .kpi-box{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 20px;}}
    .status-cleared{{background:#dcfce7;color:#15803d;}}
    .status-favorable{{background:#dbeafe;color:#1e40af;}}
    .status-pending{{background:#fef9c3;color:#854d0e;}}
    .status-risk{{background:#ffedd5;color:#9a3412;}}
    .status-blocked{{background:#fee2e2;color:#991b1b;}}
    .status-required{{background:#f3e8ff;color:#6b21a8;}}
    .ms-done{{background:#2563eb;border-color:#2563eb;}}
    .ms-next{{background:#fff;border-color:#2563eb;}}
    .ms-future{{background:#fff;border-color:#94a3b8;}}
    .fin-bar-segment{{display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;color:#fff;min-width:40px;transition:opacity .2s;}}
    .fin-bar-segment:hover{{opacity:.85;}}
    .news-row:hover{{background:#f8fafc;}}
    .news-row{{border-bottom:1px solid #f1f5f9;}}
    .news-row:last-child{{border-bottom:none;}}
    .fact-row{{border-left:3px solid transparent;}}
    .fact-row.hedged{{border-left-color:#f59e0b;}}
    .tag-hedged{{background:#fef3c7;color:#92400e;font-size:.65rem;padding:1px 6px;border-radius:4px;}}
    .section-label{{font-size:.65rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin-bottom:10px;}}
  </style>
</head>
<body class="min-h-screen">

<!-- ═══ HEADER ═══ -->
<header style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);" class="shadow-2xl">
  <div class="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between gap-4">
    <div>
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-black text-sm">M</div>
        <h1 class="text-white text-xl font-bold tracking-tight">M&A Deal Tracker</h1>
      </div>
      <p class="text-slate-500 text-xs mt-1 ml-11">Fact-based · Sources cited · No inference</p>
    </div>
    <div class="flex items-center gap-4">
      <div class="text-right hidden sm:block">
        <div class="text-slate-500 text-xs">Last updated</div>
        <div class="text-slate-200 text-sm font-semibold">{generated_at}</div>
      </div>
      <div class="relative">
        <input type="search" id="search" placeholder="Search..."
               class="bg-white/10 border border-white/20 text-white placeholder-slate-500
                      rounded-lg px-3 py-2 text-sm w-44 focus:outline-none focus:border-blue-400 focus:bg-white/15">
      </div>
      <span id="deal-badge" class="bg-blue-600 text-white text-xs font-bold px-3 py-1.5 rounded-full whitespace-nowrap"></span>
    </div>
  </div>
</header>

<!-- ═══ CLI BAR ═══ -->
<div style="background:#0f172a;border-bottom:1px solid #1e293b;" class="px-6 py-2.5">
  <div class="max-w-7xl mx-auto flex items-center gap-2 text-xs flex-wrap">
    <span class="text-yellow-400 font-bold">$</span>
    <code class="text-emerald-400">python dashboard.py update</code>
    <span class="text-slate-600">·</span>
    <code class="text-emerald-400">python dashboard.py add</code>
    <span class="text-slate-600">·</span>
    <code class="text-emerald-400">python dashboard.py delete</code>
    <span class="text-slate-600">·</span>
    <code class="text-emerald-400">python dashboard.py list</code>
  </div>
</div>

<!-- ═══ CARDS ═══ -->
<main id="cards" class="max-w-7xl mx-auto px-6 py-6 space-y-6"></main>
<div id="no-results" class="hidden text-center py-20 text-slate-400">No deals match your search.</div>

<script>
const DATA = {data_json};

/* ── helpers ── */
function esc(s){{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
function fmt(s){{
  if(!s) return '';
  try{{
    const d=new Date(s);
    if(!isNaN(d)) return d.toLocaleDateString('en-US',{{month:'short',day:'numeric',year:'numeric'}});
  }}catch(e){{}}
  return String(s).slice(0,16);
}}

/* ── STATUS BADGE ── */
const STATUS_MAP={{
  cleared:  ['status-cleared',  '✓ Cleared'],
  favorable:['status-favorable','◎ Favorable'],
  pending:  ['status-pending',  '⏳ Pending'],
  risk:     ['status-risk',     '⚠ Risk'],
  blocked:  ['status-blocked',  '✗ Blocked'],
  required: ['status-required', '◉ Required'],
}};
function statusBadge(s){{
  const [cls,label]=STATUS_MAP[s]||['status-pending','⏳ '+esc(s)];
  return `<span class="text-xs font-semibold px-2.5 py-1 rounded-full ${{cls}}">${{label}}</span>`;
}}

/* ── FINANCING SECTION ── */
function financingHTML(fs){{
  if(!fs||!fs.components||!fs.components.length){{
    return '<p class="text-slate-400 italic text-sm py-2">No financing structure reported in available sources.</p>';
  }}

  /* stacked bar */
  const bar = fs.components.map(c=>
    `<div class="fin-bar-segment" style="width:${{c.pct}}%;background:${{c.color||'#334155'}};"
          title="${{esc(c.label)}}: ${{esc(c.amount)}} (${{c.pct}}%)"
     >${{c.pct}}%</div>`
  ).join('');

  /* bridge note banner */
  const bridgeBanner = fs.bridge_note ? `
    <div style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:10px 14px;margin-bottom:16px;display:flex;gap:8px;align-items:flex-start;">
      <span style="font-size:.85rem;flex-shrink:0;">🔗</span>
      <p style="font-size:.75rem;color:#78350f;line-height:1.5;margin:0;word-break:break-word;overflow-wrap:break-word;">${{esc(fs.bridge_note)}}</p>
    </div>` : '';

  /* breakdown cards — banks support both string[] and {{name,pct,role}}[] */
  const cards = fs.components.map(c=>{{
    /* parties */
    const partiesHTML = (c.parties||[]).length ? `
      <div style="margin-top:10px;">
        <div class="section-label">Equity Providers</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;">
          ${{(c.parties||[]).map(p=>`<span style="background:#f1f5f9;color:#475569;font-size:.65rem;padding:2px 8px;border-radius:4px;white-space:nowrap;">${{esc(p)}}</span>`).join('')}}
        </div>
      </div>` : '';

    /* banks — support string or {{name, pct, role}} */
    const bankItems = (c.banks||[]).map(b=>{{
      if(typeof b==='string') return {{name:b, pct:null, role:null}};
      return b;
    }});
    const banksHTML = bankItems.length ? `
      <div style="margin-top:10px;">
        <div class="section-label">Banks${{fs.bank_pct_disclosed===false ? ' · % split not publicly disclosed' : ''}}</div>
        <div style="display:flex;flex-direction:column;gap:5px;">
          ${{bankItems.map(b=>{{
            const pctBar = b.pct ? `
              <div style="display:flex;align-items:center;gap:6px;flex:1;">
                <div style="flex:1;height:5px;background:#e2e8f0;border-radius:3px;min-width:60px;">
                  <div style="width:${{b.pct}}%;height:100%;background:${{c.color||'#2563eb'}};border-radius:3px;"></div>
                </div>
                <span style="font-size:.65rem;font-weight:700;color:${{c.color||'#2563eb'}};white-space:nowrap;">${{b.pct}}%</span>
              </div>` : '';
            const roleTag = b.role ? `<span style="font-size:.6rem;color:#94a3b8;margin-left:4px;">${{esc(b.role)}}</span>` : '';
            return `
              <div style="display:flex;align-items:center;gap:8px;padding:5px 8px;background:#eff6ff;border-radius:6px;">
                <span style="font-size:.7rem;font-weight:600;color:#1d4ed8;overflow:hidden;text-overflow:ellipsis;">${{esc(b.name||b)}}</span>
                ${{roleTag}}
                ${{pctBar}}
              </div>`;
          }}).join('')}}
        </div>
      </div>` : '';

    return `
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;min-width:0;overflow:hidden;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:6px;">
          <div style="min-width:0;">
            <div style="font-weight:700;color:#0f172a;font-size:.85rem;">${{esc(c.label)}}</div>
            ${{c.sublabel ? `<div style="color:#64748b;font-size:.72rem;margin-top:3px;line-height:1.4;">${{esc(c.sublabel)}}</div>` : ''}}
          </div>
          <div style="text-align:right;flex-shrink:0;">
            <div style="font-size:1.5rem;font-weight:900;color:${{c.color||'#334155'}};line-height:1;">${{esc(c.amount)}}</div>
            <div style="font-size:.65rem;color:#94a3b8;font-weight:600;margin-top:2px;">${{c.pct}}% of total</div>
          </div>
        </div>
        ${{partiesHTML}}
        ${{banksHTML}}
        ${{c.notes ? `<div style="margin-top:10px;font-size:.72rem;color:#64748b;font-style:italic;line-height:1.4;border-top:1px solid #e2e8f0;padding-top:8px;word-break:break-word;overflow-wrap:break-word;">${{esc(c.notes)}}</div>` : ''}}
      </div>`;
  }}).join('');

  return `
    <div style="margin-bottom:16px;">
      <div class="section-label">Structure Overview — ${{esc(fs.total_label||'')}}</div>
      <div style="display:flex;border-radius:8px;overflow:hidden;height:40px;margin-bottom:8px;">${{bar}}</div>
      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        ${{fs.components.map(c=>`
          <div style="display:flex;align-items:center;gap:6px;font-size:.75rem;color:#475569;">
            <span style="width:12px;height:12px;border-radius:3px;flex-shrink:0;background:${{c.color||'#334155'}};"></span>
            ${{esc(c.label)}} · ${{esc(c.amount)}} (${{c.pct}}%)
          </div>`).join('')}}
      </div>
    </div>
    ${{bridgeBanner}}
    <div style="display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));min-width:0;">${{cards}}</div>`;
}}

/* ── REGULATORY TABLE ── */
function regulatoryHTML(tracker){{
  if(!tracker||!tracker.length){{
    return '<p class="text-slate-400 italic text-sm py-2">No regulatory information reported in available sources.</p>';
  }}
  const rows = tracker.map(r=>{{
    const src = r.source_url
      ? `<a href="${{esc(r.source_url)}}" target="_blank" rel="noopener noreferrer"
            class="text-blue-600 hover:underline text-xs font-medium">Source →</a>`
      : '';
    const notInSrcBadge = r.not_in_sources
      ? `<span style="display:inline-block;font-size:.6rem;background:#f3f4f6;color:#6b7280;border:1px solid #d1d5db;padding:1px 7px;border-radius:4px;margin-top:5px;">Standard process · not confirmed in sources</span>`
      : '';
    return `
      <tr class="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
        <td class="py-3 px-4 text-sm font-semibold text-slate-700 whitespace-nowrap">${{esc(r.jurisdiction)}}</td>
        <td class="py-3 px-4 text-sm text-slate-600 whitespace-nowrap">${{esc(r.body)}}</td>
        <td class="py-3 px-4">${{statusBadge(r.status)}}</td>
        <td class="py-3 px-4 text-sm text-slate-600 leading-snug">
          <div>${{esc(r.notes||'')}}</div>
          ${{notInSrcBadge}}
        </td>
        <td class="py-3 px-4 whitespace-nowrap">
          ${{r.source_date ? `<div class="text-xs text-slate-400 mb-1">${{esc(r.source_date)}}</div>` : ''}}
          ${{src || (r.not_in_sources ? '<span class="text-xs text-slate-300">—</span>' : '')}}
        </td>
      </tr>`;
  }}).join('');

  return `
    <div class="overflow-x-auto rounded-xl border border-slate-200">
      <table class="w-full min-w-[600px]">
        <thead>
          <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
            <th class="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Jurisdiction</th>
            <th class="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Regulator / Body</th>
            <th class="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
            <th class="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Notes</th>
            <th class="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Source</th>
          </tr>
        </thead>
        <tbody class="bg-white">${{rows}}</tbody>
      </table>
    </div>`;
}}

/* ── TIMELINE ── */
function timelineHTML(milestones){{
  if(!milestones||!milestones.length) return '';

  /* Each milestone column is 148px wide; connector fills the gap */
  const cols = milestones.map((m,i)=>{{
    const isDone = m.status==='completed';
    const isNext = m.status==='upcoming';

    const dotBg     = isDone ? '#2563eb'  : 'white';
    const dotBorder = isDone ? '#2563eb'  : isNext ? '#2563eb' : '#cbd5e1';
    const dotColor  = isDone ? 'white'    : isNext ? '#2563eb' : '#94a3b8';
    const labelColor= isDone ? '#0f172a'  : isNext ? '#1d4ed8' : '#94a3b8';
    const dateColor = isDone ? '#2563eb'  : isNext ? '#3b82f6' : '#94a3b8';
    const labelW    = isDone ? '700'      : isNext ? '700'     : '400';

    const connectorColor = (isDone && i < milestones.length-1) ? '#2563eb' : '#e2e8f0';
    const connector = i < milestones.length-1 ? `
      <div style="flex:1;height:2px;background:${{connectorColor}};margin-top:19px;min-width:32px;"></div>` : '';

    return `
      <div style="display:flex;align-items:flex-start;flex-shrink:0;">
        <div style="display:flex;flex-direction:column;align-items:center;width:148px;">
          <!-- dot -->
          <div style="
            width:40px;height:40px;border-radius:50%;
            background:${{dotBg}};border:2.5px solid ${{dotBorder}};
            display:flex;align-items:center;justify-content:center;
            font-size:.8rem;font-weight:900;color:${{dotColor}};
            flex-shrink:0;box-shadow:0 0 0 4px ${{isDone?'rgba(37,99,235,.1)':isNext?'rgba(37,99,235,.08)':'transparent'}};
          ">${{isDone ? '✓' : i+1}}</div>
          <!-- label block — full width, no overflow -->
          <div style="margin-top:12px;text-align:center;width:100%;padding:0 8px;box-sizing:border-box;">
            <div style="font-size:.72rem;font-weight:${{labelW}};color:${{labelColor}};line-height:1.35;word-break:break-word;">
              ${{esc(m.label)}}
            </div>
            <div style="font-size:.68rem;color:${{dateColor}};margin-top:4px;font-weight:${{isDone?'600':'400'}};">
              ${{esc(m.date)}}
            </div>
          </div>
        </div>
        ${{connector}}
      </div>`;
  }}).join('');

  return `
    <div style="overflow-x:auto;padding:4px 2px 16px;">
      <div style="display:flex;align-items:flex-start;min-width:${{milestones.length*148}}px;">
        ${{cols}}
      </div>
    </div>`;
}}

/* ── LATEST NEWS ── */
function newsHTML(news){{
  if(!news||!news.length)
    return '<p class="text-slate-400 italic text-sm py-2">No news reported in available sources.</p>';
  return news.map(n=>{{
    const hedged = n.hedged ? '<span class="tag-hedged ml-1.5">Uncertain</span>' : '';
    return `
      <div class="news-row px-5 py-3.5">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 text-right" style="width:64px;">
            <div class="text-xs font-bold text-slate-500">${{fmt(n.published_date)}}</div>
            <div class="text-xs text-slate-400 mt-0.5 leading-tight">${{esc(n.article_source||'')}}</div>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm text-slate-800 leading-relaxed">${{esc(n.fact)}}${{hedged}}</p>
            ${{n.article_url ? `<a href="${{esc(n.article_url)}}" target="_blank" rel="noopener noreferrer"
                class="text-xs text-blue-600 hover:underline font-medium mt-1 inline-block">View article →</a>` : ''}}
          </div>
        </div>
      </div>`;
  }}).join('');
}}

/* ── SECTION WRAPPER ── */
function section(title, icon, content, accentColor){{
  return `
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="flex items-center gap-3 px-6 py-4 border-b border-slate-100"
           style="border-left:4px solid ${{accentColor||'#e2e8f0'}}">
        <span class="text-lg">${{icon}}</span>
        <h3 class="font-bold text-slate-800">${{title}}</h3>
      </div>
      <div class="px-6 py-4">${{content}}</div>
    </div>`;
}}

/* ── DEAL CARD ── */
function cardHTML(result, idx){{
  const d  = result.deal || {{}};
  const f  = result.facts || {{}};
  const fs = result.financing_structure;
  const rt = result.regulatory_tracker;
  const tl = result.timeline_milestones;
  const kp = result.kpis || {{}};
  const arts = result.articles || [];
  const upd = fmt(result.last_updated) || '—';

  /* KPI: regulatory summary */
  const regCleared = (rt||[]).filter(r=>r.status==='cleared'||r.status==='favorable').length;
  const regPending = (rt||[]).filter(r=>r.status==='pending'||r.status==='risk'||r.status==='blocked').length;
  const regTotal   = (rt||[]).length;

  /* KPI boxes */
  const kpiBoxes = `
    <div class="kpi-box">
      <div style="color:rgba(255,255,255,.5);font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Enterprise Value</div>
      <div style="color:#fff;font-size:1.4rem;font-weight:900;line-height:1.1;">${{esc(d.deal_value||kp.deal_value||'—')}}</div>
      ${{d.announced_date ? `<div style="color:rgba(255,255,255,.4);font-size:.7rem;margin-top:4px;">Announced ${{esc(d.announced_date)}}</div>` : ''}}
    </div>
    <div class="kpi-box">
      <div style="color:rgba(255,255,255,.5);font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Expected Close</div>
      <div style="color:#fff;font-size:1.4rem;font-weight:900;line-height:1.1;">${{esc(kp.expected_close||(tl&&tl.length?tl[tl.length-1].date:null)||'—')}}</div>
      ${{kp.deal_type ? `<div style="color:rgba(255,255,255,.4);font-size:.7rem;margin-top:4px;">${{esc(kp.deal_type)}}</div>` : ''}}
    </div>
    ${{regTotal ? `
    <div class="kpi-box">
      <div style="color:rgba(255,255,255,.5);font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Regulatory</div>
      <div style="display:flex;align-items:baseline;gap:6px;">
        <span style="color:#4ade80;font-size:1.4rem;font-weight:900;line-height:1.1;">${{regCleared}}</span>
        <span style="color:rgba(255,255,255,.4);font-size:.8rem;">cleared</span>
        <span style="color:rgba(255,255,255,.2);">/</span>
        <span style="color:#fbbf24;font-size:1.4rem;font-weight:900;line-height:1.1;">${{regPending}}</span>
        <span style="color:rgba(255,255,255,.4);font-size:.8rem;">pending</span>
      </div>
      <div style="color:rgba(255,255,255,.4);font-size:.7rem;margin-top:4px;">${{regTotal}} jurisdictions tracked</div>
    </div>` : ''}}`;

  /* sources strip */
  const sourcesHTML = arts.length ? `
    <div class="bg-slate-50 border-t border-slate-200 px-6 py-3 flex flex-wrap gap-2 items-center">
      <span class="text-xs text-slate-400 font-semibold uppercase tracking-wider mr-1">Sources</span>
      ${{arts.map(a=>`<a href="${{esc(a.link)}}" target="_blank" rel="noopener noreferrer" title="${{esc(a.title)}}"
          class="text-xs bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 px-2.5 py-1 rounded-lg transition-colors"
        >${{esc(a.source)}}</a>`).join('')}}
    </div>` : '';

  return `
    <div class="deal-card rounded-2xl overflow-hidden shadow-sm border border-slate-200"
         data-search="${{esc((d.name+' '+d.buyer+' '+d.target+' '+(d.sector||'')).toLowerCase())}}">

      <!-- ▸ HEADER -->
      <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);" class="px-6 py-5">
        <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span style="color:#fff;font-size:1.25rem;font-weight:800;">${{esc(d.buyer)}}</span>
              <span style="color:#2563eb;font-size:1.1rem;">→</span>
              <span style="color:#fff;font-size:1.25rem;font-weight:800;">${{esc(d.target)}}</span>
            </div>
            ${{d.sector ? `<div style="color:#94a3b8;font-size:.75rem;margin-top:4px;">${{esc(d.sector)}}</div>` : ''}}
          </div>
          <div class="flex items-center gap-2">
            <span style="background:rgba(37,99,235,.3);color:#93c5fd;font-size:.65rem;font-weight:700;padding:3px 10px;border-radius:999px;border:1px solid rgba(147,197,253,.2);">IN PROGRESS</span>
            <span style="color:rgba(255,255,255,.35);font-size:.7rem;">Data as of ${{upd}}</span>
          </div>
        </div>
        <!-- KPIs -->
        <div class="grid gap-3" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr))">
          ${{kpiBoxes}}
        </div>
      </div>

      <!-- ▸ BODY SECTIONS -->
      <div class="space-y-4 p-4" style="background:#f0f2f5;">

        ${{section('Financing Structure', '💰', financingHTML(fs||null), '#2563eb')}}

        ${{section('Regulatory Tracker', '🏛️', regulatoryHTML(rt||null), '#f59e0b')}}

        ${{tl&&tl.length ? section('Deal Timeline', '📅', timelineHTML(tl), '#10b981') : ''}}

        ${{section('Latest News', '📰', newsHTML(f.latest_news||null), '#8b5cf6')}}

      </div>

      ${{sourcesHTML}}
    </div>`;
}}

/* ── RENDER ── */
function render(data){{
  document.getElementById('cards').innerHTML = data.map((r,i)=>cardHTML(r,i)).join('');
  const n = data.length;
  document.getElementById('deal-badge').textContent = n+' Active Deal'+(n!==1?'s':'');
}}

/* ── SEARCH ── */
document.getElementById('search').addEventListener('input',function(){{
  const q=this.value.toLowerCase().trim();
  let v=0;
  document.querySelectorAll('.deal-card').forEach(c=>{{
    const m=!q||c.dataset.search.includes(q)||c.textContent.toLowerCase().includes(q);
    c.style.display=m?'':'none';
    if(m)v++;
  }});
  document.getElementById('deal-badge').textContent=v+' Active Deal'+(v!==1?'s':'');
  document.getElementById('no-results').classList.toggle('hidden',v>0);
}});

render(DATA);
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# ────────────────────────────────────────────────
# CLI Commands
# ────────────────────────────────────────────────

def get_client():
    try:
        import anthropic
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "anthropic"],
                       check=True, capture_output=True)
        import anthropic

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("\nANTHROPIC_API_KEY not set.")
        key = input("Paste your Anthropic API key: ").strip()
        print(f"\nTo avoid this prompt, add to ~/.zshrc:\n"
              f"  export ANTHROPIC_API_KEY='{key}'\n")
    return anthropic.Anthropic(api_key=key)


def cmd_update():
    print("\n── M&A Dashboard Update ──────────────────────────\n")
    data = load_deals()
    if not data["deals"]:
        print("No deals configured. Run: python dashboard.py add")
        return

    client = get_client()
    results = []

    for deal in data["deals"]:
        print(f"\n  Deal: {deal['name']}")
        articles = collect_articles_for_deal(deal)

        facts = None
        if articles:
            print(f"    Extracting facts with Claude (temperature=0)...")
            facts = extract_facts(deal["name"], articles, client)
            total = sum(len(v) for v in (facts or {}).values() if isinstance(v, list))
            print(f"    Extracted {total} verified facts.")
        else:
            print("    No articles found — skipping extraction.")

        results.append({
            "deal": deal,
            "articles": articles,
            "facts": facts,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

    output = generate_html(results)
    print(f"\n  Dashboard written to: {output}")

    import webbrowser
    webbrowser.open(f"file://{output.resolve()}")
    print("  Opened in browser.\n")

    # Optional: GitHub Pages push
    git_dir = SCRIPT_DIR / ".git"
    if git_dir.exists():
        push = input("Push to GitHub Pages? (y/n): ").strip().lower()
        if push == "y":
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            subprocess.run(["git", "-C", str(SCRIPT_DIR), "add", "index.html"], check=True)
            subprocess.run(["git", "-C", str(SCRIPT_DIR), "commit", "-m",
                            f"dashboard: update {ts}"], check=True)
            subprocess.run(["git", "-C", str(SCRIPT_DIR), "push"], check=True)
            print("Pushed to GitHub.")


def cmd_add():
    print("\n── Add New Deal ──────────────────────────────────\n")
    name = input("Deal display name (e.g. 'Exxon / Pioneer'): ").strip()
    if not name:
        print("Name is required.")
        return

    buyer = input("Buyer company: ").strip()
    target = input("Target company: ").strip()
    deal_value = input("Deal value (e.g. '$60B') [optional]: ").strip()
    announced = input("Announced date (e.g. 'Oct 2023') [optional]: ").strip()
    sector = input("Sector (e.g. 'Energy', 'Media') [optional]: ").strip()

    default_queries = [
        f"{buyer} {target} acquisition",
        f"{buyer} {target} merger regulatory approval",
        f"{name} deal closing",
    ]
    print(f"\nDefault search queries:\n" +
          "\n".join(f"  • {q}" for q in default_queries))
    custom = input("\nAdd extra queries (comma-separated) [optional]: ").strip()

    queries = default_queries
    if custom:
        queries += [q.strip() for q in custom.split(",") if q.strip()]

    deal_id = re.sub(r"[^a-z0-9]+", "-", name.lower())[:30].strip("-")

    new = {"id": deal_id, "name": name, "buyer": buyer, "target": target,
           "search_queries": queries}
    if deal_value:  new["deal_value"] = deal_value
    if announced:   new["announced_date"] = announced
    if sector:      new["sector"] = sector

    data = load_deals()
    data["deals"].append(new)
    save_deals(data)
    print(f"\n  Added '{name}'. Run 'python dashboard.py update' to fetch news.\n")


def cmd_delete():
    data = load_deals()
    if not data["deals"]:
        print("No deals to delete.")
        return

    print("\n── Delete Deal ───────────────────────────────────\n")
    for i, d in enumerate(data["deals"], 1):
        print(f"  {i}. {d['name']}")

    try:
        n = int(input("\nEnter number to delete (0 to cancel): "))
        if n == 0:
            return
        if 1 <= n <= len(data["deals"]):
            removed = data["deals"].pop(n - 1)
            save_deals(data)
            print(f"\n  Deleted: {removed['name']}\n")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")


def cmd_list():
    data = load_deals()
    if not data["deals"]:
        print("No deals configured.")
        return

    print(f"\n── Configured Deals ({len(data['deals'])}) ─────────────────────\n")
    for i, d in enumerate(data["deals"], 1):
        print(f"  {i}. {d['name']}")
        if d.get("deal_value"):     print(f"     Value:     {d['deal_value']}")
        if d.get("announced_date"): print(f"     Announced: {d['announced_date']}")
        if d.get("sector"):         print(f"     Sector:    {d['sector']}")
        print(f"     Queries:   {len(d.get('search_queries', []))}")
        print()


def print_help():
    print(__doc__)


COMMANDS = {
    "update": cmd_update,
    "add": cmd_add,
    "delete": cmd_delete,
    "list": cmd_list,
    "help": print_help,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    fn = COMMANDS.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown command: {cmd}")
        print_help()
