#!/usr/bin/env python3
"""
Deep Research Agent: Similar News & Company Incident Timeline Extractor
========================================================================
Given a user prompt describing an incident, crisis, operational failure,
or corporate event, this agent:
  1. Deconstructs the event characteristics and search criteria.
  2. Queries Tavily Live News Search (or live fallback search) to discover
     5-10 major companies that experienced similar events.
  3. Uses focused sub-agent research with full webpage extraction (httpx + markdownify)
     to gather verified dates, triggers, causes, impacts, and citations.
  4. Fetches historical stock price data for each company and maps stock prices,
     trading volume, and percentage drawdown onto every milestone date.
  5. Outputs the final result as a clean, standardized JSON document and saves it to disk.

Keys supported:
  - GROQ_API_KEY (default LLM, e.g. openai/gpt-oss-120b)
  - TAVILY_API_KEY (Tavily Live News Search)
  - OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY (optional alternatives)
"""

import os
import sys
import json
import re
import time
import argparse
import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Type, TypeVar

import httpx
from markdownify import markdownify
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Financial data
import yfinance as yf
import pandas as pd

# Terminal rendering
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
except ImportError:
    console = None

# Load environment variables (.env in current dir, or fallback to parent dir)
load_dotenv(".env")
if not os.getenv("GROQ_API_KEY") and not os.getenv("LLM_API_KEY"):
    load_dotenv("../eventlens/.env")


# ============================================================================
# Pydantic Schemas for Structured JSON Output (With Stock Price Mapping)
# ============================================================================

class TimelineMilestone(BaseModel):
    """A single chronological milestone in the incident timeline mapped with stock data."""
    date: str = Field(
        ...,
        description="Exact date or timeframe of this milestone (e.g., '2024-07-19' or '2024-07-19 04:09 UTC')"
    )
    phase: str = Field(
        ...,
        description="Phase name (e.g. 'Trigger / Precursor', 'Outbreak / Initial Impact', 'Escalation / Contagion', 'Emergency Containment', 'Resolution / Aftermath')"
    )
    event: str = Field(
        ...,
        description="Detailed description of what specifically occurred at this milestone"
    )
    impact: str = Field(
        ...,
        description="Measurable consequence at this stage (e.g., stock drop, flight cancellations, regulatory intervention, leadership change)"
    )
    # Stock price fields mapped onto this milestone date
    stock_price: Optional[float] = Field(
        None,
        description="Closing stock price (in USD) on or nearest to this milestone date"
    )
    stock_change_from_baseline_pct: Optional[float] = Field(
        None,
        description="Percentage change in stock price relative to pre-incident baseline"
    )
    trading_volume: Optional[int] = Field(
        None,
        description="Trading volume on this milestone date"
    )


class SourceCitation(BaseModel):
    """Source URL and title for research citations."""
    title: str = Field(..., description="Title of the article or publication")
    url: str = Field(..., description="Web URL of the cited source")


class DailyPricePoint(BaseModel):
    """Daily price entry for plotting continuous trajectory."""
    date: str
    close: float


