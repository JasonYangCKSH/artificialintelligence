import sys
import time
import argparse
from common import *

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
WHITE_WIN_SCORE = 100_000_000
BLACK_WIN_SCORE = 90_000_000
WHITE_OPEN_4 = 6_000_000
BLACK_OPEN_4 = 8_000_000
WHITE_CLOSED_4 = 1_500_000
BLACK_CLOSED_4 = 700_000
WHITE_OPEN_3 = 240_000
BLACK_OPEN_3 = 480_000
WHITE_CLOSED_3 = 60_000
BLACK_CLOSED_3 = 120_000
WHITE_OPEN_2 = 15_000
BLACK_OPEN_2 = 14_000
WHITE_CLOSED_2 = 4_000
BLACK_CLOSED_2 = 4_000

WHITE_MULTIPLE_OPEN_4 = 9_000_000
WHITE_4_3 = 4_000_000
WHITE_MULTIPLE_OPEN_3 = 1_200_000
BLACK_MULTIPLE_OPEN_4 = 12_000_000
BLACK_4_3 = 7_000_000
BLACK_MULTIPLE_OPEN_3 = 4_000_000

THREAT = 1.2


INF = 10**18
TIME_LIMIT = 4.9
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=5, help="minimax search depth")
    parser.add_argument("--max-candidates", type=int, default=7, help="candidate move cap")
    parser.add_argument("--neighbor-radius", type=int, default=2, help="generate moves near existing stones")
    return parser.parse_args()

ARGS = parse_args()


# Transposition Table（跨節點快取，每回合清空）
trans_table = {}


def board_key(board):
    """將棋盤轉為可雜湊的 tuple，作為 transposition table 的 key。"""
    return tuple(tuple(row) for row in board)


# Evaluation Function


def count_open_num(board, x: int, y: int, t: int) -> int:
    if t <= 1 or t >= 5: 
        return 0
    size = len(board)
    color = board[y][x]
    count = 0
    for dx, dy in DIRECTIONS:
        left = count_dir(board, x, y, -dx, -dy, color)
        right = count_dir(board, x, y, dx, dy, color)
        total = 1 + left + right

        if total != t:
            continue

        lx = x - (left + 1) * dx
        ly = y - (left + 1) * dy
        rx = x + (right + 1) * dx
        ry = y + (right + 1) * dy

        left_open = in_bounds(lx, ly, size) and board[ly][lx] == EMPTY
        right_open = in_bounds(rx, ry, size) and board[ry][rx] == EMPTY

        if left_open and right_open:
            count+=1

    return count
def count_closed_num(board, x: int, y: int, t: int)->int:
    if t <= 1 or t >= 5: 
        return 0
    size = len(board)
    color = board[y][x]
    count = 0
    for dx, dy in DIRECTIONS:
        left = count_dir(board, x, y, -dx, -dy, color)
        right = count_dir(board, x, y, dx, dy, color)
        total = 1 + left + right

        if total != t:
            continue

        lx = x - (left + 1) * dx
        ly = y - (left + 1) * dy
        rx = x + (right + 1) * dx
        ry = y + (right + 1) * dy

        left_open = in_bounds(lx, ly, size) and board[ly][lx] == EMPTY
        right_open = in_bounds(rx, ry, size) and board[ry][rx] == EMPTY

        if left_open ^ right_open:
            count+=1

    return count

