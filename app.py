from __future__ import annotations

import webbrowser
import json
import sys
import time
import random
from dataclasses import dataclass
import webbrowser
from enum import Enum, IntEnum
from pathlib import Path
from tkinter import messagebox
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import customtkinter as ctk

from core_bridge import GameCore

def run_intro():
    pygame.init()
    display = (800, 600)
    
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL | NOFRAME)
    pygame.display.set_caption("Leksa Game Intro")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, (display[0] / display[1]), 0.1, 50.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, -0.5, -7) 
    glRotatef(25, 1, 0, 0) 

    vertices = (
        (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
        (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
    )
    edges = (
        (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
        (6,3), (6,4), (6,7), (5,1), (5,4), (5,7)
    )
    surfaces = (
        (0,1,2,3), (3,2,7,6), (6,7,5,4),
        (4,5,1,0), (1,5,7,2), (4,0,3,6)
    )

    colors = (
        (0.8, 0.4, 0.4), (0.4, 0.8, 0.4), (0.4, 0.4, 0.8),
        (0.8, 0.8, 0.4), (0.8, 0.4, 0.8), (0.4, 0.8, 0.8)
    )

    def draw_cube():
        glBegin(GL_QUADS)
        for i, surface in enumerate(surfaces):
            glColor3fv(colors[i])
            for vertex in surface:
                glVertex3fv(vertices[vertex])
        glEnd()

        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3fv((0.2, 0.2, 0.2)) 
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

    font = pygame.font.SysFont("Arial", 64, bold=True)
    text_surface = font.render("GUESS THE WORD", True, (50, 50, 50))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_size()

    def draw_text_overlay():
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, display[0], 0, display[1])
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        raster_x = (display[0] - text_width) / 2
        raster_y = display[1] - text_height - 50

        glRasterPos2f(raster_x, raster_y)
        glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    clock = pygame.time.Clock()
    start_time = time.time()
    duration = 2.5
    running = True

    glEnable(GL_DEPTH_TEST)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        if time.time() - start_time > duration:
            running = False

        glRotatef(1.5, 0, 1, 0) 

        glClearColor(0.9, 0.9, 0.9, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        draw_cube()
        draw_text_overlay()
        
        pygame.display.flip()
        clock.tick(60)
    pygame.display.quit() 


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
        "msg_hint_no_lives": "Not enough lives for a hint!",
        "msg_hint_all_revealed": "All letters already revealed!",
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
        "msg_hint_no_lives": "Недостатньо життів для підказки!",
        "msg_hint_all_revealed": "Усі літери вже відкриті!",
    },
}
CATEGORY_TRANSLATIONS = {
    Language.EN: {
        "ANIMAL": "Animal",
        "CAR_BRAND": "Car brand",
        "CITY": "City",
        "COLOR": "Color",
        "EDUCATION": "Education",
        "FINANCE": "Finance",
        "FOOD": "Food",
        "FRUIT": "Fruit",
        "GEOGRAPHY": "Geography",
        "HARDWARE": "Hardware",
        "OPERATING_SYSTEM": "Operating system",
        "PROFESSION": "Profession",
        "PROGRAMMING": "Programming",
        "SEASON": "Season",
        "SOCIAL": "Social",
        "SPACE": "Space",
        "SPORT": "Sport",
        "TECHNOLOGY": "Technology",
        "ANY": "Any", 
    },
    Language.UK: {
        "ANIMAL": "Тварина",
        "CAR_BRAND": "Марка авто",
        "CITY": "Місто",
        "COLOR": "Колір",
        "EDUCATION": "Освіта",
        "FINANCE": "Фінанси",
        "FOOD": "Їжа",
        "FRUIT": "Фрукт",
        "GEOGRAPHY": "Географія",
        "HARDWARE": "Апаратне забезпечення",
        "OPERATING_SYSTEM": "Операційна система",
        "PROFESSION": "Професія",
        "PROGRAMMING": "Програмування",
        "SEASON": "Сезон",
        "SOCIAL": "Соціальне",
        "SPACE": "Космос",
        "SPORT": "Спорт",
        "TECHNOLOGY": "Технології",
        "ANY": "Будь-яка", 
    },
}

WORD_TRANSLATIONS_MAP = {
    "PYTHON": "ПІТОН", "JAVA": "ДЖАВА", "SCRIPT": "СКРИПТ", "CPP": "СІПЛЮС", "RUBY": "РУБІ", "SWIFT": "СВІФТ",
    "SERVER": "СЕРВЕР", "DATABASE": "БАЗА", "NETWORK": "МЕРЕЖА", "INTERNET": "ІНТЕРНЕТ", "CLOUD": "ХМАРА", "ROBOT": "РОБОТ",
    "LINUX": "ЛІНУКС", "WINDOWS": "ВІНДОВС", "MACOS": "МАКОС", "ANDROID": "АНДРОЇД", "UNIX": "ЮНІКС",
    "DISPLAY": "ЕКРАН", "MONITOR": "МОНІТОР", "KEYBOARD": "КЛАВІАТУРА", "LAPTOP": "НОУТБУК", "MEMORY": "ПАМЯТЬ", "CAMERA": "КАМЕРА",
    "MOUSE": "МИША", "PRINTER": "ПРИНТЕР", "ROUTER": "РОУТЕР",
    "UKRAINE": "УКРАЇНА", "POLAND": "ПОЛЬЩА", "FRANCE": "ФРАНЦІЯ", "CANADA": "КАНАДА", "BRAZIL": "БРАЗИЛІЯ",
    "JAPAN": "ЯПОНІЯ", "ITALY": "ІТАЛІЯ", "SPAIN": "ІСПАНІЯ", "CHINA": "КИТАЙ",
    "LONDON": "ЛОНДОН", "PARIS": "ПАРИЖ", "KYIV": "КИЇВ", "BERLIN": "БЕРЛІН", "TOKYO": "ТОКІО", "LVIV": "ЛЬВІВ", "ROME": "РИМ", "OSLO": "ОСЛО",
    "APPLE": "ЯБЛУКО", "BANANA": "БАНАН", "ORANGE": "АПЕЛЬСИН", "LEMON": "ЛИМОН", "CHERRY": "ВИШНЯ", "MANGO": "МАНГО", "PEACH": "ПЕРСИК", "GRAPE": "ВИНОГРАД",
    "PIZZA": "ПІЦА", "BURGER": "БУРГЕР", "SUSHI": "СУШІ", "PASTA": "ПАСТА", "BREAD": "ХЛІБ", "SOUP": "СУП", "STEAK": "СТЕЙК", "CAKE": "ТОРТ",
    "TIGER": "ТИГР", "EAGLE": "ОРЕЛ", "SHARK": "АКУЛА", "PANDA": "ПАНДА", "ZEBRA": "ЗЕБРА", "HORSE": "КІНЬ", "RABBIT": "КРОЛИК", "LION": "ЛЕВ", "WOLF": "ВОВК", "BEAR": "ВЕДМІДЬ",
    "TOYOTA": "ТОЙОТА", "TESLA": "ТЕСЛА", "HONDA": "ХОНДА", "VOLVO": "ВОЛЬВО", "FORD": "ФОРД", "BMW": "БМВ", "AUDI": "АУДІ", "NISSAN": "НІССАН",
    "SOCCER": "ФУТБОЛ", "TENNIS": "ТЕНІС", "HOCKEY": "ХОКЕЙ", "BOXING": "БОКС", "RUGBY": "РЕГБІ", "GOLF": "ГОЛЬФ", "JUDO": "ДЗЮДО",
    "DOCTOR": "ЛІКАР", "DRIVER": "ВОДІЙ", "ARTIST": "МИТЕЦЬ", "FARMER": "ФЕРМЕР", "PILOT": "ПІЛОТ", "CHEF": "КУХАР", "NURSE": "МЕДСЕСТРА",
    "GALAXY": "ГАЛАКТИКА", "PLANET": "ПЛАНЕТА", "ORBIT": "ОРБІТА", "ROCKET": "РАКЕТА", "MOON": "МІСЯЦЬ", "MARS": "МАРС", "STAR": "ЗІРКА",
    "SUMMER": "ЛІТО", "WINTER": "ЗИМА", "AUTUMN": "ОСІНЬ", "SPRING": "ВЕСНА",
    "YELLOW": "ЖОВТИЙ", "PURPLE": "ФІОЛЕТОВИЙ", "SILVER": "СРІБНИЙ", "RED": "ЧЕРВОНИЙ", "BLUE": "СИНІЙ", "GREEN": "ЗЕЛЕНИЙ",
    "SCHOOL": "ШКОЛА", "LESSON": "УРОК", "STUDENT": "СТУДЕНТ", "TEACHER": "ВЧИТЕЛЬ", "BOOK": "КНИГА", "EXAM": "ЕКЗАМЕН",
    "FAMILY": "СІМЯ", "FRIEND": "ДРУГ", "MARKET": "РИНОК", "PARTY": "ВЕЧІРКА", "TEAM": "КОМАНДА", "GROUP": "ГРУПА",
    "MONEY": "ГРОШІ", "DOLLAR": "ДОЛАР", "EURO": "ЄВРО", "BANK": "БАНК", "COIN": "МОНЕТА"
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

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center") 
        
        self.title_label = ctk.CTkLabel(self.content_frame, font=("Segoe UI", 32, "bold"))
        self.title_label.pack(pady=30)

        self.category_combobox = ctk.CTkComboBox(
            self.content_frame, 
            width=220, 
            height=45,
            values=self.master_app.get_friendly_categories(),
            command=self._category_selected
        )
        selected_friendly_name = self.master_app.get_friendly_category_name(self.master_app.selected_category)
        self.category_combobox.set(selected_friendly_name)
        self.category_combobox.pack(pady=10)

        self.start_button = ctk.CTkButton(self.content_frame, text="", width=220, height=45, command=self.master_app.show_game)
        self.stats_button = ctk.CTkButton(self.content_frame, text="", width=220, height=45, command=self.master_app.show_stats)
        
        self.author_button = ctk.CTkButton(self.content_frame, text="GitHub / Автор", width=220, height=45, command=self.master_app.open_author_page)
        
        self.exit_button = ctk.CTkButton(self.content_frame, text="", width=220, height=45, command=self.master_app.destroy)

        self.start_button.pack(pady=10)
        self.stats_button.pack(pady=10)
        
        self.author_button.pack(pady=10)
        
        self.exit_button.pack(pady=10)
        
    def _update_combobox_display(self) -> None:
        selected_friendly_name = self.master_app.get_friendly_category_name(
            self.master_app.selected_category
        )
        self.category_combobox.set(selected_friendly_name)

    def _category_selected(self, choice: str) -> None:
        self.master_app.selected_category = choice
        self.after(5, self._update_combobox_display)
        self.master_app.game_frame.refresh_texts()

    def refresh_texts(self) -> None:
        self.title_label.configure(text=self.master_app.t("menu_title"))
        self.category_combobox.configure(values=self.master_app.get_friendly_categories())
        self._update_combobox_display() 
        
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
        
        self.revealed_indices = set()
        self.life_penalty = 0

        self.top_bar = ctk.CTkFrame(self, fg_color="white")
        self.title_label = ctk.CTkLabel(self.top_bar, font=("Segoe UI", 26, "bold"))
      
        self.category_label = ctk.CTkLabel(self.top_bar, font=("Segoe UI", 18, "italic"), text_color="#2c3e50")
        
        self.word_hint_label = ctk.CTkLabel(self.top_bar, font=("Segoe UI", 26, "bold"))
        
        self.top_right_vbox = ctk.CTkFrame(self.top_bar, fg_color="white")
        
        self.language_button = ctk.CTkButton(self.top_right_vbox, width=140, text="", command=lambda: self.master_app.toggle_language())
        self.language_button.pack(side="top", pady=(4, 2))

        self.tools_frame = ctk.CTkFrame(self.top_right_vbox, fg_color="white")
        self.tools_frame.pack(side="top", pady=(2, 4))

        self.music_btn = ctk.CTkButton(
            self.tools_frame, 
            text="🔊", 
            width=40, 
            height=30,
            fg_color="#3498db",
            font=("Segoe UI", 16),
            command=self._on_music_toggle
        )
        self.music_btn.pack(side="left", padx=2)

        self.hint_btn = ctk.CTkButton(
            self.tools_frame,
            text="💡",
            width=40,
            height=30,
            fg_color="#f1c40f",
            hover_color="#f39c12",
            font=("Segoe UI", 16),
            command=self._on_hint_click
        )
        self.hint_btn.pack(side="left", padx=2)

        self.hearts_frame = ctk.CTkFrame(self.top_right_vbox, fg_color="white")
        self.hearts_frame.pack(side="top")

        self.placeholder_row = ctk.CTkFrame(self, fg_color="white")
        self.guess_container = ctk.CTkScrollableFrame(self, fg_color="#f8f8f8")

        self.input_row = ctk.CTkFrame(self, fg_color="white")
        self.entry = ctk.CTkEntry(self.input_row, height=40, font=("Segoe UI", 18))
        self.submit_button = ctk.CTkButton(self.input_row, height=40, command=self._submit_guess)

        self.control_row = ctk.CTkFrame(self, fg_color="white")
        self.restart_button = ctk.CTkButton(self.control_row, width=120, command=self.start_game)
        self.back_button = ctk.CTkButton(self.control_row, width=120, command=self.master_app.show_menu)

        self._build()

    def _on_hint_click(self):
        if self._game_over:
            return

        current_lives = self._get_current_lives()

        if current_lives <= 1:
            messagebox.showwarning("Hint", self.master_app.t("msg_hint_no_lives"))
            return

        secret = self._latest_secret
        if not secret:
            return

        available_indices = [i for i in range(len(secret)) if i not in self.revealed_indices]
        
        if not available_indices:
            messagebox.showinfo("Hint", self.master_app.t("msg_hint_all_revealed"))
            return

        idx_to_reveal = random.choice(available_indices)
        self.revealed_indices.add(idx_to_reveal)
        
        self.life_penalty += 1
        self._update_state()
    
    def _get_current_lives(self):
        try:
            core_lives = int(self.master_app.core.get_lives())
        except Exception:
            core_lives = self.master_app.attempts_per_game
        
        return core_lives - self.life_penalty

    def _on_music_toggle(self):
        is_playing = self.master_app.toggle_music()
        if is_playing:
            self.music_btn.configure(text="🔊", fg_color="#3498db")
        else:
            self.music_btn.configure(text="🔇", fg_color="#95a5a6")

    def _build(self) -> None:
        self.top_bar.pack(fill="x", padx=10, pady=(10, 5))
        self.title_label.pack(side="left")
        self.category_label.pack(side="left", padx=8) 
        self.word_hint_label.pack(side="left", padx=8) 
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
        self.revealed_indices.clear()
        self.life_penalty = 0
        
        selected_category = self.master_app.selected_category 
        try:
            self.master_app.core.start_game(category=selected_category)
        except Exception as exc:
            messagebox.showerror(self.master_app.t("error_title"), str(exc))
            return

        try:
            secret = self.master_app.core.get_secret() or b""
            if isinstance(secret, bytes):
                secret = secret.decode("utf-8")
            
            import re
            secret = re.sub(r'[^A-Z]', '', secret.upper())
            
        except Exception:
            secret = ""

        if self.master_app.language == Language.UK:
            if secret in WORD_TRANSLATIONS_MAP:
                uk_secret = WORD_TRANSLATIONS_MAP[secret]
                
                self.master_app.core._local_secret = uk_secret
                self.master_app.core._use_local_emulation = True
                self.master_app.core._local_attempts = self.master_app.attempts_per_game
                self.master_app.core._local_won = False
                self.master_app.core._local_lost = False
                
                secret = uk_secret

        self._latest_secret = secret
        self.word_length = len(secret) if secret else 5
        self._game_over = False
        self.entry.configure(state="normal")
        self.submit_button.configure(state="normal")
        self.hint_btn.configure(state="normal")
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
        attempts_left = self._get_current_lives()
        
        won = False
        lost = False
        
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

        if attempts_left <= 0 and not won:
            lost = True

        mask_word = "?" * self.word_length
        secret = self._latest_secret
        
        if secret:
            mask_list = []
            for i in range(len(secret)):
                if i in self.revealed_indices:
                    mask_list.append(secret[i])
                else:
                    mask_list.append("?")
            mask_word = "".join(mask_list)

        if won:
            mask_word = secret

        self.word_hint_label.configure(text=self.master_app.t("word_hint", mask=mask_word))
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
        self.hint_btn.configure(state="disabled")

    def _update_placeholder_tiles(self, mask: str) -> None:
        for t in self.placeholder_tiles:
            t.destroy()
        self.placeholder_tiles.clear()
        if not mask:
            return
        for ch in mask:
            text_col = "#2c3e50"
            bg_col = "#ecf0f1"
            if ch != "?":
                bg_col = "#ffeaa7"
            
            tile = ctk.CTkLabel(self.placeholder_row, text=ch, width=48, height=48, corner_radius=6, fg_color=bg_col, text_color=text_col, font=("Consolas", 24, "bold"))
            tile.pack(side="left", padx=4, pady=4)
            self.placeholder_tiles.append(tile)

    def refresh_texts(self) -> None:
        self.title_label.configure(text=self.master_app.t("game_title"))
    
        friendly_category = self.master_app.get_friendly_category_name(self.master_app.selected_category)
        self.category_label.configure(text=f"({friendly_category})")
        
        self.restart_button.configure(text=self.master_app.t("btn_restart"))
        self.back_button.configure(text=self.master_app.t("btn_back"))
        self.submit_button.configure(text=self.master_app.t("btn_submit"))
        self.entry.configure(placeholder_text=self.master_app.t("input_placeholder"))
        lang_text = self.master_app.t("btn_language_to_uk") if self.master_app.language == Language.EN else self.master_app.t("btn_language_to_en")
        self.language_button.configure(text=lang_text)
        if self.word_length > 0:
            self._update_state()


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

        self.is_muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            music_path = self._ui_dir / "music.mp3"
            if music_path.exists():
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
            else:
                print(f"Music file not found at: {music_path}")
        except Exception as e:
            print(f"Music init error: {e}")

        self.available_categories: list[str] = ["ANY"] 
        self._selected_category: str = "ANY"

        try:
            lib_path = self._resolve_library_path()
            words = self.project_root / "words.txt"
            self.core = GameCore(lib_path, words)
            self.available_categories = [c.upper() for c in (self.core.get_categories() or ["ANY"])]
            self._selected_category = self.available_categories[0] 
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load game core: {e}")
            raise

        self.menu_frame = MenuFrame(self)
        self.game_frame = GameFrame(self)
        self.stats_frame = StatsFrame(self)

        self.menu_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self._apply_language()

    def toggle_music(self) -> bool:
        self.is_muted = not self.is_muted
        if self.is_muted:
            pygame.mixer.music.pause()
            return False
        else:
            pygame.mixer.music.unpause()
            return True
           
    def open_author_page(self):
        webbrowser.open("https://github.com/leksahk")    

    def _resolve_library_path(self) -> Path:
        import sys
        
        binary = "game_core.dll" if sys.platform.startswith("win") else ("libgame_core.dylib" if sys.platform == "darwin" else "libgame_core.so")
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

    @property
    def selected_category(self) -> str:
        return self._selected_category

    @selected_category.setter
    def selected_category(self, value: str) -> None:
        key = self.get_category_key(value) 
        if key in self.available_categories:
            self._selected_category = key

    def get_friendly_category_name(self, category_key: str) -> str:
        return CATEGORY_TRANSLATIONS.get(self.language, {}).get(
            category_key, 
            category_key.replace("_", " ").title()
        )

    def get_friendly_categories(self) -> list[str]:
        return [
            self.get_friendly_category_name(key) 
            for key in self.available_categories
        ]

    def get_category_key(self, friendly_name: str) -> str:
        translation_map = CATEGORY_TRANSLATIONS.get(self.language, {})
        
        for key, name in translation_map.items():
            if name == friendly_name:
                return key  
        return friendly_name.replace(" ", "_").upper()


    def show_menu(self) -> None:
        self._show_frame(self.menu_frame)

    def show_game(self) -> None:
        self._show_frame(self.game_frame)
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
    try:
        run_intro()
    except Exception as e:
        print(f"Не вдалося запустити 3D-інтро: {e}")

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = GameApp()
    app.mainloop()


if __name__ == "__main__":
    main()