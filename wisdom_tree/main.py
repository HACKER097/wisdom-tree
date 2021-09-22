import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import curses
from curses import textpad
import time
import random
import pickle
from pathlib import Path
from pytube import YouTube, Playlist
import re
import urllib.request
import threading
import ctypes
import vlc

os.environ['VLC_VERBOSE'] = '-1'

if not os.name == "posix" and not ctypes.windll.shell32.IsUserAnAdmin() != 0:
    print("PLEASE RUN AS ADMINISTRATOR")
    exit()

RES_FOLDER = Path(__file__).parent / "res"
QUOTE_FOLDER = Path(__file__).parent
QUOTE_FILE_NAME = "qts.txt"
QUOTE_FILE = QUOTE_FOLDER / QUOTE_FILE_NAME

TIMER_WORK_MINS =  (20 , 20 , 40 , 50)
TIMER_BREAK_MINS = (20 , 10 , 20 , 10)

TIMER_WORK = (
	TIMER_WORK_MINS[0] * 60, 
	TIMER_WORK_MINS[1] * 60, 
	TIMER_WORK_MINS[2] * 60, 
	TIMER_WORK_MINS[3] * 60)

TIMER_BREAK = (
	TIMER_BREAK_MINS[0] * 60, 
	TIMER_BREAK_MINS[1] * 60, 
	TIMER_BREAK_MINS[2] * 60, 
	TIMER_BREAK_MINS[3] * 60)

SOUNDS_MUTED = False # This is for only growth and start_timer, alarm stays
TIMER_START_SOUND = str(RES_FOLDER / "timerstart.wav")
ALARM_SOUND = str(RES_FOLDER / "alarm.wav")
GROWTH_SOUND = str(RES_FOLDER/ "growth.waw")

effect_volume = 100 # How loud sound effects are, not including ambience and music.

__all__ = ["run_app"]

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

def play_sound(sound):

    if SOUNDS_MUTED and sound != ALARM_SOUND:
        return

    media = vlc.MediaPlayer(sound)
    media.audio_set_volume(effect_volume)
    media.play()

def toggle_sounds():
    global SOUNDS_MUTED
    SOUNDS_MUTED = not SOUNDS_MUTED

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
        text[: int(anilen)], " ", "#", 8
    )  # aads "#" after the 7th word to split line
    text = text.split("#")  # splits text into 2 list
    for i in range(len(text)):
        stdscr.addstr(
            y + i,
            int(x - len(text[i]) / 2),
            str(text[i]),
            curses.color_pair(color_pair),
        )  # displays the list in 2 lines


def getrandomline(file):  # returns random quote
    lines = open(file, encoding="utf8").read().splitlines()
    myline = random.choice(lines)
    return myline


def getqt():  # returns random quote
    return getrandomline(QUOTE_FILE)


def printart(
    stdscr, file, x, y, color_pair
):  # prints line one by one to display text art, also in the middle
    with open(file, "r", encoding="utf8") as f:
        lines = f.readlines()

        for i in range(len(lines)):
            stdscr.addstr(
                y + i - len(lines),
                x - int(len(max(lines, key=len)) / 2),
                lines[i],
                curses.color_pair(color_pair),
            )


