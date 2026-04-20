import sys
import time
import argparse
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WIN_SCORE = 100_000_000
INF = 10**18

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=4, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=4, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=2, help="generate moves near existing stones")
    return parser.parse_args()

ARGS = parse_args()

# ──────────────────────────────────────────────
# Transposition Table（跨節點快取，每回合清空）
# ──────────────────────────────────────────────
trans_table: dict = {}


def board_key(board):
    """將棋盤轉為可雜湊的 tuple，作為 transposition table 的 key。"""
    return tuple(tuple(row) for row in board)


# ──────────────────────────────────────────────
# Evaluation Function
# ──────────────────────────────────────────────

# 各威脅型樣的基礎分數
SCORE_TABLE = {
    5: WIN_SCORE,       # 五連（或長連）
    'open_four':   100_000,
    'closed_four':  10_000,
    'open_three':    1_000,
    'closed_three':    100,
    'open_two':         10,
    'closed_two':        1,
}

BLACK_PENALTY = 1.2   # 黑方分數懲罰乘數（防守優先）


def score_segment(stones: int, open_ends: int) -> int:
    """
    根據連子數(stones)與開放端數(open_ends=0/1/2)回傳分數。
    stones 已排除越界與對方子干擾。
    """
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
    採「連續段落」分析：遇到對方子截斷，統計每段的子數與兩端開放性。
    同時考慮跳連（空格在中間），使用長度 6 視窗滑動偵測跳連型樣。
    """
    size = len(board)
    opp = opponent(color)
    total = 0
    n = len(cells)

    # ── 1. 直接連子段落掃描 ──────────────────────
    i = 0
    while i < n:
        x, y = cells[i]
        if board[y][x] != color:
            i += 1
            continue

        # 找到連子起點，向右延伸
        j = i
        while j < n and board[cells[j][1]][cells[j][0]] == color:
            j += 1

        stones = j - i
        # 判斷左端是否開放
        if i > 0:
            lx, ly = cells[i - 1]
            left_open = board[ly][lx] == EMPTY
        else:
            left_open = False
        # 判斷右端是否開放
        if j < n:
            rx, ry = cells[j]
            right_open = board[ry][rx] == EMPTY
        else:
            right_open = False

        open_ends = (1 if left_open else 0) + (1 if right_open else 0)
        total += score_segment(stones, open_ends)
        i = j

    # ── 2. 跳連視窗掃描（長度 ≤ 6 的視窗）─────────
    # 在視窗中若只有 color 和 EMPTY，則計算 color 子數與兩端狀態
    WIN = 6
    for start in range(n - WIN + 1):
        window = cells[start: start + WIN]
        # 視窗內不能有對方子
        if any(board[y][x] == opp for x, y in window):
            continue

        stones = sum(1 for x, y in window if board[y][x] == color)
        if stones < 2:
            continue

        # 跳連：中間有空格才算跳連（連續連已在上方計算）
        empties_in = sum(1 for x, y in window if board[y][x] == EMPTY)
        if empties_in == 0:
            continue  # 純連子已在段落掃描計算

        # 判斷視窗兩端（視窗外一格）的開放性
        if start > 0:
            lx, ly = cells[start - 1]
            left_open = board[ly][lx] == EMPTY
        else:
            left_open = False
        end_idx = start + WIN
        if end_idx < n:
            rx, ry = cells[end_idx]
            right_open = board[ry][rx] == EMPTY
        else:
            right_open = False

        open_ends = (1 if left_open else 0) + (1 if right_open else 0)
        # 跳連視窗內空格數決定「有效」型樣：視窗 6 格內子+空格=6
        # 跳連分數打折（不如連續強）
        jump_score = score_segment(stones, open_ends) // 2
        total += jump_score

    return total


def get_all_lines(board) -> list:
    """
    產生棋盤所有橫、直、斜線的 (x,y) 序列，供 scan_line 使用。
    每條線長度需 ≥ 5 才有意義。
    """
    size = len(board)
    lines = []

    # 橫線
    for y in range(size):
        lines.append([(x, y) for x in range(size)])

    # 直線
    for x in range(size):
        lines.append([(x, y) for y in range(size)])

    # 主對角線（左上→右下）
    for start in range(-(size - 1), size):
        line = []
        for k in range(size):
            x, y = k, k - start
            if 0 <= x < size and 0 <= y < size:
                line.append((x, y))
        if len(line) >= 5:
            lines.append(line)

    # 副對角線（右上→左下）
    for start in range(0, 2 * size - 1):
        line = []
        for k in range(size):
            x, y = k, start - k
            if 0 <= x < size and 0 <= y < size:
                line.append((x, y))
        if len(line) >= 5:
            lines.append(line)

    return lines


# 快取所有線段（棋盤大小固定後不變）
_cached_lines = None
_cached_size = None


def get_lines_cached(board):
    global _cached_lines, _cached_size
    size = len(board)
    if _cached_size != size:
        _cached_lines = get_all_lines(board)
        _cached_size = size
    return _cached_lines


def evaluate_board(board) -> int:
    """
    評估函數：回傳「白方分數 - 黑方分數」(White 視角正值)。
    對每條掃描線分別計算 BLACK / WHITE 的型樣分數。
    黑方分數乘以懲罰係數以體現防守優先策略。
    """
    lines = get_lines_cached(board)
    white_score = 0
    black_score = 0

    for line in lines:
        white_score += scan_line(board, line, WHITE)
        black_score += scan_line(board, line, BLACK)

    return white_score - int(black_score * BLACK_PENALTY)


# ──────────────────────────────────────────────
# Move Generation
# ──────────────────────────────────────────────

def has_winning_move(board, color: int):
    """
    快速檢查 color 方是否有立即獲勝的棋步。
    回傳 (x, y) 或 None。
    """
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_legal_move(board, x, y, color):
                if is_win_after_move(board, x, y, color):
                    return (x, y)
    return None


def has_open_four(board, x: int, y: int, color: int) -> bool:
    """判斷落子 (x,y) 後 color 方是否形成 open_four。"""
    for dx, dy in DIRECTIONS:
        if is_open_four_in_direction(board, x, y, color, dx, dy):
            return True
    return False


def has_four(board, x: int, y: int, color: int) -> bool:
    """判斷落子 (x,y) 後 color 方是否形成任意四連（open 或 closed）。"""
    for dx, dy in DIRECTIONS:
        if line_total(board, x, y, dx, dy, color) >= 4:
            return True
    return False


def has_open_three(board, x: int, y: int, color: int) -> bool:
    """判斷落子 (x,y) 後 color 方是否形成 open_three。"""
    for dx, dy in DIRECTIONS:
        if has_open_three_in_direction_for_black(board, x, y, dx, dy) if color == BLACK \
                else _white_open_three_dir(board, x, y, dx, dy):
            return True
    return False


def _white_open_three_dir(board, x: int, y: int, dx: int, dy: int) -> bool:
    """白方 open_three 方向判斷：落子後在此方向形成 open_four 的空間。"""
    size = len(board)
    # 嘗試放一顆子後，若此方向有空格可進一步形成 open_four
    left = count_dir(board, x, y, -dx, -dy, WHITE)
    right = count_dir(board, x, y, dx, dy, WHITE)
    total = 1 + left + right
    if total != 3:
        return False
    lx = x - (left + 1) * dx
    ly = y - (left + 1) * dy
    rx = x + (right + 1) * dx
    ry = y + (right + 1) * dy
    left_open = in_bounds(lx, ly, size) and board[ly][lx] == EMPTY
    right_open = in_bounds(rx, ry, size) and board[ry][rx] == EMPTY
    return left_open and right_open


def move_priority(board, x: int, y: int, player: int) -> int:
    """
    計算落子 (x,y) 的啟發優先級分數（越高越優先搜尋）。
    用於 ordered_move 的排序鍵值。
    """
    opp = opponent(player)

    # 暫時落子
    board[y][x] = player

    priority = 0

    # (a) 白方直接獲勝
    if is_win_after_move(board, x, y, player):
        board[y][x] = EMPTY
        return 10_000_000

    # (c) 白方形成 open_four 或 closed_four
    if has_four(board, x, y, player):
        priority += 500_000

    # (e) 白方形成 open_three
    if has_open_three(board, x, y, player):
        priority += 50_000

    board[y][x] = EMPTY

    # (b) 防守對方五連
    board[y][x] = opp
    if is_win_after_move(board, x, y, opp):
        board[y][x] = EMPTY
        return 9_000_000  # 僅次於直接獲勝

    # (d) 防守對方 open_four
    if has_open_four(board, x, y, opp):
        priority += 800_000

    # 防守對方一般 four
    if has_four(board, x, y, opp):
        priority += 100_000

    board[y][x] = EMPTY

    # (f) 局部靜態評分增量
    board[y][x] = player
    local = evaluate_board(board) #整個盤面誰佔優勢、優勢多少
    #local=occupied_neighbors(board, x, y, 2) * 10
    board[y][x] = EMPTY
    priority += local

    return priority


def ordered_move(board, player: int, lookahead: int, max_candidates: int, radius: int) -> list:
    """
    產生並排序候選棋步，回傳最多 max_candidates 個 (x, y)。

    參數:
        board          : 當前棋盤
        player         : 當前落子方（通常為 WHITE）
        lookahead      : 搜尋深度（供未來擴充使用）
        max_candidates : 候選棋步上限
        radius         : 考慮已有棋子周圍 radius 格內的空格

    回傳:
        list of (x, y)，依啟發分數由高至低排序
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
# Minimax with Alpha-Beta Pruning
# ──────────────────────────────────────────────

