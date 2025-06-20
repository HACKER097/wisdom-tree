import os
import pickle
import random
from pathlib import Path
from typing import List

from wisdom_tree.config import QUOTE_FILE


def get_user_config_directory() -> str:
    if os.name == "nt":
        appdata = os.getenv("LOCALAPPDATA")
        if appdata:
            return appdata
        appdata = os.getenv("APPDATA")
        if appdata:
            return appdata
        return None

    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return xdg_config_home
    return os.path.join(os.path.expanduser("~"), ".config")


class QuoteManager:
    def __init__(self):
        self.quotes_cache = self._load_quotes()

    def _load_quotes(self) -> List[str]:
        try:
            with open(QUOTE_FILE, encoding="utf8") as f:
                return f.read().splitlines()
        except Exception:
            return []

    def get_random_quote(self) -> str:
        if not self.quotes_cache:
            return "Keep growing, keep learning."
        return random.choice(self.quotes_cache)

    def reload_quotes(self) -> None:
        self.quotes_cache = self._load_quotes()


class StateManager:
    def __init__(self, state_file: Path):
        self.state_file = state_file

    def save_tree_age(self, age: int) -> None:
        try:
            with open(self.state_file, "wb") as f:
                pickle.dump(age, f, protocol=None)
        except Exception as e:
            print(f"Error saving tree age: {e}")

    def load_tree_age(self) -> int:
        try:
            with open(self.state_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            return 1

    def file_exists(self) -> bool:
        return self.state_file.exists()


def get_random_line_from_file(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf8") as f:
            lines = f.read().splitlines()
        return random.choice(lines) if lines else ""
    except Exception:
        return ""


def ensure_directory_exists(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