def key_events(stdscr, tree1, maxx):

    global effect_volume # Used for setting the sound effect volume with '{' and '}'

    key = stdscr.getch()

    if key in (curses.KEY_UP, ord("k")):
        tree1.showtimer = True
        tree1.selectedtimer -= 1
        tree1.timerhidetime = int(time.time()) + 5

    if key in (curses.KEY_DOWN, ord("j")):
        tree1.showtimer = True
        tree1.selectedtimer += 1
        tree1.timerhidetime = int(time.time()) + 5

    if key == curses.KEY_ENTER or key == 10 or key == 13:  # this is enter key
        if tree1.showtimer:
            if tree1.currentmenu == "timer":
                tree1.starttimer(tree1.selectedtimer, stdscr, maxx)
            else:
                tree1.featureselect(tree1.selectedtimer, maxx, stdscr)
            play_sound(TIMER_START_SOUND)
            tree1.showtimer = False

        if tree1.breakover:
            tree1.breakover = False
            tree1.starttimer(tree1.selectedtimer, stdscr, maxx)
            play_sound(TIMER_START_SOUND)

    if key == ord("q"):
        treedata = open(RES_FOLDER / "treedata", "wb")
        pickle.dump(tree1.age, treedata, protocol=None)
        treedata.close()
        for file in list(_ for _ in QUOTE_FOLDER.glob("*.ogg")):
            os.remove(file)
        for file in list(_ for _ in QUOTE_FOLDER.glob("*.webm")):
            os.remove(file)
        exit()

    if key == ord("u"):
        toggle_sounds()

    if key in (curses.KEY_RIGHT, ord("l")):
        if tree1.showtimer:
            tree1.selectedtimer = 0
            tree1.currentmenu = "feature"

        else:
            tree1.radiomode = False
            tree1.music_list_num += 1
            if tree1.music_list_num > len(tree1.music_list) - 1:
                tree1.music_list_num = len(tree1.music_list) - 1
            tree1.media.stop()
            tree1.media = vlc.MediaPlayer(tree1.music_list[tree1.music_list_num])
            tree1.media.play()
            tree1.show_music = True
            tree1.musichidetime = int(time.time()) + 5

    if key in (curses.KEY_LEFT, ord("h")):
        if tree1.showtimer:
            tree1.selectedtimer = 0
            tree1.currentmenu = "timer"
        else:
            tree1.radiomode = False
            tree1.music_list_num -= 1
            if tree1.music_list_num < 0:
                tree1.music_list_num = 0
            tree1.media.stop()
            tree1.media = vlc.MediaPlayer(tree1.music_list[tree1.music_list_num])
            tree1.media.play()
            tree1.show_music = True
            tree1.musichidetime = int(time.time()) + 5

    if key == ord(" "):
        if tree1.media.is_playing():
            tree1.media.pause()
        tree1.pause = True
        tree1.pausetime = time.time()

    if key == ord("m"):
        tree1.media.pause()

    if not tree1.isloading and key == ord("n"):
        tree1.lofiradio()

    if key == ord("]"):
        tree1.media.audio_set_volume(tree1.media.audio_get_volume()+1)
        tree1.notifyendtime = int(time.time()) + 2
        volume = str(round(tree1.media.audio_get_volume())) + "%"
        tree1.notifystring = " "*round(maxx*(tree1.media.audio_get_volume()/100)-len(volume)-2) + volume
        tree1.invert = True
        tree1.isnotify = True

    if key == ord("["):
        tree1.media.audio_set_volume(tree1.media.audio_get_volume()-1)
        tree1.notifyendtime = int(time.time()) + 2
        volume = str(round(tree1.media.audio_get_volume())) + "%"
        tree1.notifystring = " "*round(maxx*(tree1.media.audio_get_volume()/100)-len(volume)-2) + volume

        tree1.invert = True
        tree1.isnotify = True

    if key == ord("}"):
        effect_volume = min(100, effect_volume+1)

        tree1.notifyendtime = int(time.time()) + 2

        volume = str(effect_volume) + "%"
        tree1.notifystring = " "*round(maxx*(effect_volume/100)-len(volume)-2) + volume
        tree1.invert = True
        tree1.isnotify = True

    if key == ord("{"):
        effect_volume = max(0, effect_volume-1)

        tree1.notifyendtime = int(time.time()) + 2

        volume = str(effect_volume) + "%"
        tree1.notifystring = " "*round(maxx*(effect_volume/100)-len(volume)-2) + volume
        tree1.invert = True
        tree1.isnotify = True

    if key == ord("="):

        if tree1.media.get_time()+10000 < tree1.media.get_length():
            tree1.media.set_time(i_time=tree1.media.get_time()+10000)
        else:
            tree1.media.set_time(tree1.media.get_length()-1)

        time_sec = tree1.media.get_time()/1000
        display_time =  str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60).zfill(2)
        tree1.notifyendtime = int(time.time()) + 2
        try:
            tree1.notifystring = " "*(round(maxx*(tree1.media.get_time()/tree1.media.get_length()))-len(display_time)) + display_time
        except ZeroDivisionError:
            pass
        tree1.invert = True
        tree1.isnotify = True

    if key == ord("-"):
        if tree1.media.get_time()-10000 > 0:
            tree1.media.set_time(i_time=tree1.media.get_time()-10000)
        else:
            tree1.media.set_time(0)


        time_sec = tree1.media.get_time()/1000
        display_time =  str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60).zfill(2)
        tree1.notifyendtime = int(time.time()) + 2
        tree1.notifystring = " "*(round(maxx*(tree1.media.get_time()/tree1.media.get_length()))-len(display_time)) + display_time
        tree1.invert = True
        tree1.isnotify = True

    for i in range(10):
        if key == ord(str(i)):
            tree1.media.set_time(i_time=int(tree1.media.get_length()*(i/10)))

            time_sec = tree1.media.get_time()/1000
            display_time =  str(int(time_sec / 60)).zfill(2) + ":" + str(int(time_sec) % 60).zfill(2)
            tree1.notifyendtime = int(time.time()) + 2
            tree1.notifystring = " "*(round(maxx*(tree1.media.get_time()/tree1.media.get_length()))-len(display_time)) + display_time
            tree1.invert = True
            tree1.isnotify = True

    if tree1.media.audio_get_volume() > 100:
        tree1.media.audio_set_volume(100)



