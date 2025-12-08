from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core_bridge_fixed import GameCore


class Language(Enum):
    EN = "en"
    UK = "uk"


TRANSLATIONS = {
    Language.EN: {
        "app_title": "Guess The Word",
        "menu_title": "Guess The Word",
        "btn_start": "Start Game",
        "btn_stats": "Statistics",
        "btn_exit": "Exit",
        "stats_title": "Statistics",
        "stats_wins": "Wins: {value}",
        "stats_losses": "Losses: {value}",
        "stats_rate": "Win rate: {value:.1f}%",
        "game_title": "Daily Puzzle",
        "btn_restart": "Restart",
        "btn_back": "Back",
        "btn_submit": "Submit",
        "word_hint": "Word: {mask}",
        "attempts_label": "Attempts left: {count}",
        "input_placeholder": "Type your guess",
        "invalid_guess_title": "Invalid guess",
        "invalid_guess_length": "Word must contain {count} letters",
        "victory_title": "Victory",
        "victory_message": "Perfect! You guessed the word.",
        "defeat_title": "Defeat",
        "defeat_message": "No attempts left. Try again!",
        "error_title": "Error",
        "btn_language_to_uk": "Українська",
        "btn_language_to_en": "English",
    },
    Language.UK: {
        "app_title": "Вгадай слово",
        "menu_title": "Вгадай слово",
        "btn_start": "Почати гру",
        "btn_stats": "Статистика",
        "btn_exit": "Вихід",
        "stats_title": "Статистика",
        "stats_wins": "Перемоги: {value}",
        "stats_losses": "Поразки: {value}",
        "stats_rate": "Відсоток перемог: {value:.1f}%",
        "game_title": "Щоденний челендж",
        "btn_restart": "Рестарт",
        "btn_back": "Назад",
        "btn_submit": "Перевірити",
        "word_hint": "Слово: {mask}",
        "attempts_label": "Залишилось спроб: {count}",
        "input_placeholder": "Введи слово",
        "invalid_guess_title": "Неправильне слово",
        "invalid_guess_length": "Слово має містити {count} літер",
        "victory_title": "Перемога",
        "victory_message": "Чудово! Ти відгадав слово.",
        "defeat_title": "Поразка",
        "defeat_message": "Спроби закінчились. Спробуй ще!",
        "error_title": "Помилка",
        "btn_language_to_uk": "Українська",
        "btn_language_to_en": "English",
    },
}


