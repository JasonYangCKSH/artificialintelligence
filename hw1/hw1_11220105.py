
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
    
    size = len(board)
    opp  = opponent(player)
    
    # ═══════════════════════════════════════════
    # Step 1：收集所有候選點（鄰近現有棋子的空格）
    # ═══════════════════════════════════════════
    candidates = set()
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY:
                continue
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny, size) \
                    and board[ny][nx] == EMPTY \
                    and is_legal_move(board, nx, ny, player):
                        candidates.add((nx, ny))
    
    if not candidates:
        return []
    
    # ═══════════════════════════════════════════
    # Step 2：依威脅等級分桶
    # ═══════════════════════════════════════════
    
    win_moves      = []   # 優先度 1：我方落子直接贏
    must_block     = []   # 優先度 2：對手落子直接贏，必須擋
    # ↑ 以上兩種情況，找到就應該直接回傳，不需要繼續看其他點
    
    threat_moves   = []   # 優先度 3：製造我方活四 / 衝四
    defence_moves  = []   # 優先度 4：擋對手活三 / 活四
    normal_moves   = []   # 優先度 5：一般發展點
    
    for x, y in candidates:
        
        # ── 優先度 1 ──────────────────────────
        if is_win_after_move(board, x, y, player):
            win_moves.append((x, y))
        
        # ── 優先度 2 ──────────────────────────
        elif is_win_after_move(board, x, y, opp):
            must_block.append((x, y))
        
        # ── 優先度 3 & 4（之後填入具體棋型判斷）──
        else:

            # TODO: 用 line_total / is_open_four_in_direction 等
            #       判斷是「進攻點」還是「防守點」還是「普通點」
            # ── 分桶：一個點只進一個桶 ──────────────────────
            is_threat = False
            is_defence = False
            for dx, dy in DIRECTIONS:

                # ── 進攻判斷：WHITE 落在這裡能形成強棋型 ──
                if is_open_four_in_direction(board, x, y, WHITE, dx, dy):
                    is_threat = True
                # ── 防守判斷：BLACK 在這裡已有威脅，需要擋 ──
                if has_four_in_direction_for_black(board, x, y, dx, dy) or \
                    has_open_three_in_direction_for_black(board, x, y, dx, dy):
                    is_defence = True

            # ── 分桶：一個點只進一個桶 ──────────────────────
            if is_threat and is_defence:
                threat_moves.append((x, y))    # 攻守兼備，優先進攻桶
            elif is_defence:
                defence_moves.append((x, y))
            elif is_threat:
                threat_moves.append((x, y))
            else:
                normal_moves.append((x, y))    # 真正的普通點
    
    # ═══════════════════════════════════════════
    # Step 3：快速決勝（不需要進 Negamax）
    # ═══════════════════════════════════════════
    
    if win_moves:
        return win_moves[:1]    # 直接贏，只回傳一個就夠
    
    if must_block:
        return must_block[:1]   # 必擋，也只需要一個
    
    # ═══════════════════════════════════════════
    # Step 4：其餘候選點打分排序後回傳
    # ═══════════════════════════════════════════
    
    def score(pos):
        x, y = pos
        # TODO: 之後填入評分邏輯
        total = 0
        board[y][x] = WHITE
        for dx, dy in DIRECTIONS:
            length = line_total(board, x, y, dx, dy, WHITE)
            if length == 4:
                total += 50_000
            elif length == 3:
                total += 8_000
            elif length == 2:
                total += 500

        board[y][x] = EMPTY


        black_fours_num = count_black_four_directions(board, x, y)
        black_open_three_num = count_black_open_three_directions(board, x, y)
        total += black_fours_num * 30_000   
        total += black_open_three_num * 2000 
        
        board[y][x] = WHITE
        if is_black_forbidden_after_move(board, x, y):
            total += 500
        board[y][x] = EMPTY

        total += occupied_neighbors(board, x, y, radius=1) * 50
        return total
    
    rest = sorted(threat_moves + defence_moves + normal_moves,
                  key=score, reverse=True)
    
    return rest[:max_candidates]

def _block_score(board, x: int, y: int) -> int:
    """
    評估擋在 (x,y) 的緊急程度。
    黑方在這個點的威脅越多，分數越高。
    """
    score = 0

    # 黑方四連威脅數（非常緊急）
    score += count_black_four_directions(board, x, y)  * 30_000

    # 黑方活三威脅數（緊急）
    score += count_black_open_three_directions(board, x, y) * 5_000

    # 同時白方落這裡也有進攻價值 → 攻守兼備的點優先
    board[y][x] = WHITE
    for dx, dy in DIRECTIONS:
        length = line_total(board, x, y, dx, dy, WHITE)
        if length >= 4:
            score += 10_000
        elif length == 3:
            score += 1_000
    board[y][x] = EMPTY

    return score
def choose_move(board, depth: int, max_candidates: int, radius: int):
    size = len(board)

    if is_empty_board(board):
        c = size // 2
        return c, c
    candidates = ordered_moves(board, WHITE, max_candidates=max_candidates, radius=radius)
    
    for x, y in candidates:
        # 第一優先：我方直接贏
        if is_win_after_move(board, x, y, WHITE):
            return x, y
    
    for x, y in candidates:
        # 第二優先：擋對手直接贏
        if is_win_after_move(board, x, y, BLACK):
            return x, y
    open_three_blocks = []
    for x, y in candidates:
        for dx, dy in DIRECTIONS:
            if has_open_three_in_direction_for_black(board, x, y, dx, dy):
                open_three_blocks.append((x, y))
                break   # 同一個點不重複加

    if open_three_blocks:
        # 有多個活三威脅時，選 score 最高的那個點擋
        return max(open_three_blocks,
                   key=lambda pos: _block_score(board, pos[0], pos[1]))
    
    # 其餘：回傳評分最高的
    return candidates[0]

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
    
