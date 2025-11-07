#!/usr/bin/env python3
import curses
import random
import time
from typing import Deque, Tuple


Position = Tuple[int, int]


class SnakeGame:
    def __init__(self, height: int = 20, width: int = 40, speed: int = 120) -> None:
        if height < 5 or width < 10:
            raise ValueError("网格尺寸过小，无法启动游戏。")

        self.height = height
        self.width = width
        self.speed = speed  # 毫秒

        self.snake: Deque[Position] = self._create_initial_snake()
        self.direction: Position = (0, 1)  # 初始向右
        self.pending_direction: Position = self.direction

        self.food: Position = self._generate_food()
        self.score = 0
        self.is_over = False

    def _create_initial_snake(self) -> Deque[Position]:
        from collections import deque

        row = self.height // 2
        start = self.width // 2 - 1
        snake = deque(
            [(row, start + i) for i in range(3)]
        )  # 身体列表最后一个元素是蛇头
        return snake

    def _generate_food(self) -> Position:
        while True:
            pos = (
                random.randint(1, self.height - 2),
                random.randint(1, self.width - 2),
            )
            if pos not in self.snake:
                return pos

    def _next_head(self) -> Position:
        head_row, head_col = self.snake[-1]
        d_row, d_col = self.direction
        return head_row + d_row, head_col + d_col

    def _collides(self, position: Position) -> bool:
        row, col = position
        # 边界碰撞
        if row <= 0 or row >= self.height - 1:
            return True
        if col <= 0 or col >= self.width - 1:
            return True
        # 自撞
        if position in self.snake:
            return True
        return False

    def change_direction(self, new_direction: Position) -> None:
        # 防止在同一帧内反向移动导致死亡
        opposite = (-self.direction[0], -self.direction[1])
        if new_direction != opposite:
            self.pending_direction = new_direction

    def tick(self) -> None:
        if self.is_over:
            return

        self.direction = self.pending_direction
        new_head = self._next_head()

        if self._collides(new_head):
            self.is_over = True
            return

        self.snake.append(new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self._generate_food()
        else:
            self.snake.popleft()

    def draw(self, window: "curses.window") -> None:
        window.clear()
        window.border()

        try:
            food_row, food_col = self.food
            window.addch(food_row, food_col, ord("@"))

            for row, col in list(self.snake)[:-1]:
                window.addch(row, col, ord("o"))

            head_row, head_col = self.snake[-1]
            window.addch(head_row, head_col, ord("O"))

            score_text = f" Score: {self.score} "
            if self.width > 4:
                window.addnstr(0, 2, score_text, self.width - 4)
        except curses.error:
            pass

        window.refresh()


DIRECTION_KEYS = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
}


def run(stdscr: "curses.window") -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)

    height, width = stdscr.getmaxyx()

    min_height, min_width = 7, 14
    if height < min_height or width < min_width:
        stdscr.nodelay(False)
        stdscr.clear()
        warning = "Terminal window too small for Snake."
        hint = f"Min size: {min_height}x{min_width}. Resize and press any key."
        stdscr.addnstr(0, 0, warning, max(0, width - 1))
        stdscr.addnstr(2, 0, hint, max(0, width - 1))
        stdscr.refresh()
        stdscr.getch()
        return

    # 给边框留出空间
    usable_height = max(5, height - 2)
    usable_width = max(10, width - 2)

    game = SnakeGame(height=usable_height, width=usable_width, speed=120)

    last_tick = time.time()

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        if key in DIRECTION_KEYS:
            game.change_direction(DIRECTION_KEYS[key])

        now = time.time()
        if (now - last_tick) * 1000 >= game.speed:
            game.tick()
            last_tick = now

        game.draw(stdscr)

        if game.is_over:
            message = " Game over! Press r to restart, q to quit "
            start_col = max(1, (game.width - len(message)) // 2)
            try:
                if game.width > 2:
                    stdscr.addnstr(game.height // 2, start_col, message, game.width - 2)
            except curses.error:
                pass
            stdscr.refresh()

            while True:
                retry_key = stdscr.getch()
                if retry_key == ord("q"):
                    return
                if retry_key == ord("r"):
                    game = SnakeGame(height=usable_height, width=usable_width, speed=game.speed)
                    last_tick = time.time()
                    break
        time.sleep(0.01)


def main() -> None:
    curses.wrapper(run)


if __name__ == "__main__":
    main()