class LetterStatus(IntEnum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


STATUS_COLORS = {
    LetterStatus.CORRECT: "#27ae60",
    LetterStatus.PRESENT: "#f39c12",
    LetterStatus.ABSENT: "#c0392b",
}


@dataclass
class GameStats:
    wins: int = 0
    losses: int = 0

    @property
    def total(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        return (self.wins / self.total) * 100 if self.total else 0.0


class StatsStore:
    def __init__(self, path: Path, persist: bool = True):
        self.path = path
        self.persist = bool(persist)
        self.data = GameStats()
        if self.persist:
            self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self.data = GameStats(**raw)
        except Exception:
            self.data = GameStats()

    def save(self) -> None:
        if not self.persist:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self.data.__dict__, fh, indent=2)

    def record(self, won: bool) -> None:
        if won:
            self.data.wins += 1
        else:
            self.data.losses += 1
        self.save()


class MenuFrame(ctk.CTkFrame):
    def __init__(self, master: "GameApp"):
        super().__init__(master, fg_color="white")
        self.master_app = master
        self.title_label = ctk.CTkLabel(self, font=("Segoe UI", 32, "bold"))
        self.title_label.pack(pady=30)

        self.start_button = ctk.CTkButton(self, text="", width=220, height=45, command=self.master_app.show_game)
        self.stats_button = ctk.CTkButton(self, text="", width=220, height=45, command=self.master_app.show_stats)
        self.exit_button = ctk.CTkButton(self, text="", width=220, height=45, command=self.master_app.destroy)

        self.start_button.pack(pady=10)
        self.stats_button.pack(pady=10)
        self.exit_button.pack(pady=10)

    def refresh_texts(self) -> None:
        self.title_label.configure(text=self.master_app.t("menu_title"))
        self.start_button.configure(text=self.master_app.t("btn_start"))
        self.stats_button.configure(text=self.master_app.t("btn_stats"))
        self.exit_button.configure(text=self.master_app.t("btn_exit"))


class StatsFrame(ctk.CTkFrame):
    def __init__(self, master: "GameApp"):
        super().__init__(master, fg_color="white")
        self.master_app = master
        self.title_label = ctk.CTkLabel(self, font=("Segoe UI", 32, "bold"))
        self.win_label = ctk.CTkLabel(self, font=("Segoe UI", 20))
        self.loss_label = ctk.CTkLabel(self, font=("Segoe UI", 20))
        self.rate_label = ctk.CTkLabel(self, font=("Segoe UI", 20))
        self.back_button = ctk.CTkButton(self, width=160, command=self.master_app.show_menu)

        self.title_label.pack(pady=30)
        self.win_label.pack(pady=5)
        self.loss_label.pack(pady=5)
        self.rate_label.pack(pady=5)
        self.back_button.pack(pady=25)

    def refresh(self) -> None:
        stats = self.master_app.stats_store.data
        self.win_label.configure(text=self.master_app.t("stats_wins", value=stats.wins))
        self.loss_label.configure(text=self.master_app.t("stats_losses", value=stats.losses))
        self.rate_label.configure(text=self.master_app.t("stats_rate", value=stats.win_rate))

    def refresh_texts(self) -> None:
        self.title_label.configure(text=self.master_app.t("stats_title"))
        self.back_button.configure(text=self.master_app.t("btn_back"))
        self.refresh()


class GameFrame(ctk.CTkFrame):
    def __init__(self, master: "GameApp"):
        super().__init__(master, fg_color="white")
        self.master_app = master
        self.word_length = 0
        self._game_over = False
        self._latest_secret = ""
        self.hearts: list[ctk.CTkLabel] = []
        self.guess_rows: list[ctk.CTkFrame] = []
        self.placeholder_tiles: list[ctk.CTkLabel] = []

        # Top bar
        self.top_bar = ctk.CTkFrame(self, fg_color="white")
        self.title_label = ctk.CTkLabel(self.top_bar, font=("Segoe UI", 26, "bold"))
        self.target_label = ctk.CTkLabel(self.top_bar, font=("Segoe UI", 26, "bold"))
        self.top_right_vbox = ctk.CTkFrame(self.top_bar, fg_color="white")
        self.language_button = ctk.CTkButton(self.top_right_vbox, width=140, text="", command=lambda: self.master_app.toggle_language())
        self.language_button.pack(side="top", pady=(4, 2))
        self.hearts_frame = ctk.CTkFrame(self.top_right_vbox, fg_color="white")
        self.hearts_frame.pack(side="top")

        # Layout
        self.placeholder_row = ctk.CTkFrame(self, fg_color="white")
        self.guess_container = ctk.CTkScrollableFrame(self, fg_color="#f8f8f8")

        self.input_row = ctk.CTkFrame(self, fg_color="white")
        self.entry = ctk.CTkEntry(self.input_row, height=40, font=("Segoe UI", 18))
        self.submit_button = ctk.CTkButton(self.input_row, height=40, command=self._submit_guess)

        self.control_row = ctk.CTkFrame(self, fg_color="white")
        self.restart_button = ctk.CTkButton(self.control_row, width=120, command=self.start_game)
        self.back_button = ctk.CTkButton(self.control_row, width=120, command=self.master_app.show_menu)

        self._build()

    def _build(self) -> None:
        self.top_bar.pack(fill="x", padx=10, pady=(10, 5))
        self.title_label.pack(side="left")
        self.target_label.pack(side="left", padx=8)
        self.top_right_vbox.pack(side="right", padx=10)
        self._build_hearts()

        self.placeholder_row.pack(fill="x", padx=20, pady=(5, 0))
        self.guess_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.input_row.pack(fill="x", padx=20, pady=(0, 10))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda _e: self._submit_guess())
        self.submit_button.pack(side="left")

        self.control_row.pack(pady=(0, 15))
        self.restart_button.pack(side="left", padx=5)
        self.back_button.pack(side="left", padx=5)

    def _build_hearts(self) -> None:
        for h in self.hearts:
            h.destroy()
        self.hearts.clear()
        for _ in range(self.master_app.attempts_per_game):
            heart = ctk.CTkLabel(self.hearts_frame, text="♥", font=("Segoe UI", 26), text_color="#c0392b")
            heart.pack(side="left", padx=2)
            self.hearts.append(heart)

    def start_game(self) -> None:
        try:
            self.master_app.core.start_game()
        except Exception as exc:
            messagebox.showerror(self.master_app.t("error_title"), str(exc))
            return

        try:
            secret = self.master_app.core.get_secret() or b""
            if isinstance(secret, bytes):
                secret = secret.decode("utf-8")
        except Exception:
            secret = ""

        self._latest_secret = secret
        self.word_length = len(secret) if secret else 5
        self._game_over = False
        self.entry.configure(state="normal")
        self.submit_button.configure(state="normal")
        self.entry.delete(0, "end")
        self._reset_board()
        self._build_hearts()
        self._update_state()

    def _reset_board(self) -> None:
        for row in self.guess_rows:
            row.destroy()
        self.guess_rows.clear()
        for t in self.placeholder_tiles:
            t.destroy()
        self.placeholder_tiles.clear()

    def _submit_guess(self) -> None:
        if self._game_over:
            return
        guess = self.entry.get().strip().upper()
        if not guess:
            return
        if self.word_length <= 0 or len(guess) != self.word_length:
            messagebox.showerror(self.master_app.t("invalid_guess_title"), self.master_app.t("invalid_guess_length", count=self.word_length))
            return
        try:
            statuses = self.master_app.core.guess_word(guess, self.word_length)
        except Exception as exc:
            messagebox.showerror(self.master_app.t("error_title"), str(exc))
            return

        self.entry.delete(0, "end")
        self._append_guess_row(guess, statuses)
        self._update_state()

    def _append_guess_row(self, word: str, statuses: list[int]) -> None:
        row = ctk.CTkFrame(self.guess_container, fg_color="#f8f8f8")
        row.pack(pady=5)
        for idx, ch in enumerate(word):
            val = statuses[idx] if idx < len(statuses) else 0
            status = LetterStatus(val)
            color = STATUS_COLORS.get(status, "#bdc3c7")
            tile = ctk.CTkLabel(row, text=ch, width=60, height=60, corner_radius=8, fg_color=color, text_color="white", font=("Consolas", 28, "bold"))
            tile.pack(side="left", padx=5)
        self.guess_rows.append(row)

    def _update_state(self) -> None:
        attempts_left = None
        won = False
        lost = False
        try:
            attempts_left = int(self.master_app.core.get_lives())
        except Exception:
            attempts_left = None
        try:
            status = int(self.master_app.core.get_game_status())
            won = (status == 1)
            lost = (status == -1)
        except Exception:
            try:
                s = self.master_app.core.get_state()
                if hasattr(s, "as_dict"):
                    sd = s.as_dict()
                    attempts_left = sd.get("attempts_left", attempts_left)
                    won = sd.get("won", False)
                    lost = sd.get("lost", False)
                else:
                    attempts_left = getattr(s, "attempts_left", attempts_left)
                    won = getattr(s, "won", won)
                    lost = getattr(s, "lost", lost)
            except Exception:
                pass

        if attempts_left is None:
            attempts_left = self.master_app.attempts_per_game

        mask_word = "?" * self.word_length
        if won:
            try:
                secret = self.master_app.core.get_secret() or b""
                if isinstance(secret, bytes):
                    secret = secret.decode("utf-8")
            except Exception:
                secret = self._latest_secret
            if secret:
                mask_word = secret
        self.target_label.configure(text=self.master_app.t("word_hint", mask=mask_word))
        self._update_placeholder_tiles(mask_word)
        self._update_hearts(attempts_left)

        if won and not self._game_over:
            self.master_app.stats_store.record(True)
            self._game_over = True
            self._lock_inputs()
            messagebox.showinfo(self.master_app.t("victory_title"), self.master_app.t("victory_message"))
        elif lost and not self._game_over:
            self.master_app.stats_store.record(False)
            self._game_over = True
            self._lock_inputs()
            messagebox.showwarning(self.master_app.t("defeat_title"), self.master_app.t("defeat_message"))

    def _update_hearts(self, attempts_left: int) -> None:
        for idx, heart in enumerate(self.hearts):
            color = "#c0392b" if idx < attempts_left else "#dfe4ea"
            heart.configure(text_color=color)

    def _lock_inputs(self) -> None:
        self.entry.configure(state="disabled")
        self.submit_button.configure(state="disabled")

    def _update_placeholder_tiles(self, mask: str) -> None:
        for t in self.placeholder_tiles:
            t.destroy()
        self.placeholder_tiles.clear()
        if not mask:
            return
        for ch in mask:
            tile = ctk.CTkLabel(self.placeholder_row, text=ch, width=48, height=48, corner_radius=6, fg_color="#ecf0f1", text_color="#2c3e50", font=("Consolas", 24, "bold"))
            tile.pack(side="left", padx=4, pady=4)
            self.placeholder_tiles.append(tile)

    def refresh_texts(self) -> None:
        self.title_label.configure(text=self.master_app.t("game_title"))
        self.target_label.configure(text=self.master_app.t("word_hint", mask=("?" * self.word_length)))
        self.restart_button.configure(text=self.master_app.t("btn_restart"))
        self.back_button.configure(text=self.master_app.t("btn_back"))
        self.submit_button.configure(text=self.master_app.t("btn_submit"))
        self.entry.configure(placeholder_text=self.master_app.t("input_placeholder"))
        lang_text = self.master_app.t("btn_language_to_uk") if self.master_app.language == Language.EN else self.master_app.t("btn_language_to_en")
        self.language_button.configure(text=lang_text)


class GameApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.attempts_per_game = 5
        self.geometry("850x650")
        self.resizable(False, False)
        self.configure(fg_color="#f2f2f2")

        self._ui_dir = Path(__file__).resolve().parent
        self.project_root = self._ui_dir.parent
        self.language = Language.EN
        self.stats_store = StatsStore(self._ui_dir / "stats.json", persist=True)

        # load core
        try:
            lib_path = self._resolve_library_path()
            words = self.project_root / "words.txt"
            self.core = GameCore(lib_path, words)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load game core: {e}")
            raise

        # frames
        self.menu_frame = MenuFrame(self)
        self.game_frame = GameFrame(self)
        self.stats_frame = StatsFrame(self)

        self.menu_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self._apply_language()

    def _resolve_library_path(self) -> Path:
        binary = "game_core.dll" if self._is_windows() else ("libgame_core.dylib" if self._is_macos() else "libgame_core.so")
        candidates = [
            self._ui_dir / binary,
            self.project_root / "cpp_core" / "build" / "Release" / binary,
            self.project_root / "cpp_core" / "build" / binary,
        ]
        for c in candidates:
            if c.exists():
                dest = self._ui_dir / binary
                if c.resolve() != dest.resolve():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    from shutil import copy2

                    copy2(c, dest)
                return dest
        raise FileNotFoundError("Cannot find native game core. Build C++ project first.")

    @staticmethod
    def _is_windows() -> bool:
        import sys

        return sys.platform.startswith("win")

    @staticmethod
    def _is_macos() -> bool:
        import sys

        return sys.platform == "darwin"

    def show_menu(self) -> None:
        self._show_frame(self.menu_frame)

    def show_game(self) -> None:
        self._show_frame(self.game_frame)
        # start a new game when entering
        self.game_frame.start_game()

    def show_stats(self) -> None:
        self._show_frame(self.stats_frame)

    def _show_frame(self, frame: ctk.CTkFrame) -> None:
        for child in (self.menu_frame, self.game_frame, self.stats_frame):
            child.pack_forget()
        frame.pack(fill="both", expand=True, padx=20, pady=20)

    def t(self, key: str, **kwargs) -> str:
        return TRANSLATIONS[self.language][key].format(**kwargs)

    def toggle_language(self) -> None:
        self.language = Language.UK if self.language == Language.EN else Language.EN
        self._apply_language()

    def _apply_language(self) -> None:
        self.title(self.t("app_title"))
        self.menu_frame.refresh_texts()
        self.stats_frame.refresh_texts()
        self.game_frame.refresh_texts()


def main() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    main()