def GetSong(link):

    video = YouTube("http://youtube.com/" + link.split("/")[-1] )

    try:
        video.streams
    except:
        return "WRONG LINK ERROR"

    try:
        songfile = str(video.streams.get_by_itag(251).download(timeout=30))
    except:
        return "DOWNLOAD ERROR"

    try:
        AudioSegment.from_file(songfile, "webm").export(str(songfile + ".ogg"), format="ogg")
    except:
        return "CONVERT ERROR"

    os.remove(songfile) 
    if os.name == "posix":
        songpath = str(songfile+".ogg").split("/")[-1]
    else:
        songpath = str(songfile+".ogg").split("\\")[-1]
        
    os.rename(songfile+".ogg", songpath)

    return songpath

def GetLinks(search_string):
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_string.replace(" ", "+"))
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    return "http://youtube.com/watch?v=" + str(video_ids[0])

#print(GetSong(GetLinks(input())))
#time.sleep(100)

class tree:
    def __init__(self, stdscr, age):
        self.stdscr = stdscr
        self.age = age
        self.show_music = False
        self.music_list = list(_ for _ in RES_FOLDER.glob("*.ogg"))
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
            " LOFI RADIO 1 ",
            " LOFI RADIO 2 ",
            " LOFI RADIO 3 ",
            " CUSTOM PLAYLIST "
        ]
        self.currentmenu = "timer"
        self.selectedtimer = 0
        self.istimer = False
        self.isbreak = False
        self.breakover = False
        self.timerhidetime = 0
        self.musichidetime = 0
        random.seed(int(time.time() / (60 * 60 * 24)))
        self.season = random.choice(
            ["rain", "heavy_rain", "light_rain", "snow", "windy"]
        )
        self.youtubedisplay = False
        self.downloaddisplay = False
        self.spinnerstate = 0
        self.notifyendtime = 0
        self.isnotify = False
        self.notifystring = " "
        self.playlist = Playlist("https://www.youtube.com/playlist?list=PL6fhs6TSspZvN45CPJApnMYVsWhkt55h7")
        self.radiomode = False
        self.isloading = False
        self.invert = False
        self.breakendtext = "BREAK IS OVER, PRESS ENTER TO START NEW TIMER"
        random.seed()


    def display(self, maxx, maxy, seconds):
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

        # RAIN

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
        if self.showtimer:

            if self.currentmenu == "timer":
                if self.selectedtimer > len(self.timerlist) - 1:
                    self.selectedtimer = len(self.timerlist) - 1
                if self.selectedtimer < 0:
                    self.selectedtimer = 0

            if self.currentmenu == "feature":
                if self.selectedtimer > len(self.featurelist) - 1:
                    self.selectedtimer = len(self.featurelist) - 1
                if self.selectedtimer < 0:
                    self.selectedtimer = 0


            for i in range(len(self.timerlist)):
                if i == self.selectedtimer and self.currentmenu == "timer":
                    stdscr.addstr(
                        int((maxy - len(self.timerlist)*2) / 2) + i * 2,
                        int(maxx / 25 + 4),
                        self.timerlist[i],
                        curses.A_REVERSE,
                    )
                else:
                    stdscr.addstr(
                        int((maxy - len(self.timerlist)*2) / 2) + i * 2,
                        int(maxx / 25),
                        self.timerlist[i],
                    )

            for i in range(len(self.featurelist)):
                if i == self.selectedtimer and self.currentmenu == "feature":
                    stdscr.addstr(
                        int((maxy - len(self.featurelist)*2) / 2) + i * 2,
                        int(maxx * 24 / 25 - len(self.featurelist[i])) - 4,
                        self.featurelist[i],
                        curses.A_REVERSE,
                    )
                else:
                    stdscr.addstr(
                        int((maxy - len(self.featurelist)*2) / 2) + i * 2,
                        int(maxx * 24 / 25 - len(self.featurelist[i])),
                        self.featurelist[i],
                    )

        if int(time.time()) >= self.timerhidetime:
            self.showtimer = False

        if self.istimer:
            self.secondsleft = int(self.workendtime) - int(time.time())
            timertext = (
                "Break in: "
                + str(int(self.secondsleft / 60)).zfill(2)
                + ":"
                + str(self.secondsleft % 60).zfill(2)
            )
            stdscr.addstr(
                int(maxy * 10 / 11), int(maxx / 2 - len(timertext) / 2), timertext
            )

        if self.breakover:
            self.stdscr.addstr(
                int(maxy * 10 / 11),
                int(
                    maxx / 2 - len(self.breakendtext) / 2
                ),
                self.breakendtext,
                curses.A_BLINK | curses.A_BOLD,
            )

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
            self.istimer == False
        
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
        self.radiomode = False
        if inputfeature == 0:
            if hasattr(self, "media"):
                self.media.stop()
            self.youtubedisplay = True
        if inputfeature == 1:
            self.playlist = Playlist("https://www.youtube.com/playlist?list=PLOzDu-MXXLliO9fBNZOQTBDddoA3FzZUo")
            self.lofiradio()

        if inputfeature == 2:
            self.playlist = Playlist("https://www.youtube.com/playlist?list=PL0ONFXpPDe_mtm3ciwL-v7EE-7yLHDlP8")
            self.lofiradio()

        if inputfeature == 3:
            self.playlist = Playlist("https://www.youtube.com/playlist?list=PLKYTmz7SemaqVDF6XJ15bv_8-j7ckkNgb")
            self.lofiradio()

        if inputfeature == 4:
            curses.textpad.rectangle(stdscr, 0,0,2, maxx-1)
            stdscr.addstr(1,1, "ENTER PLAyLIST LINK : ")
            stdscr.refresh()

            curses.echo()
            curses.nocbreak()
            stdscr.nodelay(False)
            stdscr.keypad(False)
            curses.curs_set(1)

            templink = stdscr.getstr()
            templink = str(templink)[1:][:-1]
            self.playlist = Playlist(str(templink))

            curses.noecho()
            curses.cbreak()
            stdscr.nodelay(True)
            stdscr.keypad(True)
            curses.curs_set(0)

            self.lofiradio()

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



    def youtube(self, stdscr, maxx):
        if self.youtubedisplay:
            curses.textpad.rectangle(stdscr, 0,0,2, maxx-1)
            stdscr.addstr(1,1, "ENTER SEARCH QUERY/LINK : ")
            stdscr.refresh()

            if not "songinput" in locals():

                curses.echo()
                curses.nocbreak()
                stdscr.nodelay(False)
                stdscr.keypad(False)
                curses.curs_set(1)

                songinput = str(stdscr.getstr())

                curses.noecho()
                curses.cbreak()
                stdscr.nodelay(True)
                stdscr.keypad(True)
                curses.curs_set(0)


            stdscr.addstr(1,1, "GETTING AUDIO")

            getsongthread = threading.Thread(target=self.playyoutube, args=(songinput,))
            getsongthread.daemon = True
            getsongthread.start()

            self.youtubedisplay = False

            self.downloaddisplay = True

            del songinput



        if self.downloaddisplay:
            self.loading(stdscr, maxx)


    def playyoutube(self, songinput):

        try:
            yt = YouTube(GetLinks(songinput))
            song = yt.streams.get_by_itag(251).url

            self.media = vlc.MediaPlayer(song)

            self.media.play()

        except:
            self.notifyendtime = int(time.time()) + 5
            self.notifystring = "ERROR GETTING AUDIO, PLEASE TRY AGAIN"
            self.isnotify = True
            exit()

        self.downloaddisplay = False

        self.yt_title = yt.title


        self.notifyendtime = int(time.time()) + 10
        self.notifystring = "Playing: " + self.yt_title
        self.invert = False
        self.isnotify = True

    def getlofisong(self): 
        # some links dont work, use recursion to find a link which works

        try:
    
            self.lofilink = random.choice(self.playlist.video_urls)
            link = YouTube(self.lofilink).streams.get_by_itag(251).url

            return link

        except:

            self.isloading = False

            self.notifyendtime = int(time.time()) + 10
            self.notifystring = "UNABLE TO CONNECT, PLEASE CHECK INTERNET CONNECTION"
            self.invert = False
            self.isnotify = True
            self.radiomode = False
            exit()
      

    def lofiradio(self):
         #lofi playlist from youtube

        self.media.stop()

        self.isloading = True
        self.radiomode = True

        radiothread = threading.Thread(target=self.actuallofiradio)
        radiothread.daemon = True
        radiothread.start()


    def actuallofiradio(self):


        if not hasattr(self, "lofisong"):
            self.lofisong = self.getlofisong()

        if self.lofisong == "ERROR":
            exit()


        self.media = vlc.MediaPlayer(self.lofisong)
        self.media.play()

        self.notifyendtime = int(time.time()) + 10
        self.notifystring = "Playing: " + YouTube(self.lofilink).title
        self.invert = False
        self.isnotify = True

        self.lofisong = self.getlofisong()

        self.isloading = False





