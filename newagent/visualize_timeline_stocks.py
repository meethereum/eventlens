#!/usr/bin/env python3
"""
Company-Wise Horizontal Event & Stock Price Graph Visualizer
============================================================
Reads `similar_news_timeline.json`, plots uncluttered company-by-company
horizontal milestone graphs mapped directly to their stock price trajectories,
and outputs high-resolution forensic charts.

Usage:
    python visualize_timeline_stocks.py
    python visualize_timeline_stocks.py --input similar_news_timeline.json --output horizontal_stock_graphs.png
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
except ImportError:
    console = None


def load_timeline_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file '{filepath}' not found. Please run agent.py first.")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_horizontal_company_charts(data: dict, output_image_path: str = "similar_news_stock_analysis.png"):
    """
    Generate uncluttered company-wise horizontal charts:
    Each company gets its own dedicated horizontal row featuring its stock price curve
    with milestone nodes mapped horizontally across time.
    """
    companies = data.get("similar_company_events", [])
    valid_companies = [c for c in companies if c.get("stock_metrics") and c["stock_metrics"].get("daily_series")]

    if not valid_companies:
        print("Notice: No company stock price series found in JSON.")
        return

    n_comps = len(valid_companies)
    fig, axes = plt.subplots(n_comps, 1, figsize=(15, 3.2 * n_comps), sharex=False, dpi=160)
    if n_comps == 1:
        axes = [axes]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    phase_colors = {
        "trigger": "#f59e0b",
        "precursor": "#f59e0b",
        "outbreak": "#ef4444",
        "crisis": "#ef4444",
        "crash": "#ef4444",
        "escalation": "#f43f5e",
        "containment": "#a855f7",
        "resolution": "#10b981",
        "aftermath": "#06b6d4"
    }

    for idx, (comp, ax) in enumerate(zip(valid_companies, axes)):
        sm = comp["stock_metrics"]
        ticker = sm["ticker"]
        df_daily = pd.DataFrame(sm["daily_series"])
        df_daily["date"] = pd.to_datetime(df_daily["date"])
        df_daily = df_daily.sort_values("date")

        # 1. Continuous Stock Price Line
        ax.plot(
            df_daily["date"],
            df_daily["close"],
            color="#0284c7",
            linewidth=2.2,
            label=f"{ticker} Close ($)"
        )
        ax.fill_between(
            df_daily["date"],
            df_daily["close"],
            df_daily["close"].min() * 0.98,
            color="#0ea5e9",
            alpha=0.08
        )

        # Baseline horizontal reference line
        base_p = sm["baseline_price"]
        ax.axhline(base_p, color="#64748b", linestyle="--", linewidth=1.0, alpha=0.7, label=f"Baseline: ${base_p:.2f}")

        # 2. Horizontal Milestone Nodes Mapped with Stock Prices
        timeline = comp.get("timeline", [])
        annot_toggle = 0
        for m_idx, m in enumerate(timeline):
            if m.get("stock_price") is not None:
                m_date = pd.to_datetime(m["date"][:10])
                m_price = m["stock_price"]
                p_lower = m["phase"].lower()

                # Choose phase color
                color = "#3b82f6"
                for k, c_code in phase_colors.items():
                    if k in p_lower:
                        color = c_code
                        break

                # Draw Milestone Node (Circle Marker)
                ax.scatter(m_date, m_price, color=color, s=80, zorder=6, edgecolor="white", linewidth=1.5)

                # Vertical dotted drop-line from node to chart axis
                ax.axvline(m_date, color=color, linestyle=":", alpha=0.45, linewidth=1.0)

                # Node Callout Box
                chg_str = f"{m['stock_change_from_baseline_pct']:+.1f}%" if m.get("stock_change_from_baseline_pct") is not None else ""
                callout_text = f"Node {m_idx + 1}: {m['phase']}\n${m_price:.2f} ({chg_str})"

                y_offset = 26 if (annot_toggle % 2 == 0) else -32
                annot_toggle += 1

                ax.annotate(
                    callout_text,
                    xy=(m_date, m_price),
                    xytext=(0, y_offset),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    fontweight="bold",
                    color="#0f172a",
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.0),
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=color, alpha=0.92, lw=1.2)
                )

        # Subplot Title & Badges
        dd_str = f"Max Drawdown: {sm['max_drawdown_pct']:.1f}%"
        ax.set_title(
            f"Company {idx + 1}: {comp['company_name']} ({ticker}) | {comp['incident_title']} | {dd_str}",
            fontsize=11,
            fontweight="bold",
            loc="left",
            pad=10
        )
        ax.set_ylabel("Share Price ($)", fontsize=9, fontweight="semibold")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=8, frameon=True)

    fig.suptitle(
        f"Company-Wise Horizontal Event & Stock Price Trajectory\nIncident Archetype: {data.get('incident_category')}",
        fontsize=14,
        fontweight="bold",
        y=0.995
    )

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"✓ Generated uncluttered company-wise horizontal charts: {os.path.abspath(output_image_path)}")


def draw_analytical_conclusions(data: dict) -> str:
    """Generate markdown report with key market findings."""
    companies = data.get("similar_company_events", [])
    conclusions_md = []
    conclusions_md.append(f"# Crisis Forensics & Market Conclusions Report\n")
    conclusions_md.append(f"**Archetype:** {data.get('incident_category')}\n")
    conclusions_md.append(f"**Prompt:** *\"{data.get('query_prompt')}\"*\n\n")

    conclusions_md.append("## Cross-Company Impact Summary\n")
    conclusions_md.append("| Company | Ticker | Incident | Baseline Price | Trough Price | Peak Drawdown |\n")
    conclusions_md.append("| :--- | :--- | :--- | :--- | :--- | :--- |\n")

    for c in companies:
        sm = c.get("stock_metrics")
        ticker = sm["ticker"] if sm else "N/A"
        base_p = f"${sm['baseline_price']:.2f}" if sm else "N/A"
        trough_p = f"${sm['trough_price']:.2f}" if sm else "N/A"
        dd_str = f"{sm['max_drawdown_pct']:.1f}%" if sm else "N/A"
        conclusions_md.append(f"| **{c['company_name']}** | `{ticker}` | {c['incident_title']} | {base_p} | {trough_p} | **{dd_str}** |\n")

    report_str = "".join(conclusions_md)
    with open("crisis_stock_conclusions.md", "w", encoding="utf-8") as f:
        f.write(report_str)
    return report_str


def main():
    parser = argparse.ArgumentParser(description="Generate company-wise horizontal news & stock graphs.")
    parser.add_argument("--input", "-i", type=str, default="similar_news_timeline.json")
    parser.add_argument("--output", "-o", type=str, default="similar_news_stock_analysis.png")
    args = parser.parse_args()

    data = load_timeline_json(args.input)
    generate_horizontal_company_charts(data, output_image_path=args.output)
    draw_analytical_conclusions(data)


if __name__ == "__main__":
    main()
