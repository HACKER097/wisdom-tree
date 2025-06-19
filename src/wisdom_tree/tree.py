import curses
import random
import time
from typing import Any

from wisdom_tree.config import RES_FOLDER
from wisdom_tree.ui import add_animated_text, print_art


class TreeDisplay:
    def __init__(self, age: int = 1):
        self.age = age
        self.artfile = ""
        random.seed(int(time.time() / (60 * 60 * 24)))
        self.season = random.choice(
            ["rain", "heavy_rain", "light_rain", "snow", "windy"]
        )
        random.seed()

    def get_art_file(self) -> str:
        if self.age >= 1 and self.age < 5:
            return str(RES_FOLDER / "p1.txt")
        elif self.age >= 5 and self.age < 10:
            return str(RES_FOLDER / "p2.txt")
        elif self.age >= 10 and self.age < 20:
            return str(RES_FOLDER / "p3.txt")
        elif self.age >= 20 and self.age < 30:
            return str(RES_FOLDER / "p4.txt")
        elif self.age >= 30 and self.age < 40:
            return str(RES_FOLDER / "p5.txt")
        elif self.age >= 40 and self.age < 70:
            return str(RES_FOLDER / "p6.txt")
        elif self.age >= 70 and self.age < 120:
            return str(RES_FOLDER / "p7.txt")
        elif self.age >= 120 and self.age < 200:
            return str(RES_FOLDER / "p8.txt")
        else:  # age >= 200
            return str(RES_FOLDER / "p9.txt")

    def display(self, stdscr: Any, maxx: int, maxy: int) -> None:
        self.artfile = self.get_art_file()
        print_art(stdscr, self.artfile, int(maxx / 2), int(maxy * 3 / 4), 1)
        add_animated_text(
            int(maxx / 2),
            int(maxy * 3 / 4),
            "age: " + str(int(self.age)) + " ",
            -1,
            stdscr,
            3,
        )

    def grow(self) -> None:
        self.age += 1

    def set_age(self, age: int) -> None:
        self.age = age


class SeasonalEffects:
    def __init__(self, season: str):
        self.season = season

    def render_rain(
        self,
        stdscr: Any,
        maxx: int,
        maxy: int,
        seconds: int,
        intensity: int,
        speed: int,
        char: str,
        color_pair: int,
    ) -> None:
        random.seed(int(seconds / speed))

        for i in range(intensity):
            ry = random.randrange(int(maxy * 1 / 4), int(maxy * 3 / 4))
            rx = random.randrange(int(maxx / 3), int(maxx * 2 / 3))
            stdscr.addstr(ry, rx, char, curses.color_pair(color_pair))

        random.seed()

    def render(self, stdscr: Any, maxx: int, maxy: int, seconds: int) -> None:
        if self.season == "rain":
            self.render_rain(stdscr, maxx, maxy, seconds, 30, 30, "/", 4)
        elif self.season == "light_rain":
            self.render_rain(stdscr, maxx, maxy, seconds, 30, 60, "`", 4)
        elif self.season == "heavy_rain":
            self.render_rain(stdscr, maxx, maxy, seconds, 40, 20, "/", 4)
        elif self.season == "snow":
            self.render_rain(stdscr, maxx, maxy, seconds, 30, 30, ".", 5)
        elif self.season == "windy":
            self.render_rain(stdscr, maxx, maxy, seconds, 20, 30, "-", 4)


class TreeManager:
    def __init__(self, initial_age: int = 1):
        self.tree = TreeDisplay(initial_age)
        self.effects = SeasonalEffects(self.tree.season)
        self.last_growth = time.time()
        self.growth_interval = 600  # 10 minutes

    def update(self, quote_changed: bool = False) -> None:
        if quote_changed:
            self.tree.grow()

    def display(self, stdscr: Any, maxx: int, maxy: int, seconds: int) -> None:
        self.tree.display(stdscr, maxx, maxy)
        self.effects.render(stdscr, maxx, maxy, seconds)

    def get_age(self) -> int:
        return int(self.tree.age)

    def set_age(self, age: int) -> None:
        self.tree.set_age(age)

    def save_age(self) -> int:
        return int(self.tree.age)

    def load_age(self, age: int) -> None:
        self.tree.set_age(age)