class StockPerformanceMetrics(BaseModel):
    """Financial impact and stock price metrics over the incident window."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g. CRWD, MSFT, DAL)")
    baseline_date: str = Field(..., description="Date of pre-crisis baseline price")
    baseline_price: float = Field(..., description="Pre-crisis baseline closing price (USD)")
    trough_date: str = Field(..., description="Date of lowest stock price during the crisis window")
    trough_price: float = Field(..., description="Lowest closing stock price (USD)")
    max_drawdown_pct: float = Field(..., description="Maximum drawdown percentage from baseline")
    daily_series: List[DailyPricePoint] = Field(
        default_factory=list,
        description="Daily closing price series for charting"
    )


class CompanyIncidentReport(BaseModel):
    """Detailed deep research dossier, timeline, and stock data for a single major company."""
    company_name: str = Field(..., description="Name of the major company (e.g., CrowdStrike, Microsoft)")
    stock_ticker: Optional[str] = Field(
        None,
        description="Public stock ticker symbol (e.g. CRWD, MSFT, DAL, JPM) or null if private/governmental"
    )
    industry: str = Field(..., description="Industry or sector of the company")
    incident_title: str = Field(..., description="Clear, descriptive title of the news event / incident")
    event_timeframe: str = Field(..., description="Overall period or year(s) during which the event occurred")
    summary: str = Field(..., description="Executive summary of the incident and what transpired")
    similarity_rationale: str = Field(
        ...,
        description="Detailed explanation of why and how this event is similar to the user's prompt"
    )
    key_parallels: List[str] = Field(
        ...,
        description="List of specific mechanisms or parallels matching the user prompt"
    )
    key_differences: List[str] = Field(
        ...,
        description="List of key differences or unique factors compared to the user prompt"
    )
    timeline: List[TimelineMilestone] = Field(
        ...,
        description="Chronological sequence of milestone events with mapped stock prices"
    )
    stock_metrics: Optional[StockPerformanceMetrics] = Field(
        None,
        description="Summary of stock price performance, drawdown, and daily price series"
    )
    total_impact_assessment: str = Field(
        ...,
        description="High-level assessment of total financial, operational, regulatory, or reputational damage"
    )
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="List of verified research sources and article links"
    )


class DiscoveredCompanyCandidate(BaseModel):
    """A discovered candidate company for deep investigation."""
    company_name: str = Field(..., description="Major company name")
    stock_ticker: Optional[str] = Field(None, description="Stock ticker (e.g. CRWD, MSFT, AMZN, DAL) or null if private")
    incident_title: str = Field(..., description="Brief title of the analogous incident")
    year: str = Field(..., description="Year or timeframe")
    brief_similarity: str = Field(..., description="Why this matches the user scenario")


class DiscoveryPlan(BaseModel):
    """Output of the prompt analysis and company discovery subagent."""
    incident_category: str = Field(..., description="High-level category of the incident")
    core_themes: List[str] = Field(..., description="Key themes and causal mechanisms extracted from prompt")
    search_queries_used: List[str] = Field(..., description="Search queries formulated to find precedents")
    discovered_companies: List[DiscoveredCompanyCandidate] = Field(
        ...,
        description="List of 5 to 10 major companies that experienced similar events"
    )


class DeepResearchTimelineOutput(BaseModel):
    """Top-level JSON schema containing the full multi-company timeline report with stock mappings."""
    query_prompt: str = Field(..., description="The original prompt provided by the user")
    generated_at: str = Field(..., description="ISO timestamp of report generation")
    incident_category: str = Field(..., description="Identified incident category")
    core_themes: List[str] = Field(..., description="Key thematic dimensions analyzed")
    executive_synthesis: str = Field(
        ...,
        description="Comparative synthesis highlighting common patterns and financial damage across all analyzed companies"
    )
    total_companies_analyzed: int = Field(..., description="Number of major companies included (5-10)")
    similar_company_events: List[CompanyIncidentReport] = Field(
        ...,
        description="Collection of 5-10 major companies with deep chronological timelines and mapped stock prices"
    )


T = TypeVar("T", bound=BaseModel)

def extract_json_and_validate(raw_text: str, pydantic_cls: Type[T]) -> T:
    """
    Extracts JSON substring from LLM response (handling markdown fences or thinking tokens)
    and validates it against the target Pydantic schema.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Received empty response from LLM.")

    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()

    match = re.search(r"(\{.*\})", text, re.DOTALL)
    candidate_json = match.group(1) if match else text

    try:
        data = json.loads(candidate_json)
        return pydantic_cls.model_validate(data)
    except Exception as e:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            sub = text[start:end+1]
            try:
                data = json.loads(sub)
                return pydantic_cls.model_validate(data)
            except Exception as e2:
                raise ValueError(f"Failed to parse and validate {pydantic_cls.__name__}: {e2}\nText was:\n{text[:500]}")
        raise ValueError(f"Could not parse JSON for {pydantic_cls.__name__}: {e}\nText was:\n{text[:500]}")


# ============================================================================
# Historical Stock Price Mapping via yfinance
# ============================================================================

