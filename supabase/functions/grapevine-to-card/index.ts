/**
 * grapevine-to-card — Supabase Edge Function v1.1
 *
 * Routes:
 *   GET  /health
 *   POST /extract   { "note_id": "uuid" }
 *
 * Handles two flows:
 *   A) WHISPER_NOTE with pattern_candidate → new KNOWLEDGE_CARD (existing flow)
 *   B) KNOWLEDGE_CARD from Drop Point with body_md → enrich in-place
 */

const ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages';
const MODEL         = 'claude-sonnet-4-6';

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

// ── System prompt for WHISPER_NOTE → new card ────────────────────────────────
const SYSTEM_WHISPER = `You are a senior editorial intelligence editor at a Benelux M&A and dealflow intelligence platform.
Your task: distil a WHISPER_NOTE flagged as a pattern candidate into a KNOWLEDGE_CARD — a durable, reusable knowledge asset for Benelux deal professionals.

Audience: founders aged 55+ considering succession or exit, family offices, PE partners, notaries, boutique M&A lawyers — Benelux lower mid-market (BE/NL/LU + Northern FR), EV 5-50M EUR.
Goal: immediately useful in a real deal conversation. Tone: senior advisory, precise, non-generic.

The card must answer four questions:
1. CORE INSIGHT     — What is the structural pattern, and why is it recurring in this market now? (2-3 sentences, present tense, pattern-level)
2. DEAL IMPLICATION — How should a deal professional change their approach in a founder meeting, origination call, or CIM? (2-3 sentences, actionable)
3. MISREAD RISK     — What is the most dangerous misinterpretation that leads advisors to misjudge the deal or founder? (1-2 sentences, direct)
4. BEST USE         — List 3-5 concrete use cases

Return ONLY valid JSON, no markdown fences:
{"title":"string","core_insight":"string","deal_implication":"string","misread_risk":"string","best_use":["string"]}`;

// ── System prompt for Drop Point KNOWLEDGE_CARD enrichment ───────────────────
const SYSTEM_KC = `You are a senior editorial intelligence editor at a Benelux M&A and dealflow intelligence platform.
Your task: read a source document and extract a reusable KNOWLEDGE_CARD for Benelux deal professionals.

Audience: founders, family offices, PE partners, boutique M&A advisors — Benelux lower mid-market (BE/NL/LU + Northern FR), EV 5-50M EUR.
Goal: immediately useful in a real deal conversation — not a book summary, but an editorial distillation.

Extract:
1. CORE INSIGHT     — The central structural insight this document offers. Why is this pattern relevant to Benelux M&A? (2-3 sentences, present tense)
2. DEAL IMPLICATION — How should a deal professional apply this in a founder conversation, origination call, or CIM? (2-3 sentences, actionable)
3. MISREAD RISK     — What is the most common misapplication or misinterpretation advisors make? (1-2 sentences)
4. BEST USE         — 3-5 concrete use cases: "founder conversation opener", "sector origination", "valuation anchor", etc.

Rules:
- Ground everything in the actual document content, not generic advice
- Keep core_insight under 180 words
- English only, no hedge words

Return ONLY valid JSON, no markdown:
{"title":"string","core_insight":"string","deal_implication":"string","misread_risk":"string","best_use":["string"]}`;

// ── Claude call helper ───────────────────────────────────────────────────────
async function callClaude(anthropicKey: string, system: string, userPrompt: string) {
  const r = await fetch(ANTHROPIC_URL, {
    method:  'POST',
    headers: {
      'x-api-key':         anthropicKey,
      'anthropic-version': '2023-06-01',
      'Content-Type':      'application/json',
    },
    body: JSON.stringify({
      model:      MODEL,
      max_tokens: 800,
      system,
      messages: [{ role: 'user', content: userPrompt }],
    }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${await r.text()}`);
  const data    = await r.json();
  const text    = data.content?.[0]?.text ?? '';
  const cleaned = text.replace(/```json|```/g, '').trim();
  const start   = cleaned.indexOf('{');
  const end     = cleaned.lastIndexOf('}') + 1;
  return JSON.parse(cleaned.slice(start, end));
}

// ── Main handler ──────────────────────────────────────────────────────────────
Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

  const ANTHROPIC_KEY = Deno.env.get('ANTHROPIC_API_KEY')          ?? '';
  const SUPA_URL      = Deno.env.get('SUPABASE_URL')               ?? '';
  const SUPA_KEY      = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')  ?? '';
  const db            = supa(SUPA_URL, SUPA_KEY);

  const json = (d: unknown, s = 200) =>
    new Response(JSON.stringify(d), { status: s, headers: { ...CORS, 'Content-Type': 'application/json' } });

  const path = new URL(req.url).pathname.replace(/.*\/grapevine-to-card/, '') || '/';

  if (path === '/health' || path === '/') {
    return json({ status: 'ok', version: '1.1', anthropic_set: !!ANTHROPIC_KEY, supabase_set: !!SUPA_URL });
  }

  if (req.method !== 'POST') return json({ error: 'POST required' }, 405);
  if (!ANTHROPIC_KEY)        return json({ error: 'ANTHROPIC_API_KEY not set' }, 500);

  let body: Record<string, string> = {};
  try { body = await req.json(); } catch { /**/ }

  if (path === '/extract') {
    const noteId = (body.note_id ?? '').trim();
    if (!noteId) return json({ error: 'note_id required' }, 400);

    // 1. Fetch note
    let rows: any[];
    try {
      rows = await db(
        `grapevine_notes?note_id=eq.${noteId}&is_deleted=eq.false&select=note_id,note_type,title,summary_short,body,body_md,structured_data,geo_country,sector_code&limit=1`
      );
    } catch (e: any) {
      return json({ error: `DB fetch failed: ${e.message}` }, 500);
    }

    if (!rows?.length) return json({ error: 'Note not found or deleted' }, 404);
    const source = rows[0];

    const sd = typeof source.structured_data === 'string'
      ? JSON.parse(source.structured_data)
      : (source.structured_data ?? {});

    // ── FLOW B: Drop Point KNOWLEDGE_CARD — enrich in-place ──────────────────
    if (source.note_type === 'KNOWLEDGE_CARD') {
      const sourceText = (source.body_md || source.body || '').slice(0, 8000);
      if (!sourceText && !source.title) return json({ error: 'No content to enrich — add text or upload PDF first' }, 400);

      const userPrompt = `Document title: ${source.title ?? '(untitled)'}
Country: ${source.geo_country ?? 'Benelux'}
Sector: ${source.sector_code ?? 'Cross-sector'}

Document content:
${sourceText || '(no body text — use title only)'}`;

      let extracted: any;
      try {
        extracted = await callClaude(ANTHROPIC_KEY, SYSTEM_KC, userPrompt);
      } catch (e: any) {
        return json({ error: `Anthropic call failed: ${e.message}` }, 500);
      }

      for (const k of ['core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
        if (!extracted[k]) return json({ error: `LLM response missing key: ${k}` }, 500);
      }

      // Patch the existing KNOWLEDGE_CARD in-place
      const patch = {
        title:         extracted.title || source.title,
        summary_short: extracted.core_insight.slice(0, 300),
        summary_llm:   extracted.core_insight.slice(0, 300),
        is_ai_derived: true,
        structured_data: {
          ...sd,
          core_insight:     extracted.core_insight,
          deal_implication: extracted.deal_implication,
          misread_risk:     extracted.misread_risk,
          best_use:         extracted.best_use,
          card_type:        sd.card_type || 'library_source',
          kb_quality:       sd.kb_quality || { tier: null, benelux_fit: null },
        },
      };

      try {
        await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH', patch);
      } catch (e: any) {
        return json({ error: `DB patch failed: ${e.message}` }, 500);
      }

      return json({
        ok:        true,
        note_id:   noteId,
        title:     extracted.title || source.title,
        status:    source.status,
        enriched:  true,
        in_place:  true,
      });
    }

    // ── FLOW A: WHISPER_NOTE pattern candidate → new KNOWLEDGE_CARD ──────────
    if (source.note_type !== 'WHISPER_NOTE') {
      return json({ error: `Unsupported note_type: ${source.note_type}` }, 400);
    }
    if (!sd.pattern_candidate) {
      return json({ error: 'structured_data.pattern_candidate is not true' }, 400);
    }

    // Duplicate guard
    const existing = await db(
      `grapevine_notes?source_ref_id=eq.${noteId}&note_type=eq.KNOWLEDGE_CARD&is_deleted=eq.false&select=note_id,title,status&limit=1`
    ).catch(() => null);
    if (existing?.length) {
      return json({ ok: true, note_id: existing[0].note_id, title: existing[0].title,
        status: existing[0].status, capture_origin: 'whisper_report',
        source_note_id: noteId, duplicate: true });
    }

    const userPrompt = `Source WHISPER_NOTE to distil:

PATTERN ANCHOR
pattern_name:      ${sd.pattern_name      ?? '(not set)'}
pattern_rationale: ${sd.pattern_rationale ?? '(not set)'}

SOURCE NOTE
title:   ${source.title         ?? ''}
country: ${source.geo_country   ?? ''}
summary: ${source.summary_short ?? ''}

body excerpt:
${(source.body_md ?? '').slice(0, 2000)}${
  (sd.editorial_angle || sd.sector_focus)
    ? `\n\n--- EDITORIAL FRAMING ---\n${sd.editorial_angle ? `editorial_angle: ${sd.editorial_angle}` : ''}${sd.sector_focus ? `\nsector_focus: ${sd.sector_focus}` : ''}`
    : ''
}`;

    let extracted: any;
    try {
      extracted = await callClaude(ANTHROPIC_KEY, SYSTEM_WHISPER, userPrompt);
    } catch (e: any) {
      return json({ error: `Anthropic call failed: ${e.message}` }, 500);
    }

    for (const k of ['title', 'core_insight', 'deal_implication', 'misread_risk', 'best_use']) {
      if (!extracted[k]) return json({ error: `LLM response missing key: ${k}` }, 500);
    }

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
        card_type:                'library_source',
        kb_quality:               { tier: null, benelux_fit: null },
      },
      geo_country:   source.geo_country ?? 'BE',
      sector_code:   source.sector_code ?? null,
      language_code: 'en',
      note_version:  1,
      is_current:    true,
      gold_status:   'grapevine',
      usable_for:    ['thought_leadership', 'sector_research'],
    };

    let created: any;
    try {
      created = await db('grapevine_notes', 'POST', card);
    } catch (e: any) {
      return json({ error: `DB write failed: ${e.message}` }, 500);
    }

    try {
      await db(`grapevine_notes?note_id=eq.${noteId}`, 'PATCH',
        { structured_data: { ...sd, pattern_candidate: false } });
    } catch { /**/ }

    const newNote = Array.isArray(created) ? created[0] : created;
    return json({ ok: true, note_id: newNote?.note_id ?? null, title: extracted.title,
      status: 'draft', capture_origin: 'whisper_report', source_note_id: noteId });
  }

  return json({ error: 'not found' }, 404);
});
