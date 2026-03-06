#!/usr/bin/env -S uv run
# /// script
# dependencies = ["matplotlib", "numpy"]
# ///
"""
Read benchmark_results.json and produce two PNG files:
  - spy_fastapi.png      (2-way comparison)
  - spy_go_rust.png      (3-way comparison)

Each PNG has three charts:
  1. Cold start breakdown (stacked bar)
  2. Warm latency server-side percentiles (grouped bar)
  3. Throughput (bar + req/sec annotation)
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import matplotlib.colors as mcolors

BG     = "#ffffff"
CARD_BG = "#f8fafc"
TEXT   = "#0f172a"
MUTED  = "#64748b"
GRID   = "#cbd5e1"

LABELS = {"spy": "SPy", "fastapi": "FastAPI", "go": "Go", "rust": "Rust"}

# Stable positions in the default color cycle.
# go shares C1 (orange) with fastapi — they never appear in the same plot.
# rust uses C3 (red) as the third colour in the spy/go/rust comparison.
_COLOR_IDX = {"spy": 0, "fastapi": 1, "go": 1, "rust": 3}

def color(fn):
    return f"C{_COLOR_IDX[fn]}"

def dark(fn):
    """Darker shade of the base color for stacked-bar segments."""
    rgba = np.array(mcolors.to_rgba(color(fn)))
    rgba[:3] *= 0.6
    return rgba

# ── load data ──────────────────────────────────────────────────────────────────
json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("benchmark_results.json")
with json_path.open() as f:
    d = json.load(f)

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


def bar_label(ax, bars):
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + ax.get_ylim()[1] * 0.01,
            f"{h:.1f}",
            ha="center", va="bottom", fontsize=8, color=TEXT,
        )


def baseline_label(ax, fns, values, baseline_fn, higher_is_better=False):
    """Multi-line label comparing each fn to baseline_fn."""
    if baseline_fn not in fns:
        return
    base_val = values[fns.index(baseline_fn)]
    if base_val == 0:
        return
    lines = [f"{LABELS[baseline_fn]}: baseline"]
    for f in fns:
        if f == baseline_fn or values[fns.index(f)] == 0:
            continue
        r = values[fns.index(f)] / base_val   # other / baseline
        if higher_is_better:
            desc = f"{r:.1f}× faster" if r > 1 else f"{1/r:.1f}× slower"
        else:
            desc = f"{1/r:.1f}× faster" if r < 1 else f"{r:.1f}× slower"
        lines.append(f"{LABELS[f]}: {desc}")
    c = color(baseline_fn)
    ax.text(0.5, -0.13, "\n".join(lines),
            transform=ax.transAxes,
            ha="center", va="top", fontsize=9, fontweight="bold",
            color=c, clip_on=False,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=c, linewidth=1.2))


def speedup_label(ax, ratio, fn, suffix):
    if ratio is None:
        return
    c = color(fn)
    text = f"{LABELS[fn]}: {ratio:.1f}× {suffix}"
    ax.text(0.5, -0.13, text,
            transform=ax.transAxes,
            ha="center", va="top", fontsize=9, fontweight="bold",
            color=c, clip_on=False,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=c, linewidth=1.2))


def make_figure(*fns):
    """Generate a 3-chart comparison figure for the given implementations."""
    title = " vs ".join(LABELS[f] for f in fns)
    n_fns = len(fns)
    # Bar width scales down as more series are added
    w = min(0.5, 0.8 / n_fns)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle(
        f"{title} — AWS Lambda Benchmark\n{d['timestamp']}",
        fontsize=13, color=TEXT, y=1.02,
    )

    # ── 1. Cold start ──────────────────────────────────────────────────────────
    ax = axes[0]
    x = np.arange(n_fns)

    init_vals    = [d[f]["cold_start"]["init_ms"]    for f in fns]
    handler_vals = [d[f]["cold_start"]["handler_ms"] for f in fns]
    totals       = [i + h for i, h in zip(init_vals, handler_vals)]

    bars = ax.bar(x, totals, w, color=[color(f) for f in fns])
    bar_label(ax, bars)

    ax.set_title("Cold Start\n(init + first handler)")
    ax.set_ylabel("ms")
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[f] for f in fns])
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    if "rust" in fns and len(fns) > 2:
        baseline_label(ax, fns, totals, "rust", higher_is_better=False)
    else:
        best_fn  = fns[totals.index(min(totals))]
        worst_fn = fns[totals.index(max(totals))]
        if totals[fns.index(best_fn)] > 0 and best_fn != worst_fn:
            ratio = totals[fns.index(worst_fn)] / totals[fns.index(best_fn)]
            speedup_label(ax, ratio, best_fn, "faster cold start")

    # ── 2. Warm latency – server-side (CloudWatch) ────────────────────────────
    ax = axes[1]
    percentiles = ["p50_ms", "p95_ms", "max_ms"]
    perc_labels = ["p50", "p95", "max"]
    x = np.arange(len(percentiles))
    offsets = np.linspace(-(n_fns - 1) / 2, (n_fns - 1) / 2, n_fns) * w

    for offset, fn in zip(offsets, fns):
        vals = [d[fn]["warm_latency"]["server"][p] for p in percentiles]
        bars = ax.bar(x + offset, vals, w, label=LABELS[fn], color=color(fn))
        bar_label(ax, bars)

    ax.set_title("Warm Latency — Server-side\n(CloudWatch Duration)")
    ax.set_ylabel("ms")
    ax.set_xticks(x)
    ax.set_xticklabels(perc_labels)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend()

    p50s = [d[f]["warm_latency"]["server"]["p50_ms"] for f in fns]
    if "rust" in fns and len(fns) > 2:
        baseline_label(ax, fns, p50s, "rust", higher_is_better=False)
    else:
        best_p50_fn  = fns[p50s.index(min(p50s))]
        worst_p50_fn = fns[p50s.index(max(p50s))]
        if p50s[fns.index(best_p50_fn)] > 0 and best_p50_fn != worst_p50_fn:
            ratio = p50s[fns.index(worst_p50_fn)] / p50s[fns.index(best_p50_fn)]
            speedup_label(ax, ratio, best_p50_fn, "lower p50")

    # ── 3. Throughput ──────────────────────────────────────────────────────────
    ax = axes[2]
    rps_vals = [d[fn]["throughput"]["requests_per_sec"] for fn in fns]
    bars = ax.bar(
        [LABELS[fn] for fn in fns], rps_vals,
        color=[color(fn) for fn in fns], width=w,
    )

    for bar, val in zip(bars, rps_vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + ax.get_ylim()[1] * 0.01,
                f"{val:.0f} req/s",
                ha="center", va="bottom", fontsize=9, color=TEXT, fontweight="bold")

    n_req = d["config"]["throughput_n"]
    c_req = d["config"]["throughput_c"]
    ax.set_title(f"Throughput\n({n_req} requests, concurrency {c_req})")
    ax.set_ylabel("requests / sec")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    if "rust" in fns and len(fns) > 2:
        baseline_label(ax, fns, rps_vals, "rust", higher_is_better=True)
    else:
        best_rps_fn  = fns[rps_vals.index(max(rps_vals))]
        worst_rps_fn = fns[rps_vals.index(min(rps_vals))]
        if rps_vals[fns.index(worst_rps_fn)] > 0 and best_rps_fn != worst_rps_fn:
            ratio = rps_vals[fns.index(best_rps_fn)] / rps_vals[fns.index(worst_rps_fn)]
            speedup_label(ax, ratio, best_rps_fn, "more req/s")

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)
    return fig


# ── generate and save both figures ─────────────────────────────────────────────
comparisons = [
    ("spy", "fastapi"),
    ("spy", "go", "rust"),
]

for fns in comparisons:
    if any(f not in d for f in fns):
        missing = [f for f in fns if f not in d]
        print(f"Skipping {' vs '.join(fns)}: {missing} not found in {json_path}")
        continue
    fig = make_figure(*fns)
    stem = "_".join(fns)
    out = json_path.with_name(f"{stem}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"Saved {out}")
    plt.close(fig)
