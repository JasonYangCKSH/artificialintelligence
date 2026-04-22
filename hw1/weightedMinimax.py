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
    parser.add_argument("--depth", type=int, default=3, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=1, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=3, help="generate moves near existing stones")
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
    """
    Alpha-beta pruned minimax with weighted lookahead evaluation.
    
    Explores game tree using DFS and prunes branches with alpha-beta cutoff.
    Returns accumulated attack + defense scores with exponential decay by depth.
    
    Weight factor: 1 / (2^depth) ensures deeper evaluations have less impact.
    
    Parameters:
        board: Current board state
        depth: Current search depth (0 = placing at x,y; deeper = opponent responses)
        alpha: Best score for maximizer (WHITE)
        beta: Best score for minimizer (BLACK)
        is_max_layer: True if this layer places WHITE stone, False for BLACK
        x, y: Position being evaluated
    
    Returns:
        Weighted evaluation score (higher = better for WHITE)
    """
    size = len(board)
    max_depth = ARGS.depth
    
    # ===== STEP 1: Terminal condition check =====
    if depth >= max_depth:
        return 0  # Reached max depth, no further evaluation
    
    # ===== STEP 2: Place stone and evaluate immediate position =====
    if is_max_layer:
        board[y][x] = WHITE
    else:
        board[y][x] = BLACK
    
    # Calculate immediate evaluation (attack + defense from WHITE's perspective)
    
    
    # ----------------WHITE perspective------------------------------
    attack = 0
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
    # ---------------------------------------------------------------


    # -----------------BLACK perspective-----------------------------
    defense = count_black_four_directions(board, x, y) * 2_000_000
    defense += count_black_open_three_directions(board, x, y) * 300_000
    # ---------------------------------------------------------------
    
    current_score = attack + defense
    
    # ===== STEP 3: Apply depth-based weight (deeper = weaker influence) =====
    weight = 1.0 / (2 ** depth)
    weighted_current = int(current_score * weight)
    
    # ===== STEP 4: Check for immediate win =====
    if is_max_layer and is_win_after_move(board, x, y, WHITE):
        board[y][x] = EMPTY
        return WIN_SCORE - depth  # Prefer faster wins
    elif not is_max_layer and is_win_after_move(board, x, y, BLACK):
        board[y][x] = EMPTY
        return -WIN_SCORE + depth
    
    # ===== STEP 5: Generate candidate moves for opponent =====
    candidates = []
    for ty in range(size):
        for tx in range(size):
            if board[ty][tx] == EMPTY:
                # Evaluate with appropriate color
                opponent_color = BLACK if is_max_layer else WHITE
                score = evaluateCurrentPosition(board, tx, ty, opponent_color)
                if score > 100:  # Only consider meaningful moves
                    candidates.append((score, tx, ty))
    
    candidates.sort(reverse=True)
    candidates = candidates[:6]  # Limit branching factor for performance
    
    # If no candidates, return current weighted score
    if not candidates:
        board[y][x] = EMPTY
        return weighted_current
    
    # ===== STEP 6: DFS with alpha-beta pruning =====
    if is_max_layer:
        # Current layer is WHITE, so opponent (BLACK) will minimize
        min_eval = INF
        for _, nx, ny in candidates:
            # Recursively evaluate: next layer is BLACK's turn (minimize)
            eval_score = minimax(board, depth + 1, alpha, beta, False, nx, ny)
            min_eval = min(min_eval, eval_score)
            
            # Alpha-beta pruning
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff - prune remaining branches
        
        board[y][x] = EMPTY
        return weighted_current + min_eval
    
    else:
        # Current layer is BLACK, so opponent (WHITE) will maximize
        max_eval = -INF
        for _, nx, ny in candidates:
            # Recursively evaluate: next layer is WHITE's turn (maximize)
            eval_score = minimax(board, depth + 1, alpha, beta, True, nx, ny)
            max_eval = max(max_eval, eval_score)
            
            # Alpha-beta pruning
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff - prune remaining branches
        
        board[y][x] = EMPTY
        return weighted_current + max_eval

def calculateForbiddenTrapScore(board):
    """
    Calculate forbidden trap penalty score.
    Currently returns 0 - to be implemented later.
    """
    return 0

def evaluateScore(board, x: int, y: int, lookahead: int) -> int:
    """
    Comprehensive position evaluation with minimax lookahead.
    Score = Minimax lookahead result + Forbidden trap penalty
    
    Minimax explores opponent responses up to 'lookahead' depth with alpha-beta pruning.
    
    Args:
        board: Game board state
        x, y: Position to evaluate
        lookahead: Search depth for minimax (0 = no lookahead, only immediate score)
    
    Returns:
        Final evaluation score for this position
    """
    if lookahead <= 0:
        # No lookahead: just evaluate immediate attack/defense
        attack = 0
        board[y][x] = WHITE
        for dx, dy in DIRECTIONS:
            length = line_total(board, x, y, dx, dy, WHITE)
            if length == 5:
                attack += 100_000_000
            elif length == 4:
                attack += 5_000_000
            elif length == 3:
                attack += 200_000
            elif length == 2:
                attack += 10_000
        board[y][x] = EMPTY
        
        defense = count_black_four_directions(board, x, y) * 2_000_000
        defense += count_black_open_three_directions(board, x, y) * 300_000
        
        return int(attack + defense)
    
    # With lookahead: use minimax to explore opponent responses
    basic_score = minimax(board=board, depth=0, alpha=-INF, beta=INF, 
                          is_max_layer=True, x=x, y=y)
    
    # Add forbidden trap penalty (reserved for future)
    forbidden_trap_score = calculateForbiddenTrapScore(board=board)
    
    return int(basic_score + forbidden_trap_score)

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
    
    # Get ranked candidates 
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