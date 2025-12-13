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

        try:
            if _is_windows():
                self.lib = ctypes.WinDLL(str(self.lib_path))
            else:
                self.lib = ctypes.CDLL(str(self.lib_path))
        except Exception as e:
            raise RuntimeError(f"Failed to load native library: {e}")

        try:
            dll_dir = self.lib_path.parent
            target = dll_dir / "words.txt"
            if not target.exists():
                shutil.copy2(self.words_path, target)
               # print(f"[DEBUG] Copied words file to {target}")
            else:
                # print(f"[DEBUG] words.txt already exists next to DLL at {target}; not overwriting")
                pass
        except Exception as e:
            print(f"[WARNING] Failed to copy words.txt next to DLL: {e}")

        self._init_db_fn = self._resolve_optional("init_db")
        if self._init_db_fn:
            try:
                self._init_db_fn()
            except Exception as e:
               # print(f"[WARNING] init_db raised: {e}")
               pass

        self._get_categories_fn = self._resolve_optional("get_categories", restype=c_char_p)
        self._get_category_fn = self._resolve_optional("get_category", restype=c_char_p)
        self._get_secret_fn = self._resolve_optional("get_secret", restype=c_char_p)
        self._get_lives_fn = self._resolve_optional("get_lives", restype=c_int)
        self._get_game_status_fn = self._resolve_optional("get_game_status", restype=c_int)

        self._start_game_fn = self._resolve_optional("start_game")
        if self._start_game_fn:
            try:
                self._start_game_fn.argtypes = [c_char_p]
                self._start_game_fn.restype = None
            except Exception:
                pass

        self._check_word_fn = self._resolve_optional("check_word_guess")
        if self._check_word_fn:
            try:
                self._check_word_fn.argtypes = [c_char_p, POINTER(c_int)]
                self._check_word_fn.restype = None
            except Exception:
                pass

        self._use_local_emulation = False
        self._local_secret = ""
        self._local_attempts = 0
        self._local_won = False
        self._local_lost = False

        self._all_words = self._load_words_file()
        if not self._all_words:
            print("[WARNING] No words loaded from words.txt; the game cannot run correctly.")

    def _resolve_optional(self, base_name: str, restype=None):
        if hasattr(self.lib, base_name):
            fn = getattr(self.lib, base_name)
            if restype is not None:
                try:
                    fn.restype = restype
                except Exception:
                    pass
            return fn
        candidates = [n for n in dir(self.lib) if base_name in n]
        if candidates:
            name = candidates[0]
           # print(f"[DEBUG] Resolved native symbol '{base_name}' -> '{name}'")
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
                    if ";" in s:
                        word, _ = s.split(";", 1)
                        words.append(word.strip().upper())
                    else:
                        words.append(s.strip().upper())
        except Exception as e:
           # print(f"[WARNING] Failed to load words file: {e}")
           pass
        return words

    def get_categories(self) -> list[str]:
        if self._get_categories_fn:
            try:
                raw = self._get_categories_fn() or b""
                text = raw.decode("utf-8")
                return text.split("|") if text else ["Any"]
            except Exception:
                pass
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
                        pass
        except Exception:
            pass
        return filtered

    def start_game(self, category: str = "Any", attempts: int = 5) -> None:
        self._use_local_emulation = False
        if self._start_game_fn:
            try:
                self._start_game_fn(category.encode("utf-8"))
            except Exception as e:
               # print(f"[WARNING] native start_game failed: {e}")
               pass

        native_secret = None
        if self._get_secret_fn:
            try:
                raw = self._get_secret_fn() or b""
                native_secret = raw.decode("utf-8") if raw else ""
            except Exception as e:
                print(f"[DEBUG] get_secret failed: {e}")
                native_secret = ""

        if not native_secret or native_secret.upper() not in self._all_words:
            candidates = self.filter_words_by_category(category)
            if not candidates:
                candidates = list(self._all_words)
            if not candidates:
                raise RuntimeError("No words available to start the game")
            self._local_secret = random.choice(candidates)
          #  print(f"[INFO] Using local emulation secret: {self._local_secret}")
            self._use_local_emulation = True
            self._local_attempts = attempts
            self._local_won = False
            self._local_lost = False
        else:
            self._local_secret = native_secret.upper()
            self._use_local_emulation = False

    def _evaluate_guess_local(self, guess: str) -> list[int]:
        guess = guess.upper()
        secret = self._local_secret.upper()
        
        if len(guess) != len(secret):
            raise ValueError("Guess length mismatch")
            
        from collections import Counter
        counts = Counter(secret)
        
        result = [0] * len(secret)
        
        for i, ch in enumerate(guess):
            if ch == secret[i]:
                result[i] = 2
                counts[ch] -= 1
        
        for i, ch in enumerate(guess):
            if result[i] == 2:
                continue
            
            if counts[ch] > 0:
                result[i] = 1
                counts[ch] -= 1
                
        return result

    def guess_word(self, word: str, length: int) -> list[int]:
        word_u = word.upper()
        if len(word_u) != length:
            raise ValueError("expected_len must match guess length")

        if self._check_word_fn and not self._use_local_emulation:
            arr = (c_int * length)()
            try:
                self._check_word_fn(word_u.encode("utf-8"), arr)
                return list(arr)
            except Exception as e:
                print(f"[WARNING] native check_word_guess failed: {e}")
           
        statuses = self._evaluate_guess_local(word_u)
        #update attempts/won/lost
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
        return