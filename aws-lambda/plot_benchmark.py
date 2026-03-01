#!/usr/bin/env python3
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

# ── colours matching the demo CSS gradient ─────────────────────────────────────
SPY_COLOR     = "#38bdf8"   # sky-400
FASTAPI_COLOR = "#818cf8"   # indigo-400
BG            = "#0f172a"   # slate-950
CARD_BG       = "#1e293b"   # slate-800
TEXT          = "#e2e8f0"   # slate-200
MUTED         = "#94a3b8"   # slate-400
GRID          = "#334155"   # slate-700

LABELS = {"spy": "SPy\n(native binary)", "fastapi": "FastAPI\n(CPython)"}
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

fig, axes = plt.subplots(1, 4, figsize=(18, 5))
fig.suptitle(
    f"Lambda Benchmark: SPy (native binary) vs FastAPI (CPython)\n{d['timestamp']}",
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

# ── 1. Cold start ──────────────────────────────────────────────────────────────
ax = axes[0]
x = np.arange(len(fns))
w = 0.5

init_vals    = [d[f]["cold_start"]["init_ms"]    for f in fns]
handler_vals = [d[f]["cold_start"]["handler_ms"] for f in fns]

b_init = ax.bar(x, init_vals, w,
                label="Init (runtime startup)", color=[SPY_COLOR, FASTAPI_COLOR])
b_hand = ax.bar(x, handler_vals, w, bottom=init_vals,
                label="Handler", color=["#0369a1", "#4338ca"])

# Annotate each segment with its value
for bar, val in zip(b_init, init_vals):
    if val > 0:
        ax.text(bar.get_x() + w / 2, val / 2, f"{val:.1f}",
                ha="center", va="center", fontsize=8, color=BG, fontweight="bold")

for bar, init, hand in zip(b_hand, init_vals, handler_vals):
    if hand > 0:
        ax.text(bar.get_x() + w / 2, init + hand / 2, f"{hand:.1f}",
                ha="center", va="center", fontsize=8, color=BG, fontweight="bold")

ax.set_title("Cold Start")
ax.set_ylabel("ms")
ax.set_xticks(x)
ax.set_xticklabels([LABELS[f] for f in fns])
ax.yaxis.grid(True)
ax.set_axisbelow(True)
ax.legend(loc="upper left")

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

# ── 3. Warm latency – client-side (hey) ───────────────────────────────────────
ax = axes[2]
percentiles = ["p50_ms", "p95_ms", "p99_ms"]
perc_labels = ["p50", "p95", "p99"]
x = np.arange(len(percentiles))
w = 0.3

for i, fn in enumerate(fns):
    vals = [d[fn]["warm_latency"]["client"][p] for p in percentiles]
    bars = ax.bar(x + (i - 0.5) * w, vals, w,
                  label=LABELS[fn].replace("\n", " "), color=COLORS[fn])
    bar_label(ax, bars)

ax.set_title("Warm Latency — Client-side\n(hey, 50 sequential requests)")
ax.set_ylabel("ms")
ax.set_xticks(x)
ax.set_xticklabels(perc_labels)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
ax.legend()

# ── 4. Throughput ──────────────────────────────────────────────────────────────
ax = axes[3]
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

# ── save ───────────────────────────────────────────────────────────────────────
plt.tight_layout()
out = json_path.with_suffix(".png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"Saved {out}")
plt.show()