def enrich_stock_timeline(
    ticker_symbol: Optional[str],
    timeline: List[TimelineMilestone]
) -> tuple[List[TimelineMilestone], Optional[StockPerformanceMetrics]]:
    """
    Fetches historical stock prices around the timeline dates,
    maps the exact stock price and % change onto each milestone,
    and returns the updated timeline along with overall stock performance metrics.
    """
    if not ticker_symbol or ticker_symbol.upper() in ("NONE", "NULL", "N/A", "PRIVATE"):
        return timeline, None

    clean_ticker = ticker_symbol.upper().strip()
    try:
        parsed_dates = []
        for m in timeline:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", m.date)
            if match:
                parsed_dates.append(pd.to_datetime(match.group(1)))
            else:
                match_yr_mo = re.search(r"(\d{4})-(\d{2})", m.date)
                if match_yr_mo:
                    parsed_dates.append(pd.to_datetime(f"{match_yr_mo.group(1)}-{match_yr_mo.group(2)}-01"))

        if not parsed_dates:
            return timeline, None

        min_date = min(parsed_dates)
        max_date = max(parsed_dates)

        # Build date range window with margins
        start_date = min_date - datetime.timedelta(days=25)
        end_date = max_date + datetime.timedelta(days=45)

        ticker_obj = yf.Ticker(clean_ticker)
        df = ticker_obj.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d")
        )

        if df.empty or len(df) < 2:
            return timeline, None

        # Remove timezone for pandas comparison
        df.index = df.index.tz_localize(None)

        # Baseline: last trading day on or immediately before first milestone
        prior_df = df[df.index <= min_date]
        baseline_idx = len(prior_df) - 1 if len(prior_df) > 0 else 0
        baseline_price = float(df.iloc[baseline_idx]["Close"])
        baseline_date = df.index[baseline_idx].strftime("%Y-%m-%d")

        # Trough (lowest closing price in window)
        min_idx = df["Close"].idxmin()
        trough_row = df.loc[min_idx]
        trough_price = float(trough_row["Close"])
        trough_date = min_idx.strftime("%Y-%m-%d")
        max_drawdown = round(((trough_price - baseline_price) / baseline_price) * 100, 2)

        # Map onto each milestone
        updated_timeline = []
        for m in timeline:
            m_copy = m.model_copy()
            match = re.search(r"(\d{4}-\d{2}-\d{2})", m.date)
            if match:
                dt = pd.to_datetime(match.group(1))
                nearest_idx = df.index.get_indexer([dt], method="nearest")[0]
                row = df.iloc[nearest_idx]
                close_p = round(float(row["Close"]), 2)
                pct_chg = round(((close_p - baseline_price) / baseline_price) * 100, 2)
                vol = int(row["Volume"])

                m_copy.stock_price = close_p
                m_copy.stock_change_from_baseline_pct = pct_chg
                m_copy.trading_volume = vol
            updated_timeline.append(m_copy)

        # Build daily series
        daily_series = [
            DailyPricePoint(
                date=idx.strftime("%Y-%m-%d"),
                close=round(float(row["Close"]), 2)
            )
            for idx, row in df.iterrows()
        ]

        metrics = StockPerformanceMetrics(
            ticker=clean_ticker,
            baseline_date=baseline_date,
            baseline_price=round(baseline_price, 2),
            trough_date=trough_date,
            trough_price=round(trough_price, 2),
            max_drawdown_pct=max_drawdown,
            daily_series=daily_series
        )

        return updated_timeline, metrics

    except Exception as e:
        if console:
            console.print(f"[dim]Stock price lookup for {clean_ticker} notice: {e}[/dim]")
        return timeline, None


# ============================================================================
# Search & Web Content Extraction Tools (Tavily Live News Primary)
# ============================================================================

