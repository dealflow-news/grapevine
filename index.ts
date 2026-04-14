/**
 * grapevine-to-card — Edge Function v1.2
 *
 * Routes:
 *   GET  /health
 *   POST /extract     { note_id }           — enrich existing note (WHISPER or KC)
 *   POST /prescreen   { filename, text?, base64?, mime? }  — batch pre-scan verdict
 *   POST /enrich      { title, text }        — batch KC enrichment
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
  return JSON.parse(cleaned.slice(s, e));
}

const json = (d: unknown, s = 200) =>
  new Response(JSON.stringify(d), { status: s, headers: { ...CORS, 'Content-Type': 'application/json' } });

// ── System prompts ────────────────────────────────────────────────────────────

const SYS_PRESCREEN = `You are an editorial intelligence classifier for V4G — Ventures4Growth, a Benelux M&A advisory firm.
Evaluate if this file should be ingested into the Grapevine Knowledge Base for Benelux lower mid-market M&A professionals (founders, PE, family offices, advisors, EV 5-50M EUR).

Return ONLY valid JSON — no markdown:
{"verdict":"ingest|review|skip","title":"<suggested card title max 12 words>","domain":"01 Sector Deep Dives|02 Strategic Narratives|03 M&A Playbooks|04 Valuation Capital Markets|05 PE Investor Models|06 ETA Entrepreneurial Buyouts|07 Buyer Psychology Deal Dynamics|08 Trends Benchmarking Reports|09 Editorial Signal Intelligence","tier":"A|B|C","source_type":"BOOK_OR_ARTICLE_EXTRACT|RESEARCH_REPORT|OWN_WHITEPAPER|INTERNAL_MEMO","benelux_fit":"direct|analogous|background","reason":"<one sentence why>"}

Verdict: ingest=directly useful for Benelux deal work | review=potentially useful but unclear | skip=personal/unrelated/admin/pure graphic`;

const SYS_WHISPER = `You are a senior editorial intelligence editor at a Benelux M&A platform. Distil a WHISPER_NOTE pattern candidate into a reusable KNOWLEDGE_CARD.
Audience: founders, PE partners, family offices, boutique M&A advisors — Benelux lower mid-market.
Return ONLY valid JSON:
{"title":"<max 12 words>","core_insight":"<2-3 sentences>","deal_implication":"<2-3 sentences>","misread_risk":"<1-2 sentences>","best_use":["<use case 1>","<use case 2>","<use case 3>"]}`;

const SYS_KC = `You are a senior editorial intelligence editor at a Benelux M&A platform. Extract a reusable KNOWLEDGE_CARD from a source document.
Audience: founders, PE partners, family offices, boutique M&A advisors — Benelux lower mid-market.
Ground everything in the actual document content. Keep core_insight under 180 words. English only.
Return ONLY valid JSON:
{"title":"<max 12 words>","core_insight":"<2-3 sentences>","deal_implication":"<2-3 sentences>","misread_risk":"<1-2 sentences>","best_use":["<use case 1>","<use case 2>","<use case 3>"]}`;

// ── Main handler ──────────────────────────────────────────────────────────────
Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

  const AK   = Deno.env.get('ANTHROPIC_API_KEY')         ?? '';
  const SURL = Deno.env.get('SUPABASE_URL')              ?? '';
  const SKEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
  const db   = supa(SURL, SKEY);

  const path = new URL(req.url).pathname.replace(/.*\/grapevine-to-card/, '') || '/';

  // ── Health ────────────────────────────────────────────────────────────────
  if (path === '/health' || path === '/') {
    return json({ status: 'ok', version: '1.2', anthropic_set: !!AK });
  }

  if (req.method !== 'POST') return json({ error: 'POST required' }, 405);
  if (!AK) return json({ error: 'ANTHROPIC_API_KEY not set' }, 500);

  let body: any = {};
  try { body = await req.json(); } catch { /**/ }

  // ── /prescreen — batch pre-scan ──────────────────────────────────────────
  if (path === '/prescreen') {
    const { filename = '', text = '', base64, mime } = body;
    if (!filename) return json({ error: 'filename required' }, 400);

    let userMsg: any;
    if (base64 && mime) {
      userMsg = [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: mime, data: base64 } },
        { type: 'text', text: `Filename: ${filename}\n\nClassify this image for the Grapevine Knowledge Base.` }
      ]}];
    } else {
      userMsg = `Filename: ${filename}\n\nContent excerpt:\n${text || '(no text — classify from filename only)'}`;
    }

    try {
      const result = await claude(AK, MODEL_HAIKU, SYS_PRESCREEN, userMsg, 300);
      return json(result);
    } catch (e: any) {
      return json({ verdict: 'review', title: filename.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' '),
        domain: '03 M&A Playbooks', tier: 'B', source_type: 'BOOK_OR_ARTICLE_EXTRACT',
        benelux_fit: 'analogous', reason: `Scan failed: ${e.message?.slice(0, 80)}` });
    }
  }

  // ── /enrich — batch KC enrichment ────────────────────────────────────────
  if (path === '/enrich') {
    const { title = '', text = '', country = 'Benelux', sector = 'Cross-sector' } = body;
    if (!title && !text) return json({ error: 'title or text required' }, 400);

    const userMsg = `Document title: ${title}\nCountry: ${country}\nSector: ${sector}\n\nContent:\n${text.slice(0, 8000) || '(no body — use title only)'}`;
    try {
      const result = await claude(AK, MODEL_SONNET, SYS_KC, userMsg, 800);
      return json(result);
    } catch (e: any) {
      return json({ error: `Enrichment failed: ${e.message}` }, 500);
    }
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

    // Flow B: Drop Point KNOWLEDGE_CARD — enrich in-place
    if (source.note_type === 'KNOWLEDGE_CARD') {
      const srcText = (source.body_md || source.body || '').slice(0, 8000);
      const userMsg = `Document title: ${source.title ?? ''}\nCountry: ${source.geo_country ?? 'Benelux'}\nSector: ${source.sector_code ?? 'Cross-sector'}\n\nContent:\n${srcText || '(no body)'}`;
      let extracted: any;
      try { extracted = await claude(AK, MODEL_SONNET, SYS_KC, userMsg); }
      catch (e: any) { return json({ error: `Anthropic: ${e.message}` }, 500); }
      for (const k of ['core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
        if (!extracted[k]) return json({ error: `Missing key: ${k}` }, 500);
      }
      const patch = {
        title: extracted.title || source.title,
        summary_short: extracted.core_insight.slice(0, 300),
        is_ai_derived: true,
        structured_data: { ...sd, core_insight: extracted.core_insight, deal_implication: extracted.deal_implication,
          misread_risk: extracted.misread_risk, best_use: extracted.best_use,
          card_type: sd.card_type || 'library_source', kb_quality: sd.kb_quality || { tier: null, benelux_fit: null } },
      };
      try { await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', patch); }
      catch (e: any) { return json({ error: `DB patch: ${e.message}` }, 500); }
      return json({ ok: true, note_id: noteId, title: extracted.title || source.title, status: source.status, in_place: true });
    }

    // Flow A: WHISPER_NOTE pattern candidate → new KNOWLEDGE_CARD
    if (source.note_type !== 'WHISPER_NOTE') return json({ error: `Unsupported: ${source.note_type}` }, 400);
    if (!sd.pattern_candidate) return json({ error: 'pattern_candidate not set' }, 400);

    const existing = await db(`grapevine_notes?source_ref_id=eq.${noteId}&note_type=eq.KNOWLEDGE_CARD&is_deleted=eq.false&select=note_id,title,status&limit=1`).catch(() => null);
    if (existing?.length) return json({ ok: true, note_id: existing[0].note_id, title: existing[0].title, status: existing[0].status, duplicate: true });

    const userMsg = `pattern_name: ${sd.pattern_name ?? ''}\npattern_rationale: ${sd.pattern_rationale ?? ''}\ntitle: ${source.title ?? ''}\ncountry: ${source.geo_country ?? ''}\nsummary: ${source.summary_short ?? ''}\n\n${(source.body_md ?? '').slice(0, 2000)}${sd.editorial_angle ? `\n\neditorial_angle: ${sd.editorial_angle}` : ''}`;
    let extracted: any;
    try { extracted = await claude(AK, MODEL_SONNET, SYS_WHISPER, userMsg); }
    catch (e: any) { return json({ error: `Anthropic: ${e.message}` }, 500); }
    for (const k of ['title', 'core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
      if (!extracted[k]) return json({ error: `Missing key: ${k}` }, 500);
    }
    const card = {
      body: extracted.core_insight, body_md: extracted.core_insight, note_type: 'KNOWLEDGE_CARD',
      capture_origin: 'whisper_report', title: extracted.title.slice(0, 300),
      summary_short: extracted.core_insight.slice(0, 300), summary_llm: extracted.core_insight.slice(0, 300),
      sensitivity_level: 'PUBLIC', visibility_scope: 'TEAM', intended_audience: 'internal',
      evidence_type: 'COMPOSITE', source_type: 'INTERNAL_MEMO', confidence: 'medium',
      time_sensitivity: 'STRUCTURAL', status: 'draft', review_status: 'pending', link_status: 'unlinked',
      is_ai_derived: true, is_deleted: false, source_ref_type: 'note_id', source_ref_id: noteId,
      derived_from: [{ type: 'grapevine_note', id: noteId, note_type: 'WHISPER_NOTE' }],
      created_by: 'grapevine-to-card-v1.2',
      structured_data: { core_insight: extracted.core_insight, deal_implication: extracted.deal_implication,
        misread_risk: extracted.misread_risk, best_use: extracted.best_use,
        source_pattern_name: sd.pattern_name ?? '', card_type: 'library_source',
        kb_quality: { tier: null, benelux_fit: null } },
      geo_country: source.geo_country ?? 'BE', sector_code: source.sector_code ?? null, language_code: 'en',
    };
    let created: any;
    try { created = await db('grapevine_notes', 'POST', card); }
    catch (e: any) { return json({ error: `DB write: ${e.message}` }, 500); }
    try { await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', { structured_data: { ...sd, pattern_candidate: false } }); } catch { /**/ }
    const nn = Array.isArray(created) ? created[0] : created;
    return json({ ok: true, note_id: nn?.note_id ?? null, title: extracted.title, status: 'draft', source_note_id: noteId });
  }

  return json({ error: 'not found' }, 404);
});
