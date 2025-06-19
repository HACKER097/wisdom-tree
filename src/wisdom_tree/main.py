# todo: add day/year progress bar
# todo: add todo list
# todo: add key listner event for changing the quote

import os
import curses
from curses import textpad
import time
import random
import pickle
from pathlib import Path
import re
YOUTUBE_REGEX = re.compile(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$')
import urllib.request
import threading
import vlc
import requests
from pytubefix import YouTube
import logging
from typing import Any

# Import config values from config.py
from wisdom_tree.config import RES_FOLDER, QUOTE_FOLDER, QUOTE_FILE_NAME, QUOTE_FILE, TIMER_WORK_MINS, TIMER_BREAK_MINS, TIMER_WORK, TIMER_BREAK, SOUNDS_MUTED, TIMER_START_SOUND, ALARM_SOUND, GROWTH_SOUND, EFFECT_VOLUME

os.environ['VLC_VERBOSE'] = '-1'

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_config_directory():
    """Returns a platform-specific root directory for user config settings."""
    # On Windows, prefer %LOCALAPPDATA%, then %APPDATA%, since we can expect the
    # AppData directories to be ACLed to be visible only to the user and admin
    # users (https://stackoverflow.com/a/7617601/1179226). If neither is set,
    # return None instead of falling back to something that may be world-readable.
    if os.name == "nt":
        appdata = os.getenv("LOCALAPPDATA")
        if appdata:
            return appdata
        appdata = os.getenv("APPDATA")
        if appdata:
            return appdata
        return None
    # On non-windows, use XDG_CONFIG_HOME if set, else default to ~/.config.
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return xdg_config_home
    return os.path.join(os.path.expanduser("~"), ".config")

def play_sound(sound: str) -> None:
    '''plays the sound if not muted'''
    if SOUNDS_MUTED and sound != ALARM_SOUND:
        return
    try:
        media = vlc.MediaPlayer(sound)
        media.audio_set_volume(EFFECT_VOLUME)
        media.play()
    except Exception as e:
        logging.error("Error playing sound: %s", e)

def toggle_sounds() -> None:
    global SOUNDS_MUTED
    SOUNDS_MUTED = not SOUNDS_MUTED
    logging.info("Sound toggled, muted: %s", SOUNDS_MUTED)

def isinternet():
    try:
        urllib.request.urlopen("https://youtube.com", timeout = 10) #Python 3.x
        return True
    except:
        return False

def replaceNth(
    s, source, target, n
):  # code from stack overflow, replaces nth occurence of an item.
    inds = [
        i for i in range(len(s) - len(source) + 1) if s[i : i + len(source)] == source
    ]
    if len(inds) < n:
        return s  # or maybe raise an error
    s = list(s)  # can't assign to string slices. So, let's listify
    s[
        inds[n - 1] : inds[n - 1] + len(source)
    ] = target  # do n-1 because we start from the first occurrence of the string, not the 0-th
    return "".join(s)


def addtext(
    x, y, text, anilen, stdscr, color_pair
):  # adds and animates text in the center

    text = replaceNth(
        text[: int(anilen)], " ", "#", 10
    )  # aads "#" after the 7th word to split line
    text = text.split("#")  # splits text into 2 list
    for i in range(len(text)):
        stdscr.addstr(
            y + i,
            int(x - len(text[i]) / 2),
            str(text[i]),
            curses.color_pair(color_pair),
        )  # displays the list in 2 lines

# Cache quotes in memory
try:
    with open(QUOTE_FILE, encoding="utf8") as f:
        QUOTES_CACHE = f.read().splitlines()
except Exception:
    QUOTES_CACHE = []

def getrandomline(file: Path) -> str:
    with open(file, "r", encoding="utf8") as f:
        lines = f.read().splitlines()
    return random.choice(lines)

def getqt() -> str:
    return random.choice(QUOTES_CACHE) if QUOTES_CACHE else ""

def printart(
    stdscr, file, x, y, color_pair
):
    '''prints line one by one to display text art, also in the middle'''
    with open(file, "r", encoding="utf8") as f:
        lines = f.readlines()

        for i in range(len(lines)):
            stdscr.addstr(
                y + i - len(lines),
                x - int(len(max(lines, key=len)) / 2),
                lines[i],
                curses.color_pair(color_pair),
            )


def adjust_media_volume(tree1: Any, new_volume: int, maxx: int) -> None:
    tree1.media.audio_set_volume(max(0, min(100, new_volume)))
    tree1.notifyendtime = int(time.time()) + 2
    volume_str = f"{round(new_volume)}%"
    tree1.notifystring = " " * round(maxx * (new_volume / 100) - len(volume_str) - 2) + volume_str
    tree1.invert = True
    tree1.isnotify = True

def GetLinks(search_string):
    search_url = "https://www.youtube.com/results?search_query=" + search_string.replace(" ", "+")
    # html = urllib.request.urlopen()
    html = requests.get(search_url)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.content.decode())
    return "http://youtube.com/watch?v=" + str(video_ids[0])

