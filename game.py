import sys
from string import ascii_lowercase as letters
from typing import List, Tuple

import numpy as np
import numpy.random as npr

POINTS = {
    3: 3,
    4: 10,
    5: 25,
}


class IllegalMove(Exception):
    pass


def countrange(x: int):
    return range(1, x + 1)


class SwapplesBoard:

    COLORS = ["red", "blue", "green", "yellow", "purple", "_"]

    def __init__(self, w=8, h=8, n_colors=5):
        self.board = np.zeros((h, w), dtype=bool)
        self.w = w
        self.h = h
        self.n_colors = n_colors

        self.init_board()

    def init_board(self):
        self.board = npr.randint(1, self.n_colors + 1, size=self.board.shape)

    def check_contiguous(x, y):
        pass

    def illegal_move(self, msg: str):
        print("Illegal move: " + msg, file=sys.stderr)
        raise IllegalMove(msg)

    def validate_col(self, col: str) -> int:
        assert len(col) == 1
        if col not in letters:
            self.illegal_move(f"illegal column {col}")
        cx = letters.index(col)
        if cx >= self.w:
            self.illegal_move(f"column {col} out of bounds")
        return cx

    def validate_row(self, row: str):
        assert len(row) == 1
        try:
            rx = int(row)
        except ValueError:
            self.illegal_move(f"illegal row {row}")
        if rx >= self.h:
            self.illegal_move(f"row {row} out of bounds")
        return rx

    def swap_horizontal(self, row: int, cx: int, cy: int) -> None:
        """
        Performs the specified swap in-place.

        Swaps columns cx,cy in row.
        """
        assert row < self.h
        assert cx < self.w
        assert cy < self.w
        assert abs(cx - cy) == 1

        t = self.board[row, cx].copy()
        self.board[row, cx] = self.board[row, cy]
        self.board[row, cy] = t

    def swap_vertical(self, rx: int, ry: int, col: int) -> None:
        """
        Performs the specified swap in-place.

        Swaps rows rx,cy in col.
        """
        assert rx < self.h
        assert ry < self.h
        assert col < self.w
        assert abs(rx - ry) == 1

        t = self.board[rx, col].copy()
        self.board[rx, col] = self.board[ry, col]
        self.board[ry, col] = t

    def propagate_or_reject_swap(
        self, acc_succ: bool = False, acc_score: int = 0, draw: bool = True
    ) -> Tuple[bool, int]:

        found_any = False
        for color in countrange(self.n_colors):
            # check for vertical patterns
            for col in range(self.w):
                for rx in range(self.h - 2):
                    found = 0
                    if not all(self.board[rx : rx + 3, col] == color):
                        continue
                    # we have found 3.
                    found = 3
                    self.board[rx : rx + 3, col] = 0
                    found_any = True
                    for delta in countrange(2):
                        if rx + delta >= self.h:
                            break
                        if self.board[rx + delta, col] == color:
                            found += 1
                            self.board[rx + delta, col] = 0
                        else:
                            break

                    if found > 0:
                        acc_score += POINTS[found]
                        acc_succ = True
                        if draw:
                            self.draw_board()

            del rx

            # check for horizontal patterns
            for row in range(self.h):
                for cx in range(self.w - 2):
                    if not all(self.board[row, cx : cx + 3] == color):
                        continue
                    # we have found 3.
                    found = 3
                    self.board[row, cx : cx + 3] = 0
                    found_any = True
                    for delta in countrange(2):
                        if cx + delta >= self.w:
                            break
                        if self.board[row, cx + delta] == color:
                            found += 1
                            self.board[row, cx - delta] = 0
                        else:
                            break
                    if found > 0:
                        acc_score += POINTS[found]
                        acc_succ = True
                        if draw:
                            self.draw_board()
        if not found_any:
            return acc_succ, acc_score
        else:
            self.shake_board()
            if draw:
                self.draw_board()
            return self.propagate_or_reject_swap(acc_succ, acc_score, draw=draw)

    def draw_board(self) -> str:
        out: List[List[str]] = []

        # column labels
        out.append('   ' + ''.join(str(x) for x in range(self.w)))
        out.append(['   '] + ['_'] * self.w)

        for row, rl in zip(range(self.h), letters):
            # row labels
            out.append([rl + ' |'])
            for col in range(self.w):
                # FIXME stopgap till we can get some pretty colors in here
                out[-1].append(self.COLORS[self.board[row, col] - 1][0].upper())


        out = "\n".join(["".join(row) for row in out])

        print("===============")
        print(out)
        return out

    def shake_board(self):
        # TODO this function is not exactly a paragon of efficiency...
        # we make up the slack by eschewing graphics
        while (self.board == 0).any():
            rs, cs = np.where(self.board == 0)
            # the lowest row with a zero
            row = rs[0]
            col = cs[0]

            # the height of the zero column
            delta = 1
            # identify solid vertical blocks of zeros, assuming where
            # returns the indices sorted ascending
            while (row + delta < self.h) and self.board[row + delta, col] == 0:
                delta += 1

            # this is the new column of values which will occupy the spaces
            # 0, 1, ..., <row>
            new_col_cap = npr.randint(1, self.n_colors + 1, size=(row + delta,))
            # the bottom <row> values of it are the ones that drop
            if row > 0:
                new_col_cap[-row:] = self.board[:row, col]
            self.board[: row + delta, col] = new_col_cap

    def make_move(self, move: str) -> Tuple[bool, int]:
        """
        [move] is a three-character string 'abc' in the format {row}{row}{col}
        (i.e. swap a,b in col c) or {row}{col}{col} (i.e. swap b,c in row a)

        Returns whether the move was accepted (i.e. the board state changed)
        and the score.
        """

        a, b, c = move

        ax = self.validate_col(a)
        cx = self.validate_row(c)

        backup_board = self.board.copy()

        if b in letters:
            bx = self.validate_col(b)
            if abs(ax - bx) != 1:
                self.illegal_move("can only swap adjacent HYPERENTITIES")
            self.swap_vertical(ax, bx, cx)
        else:
            bx = self.validate_row(b)
            if abs(cx - bx) != 1:
                self.illegal_move("can only swap adjacent HYPERENTITIES")
            self.swap_horizontal(ax, bx, cx)

        accept, score = self.propagate_or_reject_swap()
        if not accept:
            # you lose a point every time you make a pointless swap
            self.board = backup_board
            return (False, -1)
        else:
            return True, score


if __name__ == "__main__":

    game = SwapplesBoard()
    game.propagate_or_reject_swap(draw=False)
    game.draw_board()

    total_score = 0
    while (move := input("move: ")) != "quit":
        _, score = game.make_move(move)
        total_score += score
        print(f"score = {total_score}")
