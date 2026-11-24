"""Optional Stockfish move-quality audit for the bundled games.

The project previously called a plain arithmetic mean of per-move values
"Lichess accuracy".  Current Lichess game accuracy is more involved: it combines
a local-volatility-weighted arithmetic mean with a harmonic mean.  V2 ports that
aggregation in :mod:`accuracy_metrics` and reports the old arithmetic mean only
as an explicit diagnostic.

Usage:
    python src/accuracy.py --depth 10
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from accuracy_metrics import (
    accuracy_series_from_cp,
    aggregate_game_accuracy,
    lichess_win_percent,
)

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "data" / "games"


def find_stockfish() -> str | None:
    found = shutil.which("stockfish")
    if found:
        return found
    debian = Path("/usr/games/stockfish")
    return str(debian) if debian.exists() else None


def _signed_cp(info_score) -> float:
    """White-POV cp; mates become a large signed value then are clipped later."""
    value = info_score.white().score(mate_score=100_000)
    if value is None:
        raise ValueError("Engine score did not contain a cp/mate value")
    return float(value)


def game_accuracy(pgn_path: Path, engine, depth: int = 10) -> dict:
    with pgn_path.open(encoding="utf-8") as fh:
        game = chess.pgn.read_game(fh)
    if game is None:
        raise ValueError(f"Could not parse PGN: {pgn_path}")
    board = game.board()
    limit = chess.engine.Limit(depth=depth)
    post_move_cp: list[float] = []
    for move in game.mainline_moves():
        board.push(move)
        info = engine.analyse(board, limit)
        post_move_cp.append(_signed_cp(info["score"]))

    series = accuracy_series_from_cp(post_move_cp)
    faithful = {
        side: aggregate_game_accuracy(series[side], series[f"{side}_weights"])
        for side in ("white", "black")
    }
    arithmetic = {
        side: sum(series[side]) / len(series[side])
        for side in ("white", "black")
    }

    # Keep a transparent average loss diagnostic in win-percentage points.
    # This is not part of the Lichess aggregate itself.
    wp = [lichess_win_percent(15.0)] + [lichess_win_percent(x) for x in post_move_cp]
    losses = {"white": [], "black": []}
    for i, (before_w, after_w) in enumerate(zip(wp[:-1], wp[1:])):
        if i % 2 == 0:  # White moved
            losses["white"].append(max(before_w - after_w, 0.0))
        else:
            losses["black"].append(max((100 - before_w) - (100 - after_w), 0.0))

    return {
        "white": game.headers.get("White", "?"),
        "black": game.headers.get("Black", "?"),
        "white_game_accuracy": round(faithful["white"], 1),
        "black_game_accuracy": round(faithful["black"], 1),
        "white_mean_move_accuracy": round(arithmetic["white"], 1),
        "black_mean_move_accuracy": round(arithmetic["black"], 1),
        "white_avg_winpct_loss": round(sum(losses["white"]) / len(losses["white"]), 2),
        "black_avg_winpct_loss": round(sum(losses["black"]) / len(losses["black"]), 2),
        "plies": len(post_move_cp),
        "depth": depth,
        "metric_note": "game_accuracy uses current Lichess-style weighted/harmonic aggregation",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=10)
    args = ap.parse_args()
    if args.depth <= 0:
        raise SystemExit("--depth must be positive")
    binary = find_stockfish()
    if not binary:
        raise SystemExit(
            "No Stockfish found. Install a local Stockfish binary to regenerate "
            "engine metrics; the hand-evaluator analysis remains available."
        )
    results = []
    with chess.engine.SimpleEngine.popen_uci(binary) as engine:
        engine_id = dict(engine.id)
        for pgn in sorted(GAMES.glob("*.pgn")):
            results.append({"game": pgn.stem, **game_accuracy(pgn, engine, args.depth)})
    report = {
        "engine": engine_id,
        "engine_path": binary,
        "depth": args.depth,
        "metric": "Lichess-style game accuracy port audited 2026-09-16",
        "games": results,
    }
    out = ROOT / "reports" / "engine_accuracy.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for r in results:
        print(
            f"{r['game']:<26} {r['white']} {r['white_game_accuracy']}% "
            f"vs {r['black']} {r['black_game_accuracy']}%"
        )
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
