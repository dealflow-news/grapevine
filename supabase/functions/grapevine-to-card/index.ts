/**
 * grapevine-to-card — Edge Function v1.3
 * Adds /tag route + kb_tags taxonomy output to /enrich and /prescreen
 *
 * Routes:
 *   GET  /health
 *   POST /extract    { note_id }              — enrich existing note
 *   POST /prescreen  { filename, text?, ... } — batch pre-scan verdict + tags
 *   POST /enrich     { title, text }          — batch KC enrichment + tags
 *   POST /tag        { note_id }              — tag existing card with kb_tags
 */

const ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages';
const MODEL_SONNET  = 'claude-sonnet-4-6';
const MODEL_HAIKU   = 'claude-haiku-4-5-20251001';

const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, apikey',
};

function supa(url: string, key: string) {
  return async (path: string, method = 'GET', body?: unknown) => {
    const r = await fetch(`${url}/rest/v1/${path}`, {
      method,
      headers: {
        'apikey': key, 'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json',
        'Prefer': method === 'POST' ? 'return=representation' : 'return=minimal',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw new Error(`DB ${method} ${path}: ${r.status} ${await r.text()}`);
    return method === 'GET' || (method === 'POST' && r.status !== 204) ? r.json() : null;
  };
}

// claude() returns parsed JSON — used by all existing routes
async function claude(key: string, model: string, system: string, userMsg: any, maxTokens = 800) {
  const messages = Array.isArray(userMsg) ? userMsg : [{ role: 'user', content: userMsg }];
  const r = await fetch(ANTHROPIC_URL, {
    method: 'POST',
    headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, max_tokens: maxTokens, system, messages }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${await r.text()}`);
  const data = await r.json();
  const text = data.content?.[0]?.text ?? '';
  const cleaned = text.replace(/```json|```/g, '').trim();
  const s = cleaned.indexOf('{'); const e = cleaned.lastIndexOf('}') + 1;
  if (s < 0 || e <= 0) throw new Error(`No JSON in response: ${text.slice(0, 100)}`);
  return JSON.parse(cleaned.slice(s, e));
}

// claudeText() returns raw prose — used by /draft route only
async function claudeText(key: string, model: string, system: string, userMsg: string, maxTokens = 1200): Promise<string> {
  const r = await fetch(ANTHROPIC_URL, {
    method: 'POST',
    headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, max_tokens: maxTokens, system, messages: [{ role: 'user', content: userMsg }] }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${await r.text()}`);
  const data = await r.json();
  return data.content?.[0]?.text ?? '';
}

const json = (d: unknown, s = 200) =>
  new Response(JSON.stringify(d), { status: s, headers: { ...CORS, 'Content-Type': 'application/json' } });

// ── Taxonomy reference (v1.1) ─────────────────────────────────────────────────
const TAXONOMY_PROMPT = `
TAXONOMY v1.2 FINAL — assign canonical codes only:

library_domain (exactly 1):
  ld_sector_heatmaps = Sector Deep Dives & Strategic Heatmaps
  ld_strategic_narratives = Strategic Narratives & Outlooks
  ld_thought_leadership = Thought Leadership & Brand Positioning
  ld_playbooks_training = M&A Playbooks & Deal Training
  ld_editorial_newsfeeds = Editorial Strategy & News Feeds
  ld_valuation_capital = Valuation & Capital Intelligence
  ld_investor_models_pe = Investor Models & PE Insights
  ld_search_ebo = Search & Entrepreneurial Buyouts
  ld_buyer_investor_psychology = Buyer & Investor Psychology
  ld_trends_benchmarking = Trends, Reports & Benchmarking
  ld_insights_library = Insights Library (catch-all — last resort)

asset_type (exactly 1):
  ka_library_source = Library source (book/report/article extract)
  ka_pattern = Pattern (recurring market pattern from signals)
  ka_playbook = Playbook (practical how-to guide)
  ka_framework = Framework (analytical model or classification)
  ka_training_note = Training note
  ka_editorial_angle = Editorial angle (for publishing)
  ka_case_note = Case note (abstracted deal or situation)
  ka_benchmark = Benchmark / reference set
  ka_market_map = Market map / landscape
  ka_signal_digest = Signal digest (bundled signals)
  ka_thesis = Strategic thesis (explicit investment thesis)
  ka_template = Template / reusable tool
  ka_checklist = Checklist / decision gate (tied to specific process gate)
  ka_failure_pattern = Failure pattern (deal failure analysis, root cause, prevention)
  ka_internal_standard = Internal standard (V4G house view, benchmark, norm)
  ka_failure_pattern = Failure pattern (deal failure analysis, prevention, root causes)
  ka_internal_standard = Internal standard (V4G house view, benchmark, proprietary norm)
  ka_failure_pattern = Failure pattern (deal failure analysis & prevention)
  ka_internal_standard = Internal standard / house view (V4G proprietary norms)
  ka_failure_pattern = Failure pattern (deal failure analysis, preventable failure taxonomy)
  ka_internal_standard = Internal standard (house view, V4G benchmark, internal norm)
  ka_failure_pattern = Failure pattern (deal failure analysis, root cause, prevention)
  ka_internal_standard = Internal standard (house view, V4G benchmark, internal norm)

ma_lens (1-2, most specific first):
  ml_buy_side = Buy-side (acquirer strategy)
  ml_sell_side = Sell-side (exit preparation)
  ml_succession = Succession (owner/shareholder transition)
  ml_growth_capital = Growth capital (minority/scale-up)
  ml_mbo_mbi = MBO / MBI (management-led)
  ml_carveout = Carve-out / divestment
  ml_pe_investing = Private equity investing (sponsor logic)
  ml_search_fund = Search / entrepreneurial buyout
  ml_partnerships_jv = Strategic partnership / JV
  ml_post_merger_integration = Post-merger integration
  ml_valuation_pricing = Valuation / pricing
  ml_process_execution = Process execution (auction/bilateral)

strategic_themes (1-3 max):
  th_geographic_expansion = Geographic expansion
  th_product_expansion = Product / service expansion
  th_vertical_integration = Vertical integration
  th_consolidation = Consolidation / roll-up
  th_platform_build = Platform / buy-and-build strategy (platform selection + add-ons)
  th_recurring_revenue = Recurring revenue / contract quality (ARR/MRR, subscription models)
  th_succession_transition = Succession transition
  th_capital_structure = Capital structure (leverage/earn-out)
  th_value_creation = Value creation (post-deal)
  th_governance_alignment = Governance alignment
  th_key_person_dependency = Key-person dependency (valuation, integration, succession risk)
  th_talent_retention = Talent retention & team continuity (earn-out, cultural fit)
  th_founder_psychology = Founder / owner psychology
  th_buyer_psychology = Buyer / investor psychology
  th_digital_enablement = Digital / tech enablement
  th_esg_transition = ESG / transition
  th_regulatory_complexity = Regulatory complexity
  th_market_timing = Market timing / cycle

sector (0-2, sc_multi_sector ONLY if genuinely cross-sector):
  sc_software_it = Software / IT
  sc_healthcare = Healthcare / life sciences
  sc_industrials = Industrials / manufacturing
  sc_business_services = Business services
  sc_financial_services = Financial services / fintech
  sc_consumer = Consumer / retail
  sc_food_agri = Food & agri
  sc_logistics_transport = Logistics / transport
  sc_energy_infra = Energy / infra
  sc_real_estate = Real estate / proptech
  sc_education_training = Education / training (edtech, corporate training)
  sc_multi_sector = Multi-sector / cross-sector

asset_class (exactly 1):
  commodity = widely available (Bain, McKinsey, IMF) — credibility not differentiation
  contextual = reframed with Benelux/V4G lens — you add the angle
  proprietary = only V4G has it (internal memos, patterns, casenotes, failure registers)`;

// ── System prompts ────────────────────────────────────────────────────────────

const SYS_PRESCREEN = `You are an editorial intelligence classifier for V4G — Ventures4Growth, a Benelux M&A advisory firm.
Evaluate if this file should be ingested into the Grapevine Knowledge Base for lower mid-market M&A professionals in the V4G coverage region: Belgium, Netherlands, Luxembourg and Northern France (Hauts-de-France, Grand Est) — EV €5–50M.

${TAXONOMY_PROMPT}

Return ONLY valid JSON — no markdown:
{"verdict":"ingest|review|skip","title":"<suggested title max 12 words>","library_domain":"ld_*","asset_type":"ka_*","asset_class":"commodity|contextual|proprietary","ma_lens":["ml_*"],"strategic_themes":["th_*"],"sector":["sc_*"],"tier":"A|B|C","benelux_fit":"direct=BE/NL/LU/FR(N)|analogous=EU|background"
asset_class: commodity=widely available (Bain/McKinsey/IMF) | contextual=reframed with Benelux lens | proprietary=only V4G has it (internal memos, deal patterns, casenotes),"reason":"<one sentence>"}

Verdict: ingest=directly useful for BE/NL/LU/FR(N) deal work | review=potentially useful | skip=personal/admin/unrelated`;

const SYS_KC_ENRICH = `You are a senior editorial intelligence editor at a Benelux M&A platform.
Extract a reusable KNOWLEDGE_CARD and assign canonical taxonomy tags.
Audience: founders, PE partners, family offices, boutique M&A advisors — BE/NL/LU + Northern France (Hauts-de-France, Grand Est), EV €5–50M.

${TAXONOMY_PROMPT}

Return ONLY valid JSON — no markdown:
{"title":"<max 12 words>","core_insight":"<2-3 sentences>","deal_implication":"<2-3 sentences>","misread_risk":"<1-2 sentences>","best_use":["<use case 1>","<use case 2>","<use case 3>"],"library_domain":"ld_*","asset_type":"ka_*","asset_class":"commodity|contextual|proprietary","ma_lens":["ml_*"],"strategic_themes":["th_*"],"sector":["sc_*"],"benelux_fit":"direct=BE/NL/LU/FR(N)|analogous=EU|background"
asset_class: commodity=widely available (Bain/McKinsey/IMF) | contextual=reframed with Benelux lens | proprietary=only V4G has it (internal memos, deal patterns, casenotes)}`;

const SYS_TAG_ONLY = `You are a senior editorial knowledge curator at a Benelux M&A platform.
Assign canonical taxonomy tags to an existing KNOWLEDGE_CARD. Coverage region: BE/NL/LU + Northern France (Hauts-de-France, Grand Est), EV €5–50M.

${TAXONOMY_PROMPT}

Return ONLY valid JSON — no markdown:
{"library_domain":"ld_*","asset_type":"ka_*","asset_class":"commodity|contextual|proprietary","ma_lens":["ml_*"],"strategic_themes":["th_*"],"sector":["sc_*"],"benelux_fit":"direct=BE/NL/LU/FR(N)|analogous=EU|background"
asset_class: commodity=widely available (Bain/McKinsey/IMF) | contextual=reframed with Benelux lens | proprietary=only V4G has it (internal memos, deal patterns, casenotes),"confidence":"high|medium|low"}`;

const SYS_WHISPER = `You are a senior editorial intelligence editor at a Benelux M&A platform.
Distil a WHISPER_NOTE pattern candidate into a reusable KNOWLEDGE_CARD and assign taxonomy tags.
Audience: founders, PE partners, family offices, boutique M&A advisors — BE/NL/LU + Northern France (Hauts-de-France, Grand Est), EV €5–50M.

${TAXONOMY_PROMPT}

Return ONLY valid JSON:
{"title":"<max 12 words>","core_insight":"<2-3 sentences>","deal_implication":"<2-3 sentences>","misread_risk":"<1-2 sentences>","best_use":["<use case 1>","<use case 2>","<use case 3>"],"library_domain":"ld_*","asset_type":"ka_*","asset_class":"commodity|contextual|proprietary","ma_lens":["ml_*"],"strategic_themes":["th_*"],"sector":["sc_*"]}`;

// ── Briefing Studio draft prompt ──────────────────────────────────────────────
const SYS_DRAFT = `You are an editorial intelligence analyst for V4G — Ventures4Growth, a Benelux lower mid-market M&A advisory firm.
Coverage: Belgium, Netherlands, Luxembourg, Northern France (Hauts-de-France, Grand Est). Deal range: €5–50M EV.
Audience: founders, PE partners, family offices, boutique M&A advisors.

Write sharp, credible editorial content grounded in the intel sources provided.
Use conviction. Reference specific signals. Avoid corporate speak and generic observations.
Protect identities — refer to companies/people by sector or role where needed.

Output rules by format:
- BRIEFING NOTE (200–300 words): structure as Thesis → Evidence → Implication. Concise paragraphs. No bullets unless essential.
- NEWSLETTER PARAGRAPH (100–150 words): punchy editorial paragraph. Strong hook first. Name specific signals. One clear takeaway.
- LINKEDIN POST (150–200 words): insight-led. First line must hook. End with a sharp observation or open question. No hashtag spam.

Return only the final output text. No preamble, no labels, no commentary.`;

// ── Helper: build kb_tags from LLM result ─────────────────────────────────────
function buildKbTags(r: any) {
  return {
    library_domain:    r.library_domain    || 'ld_insights_library',
    asset_type:        r.asset_type        || 'ka_library_source',
    asset_class:       r.asset_class       || null,
    ma_lens:           Array.isArray(r.ma_lens)          ? r.ma_lens.slice(0, 2)          : [],
    strategic_themes:  Array.isArray(r.strategic_themes) ? r.strategic_themes.slice(0, 3) : [],
    sector:            Array.isArray(r.sector)            ? r.sector.slice(0, 2)           : [],
  };
}

// ── Main handler ──────────────────────────────────────────────────────────────
Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

  const AK   = Deno.env.get('ANTHROPIC_API_KEY')         ?? '';
  const SURL = Deno.env.get('SUPABASE_URL')              ?? '';
  const SKEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
  const db   = supa(SURL, SKEY);

  const path = new URL(req.url).pathname.replace(/.*\/grapevine-to-card/, '') || '/';

  if (path === '/health' || path === '/') {
    return json({ status: 'ok', version: '1.7', anthropic_set: !!AK });
  }

  if (req.method !== 'POST') return json({ error: 'POST required' }, 405);
  if (!AK) return json({ error: 'ANTHROPIC_API_KEY not set' }, 500);

  let body: any = {};
  try { body = await req.json(); } catch { /**/ }

  // ── /prescreen ───────────────────────────────────────────────────────────
  if (path === '/prescreen') {
    const { filename = '', text = '', base64, mime } = body;
    if (!filename) return json({ error: 'filename required' }, 400);
    let userMsg: any;
    if (base64 && mime) {
      userMsg = [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: mime, data: base64 } },
        { type: 'text', text: `Filename: ${filename}\n\nClassify this image.` }
      ]}];
    } else {
      userMsg = `Filename: ${filename}\n\nContent excerpt:\n${text || '(no text — classify from filename only)'}`;
    }
    try {
      return json(await claude(AK, MODEL_HAIKU, SYS_PRESCREEN, userMsg, 400));
    } catch (e: any) {
      return json({ verdict: 'review', title: filename.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' '),
        library_domain: 'ld_insights_library', asset_type: 'ka_library_source',
        ma_lens: [], strategic_themes: [], sector: [],
        tier: 'B', benelux_fit: 'analogous', reason: `Scan failed: ${e.message?.slice(0, 80)}` });
    }
  }

  // ── /enrich ──────────────────────────────────────────────────────────────
  if (path === '/enrich') {
    const { title = '', text = '', country = 'Benelux', sector = 'Cross-sector' } = body;
    if (!title && !text) return json({ error: 'title or text required' }, 400);
    const userMsg = `Title: ${title}\nCountry: ${country}\nSector: ${sector}\n\nContent:\n${text.slice(0, 8000) || '(no body)'}`;
    try {
      const r = await claude(AK, MODEL_SONNET, SYS_KC_ENRICH, userMsg, 1000);
      return json({ ...r, kb_tags: buildKbTags(r) });
    } catch (e: any) {
      return json({ error: `Enrichment failed: ${e.message}` }, 500);
    }
  }

  // ── /tag — tag existing card only (B1 backfill) ──────────────────────────
  if (path === '/tag') {
    const noteId = (body.note_id ?? '').trim();
    if (!noteId) return json({ error: 'note_id required' }, 400);
    let rows: any[];
    try {
      rows = await db(`grapevine_notes?note_id=eq.${noteId}&is_deleted=eq.false&select=note_id,title,body_md,structured_data,sector_code&limit=1`);
    } catch (e: any) { return json({ error: `DB fetch: ${e.message}` }, 500); }
    if (!rows?.length) return json({ error: 'Note not found' }, 404);
    const note = rows[0];
    const sd = typeof note.structured_data === 'string' ? JSON.parse(note.structured_data) : (note.structured_data ?? {});
    const userMsg = `Title: ${note.title ?? ''}\nSector: ${note.sector_code ?? 'Unknown'}\n\nCore insight:\n${sd.core_insight ?? ''}\n\nDeal implication:\n${sd.deal_implication ?? ''}\n\nBest use:\n${(sd.best_use ?? []).join('; ')}`;
    let tags: any;
    try {
      tags = await claude(AK, MODEL_HAIKU, SYS_TAG_ONLY, userMsg, 400);
    } catch (e: any) { return json({ error: `Tagging failed: ${e.message}` }, 500); }
    const kbTags = buildKbTags(tags);
    const patch = {
      structured_data: {
        ...sd,
        kb_tags: kbTags,
        // keep existing card_type for backwards compat
        card_type: sd.card_type || 'library_source',
        kb_quality: {
          ...(sd.kb_quality || {}),
          benelux_fit: tags.benelux_fit || sd.kb_quality?.benelux_fit || null,
        },
      },
    };
    try {
      await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', patch);
    } catch (e: any) { return json({ error: `DB patch: ${e.message}` }, 500); }
    return json({ ok: true, note_id: noteId, kb_tags: kbTags, confidence: tags.confidence || 'medium' });
  }

  // ── /extract — enrich existing note ──────────────────────────────────────
  if (path === '/extract') {
    const noteId = (body.note_id ?? '').trim();
    if (!noteId) return json({ error: 'note_id required' }, 400);
    let rows: any[];
    try {
      rows = await db(`grapevine_notes?note_id=eq.${noteId}&is_deleted=eq.false&select=note_id,note_type,title,summary_short,body,body_md,structured_data,geo_country,sector_code&limit=1`);
    } catch (e: any) { return json({ error: `DB fetch: ${e.message}` }, 500); }
    if (!rows?.length) return json({ error: 'Note not found' }, 404);
    const source = rows[0];
    const sd = typeof source.structured_data === 'string' ? JSON.parse(source.structured_data) : (source.structured_data ?? {});

    // Flow B: KNOWLEDGE_CARD — enrich in-place
    if (source.note_type === 'KNOWLEDGE_CARD') {
      const srcText = (source.body_md || source.body || '').slice(0, 8000);
      const userMsg = `Title: ${source.title ?? ''}\nCountry: ${source.geo_country ?? 'Benelux'}\nSector: ${source.sector_code ?? ''}\n\nContent:\n${srcText || '(no body)'}`;
      let extracted: any;
      try { extracted = await claude(AK, MODEL_SONNET, SYS_KC_ENRICH, userMsg, 1000); }
      catch (e: any) { return json({ error: `Anthropic: ${e.message}` }, 500); }
      for (const k of ['core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
        if (!extracted[k]) return json({ error: `Missing key: ${k}` }, 500);
      }
      const kbTags = buildKbTags(extracted);
      const patch = {
        title: extracted.title || source.title,
        summary_short: extracted.core_insight.slice(0, 300),
        is_ai_derived: true,
        structured_data: {
          ...sd,
          core_insight: extracted.core_insight, deal_implication: extracted.deal_implication,
          misread_risk: extracted.misread_risk, best_use: extracted.best_use,
          card_type: sd.card_type || 'library_source',
          kb_quality: { ...(sd.kb_quality || {}), tier: sd.kb_quality?.tier || null, benelux_fit: extracted.benelux_fit || sd.kb_quality?.benelux_fit || null },
          kb_tags: kbTags,
        },
      };
      try { await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', patch); }
      catch (e: any) { return json({ error: `DB patch: ${e.message}` }, 500); }
      return json({ ok: true, note_id: noteId, title: extracted.title || source.title, status: source.status, in_place: true, kb_tags: kbTags });
    }

    // Flow A: WHISPER_NOTE → new KNOWLEDGE_CARD
    if (source.note_type !== 'WHISPER_NOTE') return json({ error: `Unsupported: ${source.note_type}` }, 400);
    if (!sd.pattern_candidate) return json({ error: 'pattern_candidate not set' }, 400);
    const existing = await db(`grapevine_notes?source_ref_id=eq.${noteId}&note_type=eq.KNOWLEDGE_CARD&is_deleted=eq.false&select=note_id,title,status&limit=1`).catch(() => null);
    if (existing?.length) return json({ ok: true, note_id: existing[0].note_id, title: existing[0].title, status: existing[0].status, duplicate: true });
    const userMsg = `pattern_name: ${sd.pattern_name ?? ''}\npattern_rationale: ${sd.pattern_rationale ?? ''}\ntitle: ${source.title ?? ''}\ncountry: ${source.geo_country ?? ''}\nsummary: ${source.summary_short ?? ''}\n\n${(source.body_md ?? '').slice(0, 2000)}${sd.editorial_angle ? `\n\neditorial_angle: ${sd.editorial_angle}` : ''}`;
    let extracted: any;
    try { extracted = await claude(AK, MODEL_SONNET, SYS_WHISPER, userMsg, 1000); }
    catch (e: any) { return json({ error: `Anthropic: ${e.message}` }, 500); }
    for (const k of ['title', 'core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
      if (!extracted[k]) return json({ error: `Missing key: ${k}` }, 500);
    }
    const kbTags = buildKbTags(extracted);
    const card = {
      body: extracted.core_insight, body_md: extracted.core_insight, note_type: 'KNOWLEDGE_CARD',
      capture_origin: 'whisper_report', title: extracted.title.slice(0, 300),
      summary_short: extracted.core_insight.slice(0, 300), summary_llm: extracted.core_insight.slice(0, 300),
      sensitivity_level: 'PUBLIC', visibility_scope: 'TEAM', intended_audience: 'internal',
      evidence_type: 'COMPOSITE', source_type: 'INTERNAL_MEMO', confidence: 'medium',
      time_sensitivity: 'STRUCTURAL', status: 'draft', review_status: 'pending', link_status: 'unlinked',
      is_ai_derived: true, is_deleted: false, source_ref_type: 'note_id', source_ref_id: noteId,
      derived_from: [{ type: 'grapevine_note', id: noteId, note_type: 'WHISPER_NOTE' }],
      created_by: 'grapevine-to-card-v1.3',
      structured_data: {
        core_insight: extracted.core_insight, deal_implication: extracted.deal_implication,
        misread_risk: extracted.misread_risk, best_use: extracted.best_use,
        source_pattern_name: sd.pattern_name ?? '', card_type: 'library_source',
        kb_quality: { tier: null, benelux_fit: extracted.benelux_fit || null },
        kb_tags: kbTags,
      },
      geo_country: source.geo_country ?? 'BE', sector_code: source.sector_code ?? null, language_code: 'en',
    };
    let created: any;
    try { created = await db('grapevine_notes', 'POST', card); }
    catch (e: any) { return json({ error: `DB write: ${e.message}` }, 500); }
    try { await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', { structured_data: { ...sd, pattern_candidate: false } }); } catch { /**/ }
    const nn = Array.isArray(created) ? created[0] : created;
    return json({ ok: true, note_id: nn?.note_id ?? null, title: extracted.title, status: 'draft', source_note_id: noteId, kb_tags: kbTags });
  }

  // ── /draft — Briefing Studio editorial prose generation ─────────────────
  if (path === '/draft') {
    const { thesis_label = '', thesis_prompt = '', format = 'briefing', sources = [] } = body;
    if (!thesis_label) return json({ error: 'thesis_label required' }, 400);
    if (!Array.isArray(sources) || !sources.length) return json({ error: 'sources array required' }, 400);

    const formatLabel: Record<string, string> = {
      briefing:   'BRIEFING NOTE (200–300 words)',
      newsletter: 'NEWSLETTER PARAGRAPH (100–150 words)',
      linkedin:   'LINKEDIN POST (150–200 words)',
    };
    const fmtLabel = formatLabel[format] || formatLabel.briefing;

    const sourceSummaries = (sources as any[]).slice(0, 6).map((s: any, i: number) => {
      const body = (s.body || '').slice(0, 500);
      return `[Source ${i + 1}] ${s.title || '(untitled)'}\nType: ${s.type || 'unknown'}\n${body}`;
    }).join('\n\n---\n\n');

    const userMsg = `Format: ${fmtLabel}

Thesis: ${thesis_label}
Analytical angle: ${thesis_prompt}

Intel sources (${sources.length}):
${sourceSummaries}

Write a ${fmtLabel} grounded in these sources. Surface the signal, name the implication, give the reader a reason to act or think differently.`;

    try {
      const draft = await claudeText(AK, MODEL_SONNET, SYS_DRAFT, userMsg, 1200);
      return json({ ok: true, draft, thesis: thesis_label, format });
    } catch (e: any) {
      return json({ error: `Draft generation failed: ${e.message}` }, 500);
    }
  }

  return json({ error: 'not found' }, 404);
});