def key_events(stdscr: Any, tree1: Any, maxx: int) -> None:
    global EFFECT_VOLUME  # Moved global declaration to the top.
    key = stdscr.getch()
    # Update menu activity timestamp on navigation keys
    if key in (curses.KEY_UP, ord("k"), curses.KEY_DOWN, ord("j"), curses.KEY_RIGHT, ord("l"), curses.KEY_LEFT, ord("h"), 27):
        tree1.menu_last_active = time.time()

    # New menu navigation logic
    if key in (curses.KEY_UP, ord("k")):
        if tree1.show_sub_menu:
            tree1.current_sub_index = (tree1.current_sub_index - 1) % len(tree1.sub_menus[tree1.main_menu[tree1.current_main_index]])
        else:
            tree1.current_main_index = (tree1.current_main_index - 1) % len(tree1.main_menu)
    elif key in (curses.KEY_DOWN, ord("j")):
        if tree1.show_sub_menu:
            tree1.current_sub_index = (tree1.current_sub_index + 1) % len(tree1.sub_menus[tree1.main_menu[tree1.current_main_index]])
        else:
            tree1.current_main_index = (tree1.current_main_index + 1) % len(tree1.main_menu)
    elif key in (curses.KEY_RIGHT, ord("l")):
        if not tree1.show_sub_menu:
            tree1.show_sub_menu = True
            tree1.current_sub_index = 0
    elif key in (curses.KEY_LEFT, ord("h"), 27):  # Left arrow or Escape key
        tree1.show_sub_menu = False
    elif key == curses.KEY_ENTER or key in [10, 13]:
        if tree1.show_sub_menu:
            current_main = tree1.main_menu[tree1.current_main_index]
            if current_main == "POMODORO TIMER":
                tree1.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"
                tree1.starttimer(tree1.current_sub_index, stdscr, maxx)
            elif current_main == "MEDIA":
                tree1.featureselect(tree1.current_sub_index, maxx, stdscr)
            play_sound(TIMER_START_SOUND)
            tree1.show_sub_menu = False
        # If no sub menu, ignore enter
    # Existing controls for quitting, toggling sounds, media controls, etc.
    if key == ord("q"):
        with open(RES_FOLDER / "treedata", "wb") as treedata:
            pickle.dump(tree1.age, treedata, protocol=None)
        exit()
    if key == ord("u"):
        toggle_sounds()
    if key == ord(" "):
        if tree1.media.is_playing():
            tree1.media.pause()
        tree1.pause = True
        tree1.pausetime = time.time()
    if key == ord("m"):
        tree1.media.pause()
    if key == ord("]"):
        new_volume = tree1.media.audio_get_volume() + 1
        adjust_media_volume(tree1, new_volume, maxx)
    if key == ord("["):
        new_volume = tree1.media.audio_get_volume() - 1
        adjust_media_volume(tree1, new_volume, maxx)
    if key == ord("}"):
        EFFECT_VOLUME = min(100, EFFECT_VOLUME + 1)
        tree1.notifyendtime = int(time.time()) + 2
        volume = str(EFFECT_VOLUME) + "%"
        tree1.notifystring = " " * round(maxx * (EFFECT_VOLUME / 100) - len(volume) - 2) + volume
        tree1.invert = True
        tree1.isnotify = True
    if key == ord("{"):
        EFFECT_VOLUME = max(0, EFFECT_VOLUME - 1)
        tree1.notifyendtime = int(time.time()) + 2
        volume = str(EFFECT_VOLUME) + "%"
        tree1.notifystring = " " * round(maxx * (EFFECT_VOLUME / 100) - len(volume) - 2) + volume
        tree1.invert = True
        tree1.isnotify = True
    if key == ord("="):
        if tree1.media.get_time() + 10000 < tree1.media.get_length():
            tree1.media.set_time(i_time=tree1.media.get_time() + 10000)
        else:
            tree1.media.set_time(tree1.media.get_length() - 1)
        time_sec = tree1.media.get_time() / 1000
        display_time = str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60)
        tree1.notifyendtime = int(time.time()) + 2
        try:
            tree1.notifystring = " " * (round(maxx * (tree1.media.get_time() / tree1.media.get_length())) - len(display_time)) + display_time
        except ZeroDivisionError:
            pass
        tree1.invert = True
        tree1.isnotify = True
    if key == ord("-"):
        if tree1.media.get_time() - 10000 > 0:
            tree1.media.set_time(i_time=tree1.media.get_time() - 10000)
        else:
            tree1.media.set_time(0)
        time_sec = tree1.media.get_time() / 1000
        display_time = str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60)
        tree1.notifyendtime = int(time.time()) + 2
        tree1.notifystring = " " * (round(maxx * (tree1.media.get_time() / tree1.media.get_length())) - len(display_time)) + display_time
        tree1.invert = True
        tree1.isnotify = True
    if key == ord("r"):
        if tree1.isloop:
            tree1.isloop = False
        else:
            tree1.isloop = True
        tree1.notifyendtime = int(time.time()) + 2
        tree1.notifystring = "REPEAT: " + str(tree1.isloop)
        tree1.invert = False
        tree1.isnotify = True
    for i in range(10):
        if key == ord(str(i)):
            tree1.media.set_time(i_time=int(tree1.media.get_length() * (i / 10)))
            time_sec = tree1.media.get_time() / 1000
            display_time = str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60)
            tree1.notifyendtime = int(time.time()) + 2
            tree1.notifystring = " " * (round(maxx * (tree1.media.get_time() / tree1.media.get_length())) - len(display_time)) + display_time
            tree1.invert = True
            tree1.isnotify = True

