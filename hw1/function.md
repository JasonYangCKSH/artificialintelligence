# 一、基本工具函數（Utility）

def opponent(color: int) -> int:

def create_board(size: int):

def in_bounds(x: int, y: int, size: int) -> bool:

def board_full(board) -> bool:

def is_empty_board(board) -> bool:

# 二、連線計算核心（Line Analysis）
單向連線子數：
def count_dir(board, x: int, y: int, dx: int, dy: int, color: int) -> int:
雙向連線子數：
def line_total(board, x: int, y: int, dx: int, dy: int, color: int) -> int:



# 三、勝負判斷（Win / Overline）
長連：
def is_overline_after_move(board, x: int, y: int, color: int) -> bool:
五連：
def is_exact_five_after_move(board, x: int, y: int, color: int) -> bool:
勝負判斷：
def is_win_after_move(board, x: int, y: int, color: int) -> bool:


# 四、棋型判斷（Pattern Detection）
活四：
def is_open_four_in_direction(board, x: int, y: int, color: int, dx: int, dy: int) -> bool:
黑棋四（用於禁手）:
def has_four_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:
黑棋活三（用於禁手）:
def has_open_three_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:


# 五、禁手規則（Black Forbidden Rules）

def count_black_four_directions(board, x: int, y: int) -> int:

def count_black_open_three_directions(board, x: int, y: int) -> int:

def is_black_forbidden_after_move(board, x: int, y: int) -> bool:


# 六、合法落子（Move Legality）

def is_legal_move(board, x: int, y: int, color: int) -> bool:

# 七、輔助工具（Debug / Heuristic）

def format_board(board) -> str:

def occupied_neighbors(board, x: int, y: int, radius: int = 1) -> int: