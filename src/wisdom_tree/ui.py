import curses
import curses.textpad
import re
import time
from typing import Any

from wisdom_tree.config import TIMER_WORK_MINS, TIMER_BREAK_MINS

YOUTUBE_REGEX = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$")


def replace_nth(s: str, source: str, target: str, n: int) -> str:
    inds = [
        i for i in range(len(s) - len(source) + 1) if s[i : i + len(source)] == source
    ]
    if len(inds) < n:
        return s
    s = list(s)
    s[inds[n - 1] : inds[n - 1] + len(source)] = target
    return "".join(s)


def add_animated_text(
    x: int, y: int, text: str, anilen: int, stdscr: Any, color_pair: int
) -> None:
    text = replace_nth(text[: int(anilen)], " ", "#", 10)
    text = text.split("#")
    for i in range(len(text)):
        stdscr.addstr(
            y + i,
            int(x - len(text[i]) / 2),
            str(text[i]),
            curses.color_pair(color_pair),
        )


def print_art(stdscr: Any, file_path: str, x: int, y: int, color_pair: int) -> None:
    with open(file_path, "r", encoding="utf8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        stdscr.addstr(
            y + i - len(lines),
            x - int(len(max(lines, key=len)) / 2),
            lines[i],
            curses.color_pair(color_pair),
        )


class MenuSystem:
    def __init__(self):
        self.main_menu = ["POMODORO TIMER", "MEDIA"]
        self.sub_menus = {
            "POMODORO TIMER": [
                f" POMODORO {TIMER_WORK_MINS[0]}+{TIMER_BREAK_MINS[0]} ",
                f" POMODORO {TIMER_WORK_MINS[1]}+{TIMER_BREAK_MINS[1]} ",
                f" POMODORO {TIMER_WORK_MINS[2]}+{TIMER_BREAK_MINS[2]} ",
                f" POMODORO {TIMER_WORK_MINS[3]}+{TIMER_BREAK_MINS[3]} ",
                " CUSTOM TIMER ",
                " END TIMER NOW ",
            ],
            "MEDIA": [" PLAY MUSIC FROM YOUTUBE ", " ~CONCENTRATION MUSIC "],
        }
        self.current_main_index = 0
        self.current_sub_index = 0
        self.show_sub_menu = False
        self.menu_last_active = time.time()

    def display(self, stdscr: Any, maxy: int, maxx: int) -> None:
        if time.time() - self.menu_last_active < 5:
            start_y = int(maxy / 2) - len(self.main_menu)
            for idx, item in enumerate(self.main_menu):
                style = (
                    curses.A_REVERSE
                    if idx == self.current_main_index and not self.show_sub_menu
                    else curses.A_NORMAL
                )
                stdscr.addstr(start_y + idx * 2, 2, item, style)

            if self.show_sub_menu:
                submenu_items = self.sub_menus[self.main_menu[self.current_main_index]]
                submenu_start_y = start_y
                max_item_len = max(len(item) for item in submenu_items)
                submenu_x = maxx - max_item_len - 2
                for idx, item in enumerate(submenu_items):
                    style = (
                        curses.A_REVERSE
                        if idx == self.current_sub_index
                        else curses.A_NORMAL
                    )
                    stdscr.addstr(submenu_start_y + idx * 2, submenu_x, item, style)

    def navigate_up(self) -> None:
        self.menu_last_active = time.time()
        if self.show_sub_menu:
            self.current_sub_index = (self.current_sub_index - 1) % len(
                self.sub_menus[self.main_menu[self.current_main_index]]
            )
        else:
            self.current_main_index = (self.current_main_index - 1) % len(
                self.main_menu
            )

    def navigate_down(self) -> None:
        self.menu_last_active = time.time()
        if self.show_sub_menu:
            self.current_sub_index = (self.current_sub_index + 1) % len(
                self.sub_menus[self.main_menu[self.current_main_index]]
            )
        else:
            self.current_main_index = (self.current_main_index + 1) % len(
                self.main_menu
            )

    def navigate_right(self) -> None:
        self.menu_last_active = time.time()
        if not self.show_sub_menu:
            self.show_sub_menu = True
            self.current_sub_index = 0

    def navigate_left(self) -> None:
        self.menu_last_active = time.time()
        self.show_sub_menu = False

    def select(self) -> tuple[str, int]:
        if self.show_sub_menu:
            current_main = self.main_menu[self.current_main_index]
            return current_main, self.current_sub_index
        return "", -1


class NotificationSystem:
    def __init__(self):
        self.notifyendtime = 0
        self.isnotify = False
        self.notifystring = " "
        self.invert = False

    def show(self, stdscr: Any, maxy: int, maxx: int) -> None:
        if self.isnotify and time.time() <= self.notifyendtime:
            curses.textpad.rectangle(stdscr, 0, 0, 2, maxx - 1)
            if self.invert:
                stdscr.addstr(
                    1,
                    1,
                    self.notifystring[: maxx - 2],
                    curses.A_BOLD | curses.A_REVERSE,
                )
            else:
                stdscr.addstr(1, 1, self.notifystring[: maxx - 2], curses.A_BOLD)

    def notify(self, message: str, duration: int = 2, invert: bool = False) -> None:
        self.notifyendtime = int(time.time()) + duration
        self.notifystring = message
        self.invert = invert
        self.isnotify = True


class YouTubeInterface:
    def __init__(self):
        self.youtubedisplay = False
        self.downloaddisplay = False

    def show_input(self, stdscr: Any, maxx: int) -> str:
        if self.youtubedisplay:
            curses.textpad.rectangle(stdscr, 0, 0, 2, maxx - 1)
            stdscr.addstr(1, 1, "SEARCH or PASTE URL [type 'q' to exit]: ")
            stdscr.refresh()

            curses.echo()
            curses.nocbreak()
            stdscr.nodelay(False)
            stdscr.keypad(False)
            curses.curs_set(1)

            song_input = stdscr.getstr().decode("utf-8")

            curses.noecho()
            curses.cbreak()
            stdscr.nodelay(True)
            stdscr.keypad(True)
            curses.curs_set(0)

            if song_input != "q":
                stdscr.addstr(1, 1, "GETTING AUDIO")
                self.downloaddisplay = True
                self.youtubedisplay = False
                return song_input

            self.youtubedisplay = False
        return ""

    def is_url(self, song_input: str) -> bool:
        return bool(YOUTUBE_REGEX.match(song_input))


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    try:
        curses.init_pair(1, 113, -1)
        curses.init_pair(2, 85, -1)
        curses.init_pair(3, 3, -1)
        curses.init_pair(4, 51, -1)
        curses.init_pair(5, 15, -1)
        curses.init_pair(6, 1, -1)
        curses.init_pair(7, curses.COLOR_YELLOW, -1)
    except Exception:
        curses.init_pair(1, 1, 0)
        curses.init_pair(2, 1, 0)
        curses.init_pair(3, 1, 0)
        curses.init_pair(4, 1, 0)
        curses.init_pair(5, 1, 0)
        curses.init_pair(6, 1, 0)
        curses.init_pair(7, 1, 0)


def init_screen(stdscr: Any) -> None:
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    init_colors()
