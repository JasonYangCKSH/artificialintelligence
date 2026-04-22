import sys
import time
import argparse
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WIN_SCORE = 100_000_000
INF = 10**18
TIME_LIMIT = 4.5   # 每步最長思考時間（秒），留 0.5 秒給 IO

def parse_args():
    parser = argparse.ArgumentParser()
    # 目標最大深度：iterative deepening 會從 1 逐層加深，時間到就停
    parser.add_argument("--depth",          type=int, default=4,  help="iterative deepening max depth")
    # 候選棋步上限：根據表格 candidates=6 最穩，保持此值
    parser.add_argument("--max-candidates", type=int, default=2,  help="candidate move cap")
    parser.add_argument("--neighbor-radius",type=int, default=2,  help="generate moves near existing stones")
    return parser.parse_args()

ARGS = parse_args()

# ──────────────────────────────────────────────
# Transposition Table（每回合清空）
# ──────────────────────────────────────────────
trans_table: dict = {}
_start_time: float = 0.0


def board_key(board):
    """棋盤 → 可雜湊 tuple，作為 transposition table key。"""
    return tuple(tuple(row) for row in board)


# ──────────────────────────────────────────────
# Evaluation Function
# ──────────────────────────────────────────────

SCORE_TABLE = {
    5: WIN_SCORE,
    'open_four':   100_000,
    'closed_four':  10_000,
    'open_three':    1_000,
    'closed_three':    100,
    'open_two':         10,
    'closed_two':        1,
}

BLACK_PENALTY = 1.2   # 黑方分數懲罰乘數（體現防守優先）


def score_segment(stones: int, open_ends: int) -> int:
    """根據連子數與開放端數回傳分數。"""
    if stones <= 0:
        return 0
    if stones >= 5:
        return WIN_SCORE
    if stones == 4:
        return SCORE_TABLE['open_four'] if open_ends == 2 else SCORE_TABLE['closed_four']
    if stones == 3:
        return SCORE_TABLE['open_three'] if open_ends == 2 else SCORE_TABLE['closed_three']
    if stones == 2:
        return SCORE_TABLE['open_two'] if open_ends == 2 else SCORE_TABLE['closed_two']
    return 0


def scan_line(board, cells: list, color: int) -> int:
    """
    掃描一條線（cells 為 (x,y) 序列），統計 color 方在此線的總分。
    含直接連子段落分析與跳連視窗偵測（視窗長度 6）。
    """
    opp = opponent(color)
    total = 0
    n = len(cells)

    # ── 1. 直接連子段落掃描 ──
    i = 0
    while i < n:
        x, y = cells[i]
        if board[y][x] != color:
            i += 1
            continue
        j = i
        while j < n and board[cells[j][1]][cells[j][0]] == color:
            j += 1
        stones = j - i
        left_open  = i > 0   and board[cells[i-1][1]][cells[i-1][0]] == EMPTY
        right_open = j < n   and board[cells[j][1]][cells[j][0]]   == EMPTY
        open_ends = (1 if left_open else 0) + (1 if right_open else 0)
        total += score_segment(stones, open_ends)
        i = j

    # ── 2. 跳連視窗掃描（長度 6）──
    WIN = 6
    for start in range(n - WIN + 1):
        window = cells[start: start + WIN]
        if any(board[y][x] == opp for x, y in window):
            continue
        stones   = sum(1 for x, y in window if board[y][x] == color)
        empties  = sum(1 for x, y in window if board[y][x] == EMPTY)
        if stones < 2 or empties == 0:
            continue  # 純連子已在段落掃描計算

        left_open  = start > 0      and board[cells[start-1][1]][cells[start-1][0]]       == EMPTY
        right_open = start+WIN < n  and board[cells[start+WIN][1]][cells[start+WIN][0]] == EMPTY
        open_ends = (1 if left_open else 0) + (1 if right_open else 0)
        total += score_segment(stones, open_ends) // 2  # 跳連折半

    return total