def main():
    run = True
    stdscr = curses.initscr()
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.curs_set(0)
    curses.start_color()
    curses.noecho()
    curses.cbreak()

    curses.use_default_colors()

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
    anilen = 1
    anispeed = 1

    music_volume = 0
    music_volume_max = 1

    quote = getqt()
    play_sound(GROWTH_SOUND)

    tree1 = tree(stdscr, 1)
    tree1.media.play()

    try:

        treedata_in = open(RES_FOLDER/ "treedata", "rb")
        tree1.age = pickle.load(treedata_in)

    except:

        tree1.age = 1


    try:
        while run:

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

                if tree1.musichidetime <= int(time.time()):
                    tree1.show_music = False

                if tree1.show_music:
                    if os.name == "posix":
                        showtext = (
                            "Playing: "
                            + str(tree1.music_list[tree1.music_list_num]).split("/")[-1]
                        )
                    else:
                        showtext = (
                            "Playing: "
                            + str(tree1.music_list[tree1.music_list_num]).split('\\')[-1]
                        )
                    stdscr.addstr(
                        int(maxy / 10),
                        int(maxx / 2 - len(showtext) / 2),
                        showtext,
                        curses.A_BOLD,
                    )

                tree1.display(maxx, maxy, seconds)

                tree1.seasons(maxx, maxy, seconds)

                tree1.menudisplay(stdscr, maxy, maxx)

                tree1.youtube(stdscr, maxx)

                tree1.timer()

                if not tree1.isloading and round(tree1.media.get_position()*100) == 100:
                    if tree1.radiomode:
                        tree1.lofiradio()
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
                        for file in list(_ for _ in QUOTE_FOLDER.glob("*.ogg")):
                            os.remove(file)
                        for file in list(_ for _ in QUOTE_FOLDER.glob("*.webm")):
                            os.remove(file)
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
                        for file in list(_ for _ in QUOTE_FOLDER.glob("*.ogg")):
                            os.remove(file)
                        for file in list(_ for _ in QUOTE_FOLDER.glob("*.webm")):
                            os.remove(file)
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


def run_app():
    """A method to run the app"""
    global QUOTE_FILE
    config_file = Path(get_user_config_directory()) / "wisdom-tree" / QUOTE_FILE_NAME
    if config_file.exists():
        QUOTE_FILE = config_file
    main()


if __name__ == "__main__":
    # avoid running the app if the module is imported
    run_app()
