# Report provenance

`accuracy_metric_audit.json` and `figures/accuracy_aggregation_audit.png` are current v0.5 outputs. They come from a synthetic metric-definition stress test and are **not chess-performance results**.

`legacy_v0_4/` contains historical outputs from the pre-audit repository. In particular, `engine_accuracy.json` used a plain arithmetic mean of per-move accuracies rather than the current Lichess game aggregate. The old Morphy/Anderssen headline percentages must not be quoted as current v0.5 evidence.

A fresh local/CI run with `python-chess` regenerates hand-evaluator outputs. A fresh Stockfish run is additionally required before publishing new engine-accuracy numbers.
