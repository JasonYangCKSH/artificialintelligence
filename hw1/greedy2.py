
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
    parser.add_argument("--max-candidates", type=int, default=8, help="candidate move cap")
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
# ========== LIGHTWEIGHT GREEDY EVALUATION ==========

def evaluateCurrentPosition(board, x: int, y: int, color: int) -> int:
    """
    Lightweight immediate position value evaluation without lookahead.
    Fast and accurate for move ranking.
    """
    board[y][x] = color
    score = 0
    
    # Evaluate all directions
    for dx, dy in DIRECTIONS:
        length = line_total(board, x, y, dx, dy, color)
        if length >= 5:
            score += 100_000_000  # Winning move
        elif length == 4:
            score += 1_000_000    # Very strong
        elif length == 3:
            score += 100_000      # Strong
        elif length == 2:
            score += 10_000       # Medium
        elif length == 1:
            score += 500          # Weak
    
    board[y][x] = EMPTY
    return score

def minimax(board, depth: int, alpha: int, beta: int, is_max_layer: bool, x: int, y: int):


    pass
def evaluateScore(board, x: int, y: int, lookahead: int) -> int:
    """
    Lightweight evaluation for move ranking.
    Score = Attack + Defense (only immediate threats, no minimax)
    
    Simple and fast - lets the greedy Case logic handle strategic decisions.
    """
    attack = 0
    defense = 0


    #attack = minimax(board=board, depth=lookahead, alpha=-INF, beta=INF, is_max_layer=True, x=x, y=y)
    
    # ATTACK: WHITE's immediate potential
    board[y][x] = WHITE
    for dx, dy in DIRECTIONS:
        length = line_total(board, x, y, dx, dy, WHITE)
        if length == 5:
            attack += 100_000_000  # Instant win
        elif length == 4:
            attack += 5_000_000    # Open four or better
        elif length == 3:
            attack += 200_000      # Open three
        elif length == 2:
            attack += 10_000       # Potential
    board[y][x] = EMPTY
    
    # DEFENSE: BLACK's immediate threats
    defense = count_black_four_directions(board, x, y) * 2_000_000
    defense += count_black_open_three_directions(board, x, y) * 300_000
    

    
    return int(attack + defense)

def ordered_moves(board, player: int, lookahead: int, max_candidates: int, radius: int):
    """
    Generate and rank candidate moves using lightweight greedy evaluation.
    Fast ranking based on immediate attack/defense potential only.
    
    Args:
        board: Game board state
        player: Current player (WHITE or BLACK)
        max_candidates: Maximum number of candidates to return
        radius: Radius for searching near existing stones
    
    Returns:
        List of (score, x, y) tuples sorted by evaluation score (highest first)
    """
    size = len(board)
    candidates = set()
    
    # Generate candidate positions (near existing stones)
    for y in range(size):
        for x in range(size):
            if board[y][x] != EMPTY:
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
    
    # Evaluate all candidates (fast, no minimax)
    scores = []
    for x, y in candidates:
        score = evaluateScore(board, x, y, lookahead)
        scores.append((score, x, y))
    
    # Sort by score (highest first) and limit to max_candidates
    scores.sort(reverse=True)
    return scores[:max_candidates]


def choose_move(board, depth: int, max_candidates: int, radius: int):
    """
    Choose the best move using pure greedy strategy.
    Handles all strategic decisions directly without minimax overhead.
    
    Priority order (cascading greedy):
    1. WHITE wins immediately
    2. BLACK wins next → must block
    3. WHITE forms open four (winning threat)
    4. BLACK forms open four → must block
    5. Best ranked move by evaluation score
    
    Args:
        board: Game board state
        depth: Reserved for compatibility (not used in pure greedy)
        max_candidates: Maximum candidates to evaluate
        radius: Radius for move generation
    
    Returns:
        Tuple (x, y) representing the best move
    """
    size = len(board)
    
    # Empty board: start from center
    if is_empty_board(board):
        c = size // 2
        return c, c
    
    # Get ranked candidates (fast evaluation only)
    candidates = ordered_moves(board, WHITE, lookahead=depth, max_candidates=max_candidates, radius=radius)
    
    if not candidates:
        # Fallback: return center if no candidates
        c = size // 2
        return c, c
    # Case 2: BLACK would win next turn - MUST BLOCK
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_win_after_move(board, x, y, BLACK):
                return x, y
    # Case 1: WHITE can win immediately - ALWAYS TAKE IT
    for score, x, y in candidates:
        if is_win_after_move(board, x, y, WHITE):
            return x, y
    
    # Case 4: BLACK can form open four - MUST BLOCK
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY:
                board[y][x] = BLACK
                black_open_four = False
                for dx, dy in DIRECTIONS:
                    if is_open_four_in_direction(board, x, y, BLACK, dx, dy):
                        black_open_four = True
                        break
                board[y][x] = EMPTY
                
                if black_open_four:
                    return x, y

    
    # Case 3: WHITE can get an open four (winning threat)
    for score, x, y in candidates:
        board[y][x] = WHITE
        for dx, dy in DIRECTIONS:
            if is_open_four_in_direction(board, x, y, WHITE, dx, dy):
                board[y][x] = EMPTY
                return x, y
        board[y][x] = EMPTY



    # Case last: Return best ranked move (from lightweight evaluation)
    _, best_x, best_y = candidates[0]
    return best_x, best_y
    


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
            x, y = choose_move(board, depth=ARGS.depth, max_candidates=ARGS.max_candidates,
                               radius=ARGS.neighbor_radius)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break
       

if __name__ == "__main__":
    main()
    
