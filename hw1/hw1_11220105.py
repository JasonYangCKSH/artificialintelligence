import sys
import time
import argparse
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WIN_SCORE = 100_000_000
INF = 10**18
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=2, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=12, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=3, help="generate moves near existing stones")
    return parser.parse_args()
ARGS = parse_args()

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
def minimax(board, depth: int, alpha: int, beta: int, is_max_layer: bool, x: int, y: int):


    pass
def ordered_move(board, player: int, lookahead: int, max_candidates: int, radius: int)->list:

    pass
def choose_move(board):
    
    size = len(board)
    # empty_board
    if is_empty_board(board):
        c = size // 2
        return c, c
    
    # Get Ranked Candidate
    candidates = []
    candidate = ordered_move(board=board, player=WHITE, lookahead=ARGS.depth, max_candidates=ARGS.max_candidates, radius=ARGS.neighbor_radius)
    
    pass

  

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
            board = read_board(sys.stdin, board_size)
            x, y = choose_move(board)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break


if __name__ == "__main__":
    main()