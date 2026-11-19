#!/usr/bin/env python3
"""
Web-Based Graphical Graph Nodes Visualizer & Research Server
============================================================
FastAPI web application that serves:
  1. Interactive Vis.js network graph showing company & event milestone nodes with
     real-time historical stock prices and drawdown badges directly on the graph nodes.
  2. Multi-company stock performance curves with milestone annotations.
  3. Interactive forensic node inspector side panel.
  4. Live API endpoints to view current timeline data and trigger new deep research
     scenarios directly from the browser!

Usage:
    python web_app.py
    python web_app.py --port 8080
"""

import os
import sys
import json
import argparse
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import agent pipeline
from agent import run_research_timeline, DeepResearchTimelineOutput

load_dotenv(".env")
if not os.getenv("GROQ_API_KEY") and not os.getenv("LLM_API_KEY"):
    load_dotenv("../eventlens/.env")

app = FastAPI(title="Corporate Event & Stock Price Graph Nodes Visualizer")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "similar_news_timeline.json")

# Ensure static folder exists
os.makedirs(STATIC_DIR, exist_ok=True)


class ResearchRequest(BaseModel):
    prompt: str = Field(..., description="Corporate crisis or news event scenario to research")
    companies: int = Field(5, ge=5, le=10, description="Number of major companies to research (5 to 10)")


@app.get("/")
async def serve_index():
    """Serve the interactive web visualization frontend."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="static/index.html not found.")
    return FileResponse(index_path)


@app.get("/api/timeline")
async def get_timeline_data():
    """Return the currently saved JSON timeline data."""
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="similar_news_timeline.json not found. Please run research first.")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load timeline data: {e}")


@app.post("/api/research")
async def run_research(req: ResearchRequest):
    """Trigger deep research on a new prompt scenario and return updated JSON."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        print(f"\n[Web Server] Triggering deep research for prompt: '{req.prompt}' (Companies: {req.companies})...")
        result_dict = run_research_timeline(prompt=req.prompt, companies=req.companies)
        
        # Save updated data to disk
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
        return JSONResponse(content=result_dict)
    except Exception as e:
        print(f"[Web Server Error] {e}")
        raise HTTPException(status_code=500, detail=f"Deep research execution error: {e}")


@app.get("/api/status")
async def get_system_status():
    """Return configuration status of LLM and search agents."""
    groq_set = bool(os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY"))
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    tavily_set = bool(tavily_key and not tavily_key.startswith("your_") and len(tavily_key) > 5)
    
    return {
        "groq_configured": groq_set,
        "tavily_configured": tavily_set,
        "tavily_mode": "Live Tavily News Search" if tavily_set else "Live Search Fallback (Google News & Wikipedia)",
        "data_file_exists": os.path.exists(DATA_FILE)
    }


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    parser = argparse.ArgumentParser(description="Start the Graph Nodes & Stock Visualizer Web App.")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Web server host (default: 0.0.0.0)")
    args = parser.parse_args()

    print(f"\n==================================================================")
    print(f"🚀 Event & Stock Price Graph Nodes Visualizer Web Server Running")
    print(f"👉 Local Access URL:  http://localhost:{args.port}")
    print(f"👉 Network Access:    http://{args.host}:{args.port}")
    print(f"==================================================================\n")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
