#!/usr/bin/env -S uv run
# /// script
# dependencies = ["matplotlib", "numpy"]
# ///
"""
Read benchmark_results.json and produce benchmark.png with four charts:
  1. Cold start breakdown (stacked bar)
  2. Warm latency server-side percentiles (grouped bar)
  3. Warm latency client-side percentiles (grouped bar)
  4. Throughput (bar + req/sec annotation)
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── light-theme colours (GitHub README friendly) ───────────────────────────────
SPY_COLOR     = "#1f77b4"   # matplotlib C0 blue
FASTAPI_COLOR = "#ff7f0e"   # matplotlib C1 orange
BG            = "#ffffff"   # white
CARD_BG       = "#f8fafc"   # slate-50
TEXT          = "#0f172a"   # slate-950
MUTED         = "#64748b"   # slate-500
GRID          = "#cbd5e1"   # slate-300

LABELS = {"spy": "SPy", "fastapi": "FastAPI"}
COLORS = {"spy": SPY_COLOR, "fastapi": FASTAPI_COLOR}

# ── load data ──────────────────────────────────────────────────────────────────
json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("benchmark_results.json")
with json_path.open() as f:
    d = json.load(f)

fns = ["spy", "fastapi"]

# ── global style ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    GRID,
    "axes.labelcolor":   TEXT,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    11,
    "axes.labelsize":    9,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "xtick.labelsize":   9,
    "ytick.labelsize":   8,
    "grid.color":        GRID,
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  GRID,
    "legend.labelcolor": TEXT,
    "legend.fontsize":   8,
    "text.color":        TEXT,
})

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle(
    f"SPy vs FastAPI — AWS Lambda Benchmark\n{d['timestamp']}",
    fontsize=13, color=TEXT, y=1.02,
)

def bar_label(ax, bars, fmt="{:.1f}"):
    """Print value labels above each bar."""
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + ax.get_ylim()[1] * 0.01,
            fmt.format(h),
            ha="center", va="bottom", fontsize=8, color=TEXT,
        )

def speedup_label(ax, ratio, label="SPy", suffix="faster"):
    """Annotate the chart with a speedup badge centred below the x-axis."""
    if ratio is None:
        return
    text = f"{label}: {ratio:.1f}× {suffix}"
    ax.text(0.5, -0.13, text,
            transform=ax.transAxes,
            ha="center", va="top", fontsize=9, fontweight="bold",
            color=SPY_COLOR, clip_on=False,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=SPY_COLOR, linewidth=1.2))

# ── 1. Cold start ──────────────────────────────────────────────────────────────
ax = axes[0]
x = np.arange(len(fns))
w = 0.5

init_vals    = [d[f]["cold_start"]["init_ms"]    for f in fns]
handler_vals = [d[f]["cold_start"]["handler_ms"] for f in fns]

b_init = ax.bar(x, init_vals, w, color=[SPY_COLOR, FASTAPI_COLOR])
b_hand = ax.bar(x, handler_vals, w, bottom=init_vals, color=["#1a5f8a", "#b35a00"])

# Annotate each segment with its value and label
for bar, val in zip(b_init, init_vals):
    if val > 0:
        ax.text(bar.get_x() + w / 2, val / 2, f"init\n{val:.1f} ms",
                ha="center", va="center", fontsize=8, color="white", fontweight="bold")

for bar, init, hand in zip(b_hand, init_vals, handler_vals):
    if hand > 0:
        ax.text(bar.get_x() + w / 2, init + hand / 2, f"handler\n{hand:.1f} ms",
                ha="center", va="center", fontsize=8, color="white", fontweight="bold")

ax.set_title("Cold Start")
ax.set_ylabel("ms")
ax.set_xticks(x)
ax.set_xticklabels([LABELS[f] for f in fns])
ax.yaxis.grid(True)
ax.set_axisbelow(True)

spy_total     = d["spy"]["cold_start"]["init_ms"] + d["spy"]["cold_start"]["handler_ms"]
fastapi_total = d["fastapi"]["cold_start"]["init_ms"] + d["fastapi"]["cold_start"]["handler_ms"]
cold_ratio = fastapi_total / spy_total if spy_total > 0 and fastapi_total > 0 else None
speedup_label(ax, cold_ratio)

# ── 2. Warm latency – server-side (CloudWatch) ────────────────────────────────
ax = axes[1]
percentiles = ["p50_ms", "p95_ms", "max_ms"]
perc_labels = ["p50", "p95", "max"]
x = np.arange(len(percentiles))
w = 0.3

for i, fn in enumerate(fns):
    vals = [d[fn]["warm_latency"]["server"][p] for p in percentiles]
    bars = ax.bar(x + (i - 0.5) * w, vals, w,
                  label=LABELS[fn].replace("\n", " "), color=COLORS[fn])
    bar_label(ax, bars)

ax.set_title("Warm Latency — Server-side\n(CloudWatch Duration)")
ax.set_ylabel("ms")
ax.set_xticks(x)
ax.set_xticklabels(perc_labels)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
ax.legend()

spy_p50     = d["spy"]["warm_latency"]["server"]["p50_ms"]
fastapi_p50 = d["fastapi"]["warm_latency"]["server"]["p50_ms"]
warm_ratio = fastapi_p50 / spy_p50 if spy_p50 > 0 else None
speedup_label(ax, warm_ratio, suffix="lower p50")

# ── 3. Throughput ──────────────────────────────────────────────────────────────
ax = axes[2]
rps_vals = [d[fn]["throughput"]["requests_per_sec"] for fn in fns]
bars = ax.bar(
    [LABELS[fn] for fn in fns], rps_vals,
    color=[COLORS[fn] for fn in fns], width=0.5,
)

n  = d["config"]["throughput_n"]
c  = d["config"]["throughput_c"]
for bar, val in zip(bars, rps_vals):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + ax.get_ylim()[1] * 0.01,
            f"{val:.0f} req/s",
            ha="center", va="bottom", fontsize=9, color=TEXT, fontweight="bold")

ax.set_title(f"Throughput\n({n} requests, concurrency {c})")
ax.set_ylabel("requests / sec")
ax.yaxis.grid(True)
ax.set_axisbelow(True)

spy_rps     = d["spy"]["throughput"]["requests_per_sec"]
fastapi_rps = d["fastapi"]["throughput"]["requests_per_sec"]
tput_ratio = spy_rps / fastapi_rps if fastapi_rps > 0 else None
speedup_label(ax, tput_ratio, suffix="more req/s")

# ── save ───────────────────────────────────────────────────────────────────────
plt.tight_layout()
plt.subplots_adjust(bottom=0.18)
out = json_path.with_suffix(".png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
print(f"Saved {out}")
