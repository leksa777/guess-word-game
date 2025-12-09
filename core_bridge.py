"""Cleaned core_bridge_fixed.py — robust bridge with local fallback
This implementation matches the native exports in `cpp_core/bridge.cpp` (stdcall exports:
`init_db`, `get_categories`, `start_game(const char*)`, `check_word_guess(const char*, int*)`,
`get_secret`, `get_lives`, `get_game_status`), and provides a Python-side fallback
that emulates the word selection and guessing logic when the native functions fail
or when `get_secret()` returns an empty/dangling pointer.
"""

import ctypes
from ctypes import c_char_p, c_int, POINTER
from pathlib import Path
import random
import shutil
import sys


def _is_windows() -> bool:
    return sys.platform.startswith("win")


class NativeUnavailableError(RuntimeError):
    pass


class GameCore:
    def __init__(self, lib_path: Path, words_path: Path):
        self.lib_path = Path(lib_path)
        self.words_path = Path(words_path)
        if not self.lib_path.exists():
            raise FileNotFoundError(f"Library not found: {self.lib_path}")
        if not self.words_path.exists():
            raise FileNotFoundError(f"Words file not found: {self.words_path}")

        # Load library using WinDLL on Windows (stdcall) to help resolve decorated names
        try:
            if _is_windows():
                self.lib = ctypes.WinDLL(str(self.lib_path))
            else:
                self.lib = ctypes.CDLL(str(self.lib_path))
        except Exception as e:
            raise RuntimeError(f"Failed to load native library: {e}")

        # Ensure words.txt is next to the DLL — native init_db expects local words.txt
        try:
            dll_dir = self.lib_path.parent
            target = dll_dir / "words.txt"
            # Only copy if the target does not already exist. Avoid overwriting
            # an existing words.txt that may have been placed by the user or build.
            if not target.exists():
                shutil.copy2(self.words_path, target)
                print(f"[DEBUG] Copied words file to {target}")
            else:
                # target exists; do not overwrite. If you want to force a copy,
                # remove the target file first or run a separate update step.
                print(f"[DEBUG] words.txt already exists next to DLL at {target}; not overwriting")
        except Exception as e:
            print(f"[WARNING] Failed to copy words.txt next to DLL: {e}")

        # Try to call init_db (some builds need explicit init)
        self._init_db_fn = self._resolve_optional("init_db")
        if self._init_db_fn:
            try:
                self._init_db_fn()
            except Exception as e:
                print(f"[WARNING] init_db raised: {e}")

        # Resolve other symbols (decorated names handled by name search)
        self._get_categories_fn = self._resolve_optional("get_categories", restype=c_char_p)
        self._get_category_fn = self._resolve_optional("get_category", restype=c_char_p)
        self._get_secret_fn = self._resolve_optional("get_secret", restype=c_char_p)
        self._get_lives_fn = self._resolve_optional("get_lives", restype=c_int)
        self._get_game_status_fn = self._resolve_optional("get_game_status", restype=c_int)

        # start_game(cat)
        self._start_game_fn = self._resolve_optional("start_game")
        if self._start_game_fn:
            try:
                self._start_game_fn.argtypes = [c_char_p]
                self._start_game_fn.restype = None
            except Exception:
                pass

        # check_word_guess(const char* guess, int* out)
        self._check_word_fn = self._resolve_optional("check_word_guess")
        if self._check_word_fn:
            try:
                self._check_word_fn.argtypes = [c_char_p, POINTER(c_int)]
                self._check_word_fn.restype = None
            except Exception:
                pass

        # Local fallback state (used when native APIs are missing or return invalid values)
        self._use_local_emulation = False
        self._local_secret = ""
        self._local_attempts = 0
        self._local_won = False
        self._local_lost = False

        # Preload words from file for fallback operations
        self._all_words = self._load_words_file()
        if not self._all_words:
            print("[WARNING] No words loaded from words.txt; the game cannot run correctly.")

    def _resolve_optional(self, base_name: str, restype=None):
        # Direct attribute
        if hasattr(self.lib, base_name):
            fn = getattr(self.lib, base_name)
            if restype is not None:
                try:
                    fn.restype = restype
                except Exception:
                    pass
            return fn
        # Try to find decorated/variant names
        candidates = [n for n in dir(self.lib) if base_name in n]
        if candidates:
            name = candidates[0]
            print(f"[DEBUG] Resolved native symbol '{base_name}' -> '{name}'")
            fn = getattr(self.lib, name)
            if restype is not None:
                try:
                    fn.restype = restype
                except Exception:
                    pass
            return fn
        return None

    def _load_words_file(self) -> list[str]:
        words = []
        try:
            with self.words_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    s = line.strip()
                    if not s:
                        continue
                    # Accept both plain WORD or WORD;CATEGORY
                    if ";" in s:
                        word, _ = s.split(";", 1)
                        words.append(word.strip().upper())
                    else:
                        words.append(s.strip().upper())
        except Exception as e:
            print(f"[WARNING] Failed to load words file: {e}")
        return words

    def get_categories(self) -> list[str]:
        if self._get_categories_fn:
            try:
                raw = self._get_categories_fn() or b""
                text = raw.decode("utf-8")
                return text.split("|") if text else ["Any"]
            except Exception:
                pass
        # Fallback: parse categories from words file (lines like WORD;CAT)
        cats = set()
        try:
            with self.words_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if ";" in line:
                        _, cat = line.strip().split(";", 1)
                        cats.add(cat.strip())
        except Exception:
            pass
        return sorted(cats) if cats else ["Any"]

    def filter_words_by_category(self, category: str) -> list[str]:
        # Return uppercase words
        if category in (None, "", "Any"):
            return list(self._all_words)
        filtered = []
        try:
            with self.words_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    s = line.strip()
                    if not s:
                        continue
                    if ";" in s:
                        word, cat = s.split(";", 1)
                        if cat.strip() == category:
                            filtered.append(word.strip().upper())
                    else:
                        # plain word with no category -> include only if category==Any
                        pass
        except Exception:
            pass
        return filtered

    def start_game(self, category: str = "Any", attempts: int = 5) -> None:
        """Start a game. Prefer native start_game; if native secret is missing, fall back to Python emulation.
        The native `start_game` in the DLL ignores attempts and uses its own default (5), but we accept `attempts`
        for local emulation.
        """
        self._use_local_emulation = False
        # Try native start
        if self._start_game_fn:
            try:
                self._start_game_fn(category.encode("utf-8"))
            except Exception as e:
                print(f"[WARNING] native start_game failed: {e}")

        # Try to obtain native secret
        native_secret = None
        if self._get_secret_fn:
            try:
                raw = self._get_secret_fn() or b""
                native_secret = raw.decode("utf-8") if raw else ""
            except Exception as e:
                print(f"[DEBUG] get_secret failed: {e}")
                native_secret = ""

        # If native secret is empty or not present in words list, use local emulation
        if not native_secret or native_secret.upper() not in self._all_words:
            # pick local secret from words file filtered by category
            candidates = self.filter_words_by_category(category)
            if not candidates:
                candidates = list(self._all_words)
            if not candidates:
                raise RuntimeError("No words available to start the game")
            self._local_secret = random.choice(candidates)
            print(f"[INFO] Using local emulation secret: {self._local_secret}")
            self._use_local_emulation = True
            self._local_attempts = attempts
            self._local_won = False
            self._local_lost = False
        else:
            # Use native secret and rely on native guess evaluation
            self._local_secret = native_secret.upper()
            self._use_local_emulation = False

    def _evaluate_guess_local(self, guess: str) -> list[int]:
        # C++ logic: 2=correct,1=present,0=absent
        guess = guess.upper()
        secret = self._local_secret.upper()
        if len(guess) != len(secret):
            raise ValueError("Guess length mismatch")
        # Count letters in secret
        counts = [0] * 26
        for ch in secret:
            if 'A' <= ch <= 'Z':
                counts[ord(ch) - 65] += 1
        result = [0] * len(secret)
        # Corrects
        for i, ch in enumerate(guess):
            if ch == secret[i]:
                result[i] = 2
                counts[ord(ch) - 65] -= 1
        # Presents
        for i, ch in enumerate(guess):
            if result[i] == 2:
                continue
            if 'A' <= ch <= 'Z' and counts[ord(ch) - 65] > 0:
                result[i] = 1
                counts[ord(ch) - 65] -= 1
        return result

    def guess_word(self, word: str, length: int) -> list[int]:
        word_u = word.upper()
        if len(word_u) != length:
            raise ValueError("expected_len must match guess length")

        if self._check_word_fn and not self._use_local_emulation:
            # Call native API
            arr = (c_int * length)()
            try:
                self._check_word_fn(word_u.encode("utf-8"), arr)
                return list(arr)
            except Exception as e:
                print(f"[WARNING] native check_word_guess failed: {e}")
                # fall through to local emulation

        # Local emulation
        statuses = self._evaluate_guess_local(word_u)
        # update attempts/won/lost
        if statuses == [2] * length:
            self._local_won = True
        else:
            self._local_attempts -= 1
            if self._local_attempts <= 0:
                self._local_lost = True
        return statuses

    def get_secret(self) -> str:
        if self._get_secret_fn and not self._use_local_emulation:
            try:
                raw = self._get_secret_fn() or b""
                return raw.decode("utf-8") if raw else ""
            except Exception:
                return ""
        return self._local_secret

    def get_lives(self) -> int:
        if self._get_lives_fn and not self._use_local_emulation:
            try:
                return int(self._get_lives_fn())
            except Exception:
                return 0
        return int(self._local_attempts)

    def get_game_status(self) -> int:
        # 1=won, -1=lost, 0=ongoing
        if self._get_game_status_fn and not self._use_local_emulation:
            try:
                return int(self._get_game_status_fn())
            except Exception:
                return 0
        if self._local_won:
            return 1
        if self._local_lost:
            return -1
        return 0

    def close(self) -> None:
        # nothing to do for this thin wrapper
        return


# End of core_bridge_fixed.py
