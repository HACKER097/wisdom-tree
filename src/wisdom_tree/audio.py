import logging
import re
import time
import urllib.request
from typing import Any

import requests
import vlc
from pytubefix import YouTube

from wisdom_tree.config import (
    ALARM_SOUND,
    EFFECT_VOLUME,
    SOUNDS_MUTED,
)

YOUTUBE_REGEX = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$")


def is_internet_available() -> bool:
    try:
        urllib.request.urlopen("https://youtube.com", timeout=10)
        return True
    except Exception:
        return False


def play_sound(sound: str) -> None:
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


def get_youtube_links(search_string: str) -> str:
    search_url = (
        "https://www.youtube.com/results?search_query="
        + search_string.replace(" ", "+")
    )
    html = requests.get(search_url)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.content.decode())
    return "http://youtube.com/watch?v=" + str(video_ids[0])


def adjust_media_volume(tree_instance: Any, new_volume: int, maxx: int) -> None:
    tree_instance.media.audio_set_volume(max(0, min(100, new_volume)))
    tree_instance.notifyendtime = int(time.time()) + 2
    volume_str = f"{round(new_volume)}%"
    tree_instance.notifystring = (
        " " * round(maxx * (new_volume / 100) - len(volume_str) - 2) + volume_str
    )
    tree_instance.invert = True
    tree_instance.isnotify = True


class MediaPlayer:
    def __init__(self, music_list):
        self.music_list = music_list
        self.music_list_num = 0
        self.media = vlc.MediaPlayer(str(self.music_list[self.music_list_num]))
        self.isloop = False
        self.yt_title = ""
        self.downloaddisplay = False
        self.youtubedisplay = False
        self.spinnerstate = 0
        self.isloading = False

    def play_youtube(self, song_input: str, is_url: bool, tree_instance: Any) -> None:
        self.downloaddisplay = True
        if not is_internet_available():
            tree_instance.notifyendtime = int(time.time()) + 5
            tree_instance.notifystring = "NO INTERNET CONNECTION"
            tree_instance.isnotify = True
            return

        try:
            yt_url = song_input if is_url else get_youtube_links(song_input)
            yt = YouTube(yt_url)
            song = yt.streams.get_by_itag(251).url
            self.media = vlc.MediaPlayer(song)
            self.downloaddisplay = False
            self.media.play()
            self.yt_title = yt.title
            tree_instance.notifications.notify("Playing: " + self.yt_title, 10)
        except Exception:
            tree_instance.notifications.notify("ERROR GETTING AUDIO, PLEASE TRY AGAIN", 5)
            return

    def handle_media_end(self):
        if (
            self.media.is_playing()
            and self.media.get_length() - self.media.get_time() < 1000
        ):
            if self.isloop:
                self.media.set_position(0)
            else:
                self.media.stop()
                self.media = vlc.MediaPlayer(self.music_list[self.music_list_num])
                self.media.play()

    def show_loading_spinner(self, stdscr, maxx):
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
            "[=   ]",
        ]
        self.spinnerstate += 0.5
        if self.spinnerstate > len(spinner) - 1:
            self.spinnerstate = 0

        import curses

        curses.textpad.rectangle(stdscr, 0, 0, 2, maxx - 1)
        stdscr.addstr(1, 1, "GETTING AUDIO  " + spinner[int(self.spinnerstate)])