def evaluate_board(board) -> int:
    size = len(board)
    score = 0

    # 1. 逐方向序列計分（錨點 = 序列在該方向的起始格
    # 每條序列只從最靠前的那顆子計算，避免 N 顆子把同一段計 N 次
    for y in range(size):
        for x in range(size):
            color = board[y][x]
            if color == EMPTY:
                continue

            for dx, dy in DIRECTIONS:
                # 若往反方向還有同色子，代表本格不是起點 → 跳過
                px, py = x - dx, y - dy
                if in_bounds(px, py, size) and board[py][px] == color:
                    continue

                length = 1 + count_dir(board, x, y, dx, dy, color)
                if length < 2:
                    continue

                # 判斷兩端開放性
                lx, ly = x - dx, y - dy           # 序列前端外一格
                ex, ey = x + length * dx, y + length * dy  # 序列後端外一格
                left_open  = in_bounds(lx, ly, size) and board[ly][lx] == EMPTY
                right_open = in_bounds(ex, ey, size) and board[ey][ex] == EMPTY

                # 5 連以上
                if length >= 5:
                    score += WHITE_WIN_SCORE if color == WHITE else -BLACK_WIN_SCORE
                    continue

                # 白方加分
                if color == WHITE:
                    if length == 4:
                        if   left_open and right_open: score += WHITE_OPEN_4
                        elif left_open or  right_open: score += WHITE_CLOSED_4
                    elif length == 3:
                        if   left_open and right_open: score += WHITE_OPEN_3
                        elif left_open or  right_open: score += WHITE_CLOSED_3
                    elif length == 2:
                        if   left_open and right_open: score += WHITE_OPEN_2
                        elif left_open or  right_open: score += WHITE_CLOSED_2
                # 黑方扣分
                else:
                    if length == 4:
                        if   left_open and right_open: score -= BLACK_OPEN_4
                        elif left_open or  right_open: score -= BLACK_CLOSED_4
                    elif length == 3:
                        if   left_open and right_open: score -= BLACK_OPEN_3
                        elif left_open or  right_open: score -= BLACK_CLOSED_3
                    elif length == 2:
                        if   left_open and right_open: score -= BLACK_OPEN_2
                        elif left_open or  right_open: score -= BLACK_CLOSED_2

    # 2. Combo 加／扣分（叉口偵測，與 move_priority 邏輯一致）
    # count_open_num 從某格看所有方向，只有真正身處多方向交叉的棋子
    # 才會同時滿足 open4 >= 2 / open3 >= 2 / open4+open3 >= 1 等條件
    for y in range(size):
        for x in range(size):
            color = board[y][x]
            if color == EMPTY:
                continue

            open4 = count_open_num(board, x, y, 4)
            open3 = count_open_num(board, x, y, 3)

            if color == WHITE:
                if open4 >= 2:                    score += WHITE_MULTIPLE_OPEN_4
                if open3 >= 2:                    score += WHITE_MULTIPLE_OPEN_3
                if open4 >= 1 and open3 >= 1:    score += WHITE_4_3
            else:  # BLACK
                if open4 >= 2:                    score -= BLACK_MULTIPLE_OPEN_4
                if open3 >= 2:                    score -= BLACK_MULTIPLE_OPEN_3
                if open4 >= 1 and open3 >= 1:    score -= BLACK_4_3

    return score


def move_priority(board, x: int, y: int, player: int) -> int:
    """
    計算落子 (x,y) 的啟發優先級分數（越高越優先搜尋）。
    用於 ordered_move 的排序鍵值。
    """
    size = len(board)
    opp = opponent(player)
    priority = 0
    if not is_legal_move(board, x, y, player):
        return -1
    # win move
    board[y][x] = player
    if is_win_after_move(board, x, y, player):
        if player == WHITE:
            priority += WHITE_WIN_SCORE
        elif player == BLACK:
            priority += BLACK_WIN_SCORE
    board[y][x] = EMPTY

    # block opponent win move
    board[y][x] = opp
    if is_win_after_move(board, x, y, opp):
        if opp == BLACK:
            priority += BLACK_WIN_SCORE
        elif opp == WHITE:
            priority += WHITE_WIN_SCORE
    board[y][x] = EMPTY

    # ==================================================
    # CREATE 
    # ==================================================

    board[y][x] = player

    open4 = count_open_num(board, x, y, 4)
    closed4 = count_closed_num(board, x, y, 4)
    open3 = count_open_num(board, x, y, 3)
    closed3 = count_closed_num(board, x, y, 3)
    open2 = count_open_num(board, x, y, 2)
    closed2 = count_closed_num(board, x, y, 2)
    if player == WHITE:                          # WIHTE → WHITE
        priority += open4   * WHITE_OPEN_4
        priority += closed4 * WHITE_CLOSED_4
        priority += open3   * WHITE_OPEN_3
        priority += closed3 * WHITE_CLOSED_3
        priority += open2   * WHITE_OPEN_2
        priority += closed2 * WHITE_CLOSED_2
        if open3 >= 2:          priority += WHITE_MULTIPLE_OPEN_3
        if open4 >= 2:          priority += WHITE_MULTIPLE_OPEN_4
        if open4 >= 1 and open3 >= 1: priority += WHITE_4_3
    elif player == BLACK:
        priority += open4   * BLACK_OPEN_4
        priority += closed4 * BLACK_CLOSED_4
        priority += open3   * BLACK_OPEN_3
        priority += closed3 * BLACK_CLOSED_3
        priority += open2   * BLACK_OPEN_2
        priority += closed2 * BLACK_CLOSED_2
        if open3 >= 2:          priority += BLACK_MULTIPLE_OPEN_3
        if open4 >= 2:          priority += BLACK_MULTIPLE_OPEN_4
        if open4 >= 1 and open3 >= 1: priority += BLACK_4_3
    board[y][x] = EMPTY

    # ==================================================
    # BLOCK
    # ==================================================

    board[y][x] = opp
    open4 = count_open_num(board, x, y, 4)
    closed4 = count_closed_num(board, x, y, 4)
    open3 = count_open_num(board, x, y, 3)
    closed3 = count_closed_num(board, x, y, 3)
    open2 = count_open_num(board, x, y, 2)
    closed2 = count_closed_num(board, x, y, 2)
    if opp == WHITE:                            
        priority += open4   * WHITE_OPEN_4   * THREAT
        priority += closed4 * WHITE_CLOSED_4 * THREAT
        priority += open3   * WHITE_OPEN_3   * THREAT
        priority += closed3 * WHITE_CLOSED_3 * THREAT
        priority += open2   * WHITE_OPEN_2   * THREAT
        priority += closed2 * WHITE_CLOSED_2 * THREAT
        if open3 >= 2:               priority += WHITE_MULTIPLE_OPEN_3 * THREAT
        if open4 >= 2:               priority += WHITE_MULTIPLE_OPEN_4 * THREAT
        if open4 >= 1 and open3 >= 1: priority += WHITE_4_3            * THREAT
    elif opp == BLACK:
        priority += open4   * BLACK_OPEN_4   * THREAT
        priority += closed4 * BLACK_CLOSED_4 * THREAT
        priority += open3   * BLACK_OPEN_3   * THREAT
        priority += closed3 * BLACK_CLOSED_3 * THREAT
        priority += open2   * BLACK_OPEN_2   * THREAT
        priority += closed2 * BLACK_CLOSED_2 * THREAT
        if open3 >= 2:               priority += BLACK_MULTIPLE_OPEN_3 * THREAT
        if open4 >= 2:               priority += BLACK_MULTIPLE_OPEN_4 * THREAT
        if open4 >= 1 and open3 >= 1: priority += BLACK_4_3            * THREAT
    board[y][x] = EMPTY
  


    # Position Heuristic
    neighbors = occupied_neighbors(board, x, y, radius=2)
    priority += neighbors * 3_000

    center = size // 2
    max_dist = 2 * center
    dist = abs(x - center) + abs(y - center)
    priority += (max_dist - dist) * 1_000


    
    # Black Forbidden trap
    if player == WHITE:
        board[y][x] = BLACK
        if is_black_forbidden_after_move(board, x, y):
            priority += 40_000
        board[y][x] = EMPTY
    
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


