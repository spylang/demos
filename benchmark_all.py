"""
Benchmark all texture-mapping variants headlessly.

Runs each variant with `-n N` frames, redirects stdout to /dev/null, and
measures wall-clock end-to-end FPS. Prints a table and writes a bar chart
to benchmark_all.png.
"""

import subprocess
import time
import sys
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Frame counts are per-variant so each run takes a few seconds — the pure-py
# version is much slower and gets a smaller N.
VARIANTS = [
    ("cpython (tx.py)",   ["python", "tx.py"],                                10),
    ("numpy",             ["python", "tx_numpy.py"],                         100),
    ("numba",             ["python", "tx_numba.py"],                         300),
    ("pypy (tx.py)",      ["pypy",   "tx.py"],                               300),
    ("spy --release",     ["spy", "build", "--release", "-x", "txspy.spy"],  500),
]


def run(cmd):
    devnull = open(os.devnull, "wb")
    proc = subprocess.run(cmd, stdout=devnull, stderr=subprocess.PIPE)
    devnull.close()
    if proc.returncode != 0:
        sys.stderr.write("FAILED: " + " ".join(cmd) + "\n")
        sys.stderr.write(proc.stderr.decode(errors="replace") + "\n")
        return None
    fps = None
    for line in proc.stderr.decode(errors="replace").splitlines():
        if line.startswith("FPS:"):
            fps = float(line.split(":", 1)[1].strip())
    if fps is None:
        sys.stderr.write("no FPS line from: " + " ".join(cmd) + "\n")
        sys.stderr.write(proc.stderr.decode(errors="replace") + "\n")
    return fps


def main():
    results = []
    for name, cmd, n in VARIANTS:
        print("Running %s (n=%d) ..." % (name, n), flush=True)
        fps = run(cmd + ["-n", str(n)])
        results.append((name, fps))
        if fps is not None:
            print("  %.2f FPS" % fps)

    print()
    print("%-20s %10s" % ("variant", "FPS"))
    print("-" * 32)
    for name, fps in results:
        if fps is None:
            print("%-20s %10s" % (name, "FAILED"))
        else:
            print("%-20s %10.2f" % (name, fps))

    names = [n for n, f in results if f is not None]
    fps = [f for _, f in results if f is not None]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(names, fps, color="steelblue")
    ax.set_ylabel("FPS (higher is better)")
    ax.set_title("Texture-mapping demo — headless FPS")
    for bar, v in zip(bars, fps):
        ax.text(bar.get_x() + bar.get_width() / 2, v, "%.1f" % v,
                ha="center", va="bottom")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    out = "benchmark_all.png"
    plt.savefig(out, dpi=110)
    print("\nChart written to %s" % out)


main()
