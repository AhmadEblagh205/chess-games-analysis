"""Transparent hand-built chess evaluation.

The score combines material, compact piece-square bonuses and a simple mobility
term.  It is deliberately interpretable rather than strong.  Stockfish is the
appropriate evaluator when tactical accuracy matters.
"""
import chess

PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

CENTRE = [0, 0, 0, 0, 0, 0, 0, 0,
          0, 5, 5, 5, 5, 5, 5, 0,
          0, 5, 10, 12, 12, 10, 5, 0,
          0, 5, 12, 18, 18, 12, 5, 0,
          0, 5, 12, 18, 18, 12, 5, 0,
          0, 5, 10, 12, 12, 10, 5, 0,
          0, 5, 5, 5, 5, 5, 5, 0,
          0, 0, 0, 0, 0, 0, 0, 0]
PAWN_ADVANCE = [0, 0, 0, 0, 0, 0, 0, 0,
                2, 2, 2, -4, -4, 2, 2, 2,
                2, 0, 4, 6, 6, 4, 0, 2,
                3, 3, 8, 14, 14, 8, 3, 3,
                5, 5, 12, 18, 18, 12, 5, 5,
                10, 10, 16, 22, 22, 16, 10, 10,
                30, 30, 30, 30, 30, 30, 30, 30,
                0, 0, 0, 0, 0, 0, 0, 0]


def material(board: chess.Board) -> int:
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += value * len(board.pieces(piece_type, chess.WHITE))
        score -= value * len(board.pieces(piece_type, chess.BLACK))
    return score


def placement(board: chess.Board) -> int:
    score = 0
    for sq, piece in board.piece_map().items():
        table = PAWN_ADVANCE if piece.piece_type == chess.PAWN else CENTRE
        if piece.color == chess.WHITE:
            score += table[sq]
        else:
            score -= table[chess.square_mirror(sq)]
    return score


def mobility(board: chess.Board) -> int:
    """Hypothetical legal-move-count difference, 2 cp per move.

    The side-to-move flag is flipped on a copied position so both sides are
    evaluated from the same piece placement.  This is a heuristic feature, not
    a claim that both resulting boards are reachable game states.
    """
    b = board.copy(stack=False)
    b.turn = chess.WHITE
    white = b.legal_moves.count()
    b.turn = chess.BLACK
    black = b.legal_moves.count()
    return 2 * (white - black)


def evaluate(board: chess.Board) -> int:
    """Centipawns, White positive; terminal wins/losses dominate.

    Drawn terminal positions are exactly zero.  V1 only special-cased checkmate,
    which could assign a material advantage to a stalemate/drawn terminal node.
    """
    if board.is_checkmate():
        return -10_000 if board.turn == chess.WHITE else 10_000
    if board.is_game_over(claim_draw=True):
        return 0
    return material(board) + placement(board) + mobility(board)
