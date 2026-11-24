"""Centipawn-to-win-percentage helpers.

The repository previously used a separate ad-hoc logistic constant (~0.004)
for the hand evaluator while ``accuracy.py`` used the Lichess transform.  V2
uses one documented mapping everywhere so a centipawn number has one meaning.

Important: applying this mapping to the hand-built evaluator is a visualisation
heuristic, not a calibrated probability model.  The mapping was derived for
Stockfish evaluations, not for this project's material/placement/mobility score.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from accuracy_metrics import lichess_win_percent

DEFAULT_K = 0.00368208


def win_probability(cp: float) -> float:
    """Lichess-style win percentage expressed on [0,1]."""
    return lichess_win_percent(cp) / 100.0


def fit_k(position_cps: Sequence[Sequence[float]], results: Sequence[float],
          k_grid=None) -> float:
    """Toy game-balanced calibration utility for large personal exports.

    Every game contributes equal total weight, so a 100-ply game does not count
    twice as much as a 50-ply game merely because it has more correlated
    positions.  Positions within a game are still dependent; this utility is a
    diagnostic, not a statistically independent observation model.
    """
    import numpy as np
    if len(position_cps) != len(results) or not position_cps:
        raise ValueError("position_cps and results must contain the same non-zero number of games")
    k_grid = k_grid if k_grid is not None else np.linspace(0.001, 0.01, 91)
    best_k, best_ll = float(k_grid[0]), -np.inf
    for k in k_grid:
        game_ll = []
        for cps, result in zip(position_cps, results):
            if not cps:
                continue
            arr = np.clip(np.asarray(cps, dtype=float), -1000, 1000)
            p = 1 / (1 + np.exp(-float(k) * arr))
            p = np.clip(p, 1e-9, 1 - 1e-9)
            y = float(result)
            # Each game contributes its mean position log-loss, preventing
            # long games from dominating simply through pseudo-replication.
            ll = y * np.log(p) + (1 - y) * np.log(1 - p)
            game_ll.append(float(np.mean(ll)))
        if not game_ll:
            raise ValueError("no positions supplied")
        total = float(np.mean(game_ll))
        if total > best_ll:
            best_k, best_ll = float(k), total
    return best_k
