import math

from accuracy_metrics import (
    accuracy_series_from_cp,
    game_accuracy_from_cp,
    lichess_win_percent,
    move_accuracy,
    simple_mean_accuracy_from_cp,
)
from winprob import fit_k, win_probability


def test_lichess_win_percent_reference_points_and_clipping():
    assert math.isclose(lichess_win_percent(0), 50.0, abs_tol=1e-12)
    assert lichess_win_percent(400) > 80
    assert lichess_win_percent(-400) < 20
    # Current Lichess cp mapping clips at +/-1000, so huge values saturate at
    # about 97.5%, not mathematically at 100%.
    assert math.isclose(lichess_win_percent(10_000), lichess_win_percent(1000), abs_tol=1e-12)
    assert 97 < lichess_win_percent(10_000) < 98


def test_win_probability_reuses_same_mapping():
    for cp in (-1000, -400, 0, 400, 1000):
        assert math.isclose(win_probability(cp), lichess_win_percent(cp) / 100, rel_tol=0, abs_tol=1e-12)


def test_move_accuracy_bounds_and_direction():
    assert move_accuracy(60, 60) == 100
    assert move_accuracy(50, 55) == 100
    assert 0 <= move_accuracy(60, 10) < 20
    assert 0 <= move_accuracy(99, 0) <= 100


def test_accuracy_series_assigns_alternating_colours():
    # Four plies => two moves per side.
    s = accuracy_series_from_cp([50, 20, 80, -100])
    assert len(s["white"]) == 2
    assert len(s["black"]) == 2
    assert len(s["white_weights"]) == 2
    assert len(s["black_weights"]) == 2


def test_game_accuracy_is_not_plain_arithmetic_mean():
    path = [20, 25, 30, 35, 40, 45, 50, 55, -500, -480, -450, -430,
            -400, -380, -350, -330, -300, -280, -250, -230]
    current = game_accuracy_from_cp(path)
    plain = simple_mean_accuracy_from_cp(path)
    assert abs(current["white"] - plain["white"]) > 0.01 or abs(current["black"] - plain["black"]) > 0.01


def test_game_accuracy_stays_in_bounds():
    for path in ([0, 0, 0, 0], [1000, -1000, 1000, -1000], [50] * 20):
        out = game_accuracy_from_cp(path)
        assert 0 <= out["white"] <= 100
        assert 0 <= out["black"] <= 100


def test_game_balanced_k_fit_does_not_reward_duplication_of_one_game():
    games = [[300, 400, 500], [-300, -400, -500]]
    results = [1.0, 0.0]
    k1 = fit_k(games, results)
    # Repeating positions inside the first game should not change that game's
    # total weight because the objective averages within each game first.
    k2 = fit_k([games[0] * 10, games[1]], results)
    assert math.isclose(k1, k2, abs_tol=1e-12)


def test_k_fit_requires_matching_nonempty_games():
    import pytest
    with pytest.raises(ValueError):
        fit_k([], [])
    with pytest.raises(ValueError):
        fit_k([[100]], [1.0, 0.0])
