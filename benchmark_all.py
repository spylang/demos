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

# Pure-Python variants run under 3.15 to showcase interpreter progress; the
# numpy/numba variants need C-extension wheels, so they pin to a stable Python
# (3.13) that has prebuilt wheels on PyPI. Python variants use PEP 723 inline
# script metadata to pull in dependencies through `uv run`.
UV315 = ["uv", "run", "--python", "3.15"]
UV313 = ["uv", "run", "--python", "3.13"]

# Each entry is (label, cmd, n_frames, extra_env).
VARIANTS = [
    ("cpython3.15 (tx.py)",   UV315 + ["tx.py"],                                     10, {}),
    ("cpython3.15+JIT",       UV315 + ["tx.py"],                                     10, {"PYTHON_JIT": "1"}),
    ("numpy",                 UV313 + ["tx_numpy.py"],                              100, {}),
    ("pypy (tx.py)",          ["pypy", "tx.py"],                                    300, {}),
    ("numba",                 UV313 + ["tx_numba.py"],                              300, {}),
    ("spy --release",         ["spy", "build", "--release", "-x", "txspy.spy"],     300, {}),
]


def run(cmd, extra_env=None):
    devnull = open(os.devnull, "wb")
    env = None
    if extra_env:
        env = dict(os.environ)
        env.update(extra_env)
    proc = subprocess.run(cmd, stdout=devnull, stderr=subprocess.PIPE, env=env)
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
    for name, cmd, n, extra_env in VARIANTS:
        print("Running %s (n=%d) ..." % (name, n), flush=True)
        fps = run(cmd + ["-n", str(n)], extra_env=extra_env)
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
