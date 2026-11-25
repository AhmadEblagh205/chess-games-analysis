# Chess Evaluation & Model-Audit Laboratory

[![CI](https://github.com/AhmadEblagh205/chess-games-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/chess-games-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

I built this because I wanted to understand why a chess position was scored the way it was, and not only receive a number from an engine. It has a hand-built evaluator (material, piece-square bonuses and mobility) that I can explain, and an optional Stockfish audit for move quality. The bundled games are four public-domain nineteenth-century games in PGN form.

## What it does

- scores positions with the hand evaluator and traces the score through each PGN, with an opening-family label and a list of large swings;
- writes neutral hand-evaluation comments into PGN files;
- measures Lichess-style move and game accuracy from Stockfish, if you have it installed;
- compares the Lichess game aggregation with a plain mean on simulated centipawn paths;
- downloads your own public games from Lichess and analyses every game in the file.

## Results

I have not rerun Stockfish since correcting the accuracy aggregation, so I do not quote a new player accuracy. The old figure of 91.7 for Morphy used a plain arithmetic mean, and it is kept in `reports/legacy_v0_4/` as historical only.

The current aggregation combines a volatility-weighted mean with a harmonic mean, as Lichess does. On 1,000 simulated player-games from 500 centipawn-path worlds, the median absolute difference from a plain mean is 1.24 accuracy points, the 90th percentile is 6.59, and 54.3% of cases differ by more than one point. This tests the metric definition and is not chess evidence. The output is in `reports/accuracy_metric_audit.json`.

## How to run

```bash
pip install -r requirements.txt
python src/analysis.py
python src/annotate.py

# Needs a local Stockfish binary
python src/accuracy.py --depth 10
python src/engine.py data/games/immortal_1851.pgn --stockfish /path/to/stockfish

# Your own Lichess games
python src/fetch_lichess.py your_username --max 300
python src/analysis.py --dir data/my_games

pytest -q
pytest -q tests/test_metrics.py   # metric definitions only, no python-chess needed
```

## Repository layout

```text
src/evaluate.py          hand evaluator
src/analysis.py          PGN trajectories and swing summaries
src/annotate.py          neutral hand-eval PGN annotations
src/accuracy_metrics.py  Lichess-style numerical definitions
src/accuracy.py          optional Stockfish game audit
src/metric_audit.py      simulated aggregation test
src/engine.py            per-position Stockfish inspection
src/fetch_lichess.py     public-game downloader
src/winprob.py           shared mapping and game-balanced toy fitter
reports/legacy_v0_4/     historical pre-audit outputs
```

## Notes

Stockfish is optional. The hand score is not a calibrated win probability, and its swings are changes in my model's score and not objective mistakes. The pure metric suite passed 8 of 8 in the audit environment. The full suite needs `python-chess`, which was not installed there, so CI is the check for it. Downloaded personal exports are ignored by git. The Lichess formulae, the stalemate fix and the other v0.5 changes are in docs/METHODOLOGY.md, and `reports/README.md` says which outputs are current.

## Licence

MIT, see [LICENSE](LICENSE). The bundled historical games are nineteenth-century games supplied as PGN records.
