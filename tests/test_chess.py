import pytest
chess = pytest.importorskip("chess")
import chess.pgn

from analysis import opening_name, read_games, swings, trace_game
from evaluate import evaluate, material


def _game(path):
    with open(path, encoding="utf-8") as fh:
        game = chess.pgn.read_game(fh)
    assert game is not None
    assert not game.errors
    return game


def test_start_position_is_balanced():
    board = chess.Board()
    assert material(board) == 0
    assert evaluate(board) == 0


def test_evaluation_is_colour_symmetric():
    board = chess.Board("4k3/8/8/8/8/8/PPP5/4K3 w - - 0 1")
    mirror = chess.Board("4k3/ppp5/8/8/8/8/8/4K3 w - - 0 1")
    assert evaluate(board) == -evaluate(mirror)


def test_terminal_draw_is_zero():
    # Stalemate: black to move, no legal move, not in check.
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()
    assert evaluate(board) == 0


def test_checkmate_dominates():
    game = _game("data/games/opera_1858.pgn")
    evals, _, sans = trace_game(game)
    assert evals[-1] == 10_000
    assert sans[-1].endswith("#")


def test_all_bundled_games_parse_without_errors_and_are_legal():
    from pathlib import Path
    for p in sorted(Path("data/games").glob("*.pgn")):
        game = _game(p)
        board = game.board()
        for move in game.mainline_moves():
            assert move in board.legal_moves
            board.push(move)



def test_multi_game_pgn_reader_handles_lichess_style_exports(tmp_path):
    one = open("data/games/opera_1858.pgn", encoding="utf-8").read()
    two = open("data/games/immortal_1851.pgn", encoding="utf-8").read()
    path = tmp_path / "export.pgn"
    path.write_text(one + "\n\n" + two, encoding="utf-8")
    games = list(read_games(path))
    assert len(games) == 2
    assert games[0].headers["Event"].startswith("Paris Opera")
    assert "Immortal" in games[1].headers["Event"]

def test_swing_detector_finds_large_hand_eval_changes():
    game = _game("data/games/immortal_1851.pgn")
    evals, _, _ = trace_game(game)
    sw = swings(evals, threshold=250)
    assert len(sw) >= 3
    assert all(abs(delta) >= 250 for _, delta in sw)


def test_swing_threshold_validation():
    with pytest.raises(ValueError):
        swings([0, 100], threshold=-1)


def test_opening_labels_prefer_eco_then_prefix():
    assert opening_name([], "C33") == "King's Gambit"
    assert opening_name(["e4", "e5", "Nf3", "d6"], None) == "Philidor Defence"
    assert opening_name(["d4", "Nf6"], None) == "Other"


def test_annotated_pgn_uses_neutral_hand_swing_comments_not_blunder_nags():
    from annotate import annotate_game, GAMES
    evergreen = [p for p in GAMES.glob("*.pgn") if "evergreen" in p.stem][0]
    game = annotate_game(evergreen)
    text = str(game)
    reparsed = chess.pgn.read_game(__import__("io").StringIO(text))
    assert reparsed is not None
    plies = sum(1 for _ in reparsed.mainline())
    assert text.count("[%eval") == plies
    assert "[hand-eval]" in text
    nags = [n for node in game.mainline() for n in node.nags]
    assert chess.pgn.NAG_BLUNDER not in nags
    assert chess.pgn.NAG_MISTAKE not in nags


def test_engine_accuracy_if_stockfish_present():
    from accuracy import find_stockfish, game_accuracy
    binary = find_stockfish()
    if not binary:
        pytest.skip("stockfish not installed")
    import chess.engine
    from pathlib import Path
    pgn = sorted(Path("data/games").glob("*.pgn"))[0]
    with chess.engine.SimpleEngine.popen_uci(binary) as engine:
        result = game_accuracy(pgn, engine, depth=6)
    assert 0 < result["white_game_accuracy"] <= 100
    assert 0 < result["black_game_accuracy"] <= 100
    assert result["plies"] > 20