def fetch_webpage_content(url: str, timeout: float = 8.0, max_chars: int = 3500) -> str:
    """Fetch webpage HTML and convert to clean markdown text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        md = markdownify(response.text)
        cleaned = "\n".join([line.strip() for line in md.splitlines() if line.strip()])
        return cleaned[:max_chars]
    except Exception as e:
        return f"[Failed to fetch content from {url}: {e!s}]"


def search_web(query: str, max_results: int = 3, topic: str = "news") -> List[Dict[str, str]]:
    """
    Search live news using Tavily as the primary live news research agent.
    If Tavily key is missing or fails, seamlessly uses Google News RSS & Wikipedia fallback.
    """
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    # 1. Primary path: Tavily Live News Search
    if tavily_key and not tavily_key.startswith("your_") and len(tavily_key) > 5:
        try:
            if console:
                console.print(f"[bold cyan][Tavily Live News Agent][/bold cyan] Querying: '{query}'...")
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            t_topic = "news" if topic == "news" else "general"
            search_response = client.search(
                query=query,
                max_results=max_results,
                topic=t_topic,
                include_raw_content=False
            )
            results = []
            for item in search_response.get("results", []):
                url = item.get("url", "")
                title = item.get("title", "")
                snippet = item.get("content", "")
                full_content = fetch_webpage_content(url)
                body = full_content if len(full_content) > 200 else snippet
                results.append({
                    "title": title,
                    "url": url,
                    "content": body
                })
            if results:
                if console:
                    console.print(f"[green]✓ Tavily Live News returned {len(results)} source articles.[/green]")
                return results
        except Exception as e:
            if console:
                console.print(f"[yellow][Tavily Notice][/yellow] {e}; switching to fallback search.")
    else:
        if console:
            console.print(f"[dim][Search Notice] TAVILY_API_KEY not set in .env; using live web search fallback...[/dim]")

    # 2. Resilient Fallback: Google News RSS + Wikipedia API
    fallback_results: List[Dict[str, str]] = []

    try:
        rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        r = httpx.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6.0, follow_redirects=True)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:max_results]:
                t = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                fallback_results.append({
                    "title": t,
                    "url": link,
                    "content": desc
                })
    except Exception:
        pass

    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(query)}&utf8=&format=json"
        r = httpx.get(wiki_url, headers={"User-Agent": "DeepResearchAgent/1.0"}, timeout=6.0)
        if r.status_code == 200:
            for item in r.json().get("query", {}).get("search", [])[:2]:
                title = item.get("title", "")
                snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                wiki_slug = quote(title.replace(" ", "_"))
                page_url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
                page_md = fetch_webpage_content(page_url, max_chars=3000)
                content = page_md if len(page_md) > 200 else snippet
                fallback_results.append({
                    "title": f"Wikipedia: {title}",
                    "url": page_url,
                    "content": content
                })
    except Exception:
        pass

    return fallback_results


# ============================================================================
# LLM Client with Rate Limit Resilience
# ============================================================================

class LLMClient:
    """Wrapper around Groq, OpenAI, Anthropic, or Gemini with automated backoff retry."""

    def __init__(self, model_name: Optional[str] = None):
        self.groq_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        if self.groq_key:
            import groq
            self.provider = "groq"
            self.model = model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            self.client = groq.Groq(api_key=self.groq_key)
        elif self.openai_key:
            import openai
            self.provider = "openai"
            self.model = model_name or "gpt-4o"
            self.client = openai.OpenAI(api_key=self.openai_key)
        elif self.anthropic_key:
            import anthropic
            self.provider = "anthropic"
            self.model = model_name or "claude-3-5-sonnet-20241022"
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)
        elif self.gemini_key:
            from google import genai
            self.provider = "gemini"
            self.model = model_name or "gemini-2.0-flash"
            self.client = genai.Client(api_key=self.gemini_key)
        else:
            raise ValueError(
                "No LLM API key found! Please set GROQ_API_KEY in .env, "
                "or OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY."
            )

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 3500) -> str:
        """Execute chat completion and return string response with automatic retry on rate limits."""
        max_retries = 3
        backoff_seconds = 8.0

        for attempt in range(max_retries):
            try:
                if self.provider == "groq":
                    res = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=max_tokens
                    )
                    return res.choices[0].message.content or ""
                elif self.provider == "openai":
                    res = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=max_tokens
                    )
                    return res.choices[0].message.content or ""
                elif self.provider == "anthropic":
                    res = self.client.messages.create(
                        model=self.model,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                        max_tokens=max_tokens,
                        temperature=0.1
                    )
                    return res.content[0].text or ""
                elif self.provider == "gemini":
                    full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
                    res = self.client.models.generate_content(
                        model=self.model,
                        contents=full_prompt
                    )
                    return res.text or ""
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "rate_limit" in err_msg or "Rate limit" in err_msg) and attempt < max_retries - 1:
                    wait_time = backoff_seconds
                    wait_match = re.search(r"try again in ([0-9.]+)s", err_msg)
                    if wait_match:
                        wait_time = float(wait_match.group(1)) + 1.5
                    if console:
                        console.print(f"[yellow]Rate limit notice: waiting {wait_time:.1f}s before retry ({attempt + 1}/{max_retries})...[/yellow]")
                    time.sleep(wait_time)
                else:
                    raise e
        return ""


# ============================================================================
# Deep Research Agent Core Workflow
# ============================================================================

class DeepResearchNewsAgent:
    """
    Orchestrates the discovery of 5-10 major companies, deep research
    of their chronological incident timelines, and stock price mapping.
    """

    def __init__(self, model_name: Optional[str] = None, target_companies: int = 6):
        self.target_companies = max(5, min(10, target_companies))
        self.llm = LLMClient(model_name)

    def discover_companies(self, prompt: str) -> DiscoveryPlan:
        """
        Step 1: Deconstructs the prompt, conducts broad search queries,
        and identifies 5 to 10 distinct major companies with analogous incidents and stock tickers.
        """
        if console:
            console.print("[bold cyan]Step 1: Analyzing prompt & discovering candidate major companies...[/bold cyan]")

        initial_search_results = search_web(
            f"{prompt} similar major corporate crises company timeline",
            max_results=4,
            topic="news"
        )
        context_snippets = "\n".join([
            f"- [{r['title']}]({r['url']}): {r['content'][:300]}"
            for r in initial_search_results
        ])

        system_instruction = (
            "You are a specialized Corporate Crisis & Incident Discovery Analyst.\n"
            "Your objective is to identify distinct major global companies (e.g., Fortune 500, "
            "large tech firms, major financial institutions, critical infrastructure companies) "
            "that experienced real-world news events, crises, or situations highly analogous to the user's prompt.\n\n"
            "Requirements:\n"
            f"1. You MUST identify between 5 and {self.target_companies} distinct major companies.\n"
            "2. Each company must be a major, recognizable corporation or institution.\n"
            "3. Provide the official public stock ticker symbol (e.g. CRWD, MSFT, AMZN, DAL, JPM) if publicly traded.\n"
            "4. Ensure the incident is historically verified with documented timelines.\n"
            "5. Provide a crisp explanation of why each company's event parallels the prompt.\n"
            "6. Return ONLY a valid JSON object matching the requested schema. No markdown fences or explanations outside the JSON."
        )

        schema_json = json.dumps(DiscoveryPlan.model_json_schema(), indent=2)

        user_content = (
            f"User Prompt Scenario:\n\"{prompt}\"\n\n"
            f"Recent Search Snippets for context:\n{context_snippets}\n\n"
            f"Please discover {self.target_companies} major companies that had similar events.\n\n"
            f"Target JSON Schema:\n{schema_json}\n\n"
            "Return ONLY the JSON object."
        )

        raw = self.llm.generate(system_instruction, user_content, max_tokens=2500)
        plan = extract_json_and_validate(raw, DiscoveryPlan)
        return plan

    def research_single_company(
        self,
        candidate: DiscoveredCompanyCandidate,
        original_prompt: str,
        incident_category: str
    ) -> CompanyIncidentReport:
        """
        Step 2: Sub-agent focused research on one specific company.
        Queries Tavily Live News, fetches full markdown content, reconstructs
        the chronological timeline, and enriches it with historical stock prices.
        """
        query = f"{candidate.company_name} {candidate.incident_title} timeline dates trigger impact"
        search_results = search_web(query, max_results=3, topic="news")

        articles_context = ""
        sources: List[SourceCitation] = []
        for i, res in enumerate(search_results, 1):
            sources.append(SourceCitation(title=res["title"], url=res["url"]))
            articles_context += (
                f"\n--- SOURCE [{i}]: {res['title']} ({res['url']}) ---\n"
                f"{res['content'][:2500]}\n"
            )

        system_instruction = (
            "You are a Senior Deep Research Analyst specializing in corporate forensics and timeline reconstruction.\n"
            "Your task is to build an exhaustive, chronological timeline of the specified company's incident, "
            "comparing it specifically to the user's original prompt scenario.\n\n"
            "Guidelines for the Timeline:\n"
            "- Extract 4 to 8 distinct chronological milestones.\n"
            "- Each milestone MUST have:\n"
            "   1. 'date': A specific date (prefer format YYYY-MM-DD, e.g. '2024-07-19' or '2024-07-19 04:09 UTC').\n"
            "   2. 'phase': Clear phase name (e.g. 'Trigger / Precursor', 'Immediate Outbreak', 'Escalation', 'Emergency Containment', 'Resolution / Aftermath').\n"
            "   3. 'event': Precise factual description of what occurred.\n"
            "   4. 'impact': Tangible consequence (stock drop, operational halt, flight cancellations, executive exit, regulatory fine).\n"
            "- Detail similarities, parallels, and differences with the original prompt.\n"
            "- Return strictly a valid JSON object matching the target schema without markdown wrapping."
        )

        schema_json = json.dumps(CompanyIncidentReport.model_json_schema(), indent=2)

        user_content = (
            f"Original Prompt Scenario:\n\"{original_prompt}\"\n\n"
            f"Target Company: {candidate.company_name}\n"
            f"Stock Ticker: {candidate.stock_ticker or 'N/A'}\n"
            f"Incident: {candidate.incident_title} ({candidate.year})\n"
            f"Incident Category: {incident_category}\n\n"
            f"Gathered Research Web Context:\n{articles_context}\n\n"
            f"Target JSON Schema:\n{schema_json}\n\n"
            "Reconstruct the deep incident dossier and detailed chronological timeline. Return strictly JSON."
        )

        raw = self.llm.generate(system_instruction, user_content, max_tokens=3000)
        report = extract_json_and_validate(raw, CompanyIncidentReport)

        # Retain ticker from candidate if not filled
        if not report.stock_ticker and candidate.stock_ticker:
            report.stock_ticker = candidate.stock_ticker

        # Step 2b: Enrich timeline milestones with real historical stock prices via yfinance
        if report.stock_ticker:
            if console:
                console.print(f"    [dim]Fetching historical stock data for {report.stock_ticker}...[/dim]")
            enriched_timeline, stock_metrics = enrich_stock_timeline(
                ticker_symbol=report.stock_ticker,
                timeline=report.timeline
            )
            report.timeline = enriched_timeline
            report.stock_metrics = stock_metrics

        # Attach sources
        if not report.sources and sources:
            report.sources = sources
        elif sources:
            existing_urls = {s.url for s in report.sources}
            for s in sources:
                if s.url not in existing_urls:
                    report.sources.append(s)

        return report

    def synthesize_all(
        self,
        prompt: str,
        discovery_plan: DiscoveryPlan,
        company_reports: List[CompanyIncidentReport]
    ) -> DeepResearchTimelineOutput:
        """
        Step 3: Executive synthesis comparing recurring systemic patterns,
        triggers, stock drawdowns, and aftermath across all 5-10 companies.
        """
        companies_summary = "\n".join([
            f"- {c.company_name} ({c.event_timeframe}) [{c.stock_ticker or 'Private'}]: {c.incident_title}. "
            f"Max Drawdown: {c.stock_metrics.max_drawdown_pct if c.stock_metrics else 'N/A'}%. "
            f"Total Impact: {c.total_impact_assessment}"
            for c in company_reports
        ])

        system_instruction = (
            "You are an Executive Financial & Intelligence Director. Synthesize a comprehensive cross-company comparative analysis "
            "examining how these major companies experienced similar crises, the financial and stock price ramifications, "
            "common points of failure, crisis response efficacy, and long-term consequences."
        )

        user_content = (
            f"Prompt Scenario:\n\"{prompt}\"\n\n"
            f"Researched Companies & Financial Metrics:\n{companies_summary}\n\n"
            "Provide an executive synthesis (2-3 dense paragraphs) analyzing the cross-cutting themes, "
            "market reaction velocity, severity of valuation loss, and post-crisis corporate resilience."
        )

        try:
            executive_text = self.llm.generate(system_instruction, user_content, max_tokens=1500)
        except Exception:
            executive_text = (
                f"Analysis of {len(company_reports)} major companies reveals recurring patterns in "
                f"{discovery_plan.incident_category}, specifically regarding escalation dynamics, "
                f"equity market volatility, and structural reforms."
            )

        final_output = DeepResearchTimelineOutput(
            query_prompt=prompt,
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            incident_category=discovery_plan.incident_category,
            core_themes=discovery_plan.core_themes,
            executive_synthesis=executive_text,
            total_companies_analyzed=len(company_reports),
            similar_company_events=company_reports
        )
        return final_output

    def run(self, prompt: str) -> DeepResearchTimelineOutput:
        """Execute full Deep Research workflow for the given prompt."""
        if console:
            console.rule("[bold green]Deep Research News & Stock Timeline Agent[/bold green]")
            console.print(f"[bold yellow]Prompt:[/bold yellow] {prompt}\n")

        # 1. Discover 5-10 candidate companies
        discovery_plan = self.discover_companies(prompt)
        candidates = discovery_plan.discovered_companies[:self.target_companies]

        if console:
            console.print(f"\n[bold green]Discovered {len(candidates)} major companies with analogous events:[/bold green]")
            for idx, c in enumerate(candidates, 1):
                t_str = f" [cyan]({c.stock_ticker})[/cyan]" if c.stock_ticker else ""
                console.print(f"  {idx}. [bold]{c.company_name}[/bold]{t_str} ({c.year}) - {c.incident_title}")
            console.print("\n[bold cyan]Step 2: Delegating deep timeline & stock research for each company...[/bold cyan]")

        # 2. Deep research each company and map stock prices
        company_reports: List[CompanyIncidentReport] = []
        for idx, candidate in enumerate(candidates, 1):
            if console:
                console.print(f"  [{idx}/{len(candidates)}] Researching [bold]{candidate.company_name}[/bold]...")
            try:
                report = self.research_single_company(
                    candidate=candidate,
                    original_prompt=prompt,
                    incident_category=discovery_plan.incident_category
                )
                company_reports.append(report)
            except Exception as e:
                if console:
                    console.print(f"    [red]Warning: research for {candidate.company_name} encountered error: {e}.[/red]")

        # 3. Final synthesis
        if console:
            console.print("\n[bold cyan]Step 3: Synthesizing timeline dossiers and financial metrics into final JSON report...[/bold cyan]")

        final_report = self.synthesize_all(
            prompt=prompt,
            discovery_plan=discovery_plan,
            company_reports=company_reports
        )
        return final_report


# ============================================================================
# CLI Display & Entrypoint
# ============================================================================

def display_rich_summary(output: DeepResearchTimelineOutput):
    """Render a clean, visual timeline overview in the terminal."""
    if not console:
        return

    console.rule("[bold green]Deep Research & Stock Timeline Summary[/bold green]")
    console.print(Panel(
        f"[bold]Category:[/bold] {output.incident_category}\n"
        f"[bold]Themes:[/bold] {', '.join(output.core_themes)}\n"
        f"[bold]Executive Synthesis:[/bold]\n{output.executive_synthesis}",
        title="Cross-Company & Financial Analysis",
        border_style="cyan"
    ))

    for comp in output.similar_company_events:
        ticker_str = f" ({comp.stock_ticker})" if comp.stock_ticker else ""
        table = Table(title=f"{comp.company_name}{ticker_str}: {comp.incident_title} ({comp.event_timeframe})", border_style="blue")
        table.add_column("Date / Time", style="cyan", no_wrap=True)
        table.add_column("Phase", style="magenta")
        table.add_column("Event Description", style="white")
        table.add_column("Stock Price", style="green")
        table.add_column("Drawdown %", style="red")
        table.add_column("Impact", style="yellow")

        for m in comp.timeline:
            price_str = f"${m.stock_price:.2f}" if m.stock_price is not None else "-"
            chg_str = f"{m.stock_change_from_baseline_pct:+.1f}%" if m.stock_change_from_baseline_pct is not None else "-"
            table.add_row(m.date, m.phase, m.event[:60] + "...", price_str, chg_str, m.impact[:40] + "...")

        console.print(table)
        if comp.stock_metrics:
            console.print(
                f"[bold cyan]Stock Baseline:[/bold cyan] ${comp.stock_metrics.baseline_price:.2f} ({comp.stock_metrics.baseline_date}) | "
                f"[bold red]Trough:[/bold red] ${comp.stock_metrics.trough_price:.2f} ({comp.stock_metrics.trough_date}) | "
                f"[bold red]Max Drawdown:[/bold red] {comp.stock_metrics.max_drawdown_pct:.1f}%"
            )
        console.print(f"[bold yellow]Similarity Rationale:[/bold yellow] {comp.similarity_rationale}\n")


def run_research_timeline(prompt: str, companies: int = 6, model: Optional[str] = None) -> Dict[str, Any]:
    """Programmatic API: given prompt, returns python dict matching JSON schema."""
    agent = DeepResearchNewsAgent(model_name=model, target_companies=companies)
    output = agent.run(prompt)
    return output.model_dump()


def main():
    parser = argparse.ArgumentParser(
        description="Deep Research Agent: Fetch 5-10 similar news events with major companies and their timelines + stock prices in JSON format."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The incident or news event description to research"
    )
    parser.add_argument(
        "--companies", "-n",
        type=int,
        default=6,
        help="Number of major companies to research (5 to 10, default: 6)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="similar_news_timeline.json",
        help="File path to save the output JSON (default: similar_news_timeline.json)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="LLM model name (defaults to GROQ_MODEL or openai/gpt-oss-120b)"
    )
    parser.add_argument(
        "--groq-key",
        type=str,
        default=None,
        help="Explicitly pass Groq API Key"
    )
    parser.add_argument(
        "--tavily-key",
        type=str,
        default=None,
        help="Explicitly pass Tavily API Key"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print the raw JSON to stdout"
    )

    args = parser.parse_args()

    # Apply command line keys if provided
    if args.groq_key:
        os.environ["GROQ_API_KEY"] = args.groq_key
    if args.tavily_key:
        os.environ["TAVILY_API_KEY"] = args.tavily_key

    # Prompt handling
    prompt = args.prompt
    if not prompt:
        print("\n=== Deep Research News & Stock Timeline Agent ===")
        print("Enter a description of a corporate crisis, tech outage, scandal, bank run, or incident.")
        print("Example: A major cybersecurity glitch or faulty vendor update takes down airlines, banks, and hospital IT systems worldwide\n")
        try:
            prompt = input("Enter prompt: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not prompt:
        print("Error: Empty prompt provided. Exiting.")
        sys.exit(1)

    agent = DeepResearchNewsAgent(
        model_name=args.model,
        target_companies=args.companies
    )

    output = agent.run(prompt)
    json_data = output.model_dump()
    json_string = json.dumps(json_data, indent=2, ensure_ascii=False)

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(json_string)

    if not args.quiet:
        display_rich_summary(output)
        if console:
            console.rule("[bold green]JSON Output Saved with Stock Mappings[/bold green]")
            console.print(f"[bold green]✓ Successfully generated timeline JSON with {len(output.similar_company_events)} companies & stock prices![/bold green]")
            console.print(f"[bold cyan]Saved to file:[/bold cyan] [underline]{os.path.abspath(args.output)}[/underline]")
            console.print(f"[bold yellow]Next Step:[/bold yellow] Run [bold]python visualize_timeline_stocks.py[/bold] to generate graphs and draw forensic conclusions.\n")
        else:
            print(f"\nSuccessfully generated timeline JSON with {len(output.similar_company_events)} companies & stock prices!")
            print(f"Saved to: {os.path.abspath(args.output)}")

    if args.quiet:
        print(json_string)


if __name__ == "__main__":
    main()
