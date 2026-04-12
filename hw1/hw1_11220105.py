
import sys
import time
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
def evaluate(board, player: int):
    pass
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
    moves = ordered_moves(board, player, # ← 【修改點2】白方版候選點排序
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


def choose_move(board):
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == 0:
                return x, y


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
            x, y = choose_move(board)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break
       

if __name__ == "__main__":
    main()
    
