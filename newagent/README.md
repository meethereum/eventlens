# Deep Research Corporate Incident & Stock Price Timeline Agent

An agentic deep research system that accepts an incident scenario, discovers **5–10 similar major corporate crises** using **Tavily Live News**, reconstructs chronological event milestones, and maps **real historical stock prices, percentage drawdowns, and trading volume** onto each milestone in structured JSON.

Includes an **interactive web-based graph nodes visualization dashboard** and automated forensic market analysis.

---

## 🌟 Key Capabilities

1. **Live News Research Agent (Tavily)**:
   - Queries Tavily's neural news search for real-world corporate parallels.
   - Fetches full webpage markdown text using `httpx` + `markdownify` for deep analysis.
   - Built-in resilient live web fallback (Google News RSS & Wikipedia) if no key is provided.

2. **Chronological Milestone Reconstruction**:
   - Reconstructs 4–8 milestone events per company: *Trigger / Precursor*, *Outbreak / Initial Impact*, *Escalation / Contagion*, *Emergency Containment*, *Resolution / Aftermath*.

3. **Historical Stock Price & Drawdown Mapping**:
   - Integrates with `yfinance` to fetch historical stock data for each company's ticker (e.g. `CRWD`, `AMZN`, `SABR`, `UNH`, `MSFT`).
   - Maps exact closing price, volume, and percentage change from baseline onto every event milestone.
   - Computes pre-crisis baseline, crisis trough, and maximum percentage drawdown.

4. **Web-Based Graphical Graph Nodes Visualization**:
   - Built with **Vis.js Network** (force-directed interactive graph) and **Chart.js** (normalized stock curves).
   - **Nodes on the Graph Display Real Stock Prices**: e.g., `$76.24 (-11.1%)` directly on the milestone nodes!
   - **Interactive Node Forensics Inspector**: Click any company or milestone node to view the stock price, volume, event summary, and mini-sparkline.
   - **In-Browser Research Runner**: Type a new prompt in the web UI to trigger real-time deep research on any new scenario!

5. **Publication-Quality Forensic Charts & Written Conclusions**:
   - Multi-panel charts saved to `similar_news_stock_analysis.png`.
   - Comprehensive written analysis saved to `crisis_stock_conclusions.md`.

---

## 🚀 Quick Start

### 1. Environment Setup
The project uses Python 3.12 with `.venv`:
```bash
# If running for the first time
uv pip install -r requirements.txt
```

Configure your API keys in `.env`:
```ini
# Groq API Key (High-throughput LLM reasoning)
GROQ_API_KEY=gsk_your_groq_key_here

# Tavily API Key (Live news search)
TAVILY_API_KEY=tvly-your_tavily_key_here
```

---

## 💻 Running the Tools

### 🌐 1. Launch the Web-Based Graph Nodes Visualizer
Start the local web application:
```bash
python web_app.py --port 8000
```
Open **`http://localhost:8000`** in any web browser to explore:
- Interactive physics-based graph nodes with milestone stock prices
- Synchronized multi-company stock curves
- Node forensics inspector side panel
- "New Research" button to run any scenario directly from the browser

*(You can also double-click [stock_timeline_graph.html](file:///home/pranav/dev/pydev/newagent/stock_timeline_graph.html) to open the dashboard offline with no server).*

---

### 🔍 2. Run Deep Research from the CLI
Run the agent on any corporate crisis or scenario:
```bash
# Example 1: Global Cloud / Cybersecurity Glitch
python agent.py "A major cybersecurity glitch or faulty vendor update takes down airlines, banks, and hospital IT systems worldwide" -n 5

# Example 2: Executive Boardroom Coup & Reinstatement
python agent.py "A CEO is ousted by the board over governance disagreements and rehired days later following employee revolt" -n 5

# Example 3: Crypto / Financial Collapse
python agent.py "A cryptocurrency exchange secretly misappropriates billions in customer funds to prop up its trading arm" -n 5
```

Outputs:
- Saves the full dataset to [`similar_news_timeline.json`](file:///home/pranav/dev/pydev/newagent/similar_news_timeline.json).

---

### 📊 3. Generate Static Charts and Forensic Conclusions
Generate multi-panel charts and written market analysis:
```bash
python visualize_timeline_stocks.py
```

Outputs:
- High-res graphic: [`similar_news_stock_analysis.png`](file:///home/pranav/dev/pydev/newagent/similar_news_stock_analysis.png)
- Forensic report: [`crisis_stock_conclusions.md`](file:///home/pranav/dev/pydev/newagent/crisis_stock_conclusions.md)

---

## 📁 Project Structure

```
newagent/
├── agent.py                     # Main Deep Research Agent with Tavily & yfinance stock mapping
├── web_app.py                   # FastAPI web server hosting interactive node visualizer
├── visualize_timeline_stocks.py # Matplotlib multi-panel chart & forensic conclusions script
├── stock_timeline_graph.html    # Standalone offline-ready HTML graph dashboard
├── static/
│   └── index.html               # Frontend dashboard (Vis.js Network + Chart.js)
├── similar_news_timeline.json   # Generated multi-company incident & stock timeline data
├── similar_news_stock_analysis.png # Generated 3-panel visualization chart
├── crisis_stock_conclusions.md  # Written analytical market conclusions report
├── requirements.txt             # Project dependencies
└── .env                         # API credentials configuration
```
