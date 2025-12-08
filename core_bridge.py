import ctypes
from ctypes import c_bool, c_char_p, c_int, c_void_p
from pathlib import Path


class GameState(ctypes.Structure):
    _fields_ = [
        ("masked_word", c_char_p),
        ("attempts_left", c_int),
        ("score", c_int),
        ("won", c_bool),
        ("lost", c_bool),
    ]

    def as_dict(self) -> dict:
        return {
            "masked_word": self.masked_word.decode("utf-8") if self.masked_word else "",
            "attempts_left": int(self.attempts_left),
            "score": int(self.score),
            "won": bool(self.won),
            "lost": bool(self.lost),
        }


class GameCore:
    def __init__(self, dll_path: str | Path, words_path: str | Path):
        self.dll_path = Path(dll_path)
        self.words_path = Path(words_path)
        if not self.dll_path.exists():
            raise FileNotFoundError(f"Cannot find DLL: {self.dll_path}")
        if not self.words_path.exists():
            raise FileNotFoundError(f"Cannot find words file: {self.words_path}")

        try:
            # Debugging ctypes import
            if 'ctypes' not in globals():
                raise ImportError("ctypes module is not available in the current environment.")
            print("[DEBUG] ctypes module is available.")

            # Attempt to load the DLL
            self._lib = ctypes.CDLL(str(self.dll_path))
        except ImportError as e:
            raise RuntimeError(f"ctypes module is missing. Error: {e}")
        except OSError as e:
            raise RuntimeError(f"Failed to load DLL: {self.dll_path}. Ensure it is compatible with the Python environment. Error: {e}")

        try:
            # Try to get exported functions from DLL
            funcs = []
            for name in dir(self._lib):
                if not name.startswith('_') and callable(getattr(self._lib, name, None)):
                    funcs.append(name)
            if funcs:
                print(f"[DEBUG] Available DLL functions: {funcs}")
            else:
                print("[WARNING] No exported functions found in DLL! Please rebuild the DLL.")
                print("[INFO] See BUILD_INSTRUCTIONS.md for rebuild instructions")
        except Exception as e:
            print(f"[DEBUG] Could not list DLL functions: {e}")

        self._configure_functions()
        self._handle: c_void_p | None = None
        self._create_engine()

        print(f"[DEBUG] Fetching game state after initialization")
        state = self.get_state().as_dict()
        print(f"[DEBUG] Game state: {state}")

    def _configure_functions(self) -> None:
        # Core API
        self._lib.create_engine.argtypes = [c_char_p]
        self._lib.create_engine.restype = c_void_p

        self._lib.destroy_engine.argtypes = [c_void_p]
        self._lib.destroy_engine.restype = None

        self._lib.start_game.argtypes = [c_void_p, c_int, c_char_p]
        self._lib.start_game.restype = c_int

        # Category API - always try to configure if available
        try:
            if hasattr(self._lib, "get_categories"):
                self._lib.get_categories.argtypes = [c_void_p]
                self._lib.get_categories.restype = c_char_p
                print("[DEBUG] get_categories function found and configured")
            else:
                print("[WARNING] get_categories function NOT found in DLL")
        except Exception as e:
            print(f"[WARNING] Failed to configure get_categories: {e}")

        self._lib.guess_letter.argtypes = [c_void_p, c_char_p]
        self._lib.guess_letter.restype = c_int

        self._lib.guess_word.argtypes = [c_void_p, c_char_p, ctypes.POINTER(c_int), c_int]
        self._lib.guess_word.restype = c_int

        # Prefer a safe filling API when available to avoid returning
        # structures by value across ABIs.
        self._has_get_state_copy = False
        if hasattr(self._lib, "get_state_copy"):
            try:
                self._lib.get_state_copy.argtypes = [c_void_p, ctypes.POINTER(GameState)]
                self._lib.get_state_copy.restype = c_int
                self._has_get_state_copy = True
            except Exception:
                self._has_get_state_copy = False

        # Fallback older API (may return by value)
        if hasattr(self._lib, "get_state"):
            try:
                self._lib.get_state.argtypes = [c_void_p]
                self._lib.get_state.restype = GameState
            except Exception:
                # ignore failures — we'll prefer get_state_copy
                pass

        self._lib.get_last_error.argtypes = [ctypes.c_char_p, c_int]
        self._lib.get_last_error.restype = c_int

    def _create_engine(self) -> None:
        words_bytes = str(self.words_path).encode("utf-8")
        handle = self._lib.create_engine(words_bytes)
        if not handle:
            raise RuntimeError(self._last_error() or "Failed to create engine")
        self._handle = handle

    def _require_handle(self) -> c_void_p:
        if not self._handle:
            raise RuntimeError("Engine handle is not available")
        return self._handle

    def _last_error(self) -> str:
        buffer = ctypes.create_string_buffer(512)
        self._lib.get_last_error(buffer, len(buffer))
        return buffer.value.decode("utf-8")

    def start_game(self, attempts: int = 6, category: str = "Any", word: str = "") -> None:
        print(f"[DEBUG] Initializing game engine with word: {word} and category: {category}")
        try:
            # Pass the selected word to the game engine
            word_bytes = word.encode("utf-8")
            category_bytes = category.encode("utf-8") if category else b"Any"
            result = self._lib.start_game(self._require_handle(), attempts, category_bytes, word_bytes)
            if result != 0:
                raise RuntimeError(self._last_error() or "start_game failed")
        except Exception as e:
            raise RuntimeError(f"Failed to start game with word '{word}' and category '{category}': {e}")

    def get_categories(self) -> list[str]:
        try:
            # Parse categories directly from words.txt
            with self.words_path.open("r", encoding="utf-8") as file:
                categories = set()
                for line in file:
                    if ";" in line:
                        _, category = line.strip().split(";", 1)
                        categories.add(category.strip())
                return sorted(categories)
        except Exception as e:
            print(f"[ERROR] Failed to parse categories from words.txt: {e}")
            return ["Any"]

    def guess_letter(self, letter: str) -> int:
        if not letter or len(letter) != 1:
            raise ValueError("Letter must be a single character")
        # pass single byte char
        result = self._lib.guess_letter(self._require_handle(), letter.encode("utf-8"))
        if result == -1:
            raise RuntimeError(self._last_error() or "guess_letter failed")
        return result

    def guess_word(self, guess: str, expected_len: int) -> list[int]:
        if expected_len <= 0:
            raise ValueError("expected_len must be positive")
        encoded = guess.encode("utf-8")
        buffer = (c_int * expected_len)()
        result = self._lib.guess_word(self._require_handle(), encoded, buffer, expected_len)
        if result == -1:
            raise RuntimeError(self._last_error() or "guess_word failed")
        return [int(buffer[i]) for i in range(expected_len)]

    def get_state(self) -> GameState:
        # Prefer the safe filling API when available.
        if self._has_get_state_copy:
            out = GameState()
            res = self._lib.get_state_copy(self._require_handle(), ctypes.byref(out))
            if res != 0:
                raise RuntimeError(self._last_error() or "get_state_copy failed")
            # Convert masked_word to Python-managed bytes to avoid referencing
            # memory owned by the native side. Do not attempt to free native
            # memory here.
            masked = out.masked_word.decode("utf-8") if out.masked_word else ""
            safe = GameState()
            safe.masked_word = masked.encode("utf-8")
            safe.attempts_left = int(out.attempts_left)
            safe.score = int(out.score)
            safe.won = bool(out.won)
            safe.lost = bool(out.lost)
            return safe

        # Fallback - older API that returns a struct by value
        if hasattr(self._lib, "get_state"):
            raw = self._lib.get_state(self._require_handle())
            masked = raw.masked_word.decode("utf-8") if raw.masked_word else ""
            safe = GameState()
            safe.masked_word = masked.encode("utf-8")
            safe.attempts_left = int(raw.attempts_left)
            safe.score = int(raw.score)
            safe.won = bool(raw.won)
            safe.lost = bool(raw.lost)
            return safe

        raise RuntimeError("No supported get_state API found in the DLL")

    def close(self) -> None:
        if self._handle:
            self._lib.destroy_engine(self._handle)
            self._handle = None

    def __enter__(self) -> "GameCore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def get_current_category(self) -> str:
        # Placeholder implementation
        print("[WARNING] get_current_category is not implemented in the DLL.")
        return "Any"

    def filter_words_by_category(self, category: str) -> list[str]:
        try:
            # Filter words based on the selected category
            with self.words_path.open("r", encoding="utf-8") as file:
                filtered_words = []
                for line in file:
                    if ";" in line:
                        word, word_category = line.strip().split(";", 1)
                        if category == "Any" or word_category.strip() == category:
                            filtered_words.append(word.strip())
                return filtered_words
        except Exception as e:
            print(f"[ERROR] Failed to filter words by category: {e}")
            return []
