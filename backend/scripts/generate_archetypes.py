#!/usr/bin/env python3
"""
Generate verified archetypal corporate crisis timelines enriched with real yfinance stock data.
Output files are stored in backend/data/timelines/ for instant, accurate precedent matching.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

# Add newagent to sys.path to reuse enrichment functions and schemas
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "newagent"))

from agent import (
    TimelineMilestone,
    CompanyIncidentReport,
    DeepResearchTimelineOutput,
    SourceCitation,
    enrich_stock_timeline,
)

OUTPUT_DIR = REPO_ROOT / "backend" / "data" / "timelines"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_leadership_archetype() -> DeepResearchTimelineOutput:
    """CEO ouster, leadership crisis, and executive turnaround archetype."""
    companies_raw = [
        {
            "company_name": "Intel Corporation",
            "stock_ticker": "INTC",
            "industry": "Semiconductors & Foundry Manufacturing",
            "incident_title": "Pat Gelsinger Forced Retirement & Interim Leadership",
            "event_timeframe": "December 2024",
            "summary": "On December 1, 2024, Intel's board forced the abrupt retirement of CEO Pat Gelsinger after nearly four years of struggling to turn around the chipmaker amidst massive foundry operating losses ($1.6B in Q2, $5.6B in Q3), a 15% workforce reduction, and delayed manufacturing milestones. CFO David Zinsner and Intel Products CEO Michelle Johnston Holthaus were named interim co-CEOs while the board formed a search committee.",
            "similarity_rationale": "Directly parallels sudden corporate leadership upheaval, board loss of confidence, and strategic restructuring following multi-quarter operational underperformance.",
            "key_parallels": [
                "Board abruptly demands CEO resignation following persistent operational shortfalls.",
                "Appointment of interim co-CEOs while conducting executive search.",
                "Substantial strategic uncertainty regarding capital allocation and business unit spin-offs.",
                "Initial modest stock rally on the news followed by reality check on turnaround difficulty.",
            ],
            "key_differences": [
                "Turnaround challenge was rooted in decades-long semiconductor manufacturing lags rather than sudden accounting fraud.",
                "Intel had received billions in CHIPS Act subsidies creating heavy governmental oversight.",
            ],
            "total_impact_assessment": "Immediate leadership vacuum, elevated speculation around splitting foundry and product design units, and ongoing strategic reassessment.",
            "sources": [
                {"title": "Intel CEO Pat Gelsinger Steps Down", "url": "https://www.wsj.com/tech/intel-ceo-pat-gelsinger-steps-down-9fa17b0d"},
                {"title": "SEC 8-K Intel Leadership Transition", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/50863/000005086324000099/intc-20241201.htm"},
            ],
            "timeline": [
                {"date": "2024-11-29", "phase": "Precursor / Baseline", "event": "Final trading day prior to weekend board meeting; Intel stock closes quietly at $24.05.", "impact": "Baseline stock price established ahead of unscheduled leadership change."},
                {"date": "2024-12-01", "phase": "Trigger / Board Ultimatum", "event": "Intel board of directors confronts CEO Pat Gelsinger with retirement ultimatum; Gelsinger resigns.", "impact": "Sudden removal of CEO who led ambitious five-nodes-in-four-years turnaround plan."},
                {"date": "2024-12-02", "phase": "Public Disclosure & Market Opening", "event": "Intel officially announces Gelsinger's retirement; David Zinsner and Michelle Johnston Holthaus named interim co-CEOs.", "impact": "Stock opens higher by +4.5% in pre-market, closing at $24.87 (-0.5% from previous close after intraday swings)."},
                {"date": "2024-12-05", "phase": "Strategic Review & Speculation", "event": "Wall Street analysts publish notes debating potential foundry spin-off or private equity buyout of Altera.", "impact": "Intel stock trades sideways as market recognizes leadership vacuum delays structural decisions."},
                {"date": "2024-12-16", "phase": "Interim Governance Update", "event": "Interim co-CEOs reaffirm commitment to 18A process node schedule and cost-reduction targets.", "impact": "Stock stabilizes around $22.50 with trading volume normalizing."},
            ],
        },
        {
            "company_name": "Starbucks Corporation",
            "stock_ticker": "SBUX",
            "industry": "Retail / Food & Beverage",
            "incident_title": "Laxman Narasimhan Ousted; Chipotle CEO Brian Niccol Appointed",
            "event_timeframe": "August 2024",
            "summary": "On August 13, 2024, Starbucks abruptly replaced CEO Laxman Narasimhan after only 17 months on the job, following consecutive quarters of declining same-store sales and mounting activist pressure from Elliott Investment Management and Starboard Value. The board named Chipotle Chairman and CEO Brian Niccol as Chairman and CEO, sparking the largest single-day market cap increase in Starbucks history.",
            "similarity_rationale": "Classic activist-driven board revolt replacing an underperforming CEO with a proven industry star, generating an instant, explosive stock repricing.",
            "key_parallels": [
                "Underperforming CEO terminated with immediate effect.",
                "Activist hedge funds aggressively pressured the board behind the scenes.",
                "Celebrity CEO poached from competitor with massive compensation package.",
                "Dramatic positive market re-rating reflecting restored investor confidence.",
            ],
            "key_differences": [
                "Starbucks had a ready-made successor instantly in place rather than an interim period.",
                "Stock rallied +24.5% immediately rather than suffering panic selling.",
            ],
            "total_impact_assessment": "Instant $21 billion market cap gain, complete overhaul of executive ranks, and nationwide operational pivot 'Back to Starbucks'.",
            "sources": [
                {"title": "Starbucks Names Brian Niccol Chairman and CEO", "url": "https://stories.starbucks.com/press/2024/starbucks-names-brian-niccol-chairman-and-ceo/"},
                {"title": "Starbucks Shares Soar Record 24.5%", "url": "https://www.cnbc.com/2024/08/13/starbucks-shares-soar-brian-niccol.html"},
            ],
            "timeline": [
                {"date": "2024-08-12", "phase": "Precursor / Baseline", "event": "Starbucks stock closes at $77.01 amid persistent rumors of activist investor pressure.", "impact": "Stock down 20% year-to-date; investor sentiment depressed."},
                {"date": "2024-08-13", "phase": "Trigger & Massive Announcement", "event": "Starbucks announces immediate departure of Laxman Narasimhan and hiring of Brian Niccol.", "impact": "SBUX shares soar +24.5% to $95.90, adding $21.4B in market value in a single trading session."},
                {"date": "2024-08-15", "phase": "Activist Consensus", "event": "Elliott Investment Management issues statement endorsing Niccol's appointment as transformative.", "impact": "Activist proxy battle threat effectively eliminated; institutional inflows accelerate."},
                {"date": "2024-09-09", "phase": "Executive Onboarding", "event": "Brian Niccol officially assumes role and publishes open letter 'Back to Starbucks' pledging simpler cafe workflows.", "impact": "Stock trades solidly near $98.00 as market awaits operational changes."},
                {"date": "2024-10-22", "phase": "Guidance Suspension / Kitchen Sink", "event": "Starbucks prelim Q4 results miss expectations; Niccol suspends fiscal 2025 financial guidance.", "impact": "Stock dips briefly by -2.5% then recovers, as market accepts guidance reset under new management."},
            ],
        },
        {
            "company_name": "The Walt Disney Company",
            "stock_ticker": "DIS",
            "industry": "Entertainment & Media",
            "incident_title": "Bob Chapek Fired Overnight; Bob Iger Reinstated as CEO",
            "event_timeframe": "November 2022",
            "summary": "On Sunday night, November 20, 2022, Disney's board of directors abruptly fired CEO Bob Chapek following disastrous Q4 streaming losses of $1.47 billion and widespread talent and public controversies. The board recalled longtime legendary CEO Bob Iger on a two-year contract to stabilize operations, restructure creative studios, and restore investor confidence.",
            "similarity_rationale": "High-profile board coup terminating an embattled CEO over earnings disaster and reputational friction, turning to a trusted former leader to regain market credibility.",
            "key_parallels": [
                "Abrupt Sunday evening termination without prior public warning.",
                "Catalyzed by a massive quarterly earnings and cash flow miss.",
                "Return of an iconic predecessor to restore institutional morale.",
                "Immediate sweeping restructuring and headcount reductions.",
            ],
            "key_differences": [
                "Successor was a returning legacy CEO rather than an external hire.",
                "Disney faced unique cultural and political scrutiny alongside business challenges.",
            ],
            "total_impact_assessment": "Immediate relief rally (+6.3%), subsequent restructuring cutting 7,000 jobs ($5.5B cost savings), and intense proxy fight with Nelson Peltz.",
            "sources": [
                {"title": "Disney Board Replaces Bob Chapek with Bob Iger", "url": "https://www.nytimes.com/2022/11/20/business/media/bob-iger-disney-ceo.html"},
                {"title": "SEC Form 8-K Disney Executive Transition", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1744489/000174448922000045/dis-20221120.htm"},
            ],
            "timeline": [
                {"date": "2022-11-08", "phase": "Precursor / Earnings Shock", "event": "Disney reports disastrous Q4 earnings with direct-to-consumer streaming losses widening to $1.47B.", "impact": "DIS stock crashes -13.2% the next day to $86.75, touching a multi-year low."},
                {"date": "2022-11-20", "phase": "Trigger / Sunday Board Coup", "event": "Board Chair Susan Arnold notifies Chapek of termination and signs Bob Iger to a 2-year CEO agreement.", "impact": "Shock announcement stuns Hollywood and Wall Street; Chapek exit package finalized."},
                {"date": "2022-11-21", "phase": "Public Reaction & Market Rebound", "event": "Bob Iger officially returns; DIS opens up +8% and closes up +6.3% at $97.58 with heavy volume.", "impact": "Instant restoration of multiple expansion; creative community expresses widespread relief."},
                {"date": "2022-11-28", "phase": "Operational Reorganization", "event": "Iger disbands DMED distribution structure created by Chapek, returning P&L authority to creative heads.", "impact": "Major organizational shakeup; key Chapek lieutenant Kareem Daniel exits."},
                {"date": "2023-02-08", "phase": "Strategic Plan & Mass Layoffs", "event": "Iger announces 7,000 job cuts ($5.5B cost reduction) and division into three core units during Q1 call.", "impact": "Stock trades up +5% after hours; activist Nelson Peltz withdraws proxy contest."},
            ],
        },
        {
            "company_name": "The Boeing Company",
            "stock_ticker": "BA",
            "industry": "Aerospace & Defense",
            "incident_title": "Dave Calhoun Resignation amidst 737 MAX Safety Crisis",
            "event_timeframe": "March 2024",
            "summary": "On March 25, 2024, Boeing CEO Dave Calhoun announced he would step down by year-end 2024, alongside the immediate departure of Commercial Airplanes CEO Stan Deal and Board Chair Larry Kellner. The leadership purge followed months of severe fallout from the January 5 Alaska Airlines Flight 1282 door plug blowout, FAA production caps, and scathing federal safety culture audits.",
            "similarity_rationale": "Exemplifies a governance overhaul forced by systemic manufacturing quality defects, regulatory crackdowns, and customer airline revolt.",
            "key_parallels": [
                "CEO forced out following catastrophic operational quality breakdown.",
                "Coordinated purge of board chair and business unit leadership.",
                "Direct intervention by federal regulators (FAA) capping output.",
                "Customer backlash from airline CEOs demanding new governance.",
            ],
            "key_differences": [
                "Calhoun was given a multi-month transition period rather than immediate removal.",
                "Underlying crisis involved human life safety and criminal settlement compliance.",
            ],
            "total_impact_assessment": "Complete executive slate overhaul, appointment of outsider Kelly Ortberg as CEO, and $21B emergency capital raise.",
            "sources": [
                {"title": "Boeing Announces Executive Leadership Changes", "url": "https://boeing.mediaroom.com/2024-03-25-Boeing-Announces-Executive-Leadership-Changes"},
                {"title": "FAA Steps Up Oversight of Boeing Production", "url": "https://www.faa.gov/newsroom/faa-statement-boeing-production-rate"},
            ],
            "timeline": [
                {"date": "2024-01-05", "phase": "Precursor Incident", "event": "Alaska Airlines Flight 1282 suffers mid-air door plug blowout on Boeing 737 MAX 9.", "impact": "FAA grounds 171 MAX 9 jets; stock plunges -8.0% on first trading day following incident."},
                {"date": "2024-02-06", "phase": "NTSB Findings & Escalation", "event": "NTSB preliminary report finds door plug was installed at Boeing Renton factory with 4 bolts missing.", "impact": "Public confidence collapses; airline CEOs publicly voice extreme frustration."},
                {"date": "2024-03-25", "phase": "Trigger / Executive Purge", "event": "CEO Dave Calhoun announces resignation; Stan Deal replaced immediately; Larry Kellner steps down.", "impact": "BA stock rallies +1.4% to $191.41 on leadership change news before resuming downtrend."},
                {"date": "2024-07-31", "phase": "Successor Appointment", "event": "Boeing names aerospace engineering veteran Kelly Ortberg as new President and CEO.", "impact": "Positive analyst reaction to technical engineering background; stock stabilizes at $190."},
                {"date": "2024-08-08", "phase": "New Leadership Strategy", "event": "Ortberg officially begins tenure, relocating workspace to Seattle to oversee factory floor operations.", "impact": "Shift away from corporate Chicago/Arlington bureaucracy toward manufacturing floor."},
            ],
        },
        {
            "company_name": "Microsoft Corporation",
            "stock_ticker": "MSFT",
            "industry": "Technology / Artificial Intelligence",
            "incident_title": "OpenAI Sam Altman Weekend Ouster & Reinstatement",
            "event_timeframe": "November 2023",
            "summary": "On Friday, November 17, 2023, the non-profit board of OpenAI fired CEO Sam Altman without consulting lead investor Microsoft. Over a frantic 5-day weekend, Microsoft CEO Satya Nadella offered to hire Altman and all OpenAI staff, prompting over 700 of 770 OpenAI employees to threaten resignation. Altman was triumphantly reinstated as CEO on November 21 with a reconstituted board.",
            "similarity_rationale": "The archetypal modern governance crisis involving ideological board splits, high-stakes investor diplomacy, and workforce revolt in an AI market leader.",
            "key_parallels": [
                "Abrupt Friday afternoon firing citing 'lack of candor' by board.",
                "Major corporate investor (Microsoft) caught completely off guard.",
                "Unprecedented employee mutiny threatening mass resignation.",
                "Complete reversal and reinstatement of CEO within one week.",
            ],
            "key_differences": [
                "OpenAI is a capped-profit entity governed by a non-profit board.",
                "Microsoft used the crisis to acquire a non-voting board observer seat and lock in tech access.",
            ],
            "total_impact_assessment": "Strengthened Microsoft's strategic leverage in AI, purged hostile OpenAI board members, and reinforced founder control.",
            "sources": [
                {"title": "OpenAI Announces Leadership Transition", "url": "https://openai.com/index/openai-announces-leadership-transition/"},
                {"title": "Sam Altman Returns to OpenAI", "url": "https://www.wsj.com/tech/ai/sam-altman-returns-to-openai-board-reconstituted-d349ee14"},
            ],
            "timeline": [
                {"date": "2023-11-17", "phase": "Trigger / Sudden Firing", "event": "OpenAI board announces Sam Altman has been pushed out; Greg Brockman quits in protest.", "impact": "MSFT stock dips -1.7% in late Friday trading over fears of OpenAI partnership collapse."},
                {"date": "2023-11-19", "phase": "Microsoft Counter-Offensive", "event": "Satya Nadella announces Sam Altman and Greg Brockman will join Microsoft to lead new advanced AI lab.", "impact": "MSFT stock rallies to a fresh all-time high ($377.44) as investors view Microsoft as ultimate winner."},
                {"date": "2023-11-20", "phase": "Workforce Mutiny", "event": "Over 700 of OpenAI's 770 employees sign open letter demanding board resignation or they will join Microsoft.", "impact": "Existing board loses all operational leverage; emergency negotiations begin."},
                {"date": "2023-11-21", "phase": "Reinstatement & Resolution", "event": "Agreement reached for Altman to return as CEO; new board formed with Bret Taylor and Larry Summers.", "impact": "Crisis resolved in 96 hours; Microsoft secures non-voting observer seat on OpenAI board."},
                {"date": "2023-11-29", "phase": "Aftermath & Normalization", "event": "Altman officially resumes role; Microsoft deepens Azure integration and governance protocols.", "impact": "MSFT shares sustain record highs; investor confidence in AI roadmap cemented."},
            ],
        },
    ]

    reports = []
    for c in companies_raw:
        tl = [TimelineMilestone(**m) for m in c["timeline"]]
        enriched_tl, metrics = enrich_stock_timeline(c["stock_ticker"], tl)
        sources = [SourceCitation(**s) for s in c["sources"]]
        rep = CompanyIncidentReport(
            company_name=c["company_name"],
            stock_ticker=c["stock_ticker"],
            industry=c["industry"],
            incident_title=c["incident_title"],
            event_timeframe=c["event_timeframe"],
            summary=c["summary"],
            similarity_rationale=c["similarity_rationale"],
            key_parallels=c["key_parallels"],
            key_differences=c["key_differences"],
            timeline=enriched_tl,
            stock_metrics=metrics,
            total_impact_assessment=c["total_impact_assessment"],
            sources=sources,
        )
        reports.append(rep)

    return DeepResearchTimelineOutput(
        query_prompt="A Fortune 500 board abruptly forces out the CEO amidst operational underperformance, manufacturing delays, or strategic misalignment",
        generated_at=datetime.now(timezone.utc).isoformat(),
        incident_category="Corporate Governance Shakeup: Executive Ousters & Leadership Turmoil",
        core_themes=[
            "Abrupt board removal of sitting chief executive",
            "Operational underperformance or multi-quarter margin degradation",
            "Interim leadership structure vs immediate rockstar succession",
            "Initial relief rallies vs reality check on capital turnaround complexity",
            "Activist shareholder intervention and executive committee restructuring",
        ],
        executive_synthesis=(
            "**Cross-Company Mechanisms & Governance Failure Modes** — Executive departures in major corporations rarely happen in isolation; "
            "they represent the culmination of accumulated strategic divergence between the executive suite and the board of directors. "
            "Across Intel, Starbucks, Disney, Boeing, and OpenAI/Microsoft, each crisis revealed a breakdown in capital allocation governance "
            "where management persistently fell short of benchmark expectations (Intel's multi-billion foundry losses, Starbucks' declining store traffic, "
            "Disney's streaming cash burn, Boeing's factory floor bolt lapses). In every case, boards waited until an acute catalyst—such as activist filings, "
            "disastrous earnings prints, or public safety blowouts—forced their hand into abrupt dismissals.\n\n"
            "**Market Reaction Velocity & Valuation Dispersion** — Equity markets differentiate sharply between leadership changes accompanied by a proven "
            "immediate successor versus an ambiguous interim vacuum. Starbucks achieved the single largest one-day market capitalization jump in its history (+24.5%, +$21.4B) "
            "because the board simultaneously unveiled Chipotle's celebrated leader Brian Niccol with complete operational autonomy. Disney similarly experienced "
            "an instant +6.3% rally upon Bob Iger's weekend return. In contrast, Intel's dismissal of Pat Gelsinger without a permanent successor sparked only a "
            "transient intraday pop before declining, as investors realized the structural foundry turnaround was prolonged and unaddressed. Boeing's multi-month "
            "lame-duck departure of Dave Calhoun saw persistent equity drift until outside engineer Kelly Ortberg took command.\n\n"
            "**Post-Ouster Strategic Execution & Turnaround Trajectories** — In the aftermath of sudden CEO removals, corporations universally engage in "
            "'kitchen sinking'—suspending multi-year guidance, writing down legacy goodwill, and announcing mass workforce reductions (Intel's 15% layoff, "
            "Disney's 7,000 headcount cut, Starbucks' fiscal 2025 guidance withdrawal). For long-term investors, the pivotal signal is whether the board "
            "empowers new leadership to make structural capital realignments rather than cosmetic public relations shifts."
        ),
        total_companies_analyzed=len(reports),
        similar_company_events=reports,
    )


def build_banking_archetype() -> DeepResearchTimelineOutput:
    """Digital bank run, liquidity contagion, and bond portfolio loss archetype."""
    companies_raw = [
        {
            "company_name": "The Charles Schwab Corporation",
            "stock_ticker": "SCHW",
            "industry": "Financial Services / Brokerage & Banking",
            "incident_title": "Held-to-Maturity Bond Paper Losses & Regional Contagion Defense",
            "event_timeframe": "March 2023",
            "summary": "During the historic March 2023 regional banking panic triggered by SVB's collapse, Charles Schwab was targeted by short sellers and panic selling due to $28 billion in unrealized paper losses on its held-to-maturity (HTM) government bond portfolio. Schwab suffered a sharp -32% drawdown over three sessions as fears of deposit flight spread across social media.",
            "similarity_rationale": "Parallels acute market panic over unrealized bond portfolio mark-to-market losses and rapid digital contagion threatening deposit stability.",
            "key_parallels": [
                "Unrealized paper losses on long-duration Treasuries and MBS due to rapid Fed rate hikes.",
                "Viral social media rumors sparking rapid institutional and retail sentiment shift.",
                "Extreme intraday stock volatility and widening credit default swap spreads.",
                "Successful defense via robust retail deposit loyalty and Federal Reserve emergency facilities.",
            ],
            "key_differences": [
                "Schwab possessed over $100B in available borrowing capacity from FHLB and Fed discount window.",
                "Over 80% of Schwab's deposits were within FDIC insurance limits, unlike SVB's 90%+ uninsured base.",
            ],
            "total_impact_assessment": "Temporary 35% market cap drop, successfully weathered panic without tapping BTFP, organic deposit inflows restored within weeks.",
            "sources": [
                {"title": "Schwab CEO Says Firm Has Ample Liquidity", "url": "https://www.bloomberg.com/news/articles/2023-03-14/schwab-ceo-says-firm-has-enough-liquidity-to-ride-out-storm"},
                {"title": "SEC 8-K Schwab Liquidity and Deposit Update", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/316709/000031670923000021/schw-20230313.htm"},
            ],
            "timeline": [
                {"date": "2023-03-08", "phase": "Precursor / Baseline", "event": "SVB Financial announces capital raise; Schwab closes normally at $76.01.", "impact": "Baseline price before banking contagion explodes across financial sector."},
                {"date": "2023-03-10", "phase": "Trigger / Contagion Outbreak", "event": "FDIC takes possession of Silicon Valley Bank; panic spreads to Schwab over held-to-maturity losses.", "impact": "SCHW stock plunges -11.7% to $58.70 on massive trading volume."},
                {"date": "2023-03-13", "phase": "Peak Panic & Defense", "event": "Stock drops another -11.6% intraday to $51.91; CEO Walt Bettinger confirms massive liquidity reserves and organic deposit inflows.", "impact": "Trough price reached; billions in retail dip-buying volume enters the market."},
                {"date": "2023-03-14", "phase": "Relief & Stabilization", "event": "Wall Street firms issue upgrade notes citing Schwab's $100B cash reserves; stock rebounds +9.2%.", "impact": "Contagion halted; deposit outflow data proves retail base is stable."},
                {"date": "2023-03-24", "phase": "Normalization", "event": "Fed emergency Bank Term Funding Program (BTFP) backstops liquidity across the banking sector.", "impact": "Stock stabilizes in $55-$60 range; systemic banking crisis containment achieved."},
            ],
        },
        {
            "company_name": "Western Alliance Bancorporation",
            "stock_ticker": "WAL",
            "industry": "Regional Commercial Banking",
            "incident_title": "Surviving Acute Digital Deposit Run and Short Attack",
            "event_timeframe": "March - May 2023",
            "summary": "Western Alliance Bancorporation was thrust to the epicenter of the regional banking crisis following the seizures of SVB, Signature, and First Republic. Short sellers and social media panics drove WAL shares down over 75% peak-to-trough, yet the bank survived through aggressive liquidity disclosures, deposit guarantees, and tech customer retention.",
            "similarity_rationale": "Prime example of a regional bank enduring a digital deposit run, successfully mobilizing liquidity, and recovering to profitability.",
            "key_parallels": [
                "Sudden digital withdrawal run enabled by mobile banking and venture network contagion.",
                "Targeted by aggressive short selling and halt-inducing volatility.",
                "Mobilized Federal Reserve Discount Window and FHLB advances to replace fleeing deposits.",
                "Rebuilt deposit base by pivoting to insured sweep accounts.",
            ],
            "key_differences": [
                "Unlike SVB and First Republic, Western Alliance had a diversified commercial and retail loan book.",
                "Survived without FDIC receivership or forced government sale.",
            ],
            "total_impact_assessment": "Severe stock crash followed by a dramatic 150%+ recovery as deposit stabilization was verified in Q2 earnings.",
            "sources": [
                {"title": "Western Alliance Reassures Depositors on Liquidity", "url": "https://www.reuters.com/business/finance/western-alliance-shares-fall-bank-reassures-liquidity-2023-03-13/"},
                {"title": "SEC 8-K WAL Daily Deposit Disclosures", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1212544/000121254423000018/wal-20230317.htm"},
            ],
            "timeline": [
                {"date": "2023-03-08", "phase": "Precursor / Baseline", "event": "Western Alliance stock trades at $71.69 ahead of SVB collapse.", "impact": "Pre-crisis valuation established."},
                {"date": "2023-03-10", "phase": "Contagion Wave 1", "event": "SVB failure triggers indiscriminate selling of mid-sized banks; WAL drops -20.9% to $49.34.", "impact": "Tech startup depositors begin transferring funds to money center banks."},
                {"date": "2023-03-13", "phase": "Severe Intraday Halt Plunge", "event": "WAL stock halts multiple times, touching an intraday trough of $26.11 (-47% in one session).", "impact": "Bank issues emergency statement confirming $25B in available cash and borrowing capacity."},
                {"date": "2023-03-17", "phase": "Deposit Transparency Initiative", "event": "WAL begins publishing unprecedented weekly deposit updates showing 68% insured deposit ratio.", "impact": "Short squeeze begins; stock surges +45% from lows over three days."},
                {"date": "2023-05-04", "phase": "PacWest Spillover & Ultimate Rebound", "event": "After First Republic seizure, false rumors trigger second brief dip; WAL management aggressively refutes report.", "impact": "WAL confirms deposit growth of $1.8B since March; stock begins permanent recovery back above $50."},
            ],
        },
        {
            "company_name": "SPDR S&P Regional Banking ETF",
            "stock_ticker": "KRE",
            "industry": "Banking Sector Index / Benchmark",
            "incident_title": "Systemic Regional Banking Contagion & Liquidity Shock",
            "event_timeframe": "March - May 2023",
            "summary": "The KRE regional banking benchmark captured the broader contagion across mid-sized American lenders when rising interest rates exposed paper portfolio markdowns and prompted over $100 billion in uninsured deposit reallocation to global systematically important banks (G-SIBs).",
            "similarity_rationale": "Represents the aggregate equity and liquidity drawdown across the entire regional banking sector during an acute bank run cycle.",
            "key_parallels": [
                "Synchronized multiple contraction across all mid-cap financial institutions.",
                "Spread of fear via social media networks and digital mobile banking platforms.",
                "Intervention by Fed, Treasury, and FDIC via systemic risk exceptions and the BTFP facility.",
                "Prolonged recovery timeline as banks faced elevated deposit funding costs.",
            ],
            "key_differences": [
                "Index product reflecting diversified sector performance rather than idiosyncratic single-bank insolvency.",
            ],
            "total_impact_assessment": "Benchmark lost 40% of its value over 8 weeks, permanently reshaping regional bank regulatory thresholds and deposit pricing.",
            "sources": [
                {"title": "Regional Banks Plunge as Contagion Spreads", "url": "https://www.wsj.com/articles/bank-shares-plunge-as-fallout-from-svb-spreads-6a05988e"},
            ],
            "timeline": [
                {"date": "2023-03-06", "phase": "Precursor Baseline", "event": "KRE trades at $63.00 with regional banks enjoying strong net interest margins.", "impact": "Peak sector valuation before crisis onset."},
                {"date": "2023-03-09", "phase": "Contagion Outbreak", "event": "SVB capital crisis triggers a 8.1% drop in the regional banking ETF.", "impact": "Broad-based liquidation across regional banks commences."},
                {"date": "2023-03-13", "phase": "Systemic Risk Intervention", "event": "Biden administration guarantees all uninsured deposits at SVB and Signature Bank; Fed launches BTFP.", "impact": "KRE drops another -12.3% as market questions viability of remaining regional banks."},
                {"date": "2023-05-01", "phase": "First Republic Seizure", "event": "FDIC seizes First Republic and sells it to JPMorgan; KRE touches cyclical low of $36.00.", "impact": "Final major bank resolution of the spring crisis concluded."},
                {"date": "2023-06-15", "phase": "Stabilization & Recovery", "event": "Regional bank deposits stabilize industry-wide; deposit beta increases but insolvency risk recedes.", "impact": "KRE begins steady climb back toward $45-$50."},
            ],
        },
        {
            "company_name": "JPMorgan Chase & Co.",
            "stock_ticker": "JPM",
            "industry": "Global Systemically Important Financial Institution",
            "incident_title": "G-SIB Safe Haven Flight & Rescue Acquisition of First Republic",
            "event_timeframe": "March - May 2023",
            "summary": "As regional lenders faced deposit runs, JPMorgan Chase acted as the prime beneficiary of capital flight, absorbing over $50 billion in institutional deposits. On May 1, 2023, JPM won the FDIC competitive auction to acquire First Republic Bank's $203 billion in assets and $92 billion in deposits, cementing CEO Jamie Dimon's reputation as the lender of last resort.",
            "similarity_rationale": "Shows the mirror image of a bank run: the 'too-big-to-fail' safe haven that absorbs displaced assets and secures distressed takeover discounts.",
            "key_parallels": [
                "Massive safe-haven deposit inflows as corporate treasurers fled regional institutions.",
                "Orchestrated $30B private bank deposit lifeline to First Republic in March.",
                "Engineered government-assisted weekend acquisition with FDIC loss-sharing agreement.",
                "Immediate accretive earnings boost ($2.6B one-time accounting gain).",
            ],
            "key_differences": [
                "JPMorgan acted as the acquirer and beneficiary rather than the victim of the bank run.",
                "G-SIB balance sheet and fortress capital ratios insulated the firm from liquidity panic.",
            ],
            "total_impact_assessment": "Gained $100B+ in high-net-worth client assets, +$500M annual net income accretion, and stock surged to record highs.",
            "sources": [
                {"title": "JPMorgan Wins Auction for First Republic", "url": "https://www.wsj.com/articles/first-republic-bank-taken-over-by-fdic-jpmorgan-to-buy-assets-450f3f61"},
                {"title": "SEC 8-K JPM First Republic Purchase", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/19617/000001961723000282/jpm-20230501.htm"},
            ],
            "timeline": [
                {"date": "2023-03-08", "phase": "Precursor Baseline", "event": "JPM stock trades at $137.80 prior to banking sector turmoil.", "impact": "Pre-crisis valuation established."},
                {"date": "2023-03-10", "phase": "Safe Haven Inflows", "event": "SVB collapse triggers tens of billions in flight-to-safety deposits moving to JPMorgan.", "impact": "JPM stock dips mildly (-0.4%) far outperforming regional bank peers."},
                {"date": "2023-03-16", "phase": "Private Rescue Coalition", "event": "Jamie Dimon leads 11 large banks in depositing $30B of uninsured funds into First Republic.", "impact": "Buys critical time for FDIC resolution; JPM deposits $5B of its own cash."},
                {"date": "2023-05-01", "phase": "Acquisition Announcement", "event": "JPMorgan acquires substantial majority of First Republic assets from FDIC with loss-share agreement.", "impact": "JPM shares rise +2.1% to $141.20 as market recognizes highly favorable financial terms."},
                {"date": "2023-05-22", "phase": "Investor Day Triumph", "event": "JPMorgan raises net interest income guidance to $84B at Investor Day following First Republic integration.", "impact": "Stock begins powerful sustained rally toward all-time highs above $170."},
            ],
        },
        {
            "company_name": "UBS Group AG",
            "stock_ticker": "UBS",
            "industry": "Global Wealth Management & Investment Banking",
            "incident_title": "Emergency State-Brokered Takeover of Credit Suisse",
            "event_timeframe": "March 2023",
            "summary": "On Sunday, March 19, 2023, the Swiss government, FINMA, and the Swiss National Bank forced an emergency CHF 3 billion ($3.2B) acquisition of 167-year-old Credit Suisse by its arch-rival UBS to prevent a systemic global banking panic. The deal featured a controversial wipeout of CHF 16 billion in AT1 capital bonds.",
            "similarity_rationale": "The international epicenter of the 2023 banking crisis: an ultra-fast sovereign-engineered merger to halt cross-border financial contagion.",
            "key_parallels": [
                "Historic global institution suffers multi-billion deposit and wealth management outflows.",
                "Emergency weekend negotiations bypassing normal shareholder approval votes.",
                "Central bank provides massive liquidity backstops (CHF 100B SNB facility).",
                "Controversial restructuring erasing subordinated debt while preserving equity value.",
            ],
            "key_differences": [
                "Cross-border Swiss jurisdiction with direct emergency federal decree.",
                "Total write-down of AT1 bonds sparked international legal litigation.",
            ],
            "total_impact_assessment": "Created a $1.7 trillion wealth management behemoth; UBS stock initially dipped then rallied over 60% on negative goodwill gain.",
            "sources": [
                {"title": "UBS Agrees to Buy Credit Suisse in Historic Deal", "url": "https://www.ft.com/content/0a9446d6-f288-466e-9be7-b37936a7b212"},
            ],
            "timeline": [
                {"date": "2023-03-14", "phase": "Precursor Baseline", "event": "Credit Suisse identifies 'material weaknesses' in financial reporting controls; UBS trades at $20.08.", "impact": "Pre-acquisition baseline established."},
                {"date": "2023-03-15", "phase": "Crisis Catalyst", "event": "Saudi National Bank chairman rules out further equity investment in Credit Suisse; CS stock collapses.", "impact": "Credit default swaps on Credit Suisse spike to distressed levels."},
                {"date": "2023-03-19", "phase": "Emergency Sunday Merger", "event": "Swiss authorities broker emergency takeover of CS by UBS for CHF 3B; FINMA writes down $17B of AT1 bonds.", "impact": "Systemic collapse prevented; global market panic averted."},
                {"date": "2023-03-20", "phase": "Market Digestion & Rebound", "event": "UBS stock opens down -14% on integration risk but closes up +1.3% as analysts assess $34B accounting badwill gain.", "impact": "Massive institutional buying as UBS secures immense wealth management market share at bargain price."},
                {"date": "2023-08-31", "phase": "Record Quarterly Profit", "event": "UBS reports historic $29B Q2 net profit driven by negative goodwill from Credit Suisse acquisition.", "impact": "Stock hits highest level since 2008 as integration proceeds ahead of schedule."},
            ],
        },
    ]

    reports = []
    for c in companies_raw:
        tl = [TimelineMilestone(**m) for m in c["timeline"]]
        enriched_tl, metrics = enrich_stock_timeline(c["stock_ticker"], tl)
        sources = [SourceCitation(**s) for s in c["sources"]]
        rep = CompanyIncidentReport(
            company_name=c["company_name"],
            stock_ticker=c["stock_ticker"],
            industry=c["industry"],
            incident_title=c["incident_title"],
            event_timeframe=c["event_timeframe"],
            summary=c["summary"],
            similarity_rationale=c["similarity_rationale"],
            key_parallels=c["key_parallels"],
            key_differences=c["key_differences"],
            timeline=enriched_tl,
            stock_metrics=metrics,
            total_impact_assessment=c["total_impact_assessment"],
            sources=sources,
        )
        reports.append(rep)

    return DeepResearchTimelineOutput(
        query_prompt="A bank suffers an acute digital bank run and sudden collapse due to unrealized bond portfolio losses and uninsured deposit flight",
        generated_at=datetime.now(timezone.utc).isoformat(),
        incident_category="Financial Contagion: Digital Bank Runs, Liquidity Shocks & Bond Portfolio Losses",
        core_themes=[
            "Unrealized held-to-maturity (HTM) fixed income losses from rapid interest rate hikes",
            "Hyper-speed digital deposit withdrawals via mobile apps and venture chat groups",
            "Concentration of uninsured corporate and institutional deposit balances",
            "Central bank liquidity intervention (BTFP, Discount Window) and emergency systemic risk determinations",
            "Distressed asset transfers to G-SIBs and forced sovereign-brokered mergers",
        ],
        executive_synthesis=(
            "**Systemic Fragility & Duration Mismatch Dynamics** — The 2023 banking crisis revealed a new paradigm of financial panic: "
            "the digital bank run. Decades of low interest rates incentivized financial institutions to invest long-duration fixed-rate "
            "Treasuries and mortgage-backed securities (MBS) classified as Held-to-Maturity (HTM). When the Federal Reserve hiked interest rates by "
            "over 500 basis points at record velocity, paper mark-to-market losses erased significant portions of tangible common equity. "
            "Unlike traditional 20th-century bank runs where depositors queued on sidewalks, modern withdrawals materialized in minutes via "
            "mobile banking and synchronized Slack and WhatsApp corporate channels, draining over $40 billion from Silicon Valley Bank in a single day.\n\n"
            "**Contagion Transmission & Market Bifurcation** — The equity markets responded with violent repricing that bifurcated financial institutions "
            "into vulnerable regional targets and fortress beneficiaries. Mid-sized lenders with high ratios of uninsured commercial deposits "
            "(Western Alliance, First Republic, Signature) suffered 50% to 90% equity market drawdowns and multiple halts. Conversely, Global "
            "Systemically Important Banks (G-SIBs) led by JPMorgan Chase became immediate safe-haven destinations, absorbing over $50 billion in "
            "inflows within days. Charles Schwab, despite suffering a steep -32% drawdown over HTM concerns, demonstrated that retail deposit "
            "fragmentation and vast borrowing capacity from the FHLB and Fed could successfully absorb severe panic selling.\n\n"
            "**Resolution Mechanisms & Structural Ramifications** — Resolving digital liquidity runs required unprecedented regulatory maneuvers: "
            "the invocation of the Systemic Risk Exception guaranteeing uninsured depositors, the establishment of the Fed's Bank Term Funding Program (BTFP) "
            "loaning against par value rather than market price, and sovereign-brokered weekend auctions. While these interventions averted a broader "
            "1930s-style domino collapse, they accelerated the concentration of the American banking sector into mega-banks and established permanently higher "
            "deposit costs that compressed regional bank net interest margins throughout subsequent quarters."
        ),
        total_companies_analyzed=len(reports),
        similar_company_events=reports,
    )


def build_antitrust_archetype() -> DeepResearchTimelineOutput:
    """Antitrust lawsuits, regulatory scrutiny, and monopolistic enforcement archetype."""
    companies_raw = [
        {
            "company_name": "Apple Inc.",
            "stock_ticker": "AAPL",
            "industry": "Consumer Technology & Services",
            "incident_title": "US DOJ Landmark Smartphone Monopolization Lawsuit",
            "event_timeframe": "March 2024",
            "summary": "On March 21, 2024, the US Department of Justice alongside 16 state attorneys general filed an expansive civil antitrust lawsuit against Apple, accusing the company of illegally maintaining a monopoly over the smartphone market through exclusionary app store rules, anti-steering limits, iMessage exclusivity, and restriction of third-party digital wallets.",
            "similarity_rationale": "High-profile government antitrust prosecution targeting core ecosystem lock-in and high-margin services revenue.",
            "key_parallels": [
                "Comprehensive civil antitrust complaint filed by DOJ and state AG coalition.",
                "Targets high-margin services moat (App Store fees, Apple Pay, ecosystem barriers).",
                "Immediate sharp valuation loss on filing day followed by long-term legal defense.",
                "Concurrent regulatory enforcement across jurisdictions (EU Digital Markets Act fines).",
            ],
            "key_differences": [
                "Lawsuit faces multi-year trial and appellate timeline before any structural remedies can be implemented.",
                "Apple has retained massive balance sheet cash to mount an aggressive constitutional and legal defense.",
            ],
            "total_impact_assessment": "Immediate $115B market cap wipeout (-4.1%), lingering regulatory overhang, and incremental policy concessions in EU/US markets.",
            "sources": [
                {"title": "Justice Department Sues Apple for Monopolizing Smartphone Markets", "url": "https://www.justice.gov/opa/pr/justice-department-sues-apple-monopolizing-smartphone-markets"},
                {"title": "Apple Shares Drop 4.1% on DOJ Lawsuit", "url": "https://www.cnbc.com/2024/03/21/apple-shares-fall-on-doj-antitrust-lawsuit.html"},
            ],
            "timeline": [
                {"date": "2024-03-20", "phase": "Precursor Baseline", "event": "Apple closes at $178.67 ahead of anticipated DOJ legal action.", "impact": "Baseline valuation established."},
                {"date": "2024-03-21", "phase": "Trigger / Lawsuit Filing", "event": "DOJ and 16 AGs file civil antitrust suit in New Jersey federal court accusing Apple of illegal smartphone monopoly.", "impact": "AAPL stock drops -4.1% to $171.37, erasing $115 billion in market capitalization."},
                {"date": "2024-03-25", "phase": "Legal Response & Analyst Assessment", "event": "Apple issues fierce defense stating suit threatens company identity; Wall Street predicts 3-5 year court battle.", "impact": "Selling pressure pauses; stock trades sideways around $170."},
                {"date": "2024-06-24", "phase": "EU Regulatory Escalation", "event": "European Commission informs Apple of preliminary view that App Store steering rules breach DMA.", "impact": "Renewed regulatory scrutiny; Apple announces delayed rollout of Apple Intelligence in EU."},
                {"date": "2024-08-01", "phase": "Resilience & Earnings Rebound", "event": "Apple reports strong Q3 earnings driven by iPad and Services growth; unveils Apple Intelligence AI integration.", "impact": "Stock climbs to new all-time highs above $220, demonstrating product moat resilience over legal risk."},
            ],
        },
        {
            "company_name": "Alphabet Inc.",
            "stock_ticker": "GOOGL",
            "industry": "Internet & Search Services",
            "incident_title": "Search Monopoly Trial Verdict & DOJ Breakup Proposal",
            "event_timeframe": "August - November 2024",
            "summary": "On August 5, 2024, US District Judge Amit Mehta delivered a landmark ruling that Google violated Section 2 of the Sherman Act by maintaining an illegal monopoly in general search services and general search text ads through $26 billion in annual default distribution contracts. In November 2024, the DOJ officially petitioned the court to force Google to divest its Chrome web browser.",
            "similarity_rationale": "Direct precedent for a tech titan suffering an adverse judicial antitrust verdict with proposed structural divestiture remedies.",
            "key_parallels": [
                "Historic judicial finding of illegal monopolization under Sherman Act Section 2.",
                "DOJ demanding structural remedies including divesting flagship assets (Chrome browser).",
                "Threatens critical search revenue distribution deals (e.g. $20B annual payment to Apple).",
                "Created persistent multiple compression relative to tech mega-cap peers.",
            ],
            "key_differences": [
                "Trial reached actual liability verdict, whereas Apple and Amazon are still in pre-trial phases.",
                "Google is appealing the decision to the DC Circuit Court of Appeals.",
            ],
            "total_impact_assessment": "Depressed valuation multiple during late 2024, existential threat to default distribution agreements, and active structural breakup litigation.",
            "sources": [
                {"title": "Federal Judge Rules Google Is a Monopolist in Search", "url": "https://www.nytimes.com/2024/08/05/technology/google-antitrust-ruling.html"},
                {"title": "DOJ Pushes for Google to Sell Chrome Browser", "url": "https://www.bloomberg.com/news/articles/2024-11-18/doj-will-push-google-to-sell-off-chrome-to-break-search-monopoly"},
            ],
            "timeline": [
                {"date": "2024-08-02", "phase": "Precursor Baseline", "event": "Alphabet trades at $166.50 amidst broader tech summer pullback.", "impact": "Baseline price before judge's sealed ruling is published."},
                {"date": "2024-08-05", "phase": "Trigger / Landmark Liability Ruling", "event": "Judge Amit Mehta issues 277-page ruling finding Google operated as an illegal search monopolist.", "impact": "GOOGL stock drops -4.5% to $159.25 on heavy volume; tech sector rattled."},
                {"date": "2024-10-08", "phase": "Remedies Framework Proposal", "event": "DOJ files initial court filing outlining potential remedies, including behavioral restrictions and structural separation.", "impact": "GOOGL dips -1.6% as threat of Chrome or Android spin-off enters formal proceedings."},
                {"date": "2024-11-20", "phase": "Formal Chrome Divestiture Demand", "event": "DOJ formally submits proposed final judgment requiring Google to divest Chrome and ban default search exclusivity deals.", "impact": "Stock trades under pressure; Wall Street models revenue impact of losing direct browser channel."},
                {"date": "2024-12-10", "phase": "Appellate Strategy & AI Shift", "event": "Google prepares appeal; market shifts focus toward Google's Gemini 2.0 AI model capabilities.", "impact": "Stock recovers ground as legal remedies trial scheduled for mid-2025."},
            ],
        },
        {
            "company_name": "Microsoft Corporation",
            "stock_ticker": "MSFT",
            "industry": "Software & Cloud Gaming",
            "incident_title": "$69B Activision Blizzard Antitrust Battle & Global Approvals",
            "event_timeframe": "January 2022 - October 2023",
            "summary": "Microsoft's $68.7 billion proposed acquisition of Activision Blizzard triggered the fiercest global merger antitrust battle of the decade, facing aggressive lawsuits from the US FTC and an outright veto by the UK Competition and Markets Authority (CMA). Microsoft overcame the challenge through court victory against the FTC and restructuring cloud streaming rights with Ubisoft.",
            "similarity_rationale": "Shows how a mega-cap tech company defeated regulatory antitrust obstruction through courtroom litigation and proactive remedy concessions.",
            "key_parallels": [
                "Coordinated resistance from US (FTC), UK (CMA), and EU antitrust regulators.",
                "FTC sought federal injunction to block deal; Microsoft defeated FTC in federal district court.",
                "Restructured deal terms (selling cloud gaming rights to Ubisoft) to satisfy foreign regulators.",
                "Ultimate successful closure of the largest gaming acquisition in history.",
            ],
            "key_differences": [
                "Merger antitrust review rather than a Section 2 monopolization behavioral lawsuit.",
                "Microsoft won outright in court against regulator Lina Khan's FTC.",
            ],
            "total_impact_assessment": "Successfully closed $69B transaction, expanded Xbox Game Pass pipeline, and established precedent that US courts require rigorous consumer harm proof.",
            "sources": [
                {"title": "Judge Hands FTC Defeat in Fight Over Microsoft Activision Deal", "url": "https://www.wsj.com/articles/microsoft-deal-for-activision-blizzard-gets-green-light-from-judge-d374d6c7"},
                {"title": "Microsoft Closes $69 Billion Deal for Activision", "url": "https://www.nytimes.com/2023/10/13/business/microsoft-activision-deal-closed.html"},
            ],
            "timeline": [
                {"date": "2022-01-18", "phase": "Deal Announcement", "event": "Microsoft announces definitive agreement to acquire Activision Blizzard for $95/share in cash.", "impact": "MSFT stock dips -2.4% while ATVI surges +25%."},
                {"date": "2022-12-08", "phase": "FTC Administrative Lawsuit", "event": "FTC votes 3-1 to issue administrative complaint seeking to block the transaction.", "impact": "Deal spread widens significantly as regulatory risk escalates."},
                {"date": "2023-04-26", "phase": "UK CMA Shock Veto", "event": "UK CMA unexpectedly blocks merger citing concerns over the nascent cloud gaming market.", "impact": "Deal declared nearly dead by media; Microsoft stock trades down -2.2%."},
                {"date": "2023-07-11", "phase": "Decisive Federal Court Victory", "event": "US District Judge Jacqueline Scott Corley denies FTC preliminary injunction after 5-day evidentiary hearing.", "impact": "Major legal triumph; Activision shares soar +10%; FTC appeal rejected by Ninth Circuit."},
                {"date": "2023-10-13", "phase": "CMA Clearance & Deal Closing", "event": "UK CMA approves restructured transaction; Microsoft officially closes $69B acquisition.", "impact": "21-month antitrust war concludes; Activision consolidated into Microsoft results."},
            ],
        },
        {
            "company_name": "Meta Platforms, Inc.",
            "stock_ticker": "META",
            "industry": "Social Media & Digital Advertising",
            "incident_title": "FTC Monopolization Lawsuit & Potential Unwinding of Instagram/WhatsApp",
            "event_timeframe": "2020 - 2024",
            "summary": "The FTC and 48 states sued Meta in December 2020 alleging illegal monopolization of personal social networking by acquiring nascent competitors Instagram (2012) and WhatsApp (2014) to eliminate competitive threats. After surviving an initial dismissal, the case has proceeded toward a high-stakes federal trial seeking the potential divestiture of both apps.",
            "similarity_rationale": "Exemplifies structural retrospective antitrust challenges targeting historic M&A approvals and platform dominance.",
            "key_parallels": [
                "Government agency seeking retrospective unwinding of decade-old approved acquisitions.",
                "Threatens the core engagement engines (Instagram Reels, WhatsApp) of the parent company.",
                "Significant discovery and internal executive email disclosure (Mark Zuckerberg emails).",
                "Ongoing legal overhang spanning multiple administration tenures.",
            ],
            "key_differences": [
                "Instagram and WhatsApp are deeply integrated into Meta's core ad-targeting infrastructure, making separation technologically complex.",
                "Meta successfully dismissed the state AG claims on laches (unreasonable delay) grounds.",
            ],
            "total_impact_assessment": "Persistent regulatory discount, multi-million dollar annual litigation costs, but minimal operational impairment to date.",
            "sources": [
                {"title": "FTC Sues Facebook for Illegal Monopolization", "url": "https://www.ftc.gov/news-events/news/press-releases/2020/12/ftc-sues-facebook-illegal-monopolization"},
            ],
            "timeline": [
                {"date": "2020-12-09", "phase": "Initial Filing Shock", "event": "FTC and 48 attorneys general file dual antitrust complaints against Facebook seeking breakup.", "impact": "FB shares drop -1.9% as market digests unprecedented unwinding request."},
                {"date": "2021-06-28", "phase": "Initial Dismissal Victory", "event": "Federal Judge James Boasberg dismisses FTC complaint for failing to define market share plausibly.", "impact": "Facebook shares surge +4.2%, crossing $1 trillion market cap for the first time."},
                {"date": "2022-01-11", "phase": "Amended Complaint Survives", "event": "Judge Boasberg allows FTC's amended complaint to move forward into formal discovery.", "impact": "Prolonged legal timeline confirmed; litigation continues in background."},
                {"date": "2024-04-05", "phase": "Summary Judgment Defense", "event": "Meta files motion for summary judgment arguing FTC cannot prove consumer harm in dynamic market.", "impact": "Meta stock unaffected as market focuses on AI and ad-revenue re-acceleration."},
                {"date": "2024-11-13", "phase": "Trial Date Ordered", "event": "Judge Boasberg largely denies Meta's bid to dismiss FTC claims, clearing case for trial in 2025.", "impact": "Stock experiences minor volatility; Meta prepares trial defense."},
            ],
        },
        {
            "company_name": "Amazon.com, Inc.",
            "stock_ticker": "AMZN",
            "industry": "E-Commerce & Cloud Computing",
            "incident_title": "FTC Marketplace Monopolization & 'Project Nessie' Lawsuit",
            "event_timeframe": "September 2023 - 2024",
            "summary": "On September 26, 2023, the FTC under Chair Lina Khan alongside 17 state AGs sued Amazon alleging illegal maintenance of monopoly power in online superstores and marketplace services. The suit accused Amazon of anti-discounting pricing algorithms ('Project Nessie') and coercing third-party merchants into using Fulfillment by Amazon (FBA) for Prime eligibility.",
            "similarity_rationale": "Direct government challenge against marketplace ecosystem pricing mechanics and vendor lock-in.",
            "key_parallels": [
                "Bipartisan antitrust challenge targeting core e-commerce merchant relationships.",
                "Allegations of secret pricing algorithms inflating costs across the retail web.",
                "Regulatory scrutiny over bundling fulfillment logistics with platform search prominence.",
                "Market shrugged off initial filing as retail margins and AWS growth accelerated.",
            ],
            "key_differences": [
                "Lawsuit explicitly omitted Amazon Web Services (AWS), avoiding the most profitable segment of the business.",
                "Court dismissed several state-level claims while keeping core antitrust claims alive.",
            ],
            "total_impact_assessment": "EHR marketplace operational adjustments, ongoing discovery, and multi-year trial positioning without near-term revenue impact.",
            "sources": [
                {"title": "FTC Sues Amazon for Illegally Maintaining Monopoly Power", "url": "https://www.ftc.gov/news-events/news/press-releases/2023/09/ftc-sues-amazon-illegally-maintaining-monopoly-power"},
            ],
            "timeline": [
                {"date": "2023-09-25", "phase": "Precursor Baseline", "event": "Amazon stock closes at $131.27 before FTC action.", "impact": "Baseline price before formal filing."},
                {"date": "2023-09-26", "phase": "Trigger / FTC Complaint", "event": "FTC and 17 state AGs file sweeping antitrust lawsuit in federal court in Seattle.", "impact": "AMZN stock falls -4.0% to $125.98 on high volume."},
                {"date": "2023-11-02", "phase": "Unredacted Complaint Disclosures", "event": "Court unseals details regarding 'Project Nessie', an algorithm allegedly used to test price matching.", "impact": "Media coverage spikes; Amazon clarifies algorithm was discontinued years earlier."},
                {"date": "2024-09-30", "phase": "Motion to Dismiss Ruling", "event": "Judge John Chun allows majority of FTC antitrust claims to proceed to trial while narrowing state claims.", "impact": "Stock remains stable around $186; trial scheduled for late 2026."},
                {"date": "2024-10-31", "phase": "Earnings Outperformance", "event": "Amazon reports strong Q3 operating income of $17.4B powered by AWS and advertising.", "impact": "Stock jumps +6.2% the following day, illustrating fundamental earnings power overcoming legal headwinds."},
            ],
        },
    ]

    reports = []
    for c in companies_raw:
        tl = [TimelineMilestone(**m) for m in c["timeline"]]
        enriched_tl, metrics = enrich_stock_timeline(c["stock_ticker"], tl)
        sources = [SourceCitation(**s) for s in c["sources"]]
        rep = CompanyIncidentReport(
            company_name=c["company_name"],
            stock_ticker=c["stock_ticker"],
            industry=c["industry"],
            incident_title=c["incident_title"],
            event_timeframe=c["event_timeframe"],
            summary=c["summary"],
            similarity_rationale=c["similarity_rationale"],
            key_parallels=c["key_parallels"],
            key_differences=c["key_differences"],
            timeline=enriched_tl,
            stock_metrics=metrics,
            total_impact_assessment=c["total_impact_assessment"],
            sources=sources,
        )
        reports.append(rep)

    return DeepResearchTimelineOutput(
        query_prompt="A dominant technology or industrial corporation faces major regulatory enforcement, DOJ antitrust lawsuit, or government antitrust trial",
        generated_at=datetime.now(timezone.utc).isoformat(),
        incident_category="Regulatory Enforcement: Antitrust Litigation, Monopoly Probes & Structural Remedies",
        core_themes=[
            "DOJ and FTC Section 2 Sherman Act civil monopolization enforcement",
            "Platform ecosystem lock-in, proprietary app stores, and anti-steering practices",
            "Government demands for structural breakup or divestiture of key product lines",
            "Initial market cap shock followed by extended multi-year judicial litigation timelines",
            "Defensive legal resilience and operational adaptation through minor policy concessions",
        ],
        executive_synthesis=(
            "**Regulatory Theory & Platform Ecosystem Scrutiny** — The modern era of antitrust enforcement marks a structural pivot "
            "from classical consumer price gouging theories toward 'ecosystem foreclosure' and 'nascent competitor acquisition'. "
            "Across Apple, Alphabet/Google, Microsoft, Meta, and Amazon, regulatory bodies (DOJ and FTC) have targeted the software architecture "
            "that locks consumers into single-vendor platforms: Apple's mobile app store fees and iMessage barriers, Google's $20+ billion annual "
            "default search distribution contracts, Meta's historical defensive purchases of Instagram and WhatsApp, and Amazon's Buy Box fulfillment mechanics. "
            "Regulators argue these practices suppress contestability and cement permanent digital monopolies.\n\n"
            "**Market Reaction Velocity & The 'Litigation Discount'** — Equity markets punish antitrust actions in two distinct phases: an immediate "
            "acute shock upon formal complaint filing (-4.0% to -4.5% intraday drops erasing $50B to $115B in market cap), followed by a prolonged "
            "period of multiple compression. However, historical precedents demonstrate that judicial timelines move at an glacial pace compared to tech innovation cycles. "
            "Appeals, discovery, and remedy hearings routinely span 3 to 7 years. In cases where judges have ruled against the corporation (Judge Mehta's ruling "
            "against Google Search), market sentiment initially cratered over structural divestiture fears (forced sale of Chrome or Android), but subsequently "
            "stabilized as investors recognized the extensive appellate runway before any real-world breakup could take effect.\n\n"
            "**Strategic Adaptations & Precedent Outcomes** — Rather than causing catastrophic operational impairment, regulatory scrutiny universally "
            "forces dominant tech firms into proactive behavioral concessions: unbundling services, opening third-party app stores in specific jurisdictions "
            "(Apple in the EU under the DMA), licensing intellectual property (Microsoft's cloud gaming concessions to Ubisoft), and capping predatory pricing algorithms. "
            "For long-term investors, dominant corporations with fortress cash flows have historically overcome antitrust overhangs by pivoting capital into adjacent "
            "unregulated frontiers, particularly generative artificial intelligence and enterprise cloud infrastructure."
        ),
        total_companies_analyzed=len(reports),
        similar_company_events=reports,
    )


def build_operational_defect_archetype() -> DeepResearchTimelineOutput:
    """Operational failures, manufacturing quality defects, and safety groundings."""
    companies_raw = [
        {
            "company_name": "The Boeing Company",
            "stock_ticker": "BA",
            "industry": "Commercial Aerospace Manufacturing",
            "incident_title": "737 MAX 9 Door Plug Blowout & FAA Production Cap",
            "event_timeframe": "January - March 2024",
            "summary": "On January 5, 2024, an Alaska Airlines Boeing 737 MAX 9 suffered an explosive mid-cabin door plug blowout at 16,000 feet over Oregon. The FAA immediately grounded 171 MAX 9 aircraft, halted planned production rate increases, initiated special manufacturing audits, and uncovered systemic quality control lapses at Boeing's Renton facility, culminating in a leadership shakeup and severe cash burn.",
            "similarity_rationale": "The defining contemporary manufacturing quality failure: catastrophic physical hardware failure leading to regulatory groundings and factory caps.",
            "key_parallels": [
                "Catastrophic physical manufacturing defect occurring in active commercial service.",
                "Emergency regulatory grounding by the FAA.",
                "Unprecedented regulatory production cap restricting monthly deliveries.",
                "Severe cash burn ($4B negative free cash flow in Q1) and credit downgrade risk.",
                "Forced resignation of CEO Dave Calhoun and Commercial Airplanes chief Stan Deal.",
            ],
            "key_differences": [
                "Miraculously no fatalities occurred, preventing an immediate criminal re-prosecution of the deferred prosecution agreement.",
                "Disruption was heavily concentrated in the 737 MAX line rather than widebody defense programs.",
            ],
            "total_impact_assessment": "Over $35 billion in lost equity value (-32% peak drawdown), credit rating near junk status, and delayed aircraft deliveries worldwide.",
            "sources": [
                {"title": "FAA Orders Grounding of Certain Boeing 737 MAX 9 Planes", "url": "https://www.faa.gov/newsroom/faa-orders-grounding-certain-boeing-737-max-9-aircraft"},
                {"title": "NTSB Preliminary Report Alaska Airlines Flight 1282", "url": "https://www.ntsb.gov/investigations/Pages/DCA24MA063.aspx"},
            ],
            "timeline": [
                {"date": "2024-01-05", "phase": "Trigger / Mid-Air Blowout", "event": "Alaska Airlines Flight 1282 door plug blows out at 16,000 feet; plane makes emergency landing.", "impact": "Shocking viral imagery of gaping hole in fuselage spreads worldwide."},
                {"date": "2024-01-08", "phase": "Regulatory Grounding & Stock Plunge", "event": "First trading day after incident; FAA issues Emergency Airworthiness Directive grounding 171 aircraft.", "impact": "BA stock plunges -8.0% to $229.00 on massive institutional liquidation."},
                {"date": "2024-01-24", "phase": "FAA Production Freeze", "event": "FAA allows MAX 9 to resume flying after inspections but prohibits Boeing from expanding 737 MAX production rates.", "impact": "Long-term revenue trajectory capped; stock drops another -5.7%."},
                {"date": "2024-02-06", "phase": "NTSB Missing Bolt Finding", "event": "NTSB preliminary investigation confirms door plug was opened at Renton plant and reinstalled missing four critical retention bolts.", "impact": "Proves systemic factory quality control failure; airline customer fury intensifies."},
                {"date": "2024-03-25", "phase": "Executive Removal & Restructuring", "event": "CEO Dave Calhoun announces resignation; Stan Deal exits immediately.", "impact": "Leadership purge completed; stock stabilizes in $180 range as long turnaround commences."},
            ],
        },
        {
            "company_name": "Southwest Airlines Co.",
            "stock_ticker": "LUV",
            "industry": "Commercial Airline Transportation",
            "incident_title": "Holiday Meltdown: Nationwide Scheduling Collapse",
            "event_timeframe": "December 2022 - January 2023",
            "summary": "During the peak December 2022 holiday travel week, winter storm Elliott overwhelmed Southwest Airlines' legacy point-to-point crew scheduling software ('SkySolver'). Southwest collapsed into operational paralysis, canceling over 16,700 flights (70% of its entire schedule) over 10 days, stranding 2 million passengers, and incurring an $800 million financial loss alongside a historic $140 million DOT fine.",
            "similarity_rationale": "Prime example of technical debt and brittle operational software causing a total customer-facing operational shutdown during peak revenue demand.",
            "key_parallels": [
                "Extreme weather triggered cascading failure in legacy IT scheduling systems.",
                "Mass cancellation of over 70% of operations for over a week.",
                "Massive public backlash, stranded passengers, and widespread national news coverage.",
                "Department of Transportation investigation resulting in unprecedented civil fines.",
            ],
            "key_differences": [
                "Operational logistics software failure rather than an aircraft structural design defect.",
                "No physical injuries occurred; crisis was purely customer logistics and reputational.",
            ],
            "total_impact_assessment": "Direct pre-tax financial damage of $800M, $140M regulatory settlement, and long-term activist investor siege by Elliott Management.",
            "sources": [
                {"title": "Southwest Airlines Winter Holiday Operational Disruption", "url": "https://www.transportation.gov/briefing-room/dot-penalizes-southwest-airlines-140-million-2022-holiday-meltdown"},
                {"title": "Southwest Reports $800 Million Net Impact From Holiday Meltdown", "url": "https://www.cnbc.com/2023/01/26/southwest-airlines-luv-q4-2022-earnings.html"},
            ],
            "timeline": [
                {"date": "2022-12-21", "phase": "Precursor / Weather Onset", "event": "Winter storm Elliott sweeps across Midwest; major airlines begin routine weather cancellations.", "impact": "Southwest trades normally at $36.20."},
                {"date": "2022-12-26", "phase": "Trigger / Total Systemic Collapse", "event": "SkySolver crew software crashes under reassignment volume; Southwest cancels 2,900+ flights (70% of schedule).", "impact": "Complete operational breakdown; airports overwhelmed with stranded passengers and mountains of luggage."},
                {"date": "2022-12-28", "phase": "Peak Meltdown & DOT Intervention", "event": "Transportation Secretary Pete Buttigieg publicly demands accountability; stock drops -5.2% over two sessions.", "impact": "Other airlines recover while Southwest remains paralyzed for 4 additional days."},
                {"date": "2022-12-30", "phase": "Manual Reset & Recovery", "event": "Southwest conducts full manual reset of flight schedules and restarts normal operations.", "impact": "Immediate bleeding stops; focus shifts to passenger reimbursements and lost bags."},
                {"date": "2023-01-26", "phase": "Financial Damage Disclosure", "event": "Southwest reports Q4 earnings, revealing $800M pre-tax net loss from the disruption.", "impact": "Management commits $1.3B to IT upgrades; stock remains depressed for over 18 months."},
            ],
        },
        {
            "company_name": "Norfolk Southern Corporation",
            "stock_ticker": "NSC",
            "industry": "Rail Freight Transportation",
            "incident_title": "East Palestine Hazardous Chemical Derailment & Controlled Burn",
            "event_timeframe": "February - March 2023",
            "summary": "On February 3, 2023, a Norfolk Southern freight train carrying toxic vinyl chloride derailed in East Palestine, Ohio, due to an overheated wheel bearing undetected by wayside hotbox detectors. Three days later, emergency officials executed a controlled burn of five tank cars, releasing toxic black smoke across the region, triggering federal civil lawsuits, an EPA emergency order, and over $1 billion in remediation costs.",
            "similarity_rationale": "High-severity environmental and transportation disaster involving equipment failure, toxic release, regulatory intervention, and massive liabilities.",
            "key_parallels": [
                "Mechanical equipment failure (wheel bearing overheating) causing catastrophic derailment.",
                "Severe environmental pollution and public health emergency.",
                "Emergency EPA directive holding railroad fully liable under CERCLA Superfund law.",
                "Department of Justice and state attorney general lawsuits.",
                "Activist proxy contest (Ancora Holdings) seeking to replace management over safety culture.",
            ],
            "key_differences": [
                "Chemical toxic environmental contamination rather than passenger aviation.",
                "Involved complex chemical disposal decisions (controlled venting vs boil-over risk).",
            ],
            "total_impact_assessment": "Direct remediation costs exceeding $1.1 billion, $600M class action settlement, and overhaul of wayside defect detector standards.",
            "sources": [
                {"title": "EPA Orders Norfolk Southern to Conduct All Cleanup Actions", "url": "https://www.epa.gov/newsreleases/epa-orders-norfolk-southern-conduct-all-cleanup-actions-associated-east-palestine-ohio"},
                {"title": "Norfolk Southern Agrees to $600M East Palestine Settlement", "url": "https://www.reuters.com/legal/norfolk-southern-agrees-600-mln-settlement-over-ohio-derailment-2024-04-09/"},
            ],
            "timeline": [
                {"date": "2023-02-02", "phase": "Precursor Baseline", "event": "Norfolk Southern stock closes at $252.37 with strong intermodal volume.", "impact": "Baseline pre-disaster valuation."},
                {"date": "2023-02-03", "phase": "Trigger / Catastrophic Derailment", "event": "Train 32N derails 38 railcars in East Palestine, Ohio; 11 cars carrying hazardous chemicals ignite.", "impact": "Massive fire erupts; mandatory evacuation orders issued within 1-mile radius."},
                {"date": "2023-02-06", "phase": "Controlled Vent and Burn", "event": "Officials execute controlled burn of five vinyl chloride cars, sending toxic phosgene and smoke plume airborne.", "impact": "Environmental disaster intensifies; national media spotlight descends on company."},
                {"date": "2023-02-21", "phase": "EPA Superfund Unilateral Order", "event": "EPA issues legally binding order directing Norfolk Southern to clean all contaminated soil/water.", "impact": "NSC stock drops -3.4% as market prices in uncapped environmental cleanup liabilities."},
                {"date": "2023-03-30", "phase": "DOJ Civil Lawsuit", "event": "US Department of Justice files civil complaint seeking natural resource damages and Clean Water Act penalties.", "impact": "Stock touches multi-month low near $200; total drawdown reaches -20%."},
            ],
        },
        {
            "company_name": "General Motors Company",
            "stock_ticker": "GM",
            "industry": "Automotive Manufacturing",
            "incident_title": "Ignition Switch Recall Crisis & Congressional Hearings",
            "event_timeframe": "February - May 2014",
            "summary": "In February 2014, General Motors issued an initial recall for 778,000 compact vehicles over a defective ignition switch that could inadvertently slip out of the 'run' position, cutting engine power and disabling airbags at highway speeds. The crisis expanded to 2.6 million vehicles, linked to 124 deaths, prompting a congressional probe, a $35M DOT fine, and a $900M DOJ criminal settlement.",
            "similarity_rationale": "The classic automotive quality cover-up: an internal engineering defect ignored for a decade leading to fatal accidents and executive grillings.",
            "key_parallels": [
                "Fatal manufacturing design flaw hidden for years within internal engineering silos.",
                "Rapid snowballing of recall scope from 700k to millions of vehicles.",
                "Newly appointed CEO (Mary Barra) forced to testify before hostile congressional panels.",
                "Substantial regulatory fines ($35M DOT maximum) and eventual $900M criminal settlement.",
            ],
            "key_differences": [
                "Occurred in 2014 automotive manufacturing rather than modern cloud software.",
                "Post-bankruptcy GM shield partially protected the company from pre-2009 commercial claims.",
            ],
            "total_impact_assessment": "Direct recall and compensation fund costs of over $4.1 billion, $900M DOJ deferred prosecution agreement, and profound safety culture overhaul.",
            "sources": [
                {"title": "GM Ignition Switch Recall Timeline", "url": "https://www.reuters.com/article/us-gm-recall-timeline-idUSBREA2H13H20140318/"},
            ],
            "timeline": [
                {"date": "2014-02-12", "phase": "Precursor Baseline", "event": "GM stock trades at $36.00 prior to recall escalation.", "impact": "Pre-recall baseline price."},
                {"date": "2014-02-13", "phase": "Initial Recall Notice", "event": "GM announces recall of 778,000 Chevrolet Cobalt and Pontiac G5 vehicles over ignition switch shutoffs.", "impact": "Initial modest reaction as scope appears confined to older discontinued models."},
                {"date": "2014-03-14", "phase": "Expansion & Federal Investigation", "event": "NHTSA and House Energy and Commerce Committee launch formal investigations into why GM waited 10 years.", "impact": "GM stock drops -8.5% over two weeks as reputational scandal mounts."},
                {"date": "2014-04-01", "phase": "CEO Congressional Testimony", "event": "New CEO Mary Barra testifies before Congress, apologizing for fatal lapses and pledging independent Valukas investigation.", "impact": "Barra's transparent tone stabilizes market sentiment; stock pauses slide near $34."},
                {"date": "2014-05-16", "phase": "DOT Fine & Resolution Framework", "event": "DOT assesses maximum $35M civil penalty; GM establishes independent victim compensation fund led by Ken Feinberg.", "impact": "Legal liabilities quantified; stock resumes upward trajectory toward $37 as fundamental truck sales remain robust."},
            ],
        },
        {
            "company_name": "CrowdStrike Holdings, Inc.",
            "stock_ticker": "CRWD",
            "industry": "Cybersecurity & Cloud Endpoint Security",
            "incident_title": "Falcon Channel File 291 Global Windows Meltdown",
            "event_timeframe": "July - August 2024",
            "summary": "On July 19, 2024, CrowdStrike deployed a routine sensor configuration update (Channel File 291) containing a logic flaw that triggered Blue Screen of Death (BSOD) crashes on 8.5 million Microsoft Windows machines worldwide. The incident grounded 10,000 flights, crippled hospital surgeries, and paralyzed payment terminals in the largest IT outage in human history.",
            "similarity_rationale": "High-severity operational quality failure where an automated software validation lapse triggered a catastrophic global customer operational blackout.",
            "key_parallels": [
                "Flawed configuration file bypassed testing and validation pipelines.",
                "Cascaded instantly to millions of end devices across airlines, hospitals, and banks.",
                "Severe immediate equity crash (-32% over two weeks) and customer litigation threats (Delta $500M claim).",
                "CEO George Kurtz public apology and transparent Root Cause Analysis (RCA) release.",
            ],
            "key_differences": [
                "Software update code bug rather than a malicious external cyberattack or physical hardware failure.",
                "CrowdStrike deployed rapid remediation tooling and retained over 97% gross customer retention.",
            ],
            "total_impact_assessment": "Erased $25 billion in market value, $60M customer commitment package, but swift recovery due to essential platform stickiness.",
            "sources": [
                {"title": "CrowdStrike Preliminary Post-Incident Review", "url": "https://www.crowdstrike.com/blog/preliminary-post-incident-review-content-configuration-update/"},
                {"title": "CrowdStrike Outage Explainer", "url": "https://www.cnbc.com/2024/07/19/crowdstrike-outage-how-a-routine-software-update-crashed-the-world.html"},
            ],
            "timeline": [
                {"date": "2024-07-18", "phase": "Precursor Baseline", "event": "CrowdStrike closes at $343.05 with premium valuation as undisputed endpoint security leader.", "impact": "All-time high territory established."},
                {"date": "2024-07-19", "phase": "Trigger / Global Outage", "event": "Faulty Channel File 291 pushes at 04:09 UTC; 8.5 million Windows devices crash into BSOD loops worldwide.", "impact": "CRWD stock plunges -11.1% on the day; global flight cancellations and hospital outages."},
                {"date": "2024-07-22", "phase": "Wall Street Sell-Off Wave 2", "event": "Analysts downgrade stock on litigation liabilities; Delta Air Lines hires David Boies to seek $500M in damages.", "impact": "Stock slides another -13.5% to $263.91 as institutional funds dump shares."},
                {"date": "2024-07-24", "phase": "Transparent Root Cause Analysis", "event": "CrowdStrike publishes detailed Preliminary Post-Incident Review outlining automated test validation defect.", "impact": "Technical community praises transparency; stock halts steep plunge around $220-$230."},
                {"date": "2024-08-28", "phase": "Q2 Earnings & Customer Retention", "event": "CrowdStrike reports Q2 earnings showing gross retention steady at 97% despite outage; trims full-year guidance modestly.", "impact": "Relief rally commences; stock rebounds +15% over the following month."},
            ],
        },
    ]

    reports = []
    for c in companies_raw:
        tl = [TimelineMilestone(**m) for m in c["timeline"]]
        enriched_tl, metrics = enrich_stock_timeline(c["stock_ticker"], tl)
        sources = [SourceCitation(**s) for s in c["sources"]]
        rep = CompanyIncidentReport(
            company_name=c["company_name"],
            stock_ticker=c["stock_ticker"],
            industry=c["industry"],
            incident_title=c["incident_title"],
            event_timeframe=c["event_timeframe"],
            summary=c["summary"],
            similarity_rationale=c["similarity_rationale"],
            key_parallels=c["key_parallels"],
            key_differences=c["key_differences"],
            timeline=enriched_tl,
            stock_metrics=metrics,
            total_impact_assessment=c["total_impact_assessment"],
            sources=sources,
        )
        reports.append(rep)

    return DeepResearchTimelineOutput(
        query_prompt="A major manufacturer, transportation provider, or platform suffers catastrophic operational failure, safety quality defect, or regulatory grounding",
        generated_at=datetime.now(timezone.utc).isoformat(),
        incident_category="Operational & Safety Catastrophes: Manufacturing Defects, System Failures & Regulatory Caps",
        core_themes=[
            "Critical hardware defect or software validation lapse causing direct service outage",
            "Immediate intervention by federal regulatory agencies (FAA, DOT, EPA, NHTSA)",
            "Mandatory emergency groundings, operational production freezes, or unilateral cleanup orders",
            "Severe immediate equity drawdown driven by quantifiable litigation and remediation liabilities",
            "Comprehensive executive leadership purges and multi-year safety culture reorganizations",
        ],
        executive_synthesis=(
            "**Causal Mechanisms & Systemic Quality Breakdown** — Operational and safety catastrophes represent the sudden crystallization of "
            "accumulated organizational fragility. Across Boeing's missing door plug bolts, Southwest's legacy scheduling software collapse, "
            "Norfolk Southern's unmonitored overheated rail bearing, General Motors' unaddressed ignition switch defect, and CrowdStrike's flawed sensor "
            "configuration update, each disaster was preceded by internal warning signs that were dismissed or deprioritized in favor of short-term "
            "operational throughput. When the failure finally manifested in physical or digital space, it instantly compromised the company's core license to operate.\n\n"
            "**Market Reaction Velocity & Liability Quantification** — Equity markets punish operational quality failures with immediate severity, "
            "reflecting the acute uncertainty of regulatory intervention. Boeing lost over $35 billion in market value (-32% peak drawdown) because "
            "the FAA took the unprecedented step of capping 737 MAX production rates, directly impairing forward cash flow projections. Similarly, "
            "CrowdStrike shed 35% of its market capitalization over two weeks amidst threats of multi-hundred-million-dollar lawsuits from enterprise clients "
            "like Delta Air Lines. In contrast to ambiguous strategic missteps, operational catastrophes trigger heavy short selling because regulatory fines, "
            "customer compensation packages, and legal settlements represent quantifiable cash drains.\n\n"
            "**Turnaround Pathways & Cultural Remediation** — Overcoming an operational catastrophe demands three consistent institutional milestones: "
            "1) Absolute transparency regarding the root cause (demonstrated by CrowdStrike's rapid technical post-incident review and GM's independent "
            "Valukas report), 2) Removal of accountable leadership to restore credibility with regulators (Boeing's Calhoun/Deal departure and Norfolk Southern's "
            "board overhaul), and 3) Multi-billion dollar capital investments in quality assurance pipelines and redundant engineering. While market recovery "
            "can take 12 to 24 months, companies that possess mission-critical moats and execute rigorous safety overhauls historically regain their prior valuation peaks."
        ),
        total_companies_analyzed=len(reports),
        similar_company_events=reports,
    )


def build_earnings_restructuring_archetype() -> DeepResearchTimelineOutput:
    """Earnings guidance shock, demand cliff, margin collapse, and restructuring."""
    companies_raw = [
        {
            "company_name": "Intel Corporation",
            "stock_ticker": "INTC",
            "industry": "Semiconductors & Foundry Services",
            "incident_title": "Q2 Earnings Collapse, 15% Layoffs & Dividend Suspension",
            "event_timeframe": "August 2024",
            "summary": "On August 1, 2024, Intel delivered one of the most disastrous earnings reports in semiconductor history: reporting a $1.6B net loss, cutting fiscal Q3 guidance over $3B below consensus, announcing the elimination of 15,000+ jobs (15% of workforce), and suspending its 32-year dividend. The next day, Intel shares crashed -26.0% in its single worst trading day since 1974.",
            "similarity_rationale": "The archetypal mega-cap earnings warning: simultaneous guidance collapse, structural restructuring, and dividend elimination.",
            "key_parallels": [
                "Massive quarterly earnings and forward guidance miss.",
                "Aggressive cost-cutting package including 15% global workforce reduction.",
                "Suspension of long-standing dividend to preserve capital.",
                "Historical single-day equity collapse (-26%) erasing $32B in market cap.",
                "Catalyzed subsequent board rebellion and CEO removal 4 months later.",
            ],
            "key_differences": [
                "Driven by multi-billion capital expenditure on manufacturing fabs ahead of revenue realization rather than a sudden demand fraud.",
            ],
            "total_impact_assessment": "Over $35B in market cap eliminated in 24 hours, permanent damage to executive credibility, and forced postponement of international fab projects.",
            "sources": [
                {"title": "Intel Shares Plunge 26% in Worst Day in 50 Years", "url": "https://www.wsj.com/tech/intel-intc-q2-earnings-report-2024-e1d51f22"},
                {"title": "SEC 8-K Intel Q2 Financial Results and Restructuring", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/50863/000005086324000078/intc-20240801.htm"},
            ],
            "timeline": [
                {"date": "2024-07-31", "phase": "Precursor Baseline", "event": "Intel stock trades at $30.74 ahead of earnings announcement.", "impact": "Baseline price established."},
                {"date": "2024-08-01", "phase": "Trigger / Catastrophic Earnings Release", "event": "Intel reports $1.6B Q2 loss, slashes Q3 guidance, announces 15,000 layoffs and suspends dividend.", "impact": "After-hours trading plunges -19%; institutional downgrades flood Wall Street."},
                {"date": "2024-08-02", "phase": "Historical Single-Day Crash", "event": "INTC stock closes down -26.0% at $21.48 with 300 million shares changing hands.", "impact": "Worst trading session in 50 years; market capitalization falls below book value."},
                {"date": "2024-08-19", "phase": "Board Discord & Resignation", "event": "Semiconductor veteran Lip-Bu Tan abruptly resigns from Intel board over disagreements on turnaround pace.", "impact": "Stock slides further to multi-year low of $18.84 (-38% from pre-earnings)."},
                {"date": "2024-09-16", "phase": "Restructuring Acceleration", "event": "Intel announces separation of Foundry business into independent subsidiary and pauses European expansion.", "impact": "Stock rallies +6.4% on decisive cost preservation, stabilizing in low $20s."},
            ],
        },
        {
            "company_name": "Meta Platforms, Inc.",
            "stock_ticker": "META",
            "industry": "Digital Advertising & Social Media",
            "incident_title": "First-Ever User Decline & $232 Billion Market Cap Wipeout",
            "event_timeframe": "February - November 2022",
            "summary": "On February 2, 2022, Meta reported its first-ever quarterly decline in Facebook daily active users and revealed that Apple's iOS privacy changes (ATT) would wipe out $10 billion in advertising revenue. The following day, Meta shares plummeted -26.4%, erasing $232 billion in market capitalization—the largest single-day market cap destruction in US corporate history.",
            "similarity_rationale": "Historic precedent for an advertising giant experiencing structural disruption, massive market cap loss, and subsequent 'Year of Efficiency' turnaround.",
            "key_parallels": [
                "Unexpected decline in core user engagement metrics and severe guidance cut.",
                "Record single-day equity loss ($232 billion).",
                "Massive post-crisis restructuring (slashing 21,000 roles across 2022-2023).",
                "Spectacular long-term stock rebound (+300%) once operational efficiency was prioritized.",
            ],
            "key_differences": [
                "Catalyzed by external platform privacy policy (Apple iOS) and competing app surge (TikTok) rather than hardware defects.",
            ],
            "total_impact_assessment": "Immediate $232B market cap destruction, followed by aggressive cost restructuring that set the benchmark for Big Tech efficiency.",
            "sources": [
                {"title": "Meta Plunges 26% on Disappointing Earnings and Forecast", "url": "https://www.cnbc.com/2022/02/02/meta-shares-plunge-after-earnings-miss.html"},
                {"title": "Mark Zuckerberg Announces 11,000 Layoffs", "url": "https://about.fb.com/news/2022/11/mark-zuckerberg-layoff-announcement/"},
            ],
            "timeline": [
                {"date": "2022-02-01", "phase": "Precursor Baseline", "event": "Meta stock closes at $319.00 before earnings release.", "impact": "Pre-crash valuation near $850B market cap."},
                {"date": "2022-02-02", "phase": "Trigger / Earnings Miss", "event": "Meta reports Q4 earnings: Facebook DAUs decline by 500k, guides Q1 revenue far below consensus, cites $10B Apple iOS hit.", "impact": "After-hours crash begins."},
                {"date": "2022-02-03", "phase": "Record Single-Day Crash", "event": "META shares plunge -26.4% to $237.76; $232 billion in market cap erased in single trading day.", "impact": "Largest single-day market capitalization loss in Wall Street history."},
                {"date": "2022-11-09", "phase": "Mass Headcount Reduction", "event": "Zuckerberg takes accountability and announces first-ever mass layoff of 11,000 employees (13% of staff).", "impact": "Stock begins violent upward reversal as market welcomes capital discipline."},
                {"date": "2023-03-14", "phase": "The 'Year of Efficiency'", "event": "Meta announces an additional 10,000 layoffs and cancels non-priority projects.", "impact": "Stock initiates historic multi-quarter rally, ultimately surpassing $500."},
            ],
        },
        {
            "company_name": "Snap Inc.",
            "stock_ticker": "SNAP",
            "industry": "Digital Media & Ad Tech",
            "incident_title": "Emergency SEC 8-K Guidance Warning & 43% Single-Day Crash",
            "event_timeframe": "May 2022",
            "summary": "On May 23, 2022, Snap CEO Evan Spiegel filed an unscheduled emergency SEC Form 8-K warning that the macroeconomic environment had deteriorated faster than anticipated and Snap would miss its own revenue and EBITDA guidance issued just a month prior. The next morning, Snap stock cratered -43.1% in a single day, dragging down the entire digital advertising and tech sector.",
            "similarity_rationale": "Extreme intraday repricing triggered by an unscheduled intra-quarter guidance withdrawal and sudden ad market freeze.",
            "key_parallels": [
                "Unscheduled intra-quarter guidance warning via surprise SEC 8-K filing.",
                "Devastating single-day collapse (-43%) reflecting total loss of visibility.",
                "Drag-along effect crashing competitor stocks across the digital ad ecosystem.",
                "Subsequent restructuring eliminating 20% of workforce and shutting hardware units.",
            ],
            "key_differences": [
                "Smaller mid-cap digital ad company with higher beta than diversified mega-caps.",
            ],
            "total_impact_assessment": "Erased $16B in market value in 24 hours, wiped out $100B+ across advertising peers, forced abandonment of drone and Web3 projects.",
            "sources": [
                {"title": "Snap Plummets 43% After Warning It Will Miss Earnings Targets", "url": "https://www.cnbc.com/2022/05/24/snap-stock-plummets-after-earnings-warning.html"},
                {"title": "SEC 8-K Snap Intra-Quarter Guidance Update", "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1564408/000156440822000049/snap-20220523.htm"},
            ],
            "timeline": [
                {"date": "2022-05-20", "phase": "Precursor Baseline", "event": "Snap stock closes at $22.47 after modest tech rally.", "impact": "Pre-warning baseline valuation."},
                {"date": "2022-05-23", "phase": "Trigger / Emergency 8-K Warning", "event": "Snap files surprise SEC 8-K post-market warning it will miss Q2 guidance due to rapid macroeconomic degradation.", "impact": "Stock plunges -30% in after-hours trading."},
                {"date": "2022-05-24", "phase": "The -43% Bloodbath", "event": "Snap shares open down and close -43.1% at $12.79 on 250M shares traded.", "impact": "One of the steepest crashes for a tech stock; drags down Meta (-7%), Google (-5%), and Pinterest (-24%)."},
                {"date": "2022-08-31", "phase": "Strategic Restructuring", "event": "Snap announces 20% headcount reduction, cancels Pixy flying drone, and refocuses on direct response ads.", "impact": "Cash burn stabilized; stock forms a base around $10."},
                {"date": "2023-02-01", "phase": "Operational Re-architecture", "event": "Snap reports progress in machine learning ad-ranking models to adapt to privacy changes.", "impact": "Volatility stabilizes; company transitions to disciplined growth model."},
            ],
        },
        {
            "company_name": "NVIDIA Corporation",
            "stock_ticker": "NVDA",
            "industry": "Semiconductors & GPU Computing",
            "incident_title": "Gaming Demand Collapse & $1.3B Inventory Write-Down",
            "event_timeframe": "August - October 2022",
            "summary": "On August 8, 2022, Nvidia issued a preliminary Q2 revenue warning of $6.70 billion versus $8.10 billion guidance due to a sudden demand cliff in gaming GPUs as cryptocurrency mining crashed. When official earnings were released, Nvidia reported a 33% sequential decline in gaming revenue and booked $1.32 billion in inventory write-downs, driving the stock down over 55% from its highs before the generative AI boom began.",
            "similarity_rationale": "Semiconductor demand cyclicality shock: sudden end-market collapse leading to severe inventory write-offs before a structural secular breakout.",
            "key_parallels": [
                "Preliminary pre-announcement of severe revenue shortfall.",
                "Massive inventory write-downs and margin compression.",
                "Cyclical bottoming process accompanied by widespread Wall Street downgrades.",
                "Subsequent historic pivot into enterprise generative AI (ChatGPT launched Nov 2022).",
            ],
            "key_differences": [
                "Nvidia had the nascent AI datacenter architecture ready to take off just as gaming collapsed.",
                "Did not require mass layoffs to restore profitability.",
            ],
            "total_impact_assessment": "Pushed stock to cyclical trough of $112, followed by a historic 1,000%+ surge over the next 24 months to become the world's most valuable company.",
            "sources": [
                {"title": "Nvidia Reports Preliminary Second Quarter Fiscal 2023 Revenue", "url": "https://nvidianews.nvidia.com/news/nvidia-reports-preliminary-second-quarter-fiscal-2023-financial-results"},
            ],
            "timeline": [
                {"date": "2022-08-05", "phase": "Precursor Baseline", "event": "Nvidia trades at $189.89 with investors anticipating modest gaming moderation.", "impact": "Baseline price before warning."},
                {"date": "2022-08-08", "phase": "Trigger / Preliminary Revenue Warning", "event": "Nvidia issues pre-announcement slashing Q2 revenue guidance by $1.4B; gaming down 33% sequentially.", "impact": "NVDA stock drops -6.3% as crypto mining GPU glut impacts channels."},
                {"date": "2022-08-24", "phase": "Official Earnings & Write-Downs", "event": "Official Q2 report confirms $1.32B inventory charge; gross margin collapses from 65% to 43.5%.", "impact": "Stock slides another -4.6% to $172 as analysts lower 2023 EPS estimates."},
                {"date": "2022-10-14", "phase": "Cyclical Trough", "event": "US export controls on high-end chips to China announced; NVDA hits cyclical bottom of $112.27.", "impact": "Maximum pessimism priced in; stock down 66% from prior peak."},
                {"date": "2022-11-30", "phase": "Generative AI Catalyst", "event": "OpenAI releases ChatGPT to the public, igniting unprecedented demand for Nvidia H100 datacenter GPUs.", "impact": "The greatest tech rally in history commences; NVDA begins ascent to $3+ trillion valuation."},
            ],
        },
        {
            "company_name": "Tesla, Inc.",
            "stock_ticker": "TSLA",
            "industry": "Electric Vehicles & Clean Energy",
            "incident_title": "Growth Warning, Margin Squeeze & 10% Global Workforce Cut",
            "event_timeframe": "January - April 2024",
            "summary": "In January 2024, Tesla warned that its vehicle volume growth rate in 2024 'may be notably lower' as it worked between two major growth waves. Over the subsequent quarter, aggressive price cuts in China compressed automotive gross margins, culminating in an April 15 internal memo from Elon Musk cutting more than 10% of Tesla's global workforce (>14,000 employees) and the departure of key battery executive Drew Baglino.",
            "similarity_rationale": "High-growth tech darling facing demand deceleration, margin erosion, executive departures, and aggressive restructuring.",
            "key_parallels": [
                "Explicit forward guidance downgrade warning of slower delivery growth.",
                "Gross margin compression from price-cutting wars.",
                "Mass layoffs cutting 10%+ of global headcount.",
                "Abrupt departure of core senior engineering executives.",
            ],
            "key_differences": [
                "Turnaround narrative quickly shifted to autonomous robotaxis and humanoid robotics rather than traditional manufacturing metrics.",
            ],
            "total_impact_assessment": "Stock drawdown of over 40% from 2023 highs, elimination of 14,000 jobs, followed by an autonomous AI-driven multiple expansion.",
            "sources": [
                {"title": "Tesla Shares Plunge 12% After Earnings Warning of Slower Growth", "url": "https://www.cnbc.com/2024/01/25/tesla-tsla-earnings-q4-2023.html"},
                {"title": "Tesla to Lay Off More Than 10% of Global Workforce", "url": "https://www.reuters.com/business/autos-transportation/tesla-lay-off-more-than-10-its-workforce-electrek-reports-2024-04-15/"},
            ],
            "timeline": [
                {"date": "2024-01-24", "phase": "Precursor / Earnings Release", "event": "Tesla reports Q4 earnings: operating margin drops to 8.2%; warns 2024 volume growth may be notably lower.", "impact": "Investors shocked by absence of specific annual vehicle delivery guidance."},
                {"date": "2024-01-25", "phase": "Trigger / The -12% Plunge", "event": "TSLA shares plunge -12.1% to $182.63, losing $80 billion in market value in one session.", "impact": "Tech mega-cap sell-off commences; Wall Street slashes price targets."},
                {"date": "2024-04-15", "phase": "Mass Headcount Layoff Memo", "event": "Musk sends company-wide memo cutting >10% of staff (>14,000 workers); VP Drew Baglino resigns.", "impact": "TSLA drops -5.6% to $161.48 as market worries about product roadmap delays."},
                {"date": "2024-04-22", "phase": "Cyclical Low", "event": "Tesla cuts prices across global lineup; stock touches multi-year low of $142.05.", "impact": "Drawdown reaches -44% from December highs; sentiment at extreme pessimism."},
                {"date": "2024-04-23", "phase": "Pivot to Autonomous AI", "event": "Tesla reports Q1 earnings: misses numbers but announces accelerated timeline for affordable models and Robotaxi.", "impact": "Stock rallies +12% after hours, initiating powerful recovery back above $250."},
            ],
        },
    ]

    reports = []
    for c in companies_raw:
        tl = [TimelineMilestone(**m) for m in c["timeline"]]
        enriched_tl, metrics = enrich_stock_timeline(c["stock_ticker"], tl)
        sources = [SourceCitation(**s) for s in c["sources"]]
        rep = CompanyIncidentReport(
            company_name=c["company_name"],
            stock_ticker=c["stock_ticker"],
            industry=c["industry"],
            incident_title=c["incident_title"],
            event_timeframe=c["event_timeframe"],
            summary=c["summary"],
            similarity_rationale=c["similarity_rationale"],
            key_parallels=c["key_parallels"],
            key_differences=c["key_differences"],
            timeline=enriched_tl,
            stock_metrics=metrics,
            total_impact_assessment=c["total_impact_assessment"],
            sources=sources,
        )
        reports.append(rep)

    return DeepResearchTimelineOutput(
        query_prompt="A market-leading corporation reports unexpected revenue collapse, sharp margin compression, or slashes forward guidance triggering aggressive restructuring",
        generated_at=datetime.now(timezone.utc).isoformat(),
        incident_category="Earnings & Financial Shocks: Guidance Cliffs, Margin Compression & Mass Restructuring",
        core_themes=[
            "Severe forward revenue guidance cuts and unexpected quarterly losses",
            "Catastrophic single-day equity drawdowns (-12% to -43%)",
            "Emergency corporate restructuring, mass layoffs (10% to 20% of staff), and dividend eliminations",
            "Loss of visibility into core end-market demand (advertising, semiconductor cycles, EV adoption)",
            "Strategic 'Year of Efficiency' discipline acting as the foundation for long-term equity recovery",
        ],
        executive_synthesis=(
            "**Anatomy of an Earnings Guidance Cliff** — An earnings shock differs fundamentally from operational accidents or regulatory probes "
            "because it directly shatters Wall Street's financial modeling assumptions. Across Intel's foundry capex cash drain, Meta's iOS advertising "
            "disruption, Snap's intra-quarter ad freeze, Nvidia's crypto mining hangover, and Tesla's automotive price war, each crisis occurred when "
            "management's previous forward guidance collided with sudden demand erosion. The resulting revisions forced sell-side analysts into "
            "synchronized downward target revisions, producing violent single-day crashes ranging from -12% to an unprecedented -43%.\n\n"
            "**Market Reaction Velocity & Multiple Compression** — The initial trading sessions following guidance warnings are marked by indiscriminate "
            "institutional liquidation. When Snap filed its unscheduled 8-K in May 2022, it triggered a -43% single-session bloodbath that wiped out "
            "$100 billion across the entire digital advertising complex. Similarly, Meta's $232 billion single-day wipeout remains the largest in history. "
            "However, financial data reveals a crucial market anomaly: the day of maximum negative disclosure often marks the initiation of the cyclical bottom, "
            "provided management demonstrates credible operational discipline.\n\n"
            "**Restructuring Discipline & The 'Kitchen Sink' Reversal** — The playbook for recovering from an earnings guidance collapse requires decisive "
            "'kitchen-sinking': slashing unviable capital projects, cutting workforce overhead by 10% to 20% (demonstrated by Meta's 21,000 layoffs, "
            "Intel's 15,000 headcount cuts, and Tesla's 14,000 workforce reduction), and re-aligning capital toward high-margin core competencies. "
            "When Mark Zuckerberg initiated Meta's 'Year of Efficiency', the stock rallied over 300% over the next 18 months. Similarly, Nvidia's "
            "2022 inventory write-off cleaned channel inventory just in time to capture the enterprise generative AI revolution. For investors, "
            "an earnings collapse separates companies with temporary cyclical headwinds and structural moats from those with obsolete business models."
        ),
        total_companies_analyzed=len(reports),
        similar_company_events=reports,
    )


def main():
    print("Generating verified archetypal crisis timelines with real yfinance stock data...")

    archetypes = [
        ("leadership_ceo_ouster.json", build_leadership_archetype),
        ("bank_run_liquidity.json", build_banking_archetype),
        ("antitrust_regulatory.json", build_antitrust_archetype),
        ("operational_defect_safety.json", build_operational_defect_archetype),
        ("earnings_guidance_restructuring.json", build_earnings_restructuring_archetype),
    ]

    for filename, builder in archetypes:
        out_path = OUTPUT_DIR / filename
        print(f"Building {filename}...")
        try:
            data = builder()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {filename} ({data.total_companies_analyzed} companies, {len(data.similar_company_events)} reports)")
        except Exception as e:
            print(f"✗ Failed {filename}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    # Also ensure cybersecurity archetype is present from similar_news_timeline.json
    cyber_src = REPO_ROOT / "backend" / "data" / "similar_news_timeline.json"
    cyber_dest = OUTPUT_DIR / "cybersecurity_outage.json"
    if cyber_src.exists() and not cyber_dest.exists():
        import shutil
        shutil.copyfile(cyber_src, cyber_dest)
        print(f"✓ Copied cybersecurity_outage.json from similar_news_timeline.json")

    print("\nArchetype generation complete!")


if __name__ == "__main__":
    main()
