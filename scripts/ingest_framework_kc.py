#!/usr/bin/env python3
"""
ingest_framework_kc.py — Ingest the 10 hand-crafted Knowledge Cards
from the Grapevine Editorial Base Framework directly into Grapevine.

These are pre-validated, high-quality cards — ingested as active directly.

Usage:
    python ingest_framework_kc.py [--dry-run]
"""
import os, sys, json, httpx, time
from datetime import datetime

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://rirkgpsdcaxnowwmliof.supabase.co')
SUPABASE_KEY = (os.environ.get('SUPABASE_SERVICE_KEY')
                or os.environ.get('SUPABASE_ANON_KEY')
                or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpcmtncHNkY2F4bm93d21saW9mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4NjU2OTYsImV4cCI6MjA4NzQ0MTY5Nn0.zZux0_8odNgdltD7LYF5C_zpRPx0Bdvg6q0omZV72Lg')
DRY_RUN = '--dry-run' in sys.argv

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}

# ── 10 Framework Knowledge Cards ─────────────────────────────────────────────
FRAMEWORK_CARDS = [
  {
    "ebl_id": "KC-001/EBL-0005",
    "title": "Mid-Market Pricing Reality Check — Benelux 2026",
    "core_insight": "Benelux mid-market EV/EBITDA multiples are compressing — sellers anchored at 2021-22 peak levels are negotiating against a market that has repriced. Median EV/EBITDA now 6.0–7.5x (down from 8–9x peak), with Healthcare/Tech commanding a 1.5x premium. Founders who deferred exit decisions since 2022 are now selling into a buyer's market without realising it.",
    "deal_implication": "Professional valuation framing at mandate stage is not optional — it is the first deal-protection move. Use benchmark data to reset seller expectations before any buyer interaction. Founders who enter process with realistic anchors close faster and with fewer post-LOI blow-ups.",
    "misread_risk": "Treating current multiples as a temporary dip rather than a structural repricing. The 8–9x era was the anomaly, not the norm — advisors who frame this as 'wait for recovery' are setting up their clients for repeated disappointment.",
    "best_use": [
        "Mandate onboarding: reset founder price expectations with data before first buyer call",
        "Founder conversation opener when they reference 2021 comparable transactions",
        "Counter-argument when seller refuses valuation below 8x",
        "Content anchor for market update editorial pieces",
    ],
    "library_domain": "ld_valuation_capital",
    "asset_type": "ka_benchmark",
    "asset_class": "contextual",
    "ma_lens": ["ml_sell_side", "ml_valuation_pricing"],
    "strategic_themes": ["th_market_timing", "th_founder_psychology", "th_capital_structure"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-002/EBL-0001",
    "title": "Global PE Dry Powder — The Benelux Translation",
    "core_insight": "Global PE dry powder sits at record ~$2.5T but deployment is slowing. For Benelux mid-market sellers, this creates a paradox: PE has the capital but not the conviction. Average holding periods have extended to 5.5 years as sponsors delay exits. The implication is counter-intuitive — more capital availability does not mean faster processes.",
    "deal_implication": "PE buyers who say 'the market is tough' are not bluffing about conviction — they are under pressure to deploy but require zero-surprise processes. Sellers who present a clean, pre-diligenced dossier with no working capital ambiguity dramatically improve their PE deal probability.",
    "misread_risk": "Interpreting dry powder levels as unconditional buyer enthusiasm. Sponsors are selective precisely because they have options — a messy process or uncertain management team will be passed on regardless of the available capital.",
    "best_use": [
        "Counter PE buyer's 'market is tough' narrative with data",
        "Sell-side prep briefing on PE decision criteria",
        "Investor conversation on deal timing and process design",
        "Editorial backdrop for PE activity pieces",
    ],
    "library_domain": "ld_investor_models_pe",
    "asset_type": "ka_benchmark",
    "asset_class": "contextual",
    "ma_lens": ["ml_pe_investing", "ml_sell_side"],
    "strategic_themes": ["th_market_timing", "th_buyer_psychology", "th_value_creation"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-003/EBL-0013",
    "title": "V4G House Valuation Anchors — Damodaran Applied",
    "core_insight": "Five Damodaran reference points every V4G partner should know by heart: European equity risk premium ~5.5%, small firm premium for SMEs +2–3%, country risk premium BE/NL near zero, cost of equity for typical Benelux mid-market target 10–13%, and implied maximum EV at standard returns. These numbers translate headline multiples into fundamental value logic.",
    "deal_implication": "Never argue multiples — argue cost of equity. When a founder quotes 8x EBITDA from a newspaper headline, reframe: 'At your asking price, a buyer's return would be X% — here is why that does or does not work for them.' This shifts the conversation from opinion to financial logic.",
    "misread_risk": "Applying global or large-cap Damodaran parameters to Benelux SMEs. The small firm premium and illiquidity discount materially change the output — using wrong inputs gives confident-sounding but incorrect valuations.",
    "best_use": [
        "Internal partner reference for valuation conversations",
        "First principles counter to unrealistic seller expectations",
        "Training material for junior analysts",
        "Foundation for vendor loan and earn-out structuring discussions",
    ],
    "library_domain": "ld_valuation_capital",
    "asset_type": "ka_internal_standard",
    "asset_class": "proprietary",
    "ma_lens": ["ml_valuation_pricing", "ml_sell_side"],
    "strategic_themes": ["th_capital_structure", "th_founder_psychology"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-004/EBL-0049",
    "title": "Founder Hesitation Playbook — Three-Phase Model",
    "core_insight": "Founders hesitate at three predictable phases: pre-mandate (identity crisis and legacy anxiety), post-LOI (cold feet as reality sets in), and during DD (information fatigue and loss of control). Most deal failures attributed to 'cold feet' are actually predictable phase-specific reactions that can be managed with the right intervention — if the advisor recognises the phase.",
    "deal_implication": "When a founder goes silent post-LOI, do not chase with deal updates. Instead, address the identity question: 'What does life after this deal look like for you?' The commercial stall is rarely about price — it is about identity, legacy, and fear of irrelevance. Phase-specific responses prevent unnecessary process failures.",
    "misread_risk": "Treating founder hesitation as a negotiation tactic or price signal. Misreading emotional withdrawal as a commercial manoeuvre leads advisors to make concessions that do not solve the real problem — and may actually deepen the founder's distrust.",
    "best_use": [
        "Mandate onboarding: map founder to hesitation archetype",
        "Mid-process intervention when founder communication slows",
        "Team debrief after failed process — identify which phase triggered failure",
        "Editorial angle: 'Why deals die before they start'",
    ],
    "library_domain": "ld_buyer_investor_psychology",
    "asset_type": "ka_failure_pattern",
    "asset_class": "proprietary",
    "ma_lens": ["ml_sell_side", "ml_succession"],
    "strategic_themes": ["th_founder_psychology", "th_succession_transition", "th_key_person_dependency"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-005/EBL-0048",
    "title": "Buyer Conviction Signals — Four-Week Early Read",
    "core_insight": "Buyer seriousness can be read from four signals within the first two weeks of contact: response speed (<48h = serious, >5 days = tourist), operational questions versus financial questions (operations first = integration mindset), team composition in first meeting, and speed of NDA return. These signals predict process commitment with high accuracy.",
    "deal_implication": "Stop investing equal process energy in all interested parties. A buyer who asks about the management team in the first call and returns the NDA within 24 hours has a different probability profile than one who asks only about EBITDA margins and takes two weeks to sign. Screen by conviction signals before investing in data room access.",
    "misread_risk": "Interpreting financial sophistication as buyer seriousness. Some of the most financially articulate buyers are the least committed — they are benchmarking, not buying. Operational curiosity is the stronger signal.",
    "best_use": [
        "Buyer longlist qualification — score each buyer against conviction signals",
        "Process design: sequence introductions to maximise signal capture",
        "Seller briefing: explain why V4G recommends selective process over broad auction",
        "Content piece: 'How to spot a serious buyer in week one'",
    ],
    "library_domain": "ld_buyer_investor_psychology",
    "asset_type": "ka_pattern",
    "asset_class": "proprietary",
    "ma_lens": ["ml_buy_side", "ml_process_execution"],
    "strategic_themes": ["th_buyer_psychology", "th_market_timing"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-006/EBL-0018",
    "title": "Vendor Loan Intelligence — V4G Benelux Benchmarks",
    "core_insight": "Vendor loans are the hidden bridge between seller expectations and buyer affordability in Benelux mid-market transactions. Typical parameters: 10–25% of EV, duration 3–5 years, interest 3–5% above base rate, with standard subordination clauses. Founders who understand vendor loans before negotiations accept them as structuring tools rather than concessions — a critical mindset difference.",
    "deal_implication": "Introduce vendor loan mechanics at mandate stage, not during SPA negotiation. When framed early as a normal structuring instrument, founders approach them constructively. When introduced late as a buyer demand, they trigger loss aversion and often kill deals. Timing of the conversation determines the outcome.",
    "misread_risk": "Treating vendor loans as a sign of buyer weakness or insufficient financing. In the Benelux mid-market, vendor loans are standard practice — their absence in a competitive process is actually unusual. Sellers who refuse them on principle systematically reduce their buyer universe.",
    "best_use": [
        "Mandate onboarding: normalise vendor loan concept before any buyer contact",
        "Structuring conversations when EV gap appears between parties",
        "Training material on deal structuring fundamentals",
        "Counter when seller says 'I want full cash at closing'",
    ],
    "library_domain": "ld_valuation_capital",
    "asset_type": "ka_internal_standard",
    "asset_class": "proprietary",
    "ma_lens": ["ml_sell_side", "ml_valuation_pricing"],
    "strategic_themes": ["th_capital_structure", "th_founder_psychology"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-007/EBL-0037",
    "title": "Platform vs Add-On Decision Tree — PE Buyer Logic",
    "core_insight": "PE buyers evaluate targets through two fundamentally different lenses: platform (standalone leadership position, management depth, market defensibility, >€5M EBITDA) versus add-on (bolt-on synergies, geographic or product extension, integration fit). These lenses drive different valuation logic, different process timelines, and different founder conversations. Misclassifying a platform-quality business as an add-on candidate is a systematic value destruction error.",
    "deal_implication": "Positioning a client as platform-worthy versus accepting add-on classification changes the multiple by 0.5–1.5x and the buyer universe by 80%. The classification decision must be made before mandate, not during process. It determines which funds to approach, which narrative to build, and which management team story to tell.",
    "misread_risk": "Treating EV as the primary classifier. A €3M EBITDA business with dominant regional market share, deep management team, and recurring revenue can be a platform — a €8M EBITDA business with key-person dependency and no management layer below the founder cannot.",
    "best_use": [
        "Pre-mandate positioning decision — platform or add-on?",
        "PE buyer mapping — which funds have active platform searches versus add-on programmes?",
        "Sell-side narrative construction — what makes this a platform story?",
        "Founder briefing on why management depth determines valuation",
    ],
    "library_domain": "ld_investor_models_pe",
    "asset_type": "ka_framework",
    "asset_class": "proprietary",
    "ma_lens": ["ml_pe_investing", "ml_buy_side"],
    "strategic_themes": ["th_platform_build", "th_consolidation", "th_value_creation"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-008/EBL-0015",
    "title": "Private vs Public Pricing Gap — Lincoln PMI Q1 2026",
    "core_insight": "Private market multiples lag public markets by 6–12 months. Lincoln Private Market Index Q1 2026 shows private mid-market multiples at ~7.5x — while public comparable recovery is already reflected in equity markets. This lag creates a timing window: sellers who wait for 'market recovery' are actually waiting for private market repricing that follows with a delay.",
    "deal_implication": "For sellers tempted to wait: the public market recovery they are watching has not yet reached private mid-market pricing. For PE buyers: current private multiples represent a structural buying opportunity relative to public benchmarks — an argument that resonates with LP-facing fund narratives.",
    "misread_risk": "Assuming that public market multiples directly translate to private mid-market transactions. The illiquidity discount, lack of scale premium, and concentration risk systematically widen the gap. Founders watching listed company valuations are benchmarking against an incomparable universe.",
    "best_use": [
        "Counter buyer argument that multiples are too high",
        "Seller briefing on timing — private market lags public market",
        "PE LP narrative: private market opportunity versus public comparables",
        "Quarterly market update content with data anchor",
    ],
    "library_domain": "ld_valuation_capital",
    "asset_type": "ka_benchmark",
    "asset_class": "contextual",
    "ma_lens": ["ml_valuation_pricing", "ml_buy_side"],
    "strategic_themes": ["th_market_timing", "th_buyer_psychology"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-009/EBL-0009",
    "title": "Belux M&A Landscape — Vlerick Market Intelligence",
    "core_insight": "The Belgian M&A market is structurally different from NL and DACH: smaller deal sizes, higher proportion of succession-driven transactions (~55% vs 35% in NL), longer trust-building phases, and stronger preference for bilateral over auction processes. Annual deal count Belgium ~350–400, with family-owned and founder-led businesses dominating the €5–25M segment.",
    "deal_implication": "Belgian founders require a fundamentally different engagement approach than Dutch or German counterparts. Process efficiency is less valued than relationship depth. A V4G partner who invests 6–9 months in trust-building before mandate will consistently outperform transaction-focused advisors who push for speed. This is not inefficiency — it is Belux market reality.",
    "misread_risk": "Applying Dutch or Anglo-Saxon process norms to Belgian mandates. Bilateral exclusivity, longer LOI-to-close timelines, and family council involvement are not obstacles to manage — they are structural features to build the process around.",
    "best_use": [
        "Client pitch: explain V4G's Belgian market approach versus transactional advisors",
        "Anchor for Belgian founder conversations about process timeline",
        "Competitive differentiation: local market intelligence as trust signal",
        "Editorial: Belgium M&A market characterisation pieces",
    ],
    "library_domain": "ld_trends_benchmarking",
    "asset_type": "ka_benchmark",
    "asset_class": "contextual",
    "ma_lens": ["ml_sell_side", "ml_succession"],
    "strategic_themes": ["th_founder_psychology", "th_market_timing", "th_succession_transition"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
  {
    "ebl_id": "KC-010/EBL-0051",
    "title": "Why Deals Die — V4G Top 5 Failure Analysis",
    "core_insight": "80% of Benelux mid-market deal failures trace back to five root causes: DD surprises (35% of failures — undisclosed risks surface during diligence), founder cold feet post-LOI (25% — identity and legacy anxiety peaks at commitment stage), working capital disputes at closing (20% — mechanism misunderstood by seller), buyer withdrawal due to market timing shift (12%), and clause friction in SPA negotiation (8%). Most are preventable with systematic pre-mandate intervention.",
    "deal_implication": "Deal failure is not random — it follows a predictable distribution. Pre-DD readiness investment (financial clean-up, management team documentation, working capital normalisation) addresses the single largest failure category. Mandate acceptance should be conditional on seller commitment to this preparation phase.",
    "misread_risk": "Treating deal failure as buyer fault or market bad luck. Internal analysis consistently shows that advisor-side preparation gaps — particularly around founder expectation setting and DD readiness — are the controllable variable. Advisors who externalise failure miss the improvement opportunity.",
    "best_use": [
        "Mandate onboarding: set expectations on preparation requirements with data",
        "Post-process debrief framework for team learning",
        "Content: 'The five reasons Benelux deals fail' — high engagement editorial",
        "Competitive pitch: 'Here is how we actively prevent the top 5 failure modes'",
    ],
    "library_domain": "ld_playbooks_training",
    "asset_type": "ka_failure_pattern",
    "asset_class": "proprietary",
    "ma_lens": ["ml_sell_side", "ml_process_execution"],
    "strategic_themes": ["th_founder_psychology", "th_key_person_dependency", "th_value_creation"],
    "sector": ["sc_multi_sector"],
    "benelux_fit": "direct",
    "tier": "A",
  },
]

def sb_post(data):
    r = httpx.post(
        f'{SUPABASE_URL}/rest/v1/grapevine_notes',
        json=data,
        headers=HEADERS,
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def main():
    print(f"\n{'='*60}")
    print(f"  Framework KC Ingest  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}  |  {len(FRAMEWORK_CARDS)} cards")
    print(f"{'='*60}\n")

    ok = 0; err = 0

    for i, card in enumerate(FRAMEWORK_CARDS):
        print(f"  [{i+1}/{len(FRAMEWORK_CARDS)}] {card['title'][:65]}")

        note = {
            'note_type':          'KNOWLEDGE_CARD',
            'status':             'active',
            'review_status':      'approved',
            'capture_origin':     'drop_point',
            'source_type':        'INTERNAL_MEMO' if card['asset_class'] == 'proprietary' else 'BOOK_OR_ARTICLE_EXTRACT',
            'evidence_type':      'COMPOSITE',
            'sensitivity_level':  'INTERNALONLY' if card['asset_class'] == 'proprietary' else 'PUBLIC',
            'visibility_scope':   'TEAM',
            'intended_audience':  'internal',
            'time_sensitivity':   'STRUCTURAL',
            'confidence':         'high',
            'link_status':        'link_pending',
            'is_ai_derived':      False,
            'is_deleted':         False,
            'title':              card['title'],
            'body':               card['core_insight'],
            'body_md':            card['core_insight'],
            'summary_short':      card['core_insight'][:300],
            'summary_llm':        card['core_insight'][:300],
            'geo_country':        'BE/NL/LU/FR(N)',
            'language_code':      'en',
            'created_by':         'framework_import_v1',
            'structured_data': {
                'core_insight':     card['core_insight'],
                'deal_implication': card['deal_implication'],
                'misread_risk':     card['misread_risk'],
                'best_use':         card['best_use'],
                'card_type':        'library_source',
                'ebl_id':           card['ebl_id'],
                'kb_quality': {
                    'tier':         card['tier'],
                    'benelux_fit':  card['benelux_fit'],
                },
                'kb_tags': {
                    'library_domain':   card['library_domain'],
                    'asset_type':       card['asset_type'],
                    'asset_class':      card['asset_class'],
                    'ma_lens':          card['ma_lens'],
                    'strategic_themes': card['strategic_themes'],
                    'sector':           card['sector'],
                },
            },
        }

        if DRY_RUN:
            print(f"    ld={card['library_domain']}  at={card['asset_type']}  class={card['asset_class']}")
            ok += 1
            continue

        try:
            result = sb_post(note)
            note_id = result[0]['note_id'] if result else 'unknown'
            print(f"    ✓ {note_id[:8]} — {card['asset_class']} | {card['asset_type']}")
            ok += 1
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:80]}")
            err += 1

        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"  DONE: {ok} ingested  |  {err} errors")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