def minimax(board, depth: int, alpha: int, beta: int,
            is_max_layer: bool, last_x: int, last_y: int):
    """
    Minimax 搜尋含 Alpha-Beta 剪枝與 Transposition Table。

    參數:
        board        : 當前棋盤
        depth        : 剩餘搜尋深度
        alpha        : Alpha 值（MAX 層下界）
        beta         : Beta 值（MIN 層上界）
        is_max_layer : True = WHITE（最大化），False = BLACK（最小化）
        last_x, last_y : 上一手落子位置（用於判斷終局）

    回傳:
        (score, best_x, best_y)
    """
    # Step1: Base Case ──────────────────────────────
    # 判斷上一手落子者
    last_player = BLACK if is_max_layer else WHITE  # 剛落完子的是對手
    # 上一手是否已獲勝
    if  last_x >= 0 and is_win_after_move(board, last_x, last_y, last_player):
        if last_player == WHITE:
            return WIN_SCORE + depth, -1, -1   # 越快贏分越高
        else:
            return -WIN_SCORE - depth, -1, -1
    
    if board_full(board):
        return 0, -1, -1  # DRAW: return score = 0

    if depth == 0:
        return evaluate_board(board), -1, -1 #  到達搜尋底部，靜態評估
    # ───────────────────────────────────────────────


    # Step2: Transposition Table 查表 ──────────────
    key = board_key(board)
    if key in trans_table:
        entry = trans_table[key]
        if entry['depth'] >= depth:
            flag = entry['flag']
            s = entry['score']
            if flag == 'exact':
                return s, entry['x'], entry['y']
            elif flag == 'lower' and s >= beta:
                return s, entry['x'], entry['y']
            elif flag == 'upper' and s <= alpha:
                return s, entry['x'], entry['y']
    # ──────────────────────────────────────────



    # Step3: ── 決定當前落子方 ─────────────────────────
    current_player = WHITE if is_max_layer else BLACK

    # ── 產生候選棋步 ──────────────────────────
    moves = ordered_move(board,player=current_player,lookahead=depth,max_candidates=ARGS.max_candidates,radius=ARGS.neighbor_radius)

    if not moves:
        return evaluate_board(board), -1, -1

    best_score = -INF if is_max_layer else INF
    best_x, best_y = moves[0]
    orig_alpha = alpha

    for x, y in moves:
        board[y][x] = current_player

        score, _, _ = minimax(
            board, depth - 1, alpha, beta,
            not is_max_layer, x, y
        )

        board[y][x] = EMPTY

        if is_max_layer:
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
            alpha = max(alpha, best_score)
        else:
            if score < best_score:
                best_score = score
                best_x, best_y = x, y
            beta = min(beta, best_score)

        if alpha >= beta:
            break  # Alpha-Beta 剪枝

    # ── Transposition Table 存表 ──────────────
    if best_score <= orig_alpha:
        flag = 'upper'
    elif best_score >= beta:
        flag = 'lower'
    else:
        flag = 'exact'

    trans_table[key] = {
        'score': best_score,
        'depth': depth,
        'flag': flag,
        'x': best_x,
        'y': best_y,
    }

    return best_score, best_x, best_y


# ──────────────────────────────────────────────
# Read Board & Main (不可修改)
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


def choose_move(board):
    """
    選出最佳落子位置。
    1. 空盤落中央
    2. 若白方有直接獲勝棋步，立即落子
    3. 若黑方有 open_four 或即將獲勝，優先防守
    4. 否則呼叫 Minimax 搜尋
    """
    global trans_table
    trans_table = {}  # 每回合清空，避免過期快取

    size = len(board)

    # ── 空盤落中央 ────────────────────────────
    if is_empty_board(board):
        c = size // 2
        return c, c

    # ── (a) 白方直接獲勝 ──────────────────────
    win_move = has_winning_move(board, WHITE)
    if win_move:
        return win_move

    # ── (b) 防守黑方即將獲勝 ──────────────────
    block_move = has_winning_move(board, BLACK)
    if block_move:
        # 確認此位置對白方合法（若非法則退回 minimax）
        bx, by = block_move
        if is_legal_move(board, bx, by, WHITE):
            return bx, by

    # ── Minimax 搜尋 ──────────────────────────
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