def get_all_lines(board) -> list:
    """產生棋盤所有橫/直/斜線的 (x,y) 序列（長度 ≥ 5 才納入）。"""
    size = len(board)
    lines = []
    for y in range(size):
        lines.append([(x, y) for x in range(size)])
    for x in range(size):
        lines.append([(x, y) for y in range(size)])
    for start in range(-(size - 1), size):
        line = [(k, k - start) for k in range(size) if 0 <= k < size and 0 <= k - start < size]
        if len(line) >= 5:
            lines.append(line)
    for start in range(0, 2 * size - 1):
        line = [(k, start - k) for k in range(size) if 0 <= k < size and 0 <= start - k < size]
        if len(line) >= 5:
            lines.append(line)
    return lines


_cached_lines = None
_cached_size  = None


def get_lines_cached(board):
    global _cached_lines, _cached_size
    size = len(board)
    if _cached_size != size:
        _cached_lines = get_all_lines(board)
        _cached_size  = size
    return _cached_lines


def evaluate_board(board) -> int:
    """全盤評估：回傳 white_score - black_score（White 視角正值）。"""
    lines = get_lines_cached(board)
    white_score = 0
    black_score = 0
    for line in lines:
        white_score += scan_line(board, line, WHITE)
        black_score += scan_line(board, line, BLACK)
    return white_score - int(black_score * BLACK_PENALTY)


# ──────────────────────────────────────────────
# ★ 核心修改一：局部評估（取代 move_priority 裡的全盤掃描）
# ──────────────────────────────────────────────

def get_line_through(board, x: int, y: int, dx: int, dy: int) -> list:
    """
    取得通過 (x,y) 在 (dx,dy) 方向的完整棋盤線段。
    先往反方向走到頭，再往正方向收集所有格子。
    """
    size = len(board)
    sx, sy = x, y
    while in_bounds(sx - dx, sy - dy, size):
        sx -= dx
        sy -= dy
    cells = []
    cx, cy = sx, sy
    while in_bounds(cx, cy, size):
        cells.append((cx, cy))
        cx += dx
        cy += dy
    return cells


def evaluate_local(board, x: int, y: int) -> int:
    """
    局部評估：只掃描通過 (x,y) 的 4 條線。
    比 evaluate_board 快約 10-15 倍，適合 move ordering 使用。
    """
    white_score = 0
    black_score = 0
    for dx, dy in DIRECTIONS:
        cells = get_line_through(board, x, y, dx, dy)
        if len(cells) >= 5:
            white_score += scan_line(board, cells, WHITE)
            black_score += scan_line(board, cells, BLACK)
    return white_score - int(black_score * BLACK_PENALTY)


# ──────────────────────────────────────────────
# Move Generation
# ──────────────────────────────────────────────

def has_winning_move(board, color: int):
    """快速檢查 color 方是否有立即獲勝棋步，回傳 (x,y) 或 None。"""
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_legal_move(board, x, y, color):
                if is_win_after_move(board, x, y, color):
                    return (x, y)
    return None


def has_open_four(board, x: int, y: int, color: int) -> bool:
    """落子 (x,y) 後 color 方是否形成 open_four。"""
    for dx, dy in DIRECTIONS:
        if is_open_four_in_direction(board, x, y, color, dx, dy):
            return True
    return False


def has_four(board, x: int, y: int, color: int) -> bool:
    """落子 (x,y) 後 color 方是否形成任意四連（open 或 closed）。"""
    for dx, dy in DIRECTIONS:
        if line_total(board, x, y, dx, dy, color) >= 4:
            return True
    return False


def has_open_three(board, x: int, y: int, color: int) -> bool:
    """落子 (x,y) 後 color 方是否形成 open_three。"""
    for dx, dy in DIRECTIONS:
        if color == BLACK:
            if has_open_three_in_direction_for_black(board, x, y, dx, dy):
                return True
        else:
            if _white_open_three_dir(board, x, y, dx, dy):
                return True
    return False


