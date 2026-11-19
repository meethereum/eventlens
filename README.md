# EventLens v1

A financial research assistant. Ask a question about a company event ("Intel's CEO was just ousted, what should I expect?") and EventLens analyses it across 10 fixed criteria — USD strength, rates, oil, market regime, sector momentum, cross-sector dependencies, geopolitical risk, financial health, earnings, and valuation — computes evidence-weighted scenario confidence using real FRED, SEC EDGAR, and market data, then has an LLM write an analyst-style research note from the card outputs.

---

## Quick start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — fill in FRED_API_KEY, LLM_API_KEY, SEC_USER_AGENT

# 2. Build and run
docker compose up --build

# 3. Open
open http://localhost:8080
```

That's it. One command, one published port (`${WEB_PORT:-8080}`).

---

## Architecture

```
http://localhost:8080
        │
        ▼
   nginx (web container)
   ├── /* → Vite SPA (React + TypeScript + Tailwind)
   └── /api/* → proxy → FastAPI (backend container, port 8000)
                         ├── POST /api/analyze   SSE stream
                         ├── GET  /api/health
                         ├── GET  /api/cards/{id}/inspect
                         ├── POST /api/simulate
                         ├── POST /api/simulate/explain
                         ├── GET  /api/precedents
                         ├── GET  /api/cards/{id}/unusual-days
                         ├── POST /api/explain-day
                         └── POST /api/baseline  plain-LLM comparison
```

### Backend stack
- **Python 3.11**, FastAPI, sse-starlette, uvicorn
- **Data**: FRED API, yfinance, SEC EDGAR, optional Finnhub company news, Caldara-Iacoviello GPR index
- **Cache**: diskcache (named Docker volume, survives restarts)
- **Math**: numpy, scipy — all scoring is deterministic code, no LLM inside cards

### Frontend stack
- **Vite + React + TypeScript**, Tailwind CSS, shadcn/ui
- **Charts**: Apache ECharts (via echarts-for-react)
- **Animation**: Framer Motion
- **Queries**: TanStack Query

### Analysis pipeline

```
User query
    │
    ▼ LLM call 1 (parse)
{ticker, event_type, as_of, intent}
    │
    ▼ scope check
10 cards fetched concurrently ──────────────────────────────────────────────
  C1 USD Strength       (FRED DTWEXBGS)
  C2 Rates & Inflation  (FRED DGS10, DFF, T10Y2Y, CPIAUCSL)
  C3 Oil & Energy       (FRED DCOILWTICO, DCOILBRENTEU)
  C4 Market Regime      (yfinance SPY, FRED VIXCLS)
  C5 Sector Strength    (yfinance stock vs sector ETF vs SPY)
  C6 Cross-Sector Dep.  (curated dependencies.json + yfinance proxies)
  C7 Geopolitics        (GPR index + FRED USEPUINDXD)
  C8 Financial Health   (SEC EDGAR XBRL)
  C9 Earnings & Growth  (SEC EDGAR XBRL + yfinance)
  C10 Valuation & Momentum (SEC EDGAR XBRL + yfinance)
    │
    ▼ aggregation math (scipy Beta CIs, Shannon entropy)
{composite_signal, evidence_strength, scenario_scores, card_contributions}
    │
    ▼ LLM call 2 (synthesise)
analyst research note (headline, summary, key drivers, counter-evidence,
                       scenarios, disclaimer)
```

---

## Configuration

All configuration lives in `.env`. Never edit source files to change settings.

### Required keys

| Variable | Description |
|---|---|
| `FRED_API_KEY` | Free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `LLM_API_KEY` | Your LLM provider API key |
| `SEC_USER_AGENT` | Format: `AppName/1.0 your@email.com` (SEC fair-use policy) |

### LLM switching

EventLens talks to any OpenAI-compatible `/chat/completions` endpoint. To switch providers, change three variables in `.env` and run `docker compose up -d`. Nothing else.

#### Groq (default — free tier available)
```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=openai/gpt-oss-120b
# Optional: control reasoning token budget
# LLM_EXTRA_BODY={"reasoning_effort":"default"}
```

#### OpenAI
```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=         # check platform.openai.com/docs/models
```

#### OpenRouter (100+ models, one API key)
```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=         # check openrouter.ai/models
```

#### Ollama (local, host must be running Ollama)
```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=         # check: ollama list
```

### Fallback model

If the primary model returns a daily-quota 429, EventLens automatically retries with `LLM_FALLBACK_MODEL`:
```env
LLM_FALLBACK_MODEL=openai/gpt-oss-20b
```
The status pill shows "fallback model" when this activates.

### Rate limiting

```env
LLM_RPM_LIMIT=25     # client-side requests/minute cap
LLM_TIMEOUT_S=60     # per-request timeout
LLM_MAX_INPUT_TOKENS=4000  # input truncation ceiling
```

---

## Demo mode

With no keys set, EventLens boots in demo mode and replays recorded fixtures for four scripted queries:

| Query | Ticker | As-of |
|---|---|---|
| Intel's CEO was just ousted. What should I expect? | INTC | 2024-12-02 |
| Russia has invaded Ukraine and oil is spiking. How does that affect Exxon? | XOM | 2022-02-25 |
| Silicon Valley Bank just collapsed. What does that mean for JPMorgan? | JPM | 2023-03-13 |
| Nvidia fell sharply after the DeepSeek news. Is that company-specific or sector-wide? | NVDA | 2025-01-28 |

To force demo mode: `DEMO_MODE=1`  
To force live mode: `DEMO_MODE=0`  
Default (`DEMO_MODE=auto`): live when all keys are present, demo otherwise.

---

## Recording new fixtures

Run this inside the backend container to capture a live analysis as a replayable fixture:

```bash
docker compose exec backend python /app/scripts/record_fixture.py \
  --query "Intel's CEO was just ousted. What should I expect?" \
  --ticker INTC \
  --as-of 2024-12-02 \
  --out /app/fixtures/intc_2024_12_02.json
```

The script streams `/api/analyze`, records each SSE event with its timing, and writes the fixture file. Requires live mode (`DEMO_MODE=0`) and all data-source keys set.

---

## Verifying data sources

```bash
docker compose exec backend python /app/scripts/check_apis.py
```

Checks all 9 FRED series, 29 yfinance tickers, and 15 EDGAR CIK lookups. Exits with code 1 if any fail.

---

## Running tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

60 unit tests across four files:
- `tests/test_scoring_math.py` — z-score, correlation, macro signal, quality
- `tests/test_aggregation.py` — golden-number tests for each aggregation formula component
- `tests/test_golden.py` — full 10-card golden test verifying scenario distribution, credible intervals, and contributions
- `tests/test_new_features.py` — scenario sensitivity, precedent date filtering, unusual-day detection, and feature API flows

---

## Covered universe (v1)

| Ticker | Sector |
|---|---|
| NVDA, INTC, AAPL, MSFT | Technology (XLK) |
| GM, SBUX, AMZN | Consumer Discretionary (XLY) |
| DIS | Communication Services (XLC) |
| BA, RTX | Industrials (XLI) |
| XOM, CVX | Energy (XLE) |
| JPM, SCHW | Financials (XLF) |
| UNH | Health Care (XLV) |

Queries about other tickers get a "not covered in v1" message.

---

## Dev mode (hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- Backend: uvicorn `--reload` on port 8000
- Frontend: Vite dev server on port 5173

---

## Scenario tools

After an analysis completes, the UI offers three additional views:

- **What-if simulator** — applies deterministic changes to linked evidence cards and presents a plain-language outlook with ranked drivers. The explicit explanation action may make one cached LLM call; slider updates do not.
- **Similar past events** — ranks locally stored, source-linked precedents and charts normalized 60-trading-day outcomes. Build the static library with `docker compose exec backend python -m scripts.build_precedents`, then verify it with `docker compose exec backend python -m scripts.validate_precedents --check-urls`.
- **Unusual-day explanation** — shows robust outliers in the adjusted-close price chart, then provides a cited comparison with sector, market, SEC filings, and optional Finnhub headlines. Demo runs must use only fixture evidence; live explanations use a cited template if news or the LLM is unavailable.

The scenario endpoints use the in-memory run store, so they are available only while that run remains in the current backend process.

The checked-in precedent file currently has no verified records. The old four-row demo seed had neither valid source URLs nor realized outcomes and was removed rather than presented as historical evidence. Building the requested 100+ record library requires successful SEC and adjusted-close data access; the builder aborts instead of writing incomplete or invented outcomes.

---

## What's not in v1

- **C11 Historical Precedent** — locked card, coming in v2
- **Verified precedent library** — not bundled yet; the static dataset stays empty until at least 100 complete, source-checked records are available
- **Graph/vector memory** — no vector database, LangChain, LangGraph, or embeddings
- **Auth** — none
- **Buy/sell advice** — explicitly refused; EventLens is descriptive only
- **LLM inside cards** — all card logic is deterministic code

---

## Scoring math (brief)

Macro cards (C1–C4, C7):  
`s = sign(ρ) × tanh(z / 2)` where z is the 20-day change z-scored over 756 trading days, and ρ is the 252-day Pearson correlation between the stock's daily returns and the factor's daily changes.

Aggregation:  
`e_i = 0.6 × w_i × q_i` (evidence per card, discounted for correlation)  
`p_k = (E_k + 1) / (Σ E + 3)` (Dirichlet posterior, α=1)  
`Evidence strength = 1 − H(p) / ln(3)` (normalised Shannon entropy)

See `backend/app/scoring/` for the full implementation and `backend/tests/` for unit tests with hand-computed golden numbers.
