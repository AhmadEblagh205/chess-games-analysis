"""Optional Stockfish inspection: finite-search centipawn evaluations and
large evaluation changes when a local engine binary is available.

Usage:
    python src/engine.py data/games/immortal_1851.pgn --stockfish /usr/bin/stockfish
"""
import argparse
from pathlib import Path

import chess.engine
import chess.pgn


def analyse(pgn_path: Path, engine_path: str, depth: int = 14):
    with pgn_path.open(encoding="utf-8") as fh:
        game = chess.pgn.read_game(fh)
    if game is None:
        raise ValueError(f"Could not parse PGN: {pgn_path}")
    board = game.board()
    with chess.engine.SimpleEngine.popen_uci(engine_path) as eng:
        prev = None
        for i, mv in enumerate(game.mainline_moves(), 1):
            san = board.san(mv)
            board.push(mv)
            info = eng.analyse(board, chess.engine.Limit(depth=depth))
            cp = info["score"].white().score(mate_score=10_000)
            tag = ""
            if prev is not None and abs(cp - prev) >= 150:
                tag = "  <- swing"
            print(f"{i:3d}. {san:<8} {cp:+5d} cp{tag}")
            prev = cp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pgn")
    ap.add_argument("--stockfish", default="stockfish")
    ap.add_argument("--depth", type=int, default=14)
    args = ap.parse_args()
    analyse(Path(args.pgn), args.stockfish, args.depth)


if __name__ == "__main__":
    main()
