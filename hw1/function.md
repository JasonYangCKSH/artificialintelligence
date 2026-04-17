```py
def opponent(color: int) -> int:
def create_board(size: int):
def in_bounds(x: int, y: int, size: int) -> bool:
def board_full(board) -> bool:
def count_dir(board, x: int, y: int, dx: int, dy: int, color: int) -> int:
def line_total(board, x: int, y: int, dx: int, dy: int, color: int) -> int:
def is_overline_after_move(board, x: int, y: int, color: int) -> bool:
def is_exact_five_after_move(board, x: int, y: int, color: int) -> bool:
def is_win_after_move(board, x: int, y: int, color: int) -> bool:
def is_open_four_in_direction(board, x: int, y: int, color: int, dx: int, dy: int) -> bool:
def has_four_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:
def has_open_three_in_direction_for_black(board, x: int, y: int, dx: int, dy: int) -> bool:
def count_black_four_directions(board, x: int, y: int) -> int:
def count_black_open_three_directions(board, x: int, y: int) -> int:
def is_black_forbidden_after_move(board, x: int, y: int) -> bool:
def is_legal_move(board, x: int, y: int, color: int) -> bool:
def legal_moves(board, color: int):
def format_board(board) -> str:
def occupied_neighbors(board, x: int, y: int, radius: int = 1) -> int:
def is_empty_board(board) -> bool:
```
