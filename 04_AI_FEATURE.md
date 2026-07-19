# AI Feature

## The four options (for reference)

Everything "AI" could do here, in rough order of effort. Not exclusive — start with
one, add later.

**A — Narrative summary of fundamentals.** *(v1 choice.)*
Feed the model a stock's computed ratios + financials; it returns a plain-English
readout ("revenue grew steadily but debt-to-equity climbed 0.4→1.1 while operating
margin slipped — growth is increasingly debt-funded"). One API call per stock, cheap,
highest value-to-effort. Makes numbers legible at a glance.

**B — Q&A / chat about a stock.** *(defer to v2.)*
User asks "why did margins drop in FY23?"; model answers from the stored data. More
work (context management per question), only as good as the data you supply.

**C — Structured scoring/comparison.** *(defer; keep descriptive if built.)*
User defines what "good" means (weights on growth/valuation/debt); model produces
scores or a side-by-side. **Risk:** drifts toward "AI tells you what to buy." Only
acceptable if transparent and descriptive, never a black-box buy signal.

**D — AI in the pipeline (normalize messy fundamentals).** *(build only if needed.)*
Use the model to clean/normalize inconsistent scraped fundamentals (extract numbers
from messy tables, unify labels/units). Real engineering use; reach for it if the
scraped data is as messy as scraped data usually is. Lives in the pipeline, not the UI.

---

## v1 decision: build A only

Narrative summary. Best effort-to-value ratio, honest, and it ticks the "maybe use
AI" box in a way that's defensible in an interview (LLM summarization over structured
financial data via the Anthropic API). B and C deferred; D held in reserve for the
pipeline if data quality demands it.

---

## How A works

**Endpoint:** `GET /analysis/{symbol}` (see `05_SCHEMA_AND_API.md`).

**Flow:**
1. Load the stock's latest `fundamentals` snapshot + a few derived facts (growth
   rates, trend directions) from Postgres.
2. Build a structured prompt (below) containing **only real numbers** we hold.
3. Call the Anthropic API (`claude-sonnet` class).
4. Cache the returned narrative (keyed by symbol + fundamentals snapshot date) so we
   don't re-pay on every page view. Regenerate when a newer snapshot exists.
5. Return narrative + the "as of" date + a standing disclaimer.

**Model:** a `claude-sonnet`-class model is the right balance of quality/cost for
summarization. (Confirm exact current model string from Anthropic's docs at build
time rather than hardcoding from memory.)

---

## Prompt design (enforces the guardrail)

The prompt is where "describe, don't advise" is made real. Two parts.

**System prompt (fixed):**
```
You are a financial-data explainer. You are given structured fundamental data for a
single publicly listed Indian (NSE) company. Your job is to describe and interpret
what the numbers show in clear, plain English for a retail investor who wants to
understand the company's financial profile.

Rules:
- Describe and explain ONLY. Do not recommend buying, selling, or holding.
- Do not predict future price or returns. Past performance does not indicate future
  results — say so if the user seems to be extrapolating.
- Stick to the numbers provided. Do not invent figures, ratios, or facts not present
  in the input. If a metric is missing, say it's not available rather than guessing.
- Point out both strengths and concerns neutrally (e.g. "margins improved" AND "debt
  rose"). No hype, no doom.
- Keep it to ~150–250 words. Use plain language; briefly define a ratio if it aids
  understanding.
- End with a one-line reminder that this is descriptive analysis, not investment
  advice.
```

**User prompt (per stock, structured):**
```
Company: {name} ({symbol}), sector: {sector}
Data as of: {snapshot_date}

Valuation:
- P/E: {pe}          (sector median if known: {sector_pe})
- P/B: {pb}

Profitability:
- ROE: {roe}%
- Operating margin: {op_margin}% (3yr ago: {op_margin_3y})

Growth (revenue):
- 1yr: {rev_growth_1y}%   3yr CAGR: {rev_cagr_3y}%

Leverage:
- Debt-to-equity: {de}   (3yr ago: {de_3y})

Income:
- Dividend yield: {div_yield}%   Paid dividends last {n} years: {div_years}

[Only include metrics we actually have. Omit missing ones or mark them "N/A".]

Write the plain-English analysis per your rules.
```

**Why this shape:**
- Passing **structured, real numbers** (not "analyze RELIANCE") keeps the model
  grounded and prevents it from inventing data — critical since hallucinated
  financials would be worse than none.
- The explicit "only use provided data / say N/A if missing" rule guards against the
  gaps in free fundamentals (`02_DATA_SOURCES.md`).
- The advice ban + "not investment advice" footer enforce the project guardrail at
  the generation layer, not just in UI copy.

---

## Caching

- Key: `(symbol, fundamentals_snapshot_date)`.
- Store the narrative text alongside the snapshot (or a small `analysis_cache` table).
- Invalidate/regenerate only when a newer fundamentals snapshot lands.
- Result: one Anthropic call per stock per fundamentals update, not per page view.

---

## Cost sense

Summarization calls are small (a few hundred tokens in, ~250 words out). With
caching keyed to snapshot dates, you generate roughly once per stock per week
(fundamentals cadence). Trivial cost for a personal tool. Confirm current pricing in
Anthropic's docs.

---

## UI treatment

- Show the narrative in a clearly-labeled "AI analysis" card on the stock detail page.
- Always show the "as of {date}" and the "descriptive analysis, not investment advice"
  line next to it.
- Never render it as a verdict/score. It's prose that explains the numbers sitting
  right above it.
