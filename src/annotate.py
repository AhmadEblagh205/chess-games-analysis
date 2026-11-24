"""Annotated PGN export using the transparent hand evaluator.

V1 wrote standard chess ``?``/``??`` NAGs from a shallow handcrafted evaluator.
Those glyphs imply objective move-quality judgments the model cannot support,
especially in tactical sacrifices.  V2 therefore writes evaluation comments and
neutral ``hand-swing`` diagnostics only.  Objective blunder labels require the
optional Stockfish path.
"""
from pathlib import Path

import chess
import chess.pgn

from evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "data" / "games"
OUT = ROOT / "data" / "games_annotated"


def annotate_game(pgn_path: Path, swing_threshold: int = 200) -> chess.pgn.Game:
    with pgn_path.open(encoding="utf-8") as fh:
        game = chess.pgn.read_game(fh)
    if game is None:
        raise ValueError(f"Could not parse PGN: {pgn_path}")
    nodes = list(game.mainline())
    board = game.board()
    evals = [evaluate(board)]
    movers = []
    for node in nodes:
        movers.append(board.turn)
        board.push(node.move)
        evals.append(evaluate(board))
    for i, node in enumerate(nodes):
        after = evals[i + 1]
        node.comment = f"[%eval {after / 100:.2f}] [hand-eval]"
        # Keep a neutral two-ply swing diagnostic for pedagogy, but do not map
        # it to NAG_MISTAKE/NAG_BLUNDER. Tactical sacrifices are exactly where
        # this model is weakest.
        end = min(i + 2, len(evals) - 1)
        delta_white = evals[end] - evals[i]
        mover_delta = delta_white if movers[i] == chess.WHITE else -delta_white
        if mover_delta <= -swing_threshold:
            node.comment += f" [hand-swing {mover_delta:+d}cp over <=2 plies]"
    return game


def main():
    OUT.mkdir(exist_ok=True)
    for pgn in sorted(GAMES.glob("*.pgn")):
        game = annotate_game(pgn)
        dest = OUT / f"{pgn.stem}_annotated.pgn"
        dest.write_text(str(game) + "\n", encoding="utf-8")
        flagged = sum("hand-swing" in n.comment for n in game.mainline())
        print(f"{dest.name}: {flagged} neutral hand-eval swings flagged")


if __name__ == "__main__":
    main()
