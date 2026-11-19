import type { DeepResearchTimelineOutput } from "@/types"

export const DEFAULT_TIMELINE_DATA: DeepResearchTimelineOutput = {
  "query_prompt": "A Fortune 500 board abruptly forces out the CEO amidst operational underperformance, manufacturing delays, or strategic misalignment",
  "generated_at": "2026-11-19T13:33:57.770114+00:00",
  "incident_category": "Corporate Governance Shakeup: Executive Ousters & Leadership Turmoil",
  "core_themes": [
    "Abrupt board removal of sitting chief executive",
    "Operational underperformance or multi-quarter margin degradation",
    "Interim leadership structure vs immediate rockstar succession",
    "Initial relief rallies vs reality check on capital turnaround complexity",
    "Activist shareholder intervention and executive committee restructuring"
  ],
  "executive_synthesis": "**Cross-Company Mechanisms & Governance Failure Modes** \u2014 Executive departures in major corporations rarely happen in isolation; they represent the culmination of accumulated strategic divergence between the executive suite and the board of directors. Across Intel, Starbucks, Disney, Boeing, and OpenAI/Microsoft, each crisis revealed a breakdown in capital allocation governance where management persistently fell short of benchmark expectations (Intel's multi-billion foundry losses, Starbucks' declining store traffic, Disney's streaming cash burn, Boeing's factory floor bolt lapses). In every case, boards waited until an acute catalyst\u2014such as activist filings, disastrous earnings prints, or public safety blowouts\u2014forced their hand into abrupt dismissals.\n\n**Market Reaction Velocity & Valuation Dispersion** \u2014 Equity markets differentiate sharply between leadership changes accompanied by a proven immediate successor versus an ambiguous interim vacuum. Starbucks achieved the single largest one-day market capitalization jump in its history (+24.5%, +$21.4B) because the board simultaneously unveiled Chipotle's celebrated leader Brian Niccol with complete operational autonomy. Disney similarly experienced an instant +6.3% rally upon Bob Iger's weekend return. In contrast, Intel's dismissal of Pat Gelsinger without a permanent successor sparked only a transient intraday pop before declining, as investors realized the structural foundry turnaround was prolonged and unaddressed. Boeing's multi-month lame-duck departure of Dave Calhoun saw persistent equity drift until outside engineer Kelly Ortberg took command.\n\n**Post-Ouster Strategic Execution & Turnaround Trajectories** \u2014 In the aftermath of sudden CEO removals, corporations universally engage in 'kitchen sinking'\u2014suspending multi-year guidance, writing down legacy goodwill, and announcing mass workforce reductions (Intel's 15% layoff, Disney's 7,000 headcount cut, Starbucks' fiscal 2025 guidance withdrawal). For long-term investors, the pivotal signal is whether the board empowers new leadership to make structural capital realignments rather than cosmetic public relations shifts.",
  "total_companies_analyzed": 5,
  "similar_company_events": [
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
        "Initial modest stock rally on the news followed by reality check on turnaround difficulty."
      ],
      "key_differences": [
        "Turnaround challenge was rooted in decades-long semiconductor manufacturing lags rather than sudden accounting fraud.",
        "Intel had received billions in CHIPS Act subsidies creating heavy governmental oversight."
      ],
      "timeline": [
        {
          "date": "2024-11-29",
          "phase": "Precursor / Baseline",
          "event": "Final trading day prior to weekend board meeting; Intel stock closes quietly at $24.05.",
          "impact": "Baseline stock price established ahead of unscheduled leadership change.",
          "stock_price": 24.05,
          "stock_change_from_baseline_pct": 0.0,
          "trading_volume": 36616800
        },
        {
          "date": "2024-12-01",
          "phase": "Trigger / Board Ultimatum",
          "event": "Intel board of directors confronts CEO Pat Gelsinger with retirement ultimatum; Gelsinger resigns.",
          "impact": "Sudden removal of CEO who led ambitious five-nodes-in-four-years turnaround plan.",
          "stock_price": 23.93,
          "stock_change_from_baseline_pct": -0.5,
          "trading_volume": 150497900
        },
        {
          "date": "2024-12-02",
          "phase": "Public Disclosure & Market Opening",
          "event": "Intel officially announces Gelsinger's retirement; David Zinsner and Michelle Johnston Holthaus named interim co-CEOs.",
          "impact": "Stock opens higher by +4.5% in pre-market, closing at $24.87 (-0.5% from previous close after intraday swings).",
          "stock_price": 23.93,
          "stock_change_from_baseline_pct": -0.5,
          "trading_volume": 150497900
        },
        {
          "date": "2024-12-05",
          "phase": "Strategic Review & Speculation",
          "event": "Wall Street analysts publish notes debating potential foundry spin-off or private equity buyout of Altera.",
          "impact": "Intel stock trades sideways as market recognizes leadership vacuum delays structural decisions.",
          "stock_price": 20.8,
          "stock_change_from_baseline_pct": -13.51,
          "trading_volume": 167993500
        },
        {
          "date": "2024-12-16",
          "phase": "Interim Governance Update",
          "event": "Interim co-CEOs reaffirm commitment to 18A process node schedule and cost-reduction targets.",
          "impact": "Stock stabilizes around $22.50 with trading volume normalizing.",
          "stock_price": 20.83,
          "stock_change_from_baseline_pct": -13.39,
          "trading_volume": 73832900
        }
      ],
      "stock_metrics": {
        "ticker": "INTC",
        "baseline_date": "2024-11-29",
        "baseline_price": 24.05,
        "trough_date": "2024-12-19",
        "trough_price": 19.06,
        "max_drawdown_pct": -20.75,
        "daily_series": [
          {
            "date": "2024-11-04",
            "close": 22.52
          },
          {
            "date": "2024-11-05",
            "close": 23.32
          },
          {
            "date": "2024-11-06",
            "close": 25.05
          },
          {
            "date": "2024-11-07",
            "close": 26.23
          },
          {
            "date": "2024-11-08",
            "close": 26.2
          },
          {
            "date": "2024-11-11",
            "close": 25.05
          },
          {
            "date": "2024-11-12",
            "close": 24.16
          },
          {
            "date": "2024-11-13",
            "close": 24.92
          },
          {
            "date": "2024-11-14",
            "close": 25.03
          },
          {
            "date": "2024-11-15",
            "close": 24.35
          },
          {
            "date": "2024-11-18",
            "close": 24.84
          },
          {
            "date": "2024-11-19",
            "close": 24.2
          },
          {
            "date": "2024-11-20",
            "close": 24.01
          },
          {
            "date": "2024-11-21",
            "close": 24.44
          },
          {
            "date": "2024-11-22",
            "close": 24.5
          },
          {
            "date": "2024-11-25",
            "close": 24.87
          },
          {
            "date": "2024-11-26",
            "close": 24.05
          },
          {
            "date": "2024-11-27",
            "close": 23.65
          },
          {
            "date": "2024-11-29",
            "close": 24.05
          },
          {
            "date": "2024-12-02",
            "close": 23.93
          },
          {
            "date": "2024-12-03",
            "close": 22.47
          },
          {
            "date": "2024-12-04",
            "close": 21.96
          },
          {
            "date": "2024-12-05",
            "close": 20.8
          },
          {
            "date": "2024-12-06",
            "close": 20.92
          },
          {
            "date": "2024-12-09",
            "close": 20.81
          },
          {
            "date": "2024-12-10",
            "close": 20.16
          },
          {
            "date": "2024-12-11",
            "close": 20.12
          },
          {
            "date": "2024-12-12",
            "close": 20.78
          },
          {
            "date": "2024-12-13",
            "close": 20.34
          },
          {
            "date": "2024-12-16",
            "close": 20.83
          },
          {
            "date": "2024-12-17",
            "close": 20.44
          },
          {
            "date": "2024-12-18",
            "close": 19.3
          },
          {
            "date": "2024-12-19",
            "close": 19.06
          },
          {
            "date": "2024-12-20",
            "close": 19.52
          },
          {
            "date": "2024-12-23",
            "close": 20.2
          },
          {
            "date": "2024-12-24",
            "close": 20.4
          },
          {
            "date": "2024-12-26",
            "close": 20.44
          },
          {
            "date": "2024-12-27",
            "close": 20.3
          },
          {
            "date": "2024-12-30",
            "close": 19.82
          },
          {
            "date": "2024-12-31",
            "close": 20.05
          },
          {
            "date": "2025-01-02",
            "close": 20.22
          },
          {
            "date": "2025-01-03",
            "close": 20.56
          },
          {
            "date": "2025-01-06",
            "close": 19.87
          },
          {
            "date": "2025-01-07",
            "close": 20.01
          },
          {
            "date": "2025-01-08",
            "close": 19.88
          },
          {
            "date": "2025-01-10",
            "close": 19.15
          },
          {
            "date": "2025-01-13",
            "close": 19.2
          },
          {
            "date": "2025-01-14",
            "close": 19.2
          },
          {
            "date": "2025-01-15",
            "close": 19.72
          },
          {
            "date": "2025-01-16",
            "close": 19.67
          },
          {
            "date": "2025-01-17",
            "close": 21.49
          },
          {
            "date": "2025-01-21",
            "close": 21.77
          },
          {
            "date": "2025-01-22",
            "close": 21.86
          },
          {
            "date": "2025-01-23",
            "close": 21.57
          },
          {
            "date": "2025-01-24",
            "close": 20.83
          },
          {
            "date": "2025-01-27",
            "close": 20.29
          },
          {
            "date": "2025-01-28",
            "close": 19.8
          },
          {
            "date": "2025-01-29",
            "close": 19.75
          }
        ]
      },
      "total_impact_assessment": "Immediate leadership vacuum, elevated speculation around splitting foundry and product design units, and ongoing strategic reassessment.",
      "sources": [
        {
          "title": "Intel CEO Pat Gelsinger Steps Down",
          "url": "https://www.wsj.com/tech/intel-ceo-pat-gelsinger-steps-down-9fa17b0d"
        },
        {
          "title": "SEC 8-K Intel Leadership Transition",
          "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/50863/000005086324000099/intc-20241201.htm"
        }
      ]
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
        "Dramatic positive market re-rating reflecting restored investor confidence."
      ],
      "key_differences": [
        "Starbucks had a ready-made successor instantly in place rather than an interim period.",
        "Stock rallied +24.5% immediately rather than suffering panic selling."
      ],
      "timeline": [
        {
          "date": "2024-08-12",
          "phase": "Precursor / Baseline",
          "event": "Starbucks stock closes at $77.01 amid persistent rumors of activist investor pressure.",
          "impact": "Stock down 20% year-to-date; investor sentiment depressed.",
          "stock_price": 72.38,
          "stock_change_from_baseline_pct": 0.0,
          "trading_volume": 13123000
        },
        {
          "date": "2024-08-13",
          "phase": "Trigger & Massive Announcement",
          "event": "Starbucks announces immediate departure of Laxman Narasimhan and hiring of Brian Niccol.",
          "impact": "SBUX shares soar +24.5% to $95.90, adding $21.4B in market value in a single trading session.",
          "stock_price": 90.11,
          "stock_change_from_baseline_pct": 24.5,
          "trading_volume": 157215500
        },
        {
          "date": "2024-08-15",
          "phase": "Activist Consensus",
          "event": "Elliott Investment Management issues statement endorsing Niccol's appointment as transformative.",
          "impact": "Activist proxy battle threat effectively eliminated; institutional inflows accelerate.",
          "stock_price": 89.15,
          "stock_change_from_baseline_pct": 23.17,
          "trading_volume": 21109800
        },
        {
          "date": "2024-09-09",
          "phase": "Executive Onboarding",
          "event": "Brian Niccol officially assumes role and publishes open letter 'Back to Starbucks' pledging simpler cafe workflows.",
          "impact": "Stock trades solidly near $98.00 as market awaits operational changes.",
          "stock_price": 87.17,
          "stock_change_from_baseline_pct": 20.44,
          "trading_volume": 10089700
        },
        {
          "date": "2024-10-22",
          "phase": "Guidance Suspension / Kitchen Sink",
          "event": "Starbucks prelim Q4 results miss expectations; Niccol suspends fiscal 2025 financial guidance.",
          "impact": "Stock dips briefly by -2.5% then recovers, as market accepts guidance reset under new management.",
          "stock_price": 91.52,
          "stock_change_from_baseline_pct": 26.45,
          "trading_volume": 6670900
        }
      ],
      "stock_metrics": {
        "ticker": "SBUX",
        "baseline_date": "2024-08-12",
        "baseline_price": 72.38,
        "trough_date": "2024-07-25",
        "trough_price": 68.89,
        "max_drawdown_pct": -4.82,
        "daily_series": [
          {
            "date": "2024-07-18",
            "close": 69.71
          },
          {
            "date": "2024-07-19",
            "close": 74.48
          },
          {
            "date": "2024-07-22",
            "close": 71.93
          },
          {
            "date": "2024-07-23",
            "close": 71.65
          },
          {
            "date": "2024-07-24",
            "close": 70.17
          },
          {
            "date": "2024-07-25",
            "close": 68.89
          },
          {
            "date": "2024-07-26",
            "close": 69.58
          },
          {
            "date": "2024-07-29",
            "close": 70.66
          },
          {
            "date": "2024-07-30",
            "close": 71.35
          },
          {
            "date": "2024-07-31",
            "close": 73.24
          },
          {
            "date": "2024-08-01",
            "close": 70.57
          },
          {
            "date": "2024-08-02",
            "close": 71.3
          },
          {
            "date": "2024-08-05",
            "close": 69.4
          },
          {
            "date": "2024-08-06",
            "close": 70.82
          },
          {
            "date": "2024-08-07",
            "close": 70.74
          },
          {
            "date": "2024-08-08",
            "close": 71.18
          },
          {
            "date": "2024-08-09",
            "close": 70.56
          },
          {
            "date": "2024-08-12",
            "close": 72.38
          },
          {
            "date": "2024-08-13",
            "close": 90.11
          },
          {
            "date": "2024-08-14",
            "close": 88.23
          },
          {
            "date": "2024-08-15",
            "close": 89.15
          },
          {
            "date": "2024-08-16",
            "close": 89.62
          },
          {
            "date": "2024-08-19",
            "close": 87.25
          },
          {
            "date": "2024-08-20",
            "close": 87.92
          },
          {
            "date": "2024-08-21",
            "close": 87.7
          },
          {
            "date": "2024-08-22",
            "close": 87.37
          },
          {
            "date": "2024-08-23",
            "close": 88.88
          },
          {
            "date": "2024-08-26",
            "close": 90.4
          },
          {
            "date": "2024-08-27",
            "close": 93.21
          },
          {
            "date": "2024-08-28",
            "close": 90.09
          },
          {
            "date": "2024-08-29",
            "close": 89.67
          },
          {
            "date": "2024-08-30",
            "close": 89.4
          },
          {
            "date": "2024-09-03",
            "close": 88.08
          },
          {
            "date": "2024-09-04",
            "close": 87.28
          },
          {
            "date": "2024-09-05",
            "close": 86.55
          },
          {
            "date": "2024-09-06",
            "close": 86.16
          },
          {
            "date": "2024-09-09",
            "close": 87.17
          },
          {
            "date": "2024-09-10",
            "close": 88.23
          },
          {
            "date": "2024-09-11",
            "close": 92.83
          },
          {
            "date": "2024-09-12",
            "close": 93.85
          },
          {
            "date": "2024-09-13",
            "close": 93.18
          },
          {
            "date": "2024-09-16",
            "close": 91.04
          },
          {
            "date": "2024-09-17",
            "close": 91.16
          },
          {
            "date": "2024-09-18",
            "close": 90.86
          },
          {
            "date": "2024-09-19",
            "close": 91.6
          },
          {
            "date": "2024-09-20",
            "close": 90.8
          },
          {
            "date": "2024-09-23",
            "close": 90.26
          },
          {
            "date": "2024-09-24",
            "close": 89.28
          },
          {
            "date": "2024-09-25",
            "close": 90.39
          },
          {
            "date": "2024-09-26",
            "close": 92.14
          },
          {
            "date": "2024-09-27",
            "close": 92.03
          },
          {
            "date": "2024-09-30",
            "close": 92.16
          },
          {
            "date": "2024-10-01",
            "close": 92.1
          },
          {
            "date": "2024-10-02",
            "close": 91.22
          },
          {
            "date": "2024-10-03",
            "close": 90.33
          },
          {
            "date": "2024-10-04",
            "close": 91.3
          },
          {
            "date": "2024-10-07",
            "close": 90.83
          },
          {
            "date": "2024-10-08",
            "close": 90.95
          },
          {
            "date": "2024-10-09",
            "close": 90.63
          },
          {
            "date": "2024-10-10",
            "close": 88.74
          },
          {
            "date": "2024-10-11",
            "close": 90.32
          },
          {
            "date": "2024-10-14",
            "close": 89.58
          },
          {
            "date": "2024-10-15",
            "close": 89.84
          },
          {
            "date": "2024-10-16",
            "close": 90.24
          },
          {
            "date": "2024-10-17",
            "close": 90.06
          },
          {
            "date": "2024-10-18",
            "close": 91.54
          },
          {
            "date": "2024-10-21",
            "close": 91.17
          },
          {
            "date": "2024-10-22",
            "close": 91.52
          },
          {
            "date": "2024-10-23",
            "close": 92.31
          },
          {
            "date": "2024-10-24",
            "close": 91.84
          },
          {
            "date": "2024-10-25",
            "close": 91.99
          },
          {
            "date": "2024-10-28",
            "close": 92.66
          },
          {
            "date": "2024-10-29",
            "close": 92.06
          },
          {
            "date": "2024-10-30",
            "close": 92.0
          },
          {
            "date": "2024-10-31",
            "close": 92.36
          },
          {
            "date": "2024-11-01",
            "close": 93.46
          },
          {
            "date": "2024-11-04",
            "close": 91.72
          },
          {
            "date": "2024-11-05",
            "close": 91.78
          },
          {
            "date": "2024-11-06",
            "close": 90.82
          },
          {
            "date": "2024-11-07",
            "close": 90.86
          },
          {
            "date": "2024-11-08",
            "close": 92.21
          },
          {
            "date": "2024-11-11",
            "close": 94.82
          },
          {
            "date": "2024-11-12",
            "close": 93.39
          },
          {
            "date": "2024-11-13",
            "close": 94.34
          },
          {
            "date": "2024-11-14",
            "close": 93.8
          },
          {
            "date": "2024-11-15",
            "close": 93.61
          },
          {
            "date": "2024-11-18",
            "close": 95.49
          },
          {
            "date": "2024-11-19",
            "close": 93.54
          },
          {
            "date": "2024-11-20",
            "close": 93.46
          },
          {
            "date": "2024-11-21",
            "close": 95.17
          },
          {
            "date": "2024-11-22",
            "close": 97.49
          },
          {
            "date": "2024-11-25",
            "close": 96.86
          },
          {
            "date": "2024-11-26",
            "close": 95.76
          },
          {
            "date": "2024-11-27",
            "close": 96.55
          },
          {
            "date": "2024-11-29",
            "close": 97.45
          },
          {
            "date": "2024-12-02",
            "close": 96.55
          },
          {
            "date": "2024-12-03",
            "close": 96.61
          },
          {
            "date": "2024-12-04",
            "close": 95.78
          },
          {
            "date": "2024-12-05",
            "close": 94.38
          }
        ]
      },
      "total_impact_assessment": "Instant $21 billion market cap gain, complete overhaul of executive ranks, and nationwide operational pivot 'Back to Starbucks'.",
      "sources": [
        {
          "title": "Starbucks Names Brian Niccol Chairman and CEO",
          "url": "https://stories.starbucks.com/press/2024/starbucks-names-brian-niccol-chairman-and-ceo/"
        },
        {
          "title": "Starbucks Shares Soar Record 24.5%",
          "url": "https://www.cnbc.com/2024/08/13/starbucks-shares-soar-brian-niccol.html"
        }
      ]
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
        "Immediate sweeping restructuring and headcount reductions."
      ],
      "key_differences": [
        "Successor was a returning legacy CEO rather than an external hire.",
        "Disney faced unique cultural and political scrutiny alongside business challenges."
      ],
      "timeline": [
        {
          "date": "2022-11-08",
          "phase": "Precursor / Earnings Shock",
          "event": "Disney reports disastrous Q4 earnings with direct-to-consumer streaming losses widening to $1.47B.",
          "impact": "DIS stock crashes -13.2% the next day to $86.75, touching a multi-year low.",
          "stock_price": 96.86,
          "stock_change_from_baseline_pct": 0.0,
          "trading_volume": 27130300
        },
        {
          "date": "2022-11-20",
          "phase": "Trigger / Sunday Board Coup",
          "event": "Board Chair Susan Arnold notifies Chapek of termination and signs Bob Iger to a 2-year CEO agreement.",
          "impact": "Shock announcement stuns Hollywood and Wall Street; Chapek exit package finalized.",
          "stock_price": 94.61,
          "stock_change_from_baseline_pct": -2.32,
          "trading_volume": 70273500
        },
        {
          "date": "2022-11-21",
          "phase": "Public Reaction & Market Rebound",
          "event": "Bob Iger officially returns; DIS opens up +8% and closes up +6.3% at $97.58 with heavy volume.",
          "impact": "Instant restoration of multiple expansion; creative community expresses widespread relief.",
          "stock_price": 94.61,
          "stock_change_from_baseline_pct": -2.32,
          "trading_volume": 70273500
        },
        {
          "date": "2022-11-28",
          "phase": "Operational Reorganization",
          "event": "Iger disbands DMED distribution structure created by Chapek, returning P&L authority to creative heads.",
          "impact": "Major organizational shakeup; key Chapek lieutenant Kareem Daniel exits.",
          "stock_price": 92.78,
          "stock_change_from_baseline_pct": -4.21,
          "trading_volume": 13660000
        },
        {
          "date": "2023-02-08",
          "phase": "Strategic Plan & Mass Layoffs",
          "event": "Iger announces 7,000 job cuts ($5.5B cost reduction) and division into three core units during Q1 call.",
          "impact": "Stock trades up +5% after hours; activist Nelson Peltz withdraws proxy contest.",
          "stock_price": 108.38,
          "stock_change_from_baseline_pct": 11.89,
          "trading_volume": 27719900
        }
      ],
      "stock_metrics": {
        "ticker": "DIS",
        "baseline_date": "2022-11-08",
        "baseline_price": 96.86,
        "trough_date": "2022-12-28",
        "trough_price": 81.61,
        "max_drawdown_pct": -15.75,
        "daily_series": [
          {
            "date": "2022-10-14",
            "close": 91.58
          },
          {
            "date": "2022-10-17",
            "close": 94.37
          },
          {
            "date": "2022-10-18",
            "close": 95.48
          },
          {
            "date": "2022-10-19",
            "close": 95.98
          },
          {
            "date": "2022-10-20",
            "close": 95.59
          },
          {
            "date": "2022-10-21",
            "close": 98.93
          },
          {
            "date": "2022-10-24",
            "close": 98.62
          },
          {
            "date": "2022-10-25",
            "close": 101.18
          },
          {
            "date": "2022-10-26",
            "close": 101.45
          },
          {
            "date": "2022-10-27",
            "close": 101.26
          },
          {
            "date": "2022-10-28",
            "close": 102.73
          },
          {
            "date": "2022-10-31",
            "close": 103.3
          },
          {
            "date": "2022-11-01",
            "close": 102.77
          },
          {
            "date": "2022-11-02",
            "close": 98.72
          },
          {
            "date": "2022-11-03",
            "close": 96.23
          },
          {
            "date": "2022-11-04",
            "close": 96.55
          },
          {
            "date": "2022-11-07",
            "close": 97.37
          },
          {
            "date": "2022-11-08",
            "close": 96.86
          },
          {
            "date": "2022-11-09",
            "close": 84.11
          },
          {
            "date": "2022-11-10",
            "close": 87.71
          },
          {
            "date": "2022-11-11",
            "close": 92.12
          },
          {
            "date": "2022-11-14",
            "close": 91.41
          },
          {
            "date": "2022-11-15",
            "close": 92.6
          },
          {
            "date": "2022-11-16",
            "close": 91.09
          },
          {
            "date": "2022-11-17",
            "close": 88.67
          },
          {
            "date": "2022-11-18",
            "close": 89.01
          },
          {
            "date": "2022-11-21",
            "close": 94.61
          },
          {
            "date": "2022-11-22",
            "close": 93.28
          },
          {
            "date": "2022-11-23",
            "close": 95.87
          },
          {
            "date": "2022-11-25",
            "close": 95.86
          },
          {
            "date": "2022-11-28",
            "close": 92.78
          },
          {
            "date": "2022-11-29",
            "close": 91.81
          },
          {
            "date": "2022-11-30",
            "close": 94.89
          },
          {
            "date": "2022-12-01",
            "close": 95.59
          },
          {
            "date": "2022-12-02",
            "close": 96.4
          },
          {
            "date": "2022-12-05",
            "close": 93.01
          },
          {
            "date": "2022-12-06",
            "close": 89.48
          },
          {
            "date": "2022-12-07",
            "close": 89.35
          },
          {
            "date": "2022-12-08",
            "close": 89.73
          },
          {
            "date": "2022-12-09",
            "close": 90.54
          },
          {
            "date": "2022-12-12",
            "close": 91.78
          },
          {
            "date": "2022-12-13",
            "close": 91.82
          },
          {
            "date": "2022-12-14",
            "close": 91.28
          },
          {
            "date": "2022-12-15",
            "close": 87.74
          },
          {
            "date": "2022-12-16",
            "close": 87.34
          },
          {
            "date": "2022-12-19",
            "close": 83.17
          },
          {
            "date": "2022-12-20",
            "close": 84.37
          },
          {
            "date": "2022-12-21",
            "close": 84.27
          },
          {
            "date": "2022-12-22",
            "close": 84.03
          },
          {
            "date": "2022-12-23",
            "close": 85.33
          },
          {
            "date": "2022-12-27",
            "close": 83.74
          },
          {
            "date": "2022-12-28",
            "close": 81.61
          },
          {
            "date": "2022-12-29",
            "close": 84.53
          },
          {
            "date": "2022-12-30",
            "close": 84.24
          },
          {
            "date": "2023-01-03",
            "close": 86.26
          },
          {
            "date": "2023-01-04",
            "close": 89.18
          },
          {
            "date": "2023-01-05",
            "close": 89.12
          },
          {
            "date": "2023-01-06",
            "close": 91.06
          },
          {
            "date": "2023-01-09",
            "close": 91.89
          },
          {
            "date": "2023-01-10",
            "close": 92.65
          },
          {
            "date": "2023-01-11",
            "close": 93.4
          },
          {
            "date": "2023-01-12",
            "close": 96.77
          },
          {
            "date": "2023-01-13",
            "close": 96.37
          },
          {
            "date": "2023-01-17",
            "close": 96.87
          },
          {
            "date": "2023-01-18",
            "close": 96.03
          },
          {
            "date": "2023-01-19",
            "close": 96.06
          },
          {
            "date": "2023-01-20",
            "close": 100.33
          },
          {
            "date": "2023-01-23",
            "close": 102.47
          },
          {
            "date": "2023-01-24",
            "close": 102.77
          },
          {
            "date": "2023-01-25",
            "close": 104.83
          },
          {
            "date": "2023-01-26",
            "close": 106.36
          },
          {
            "date": "2023-01-27",
            "close": 106.21
          },
          {
            "date": "2023-01-30",
            "close": 104.32
          },
          {
            "date": "2023-01-31",
            "close": 105.19
          },
          {
            "date": "2023-02-01",
            "close": 106.06
          },
          {
            "date": "2023-02-02",
            "close": 109.76
          },
          {
            "date": "2023-02-03",
            "close": 107.34
          },
          {
            "date": "2023-02-06",
            "close": 106.53
          },
          {
            "date": "2023-02-07",
            "close": 108.23
          },
          {
            "date": "2023-02-08",
            "close": 108.38
          },
          {
            "date": "2023-02-09",
            "close": 107.0
          },
          {
            "date": "2023-02-10",
            "close": 104.77
          },
          {
            "date": "2023-02-13",
            "close": 104.38
          },
          {
            "date": "2023-02-14",
            "close": 104.38
          },
          {
            "date": "2023-02-15",
            "close": 105.92
          },
          {
            "date": "2023-02-16",
            "close": 102.61
          },
          {
            "date": "2023-02-17",
            "close": 102.02
          },
          {
            "date": "2023-02-21",
            "close": 98.98
          },
          {
            "date": "2023-02-22",
            "close": 98.59
          },
          {
            "date": "2023-02-23",
            "close": 98.63
          },
          {
            "date": "2023-02-24",
            "close": 97.25
          },
          {
            "date": "2023-02-27",
            "close": 97.39
          },
          {
            "date": "2023-02-28",
            "close": 96.58
          },
          {
            "date": "2023-03-01",
            "close": 95.54
          },
          {
            "date": "2023-03-02",
            "close": 95.91
          },
          {
            "date": "2023-03-03",
            "close": 98.06
          },
          {
            "date": "2023-03-06",
            "close": 97.6
          },
          {
            "date": "2023-03-07",
            "close": 96.04
          },
          {
            "date": "2023-03-08",
            "close": 96.28
          },
          {
            "date": "2023-03-09",
            "close": 93.21
          },
          {
            "date": "2023-03-10",
            "close": 90.72
          },
          {
            "date": "2023-03-13",
            "close": 89.78
          },
          {
            "date": "2023-03-14",
            "close": 90.52
          },
          {
            "date": "2023-03-15",
            "close": 90.27
          },
          {
            "date": "2023-03-16",
            "close": 91.42
          },
          {
            "date": "2023-03-17",
            "close": 90.36
          },
          {
            "date": "2023-03-20",
            "close": 91.35
          },
          {
            "date": "2023-03-21",
            "close": 93.6
          },
          {
            "date": "2023-03-22",
            "close": 92.01
          },
          {
            "date": "2023-03-23",
            "close": 92.91
          },
          {
            "date": "2023-03-24",
            "close": 91.22
          }
        ]
      },
      "total_impact_assessment": "Immediate relief rally (+6.3%), subsequent restructuring cutting 7,000 jobs ($5.5B cost savings), and intense proxy fight with Nelson Peltz.",
      "sources": [
        {
          "title": "Disney Board Replaces Bob Chapek with Bob Iger",
          "url": "https://www.nytimes.com/2022/11/20/business/media/bob-iger-disney-ceo.html"
        },
        {
          "title": "SEC Form 8-K Disney Executive Transition",
          "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1744489/000174448922000045/dis-20221120.htm"
        }
      ]
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
        "Customer backlash from airline CEOs demanding new governance."
      ],
      "key_differences": [
        "Calhoun was given a multi-month transition period rather than immediate removal.",
        "Underlying crisis involved human life safety and criminal settlement compliance."
      ],
      "timeline": [
        {
          "date": "2024-01-05",
          "phase": "Precursor Incident",
          "event": "Alaska Airlines Flight 1282 suffers mid-air door plug blowout on Boeing 737 MAX 9.",
          "impact": "FAA grounds 171 MAX 9 jets; stock plunges -8.0% on first trading day following incident.",
          "stock_price": 249.0,
          "stock_change_from_baseline_pct": 0.0,
          "trading_volume": 3849700
        },
        {
          "date": "2024-02-06",
          "phase": "NTSB Findings & Escalation",
          "event": "NTSB preliminary report finds door plug was installed at Boeing Renton factory with 4 bolts missing.",
          "impact": "Public confidence collapses; airline CEOs publicly voice extreme frustration.",
          "stock_price": 208.58,
          "stock_change_from_baseline_pct": -16.23,
          "trading_volume": 7556900
        },
        {
          "date": "2024-03-25",
          "phase": "Trigger / Executive Purge",
          "event": "CEO Dave Calhoun announces resignation; Stan Deal replaced immediately; Larry Kellner steps down.",
          "impact": "BA stock rallies +1.4% to $191.41 on leadership change news before resuming downtrend.",
          "stock_price": 191.41,
          "stock_change_from_baseline_pct": -23.13,
          "trading_volume": 12953000
        },
        {
          "date": "2024-07-31",
          "phase": "Successor Appointment",
          "event": "Boeing names aerospace engineering veteran Kelly Ortberg as new President and CEO.",
          "impact": "Positive analyst reaction to technical engineering background; stock stabilizes at $190.",
          "stock_price": 190.6,
          "stock_change_from_baseline_pct": -23.45,
          "trading_volume": 15417000
        },
        {
          "date": "2024-08-08",
          "phase": "New Leadership Strategy",
          "event": "Ortberg officially begins tenure, relocating workspace to Seattle to oversee factory floor operations.",
          "impact": "Shift away from corporate Chicago/Arlington bureaucracy toward manufacturing floor.",
          "stock_price": 168.87,
          "stock_change_from_baseline_pct": -32.18,
          "trading_volume": 6063800
        }
      ],
      "stock_metrics": {
        "ticker": "BA",
        "baseline_date": "2024-01-05",
        "baseline_price": 249.0,
        "trough_date": "2024-09-20",
        "trough_price": 153.29,
        "max_drawdown_pct": -38.44,
        "daily_series": [
          {
            "date": "2023-12-11",
            "close": 248.08
          },
          {
            "date": "2023-12-12",
            "close": 248.63
          },
          {
            "date": "2023-12-13",
            "close": 250.91
          },
          {
            "date": "2023-12-14",
            "close": 256.24
          },
          {
            "date": "2023-12-15",
            "close": 264.27
          },
          {
            "date": "2023-12-18",
            "close": 260.41
          },
          {
            "date": "2023-12-19",
            "close": 263.51
          },
          {
            "date": "2023-12-20",
            "close": 260.25
          },
          {
            "date": "2023-12-21",
            "close": 262.02
          },
          {
            "date": "2023-12-22",
            "close": 260.44
          },
          {
            "date": "2023-12-26",
            "close": 262.79
          },
          {
            "date": "2023-12-27",
            "close": 262.1
          },
          {
            "date": "2023-12-28",
            "close": 260.35
          },
          {
            "date": "2023-12-29",
            "close": 260.66
          },
          {
            "date": "2024-01-02",
            "close": 251.76
          },
          {
            "date": "2024-01-03",
            "close": 243.91
          },
          {
            "date": "2024-01-04",
            "close": 244.94
          },
          {
            "date": "2024-01-05",
            "close": 249.0
          },
          {
            "date": "2024-01-08",
            "close": 229.0
          },
          {
            "date": "2024-01-09",
            "close": 225.76
          },
          {
            "date": "2024-01-10",
            "close": 227.84
          },
          {
            "date": "2024-01-11",
            "close": 222.66
          },
          {
            "date": "2024-01-12",
            "close": 217.7
          },
          {
            "date": "2024-01-16",
            "close": 200.52
          },
          {
            "date": "2024-01-17",
            "close": 203.06
          },
          {
            "date": "2024-01-18",
            "close": 211.61
          },
          {
            "date": "2024-01-19",
            "close": 215.02
          },
          {
            "date": "2024-01-22",
            "close": 214.93
          },
          {
            "date": "2024-01-23",
            "close": 211.5
          },
          {
            "date": "2024-01-24",
            "close": 214.13
          },
          {
            "date": "2024-01-25",
            "close": 201.88
          },
          {
            "date": "2024-01-26",
            "close": 205.47
          },
          {
            "date": "2024-01-29",
            "close": 205.19
          },
          {
            "date": "2024-01-30",
            "close": 200.44
          },
          {
            "date": "2024-01-31",
            "close": 211.04
          },
          {
            "date": "2024-02-01",
            "close": 209.81
          },
          {
            "date": "2024-02-02",
            "close": 209.38
          },
          {
            "date": "2024-02-05",
            "close": 206.63
          },
          {
            "date": "2024-02-06",
            "close": 208.58
          },
          {
            "date": "2024-02-07",
            "close": 211.92
          },
          {
            "date": "2024-02-08",
            "close": 209.22
          },
          {
            "date": "2024-02-09",
            "close": 209.2
          },
          {
            "date": "2024-02-12",
            "close": 209.33
          },
          {
            "date": "2024-02-13",
            "close": 204.46
          },
          {
            "date": "2024-02-14",
            "close": 203.38
          },
          {
            "date": "2024-02-15",
            "close": 205.33
          },
          {
            "date": "2024-02-16",
            "close": 203.89
          },
          {
            "date": "2024-02-20",
            "close": 203.37
          },
          {
            "date": "2024-02-21",
            "close": 201.57
          },
          {
            "date": "2024-02-22",
            "close": 201.5
          },
          {
            "date": "2024-02-23",
            "close": 200.83
          },
          {
            "date": "2024-02-26",
            "close": 200.54
          },
          {
            "date": "2024-02-27",
            "close": 201.4
          },
          {
            "date": "2024-02-28",
            "close": 207.0
          },
          {
            "date": "2024-02-29",
            "close": 203.72
          },
          {
            "date": "2024-03-01",
            "close": 200.0
          },
          {
            "date": "2024-03-04",
            "close": 200.54
          },
          {
            "date": "2024-03-05",
            "close": 201.14
          },
          {
            "date": "2024-03-06",
            "close": 201.0
          },
          {
            "date": "2024-03-07",
            "close": 203.03
          },
          {
            "date": "2024-03-08",
            "close": 198.49
          },
          {
            "date": "2024-03-11",
            "close": 192.49
          },
          {
            "date": "2024-03-12",
            "close": 184.24
          },
          {
            "date": "2024-03-13",
            "close": 182.35
          },
          {
            "date": "2024-03-14",
            "close": 181.15
          },
          {
            "date": "2024-03-15",
            "close": 182.53
          },
          {
            "date": "2024-03-18",
            "close": 179.84
          },
          {
            "date": "2024-03-19",
            "close": 181.14
          },
          {
            "date": "2024-03-20",
            "close": 187.78
          },
          {
            "date": "2024-03-21",
            "close": 187.7
          },
          {
            "date": "2024-03-22",
            "close": 188.85
          },
          {
            "date": "2024-03-25",
            "close": 191.41
          },
          {
            "date": "2024-03-26",
            "close": 187.5
          },
          {
            "date": "2024-03-27",
            "close": 191.95
          },
          {
            "date": "2024-03-28",
            "close": 192.99
          },
          {
            "date": "2024-04-01",
            "close": 189.5
          },
          {
            "date": "2024-04-02",
            "close": 188.04
          },
          {
            "date": "2024-04-03",
            "close": 184.92
          },
          {
            "date": "2024-04-04",
            "close": 183.29
          },
          {
            "date": "2024-04-05",
            "close": 183.14
          },
          {
            "date": "2024-04-08",
            "close": 181.56
          },
          {
            "date": "2024-04-09",
            "close": 178.12
          },
          {
            "date": "2024-04-10",
            "close": 174.63
          },
          {
            "date": "2024-04-11",
            "close": 173.36
          },
          {
            "date": "2024-04-12",
            "close": 169.55
          },
          {
            "date": "2024-04-15",
            "close": 167.82
          },
          {
            "date": "2024-04-16",
            "close": 170.55
          },
          {
            "date": "2024-04-17",
            "close": 170.21
          },
          {
            "date": "2024-04-18",
            "close": 170.23
          },
          {
            "date": "2024-04-19",
            "close": 169.82
          },
          {
            "date": "2024-04-22",
            "close": 170.48
          },
          {
            "date": "2024-04-23",
            "close": 169.18
          },
          {
            "date": "2024-04-24",
            "close": 164.33
          },
          {
            "date": "2024-04-25",
            "close": 166.81
          },
          {
            "date": "2024-04-26",
            "close": 167.22
          },
          {
            "date": "2024-04-29",
            "close": 173.49
          },
          {
            "date": "2024-04-30",
            "close": 167.84
          },
          {
            "date": "2024-05-01",
            "close": 171.46
          },
          {
            "date": "2024-05-02",
            "close": 178.85
          },
          {
            "date": "2024-05-03",
            "close": 179.79
          },
          {
            "date": "2024-05-06",
            "close": 178.35
          },
          {
            "date": "2024-05-07",
            "close": 176.71
          },
          {
            "date": "2024-05-08",
            "close": 180.35
          },
          {
            "date": "2024-05-09",
            "close": 181.25
          },
          {
            "date": "2024-05-10",
            "close": 178.51
          },
          {
            "date": "2024-05-13",
            "close": 178.44
          },
          {
            "date": "2024-05-14",
            "close": 180.76
          },
          {
            "date": "2024-05-15",
            "close": 176.99
          },
          {
            "date": "2024-05-16",
            "close": 182.96
          },
          {
            "date": "2024-05-17",
            "close": 184.95
          },
          {
            "date": "2024-05-20",
            "close": 186.61
          },
          {
            "date": "2024-05-21",
            "close": 184.78
          },
          {
            "date": "2024-05-22",
            "close": 186.28
          },
          {
            "date": "2024-05-23",
            "close": 172.21
          },
          {
            "date": "2024-05-24",
            "close": 174.52
          },
          {
            "date": "2024-05-28",
            "close": 175.08
          },
          {
            "date": "2024-05-29",
            "close": 171.65
          },
          {
            "date": "2024-05-30",
            "close": 172.75
          },
          {
            "date": "2024-05-31",
            "close": 177.61
          },
          {
            "date": "2024-06-03",
            "close": 184.57
          },
          {
            "date": "2024-06-04",
            "close": 188.62
          },
          {
            "date": "2024-06-05",
            "close": 189.85
          },
          {
            "date": "2024-06-06",
            "close": 191.42
          },
          {
            "date": "2024-06-07",
            "close": 190.24
          },
          {
            "date": "2024-06-10",
            "close": 190.12
          },
          {
            "date": "2024-06-11",
            "close": 185.5
          },
          {
            "date": "2024-06-12",
            "close": 182.67
          },
          {
            "date": "2024-06-13",
            "close": 180.7
          },
          {
            "date": "2024-06-14",
            "close": 177.27
          },
          {
            "date": "2024-06-17",
            "close": 178.39
          },
          {
            "date": "2024-06-18",
            "close": 174.99
          },
          {
            "date": "2024-06-20",
            "close": 176.3
          },
          {
            "date": "2024-06-21",
            "close": 176.56
          },
          {
            "date": "2024-06-24",
            "close": 179.1
          },
          {
            "date": "2024-06-25",
            "close": 175.1
          },
          {
            "date": "2024-06-26",
            "close": 178.5
          },
          {
            "date": "2024-06-27",
            "close": 182.51
          },
          {
            "date": "2024-06-28",
            "close": 182.01
          },
          {
            "date": "2024-07-01",
            "close": 186.7
          },
          {
            "date": "2024-07-02",
            "close": 185.42
          },
          {
            "date": "2024-07-03",
            "close": 184.31
          },
          {
            "date": "2024-07-05",
            "close": 184.83
          },
          {
            "date": "2024-07-08",
            "close": 185.84
          },
          {
            "date": "2024-07-09",
            "close": 183.24
          },
          {
            "date": "2024-07-10",
            "close": 183.73
          },
          {
            "date": "2024-07-11",
            "close": 183.91
          },
          {
            "date": "2024-07-12",
            "close": 182.31
          },
          {
            "date": "2024-07-15",
            "close": 179.11
          },
          {
            "date": "2024-07-16",
            "close": 186.05
          },
          {
            "date": "2024-07-17",
            "close": 184.84
          },
          {
            "date": "2024-07-18",
            "close": 180.23
          },
          {
            "date": "2024-07-19",
            "close": 179.67
          },
          {
            "date": "2024-07-22",
            "close": 178.9
          },
          {
            "date": "2024-07-23",
            "close": 186.48
          },
          {
            "date": "2024-07-24",
            "close": 180.07
          },
          {
            "date": "2024-07-25",
            "close": 184.35
          },
          {
            "date": "2024-07-26",
            "close": 186.89
          },
          {
            "date": "2024-07-29",
            "close": 185.43
          },
          {
            "date": "2024-07-30",
            "close": 186.86
          },
          {
            "date": "2024-07-31",
            "close": 190.6
          },
          {
            "date": "2024-08-01",
            "close": 178.31
          },
          {
            "date": "2024-08-02",
            "close": 169.95
          },
          {
            "date": "2024-08-05",
            "close": 167.03
          },
          {
            "date": "2024-08-06",
            "close": 165.04
          },
          {
            "date": "2024-08-07",
            "close": 163.24
          },
          {
            "date": "2024-08-08",
            "close": 168.87
          },
          {
            "date": "2024-08-09",
            "close": 167.91
          },
          {
            "date": "2024-08-12",
            "close": 164.13
          },
          {
            "date": "2024-08-13",
            "close": 168.76
          },
          {
            "date": "2024-08-14",
            "close": 168.5
          },
          {
            "date": "2024-08-15",
            "close": 176.41
          },
          {
            "date": "2024-08-16",
            "close": 179.99
          },
          {
            "date": "2024-08-19",
            "close": 179.64
          },
          {
            "date": "2024-08-20",
            "close": 172.1
          },
          {
            "date": "2024-08-21",
            "close": 173.43
          },
          {
            "date": "2024-08-22",
            "close": 172.76
          },
          {
            "date": "2024-08-23",
            "close": 174.96
          },
          {
            "date": "2024-08-26",
            "close": 173.48
          },
          {
            "date": "2024-08-27",
            "close": 173.05
          },
          {
            "date": "2024-08-28",
            "close": 170.71
          },
          {
            "date": "2024-08-29",
            "close": 172.26
          },
          {
            "date": "2024-08-30",
            "close": 173.74
          },
          {
            "date": "2024-09-03",
            "close": 161.02
          },
          {
            "date": "2024-09-04",
            "close": 163.22
          },
          {
            "date": "2024-09-05",
            "close": 162.15
          },
          {
            "date": "2024-09-06",
            "close": 157.62
          },
          {
            "date": "2024-09-09",
            "close": 162.91
          },
          {
            "date": "2024-09-10",
            "close": 160.07
          },
          {
            "date": "2024-09-11",
            "close": 161.33
          },
          {
            "date": "2024-09-12",
            "close": 162.77
          },
          {
            "date": "2024-09-13",
            "close": 156.77
          },
          {
            "date": "2024-09-16",
            "close": 155.55
          },
          {
            "date": "2024-09-17",
            "close": 156.39
          },
          {
            "date": "2024-09-18",
            "close": 155.11
          },
          {
            "date": "2024-09-19",
            "close": 154.59
          },
          {
            "date": "2024-09-20",
            "close": 153.29
          }
        ]
      },
      "total_impact_assessment": "Complete executive slate overhaul, appointment of outsider Kelly Ortberg as CEO, and $21B emergency capital raise.",
      "sources": [
        {
          "title": "Boeing Announces Executive Leadership Changes",
          "url": "https://boeing.mediaroom.com/2024-03-25-Boeing-Announces-Executive-Leadership-Changes"
        },
        {
          "title": "FAA Steps Up Oversight of Boeing Production",
          "url": "https://www.faa.gov/newsroom/faa-statement-boeing-production-rate"
        }
      ]
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
        "Complete reversal and reinstatement of CEO within one week."
      ],
      "key_differences": [
        "OpenAI is a capped-profit entity governed by a non-profit board.",
        "Microsoft used the crisis to acquire a non-voting board observer seat and lock in tech access."
      ],
      "timeline": [
        {
          "date": "2023-11-17",
          "phase": "Trigger / Sudden Firing",
          "event": "OpenAI board announces Sam Altman has been pushed out; Greg Brockman quits in protest.",
          "impact": "MSFT stock dips -1.7% in late Friday trading over fears of OpenAI partnership collapse.",
          "stock_price": 362.12,
          "stock_change_from_baseline_pct": 0.0,
          "trading_volume": 40157000
        },
        {
          "date": "2023-11-19",
          "phase": "Microsoft Counter-Offensive",
          "event": "Satya Nadella announces Sam Altman and Greg Brockman will join Microsoft to lead new advanced AI lab.",
          "impact": "MSFT stock rallies to a fresh all-time high ($377.44) as investors view Microsoft as ultimate winner.",
          "stock_price": 369.55,
          "stock_change_from_baseline_pct": 2.05,
          "trading_volume": 52465100
        },
        {
          "date": "2023-11-20",
          "phase": "Workforce Mutiny",
          "event": "Over 700 of OpenAI's 770 employees sign open letter demanding board resignation or they will join Microsoft.",
          "impact": "Existing board loses all operational leverage; emergency negotiations begin.",
          "stock_price": 369.55,
          "stock_change_from_baseline_pct": 2.05,
          "trading_volume": 52465100
        },
        {
          "date": "2023-11-21",
          "phase": "Reinstatement & Resolution",
          "event": "Agreement reached for Altman to return as CEO; new board formed with Bret Taylor and Larry Summers.",
          "impact": "Crisis resolved in 96 hours; Microsoft secures non-voting observer seat on OpenAI board.",
          "stock_price": 365.27,
          "stock_change_from_baseline_pct": 0.87,
          "trading_volume": 28423100
        },
        {
          "date": "2023-11-29",
          "phase": "Aftermath & Normalization",
          "event": "Altman officially resumes role; Microsoft deepens Azure integration and governance protocols.",
          "impact": "MSFT shares sustain record highs; investor confidence in AI roadmap cemented.",
          "stock_price": 370.93,
          "stock_change_from_baseline_pct": 2.43,
          "trading_volume": 28963400
        }
      ],
      "stock_metrics": {
        "ticker": "MSFT",
        "baseline_date": "2023-11-17",
        "baseline_price": 362.12,
        "trough_date": "2023-10-26",
        "trough_price": 320.39,
        "max_drawdown_pct": -11.52,
        "daily_series": [
          {
            "date": "2023-10-23",
            "close": 321.78
          },
          {
            "date": "2023-10-24",
            "close": 322.97
          },
          {
            "date": "2023-10-25",
            "close": 332.87
          },
          {
            "date": "2023-10-26",
            "close": 320.39
          },
          {
            "date": "2023-10-27",
            "close": 322.26
          },
          {
            "date": "2023-10-30",
            "close": 329.59
          },
          {
            "date": "2023-10-31",
            "close": 330.37
          },
          {
            "date": "2023-11-01",
            "close": 338.15
          },
          {
            "date": "2023-11-02",
            "close": 340.35
          },
          {
            "date": "2023-11-03",
            "close": 344.73
          },
          {
            "date": "2023-11-06",
            "close": 348.37
          },
          {
            "date": "2023-11-07",
            "close": 352.28
          },
          {
            "date": "2023-11-08",
            "close": 354.89
          },
          {
            "date": "2023-11-09",
            "close": 352.44
          },
          {
            "date": "2023-11-10",
            "close": 361.21
          },
          {
            "date": "2023-11-13",
            "close": 358.29
          },
          {
            "date": "2023-11-14",
            "close": 361.8
          },
          {
            "date": "2023-11-15",
            "close": 361.94
          },
          {
            "date": "2023-11-16",
            "close": 368.31
          },
          {
            "date": "2023-11-17",
            "close": 362.12
          },
          {
            "date": "2023-11-20",
            "close": 369.55
          },
          {
            "date": "2023-11-21",
            "close": 365.27
          },
          {
            "date": "2023-11-22",
            "close": 369.95
          },
          {
            "date": "2023-11-24",
            "close": 369.54
          },
          {
            "date": "2023-11-27",
            "close": 370.7
          },
          {
            "date": "2023-11-28",
            "close": 374.7
          },
          {
            "date": "2023-11-29",
            "close": 370.93
          },
          {
            "date": "2023-11-30",
            "close": 370.99
          },
          {
            "date": "2023-12-01",
            "close": 366.68
          },
          {
            "date": "2023-12-04",
            "close": 361.42
          },
          {
            "date": "2023-12-05",
            "close": 364.73
          },
          {
            "date": "2023-12-06",
            "close": 361.09
          },
          {
            "date": "2023-12-07",
            "close": 363.2
          },
          {
            "date": "2023-12-08",
            "close": 366.41
          },
          {
            "date": "2023-12-11",
            "close": 363.54
          },
          {
            "date": "2023-12-12",
            "close": 366.55
          },
          {
            "date": "2023-12-13",
            "close": 366.54
          },
          {
            "date": "2023-12-14",
            "close": 358.28
          },
          {
            "date": "2023-12-15",
            "close": 362.98
          },
          {
            "date": "2023-12-18",
            "close": 364.86
          },
          {
            "date": "2023-12-19",
            "close": 365.46
          },
          {
            "date": "2023-12-20",
            "close": 362.87
          },
          {
            "date": "2023-12-21",
            "close": 365.73
          },
          {
            "date": "2023-12-22",
            "close": 366.75
          },
          {
            "date": "2023-12-26",
            "close": 366.83
          },
          {
            "date": "2023-12-27",
            "close": 366.25
          },
          {
            "date": "2023-12-28",
            "close": 367.44
          },
          {
            "date": "2023-12-29",
            "close": 368.18
          },
          {
            "date": "2024-01-02",
            "close": 363.12
          },
          {
            "date": "2024-01-03",
            "close": 362.85
          },
          {
            "date": "2024-01-04",
            "close": 360.25
          },
          {
            "date": "2024-01-05",
            "close": 360.06
          },
          {
            "date": "2024-01-08",
            "close": 366.86
          },
          {
            "date": "2024-01-09",
            "close": 367.94
          },
          {
            "date": "2024-01-10",
            "close": 374.77
          },
          {
            "date": "2024-01-11",
            "close": 376.59
          },
          {
            "date": "2024-01-12",
            "close": 380.35
          }
        ]
      },
      "total_impact_assessment": "Strengthened Microsoft's strategic leverage in AI, purged hostile OpenAI board members, and reinforced founder control.",
      "sources": [
        {
          "title": "OpenAI Announces Leadership Transition",
          "url": "https://openai.com/index/openai-announces-leadership-transition/"
        },
        {
          "title": "Sam Altman Returns to OpenAI",
          "url": "https://www.wsj.com/tech/ai/sam-altman-returns-to-openai-board-reconstituted-d349ee14"
        }
      ]
    }
  ]
}