def _white_open_three_dir(board, x: int, y: int, dx: int, dy: int) -> bool:
    """白方 open_three 方向判斷：此方向連子數為 3 且兩端皆開放。"""
    size = len(board)
    left  = count_dir(board, x, y, -dx, -dy, WHITE)
    right = count_dir(board, x, y,  dx,  dy, WHITE)
    total = 1 + left + right
    if total != 3:
        return False
    lx, ly = x - (left + 1) * dx,  y - (left + 1) * dy
    rx, ry = x + (right + 1) * dx, y + (right + 1) * dy
    return (in_bounds(lx, ly, size) and board[ly][lx] == EMPTY and
            in_bounds(rx, ry, size) and board[ry][rx] == EMPTY)


def move_priority(board, x: int, y: int, player: int) -> int:
    """
    計算落子 (x,y) 的啟發優先級（越高越優先搜尋）。

    ★ 修改重點：最後一步改用 evaluate_local(局部評估)
      取代原本的 evaluate_board(全盤掃描)，速度提升 ~10x。
    """
    opp = opponent(player)
    priority = 0

    # ── (a) 我方直接獲勝 ──
    board[y][x] = player
    if is_win_after_move(board, x, y, player):
        board[y][x] = EMPTY
        return 10_000_000

    # ── (c) 我方形成四連 ──
    if has_four(board, x, y, player):
        priority += 500_000

    # ── (e) 我方形成 open_three ──
    if has_open_three(board, x, y, player):
        priority += 50_000

    # ★ 局部評估（取代全盤掃描）──
    local = evaluate_local(board, x, y)
    board[y][x] = EMPTY
    priority += local

    # ── (b) 防守對方五連 ──
    board[y][x] = opp
    if is_win_after_move(board, x, y, opp):
        board[y][x] = EMPTY
        return 9_000_000

    # ── (d) 防守對方 open_four ──
    if has_open_four(board, x, y, opp):
        priority += 800_000

    # ── 防守對方一般四連 ──
    if has_four(board, x, y, opp):
        priority += 100_000

    board[y][x] = EMPTY

    return priority


def ordered_move(board, player: int, lookahead: int,
                 max_candidates: int, radius: int) -> list:
    """
    產生並排序候選棋步，回傳最多 max_candidates 個 (x, y)。
    候選格：已有棋子周圍 radius 格內的空格，通過合法性過濾後依 move_priority 排序。
    """
    size = len(board)
    candidates = []

    for y in range(size):
        for x in range(size):
            if board[y][x] != EMPTY:
                continue
            if not is_legal_move(board, x, y, player):
                continue
            if occupied_neighbors(board, x, y, radius) == 0:
                continue
            pri = move_priority(board, x, y, player)
            candidates.append((pri, x, y))

    candidates.sort(key=lambda t: -t[0])
    return [(x, y) for _, x, y in candidates[:max_candidates]]


# ──────────────────────────────────────────────
# Minimax with Alpha-Beta Pruning + Transposition Table
# ──────────────────────────────────────────────

def minimax(board, depth: int, alpha: int, beta: int,
            is_max_layer: bool, last_x: int, last_y: int):
    """
    Minimax 搜尋含 Alpha-Beta 剪枝與 Transposition Table。

    回傳: (score, best_x, best_y)
    """
    # ── 時間保護：超時直接回傳靜態評估 ──
    if time.time() - _start_time > TIME_LIMIT:
        return evaluate_board(board), -1, -1

    # ── 終止條件 ──
    last_player = BLACK if is_max_layer else WHITE
    if last_x >= 0 and is_win_after_move(board, last_x, last_y, last_player):
        return (WIN_SCORE + depth, -1, -1) if last_player == WHITE else (-WIN_SCORE - depth, -1, -1)

    if board_full(board):
        return 0, -1, -1

    if depth == 0:
        return evaluate_board(board), -1, -1

    # ── Transposition Table 查表 ──
    key = board_key(board)
    if key in trans_table:
        entry = trans_table[key]
        if entry['depth'] >= depth:
            flag, s = entry['flag'], entry['score']
            if flag == 'exact':
                return s, entry['x'], entry['y']
            elif flag == 'lower' and s >= beta:
                return s, entry['x'], entry['y']
            elif flag == 'upper' and s <= alpha:
                return s, entry['x'], entry['y']

    # ── 產生候選棋步 ──
    current_player = WHITE if is_max_layer else BLACK
    moves = ordered_move(board, current_player, depth,
                         ARGS.max_candidates, ARGS.neighbor_radius)

    if not moves:
        return evaluate_board(board), -1, -1

    best_score        = -INF if is_max_layer else INF
    best_x, best_y    = moves[0]
    orig_alpha        = alpha

    for x, y in moves:
        board[y][x] = current_player
        score, _, _  = minimax(board, depth - 1, alpha, beta, not is_max_layer, x, y)
        board[y][x]  = EMPTY

        if is_max_layer:
            if score > best_score:
                best_score, best_x, best_y = score, x, y
            alpha = max(alpha, best_score)
        else:
            if score < best_score:
                best_score, best_x, best_y = score, x, y
            beta = min(beta, best_score)

        if alpha >= beta:
            break  # Alpha-Beta 剪枝

    # ── Transposition Table 存表 ──
    if best_score <= orig_alpha:
        flag = 'upper'
    elif best_score >= beta:
        flag = 'lower'
    else:
        flag = 'exact'

    trans_table[key] = {
        'score': best_score, 'depth': depth,
        'flag': flag, 'x': best_x, 'y': best_y,
    }

    return best_score, best_x, best_y


