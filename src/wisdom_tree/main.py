import curses
import os
import threading
import time
from pathlib import Path
from typing import Any

from wisdom_tree.audio import (
    MediaPlayer,
    adjust_media_volume,
    play_sound,
    toggle_sounds,
)
from wisdom_tree.config import (
    EFFECT_VOLUME,
    GROWTH_SOUND,
    QUOTE_FILE_NAME,
    RES_FOLDER,
    TIMER_START_SOUND,
)
from wisdom_tree.timer import PomodoroTimer
from wisdom_tree.tree import TreeManager
from wisdom_tree.ui import (
    MenuSystem,
    NotificationSystem,
    YouTubeInterface,
    add_animated_text,
    init_screen,
)
from wisdom_tree.utils import QuoteManager, StateManager, get_user_config_directory

os.environ["VLC_VERBOSE"] = "-1"


class WisdomTreeApp:
    def __init__(self, stdscr: Any):
        self.stdscr = stdscr
        self.state_manager = StateManager(RES_FOLDER / "treedata")
        initial_age = self.state_manager.load_tree_age()

        self.tree_manager = TreeManager(initial_age)
        self.timer = PomodoroTimer()
        self.quote_manager = QuoteManager()
        self.menu = MenuSystem()
        self.notifications = NotificationSystem()
        self.youtube_interface = YouTubeInterface()

        music_list = list(RES_FOLDER.glob("*ogg"))
        self.media_player = MediaPlayer(music_list)
        self.media_player.media.play()

        self.pause = False
        self.pausetime = 0

    def handle_pause(self) -> None:
        if self.media_player.media.is_playing():
            self.media_player.media.pause()
        self.pause = True
        self.pausetime = time.time()

    def handle_media_selection(self, index: int, maxx: int, stdscr: Any) -> None:
        if index == 0:  # YouTube music
            if hasattr(self.media_player, "media"):
                self.media_player.media.stop()
            self.youtube_interface.youtubedisplay = True
        elif index == 1:  # Concentration music
            if hasattr(self.media_player, "media"):
                self.media_player.media.stop()
            self.media_player.play_youtube(
                "https://www.youtube.com/watch?v=oPVte6aMprI", True, self
            )

    def handle_media_seek(self, offset: int, maxx: int) -> None:
        current_time = self.media_player.media.get_time()
        length = self.media_player.media.get_length()

        if offset > 0:
            if current_time + offset < length:
                self.media_player.media.set_time(i_time=current_time + offset)
            else:
                self.media_player.media.set_time(length - 1)
        else:
            if current_time + offset > 0:
                self.media_player.media.set_time(i_time=current_time + offset)
            else:
                self.media_player.media.set_time(0)

        time_sec = self.media_player.media.get_time() / 1000
        display_time = f"{int(time_sec / 60):02d}:{int(time_sec) % 60:02d}"
        try:
            progress = (
                self.media_player.media.get_time()
                / self.media_player.media.get_length()
            )
            message = " " * (round(maxx * progress) - len(display_time)) + display_time
            self.notifications.notify(message, invert=True)
        except ZeroDivisionError:
            pass

    def handle_media_position(self, position: float, maxx: int) -> None:
        length = self.media_player.media.get_length()
        self.media_player.media.set_time(i_time=int(length * position))
        time_sec = self.media_player.media.get_time() / 1000
        display_time = f"{int(time_sec / 60):02d}:{int(time_sec) % 60:02d}"
        message = " " * (round(maxx * position) - len(display_time)) + display_time
        self.notifications.notify(message, invert=True)

    def save_and_exit(self) -> None:
        self.state_manager.save_tree_age(self.tree_manager.get_age())
        exit()

    def run_main_loop(self) -> None:
        seconds = 5
        anilen = 1
        anispeed = 1

        quote = self.quote_manager.get_random_quote()
        play_sound(GROWTH_SOUND)

        try:
            while True:
                start = time.time()

                try:
                    self.stdscr.erase()
                    maxy, maxx = self.stdscr.getmaxyx()

                    # Display quote
                    add_animated_text(
                        int(maxx / 2), int(maxy * 5 / 6), quote, anilen, self.stdscr, 2
                    )
                    anilen += anispeed
                    if anilen > 150:
                        anilen = 150

                    # Update quote and tree growth every 10 minutes
                    if seconds % (100 * 60 * 10) == 0:
                        quote = self.quote_manager.get_random_quote()
                        self.tree_manager.tree.grow()
                        anilen = 1
                        play_sound(GROWTH_SOUND)

                    # Display tree
                    self.tree_manager.display(self.stdscr, maxx, maxy, seconds)

                    # Display timer if active
                    self.timer.display_work_timer(self.stdscr, maxy, maxx)

                    # Display menu
                    self.menu.display(self.stdscr, maxy, maxx)

                    # Handle YouTube interface
                    song_input = self.youtube_interface.show_input(self.stdscr, maxx)
                    if song_input:
                        is_url = self.youtube_interface.is_url(song_input)
                        thread = threading.Thread(
                            target=self.media_player.play_youtube,
                            args=(song_input, is_url, self),
                        )
                        thread.daemon = True
                        thread.start()

                    if self.media_player.downloaddisplay:
                        self.media_player.show_loading_spinner(self.stdscr, maxx)

                    # Update timer
                    self.timer.update(self.media_player.media)

                    # Handle media end
                    self.media_player.handle_media_end()

                    # Show notifications
                    self.notifications.show(self.stdscr, maxy, maxx)

                    # Handle input
                    key_events(self.stdscr, self, maxx)

                    # Handle pause state
                    while self.pause:
                        self.stdscr.erase()
                        self.stdscr.addstr(
                            int(maxy * 3 / 5),
                            int(maxx / 2 - len("PAUSED") / 2),
                            "PAUSED",
                            curses.A_BOLD,
                        )
                        key = self.stdscr.getch()
                        if key == ord(" "):
                            self.pause = False
                            self.media_player.media.play()
                            self.stdscr.refresh()
                            if self.timer.istimer:
                                self.timer.workendtime += time.time() - self.pausetime
                        if key == ord("q"):
                            self.save_and_exit()
                        time.sleep(0.1)

                    # Handle break state
                    while self.timer.isbreak:
                        self.stdscr.erase()
                        self.stdscr.addstr(
                            int(maxy * 3 / 5),
                            int(maxx / 2 - len("PRESS SPACE TO END BREAK") / 2),
                            "PRESS SPACE TO END BREAK",
                            curses.A_BOLD,
                        )
                        break_ended = self.timer.display_break_timer(
                            self.stdscr, maxy, maxx
                        )
                        if break_ended:
                            self.media_player.media.play()

                        self.stdscr.refresh()
                        key = self.stdscr.getch()

                        if key == ord(" "):
                            self.timer.end_break_early(self.media_player.media)
                        if key == ord("q"):
                            self.save_and_exit()
                        time.sleep(0.1)

                    time.sleep(max(0.05 - (time.time() - start), 0))
                    seconds += 5

                except KeyboardInterrupt:
                    try:
                        self.stdscr.erase()
                        self.stdscr.addstr(
                            int(maxy * 3 / 5),
                            int(maxx / 2 - len("PRESS 'q' TO EXIT") / 2),
                            "PRESS 'q' TO EXIT",
                            curses.A_BOLD,
                        )
                        self.stdscr.refresh()
                        time.sleep(1)
                    except KeyboardInterrupt:
                        pass

                self.stdscr.refresh()

        finally:
            curses.echo()
            curses.nocbreak()
            curses.curs_set(1)
            self.stdscr.keypad(False)
            self.stdscr.nodelay(False)
            curses.endwin()