# Minimax with Alpha-Beta Pruning

def minimax(board, depth: int, alpha: int, beta: int,
            is_max_layer: bool, last_x: int, last_y: int):

    if time.time() - _start_time > TIME_LIMIT:
        return evaluate_board(board), -1, -1 
    # Step1: Base Case
    # 判斷上一手落子者
    last_player = BLACK if is_max_layer else WHITE  # 剛落完子的是對手
    # 上一手是否已獲勝
    if  last_x >= 0 and is_win_after_move(board, last_x, last_y, last_player):
        if last_player == WHITE:
            return WHITE_WIN_SCORE + depth, -1, -1   # 越快贏分越高
        else:
            return -BLACK_WIN_SCORE - depth, -1, -1
    
    if board_full(board):
        return 0, -1, -1  # DRAW: return score = 0

    if depth == 0:
        return evaluate_board(board), -1, -1 #  到達搜尋底部，靜態評估
   


    # Step2: Transposition Table 查表 
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
    



    # Step3: 決定當前落子方
    current_player = WHITE if is_max_layer else BLACK

    # 產生候選棋步
    moves = ordered_move(board,player=current_player,lookahead=depth,max_candidates=ARGS.max_candidates,radius=ARGS.neighbor_radius)

    if not moves:
        return evaluate_board(board), -1, -1

    best_score = -INF if is_max_layer else INF
    best_x, best_y = moves[0]
    orig_alpha = alpha

    for x, y in moves:
        board[y][x] = current_player
        # ------------------------------->DFS itself <------------------------------
        score, _, _ = minimax(
            board, depth - 1, alpha, beta,
            not is_max_layer, x, y
        )

        board[y][x] = EMPTY
        # 往上回傳
        if is_max_layer:
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
            alpha = max(alpha, best_score) # parent = bigger child
        else:
            if score < best_score:
                best_score = score
                best_x, best_y = x, y
            beta = min(beta, best_score) # parent = smaller child

        if alpha >= beta:
            break  # Alpha-Beta 剪枝

    #  Transposition Table 存表 
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


# Read Board & Main
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
    global _start_time
    _start_time = time.time()
    global trans_table
    trans_table = {}  

    size = len(board)

    # 空盤落中央
    if is_empty_board(board):
        c = size // 2
        return c, c

    # (a) 白方直接獲勝
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_legal_move(board, x, y, WHITE):
                if is_win_after_move(board, x, y, WHITE):
                    return x, y
    # (b) 防守黑方即將獲勝 
    size = len(board)
    for y in range(size):
        for x in range(size):
            if board[y][x] == EMPTY and is_legal_move(board, x, y, BLACK):
                if is_win_after_move(board, x, y, BLACK):
                    return x, y


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