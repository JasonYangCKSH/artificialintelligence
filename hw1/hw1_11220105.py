import sys


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
    # 請在此實作你的白棋策略
    # 回傳 (x, y)
    return 7, 7


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