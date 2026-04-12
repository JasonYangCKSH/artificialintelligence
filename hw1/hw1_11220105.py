
import sys
import time
import argparse
from enum import IntEnum
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WIN_SCORE = 100_000_000
INF = 10**18
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=2, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=12, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=2, help="generate moves near existing stones")
    return parser.parse_args()


ARGS = parse_args()
class ThreatCondition(IntEnum):
    OPENFOUR = 100000
    CLOSEDFOUR = 10000
    OPENTHREE = 1000

def read_board(stream, size):
    line = stream.readline().strip()
    if line != "BOARD":
        raise ValueError("expected BOARD")

    board = []
    for _ in range(size):
        row = list(map(int, stream.readline().split()))
        if len(row) != size:
            raise ValueError("invalid row length")
        board.append(row)

    line = stream.readline().strip()
    if line != "END_BOARD":
        raise ValueError("expected END_BOARD")

    return board
# >0: white > black
# <0: black > white
def evaluate(board, player: int):
    return 0
def ordered_moves(board, player: int, max_candidates: int, radius: int):
    pass
def negamax(board, depth: int, alpha: int, beta: int, player: int,
            max_candidates: int, radius: int)->int:
    # base case--------------------------
    if board_full(board):
        return 0
    if depth == 0:
        return evaluate(board, player) # <------white evaluate function
    #------------------------------------
    moves = ordered_moves(board, player,
                            max_candidates=max_candidates,
                            radius=radius)
    if not moves:
        return 0
    best = -INF
    opp = opponent(player)

    for x, y in moves:
        board[y][x] = player
        if is_win_after_move(board, x, y, player):
            val = WIN_SCORE - (ARGS.depth - depth) # ARGS.depth == MAX_DEPTH
        else:
            val = -negamax(board, depth - 1, -beta, -alpha, opp,
                           max_candidates=max_candidates, radius=radius)
        board[y][x] = EMPTY
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def choose_move(board, depth: int, max_candidates: int, radius: int):
    size = len(board)

    if is_empty_board(board):
        c = size // 2
        return c, c
    # 利用ordered_move()來找到candidata的(x, y)，存成list of moves
    moves = ordered_moves(board, WHITE,
                                max_candidates=max_candidates,
                                radius=radius)
    # 若moves為空，藉由legal_move()來尋找合法的落點list，並回傳第一個legal position
    if not moves:
        legal_now = legal_moves(board, WHITE)
        if not legal_now:
            raise RuntimeError("no legal moves for WHITE")
        return legal_now[0]
    # 預測區
    best_score = -INF
    best_move  = moves[0] # 預設 moves[0] 是 best candidate
    alpha = -INF
    beta  = INF
    opp   = opponent(WHITE)
    for x, y in moves: # test every (x, y) in moves
        board[y][x] = WHITE # first predicated that white is already put
        # 
        if is_win_after_move(board, x, y, WHITE):
            score = WIN_SCORE # 100_100_100
        else: # 
            score = -negamax(board, depth - 1, -beta, -alpha, opp,
                                   max_candidates=max_candidates,
                                   radius=radius)

        board[y][x] = EMPTY # erase predicated condition

        if score > best_score:
            best_score = score
            best_move  = (x, y)

        if score > alpha:
            alpha = score

    return best_move


def main():
    board_size = None
    my_role = None

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        parts = line.split()

        if parts[0] == "START":
            board_size = int(parts[1])
            my_role = parts[2]

        elif parts[0] == "TURN":
            if board_size is None or my_role is None:
                raise RuntimeError("engine not initialized by START")
            board = read_board(sys.stdin, board_size)
            x, y = choose_move(board, depth=ARGS.depth,max_candidates=ARGS.max_candidates,
                radius=ARGS.neighbor_radius)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break
       

if __name__ == "__main__":
    main()
    
