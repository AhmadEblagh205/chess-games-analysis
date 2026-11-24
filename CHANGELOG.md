# Changelog

## 0.5.0 — defensibility audit

- Corrected the game-accuracy definition: v1 averaged per-move values, while current Lichess game accuracy combines a local-volatility-weighted mean and a harmonic mean.
- Added dependency-light `accuracy_metrics.py` with one documented centipawn/win-percentage mapping shared across the repository.
- Added a 500-world synthetic metric audit; the median absolute difference between current aggregation and a plain mean is 1.24 points (90th percentile 6.59), demonstrating that the two definitions are not interchangeable.
- Retired the old public `Morphy accuracy: 91.7` headline pending a fresh Stockfish run with the corrected metric.
- Corrected terminal draws to evaluate at zero rather than inheriting material/placement scores.
- Replaced hand-evaluator `?`/`??` NAGs with neutral `hand-swing` comments; a shallow transparent model no longer labels tactical sacrifices as objective blunders.
- Reframed the hand-evaluator win-probability curve as a heuristic transform, not calibrated probability.
- Changed bundled opening classification to prefer PGN ECO codes, with the small SAN-prefix dictionary only as fallback.
- Changed `fit_k` to equal-weight games rather than pseudo-replicating long games by raw position count; retained a clear dependence caveat.
- Preserved all pre-audit figures/results under `reports/legacy_v0_4/` and the old annotated PGNs under `data/legacy_v0_4_annotated/`.
- Expanded tests from 9 to 19 total definitions/integration checks (8 pure metric tests pass in the audit environment; the chess-dependent part requires `python-chess`).
- Fixed the documented Lichess-export workflow: multi-game PGN files are now fully iterated instead of silently analysing only the first game.
- Added `docs/METHODOLOGY.md` and explicit runtime-evidence boundaries.

## 0.4.0 — update round 9
Annotated PGN export with an evaluation comment per move and blunder marks netted over move plus reply. This behaviour is preserved only as historical output in v0.5 because the handcrafted evaluator is not strong enough to support objective NAG labels.

## 0.3.0 — update round 6
Engine move-quality audit using a Lichess-inspired per-move win-percentage-loss formula. The historical game aggregates are retained under `reports/legacy_v0_4/`; v0.5 corrects the game-level aggregation.

## 0.2.0 — update round 2
Added a centipawn-to-win-probability drama curve and a toy fitted logistic constant. V0.5 standardises the transform and makes the calibration limitation explicit.

## 0.1.0
Initial release.
