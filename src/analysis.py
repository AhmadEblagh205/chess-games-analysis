"""Analyse PGN games with a transparent hand-built evaluator.

The hand score is useful for explaining material/placement/mobility, but it is
not a calibrated engine evaluation.  V2 therefore calls large changes
``hand-eval swings`` rather than objective blunders and labels the win-probability
view as a heuristic transform.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
import chess.pgn
import matplotlib.pyplot as plt

from evaluate import evaluate, material
from winprob import win_probability

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "reports" / "figures"

OPENINGS = {
    ("e4", "e5", "Nf3", "Nc6", "Bc4"): "Italian Game",
    ("e4", "e5", "Nf3", "Nc6", "Bb5"): "Ruy Lopez",
    ("e4", "e5", "Nf3", "d6"): "Philidor Defence",
    ("e4", "e5", "f4"): "King's Gambit",
    ("e4", "c5"): "Sicilian Defence",
    ("e4", "e5", "Nf3", "Nc6", "Nc3", "Nf6"): "Four Knights",
    ("d4", "d5"): "Queen's Pawn Game",
}

# Coarse labels for the four bundled examples. ECO takes priority because it is
# robust to transpositions in a way a tiny SAN-prefix dictionary is not.
ECO_LABELS = {
    "C33": "King's Gambit",
    "C41": "Philidor Defence",
    "C48": "Four Knights",
    "C52": "Italian Game",
}


def opening_name(sans: list[str], eco: str | None = None) -> str:
    if eco and eco in ECO_LABELS:
        return ECO_LABELS[eco]
    for prefix in sorted(OPENINGS, key=len, reverse=True):
        if tuple(sans[:len(prefix)]) == prefix:
            return OPENINGS[prefix]
    return "Other"


def trace_game(game: chess.pgn.Game):
    board = game.board()
    evals, mats, sans = [evaluate(board)], [material(board)], []
    for mv in game.mainline_moves():
        sans.append(board.san(mv))
        board.push(mv)
        evals.append(evaluate(board))
        mats.append(material(board))
    return evals, mats, sans


def swings(evals: list[int], threshold: int = 250):
    """Large absolute changes in the transparent hand evaluator."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    return [(i, evals[i] - evals[i - 1])
            for i in range(1, len(evals))
            if abs(evals[i] - evals[i - 1]) >= threshold]


def read_games(path: Path):
    """Read every game from a PGN file, validating parser errors.

    Lichess exports commonly contain many games in one file. V1 called
    ``read_game`` once per file, so the documented personal-export workflow
    silently analysed only the first game.
    """
    with path.open(encoding="utf-8") as fh:
        found = False
        while True:
            game = chess.pgn.read_game(fh)
            if game is None:
                break
            found = True
            if game.errors:
                raise ValueError(f"PGN parse errors in {path}: {game.errors}")
            yield game
    if not found:
        raise ValueError(f"Could not parse any PGN games: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=ROOT / "data" / "games")
    ap.add_argument("--swing", type=int, default=250)
    args = ap.parse_args()
    files = sorted(Path(args.dir).glob("*.pgn"))
    if not files:
        raise SystemExit(f"No PGN files in {args.dir}")

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    fig2, ax2 = plt.subplots(figsize=(9.5, 4.6))
    fig3, ax3 = plt.subplots(figsize=(9.5, 4.6))
    summary = []

    for f in files:
        for game_index, game in enumerate(read_games(f), 1):
            evals, mats, sans = trace_game(game)
            if not sans:
                continue
            sw = swings(evals, args.swing)
            white = game.headers.get("White", "?").split(",")[0]
            black = game.headers.get("Black", "?").split(",")[0]
            label = f"{white} v {black} {game.headers.get('Date', '')[:4]}"
            plies = range(len(evals))
            # Heuristic only: the Lichess logistic was calibrated for engine cp, not
            # for our handcrafted score.
            wps = [win_probability(e) for e in evals]
            ax.plot(plies, [e / 100 for e in evals], lw=1.6, label=label)
            ax2.plot(plies, [m / 100 for m in mats], lw=1.6, label=label)
            ax3.plot(plies, wps, lw=1.6, label=label)
            wp_jumps = [abs(wps[i] - wps[i - 1]) for i in range(1, len(wps))]
            drama_ply = int(max(range(len(wp_jumps)), key=wp_jumps.__getitem__)) + 1
            non_terminal = [t for t in sw if t[0] < len(sans)] or sw
            biggest = max(non_terminal, key=lambda t: abs(t[1]), default=None)
            if biggest:
                i, _ = biggest
                ax.annotate(sans[i - 1], (i, evals[i] / 100), fontsize=7.5,
                            xytext=(4, 6), textcoords="offset points")
            summary.append({
                "file": f.name,
                "game_index_in_file": game_index,
                "white": white,
                "black": black,
                "result": game.headers.get("Result"),
                "eco": game.headers.get("ECO"),
                "opening": opening_name(sans, game.headers.get("ECO")),
                "plies": len(sans),
                "hand_eval_swings": len(sw),
                "biggest_hand_eval_swing_cp": biggest[1] if biggest else 0,
                "biggest_hand_eval_swing_move": sans[biggest[0] - 1] if biggest else None,
                "largest_heuristic_probability_jump_move": sans[drama_ply - 1],
                "heuristic_probability_change": round(wps[drama_ply] - wps[drama_ply - 1], 3),
                "final_hand_eval_cp": evals[-1],
                "probability_warning": "Lichess logistic applied to hand evaluation; not calibrated",
            })

    for a, ylab, title, name in [
        (ax, "Hand evaluation (pawns, White +)",
         "Transparent hand evaluation through the game", "eval_curves.png"),
        (ax2, "Material (pawns, White +)",
         "Material balance through the game", "material_curves.png"),
    ]:
        a.axhline(0, color="grey", lw=0.8)
        a.set(xlabel="Ply", ylabel=ylab, title=title)
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    ax3.axhline(0.5, color="grey", lw=0.8)
    ax3.set(xlabel="Ply", ylabel="Heuristic P(White wins)",
            title="Lichess logistic applied to the hand score (not calibrated)")
    ax3.set_ylim(-0.02, 1.02)
    ax3.legend(fontsize=8)
    ax3.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIGURES / "eval_curves.png", dpi=150)
    fig2.tight_layout(); fig2.savefig(FIGURES / "material_curves.png", dpi=150)
    fig3.tight_layout(); fig3.savefig(FIGURES / "heuristic_winprob_curves.png", dpi=150)
    plt.close("all")

    out = ROOT / "reports" / "games_summary.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for s in summary:
        print(f"{s['white']:>10} v {s['black']:<20} {s['result']}  "
              f"{s['opening']:<18} hand-swings {s['hand_eval_swings']}")
    print(f"\nSaved -> {out}\nFigures -> {FIGURES}")


if __name__ == "__main__":
    main()
