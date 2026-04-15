"""CheetahType - Clean desktop typing speed test.

Run this file directly on Windows to open a normal GUI window.
No third-party packages are required.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk

COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it", "for", "not", "on", "with",
    "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up",
    "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time",
    "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even",
    "new", "want", "because", "any", "these", "give", "day", "most", "us", "find", "here", "thing",
    "great", "help", "put", "number", "off", "always", "move", "play", "spell", "air", "away",
    "animal", "house", "point", "page", "letter", "mother", "answer", "found", "study", "still",
    "learn", "plant", "cover", "food", "sun", "four", "between", "state", "keep", "eye", "never",
    "last", "let", "thought", "city", "tree", "cross", "farm", "hard", "start", "might", "story",
    "saw", "far", "sea", "draw", "left", "late", "run", "while", "press", "close", "night", "real",
    "life", "few", "north", "open", "seem", "together", "next", "white", "children", "begin",
    "got", "walk", "example", "ease", "paper", "group", "music", "those", "both", "mark", "book",
    "carry", "science", "eat", "room", "friend", "began", "idea", "fish", "mountain", "stop", "once",
    "base", "hear", "horse", "cut", "sure", "watch", "color", "face", "wood", "main", "enough",
    "plain", "girl", "usual", "young", "ready", "above", "ever", "red", "list", "though", "feel",
    "talk", "bird", "soon", "body", "dog", "family", "direct", "pose", "leave", "song",
]

SCORES_FILE = Path.home() / ".typex_scores.json"


@dataclass
class Score:
    wpm: int
    acc: int
    mode: str
    words: int
    ts: float


def load_scores() -> list[Score]:
    if not SCORES_FILE.exists():
        return []
    try:
        raw = json.loads(SCORES_FILE.read_text())
        scores = []
        for item in raw:
            scores.append(
                Score(
                    wpm=int(item.get("wpm", 0)),
                    acc=int(item.get("acc", 0)),
                    mode=str(item.get("mode", "time")),
                    words=int(item.get("words", 0)),
                    ts=float(item.get("ts", time.time())),
                )
            )
        return scores
    except Exception:
        return []


def save_scores(scores: list[Score]) -> None:
    SCORES_FILE.write_text(json.dumps([score.__dict__ for score in scores], indent=2))


def generate_words(word_count: int = 80) -> list[str]:
    pool = COMMON_WORDS.copy()
    random.shuffle(pool)
    return [pool[index % len(pool)] for index in range(word_count)]


def grade(wpm: int, acc: int, wrong_words: int) -> tuple[str, str]:
    # Composite score rewards both speed and accuracy and penalizes frequent mistakes.
    score = (wpm * 0.7) + (acc * 0.5) - (wrong_words * 1.5)

    if score >= 115:
        grade_label = "A+"
    elif score >= 100:
        grade_label = "A"
    elif score >= 88:
        grade_label = "B+"
    elif score >= 75:
        grade_label = "B"
    elif score >= 64:
        grade_label = "C+"
    elif score >= 52:
        grade_label = "C"
    else:
        grade_label = "C"

    if acc < 80:
        feedback = "Accuracy is holding you back. Slow down slightly and focus on clean words."
    elif wrong_words > 18:
        feedback = "You are typing fast, but too many words are missed. Aim for rhythm over rushing."
    elif wpm < 35:
        feedback = "Solid start. Build speed with short daily sessions and keep your fingers relaxed."
    elif wpm < 55:
        feedback = "Good progress. You are close to the next speed tier, keep consistency high."
    elif wpm < 75:
        feedback = "Strong run. Maintain this pace and push for cleaner high-speed bursts."
    else:
        feedback = "Excellent control and speed. Keep challenging yourself with longer sessions."

    return grade_label, feedback


class TypeSpeedChecker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CheetahType - Speed Test")
        self.geometry("1060x680")
        self.minsize(860, 560)
        self.configure(bg="#081018")

        self.mode = "time"
        self.time_limit = 60
        self.time_left = self.time_limit
        self.started = False
        self.finished = False
        self.start_time: float | None = None
        self.timer_job: str | None = None

        self.words: list[str] = []
        self.current_idx = 0
        self.current_input = ""
        self.word_results: dict[int, bool] = {}
        self.correct_words = 0
        self.wrong_words = 0
        self.total_keystrokes = 0
        self.correct_keystrokes = 0
        self.wrong_keystrokes = 0
        self.current_streak = 0
        self.max_streak = 0
        self.scores = load_scores()

        self._build_style()
        self._build_ui()
        self._bind_keys()
        self._reset_round()
        self.bind("<Configure>", self._on_window_resize)
        self.after(100, self.entry.focus_set)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#081018")
        style.configure("Card.TFrame", background="#0d1621", relief="flat")
        style.configure("Header.TLabel", background="#081018", foreground="#9fb7d0", font=("Segoe UI", 11))
        style.configure("Title.TLabel", background="#081018", foreground="#6ee7ff", font=("Segoe UI", 20, "bold"))
        style.configure("StatLabel.TLabel", background="#0d1621", foreground="#9fb7d0", font=("Segoe UI", 10, "bold"))
        style.configure("StatValue.TLabel", background="#0d1621", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("StatUnit.TLabel", background="#0d1621", foreground="#6f859b", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), background="#11c5ff")
        style.map("Accent.TButton", background=[("active", "#31d3ff")])
        style.configure("Ghost.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), background="#172231")
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), background="#3a1720")
        style.configure("TProgressbar", troughcolor="#172231", background="#11c5ff", bordercolor="#172231", lightcolor="#11c5ff", darkcolor="#11c5ff")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        self.typing_screen = ttk.Frame(outer)
        self.result_screen = ttk.Frame(outer)
        self.typing_screen.pack(fill="both", expand=True)

        top = ttk.Frame(self.typing_screen)
        top.pack(fill="x")
        ttk.Label(top, text="CheetahType", style="Title.TLabel").pack(side="left")
        self.session_label = ttk.Label(top, text=self._session_text(), style="Header.TLabel")
        self.session_label.pack(side="right")

        subtitle = ttk.Label(self.typing_screen, text="Speed. Accuracy. Control.", style="Header.TLabel")
        subtitle.pack(anchor="w", pady=(2, 12))

        stats = ttk.Frame(self.typing_screen)
        stats.pack(fill="x", pady=(0, 12))
        self.stat_wpm = self._stat_card(stats, "Speed", "0", self._speed_unit_label())
        self.stat_acc = self._stat_card(stats, "Accuracy", "100", "percent")
        self.stat_time = self._stat_card(stats, "Time", str(self.time_limit), "seconds")
        self.stat_streak = self._stat_card(stats, "Streak", "0", "correct words")
        for card in (self.stat_wpm[0], self.stat_acc[0], self.stat_time[0], self.stat_streak[0]):
            card.pack(side="left", expand=True, fill="x", padx=6)

        controls = ttk.Frame(self.typing_screen)
        controls.pack(fill="x", pady=(0, 12))
        self.mode_buttons: dict[str, ttk.Button] = {}
        self._add_mode_button(controls, "30s", "time-30")
        self._add_mode_button(controls, "60s", "time-60", active=True)
        self._add_mode_button(controls, "120s", "time-120")

        main = ttk.Frame(self.typing_screen)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        board = ttk.Frame(left, style="Card.TFrame", padding=14)
        board.pack(fill="both", expand=True)

        board_top = ttk.Frame(board, style="Card.TFrame")
        board_top.pack(fill="x", pady=(0, 8))
        self.word_count_label = ttk.Label(board_top, text="0 / 0", style="Header.TLabel")
        self.word_count_label.pack(side="right")
        ttk.Label(board_top, text="typing_test.sh - interactive", style="Header.TLabel").pack(side="left")

        self.progress = ttk.Progressbar(board, maximum=100, value=0)
        self.progress.pack(fill="x", pady=(0, 10))

        text_frame = ttk.Frame(board, style="Card.TFrame")
        text_frame.pack(fill="both", expand=True)
        self.display = tk.Text(
            text_frame,
            wrap="word",
            height=12,
            bg="#0d1621",
            fg="#d9e6f2",
            insertbackground="#11c5ff",
            relief="flat",
            padx=18,
            pady=18,
            font=("Consolas", 16),
            borderwidth=0,
        )
        self.display.pack(fill="both", expand=True)
        self.display.configure(state="disabled")

        input_row = ttk.Frame(left)
        input_row.pack(fill="x", pady=(12, 0))
        self.input_var = tk.StringVar()
        self.entry = ttk.Entry(input_row, textvariable=self.input_var, font=("Segoe UI", 14))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.start_button = ttk.Button(input_row, text="START", style="Accent.TButton", command=self.start_test)
        self.start_button.pack(side="left", padx=(10, 0))
        self.restart_button = ttk.Button(input_row, text="RESTART", style="Ghost.TButton", command=self.restart_test)
        self.restart_button.pack(side="left", padx=(10, 0))
        self.reset_button = ttk.Button(input_row, text="RESET", style="Danger.TButton", command=self.reset_test)
        self.reset_button.pack(side="left", padx=(10, 0))

        hints = ttk.Frame(left)
        hints.pack(fill="x", pady=(10, 0))
        ttk.Label(hints, text="SPACE submits a word", style="Header.TLabel").pack(side="left", padx=(0, 18))
        ttk.Label(hints, text="TAB restarts", style="Header.TLabel").pack(side="left", padx=(0, 18))
        ttk.Label(hints, text="ESC resets", style="Header.TLabel").pack(side="left")

        footer = ttk.Frame(self.typing_screen)
        footer.pack(fill="x", pady=(10, 0))
        self.footer_label = ttk.Label(footer, text=self._best_text(), style="Header.TLabel")
        self.footer_label.pack(side="left")
        ttk.Label(footer, text="Clean desktop mode", style="Header.TLabel").pack(side="right")

        self._build_result_screen()

    def _build_result_screen(self) -> None:
        top = ttk.Frame(self.result_screen)
        top.pack(fill="x")
        ttk.Label(top, text="CheetahType", style="Title.TLabel").pack(side="left")
        self.result_session_label = ttk.Label(top, text=self._session_text(), style="Header.TLabel")
        self.result_session_label.pack(side="right")

        subtitle = ttk.Label(self.result_screen, text="Run complete. Review the numbers below.", style="Header.TLabel")
        subtitle.pack(anchor="w", pady=(2, 12))

        hero = ttk.Frame(self.result_screen)
        hero.pack(fill="x", pady=(0, 12))
        self.result_wpm_card = self._result_card(hero, "Speed", "0", "#11c5ff")
        self.result_acc_card = self._result_card(hero, "Accuracy", "100%", "#39ff88")
        self.result_wrong_card = self._result_card(hero, "Wrong Words", "0", "#ff6b6b")
        for card in (self.result_wpm_card[0], self.result_acc_card[0], self.result_wrong_card[0]):
            card.pack(side="left", expand=True, fill="x", padx=6)

        info_row = ttk.Frame(self.result_screen)
        info_row.pack(fill="both", expand=True)
        self.result_info_row = info_row

        left = ttk.Frame(info_row, style="Card.TFrame", padding=14)
        left.pack(side="left", fill="both", expand=True)
        self.result_left_panel = left
        ttk.Label(left, text="Performance", style="Title.TLabel").pack(anchor="w")
        self.result_summary = tk.Text(
            left,
            height=15,
            wrap="word",
            bg="#0d1621",
            fg="#d9e6f2",
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 12),
            borderwidth=0,
        )
        self.result_summary.pack(fill="both", expand=True, pady=(10, 0))
        self.result_summary.configure(state="disabled")

        right = ttk.Frame(info_row, style="Card.TFrame", padding=14)
        right.pack(side="right", fill="y", padx=(12, 0))
        right.pack_propagate(False)
        self.result_right_panel = right
        ttk.Label(right, text="Leaderboard", style="Title.TLabel").pack(anchor="w")
        self.result_leaderboard = tk.Text(
            right,
            width=34,
            height=15,
            wrap="word",
            bg="#0d1621",
            fg="#d9e6f2",
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 11),
            borderwidth=0,
        )
        self.result_leaderboard.pack(fill="both", expand=True, pady=(10, 0))
        self.result_leaderboard.configure(state="disabled")

        actions = ttk.Frame(self.result_screen)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="PLAY AGAIN", style="Accent.TButton", command=self.restart_test).pack(side="left")
        ttk.Button(actions, text="BACK TO TEST", style="Ghost.TButton", command=self.show_typing_screen).pack(side="left", padx=(10, 0))
        ttk.Button(actions, text="RESET", style="Danger.TButton", command=self.reset_test).pack(side="left", padx=(10, 0))

        footer = ttk.Frame(self.result_screen)
        footer.pack(fill="x", pady=(10, 0))
        self.result_footer = ttk.Label(footer, text=self._best_text(), style="Header.TLabel")
        self.result_footer.pack(side="left")
        ttk.Label(footer, text="Clean desktop mode", style="Header.TLabel").pack(side="right")

    def _result_card(self, parent: ttk.Frame, label: str, value: str, color: str):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        ttk.Label(card, text=label.upper(), style="StatLabel.TLabel").pack(anchor="w")
        value_label = ttk.Label(card, text=value, foreground=color, background="#0d1621", font=("Segoe UI", 26, "bold"))
        value_label.pack(anchor="center", pady=(6, 2))
        return card, value_label

    def _stat_card(self, parent: ttk.Frame, label: str, value: str, unit: str):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        ttk.Label(card, text=label.upper(), style="StatLabel.TLabel").pack(anchor="w")
        value_label = ttk.Label(card, text=value, style="StatValue.TLabel")
        value_label.pack(anchor="center", pady=(6, 2))
        ttk.Label(card, text=unit, style="StatUnit.TLabel").pack(anchor="center")
        return card, value_label

    def _add_mode_button(self, parent: ttk.Frame, text: str, mode_key: str, active: bool = False) -> None:
        button = ttk.Button(parent, text=text, style="Accent.TButton" if active else "Ghost.TButton")
        button.pack(side="left", padx=(0, 8))
        button.configure(command=lambda key=mode_key: self.set_mode(key))
        self.mode_buttons[mode_key] = button

    def _bind_keys(self) -> None:
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Tab>", self._on_tab)
        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", lambda event: self.start_test())

    def _on_window_resize(self, event: tk.Event) -> None:
        # Keep the result screen readable on smaller windows by switching to vertical stacking.
        if event.widget is not self:
            return
        self._apply_responsive_layout(event.width)

    def _apply_responsive_layout(self, width: int) -> None:
        if not hasattr(self, "result_left_panel") or not hasattr(self, "result_right_panel"):
            return

        narrow = width < 1120

        self.result_left_panel.pack_forget()
        self.result_right_panel.pack_forget()

        if narrow:
            self.result_left_panel.pack(fill="both", expand=True)
            self.result_right_panel.pack(fill="both", expand=True, pady=(12, 0))
        else:
            self.result_left_panel.pack(side="left", fill="both", expand=True)
            self.result_right_panel.pack(side="right", fill="y", padx=(12, 0))

    def _session_text(self) -> str:
        return f"v3.0 | {len(self.scores)} saved sessions"

    def show_typing_screen(self) -> None:
        self.result_screen.pack_forget()
        self.typing_screen.pack(fill="both", expand=True)
        self.entry.focus_set()

    def show_results_screen(self) -> None:
        self.typing_screen.pack_forget()
        self.result_screen.pack(fill="both", expand=True)
        self.result_session_label.configure(text=self._session_text())
        self.result_footer.configure(text=self._best_text())

    def _best_text(self) -> str:
        if not self.scores:
            return "BEST: -"
        best = max(self.scores, key=lambda score: score.wpm)
        return f"BEST: {best.words} words in {best.mode}"

    def _speed_unit_seconds(self) -> int:
        return self.time_limit if self.mode == "time" else 60

    def _speed_unit_label(self) -> str:
        unit_seconds = self._speed_unit_seconds()
        return "words/min" if unit_seconds == 60 else f"words/{unit_seconds}s"

    def _speed_value(self, word_count: int, elapsed_seconds: float) -> int:
        elapsed_seconds = max(elapsed_seconds, 0.001)
        unit_seconds = self._speed_unit_seconds()
        return int((word_count / elapsed_seconds) * unit_seconds)

    def set_mode(self, mode_key: str) -> None:
        if mode_key == "time-30":
            self.mode = "time"
            self.time_limit = 30
        elif mode_key == "time-60":
            self.mode = "time"
            self.time_limit = 60
        elif mode_key == "time-120":
            self.mode = "time"
            self.time_limit = 120
        else:
            return

        for key, button in self.mode_buttons.items():
            button.configure(style="Accent.TButton" if key == mode_key else "Ghost.TButton")

        self.stat_wpm[0].winfo_children()[2].configure(text=self._speed_unit_label())

        self.restart_test()

    def _reset_round(self) -> None:
        self.words = generate_words(80)
        self.current_idx = 0
        self.current_input = ""
        self.word_results = {}
        self.started = False
        self.finished = False
        self.start_time = None
        self.time_left = self.time_limit
        self.correct_words = 0
        self.wrong_words = 0
        self.total_keystrokes = 0
        self.correct_keystrokes = 0
        self.wrong_keystrokes = 0
        self.current_streak = 0
        self.max_streak = 0
        self.input_var.set("")
        self.entry.configure(state="normal")
        self._render_words(idle=True)
        self._update_stats()
        self._update_results("Ready. Click start or begin typing.")
        self.show_typing_screen()

    def restart_test(self) -> None:
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self._reset_round()
        self.entry.focus_set()

    def reset_test(self) -> None:
        self.mode = "time"
        self.time_limit = 60
        for key, button in self.mode_buttons.items():
            button.configure(style="Accent.TButton" if key == "time-60" else "Ghost.TButton")
        self.restart_test()

    def start_test(self) -> None:
        if self.started or self.finished:
            return
        self.started = True
        self.start_time = time.time()
        if self.mode == "time":
            self.time_left = self.time_limit
            self._tick()
        self._render_words()
        self.entry.focus_set()

    def _tick(self) -> None:
        if self.finished or not self.started:
            return
        self.time_left -= 1
        self._update_stats()
        if self.time_left <= 0:
            self.end_test()
            return
        self.timer_job = self.after(1000, self._tick)

    def _on_tab(self, event: tk.Event) -> str:
        self.restart_test()
        return "break"

    def _on_escape(self, event: tk.Event) -> str:
        self.reset_test()
        return "break"

    def _on_key_release(self, event: tk.Event) -> None:
        if self.finished:
            return

        current = self.input_var.get()
        if not self.started and current:
            self.start_test()

        if not self.started:
            self._render_words(idle=True)
            return

        if current.endswith(" "):
            typed = current.strip()
            self._submit_word(typed)
            self.input_var.set("")
            self.current_input = ""
            self._render_words()
            return

        if len(current) > len(self.current_input):
            added = current[len(self.current_input) :]
            self.total_keystrokes += len(added)
            target = self.words[self.current_idx] if self.current_idx < len(self.words) else ""
            for offset, ch in enumerate(added):
                position = len(self.current_input) + offset
                if position < len(target) and target[position] == ch:
                    self.correct_keystrokes += 1
                else:
                    self.wrong_keystrokes += 1

        self.current_input = current
        self._update_stats()
        self._render_words()

    def _submit_word(self, typed: str) -> None:
        if self.current_idx >= len(self.words):
            return

        target = self.words[self.current_idx]
        is_correct = typed == target
        self.word_results[self.current_idx] = is_correct
        self.total_keystrokes += len(typed) + 1
        if is_correct:
            self.correct_keystrokes += len(typed) + 1
            self.correct_words += 1
            self.current_streak += 1
            self.max_streak = max(self.max_streak, self.current_streak)
        else:
            self.wrong_keystrokes += len(typed) + 1
            self.wrong_words += 1
            self.current_streak = 0

        self.current_idx += 1
        self.current_input = ""
        self._update_stats()

        if self.current_idx >= len(self.words):
            self.current_idx = 0

    def _update_stats(self) -> None:
        elapsed_seconds = (time.time() - self.start_time) if self.start_time else 0.0
        speed = self._speed_value(self.correct_words, elapsed_seconds) if self.started else 0
        acc = int((self.correct_keystrokes / max(self.total_keystrokes, 1)) * 100) if self.total_keystrokes else 100
        progress = int((self.current_idx / max(len(self.words), 1)) * 100)
        if self.mode == "time":
            progress = int(((self.time_limit - self.time_left) / max(self.time_limit, 1)) * 100)

        self.stat_wpm[1].configure(text=str(speed))
        self.stat_acc[1].configure(text=str(acc))
        self.stat_time[1].configure(text=str(max(self.time_left, 0)))
        self.stat_streak[1].configure(text=str(self.current_streak))
        self.word_count_label.configure(text=f"{self.current_idx} / {len(self.words)}")
        self.progress.configure(value=max(0, min(progress, 100)))
        self.footer_label.configure(text=self._best_text())
        self.session_label.configure(text=self._session_text())

    def _render_words(self, idle: bool = False) -> None:
        self.display.configure(state="normal")
        self.display.delete("1.0", "end")
        self.display.tag_configure("idle", foreground="#7aa6c2")
        self.display.tag_configure("past_ok", foreground="#d9e6f2")
        self.display.tag_configure("past_bad", foreground="#ff6b6b")
        self.display.tag_configure("future", foreground="#49637d")
        self.display.tag_configure("current_ok", foreground="#ffffff", font=("Consolas", 16, "bold"))
        self.display.tag_configure("current_bad", foreground="#ff6b6b", underline=True, font=("Consolas", 16, "bold"))
        self.display.tag_configure("current_next", foreground="#081018", background="#11c5ff", font=("Consolas", 16, "bold"))

        if idle:
            self.display.insert("end", "Click start, then begin typing. Space submits the word.\n\n", "idle")
            self.display.insert("end", "TAB to restart, ESC to reset.", "idle")
            self.display.configure(state="disabled")
            return

        visible_start = max(0, self.current_idx - 8)
        visible_end = min(len(self.words), self.current_idx + 28)
        for index in range(visible_start, visible_end):
            word = self.words[index]
            if index < self.current_idx:
                tag = "past_ok" if index in getattr(self, "word_results", {}) and self.word_results[index] else "past_bad"
                self.display.insert("end", word + " ", tag)
                continue
            if index > self.current_idx:
                self.display.insert("end", word + " ", "future")
                continue

            for position, character in enumerate(word):
                if position < len(self.current_input):
                    if self.current_input[position] == character:
                        self.display.insert("end", character, "current_ok")
                    else:
                        self.display.insert("end", character, "current_bad")
                elif position == len(self.current_input):
                    self.display.insert("end", character, "current_next")
                else:
                    self.display.insert("end", character, "future")
            if len(self.current_input) > len(word):
                self.display.insert("end", self.current_input[len(word):], "current_bad")
            self.display.insert("end", " ", "future")

        self.display.configure(state="disabled")

    def end_test(self) -> None:
        if self.finished:
            return
        self.finished = True
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None

        elapsed_seconds = max((time.time() - self.start_time) if self.start_time else 0.001, 0.001)
        elapsed_minutes = elapsed_seconds / 60
        wpm = int(self.correct_words / elapsed_minutes)
        raw_wpm = int((self.correct_words + self.wrong_words) / elapsed_minutes)
        speed = self._speed_value(self.correct_words, elapsed_seconds)
        raw_speed = self._speed_value(self.correct_words + self.wrong_words, elapsed_seconds)
        acc = int((self.correct_keystrokes / max(self.total_keystrokes, 1)) * 100)
        mode_label = f"{self.time_limit}s" if self.mode == "time" else self.mode

        self.scores.insert(0, Score(wpm=wpm, acc=acc, mode=mode_label, words=self.correct_words, ts=time.time()))
        self.scores.sort(key=lambda score: score.wpm, reverse=True)
        self.scores = self.scores[:10]
        save_scores(self.scores)

        title, description = grade(wpm, acc, self.wrong_words)
        leaderboard = []
        for index, score in enumerate(self.scores[:6], start=1):
            stamp = datetime.fromtimestamp(score.ts).strftime("%H:%M")
            leaderboard.append(f"{index}. {score.words:>4} words/{score.mode:<4}  {score.acc:>3}%  {stamp}")

        self._update_results(
            "\n".join([
                f"Finished in {mode_label}",
                "",
                f"Speed ({self._speed_unit_label()}): {speed}",
                f"Accuracy: {acc}%",
                f"Wrong words: {self.wrong_words}",
                f"Raw speed ({self._speed_unit_label()}): {raw_speed}",
                f"Correct words: {self.correct_words}",
                f"Max streak: {self.max_streak}",
                f"Grade: {title}",
                description,
                "",
                "Leaderboard:",
                *leaderboard,
                "",
                "Press PLAY AGAIN to try again.",
            ])
        )
        self._update_result_screen(speed, acc, raw_speed, mode_label, title, description, leaderboard)
        self.show_results_screen()
        self._render_words()
        self.entry.configure(state="disabled")
        self._update_stats()

    def _update_results(self, text: str) -> None:
        self.result_summary.configure(state="normal")
        self.result_summary.delete("1.0", "end")
        self.result_summary.insert("end", text)
        self.result_summary.configure(state="disabled")

    def _update_result_screen(
        self,
        speed: int,
        acc: int,
        raw_speed: int,
        mode_label: str,
        title: str,
        description: str,
        leaderboard: list[str],
    ) -> None:
        self.result_wpm_card[1].configure(text=str(speed))
        self.result_acc_card[1].configure(text=f"{acc}%")
        self.result_wrong_card[1].configure(text=str(self.wrong_words))

        summary = "\n".join([
            f"Mode: {mode_label}",
            "",
            f"Speed ({self._speed_unit_label()}): {speed}",
            f"Accuracy: {acc}%",
            f"Wrong words: {self.wrong_words}",
            f"Correct words: {self.correct_words}",
            f"Raw speed ({self._speed_unit_label()}): {raw_speed}",
            f"Max streak: {self.max_streak}",
            "",
            f"Grade: {title}",
            description,
            "",
            "Tip: Keep accuracy high first. Speed follows.",
        ])
        self.result_summary.configure(state="normal")
        self.result_summary.delete("1.0", "end")
        self.result_summary.insert("end", summary)
        self.result_summary.configure(state="disabled")

        leaderboard_text = "\n".join(["Top scores", "", *leaderboard])
        self.result_leaderboard.configure(state="normal")
        self.result_leaderboard.delete("1.0", "end")
        self.result_leaderboard.insert("end", leaderboard_text)
        self.result_leaderboard.configure(state="disabled")


def main() -> None:
    app = TypeSpeedChecker()
    app.mainloop()


if __name__ == "__main__":
    main()
