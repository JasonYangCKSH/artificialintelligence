import sys
import time
import argparse
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WIN_SCORE = 100_000_000
INF = 10**18
TIME_LIMIT = 4.5
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=5, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=4, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=2, help="generate moves near existing stones")
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

def has_winning_move(board, color: int):
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_legal_move(board, x, y, color):
                if is_win_after_move(board, x, y, color):
                    return (x, y)
    return None
def ordered_move(board, player: int, lookahead: int, max_candidates: int, radius: int)->list:
    size = len(board)
    candidates = []
def minimax(board, depth: int, alpha: int, beta: int, is_max_layer: bool, last_x: int,last_y: int):
    pass
def choose_move(board):

    if is_empty_board(board):
        c = size // 2
        return c, c
    # caseA: 白直接贏
    win_move = has_winning_move(board, WHITE)
    if win_move:
        return win_move


    # caseB: 黑直接贏
    block_move = has_winning_move(board, BLACK)
    if block_move:
        bx, by = block_move
        if is_legal_move(board, bx, by, WHITE):
            return bx, by


    # Minimax 搜尋 
    _, x, y = minimax(board=board,depth=ARGS.depth,alpha=-INF,beta=INF,is_max_layer=True,last_x=-1,last_y=-1)

    # 若 minimax 未能回傳有效棋步，取第一個合法棋步
    if x < 0 or y < 0 or not is_legal_move(board, x, y, WHITE):
        
        fallback = ordered_move(board, WHITE, ARGS.depth,
                                ARGS.max_candidates, ARGS.neighbor_radius)
        if fallback:
            x, y = fallback[0]
        else:
            moves = legal_moves(board, WHITE)
            x, y = moves[0] if moves else (size // 2, size // 2)

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
            board = read_board(sys.stdin, board_size)
            x, y = choose_move(board)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break


if __name__ == "__main__":
    main()