"""
# core_bridge.py
import ctypes
from ctypes import c_char_p, c_int, POINTER
from pathlib import Path

class GameCore:
    def __init__(self, lib_path: Path, words_path: Path):
        if not lib_path.exists():
            raise FileNotFoundError(f"Не знайдено бібліотеку: {lib_path}")

        # On Windows the DLL was built using __stdcall; use WinDLL
        # so ctypes looks up stdcall-decorated symbols correctly.
        try:
            import sys
            if sys.platform.startswith("win"):
                self.lib = ctypes.WinDLL(str(lib_path))
            else:
                self.lib = ctypes.CDLL(str(lib_path))
        except Exception:
            # Fallback
            self.lib = ctypes.CDLL(str(lib_path))

        # Initialize the native DB (if available)
        if hasattr(self.lib, "init_db"):
            try:
                self.lib.init_db()
            except Exception as e:
                # Some builds may export a decorated name; warn but continue
                print(f"[WARNING] init_db call failed: {e}")
        else:
            print("[WARNING] init_db symbol not found in DLL; continuing")

        # Налаштування функцій — резолвимо символи безпечно (декоровані імена)
        def _resolve_symbol(base_name: str):
            # direct attribute
            if hasattr(self.lib, base_name):
                return getattr(self.lib, base_name)
            # try to find a symbol containing the base name (decorated stdcall like _name@0)
            candidates = [n for n in dir(self.lib) if base_name in n]
            if candidates:
                resolved = getattr(self.lib, candidates[0])
                print(f"[DEBUG] Resolved native symbol '{base_name}' -> '{candidates[0]}'")
                return resolved
            raise AttributeError(f"Symbol '{base_name}' not found in native library")

        # Configure optional/category-related APIs
        try:
            get_categories_fn = _resolve_symbol("get_categories")
            get_categories_fn.restype = c_char_p
            self._get_categories_fn = get_categories_fn
        except AttributeError:
            print("[WARNING] get_categories not found in DLL")
            self._get_categories_fn = None

        try:
            get_category_fn = _resolve_symbol("get_category")
            get_category_fn.restype = c_char_p
            self._get_category_fn = get_category_fn
        except AttributeError:
            print("[WARNING] get_category not found in DLL")
            self._get_category_fn = None

        try:
            get_secret_fn = _resolve_symbol("get_secret")
            get_secret_fn.restype = c_char_p
            self._get_secret_fn = get_secret_fn
        except AttributeError:
            print("[WARNING] get_secret not found in DLL")
            self._get_secret_fn = None

        try:
            get_lives_fn = _resolve_symbol("get_lives")
            get_lives_fn.restype = c_int
            self._get_lives_fn = get_lives_fn
        except AttributeError:
            print("[WARNING] get_lives not found in DLL")
            self._get_lives_fn = None

        try:
            get_game_status_fn = _resolve_symbol("get_game_status")
            get_game_status_fn.restype = c_int
            self._get_game_status_fn = get_game_status_fn
        except AttributeError:
            print("[WARNING] get_game_status not found in DLL")
            self._get_game_status_fn = None

        # start_game and check_word_guess
        try:
            start_game_fn = _resolve_symbol("start_game")
            start_game_fn.argtypes = [c_char_p]
            start_game_fn.restype = None
            self._start_game_fn = start_game_fn
        except AttributeError:
            print("[WARNING] start_game not found in DLL")
            self._start_game_fn = None

        try:
            check_word_fn = _resolve_symbol("check_word_guess")
            check_word_fn.argtypes = [c_char_p, POINTER(c_int)]
            check_word_fn.restype = None
            self._check_word_fn = check_word_fn
        except AttributeError:
            print("[WARNING] check_word_guess not found in DLL")
            self._check_word_fn = None

    def get_categories(self) -> list[str]:
        # Prefer native API when available, otherwise parse words.txt
        if getattr(self, '_get_categories_fn', None):
            raw = self._get_categories_fn() or b""
            text = raw.decode("utf-8")
            return text.split("|") if text else ["Any"]

        # Fallback: parse words file
        try:
            with Path(self.words_path).open('r', encoding='utf-8') as f:
                cats = set()
                for line in f:
                    if ';' in line:
                        _, cat = line.strip().split(';', 1)
                        cats.add(cat.strip())
                return sorted(cats) if cats else ["Any"]
        except Exception:
            return ["Any"]

    def get_current_category(self) -> str:
        if getattr(self, '_get_category_fn', None):
            raw = self._get_category_fn() or b""
            return raw.decode("utf-8") or "Any"
        return "Any"

    def start_game(self, category: str = "Any"):
        if not getattr(self, '_start_game_fn', None):
            raise RuntimeError("start_game function is not available in native library")
        self._start_game_fn(category.encode("utf-8"))

    def guess_word(self, word: str, length: int) -> list[int]:
        if not getattr(self, '_check_word_fn', None):
            raise RuntimeError("check_word_guess function is not available in native library")
        arr = (c_int * length)()
        self._check_word_fn(word.upper().encode("utf-8"), arr)
        return list(arr)

    def get_state(self):
        class State:
            current_word = (self._get_secret_fn() or b"").decode("utf-8") if getattr(self, '_get_secret_fn', None) else ""
            current_category = self.get_current_category()
            attempts_left = self._get_lives_fn() if getattr(self, '_get_lives_fn', None) else 0
            status = self._get_game_status_fn() if getattr(self, '_get_game_status_fn', None) else 0
            won = (status == 1)
            lost = (status == -1)
        return State()
        """