def key_events(stdscr: Any, app: WisdomTreeApp, maxx: int) -> None:
    global EFFECT_VOLUME
    key = stdscr.getch()

    # Update menu activity timestamp on navigation keys
    if key in (
        curses.KEY_UP,
        ord("k"),
        curses.KEY_DOWN,
        ord("j"),
        curses.KEY_RIGHT,
        ord("l"),
        curses.KEY_LEFT,
        ord("h"),
        27,
    ):
        app.menu.menu_last_active = time.time()

    # Menu navigation
    if key in (curses.KEY_UP, ord("k")):
        app.menu.navigate_up()
    elif key in (curses.KEY_DOWN, ord("j")):
        app.menu.navigate_down()
    elif key in (curses.KEY_RIGHT, ord("l")):
        app.menu.navigate_right()
    elif key in (curses.KEY_LEFT, ord("h"), 27):
        app.menu.navigate_left()
    elif key == curses.KEY_ENTER or key in [10, 13]:
        main_item, sub_index = app.menu.select()
        if main_item == "POMODORO TIMER":
            app.timer.start_timer(sub_index, stdscr, maxx)
            play_sound(TIMER_START_SOUND)
        elif main_item == "MEDIA":
            app.handle_media_selection(sub_index, maxx, stdscr)
            play_sound(TIMER_START_SOUND)
        app.menu.show_sub_menu = False

    # Application controls
    if key == ord("q"):
        app.save_and_exit()
    if key == ord("u"):
        toggle_sounds()
    if key == ord(" "):
        app.handle_pause()
    if key == ord("m"):
        app.media_player.media.pause()
    if key == ord("]"):
        new_volume = app.media_player.media.audio_get_volume() + 1
        adjust_media_volume(app, new_volume, maxx)
    if key == ord("["):
        new_volume = app.media_player.media.audio_get_volume() - 1
        adjust_media_volume(app, new_volume, maxx)
    if key == ord("}"):
        EFFECT_VOLUME = min(100, EFFECT_VOLUME + 1)
        app.notifications.notify(f"Effects: {EFFECT_VOLUME}%", invert=True)
    if key == ord("{"):
        EFFECT_VOLUME = max(0, EFFECT_VOLUME - 1)
        app.notifications.notify(f"Effects: {EFFECT_VOLUME}%", invert=True)
    if key == ord("="):
        app.handle_media_seek(10000, maxx)
    if key == ord("-"):
        app.handle_media_seek(-10000, maxx)
    if key == ord("r"):
        app.media_player.isloop = not app.media_player.isloop
        app.notifications.notify(f"REPEAT: {app.media_player.isloop}")
    for i in range(10):
        if key == ord(str(i)):
            app.handle_media_position(i / 10, maxx)


def main(stdscr: Any) -> None:
    init_screen(stdscr)
    app = WisdomTreeApp(stdscr)
    app.run_main_loop()


def run():
    """Entry point for the CLI command."""
    config_file = Path(get_user_config_directory()) / "wisdom-tree" / QUOTE_FILE_NAME
    if config_file.exists():
        # Note: This would need to be handled differently in the new structure
        pass
    curses.wrapper(main)


if __name__ == "__main__":
    run()