# ──────────────────────────────────────────────
# Read Board（不可修改）
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# ★ 核心修改二：choose_move 加入 Iterative Deepening
# ──────────────────────────────────────────────

def choose_move(board):
    """
    選出最佳落子位置。

    流程：
      1. 空盤落中央
      2. 白方有直接獲勝棋步 → 立即落子
      3. 黑方有直接獲勝棋步 → 立即封堵
      4. Iterative Deepening Minimax（從 depth=1 逐層加深到 ARGS.depth）
         - 每層結束後保存結果
         - 剩餘時間 < 0.5 秒時停止，使用最後完整層的結果
         - 永遠不會超時或「炸」
    """
    global _start_time, trans_table
    _start_time = time.time()
    trans_table = {}   # 每回合清空，避免過期快取

    size = len(board)

    # ── 1. 空盤落中央 ──
    if is_empty_board(board):
        c = size // 2
        return c, c

    # ── 2. 白方直接獲勝 ──
    win_move = has_winning_move(board, WHITE)
    if win_move:
        return win_move

    # ── 3. 防守黑方直接獲勝 ──
    block_move = has_winning_move(board, BLACK)
    if block_move:
        bx, by = block_move
        if is_legal_move(board, bx, by, WHITE):
            return bx, by

    # ── 4. Iterative Deepening ──
    # 先用 depth=1 的 ordered_move 結果作為 fallback
    fallback_moves = ordered_move(board, WHITE, 1, ARGS.max_candidates, ARGS.neighbor_radius)
    best_x, best_y = fallback_moves[0] if fallback_moves else (size // 2, size // 2)

    for target_depth in range(1, ARGS.depth + 1):
        # 時間保護：若剩餘時間不足，跳出並用上一層結果
        elapsed = time.time() - _start_time
        if elapsed > 3.5:
            break

        score, x, y = minimax(board, target_depth, -INF, INF, True, -1, -1)

        # 只在回傳有效棋步時更新（超時會回傳 -1,-1）
        if x >= 0 and y >= 0 and is_legal_move(board, x, y, WHITE):
            best_x, best_y = x, y

        # 若找到必勝手，不需繼續加深
        if score >= WIN_SCORE:
            break

    # ── 最終 fallback（極端情況）──
    if not is_legal_move(board, best_x, best_y, WHITE):
        moves = legal_moves(board, WHITE)
        best_x, best_y = moves[0] if moves else (size // 2, size // 2)

    return best_x, best_y


def main():
    board_size = None

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()

        if parts[0] == "START":
            board_size = int(parts[1])

        elif parts[0] == "TURN":
            board = read_board(sys.stdin, board_size)
            x, y = choose_move(board)
            print(f"MOVE {x} {y}", flush=True)

        elif parts[0] == "END":
            break


if __name__ == "__main__":
    main()