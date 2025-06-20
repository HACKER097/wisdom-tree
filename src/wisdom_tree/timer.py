import curses
import time
from typing import Any

from wisdom_tree.audio import play_sound
from wisdom_tree.config import ALARM_SOUND, TIMER_BREAK, TIMER_WORK


class PomodoroTimer:
    def __init__(self):
        self.istimer = False
        self.isbreak = False
        self.breakover = False
        self.worktime = 0
        self.breaktime = 0
        self.workendtime = 0
        self.breakendtime = 0
        self.pausetime = 0
        self.pause = False
        self.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"

    def start_timer(self, timer_index: int, stdscr: Any, maxx: int) -> None:
        if timer_index == 5:  # END TIMER NOW
            self.breakendtext = "TIMER IS OVER, PRESS ENTER"
            self.worktime = 0
            self.breaktime = 0
            self.istimer = False
        elif timer_index == 4:  # CUSTOM TIMER
            self._handle_custom_timer(stdscr, maxx)
        else:  # Preset timers
            self.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"
            self.istimer = True
            self.worktime = TIMER_WORK[timer_index]
            self.breaktime = TIMER_BREAK[timer_index]
            self.workendtime = int(time.time()) + self.worktime

    def _handle_custom_timer(self, stdscr: Any, maxx: int) -> None:
        try:
            curses.textpad.rectangle(stdscr, 0, 0, 2, maxx - 1)
            stdscr.addstr(1, 1, "ENTER WORK LENGTH (min) : ")
            stdscr.refresh()

            curses.echo()
            curses.nocbreak()
            stdscr.nodelay(False)
            stdscr.keypad(False)
            curses.curs_set(1)

            self.worktime = int(stdscr.getstr()) * 60

            stdscr.addstr(1, 1, " " * (maxx - 2))
            stdscr.addstr(1, 1, "ENTER BREAK LENGTH (min) : ")
            stdscr.refresh()

            self.breaktime = int(stdscr.getstr()) * 60

            self._restore_screen_settings(stdscr)
            self.istimer = True
            self.workendtime = int(time.time()) + self.worktime

        except ValueError:
            self._restore_screen_settings(stdscr)
            # Notification will be handled by caller
            return

    def _restore_screen_settings(self, stdscr: Any) -> None:
        curses.noecho()
        curses.cbreak()
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.curs_set(0)

    def update(self, media_player: Any) -> None:
        if self.istimer and int(time.time()) >= int(self.workendtime):
            self.start_break(media_player)

    def start_break(self, media_player: Any) -> None:
        if self.istimer:
            play_sound(ALARM_SOUND)
            if media_player.is_playing():
                media_player.pause()
            self.breakendtime = int(time.time()) + self.breaktime
            self.istimer = False
            self.isbreak = True

    def display_work_timer(self, stdscr: Any, maxy: int, maxx: int) -> None:
        if self.istimer:
            remaining = max(0, int(self.workendtime - time.time()))
            timer_text = "WORK: {:02d}:{:02d}".format(remaining // 60, remaining % 60)
            stdscr.addstr(
                int(maxy * 10 / 11),
                int(maxx / 2 - len(timer_text) // 2),
                timer_text,
                curses.color_pair(1),
            )

    def display_break_timer(self, stdscr: Any, maxy: int, maxx: int) -> bool:
        if self.isbreak:
            seconds_left = int(self.breakendtime) - int(time.time())
            timer_text = (
                "Break ends in: "
                + str(int(seconds_left / 60)).zfill(2)
                + ":"
                + str(seconds_left % 60).zfill(2)
            )
            stdscr.addstr(
                int(maxy * 10 / 11), int(maxx / 2 - len(timer_text) / 2), timer_text
            )

            if seconds_left <= 0:
                self.isbreak = False
                self.breakover = True
                play_sound(ALARM_SOUND)
                return True
        return False

    def handle_pause(self, media_player: Any) -> None:
        if not self.pause:
            return

        if media_player.is_playing():
            media_player.pause()
        self.pausetime = time.time()

    def resume_from_pause(self, media_player: Any) -> None:
        self.pause = False
        media_player.play()
        if self.istimer:
            self.workendtime += time.time() - self.pausetime

    def end_break_early(self, media_player: Any) -> None:
        if self.isbreak:
            self.isbreak = False
            media_player.play()

    def get_remaining_work_time(self) -> int:
        if self.istimer:
            return max(0, int(self.workendtime - time.time()))
        return 0

    def get_remaining_break_time(self) -> int:
        if self.isbreak:
            return max(0, int(self.breakendtime - time.time()))
        return 0
