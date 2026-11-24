"""Download your own games from the Lichess public API as PGN.

The endpoint needs no key for public games:
    https://lichess.org/api/games/user/<username>

Usage:
    python src/fetch_lichess.py <username> --max 300
"""
import argparse
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parents[1] / "data" / "my_games"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("--max", type=int, default=300)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    url = (f"https://lichess.org/api/games/user/{args.username}"
           f"?max={args.max}&opening=true&clocks=false&evals=false")
    req = Request(url, headers={"Accept": "application/x-chess-pgn",
                                "User-Agent": "chess-games-analysis"})
    dest = OUT / f"{args.username}.pgn"
    with urlopen(req) as fh:
        dest.write_bytes(fh.read())
    print(f"Saved -> {dest}  (split or analyse directly with "
          f"'python src/analysis.py --dir data/my_games')")


if __name__ == "__main__":
    main()
