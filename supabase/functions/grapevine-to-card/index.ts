/**
 * grapevine-to-card — Supabase Edge Function v1.0
 * Extracts a KNOWLEDGE_CARD from a pattern-candidate WHISPER_NOTE via Claude Sonnet.
 *
 * Routes:
 *   GET  /grapevine-to-card/health
 *   POST /grapevine-to-card/extract   { "note_id": "uuid" }
 *
 * Secrets: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 */

const ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages';
const MODEL         = 'claude-sonnet-4-6';

const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, apikey',
};

// ── Supabase REST helper (same pattern as kbo-proxy) ─────────────────────
function supa(url: string, key: string) {
  return async (path: string, method = 'GET', body?: unknown) => {
    const r = await fetch(`${url}/rest/v1/${path}`, {
      method,
      headers: {
        'apikey':        key,
        'Authorization': `Bearer ${key}`,
        'Content-Type':  'application/json',
        'Prefer':        method === 'POST' ? 'return=representation' : 'return=minimal',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw new Error(`DB ${method} ${path}: ${r.status} ${await r.text()}`);
    return method === 'GET' || (method === 'POST' && r.status !== 204) ? r.json() : null;
  };
}

// ── KnowledgeCardExtractor prompt ────────────────────────────────────────
const SYSTEM = `You are a senior editorial intelligence editor at a Benelux M&A and dealflow intelligence platform.
Your task: distil a WHISPER_NOTE flagged as a pattern candidate into a KNOWLEDGE_CARD — a durable, reusable knowledge asset for Benelux deal professionals.

Audience: founders aged 55+ considering succession or exit, family offices, PE partners, notaries, boutique M&A lawyers — Benelux lower mid-market (BE/NL/LU + Northern FR), EV €5–50M.
Goal: immediately useful in a real deal conversation. Tone: senior advisory, precise, non-generic.

The card must answer four questions:
1. CORE INSIGHT     — What is the structural pattern, and why is it recurring in this market now? (2–3 sentences, present tense, pattern-level)
2. DEAL IMPLICATION — How should a deal professional change their approach in a founder meeting, origination call, or CIM? (2–3 sentences, actionable)
3. MISREAD RISK     — What is the most dangerous misinterpretation that leads advisors to misjudge the deal or founder? (1–2 sentences, direct)
4. BEST USE         — List 3–5 concrete use cases: "founder conversation opener", "sector origination memo", "CIM angle", "valuation anchor", "newsletter lead"

Operating rules:
- If editorial_angle is provided: treat it as the PRIMARY framing anchor
- If sector_focus is provided: ground deal_implication and best_use in those sectors/geographies
- Synthesise upward — never paraphrase the source note
- Write for broad dealflow audience — reusable across firms
- English only, no hedge words, keep core_insight under 180 words

Return ONLY valid JSON, no markdown fences:
{
  "title": "<Pattern name — sharp, memorable, max 12 words>",
  "core_insight": "<2–3 sentences>",
  "deal_implication": "<2–3 sentences>",
  "misread_risk": "<1–2 sentences>",
  "best_use": ["<use case 1>", "<use case 2>", "<use case 3>"]
}`;

// ── Main handler ──────────────────────────────────────────────────────────
Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

  const ANTHROPIC_KEY = Deno.env.get('ANTHROPIC_API_KEY')          ?? '';
  const SUPA_URL      = Deno.env.get('SUPABASE_URL')               ?? '';
  const SUPA_KEY      = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')  ?? '';
  const db            = supa(SUPA_URL, SUPA_KEY);

  const json = (d: unknown, s = 200) =>
    new Response(JSON.stringify(d), { status: s, headers: { ...CORS, 'Content-Type': 'application/json' } });

  const path = new URL(req.url).pathname.replace(/.*\/grapevine-to-card/, '') || '/';

  // ── Health ──
  if (path === '/health' || path === '/') {
    return json({ status: 'ok', version: '1.0', anthropic_set: !!ANTHROPIC_KEY, supabase_set: !!SUPA_URL });
  }

  if (req.method !== 'POST') return json({ error: 'POST required' }, 405);
  if (!ANTHROPIC_KEY)        return json({ error: 'ANTHROPIC_API_KEY not set' }, 500);

  let body: Record<string, string> = {};
  try { body = await req.json(); } catch { /**/ }

  // ── Extract ──
  if (path === '/extract') {
    const noteId = (body.note_id ?? '').trim();
    if (!noteId) return json({ error: 'note_id required' }, 400);

    // 1. Fetch source WHISPER_NOTE
    let rows: any[];
    try {
      rows = await db(
        `grapevine_notes?note_id=eq.${noteId}&is_deleted=eq.false&select=note_id,note_type,title,summary_short,body_md,structured_data,geo_country,sector_code&limit=1`
      );
    } catch (e: any) {
      return json({ error: `DB fetch failed: ${e.message}` }, 500);
    }

    if (!rows?.length)                          return json({ error: 'Note not found or deleted' }, 404);
    const source = rows[0];
    if (source.note_type !== 'WHISPER_NOTE')    return json({ error: `note_type must be WHISPER_NOTE, got ${source.note_type}` }, 400);

    const sd = typeof source.structured_data === 'string'
      ? JSON.parse(source.structured_data)
      : (source.structured_data ?? {});

    if (!sd.pattern_candidate)                  return json({ error: 'structured_data.pattern_candidate is not true — set it in the UI first' }, 400);

    // 1b. Duplicate guard — return existing card if already extracted
    const existing = await db(
      `grapevine_notes?source_ref_id=eq.${noteId}&note_type=eq.KNOWLEDGE_CARD&is_deleted=eq.false&select=note_id,title,status&limit=1`
    ).catch(() => null);
    if (existing?.length) {
      return json({
        ok:             true,
        note_id:        existing[0].note_id,
        title:          existing[0].title,
        status:         existing[0].status,
        capture_origin: 'whisper_report',
        source_note_id: noteId,
        duplicate:      true,
      });
    }

    // 2. Build prompt

    let userPrompt = `Source WHISPER_NOTE to distil:

PATTERN ANCHOR
pattern_name:      ${sd.pattern_name      ?? '(not set)'}
pattern_rationale: ${sd.pattern_rationale ?? '(not set)'}

SOURCE NOTE
title:   ${source.title         ?? ''}
country: ${source.geo_country   ?? ''}
summary: ${source.summary_short ?? ''}

body excerpt:
${(source.body_md ?? '').slice(0, 2000)}`;

    const editorialAngle = (sd.editorial_angle ?? '').slice(0, 500);
    const sectorFocus    = (sd.sector_focus    ?? '').slice(0, 200);
    if (editorialAngle || sectorFocus) {
      userPrompt += '\n\n--- EDITORIAL FRAMING ---';
      if (editorialAngle) userPrompt += `\neditorial_angle: ${editorialAngle}`;
      if (sectorFocus)    userPrompt += `\nsector_focus:    ${sectorFocus}`;
    }

    // 3. Call Claude Sonnet
    let extracted: any;
    try {
      const r = await fetch(ANTHROPIC_URL, {
        method:  'POST',
        headers: {
          'x-api-key':         ANTHROPIC_KEY,
          'anthropic-version': '2023-06-01',
          'Content-Type':      'application/json',
        },
        body: JSON.stringify({
          model:      MODEL,
          max_tokens: 800,
          system:     SYSTEM,
          messages:   [{ role: 'user', content: userPrompt }],
        }),
      });
      if (!r.ok) throw new Error(`Anthropic ${r.status}: ${await r.text()}`);
      const data    = await r.json();
      const text    = data.content?.[0]?.text ?? '';
      const cleaned = text.replace(/```json|```/g, '').trim();
      const start   = cleaned.indexOf('{');
      const end     = cleaned.lastIndexOf('}') + 1;
      extracted     = JSON.parse(cleaned.slice(start, end));
    } catch (e: any) {
      return json({ error: `Anthropic call failed: ${e.message}` }, 500);
    }

    // Validate required keys
    for (const k of ['title', 'core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
      if (!extracted[k]) return json({ error: `LLM response missing key: ${k}` }, 500);
    }

    // 4. Build KNOWLEDGE_CARD record
    const card = {
      body:             extracted.core_insight,
      body_md:          extracted.core_insight,
      note_type:        'KNOWLEDGE_CARD',
      capture_origin:   'whisper_report',
      title:            extracted.title.slice(0, 300),
      summary_short:    extracted.core_insight.slice(0, 300),
      summary_llm:      extracted.core_insight.slice(0, 300),
      content_kind:     'knowledge_card',
      sensitivity_level: 'PUBLIC',
      visibility_scope:  'TEAM',
      intended_audience: 'internal',
      evidence_type:     'COMPOSITE',
      source_type:       'INTERNAL_MEMO',
      confidence:        'medium',
      time_sensitivity:  'STRUCTURAL',
      status:            'draft',
      review_status:     'pending',
      link_status:       'unlinked',
      is_ai_derived:     true,
      is_deleted:        false,
      source_ref_type:   'note_id',
      source_ref_id:     noteId,
      derived_from:      [{ type: 'grapevine_note', id: noteId, note_type: 'WHISPER_NOTE' }],
      created_by:        'grapevine-to-card-v1',
      structured_data: {
        core_insight:             extracted.core_insight,
        deal_implication:         extracted.deal_implication,
        misread_risk:             extracted.misread_risk,
        best_use:                 extracted.best_use,
        source_pattern_name:      sd.pattern_name ?? '',
        source_pattern_rationale: sd.pattern_rationale ?? '',
        source_whisper_note_id:   noteId,
      },
      geo_country:   source.geo_country ?? 'BE',
      sector_code:   source.sector_code ?? null,
      language_code: 'en',
      note_version:  1,
      is_current:    true,
      gold_status:   'grapevine',
      usable_for:    ['thought_leadership', 'sector_research'],
    };

    // 5. Write to DB
    let created: any;
    try {
      created = await db('grapevine_notes', 'POST', card);
    } catch (e: any) {
      return json({ error: `DB write failed: ${e.message}` }, 500);
    }

    // 6. Clear pattern_candidate on source note — card has been extracted
    try {
      await db(
        `grapevine_notes?note_id=eq.${noteId}`,
        'PATCH',
        { structured_data: { ...sd, pattern_candidate: false } }
      );
    } catch { /* non-critical — card already created */ }

    const newNote = Array.isArray(created) ? created[0] : created;
    return json({
      ok:             true,
      note_id:        newNote?.note_id ?? null,
      title:          extracted.title,
      status:         'draft',
      capture_origin: 'whisper_report',
      source_note_id: noteId,
    });
  }

  return json({ error: 'not found' }, 404);
});
