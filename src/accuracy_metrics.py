"""Pure numerical helpers for Stockfish-evaluation accuracy metrics.

This module intentionally has no ``python-chess`` dependency, which makes the
metric definitions easy to test in isolation.

The win-percentage transform and move-accuracy curve follow the current
Lichess public implementation (audited September 2026).  The game aggregate is
also ported from Lichess: it averages a local-volatility-weighted mean and a
harmonic mean of move accuracies.  This is *not* the same as taking the simple
arithmetic mean of per-move accuracies.

Lichess source references:
- https://lichess.org/page/accuracy
- https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/AccuracyPercent.scala
- https://github.com/lichess-org/scalachess/blob/master/core/src/main/scala/eval.scala
"""
from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Iterable, Sequence

CP_CEILING = 1000.0
INITIAL_CP = 15.0
WIN_MULTIPLIER = 0.00368208


def lichess_win_percent(cp: float) -> float:
    """Map centipawns (White POV) to Lichess-style win percentage [0, 100].

    Current Lichess ceils centipawn evaluations to +/-1000 before applying the
    logistic map.  Mate scores should therefore be converted to the appropriate
    signed ceiling by the caller rather than treated as +/-10000 cp.
    """
    x = max(-CP_CEILING, min(CP_CEILING, float(cp)))
    return 100.0 / (1.0 + math.exp(-WIN_MULTIPLIER * x))


def move_accuracy(win_before: float, win_after: float, *, uncertainty_bonus: bool = True) -> float:
    """Current Lichess-style move accuracy from mover win percentages.

    Improvements are never penalised.  The current Lichess implementation adds
    a one-point uncertainty bonus after the exponential curve; that behaviour is
    enabled by default here and documented rather than hidden.
    """
    if win_after >= win_before:
        return 100.0
    drop = win_before - win_after
    raw = 103.1668100711649 * math.exp(-0.04354415386753951 * drop) - 3.166924740191411
    if uncertainty_bonus:
        raw += 1.0
    return max(0.0, min(100.0, raw))


def _weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    return sum(v * w for v, w in zip(values, weights)) / total


def _harmonic_mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot aggregate an empty move list")
    # Lichess accuracies are clamped to [0,100]. A zero accuracy makes the
    # harmonic mean zero, which is the limiting value and avoids division by 0.
    if any(v <= 0 for v in values):
        return 0.0
    return len(values) / sum(1.0 / v for v in values)


def _volatility_weights(win_percents: Sequence[float]) -> list[float]:
    """Port the local-win-percentage volatility weights used by Lichess."""
    n_moves = len(win_percents) - 1
    if n_moves <= 0:
        return []
    window = max(2, min(8, n_moves // 10))
    window = min(window, len(win_percents))
    windows: list[Sequence[float]] = []
    # Alignment copied from Lichess: repeat the first full window for the early
    # moves, then slide it, yielding exactly one weight per move.
    for _ in range(max(window - 2, 0)):
        windows.append(win_percents[:window])
    windows.extend(win_percents[i:i + window]
                   for i in range(len(win_percents) - window + 1))
    weights = [max(0.5, min(12.0, pstdev(w))) for w in windows]
    if len(weights) != n_moves:
        raise AssertionError((len(weights), n_moves, window, len(win_percents)))
    return weights


def accuracy_series_from_cp(post_move_cp: Sequence[float], *, start_white: bool = True,
                            initial_cp: float = INITIAL_CP) -> dict[str, list[float]]:
    """Return move accuracies/weights by colour from post-move White-POV cp.

    ``post_move_cp[i]`` is the engine evaluation after ply ``i+1``.  Mates should
    already be mapped to a large signed value; ``lichess_win_percent`` will cap
    the result at the current +/-1000 cp ceiling.
    """
    if not post_move_cp:
        return {"white": [], "black": [], "white_weights": [], "black_weights": []}
    wp = [lichess_win_percent(initial_cp)] + [lichess_win_percent(x) for x in post_move_cp]
    weights = _volatility_weights(wp)
    out = {"white": [], "black": [], "white_weights": [], "black_weights": []}
    for i, (before_w, after_w, weight) in enumerate(zip(wp[:-1], wp[1:], weights)):
        white_moved = (i % 2 == 0) == bool(start_white)
        if white_moved:
            before, after, key = before_w, after_w, "white"
        else:
            before, after, key = 100.0 - before_w, 100.0 - after_w, "black"
        out[key].append(move_accuracy(before, after))
        out[f"{key}_weights"].append(weight)
    return out


def aggregate_game_accuracy(move_accuracies: Sequence[float], weights: Sequence[float]) -> float:
    """Lichess-style game aggregate for one player's moves.

    It is the mean of the local-volatility-weighted arithmetic mean and the
    harmonic mean.  This intentionally differs from a plain arithmetic mean.
    """
    if len(move_accuracies) != len(weights):
        raise ValueError("accuracy and weight lengths differ")
    if not move_accuracies:
        raise ValueError("cannot aggregate an empty move list")
    weighted = _weighted_mean(move_accuracies, weights)
    harmonic = _harmonic_mean(move_accuracies)
    return 0.5 * (weighted + harmonic)


def game_accuracy_from_cp(post_move_cp: Sequence[float], *, start_white: bool = True,
                          initial_cp: float = INITIAL_CP) -> dict[str, float]:
    """Return current Lichess-style game accuracy for both colours."""
    s = accuracy_series_from_cp(post_move_cp, start_white=start_white, initial_cp=initial_cp)
    return {
        "white": aggregate_game_accuracy(s["white"], s["white_weights"]),
        "black": aggregate_game_accuracy(s["black"], s["black_weights"]),
    }


def simple_mean_accuracy_from_cp(post_move_cp: Sequence[float], *, start_white: bool = True,
                                 initial_cp: float = INITIAL_CP) -> dict[str, float]:
    """Legacy-style arithmetic mean retained only for an audit comparison."""
    s = accuracy_series_from_cp(post_move_cp, start_white=start_white, initial_cp=initial_cp)
    return {
        "white": fmean(s["white"]),
        "black": fmean(s["black"]),
    }
