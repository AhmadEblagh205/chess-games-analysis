# Methodology and audit notes

## 1. Two different modelling goals

This repository intentionally separates **interpretability** from **playing strength**.

The hand evaluator is a deterministic explanatory model:

\[
E(s)=M(s)+P(s)+2\{L_W(s)-L_B(s)\},
\]

where `M` is material in centipawns, `P` is the piece-square contribution and `L_W-L_B` is the difference in hypothetical legal-move counts. It contains no search tree. A tactical sacrifice can therefore look bad locally even when it is objectively winning.

Stockfish is an optional external reference evaluator. Its numbers are not treated as ground truth about human strength; they are search-engine evaluations at a declared depth/configuration.

## 2. Terminal-state correction

V1 only returned a special value for checkmate. V2 returns zero for any other terminal drawn position. A stalemate is a draw regardless of who owns more material.

## 3. Centipawns to win percentage

The repository now uses the current Lichess mapping consistently:

\[
WP(cp)=\frac{100}{1+\exp(-0.00368208\,\mathrm{clip}(cp,-1000,1000))}.
\]

Public references:

- <https://lichess.org/page/accuracy>
- <https://github.com/lichess-org/scalachess/blob/master/core/src/main/scala/eval.scala>

Applying this function to the hand evaluator is **not** calibration. It is only a monotonic visual transform. The mapping was designed around engine centipawns.

## 4. Move accuracy

For a mover whose win percentage falls from `before` to `after`, current Lichess uses an exponential curve of the loss; moves that do not reduce win percentage receive 100. The current source also applies a one-point uncertainty bonus before clipping to [0,100]. The implementation in `accuracy_metrics.py` follows the source audited in September 2026:

<https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/AccuracyPercent.scala>

Because upstream implementations can change, generated reports should record repository version/date rather than claiming eternal identity with Lichess.

## 5. Game-level accuracy correction

V1 simply averaged per-move accuracies. Current Lichess game accuracy does not.

For each player, local win-percentage volatility creates a bounded weight (0.5 to 12). Lichess combines:

1. the volatility-weighted arithmetic mean of move accuracy; and
2. the harmonic mean of move accuracy.

The game result is the mean of those two aggregates.

`metric_audit.py` demonstrates on synthetic centipawn paths that the arithmetic and current aggregates are not interchangeable. That experiment is about metric definition only; the paths are not legal chess positions.

## 6. Why the old Morphy 91.7% headline is retired

`reports/legacy_v0_4/engine_accuracy.json` used the old repository implementation: the correct general idea of win-percentage loss per move, but a plain arithmetic game mean and an earlier move formula. It is retained for provenance, not published as current Lichess game accuracy.

A fresh Stockfish run under v0.5 is required before publishing a new player-accuracy headline. The report should state at minimum:

- Stockfish version;
- search depth/nodes/time limit;
- relevant engine options/threads/hash if changed;
- repository commit/version;
- metric implementation date.

## 7. PGN annotation policy

The hand evaluator may annotate its own score, but it does not assign standard NAG `?` or `??` labels. Those glyphs look like objective chess judgments. V2 uses neutral `hand-swing` comments instead.

This is a general modelling principle: **a model can report what its own score did without claiming that the score is truth**.

## 8. Opening labels

The bundled files contain ECO codes. V2 uses a small ECO mapping for those examples, then falls back to SAN-prefix matching for user games. This is deliberately lightweight; a production opening classifier should use a transposition-aware opening database such as the public Lichess opening dataset.

## 9. Win-probability constant fitting

`fit_k` remains a small educational diagnostic. V1 treated every position as an independent observation, so long games received more weight and the likelihood pseudo-replicated highly dependent within-game positions.

V2 first averages position log likelihood within each game, then averages across games. This removes pure game-length weighting, but it **does not make positions independent**. A serious calibration study would need many games, a declared sampling design and uncertainty estimates clustered at game/player level.

## 10. Current evidence boundary

The September 2026 audit environment did not contain `python-chess` or Stockfish, and package installation was unavailable. Therefore:

- the dependency-light metric layer was executed: **8 tests passed**;
- all Python source files compile syntactically;
- chess-dependent code was inspected and expanded but awaits CI/local execution with declared dependencies;
- old Stockfish and hand-analysis outputs are retained under `reports/legacy_v0_4/`, never silently presented as regenerated v0.5 evidence.


## 11. Multi-game PGN exports

Lichess user exports commonly contain many games in one PGN file. V1 iterated over files but called `read_game` once per file, so the documented `fetch_lichess.py -> analysis.py` workflow silently analysed only the first game. V2 reads until EOF and validates every parsed game.