class tree:
    def __init__(self, stdscr, age):
        self.stdscr = stdscr
        self.age = age
        self.show_music = False
        self.music_list = list(_ for _ in RES_FOLDER.glob("*ogg"))
        self.music_list_num = 0
        self.media = vlc.MediaPlayer(str(self.music_list[self.music_list_num]))
        self.pause = False
        self.showtimer = False
        self.timerlist = [
            " POMODORO {}+{} ".format(TIMER_WORK_MINS[0], TIMER_BREAK_MINS[0]),
            " POMODORO {}+{} ".format(TIMER_WORK_MINS[1], TIMER_BREAK_MINS[1]),
            " POMODORO {}+{} ".format(TIMER_WORK_MINS[2], TIMER_BREAK_MINS[2]),
            " POMODORO {}+{} ".format(TIMER_WORK_MINS[3], TIMER_BREAK_MINS[3]),
            " CUSTOM TIMER ",
            " END TIMER NOW ",
        ]
        
        self.featurelist = [
            " PLAY MUSIC FROM YOUTUBE ",
            " ~CONCENTRATION MUSIC "
        ]
        self.currentmenu = "timer"
        self.selectedtimer = 0
        self.istimer = False
        self.isbreak = False
        self.breakover = False
        self.timerhidetime = 0
        random.seed(int(time.time() / (60 * 60 * 24)))
        self.season = random.choice(
            ["rain", "heavy_rain", "light_rain", "snow", "windy"]
        )
        random.seed()
        self.youtubedisplay = False
        self.downloaddisplay = False
        self.spinnerstate = 0
        self.notifyendtime = 0
        self.isnotify = False
        self.notifystring = " "
        self.playlist = None  # Removed lofi radio playlist
        self.radiomode = False  # Not used anymore.
        self.isloading = False
        self.invert = False
        self.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"
        self.isloop = False
        # Remove old timerlist and featurelist; add new main menu and sub menus
        self.main_menu = ["POMODORO TIMER", "MEDIA"]
        self.sub_menus = {
            "POMODORO TIMER": [
                " POMODORO {}+{} ".format(TIMER_WORK_MINS[0], TIMER_BREAK_MINS[0]),
                " POMODORO {}+{} ".format(TIMER_WORK_MINS[1], TIMER_BREAK_MINS[1]),
                " POMODORO {}+{} ".format(TIMER_WORK_MINS[2], TIMER_BREAK_MINS[2]),
                " POMODORO {}+{} ".format(TIMER_WORK_MINS[3], TIMER_BREAK_MINS[3]),
                " CUSTOM TIMER ",
                " END TIMER NOW ",
            ],
            "MEDIA": [
                " PLAY MUSIC FROM YOUTUBE ",
                " ~CONCENTRATION MUSIC "
            ]
        }
        self.current_main_index = 0
        self.current_sub_index = 0
        self.show_sub_menu = False
        self.menu_last_active = time.time()  # used for fading menus

    def display(self, maxx, maxy, seconds):
        '''draw the bonsai tree on stdscr'''
        if self.age >= 1 and self.age < 5:
            self.artfile = str(RES_FOLDER/"p1.txt")
        if self.age >= 5 and self.age < 10:
            self.artfile = str(RES_FOLDER/"p2.txt")
        if self.age >= 10 and self.age < 20:
            self.artfile = str(RES_FOLDER/"p3.txt")
        if self.age >= 20 and self.age < 30:
            self.artfile = str(RES_FOLDER/"p4.txt")
        if self.age >= 30 and self.age < 40:
            self.artfile = str(RES_FOLDER/"p5.txt")
        if self.age >= 40 and self.age < 70:
            self.artfile = str(RES_FOLDER/"p6.txt")
        if self.age >= 70 and self.age < 120:
            self.artfile = str(RES_FOLDER/"p7.txt")
        if self.age >= 120 and self.age < 200:
            self.artfile = str(RES_FOLDER/"p8.txt")
        if self.age >= 200:
            self.artfile = str(RES_FOLDER/"p9.txt")

        printart(self.stdscr, self.artfile, int(maxx / 2), int(maxy * 3 / 4), 1)
        addtext(
            int(maxx / 2),
            int(maxy * 3 / 4),
            "age: " + str(int(self.age)) + " ",
            -1,
            self.stdscr,
            3,
        )
        # ADDED: show timer countdown if active
        if self.istimer:
            remaining = max(0, int(self.workendtime - time.time()))
            timer_text = "WORK: {:02d}:{:02d}".format(remaining // 60, remaining % 60)
            self.stdscr.addstr(int(maxy * 3 / 4) + 2, int(maxx/2 - len(timer_text)//2), timer_text, curses.color_pair(2))

    def rain(self, maxx, maxy, seconds, intensity, speed, char, color_pair):
        random.seed(
            int(seconds / speed)
        )  # this keeps the seed same for some time, so rains looks like its going slowly

        # printart(self.stdscr, 'res/rain1.txt', int(maxx/2), int(maxy*3/4), 4)
        for i in range(intensity):
            ry = random.randrange(int(maxy * 1 / 4), int(maxy * 3 / 4))
            rx = random.randrange(int(maxx / 3), int(maxx * 2 / 3))
            self.stdscr.addstr(ry, rx, char, curses.color_pair(color_pair))

        random.seed()

    def seasons(self, maxx, maxy, seconds):
        if self.season == "rain":
            self.rain(maxx, maxy, seconds, 30, 30, "/", 4)

        if self.season == "light_rain":
            self.rain(maxx, maxy, seconds, 30, 60, "`", 4)

        if self.season == "heavy_rain":
            self.rain(maxx, maxy, seconds, 40, 20, "/", 4)

        if self.season == "snow":
            self.rain(maxx, maxy, seconds, 30, 30, ".", 5)

        if self.season == "windy":
            self.rain(maxx, maxy, seconds, 20, 30, "-", 4)

    def notify(self, stdscr, maxy, maxx):
        if self.isnotify and time.time() <= self.notifyendtime:
            curses.textpad.rectangle(stdscr, 0,0,2, maxx-1)
            if self.invert:
                stdscr.addstr(1,1, self.notifystring[:maxx-2], curses.A_BOLD | curses.A_REVERSE)
            else:
                stdscr.addstr(1,1, self.notifystring[:maxx-2], curses.A_BOLD)
            self.downloaddisplay = False
            #self.invert = False

    def menudisplay(self, stdscr, maxy, maxx):
        # Show menus only if active within last 5 seconds (fading effect)
        if time.time() - self.menu_last_active < 5:
            # Draw main menu on left
            start_y = int(maxy / 2) - len(self.main_menu)
            for idx, item in enumerate(self.main_menu):
                style = curses.A_REVERSE if idx == self.current_main_index and not self.show_sub_menu else curses.A_NORMAL
                stdscr.addstr(start_y + idx * 2, 2, item, style)
            # Draw sub menu on the right if active
            if self.show_sub_menu:
                submenu_items = self.sub_menus[self.main_menu[self.current_main_index]]
                submenu_start_y = start_y  # align submenus vertically with main menus
                max_item_len = max(len(item) for item in submenu_items)
                submenu_x = maxx - max_item_len - 2  # position so that long text doesn't spill over
                for idx, item in enumerate(submenu_items):
                    style = curses.A_REVERSE if idx == self.current_sub_index else curses.A_NORMAL
                    stdscr.addstr(submenu_start_y + idx * 2, submenu_x, item, style)

    def breakstart(self):
        if self.istimer:
            play_sound(ALARM_SOUND)
            if self.media.is_playing():
                self.media.pause()
            self.breakendtime = int(time.time()) + self.breaktime
            self.istimer = False
            self.isbreak = True

    def breakdisplay(self, maxx, maxy):
        self.secondsleft = int(self.breakendtime) - int(time.time())
        timertext = (
            "Break ends in: "
            + str(int(self.secondsleft / 60)).zfill(2)
            + ":"
            + str(self.secondsleft % 60).zfill(2)
        )
        self.stdscr.addstr(
            int(maxy * 10 / 11), int(maxx / 2 - len(timertext) / 2), timertext
        )

        if self.secondsleft == 0:
            self.media.play()
            self.isbreak = False
            self.breakover = True
            play_sound(ALARM_SOUND)

    def timer(self):
        if self.istimer and int(time.time()) == int(self.workendtime):
            self.breakstart()

    def starttimer(self, inputtime, stdscr, maxx):
        if inputtime == 5:
            self.breakendtext = "TIMER IS OVER, PRESS ENTER"
            self.worktime = 0
            self.breaktime = 0
            self.istimer = False   # Changed from '==' to '='
        
        elif inputtime == 4:

            try:

                curses.textpad.rectangle(stdscr, 0,0,2, maxx-1)
                stdscr.addstr(1,1, "ENTER WORK LENGTH (min) : ")
                stdscr.refresh()

                curses.echo()
                curses.nocbreak()
                stdscr.nodelay(False)
                stdscr.keypad(False)
                curses.curs_set(1)

                self.worktime = int(stdscr.getstr())*60

                stdscr.addstr(1,1, " "*(maxx-2))
                stdscr.addstr(1,1, "ENTER BREAK LENGTH (min) : ")
                stdscr.refresh()

                self.breaktime = int(stdscr.getstr())*60

                curses.noecho()
                curses.cbreak()
                stdscr.nodelay(True)
                stdscr.keypad(True)
                curses.curs_set(0)

                self.istimer = True

            except ValueError:
                curses.noecho()
                curses.cbreak()
                stdscr.nodelay(True)
                stdscr.keypad(True)
                curses.curs_set(0)

                self.notifystring = "VALUE ERROR, PLEASE ENTER AN INTEGER"
                self.notifyendtime = int(time.time())+5
                self.isnotify = True

                return 0


        else:
            self.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"
            self.istimer = True
            self.worktime = TIMER_WORK[inputtime]
            self.breaktime = TIMER_BREAK[inputtime]

        self.workendtime = int(time.time()) + self.worktime

    def featureselect(self, inputfeature, maxx, stdscr):
        # Only option available originally: PLAY MUSIC FROM YOUTUBE
        if inputfeature == 0:
            if hasattr(self, "media"):
                self.media.stop()
            self.youtubedisplay = True
        elif inputfeature == 1:
            # New preset for concentration music
            if hasattr(self, "media"):
                self.media.stop()
            self.playyoutube("https://www.youtube.com/watch?v=oPVte6aMprI", True)

    def loading(self, stdscr, maxx):
            spinner = [
            "[    ]",
            "[=   ]",
            "[==  ]",
            "[=== ]",
            "[ ===]",
            "[  ==]",
            "[   =]",
            "[    ]",
            "[   =]",
            "[  ==]",
            "[ ===]",
            "[====]",
            "[=== ]",
            "[==  ]",
            "[=   ]"
        ]
            self.spinnerstate+=0.5
            if self.spinnerstate > len(spinner)-1:
                self.spinnerstate = 0
            curses.textpad.rectangle(stdscr, 0,0,2, maxx-1)
            stdscr.addstr(1,1, "GETTING AUDIO  " + spinner[int(self.spinnerstate)])



    def youtube(self, stdscr: Any, maxx: int) -> None:
        if self.youtubedisplay:
            curses.textpad.rectangle(stdscr, 0, 0, 2, maxx - 1)
            stdscr.addstr(1, 1, "SEARCH or PASTE URL [type 'q' to exit]: ")
            stdscr.refresh()

            if not "songinput" in locals():

                curses.echo()
                curses.nocbreak()
                stdscr.nodelay(False)
                stdscr.keypad(False)
                curses.curs_set(1)

                songinput = stdscr.getstr().decode("utf-8")

                curses.noecho()
                curses.cbreak()
                stdscr.nodelay(True)
                stdscr.keypad(True)
                curses.curs_set(0)

            if not songinput == "q":
                stdscr.addstr(1,1, "GETTING AUDIO")

                #BUG: pattern matching doesnt work
                is_url = True if YOUTUBE_REGEX.match(songinput) else False
                getsongthread = threading.Thread(target=self.playyoutube, args=(songinput,is_url))
                getsongthread.daemon = True
                getsongthread.start()

                self.downloaddisplay = True

            del songinput

            self.youtubedisplay = False
            

        if self.downloaddisplay:
            self.loading(stdscr, maxx)


    def playyoutube(self, songinput, is_url: bool):
        # Check for internet connectivity first
        if not isinternet():
            self.notifyendtime = int(time.time()) + 5
            self.notifystring = "NO INTERNET CONNECTION"
            self.isnotify = True
            return

        try:
            yt_url = songinput if is_url else GetLinks(songinput)
            yt = YouTube(yt_url)
            song = yt.streams.get_by_itag(251).url
            self.media = vlc.MediaPlayer(song)
            self.media.play()
        except Exception:
            self.notifyendtime = int(time.time()) + 5
            self.notifystring = "ERROR GETTING AUDIO, PLEASE TRY AGAIN"
            self.isnotify = True
            return

        self.downloaddisplay = False
        self.yt_title = yt.title
        self.notifyendtime = int(time.time()) + 10
        self.notifystring = "Playing: " + self.yt_title
        self.invert = False
        self.isnotify = True

def main(stdscr: Any) -> None:
    # Removed manual curses init; stdscr is provided by curses.wrapper.
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.curs_set(0)
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    curses.use_default_colors()
    # setting color pairs
    try:

        curses.init_pair(1, 113, -1)  # passive selected text inner, outer
        curses.init_pair(2, 85, -1)  # timer color inner, outer
        curses.init_pair(3, 3, -1)  # active selected inner, outer
        curses.init_pair(4, 51, -1)  # border color inner, outer
        curses.init_pair(5, 15, -1)
        curses.init_pair(6, 1, -1)
        curses.init_pair(7, curses.COLOR_YELLOW, -1)

    except:
        curses.init_pair(1, 1, 0)  # passive selected text inner, outer
        curses.init_pair(2, 1, 0)  # timer color inner, outer
        curses.init_pair(3, 1, 0)  # active selected inner, outer
        curses.init_pair(4, 1, 0)  # border color inner, outer
        curses.init_pair(5, 1, 0)
        curses.init_pair(6, 1, 0)
        curses.init_pair(7, 1, 0)


    seconds = 5
    anilen = 1 # animation length
    anispeed = 1 # animation speed

    music_volume = 0
    music_volume_max = 1

    quote = getqt() # gets quote to display
    play_sound(GROWTH_SOUND) 

    tree1 = tree(stdscr, 1) # create a tree instance
    tree1.media.play()
    
    try:

        treedata_in = open(RES_FOLDER/ "treedata", "rb")
        tree1.age = pickle.load(treedata_in)

    except:

        tree1.age = 1


    try:
        while True:

            start = time.time()

            try:
                stdscr.erase()
                maxy, maxx = stdscr.getmaxyx()

                addtext(int(maxx / 2), int(maxy * 5 / 6), quote, anilen, stdscr, 2)
                anilen += anispeed
                if anilen > 150:
                    anilen = 150
                    
                if (seconds % (100 * 60 * 10) == 0):  # show another quote every 5 min, and grow tree
                    quote = getqt()
                    tree1.age += 1
                    anilen = 1
                    play_sound(GROWTH_SOUND)

      
                tree1.display(maxx, maxy, seconds)

                tree1.seasons(maxx, maxy, seconds)

                tree1.menudisplay(stdscr, maxy, maxx)

                tree1.youtube(stdscr, maxx)

                tree1.timer()

                if tree1.media.is_playing() and tree1.media.get_length() - tree1.media.get_time() < 1000  :

                    if tree1.isloop:
                        tree1.media.set_position(0)
                    else:
                        tree1.media.stop()
                        tree1.media = vlc.MediaPlayer(tree1.music_list[tree1.music_list_num])
                        tree1.media.play()   

                if tree1.isloading:
                    tree1.loading(stdscr, maxx)

                tree1.notify(stdscr, maxy, maxx)

                key_events(stdscr, tree1, maxx)

                while tree1.pause:
                    stdscr.erase()
                    stdscr.addstr(
                        int(maxy * 3 / 5),
                        int(maxx / 2 - len("PAUSED") / 2),
                        "PAUSED",
                        curses.A_BOLD,
                    )
                    key = stdscr.getch()
                    if key == ord(" "):
                        tree1.pause = False
                        tree1.media.play()
                        stdscr.refresh()
                        if tree1.istimer:
                            tree1.workendtime += time.time() - tree1.pausetime

                    if key == ord("q"):

                        treedata = open(RES_FOLDER / "treedata", "wb")
                        pickle.dump(tree1.age, treedata, protocol=None)
                        treedata.close()
                        exit()

                    time.sleep(0.1)

                while tree1.isbreak:
                    stdscr.erase()
                    stdscr.addstr(
                        int(maxy * 3 / 5),
                        int(maxx / 2 - len("PRESS SPACE TO END BREAK") / 2),
                        "PRESS SPACE TO END BREAK",
                        curses.A_BOLD,
                    )
                    tree1.breakdisplay(maxx, maxy)
                    stdscr.refresh()
                    key = stdscr.getch()

                    if key == ord(" "):
                        tree1.isbreak = False
                        tree1.media.play()
                        stdscr.refresh()

                    if key == ord("q"):
                        treedata = open(RES_FOLDER / "treedata", "wb")
                        pickle.dump(tree1.age, treedata, protocol=None)
                        treedata.close()
                        exit()

                    time.sleep(0.1)

                time.sleep(max(0.05 - (time.time() - start), 0))

                #time.sleep(0.1)
                seconds += 5

            except KeyboardInterrupt:

                try:
                    stdscr.erase()
                    stdscr.addstr(
                        int(maxy * 3 / 5),
                        int(maxx / 2 - len("PRESS 'q' TO EXIT") / 2),
                        "PRESS 'q' TO EXIT",
                        curses.A_BOLD,
                    )
                    stdscr.refresh()
                    time.sleep(1)
                except KeyboardInterrupt:
                    pass

            stdscr.refresh()

    finally:
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        stdscr.keypad(False)
        stdscr.nodelay(False)
        curses.endwin()


def run():
    """Entry point for the CLI command."""
    # avoid running the app if the module is imported
    config_file = Path(get_user_config_directory()) / "wisdom-tree" / QUOTE_FILE_NAME
    if config_file.exists():
        global QUOTE_FILE
        QUOTE_FILE = config_file
    curses.wrapper(main)

if __name__ == "__main__":
    run()
