
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
def forbiddenTrapScore(board, x: int, y: int, lookahead_depth = 2)->int:
    board[y][x] = WHITE
    // step1: Layer0, 當前forbiddenTrap temptation score

    // step2: Layer1, lookahead

    
    
    board[y][x] = EMPTY
    return layer0_score + layer1_score * 0.5
    pass
def evaluateScore(board, x: int, y: int) -> int:
    '''
    score = Attack + Defense - Risk + Urgency

    goal: to calculate the highest scores among many candidates

    Attack: (判斷是否有建立self的招術)

    Defense:(判斷是否有block opponent的招術)

    Forbidden_Trap
    '''
    #=======Initialize=======
    attack = 0
    defense = 0
    forbidden_trap = 0
    #========================
    
    # ATTACK
    board[y][x] = WHITE
    for dx, dy in DIRECTIONS:
        length = line_total(board, x, y, dx, dy, WHITE)
        if length >= 4: attack += 50_000
        if length == 3: attack += 8_000
        if length == 2: attack += 500
    board[y][x] = EMPTY
    
    # DEFENSE
    defense  = count_black_four_directions(board, x, y) * 35_000
    defense += count_black_open_three_directions(board, x, y) * 7_000
    
    # FORBIDDEN_TRAP
    forbidden_trap = forbiddenTrapScore(board, x, y)
    return attack + defense + forbidden_trap

def ordered_moves(board, player: int, max_candidates: int, radius: int):
    size = len(board)
    opp = opponent(player)
    candidates = set()
    for y in range(size):
        for x in range(size):
            if board[y][x] != EMPTY:
                # radius == 2 (default)
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if not(0 <= nx < size and 0 <= ny < size):
                            continue
                        if board[ny][nx] != EMPTY:
                            continue
                        candidates.add((nx, ny))
    # candidates finished
    # todo:check member in candidates
    scores = []
    candidates = list(candidates)
    for x, y in candidates:
        score = evaluateScore(board, x, y)
        scores.append((score, x, y))
    # -pick the best candidate among condidates-


    # ------------------------------------------


def choose_move(board, depth: int, max_candidates: int, radius: int):
    size = len(board)
    if is_empty_board(board):
        c = size // 2
        return c, c
    candidates = ordered_moves(board, WHITE, max_candidates=max_candidates, radius=radius)
    # case1: white win
    for x, y in candidates:
        if is_win_after_move(board, x, y, WHITE):
            return x, y
    # case2: black win
    for x, y in candidates:
        if is_win_after_move(board, x, y, BLACK):
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
            x, y = choose_move(board, depth=ARGS.depth,max_candidates=ARGS.max_candidates,
                radius=ARGS.neighbor_radius)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break
       

if __name__ == "__main__":
    main()
    
