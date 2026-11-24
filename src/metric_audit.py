"""Dependency-light audit showing why game accuracy is not a plain mean.

This experiment is synthetic.  It does not claim anything about the bundled
historical games; it demonstrates the metric-definition correction made in v2.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from accuracy_metrics import game_accuracy_from_cp, simple_mean_accuracy_from_cp

ROOT = Path(__file__).resolve().parents[1]


def simulate_eval_paths(n_worlds: int = 500, n_plies: int = 60, seed: int = 16):
    rng = np.random.default_rng(seed)
    rows = []
    for world in range(n_worlds):
        cp = 15.0
        path = []
        for ply in range(n_plies):
            # Mostly small moves with occasional tactical shocks.  This is only
            # a metric stress test, not a chess-position generator.
            shock = rng.normal(0, 45)
            if rng.random() < 0.07:
                shock += rng.normal(0, 300)
            cp = 0.92 * cp + shock
            path.append(float(cp))
        current = game_accuracy_from_cp(path)
        legacy = simple_mean_accuracy_from_cp(path)
        rows.append({
            "world": world,
            "white_current": current["white"],
            "white_plain_mean": legacy["white"],
            "white_difference": current["white"] - legacy["white"],
            "black_current": current["black"],
            "black_plain_mean": legacy["black"],
            "black_difference": current["black"] - legacy["black"],
        })
    return rows


def main():
    rows = simulate_eval_paths()
    diffs = np.array([r[c] for r in rows for c in ("white_difference", "black_difference")])
    report = {
        "experiment": "synthetic centipawn-path metric audit; not chess performance",
        "worlds": len(rows),
        "players": len(diffs),
        "median_current_minus_plain_mean": float(np.median(diffs)),
        "median_absolute_difference": float(np.median(np.abs(diffs))),
        "p90_absolute_difference": float(np.quantile(np.abs(diffs), 0.9)),
        "max_absolute_difference": float(np.max(np.abs(diffs))),
        "fraction_abs_difference_over_1_point": float(np.mean(np.abs(diffs) > 1.0)),
        "conclusion": "plain arithmetic mean and current Lichess-style game aggregation are not interchangeable",
    }
    reports = ROOT / "reports"
    figures = reports / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    (reports / "accuracy_metric_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.hist(diffs, bins=40)
    ax.axvline(0, lw=1)
    ax.set(
        xlabel="Current Lichess-style aggregate - plain mean (accuracy points)",
        ylabel="Synthetic player-games",
        title="Game-accuracy aggregation is not a plain arithmetic mean",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "accuracy_aggregation_audit.png", dpi=160)
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
