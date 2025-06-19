from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
RES_FOLDER = BASE_DIR / "res"
QUOTE_FOLDER = BASE_DIR

# Quote file settings
QUOTE_FILE_NAME = "qts.txt"
QUOTE_FILE = QUOTE_FOLDER / QUOTE_FILE_NAME

# Timer settings
TIMER_WORK_MINS = (25, 45, 50, 90)
TIMER_BREAK_MINS = (5, 15, 10, 20)
TIMER_WORK = tuple(t * 60 for t in TIMER_WORK_MINS)
TIMER_BREAK = tuple(t * 60 for t in TIMER_BREAK_MINS)

# Sound settings
SOUNDS_MUTED = False  # Only growth and start_timer are affected; alarm always plays
TIMER_START_SOUND = str(RES_FOLDER / "timerstart.wav")
ALARM_SOUND = str(RES_FOLDER / "alarm.wav")
GROWTH_SOUND = str(RES_FOLDER / "growth.waw")
EFFECT_VOLUME = 100
