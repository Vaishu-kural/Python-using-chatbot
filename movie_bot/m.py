import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import tempfile
from datetime import datetime, timedelta
import re
import random
import threading
from collections import defaultdict
import queue


def safe_read_json(filepath, default=None):
    if default is None:
        default = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def safe_write_json(filepath, data):
    directory = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


class AutomatedMovieChatbot:
    def __init__(self):
        self.movies_file = "movies.json"
        self.bookings_file = "bookings.json"
        self.preferences_file = "preferences.json"

        self.current_user = "guest"
        self.conversation_history = []
        self.context = defaultdict(lambda: None)
        self.user_preferences = {
            "genre": None,
            "time_preference": "evening",
            "theater_preference": None,
            "seat_type": "Standard",
            "favorite_movies": [],
        }

        self.automation_active = True
        self.suggestions_queue = queue.Queue()

        self._reset_booking_flow()

        self.ticket_price = 12.50
        self.vip_upcharge = 5.00
        self.tax_rate = 0.08

        self.initialize_data()
        self.load_user_preferences()

        self.create_gui()
        self.start_automation()
        self.root.after(1000, self.auto_greeting)

    # ── Booking flow reset ─────────────────────────────────────────────────
    def _reset_booking_flow(self):
        self.booking_flow = {
            "step": 0,
            "movie": None,
            "date": None,
            "time": None,
            "tickets": 1,
            "theater": None,
            "seat_type": "Standard",
        }

    # ── Hover helper (FIX: was missing entirely) ───────────────────────────
    def _make_hover(self, widget, bg_normal, bg_hover,
                    fg_normal=None, fg_hover=None):
        """
        Bind <Enter>/<Leave> events so a button changes colour on hover.
        fg_normal / fg_hover are optional — if omitted, foreground is unchanged.
        """
        def on_enter(e):
            widget.config(background=bg_hover)
            if fg_hover:
                widget.config(foreground=fg_hover)

        def on_leave(e):
            widget.config(background=bg_normal)
            if fg_normal:
                widget.config(foreground=fg_normal)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # ── Data initialisation ────────────────────────────────────────────────
    def initialize_data(self):
        if not os.path.exists(self.movies_file):
            movies_data = {
                "movies": [
                    {
                        "id": 1,
                        "title": "The Last Adventure",
                        "genre": "Action/Adventure",
                        "duration": "2h 15m",
                        "rating": "PG-13",
                        "description": "An epic journey through uncharted territories.",
                        "director": "Alex Rivera",
                        "cast": ["Chris Evans", "Zendaya", "Idris Elba"],
                        "imdb": 7.8,
                        "popularity": 95,
                        "showtimes": ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"],
                    },
                    {
                        "id": 2,
                        "title": "Cosmic Dreams",
                        "genre": "Sci-Fi",
                        "duration": "2h 30m",
                        "rating": "PG",
                        "description": "A mind-bending journey through space and time.",
                        "director": "Lisa Chen",
                        "cast": ["Tom Hanks", "Millie Bobby Brown", "Keanu Reeves"],
                        "imdb": 8.2,
                        "popularity": 98,
                        "showtimes": ["11:00 AM", "2:30 PM", "5:00 PM", "8:30 PM"],
                    },
                    {
                        "id": 3,
                        "title": "Heartstrings",
                        "genre": "Romance/Drama",
                        "duration": "1h 50m",
                        "rating": "PG-13",
                        "description": "A love story that transcends time.",
                        "director": "Sophia Lee",
                        "cast": ["Emma Stone", "Timothée Chalamet", "Viola Davis"],
                        "imdb": 7.5,
                        "popularity": 88,
                        "showtimes": ["12:00 PM", "3:30 PM", "7:00 PM", "10:00 PM"],
                    },
                    {
                        "id": 4,
                        "title": "Midnight Mystery",
                        "genre": "Thriller/Mystery",
                        "duration": "2h 5m",
                        "rating": "R",
                        "description": "A detective races against time to solve a century-old mystery.",
                        "director": "James Nolan",
                        "cast": ["Daniel Craig", "Ana de Armas", "Anthony Hopkins"],
                        "imdb": 8.0,
                        "popularity": 92,
                        "showtimes": ["1:00 PM", "4:30 PM", "9:00 PM"],
                    },
                    {
                        "id": 5,
                        "title": "Laugh Out Loud",
                        "genre": "Comedy",
                        "duration": "1h 45m",
                        "rating": "PG",
                        "description": "The funniest movie of the year!",
                        "director": "Kevin Hart",
                        "cast": ["Ryan Reynolds", "Tiffany Haddish", "Jack Black"],
                        "imdb": 6.9,
                        "popularity": 85,
                        "showtimes": ["10:30 AM", "2:00 PM", "5:30 PM", "9:30 PM"],
                    },
                ],
                "theaters": [
                    {"id": 1, "name": "City Center Cinemas", "location": "Downtown", "vip": True, "popularity": 95},
                    {"id": 2, "name": "Starlight Theater", "location": "Westside Mall", "vip": True, "popularity": 88},
                    {"id": 3, "name": "Grand Arena", "location": "Eastgate Complex", "vip": False, "popularity": 82},
                    {"id": 4, "name": "Royal IMAX", "location": "North Plaza", "vip": True, "popularity": 92},
                ],
            }
            safe_write_json(self.movies_file, movies_data)

        bdata = safe_read_json(self.bookings_file, None)
        if bdata is None or not isinstance(bdata.get("bookings"), list):
            safe_write_json(self.bookings_file, {"bookings": []})

        pdata = safe_read_json(self.preferences_file, None)
        if pdata is None or not isinstance(pdata.get("preferences"), dict):
            safe_write_json(self.preferences_file, {"preferences": {}})

    def load_user_preferences(self):
        data = safe_read_json(self.preferences_file, {"preferences": {}})
        if self.current_user in data.get("preferences", {}):
            self.user_preferences = data["preferences"][self.current_user]

    def save_user_preferences(self):
        data = safe_read_json(self.preferences_file, {"preferences": {}})
        data["preferences"][self.current_user] = self.user_preferences
        try:
            safe_write_json(self.preferences_file, data)
        except Exception:
            pass

    # ── GUI ────────────────────────────────────────────────────────────────
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("🎬 CineBook — AI Movie Assistant")
        self.root.geometry("1280x860")
        self.root.configure(bg="#0a0a0f")
        self.root.resizable(True, True)
        self.root.minsize(900, 600)

        self.C = {
            "bg_deep":    "#0a0a0f",
            "bg_panel":   "#0f0f18",
            "bg_card":    "#141420",
            "bg_input":   "#1a1a28",
            "bg_hover":   "#1e1e30",
            "gold":       "#e8b84b",
            "gold_dim":   "#a07828",
            "gold_glow":  "#f5d080",
            "crimson":    "#c0392b",
            "crimson_h":  "#e74c3c",
            "teal":       "#1abc9c",
            "text_hi":    "#f0e6c8",
            "text_mid":   "#9a8f78",
            "text_dim":   "#4a4535",
            "border":     "#2a2535",
            "border_gold":"#3a3020",
            "bot_name":   "#e8b84b",
            "user_name":  "#5dade2",
            "bot_msg":    "#d4c9a8",
            "user_msg":   "#c8dff0",
        }
        C = self.C

        style = ttk.Style()
        style.theme_use("clam")
        for widget in ("TCombobox", "TEntry"):
            style.configure(widget,
                fieldbackground=C["bg_input"],
                background=C["bg_input"],
                foreground=C["text_hi"],
                bordercolor=C["border_gold"],
                lightcolor=C["bg_input"],
                darkcolor=C["bg_input"],
                selectbackground=C["gold_dim"],
                selectforeground=C["text_hi"],
                arrowcolor=C["gold"],
                insertcolor=C["gold"],
            )
            style.map(widget,
                fieldbackground=[("readonly", C["bg_input"]), ("focus", C["bg_hover"])],
                bordercolor=[("focus", C["gold"])],
            )
        style.configure("TSeparator", background=C["border_gold"])
        style.configure("TScrollbar",
            background=C["bg_card"],
            troughcolor=C["bg_panel"],
            arrowcolor=C["gold_dim"],
            bordercolor=C["bg_panel"],
        )

        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

        self.chat_display.tag_config("user_tag",
            foreground=C["user_name"], font=("Georgia", 9, "italic"))
        self.chat_display.tag_config("user_msg",
            foreground=C["user_msg"], lmargin1=12, lmargin2=12)
        self.chat_display.tag_config("bot_tag",
            foreground=C["bot_name"], font=("Georgia", 9, "italic"))
        self.chat_display.tag_config("bot_msg",
            foreground=C["bot_msg"], lmargin1=12, lmargin2=12)
        self.chat_display.tag_config("error_tag",
            foreground="#e74c3c", lmargin1=12, lmargin2=12)
        self.chat_display.tag_config("divider",
            foreground=C["text_dim"])

        self._dot_state = 0
        self._animate_status_dot()

    def _animate_status_dot(self):
        """Pulse the status dot between bright and dim."""
        colours = [self.C["teal"], self.C["gold_dim"]]
        self._dot_state = (self._dot_state + 1) % 2
        if self.automation_active:
            self._status_dot_label.config(fg=colours[self._dot_state])
        self.root.after(900, self._animate_status_dot)

    def _random_suggestion(self):
        suggestions = [
            "🎬 Cosmic Dreams is trending — book before it sells out!",
            "⭐ Midnight Mystery has a 8.0 rating — highly recommended!",
            "🍿 Friday evening shows fill up fast — book early!",
            "💺 VIP seats for The Last Adventure still available.",
            "📅 Weekend slots are going fast — grab yours now!",
            "🎭 New this week: Heartstrings — a must-watch romance.",
        ]
        return random.choice(suggestions)

    def _build_left_panel(self):
        C = self.C
        left = tk.Frame(self.root, bg=C["bg_panel"], bd=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(left, bg=C["bg_deep"], height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        tk.Frame(header, bg=C["gold"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(header, text="  CINEBOOK",
                 font=("Georgia", 18, "bold"),
                 bg=C["bg_deep"], fg=C["gold"]).pack(side=tk.LEFT, pady=10)
        tk.Label(header, text="  AI CONCIERGE",
                 font=("Georgia", 9),
                 bg=C["bg_deep"], fg=C["text_mid"]).pack(side=tk.LEFT, pady=16)

        dot_frame = tk.Frame(header, bg=C["bg_deep"])
        dot_frame.pack(side=tk.RIGHT, padx=16)
        self._status_dot_label = tk.Label(dot_frame, text="●",
            font=("Courier", 10), bg=C["bg_deep"], fg=C["teal"])
        self._status_dot_label.pack(side=tk.LEFT)
        self.automation_status = tk.Label(dot_frame, text=" LIVE",
            font=("Courier", 9, "bold"), bg=C["bg_deep"], fg=C["teal"])
        self.automation_status.pack(side=tk.LEFT)

        # Chat area
        chat_frame = tk.Frame(left, bg=C["bg_deep"], bd=0)
        chat_frame.grid(row=1, column=0, sticky="nsew")
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = tk.Text(
            chat_frame,
            font=("Georgia", 11),
            bg=C["bg_deep"], fg=C["text_hi"],
            wrap=tk.WORD, relief=tk.FLAT, bd=0,
            padx=18, pady=14,
            state=tk.DISABLED, cursor="arrow",
            selectbackground=C["gold_dim"],
            selectforeground=C["text_hi"],
            spacing1=4, spacing3=4,
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL,
                                   command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.config(yscrollcommand=scrollbar.set)

        # Thinking indicator
        self.thinking_indicator = tk.Label(
            left, text="",
            font=("Georgia", 9, "italic"),
            bg=C["bg_panel"], fg=C["gold_dim"])
        self.thinking_indicator.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 0))

        # Suggestion ticker
        sug_frame = tk.Frame(left, bg=C["bg_card"], height=34)
        sug_frame.grid(row=3, column=0, sticky="ew")
        sug_frame.grid_propagate(False)
        tk.Frame(sug_frame, bg=C["gold"], width=3).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(sug_frame, text="  ✦  ",
                 font=("Georgia", 9), bg=C["bg_card"], fg=C["gold"]).pack(side=tk.LEFT)
        self.suggestions_text = tk.Label(
            sug_frame, text="Analysing your preferences...",
            font=("Georgia", 9, "italic"),
            bg=C["bg_card"], fg=C["text_mid"], anchor="w")
        self.suggestions_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # Toolbar
        toolbar = tk.Frame(left, bg=C["bg_panel"])
        toolbar.grid(row=4, column=0, sticky="ew", padx=8, pady=(6, 2))
        actions = [
            ("🚀 Auto-Book",  lambda: self.auto_book_movie(),    C["gold_dim"],  C["gold"]),
            ("⭐ Suggest",     lambda: self.smart_suggestions(),  C["gold_dim"],  C["gold"]),
            ("📅 Schedule",    lambda: self.auto_schedule(),      C["gold_dim"],  C["gold"]),
            ("⚡ Quick Fill",  lambda: self.quick_fill_booking(), C["crimson"],   C["crimson_h"]),
            ("🔄 Prefs",      lambda: self.learn_preferences(),  C["bg_card"],   C["bg_hover"]),
        ]
        for text, cmd, bg, hbg in actions:
            b = tk.Button(toolbar, text=text, command=cmd,
                          bg=bg, fg=C["text_hi"],
                          font=("Georgia", 9), relief=tk.FLAT,
                          cursor="hand2", padx=9, pady=5, bd=0,
                          activebackground=hbg, activeforeground=C["text_hi"])
            b.pack(side=tk.LEFT, padx=2)
            self._make_hover(b, bg, hbg)

        # Input row
        input_outer = tk.Frame(left, bg=C["bg_card"])
        input_outer.grid(row=5, column=0, sticky="ew")
        input_outer.grid_columnconfigure(0, weight=1)
        tk.Frame(input_outer, bg=C["gold"], height=2).grid(
            row=0, column=0, columnspan=2, sticky="ew")
        self.user_input = tk.Entry(
            input_outer,
            font=("Georgia", 12),
            bg=C["bg_card"], fg=C["text_hi"],
            insertbackground=C["gold"],
            relief=tk.FLAT, bd=0)
        self.user_input.grid(row=1, column=0, sticky="ew", padx=(18, 4), ipady=11)
        self.user_input.bind("<Return>", lambda e: self.process_input())

        send_btn = tk.Button(
            input_outer, text="SEND ▶",
            command=self.process_input,
            bg=C["gold"], fg=C["bg_deep"],
            font=("Georgia", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            activebackground=C["gold_glow"],
            activeforeground=C["bg_deep"],
            bd=0, padx=20)
        send_btn.grid(row=1, column=1, sticky="ns")
        self._make_hover(send_btn, C["gold"], C["gold_glow"], C["bg_deep"], C["bg_deep"])

    def _build_right_panel(self):
        C = self.C
        right = tk.Frame(self.root, bg=C["bg_panel"], bd=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        rh = tk.Frame(right, bg=C["bg_deep"], height=56)
        rh.pack(fill=tk.X)
        rh.pack_propagate(False)
        tk.Frame(rh, bg=C["crimson"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(rh, text="  BOOKING PANEL",
                 font=("Georgia", 12, "bold"),
                 bg=C["bg_deep"], fg=C["text_hi"]).pack(side=tk.LEFT, pady=10)

        ctrl = tk.Frame(right, bg=C["bg_panel"])
        ctrl.pack(fill=tk.X, padx=10, pady=(10, 4))
        self.auto_toggle_btn = tk.Button(
            ctrl, text="● AUTO-MODE: ON",
            command=self.toggle_automation,
            bg=C["teal"], fg=C["bg_deep"],
            font=("Courier", 9, "bold"),
            relief=tk.FLAT, cursor="hand2",
            activebackground="#16a085",
            activeforeground=C["bg_deep"],
            bd=0, pady=6)
        self.auto_toggle_btn.pack(fill=tk.X)
        self._make_hover(self.auto_toggle_btn, C["teal"], "#16a085", C["bg_deep"], C["bg_deep"])

        prog_card = tk.Frame(right, bg=C["bg_card"],
                              highlightbackground=C["border_gold"],
                              highlightthickness=1)
        prog_card.pack(fill=tk.X, padx=10, pady=(0, 6))
        tk.Frame(prog_card, bg=C["gold"], height=2).pack(fill=tk.X)
        self.booking_status = tk.Label(
            prog_card,
            text="  No active booking",
            font=("Courier", 9),
            bg=C["bg_card"], fg=C["text_mid"],
            justify=tk.LEFT, wraplength=230, anchor="w")
        self.booking_status.pack(fill=tk.X, padx=10, pady=8)

        div = tk.Frame(right, bg=C["bg_panel"])
        div.pack(fill=tk.X, padx=10, pady=4)
        tk.Frame(div, bg=C["border_gold"], height=1).pack(fill=tk.X)
        tk.Label(div, text="⬡  QUICK BOOKING",
                 font=("Georgia", 10, "bold"),
                 bg=C["bg_panel"], fg=C["gold"]).pack(anchor=tk.W, pady=(6, 0))

        form = tk.Frame(right, bg=C["bg_panel"])
        form.pack(fill=tk.X, padx=10)

        def flabel(text):
            tk.Label(form, text=text,
                     font=("Courier", 8),
                     bg=C["bg_panel"], fg=C["text_mid"]).pack(anchor=tk.W, pady=(8, 1))

        flabel("▸ FILM")
        self.quick_movie_var = tk.StringVar()
        self.quick_movie_combo = ttk.Combobox(form, textvariable=self.quick_movie_var,
                                               state="readonly", font=("Georgia", 10))
        self.quick_movie_combo.pack(fill=tk.X)
        self.quick_movie_combo.bind("<<ComboboxSelected>>",
                                    lambda e: self._combo_select_movie())

        flabel("▸ DATE")
        self.quick_date_var = tk.StringVar()
        self.quick_date_combo = ttk.Combobox(form, textvariable=self.quick_date_var,
                                              state="readonly", font=("Georgia", 10))
        self.quick_date_combo.pack(fill=tk.X)
        self.quick_date_combo.bind("<<ComboboxSelected>>",
                                   lambda e: self._combo_select_date())

        flabel("▸ SHOWTIME")
        self.quick_time_var = tk.StringVar()
        self.quick_time_combo = ttk.Combobox(form, textvariable=self.quick_time_var,
                                              state="readonly", font=("Georgia", 10))
        self.quick_time_combo.pack(fill=tk.X)
        self.quick_time_combo.bind("<<ComboboxSelected>>",
                                   lambda e: self._combo_select_time())

        flabel("▸ THEATER")
        self.quick_theater_var = tk.StringVar()
        self.quick_theater_combo = ttk.Combobox(form, textvariable=self.quick_theater_var,
                                                 state="readonly", font=("Georgia", 10))
        self.quick_theater_combo.pack(fill=tk.X)
        self.quick_theater_combo.bind("<<ComboboxSelected>>",
                                      lambda e: self._combo_select_theater())

        mid_row = tk.Frame(form, bg=C["bg_panel"])
        mid_row.pack(fill=tk.X, pady=(8, 0))

        tickets_col = tk.Frame(mid_row, bg=C["bg_panel"])
        tickets_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(tickets_col, text="▸ TICKETS",
                 font=("Courier", 8), bg=C["bg_panel"], fg=C["text_mid"]).pack(anchor=tk.W)
        self.quick_tickets_var = tk.StringVar(value="1")
        tk.Spinbox(tickets_col,
                   from_=1, to=10, textvariable=self.quick_tickets_var,
                   font=("Georgia", 11),
                   bg=C["bg_input"], fg=C["gold"],
                   buttonbackground=C["bg_card"],
                   insertbackground=C["gold"],
                   relief=tk.FLAT, bd=1, width=5).pack(anchor=tk.W)

        seat_col = tk.Frame(mid_row, bg=C["bg_panel"])
        seat_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        tk.Label(seat_col, text="▸ SEAT",
                 font=("Courier", 8), bg=C["bg_panel"], fg=C["text_mid"]).pack(anchor=tk.W)
        self.quick_seat_var = tk.StringVar(value="Standard")
        for seat in ("Standard", "VIP"):
            tk.Radiobutton(seat_col, text=seat,
                           variable=self.quick_seat_var, value=seat,
                           font=("Georgia", 9),
                           bg=C["bg_panel"], fg=C["text_hi"],
                           selectcolor=C["bg_deep"],
                           activebackground=C["bg_panel"],
                           activeforeground=C["gold"]).pack(anchor=tk.W)

        btns = tk.Frame(right, bg=C["bg_panel"])
        btns.pack(fill=tk.X, padx=10, pady=(12, 4))

        book_btn = tk.Button(
            btns, text="  🎫  BOOK TICKETS  ",
            command=self.quick_book_tickets,
            bg=C["crimson"], fg=C["text_hi"],
            font=("Georgia", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            activebackground=C["crimson_h"],
            activeforeground=C["text_hi"],
            bd=0, pady=9)
        book_btn.pack(fill=tk.X, pady=(0, 4))
        self._make_hover(book_btn, C["crimson"], C["crimson_h"])

        view_btn = tk.Button(
            btns, text="📋  MY BOOKINGS",
            command=self._view_bookings_to_chat,
            bg=C["bg_card"], fg=C["gold"],
            font=("Georgia", 10),
            relief=tk.FLAT, cursor="hand2",
            activebackground=C["bg_hover"],
            activeforeground=C["gold_glow"],
            bd=1, pady=7,
            highlightbackground=C["border_gold"],
            highlightthickness=1)
        view_btn.pack(fill=tk.X)
        self._make_hover(view_btn, C["bg_card"], C["bg_hover"], C["gold"], C["gold_glow"])

        self.update_quick_form()

    # ── Background threads ─────────────────────────────────────────────────
    def start_automation(self):
        threading.Thread(target=self._suggestion_loop, daemon=True).start()
        threading.Thread(target=self._status_loop, daemon=True).start()

    def _suggestion_loop(self):
        import time
        while True:
            time.sleep(12)
            if self.automation_active:
                self.suggestions_queue.put(self._random_suggestion())

    def _status_loop(self):
        import time
        while True:
            time.sleep(4)
            self.root.after(0, self._refresh_ui)

    def _refresh_ui(self):
        try:
            while not self.suggestions_queue.empty():
                msg = self.suggestions_queue.get_nowait()
                self.suggestions_text.config(text=msg)
        except queue.Empty:
            pass

        bf = self.booking_flow
        if bf["step"] > 0:
            lines = [f"📝 Booking in progress (Step {bf['step']}/5)"]
            if bf["movie"]:
                lines.append(f"🎬 {bf['movie']}")
            if bf["date"]:
                lines.append(f"📅 {bf['date']}")
            if bf["time"]:
                lines.append(f"🕐 {bf['time']}")
            self.booking_status.config(text="\n".join(lines), fg=self.C["gold"])
        else:
            self.booking_status.config(text="  No active booking", fg=self.C["text_mid"])

    # ── Quick form ─────────────────────────────────────────────────────────
    def update_quick_form(self):
        data = safe_read_json(self.movies_file, {"movies": [], "theaters": []})
        movies = data.get("movies", [])
        theaters = data.get("theaters", [])

        self.quick_movie_combo["values"] = [m["title"] for m in movies]

        today = datetime.now()
        dates = []
        for i in range(7):
            d = today + timedelta(days=i)
            label = "(Today)" if i == 0 else "(Tomorrow)" if i == 1 else f"({d.strftime('%A')})"
            dates.append(f"{d.strftime('%Y-%m-%d')} {label}")
        self.quick_date_combo["values"] = dates

        all_times = sorted({t for m in movies for t in m.get("showtimes", [])})
        self.quick_time_combo["values"] = all_times or ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
        self.quick_theater_combo["values"] = [t["name"] for t in theaters]

    # ── Combobox handlers ──────────────────────────────────────────────────
    def _combo_select_movie(self):
        movie = self.quick_movie_var.get()
        if not movie:
            return
        if self.booking_flow["step"] == 0:
            self._reset_booking_flow()
            self.booking_flow["step"] = 1
            self.booking_flow["movie"] = movie
            info = self._get_movie_info(movie)
            genre = info.get("genre", "") if info else ""
            rating = info.get("rating", "") if info else ""
            duration = info.get("duration", "") if info else ""
            self.add_message(
                f"🎬 Selected: **{movie}**\n"
                f"{genre} | {rating} | {duration}\n\n"
                "📅 Now pick a **Date** from the dropdown, or type it in chat.",
                "bot"
            )
        elif self.booking_flow["step"] >= 1:
            self.booking_flow["movie"] = movie
            self.add_message(f"🎬 Movie updated to **{movie}**.", "bot")

    def _combo_select_date(self):
        raw = self.quick_date_var.get()
        if not raw:
            return
        if not self.booking_flow["movie"]:
            movie = self.quick_movie_var.get()
            if not movie:
                self.add_message("⚠️ Please select a Movie first.", "bot")
                return
            self._reset_booking_flow()
            self.booking_flow["step"] = 1
            self.booking_flow["movie"] = movie

        m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
        date_str = m.group(1) if m else raw
        self.booking_flow["date"] = date_str
        if self.booking_flow["step"] <= 1:
            self.booking_flow["step"] = 2

        info = self._get_movie_info(self.booking_flow["movie"])
        times = info.get("showtimes", []) if info else []
        times_str = "  " + "  |  ".join(times) if times else ""
        self.add_message(
            f"📅 Date set to **{date_str}**.\n\n"
            f"🕐 Pick a **Showtime** from the dropdown.{chr(10) + times_str if times_str else ''}",
            "bot"
        )

    def _combo_select_time(self):
        showtime = self.quick_time_var.get()
        if not showtime:
            return
        if not self.booking_flow["date"]:
            self.add_message("⚠️ Please select a Date first.", "bot")
            return
        self.booking_flow["time"] = showtime
        if self.booking_flow["step"] <= 2:
            self.booking_flow["step"] = 3
        self.add_message(
            f"🕐 Showtime set to **{showtime}**.\n\n"
            "🎫 Set **Tickets** using the spinner, then pick a **Theater**.",
            "bot"
        )

    def _combo_select_theater(self):
        theater = self.quick_theater_var.get()
        if not theater:
            return
        if not self.booking_flow["time"]:
            self.add_message("⚠️ Please select a Showtime first.", "bot")
            return
        self.booking_flow["theater"] = theater
        try:
            self.booking_flow["tickets"] = int(self.quick_tickets_var.get())
        except Exception:
            self.booking_flow["tickets"] = 1
        self.booking_flow["seat_type"] = self.quick_seat_var.get() or "Standard"
        self.booking_flow["step"] = 5
        summary = self.generate_booking_summary()
        self.add_message(
            f"🏢 Theater set to **{theater}**.\n\n"
            f"{summary}\n\n"
            "Type **confirm** to book, or **cancel** to start over.",
            "bot"
        )

    # ── Inline option buttons ──────────────────────────────────────────────
    def _add_option_buttons(self, options, callback):
        self.chat_display.config(state=tk.NORMAL)
        btn_frame = tk.Frame(self.chat_display, bg=self.C["bg_card"])

        def make_handler(opt, frame):
            def handler():
                frame.destroy()
                callback(opt)
            return handler

        for opt in options:
            btn = tk.Button(
                btn_frame, text=opt,
                command=make_handler(opt, btn_frame),
                bg=self.C["gold_dim"], fg="#ffffff",
                font=("Georgia", 9), relief=tk.FLAT,
                cursor="hand2", padx=6, pady=3,
            )
            btn.pack(side=tk.LEFT, padx=3, pady=4)

        self.chat_display.window_create(tk.END, window=btn_frame)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    # ── Greeting ───────────────────────────────────────────────────────────
    def auto_greeting(self):
        h = datetime.now().hour
        tod = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        msg = (
            f"Good {tod}! I'm your AI Movie Assistant 🎬\n\n"
            "I can:\n"
            "• Book movie tickets 🎫\n"
            "• Show what's playing 🎬\n"
            "• Manage your bookings 📋\n"
            "• Give personalised recommendations ⭐\n\n"
            "Type 'help' for all commands, or just tell me what you'd like to do!"
        )
        self.add_message(msg, "bot")

    # ── Input processing ───────────────────────────────────────────────────
    def process_input(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        self.user_input.delete(0, tk.END)
        self.add_message(user_text, "user")
        self.learn_from_input(user_text)
        self.thinking_indicator.config(text="🤖 Thinking...")
        self.root.after(300, lambda: self._deliver_response(user_text))

    def _deliver_response(self, user_text):
        response = self.understand_and_respond(user_text)
        if response:
            self.add_message(response, "bot")
        self.thinking_indicator.config(text="")

    # ── Preference learning ────────────────────────────────────────────────
    def learn_from_input(self, text):
        t = text.lower()
        for genre in ["action", "comedy", "drama", "sci-fi", "thriller", "romance", "mystery"]:
            if genre in t:
                self.user_preferences["genre"] = genre.capitalize()
        if "morning" in t:
            self.user_preferences["time_preference"] = "morning"
        elif "afternoon" in t:
            self.user_preferences["time_preference"] = "afternoon"
        elif "evening" in t or "night" in t:
            self.user_preferences["time_preference"] = "evening"
        self.save_user_preferences()

    # ── Intent router ──────────────────────────────────────────────────────
    def understand_and_respond(self, message):
        ml = message.lower()

        if self.booking_flow["step"] > 0:
            if any(w in ml for w in ["cancel", "stop", "quit", "restart", "start over"]):
                self._reset_booking_flow()
                return "Booking cancelled. What else can I help you with? 😊"
            if ml.strip() in ["help", "?"]:
                return self.handle_help()
            return self.handle_booking_flow_response(message)

        if any(w in ml for w in ["hello", "hi", "hey", "greet"]):
            return "Hello! 👋 How can I help you with movies today?"
        if any(w in ml for w in ["book", "ticket", "reserve", "buy"]):
            return self.handle_book_ticket(message)
        if any(w in ml for w in ["show", "movie", "available", "playing", "list"]):
            return self.handle_show_movies()
        if any(w in ml for w in ["my booking", "view booking", "bookings", "history"]):
            return self.view_my_bookings()
        if any(w in ml for w in ["cancel", "delete", "remove"]):
            return self.handle_cancel_booking(message)
        if any(w in ml for w in ["price", "cost", "how much", "fee"]):
            return self.handle_price_query()
        if any(w in ml for w in ["recommend", "suggestion", "best", "popular"]):
            return self.handle_recommendation()
        if any(w in ml for w in ["help", "what can you", "commands", "?"]):
            return self.handle_help()
        if any(w in ml for w in ["thank", "thanks", "cheers"]):
            return random.choice([
                "You're welcome! 😊",
                "Happy to help! 🎬",
                "My pleasure — enjoy the movie! 🍿",
            ])
        return (
            "I didn't quite catch that 🤔\n"
            "Try: 'show movies', 'book tickets', 'view bookings', or 'help'."
        )

    # ── Booking handlers ───────────────────────────────────────────────────
    def handle_book_ticket(self, message):
        movie_title = self.extract_movie_title(message)

        if self.booking_flow["step"] > 0 and movie_title and movie_title != self.booking_flow.get("movie"):
            self._reset_booking_flow()
            self.add_message("⚠️ Previous booking cleared. Starting a new one...", "bot")

        if not movie_title:
            data = self._load_movies_data()
            titles = [m["title"] for m in data.get("movies", [])]
            self.add_message("🎬 Which movie would you like to book?", "bot")
            self._add_option_buttons(titles, lambda t: self._deliver_response(f"book {t}"))
            return ""

        self._reset_booking_flow()
        self.booking_flow["step"] = 1
        self.booking_flow["movie"] = movie_title
        self.quick_movie_var.set(movie_title)

        info = self._get_movie_info(movie_title)
        detail = ""
        if info:
            detail = (f"Genre: {info.get('genre')} | Rating: {info.get('rating')} | "
                      f"Duration: {info.get('duration')}\n\n")

        date_opts = []
        for i in range(7):
            d = datetime.now() + timedelta(days=i)
            lbl = "Today" if i == 0 else "Tomorrow" if i == 1 else d.strftime("%A")
            date_opts.append(f"{d.strftime('%Y-%m-%d')} ({lbl})")

        self.add_message(
            f"Great choice! 🎬 **{movie_title}**\n{detail}"
            "📅 **Which date?** Click a button or type it in chat:",
            "bot"
        )
        self._add_option_buttons(date_opts, lambda d: self._handle_inline_date(d))
        return ""

    def _handle_inline_date(self, date_str):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
        clean = m.group(1) if m else date_str
        self.add_message(f"📅 {date_str}", "user")
        self.booking_flow["date"] = clean
        self.booking_flow["step"] = 2
        self.quick_date_var.set(date_str)

        info = self._get_movie_info(self.booking_flow["movie"])
        times = info.get("showtimes", []) if info else [
            "10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
        self.add_message(f"📅 Date: **{clean}**\n\n🕐 **Which showtime?**", "bot")
        self._add_option_buttons(times, lambda t: self._handle_inline_time(t))

    def _handle_inline_time(self, time_str):
        self.add_message(f"🕐 {time_str}", "user")
        self.booking_flow["time"] = time_str
        self.booking_flow["step"] = 3
        self.quick_time_var.set(time_str)
        self.add_message(
            f"🕐 Showtime: **{time_str}**\n\n"
            "🎫 **How many tickets?** (type a number, e.g. '2', or use the spinner →)",
            "bot"
        )

    def _handle_inline_theater(self, theater_name):
        self.add_message(f"🏢 {theater_name}", "user")
        self.booking_flow["theater"] = theater_name
        try:
            self.booking_flow["tickets"] = int(self.quick_tickets_var.get())
        except Exception:
            pass
        self.booking_flow["seat_type"] = self.quick_seat_var.get() or "Standard"
        self.booking_flow["step"] = 5
        self.quick_theater_var.set(theater_name)
        summary = self.generate_booking_summary()
        self.add_message(
            f"🏢 Theater: **{theater_name}**\n\n{summary}\n\n"
            "Type **confirm** to complete booking, or **cancel** to start over.",
            "bot"
        )

    def handle_booking_flow_response(self, message):
        step = self.booking_flow["step"]

        if step == 1:
            date = self.extract_date_info(message)
            if date:
                self._handle_inline_date(date)
                return ""
            return (
                "Please pick a date:\n"
                "  • Type 'today', 'tomorrow', or a day name (e.g. 'Friday')\n"
                "  • Or click one of the date buttons above"
            )

        if step == 2:
            t = self.extract_time_info(message)
            if t:
                self._handle_inline_time(t)
                return ""
            info = self._get_movie_info(self.booking_flow["movie"])
            times = info.get("showtimes", []) if info else []
            times_str = "  " + "  |  ".join(times) if times else ""
            return (
                f"Please type a showtime (e.g. '6:30 PM').{chr(10) + times_str if times_str else ''}\n"
                "Or click one of the showtime buttons above."
            )

        if step == 3:
            word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
            ml3 = message.lower()
            count = None
            for word, val in word_map.items():
                if re.search(rf"\b{word}\b", ml3):
                    count = val
                    break
            if count is None:
                m = re.search(r"\b(\d+)\b", message)
                if m:
                    count = int(m.group(1))

            if count is not None:
                count = max(1, min(10, count))
                self.booking_flow["tickets"] = count
                self.booking_flow["step"] = 4
                self.quick_tickets_var.set(str(count))
                theaters = self._get_theaters()
                theater_names = [t["name"] for t in theaters]
                self.add_message(f"🎫 **{count} ticket(s)** added.\n\n🏢 **Which theater?**", "bot")
                self._add_option_buttons(theater_names, lambda t: self._handle_inline_theater(t))
                return ""

            return "Please tell me how many tickets — type a number like '2' or 'two'."

        if step == 4:
            theater = self._extract_theater(message)
            if theater:
                self._handle_inline_theater(theater)
                return ""
            theaters = self._get_theaters()
            theater_names = [t["name"] for t in theaters]
            self.add_message("Please choose a theater:", "bot")
            self._add_option_buttons(theater_names, lambda t: self._handle_inline_theater(t))
            return ""

        if step == 5:
            if message.lower() in ["confirm", "yes", "book it", "proceed", "ok"]:
                return self.confirm_booking()
            if message.lower() in ["cancel", "no", "stop", "quit"]:
                self._reset_booking_flow()
                return "Booking cancelled. Let me know if you'd like to try again! 😊"
            return (
                self.generate_booking_summary()
                + "\n\nType **confirm** to book, or **cancel** to start over."
            )

        return "What movie would you like to book? 🎬"

    # ── Data helpers ───────────────────────────────────────────────────────
    def _load_movies_data(self):
        return safe_read_json(self.movies_file, {"movies": [], "theaters": []})

    def _get_movie_info(self, title):
        data = self._load_movies_data()
        return next(
            (m for m in data.get("movies", [])
             if m.get("title", "").lower() == title.lower()),
            None,
        )

    def _get_theaters(self):
        return self._load_movies_data().get("theaters", [])

    def extract_movie_title(self, message):
        data = self._load_movies_data()
        movies = data.get("movies", [])

        noise = {"book", "ticket", "tickets", "movie", "film", "watch",
                 "reserve", "buy", "for", "a", "the", "please", "i", "want", "to"}
        msg_words = [w for w in message.lower().split() if w not in noise]

        def _lev(a, b):
            if len(a) < len(b):
                a, b = b, a
            if not b:
                return len(a)
            prev = list(range(len(b) + 1))
            for ca in a:
                curr = [prev[0] + 1]
                for j, cb in enumerate(b):
                    curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
                prev = curr
            return prev[-1]

        best_title, best_score = None, 0.0
        for movie in movies:
            title_words = movie.get("title", "").lower().split()
            score = 0.0
            for tw in title_words:
                if tw in msg_words:
                    score += 2
                elif len(tw) > 3 and any(
                    _lev(tw, mw) <= 2 for mw in msg_words if len(mw) > 2
                ):
                    score += 1
            normalised = score / (len(title_words) * 2)
            if normalised > best_score and normalised >= 0.4:
                best_score = normalised
                best_title = movie["title"]
        return best_title

    def extract_date_info(self, message):
        ml = message.lower()
        if "today" in ml:
            return datetime.now().strftime("%Y-%m-%d") + " (Today)"
        if "tomorrow" in ml:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " (Tomorrow)"
        if "weekend" in ml:
            days_ahead = (5 - datetime.now().weekday()) % 7 or 7
            d = datetime.now() + timedelta(days=days_ahead)
            return d.strftime("%Y-%m-%d") + " (Saturday)"
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if day in ml:
                today_wd = datetime.now().weekday()
                target_wd = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].index(day)
                diff = (target_wd - today_wd) % 7 or 7
                d = datetime.now() + timedelta(days=diff)
                return d.strftime("%Y-%m-%d") + f" ({day.capitalize()})"
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
        if m:
            return m.group(1)
        return None

    def extract_time_info(self, message):
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", message, re.IGNORECASE)
        if m:
            hour = int(m.group(1))
            minute = m.group(2) or "00"
            period = m.group(3).lower()
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            return f"{hour % 12 or 12}:{minute} {'AM' if hour < 12 else 'PM'}"
        m24 = re.search(r"\b(\d{2}):(\d{2})\b", message)
        if m24:
            h, mn = int(m24.group(1)), m24.group(2)
            period = "AM" if h < 12 else "PM"
            return f"{h % 12 or 12}:{mn} {period}"
        for word, val in {"morning": "10:00 AM", "afternoon": "2:00 PM",
                          "evening": "6:30 PM", "night": "9:00 PM"}.items():
            if word in message.lower():
                return val
        return None

    def _extract_theater(self, message):
        theaters = self._get_theaters()
        ml = message.lower()
        for t in theaters:
            if t.get("name", "").lower() in ml:
                return t["name"]
        for t in theaters:
            parts = t.get("name", "").lower().split()
            if any(p in ml for p in parts if len(p) > 3):
                return t["name"]
        return None

    # ── Booking summary & confirmation ─────────────────────────────────────
    def generate_booking_summary(self):
        bf = self.booking_flow
        total = self._calculate_total()
        return (
            "📋 **BOOKING SUMMARY**\n"
            + "─" * 32 + "\n"
            f"🎬 Movie:    {bf['movie']}\n"
            f"📅 Date:     {bf['date']}\n"
            f"🕐 Time:     {bf['time']}\n"
            f"🎫 Tickets:  {bf['tickets']}\n"
            f"🏢 Theater:  {bf['theater']}\n"
            f"💺 Seats:    {bf['seat_type']}\n"
            f"💰 Total:    ${total:.2f}\n"
            + "─" * 32
        )

    def _calculate_total(self):
        base = self.ticket_price + (
            self.vip_upcharge if self.booking_flow["seat_type"] == "VIP" else 0
        )
        subtotal = base * self.booking_flow["tickets"]
        return round(subtotal * (1 + self.tax_rate), 2)

    def confirm_booking(self):
        booking_id = f"BK{random.randint(10000, 99999)}"
        total = self._calculate_total()

        record = {
            "booking_id": booking_id,
            "username": self.current_user,
            **{k: self.booking_flow[k] for k in
               ("movie", "date", "time", "tickets", "theater", "seat_type")},
            "total_price": total,
            "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "confirmed",
        }

        try:
            data = safe_read_json(self.bookings_file, {"bookings": []})
            if not isinstance(data.get("bookings"), list):
                data = {"bookings": []}
            data["bookings"].append(record)
            safe_write_json(self.bookings_file, data)
        except Exception as e:
            return f"❌ Could not save booking: {e}\nPlease try again."

        self._reset_booking_flow()

        self.root.after(100, lambda: messagebox.showinfo(
            "Booking Confirmed! 🎉",
            f"Booking {booking_id} confirmed!\n\nEnjoy the movie 🍿"
        ))

        return (
            f"✅ **BOOKING CONFIRMED!**\n\n"
            f"Booking ID: **{booking_id}**\n"
            f"Movie:  {record['movie']}\n"
            f"Date:   {record['date']} at {record['time']}\n"
            f"Theater:{record['theater']}\n"
            f"Tickets:{record['tickets']} ({record['seat_type']})\n"
            f"Total:  ${total:.2f}\n\n"
            "🎬 Enjoy! Don't forget the popcorn 🍿\n\n"
            "Would you like to book another movie?"
        )

    # ── Quick book (right panel) ───────────────────────────────────────────
    def quick_book_tickets(self):
        movie = self.quick_movie_var.get()
        date = self.quick_date_var.get()
        showtime = self.quick_time_var.get()
        theater = self.quick_theater_var.get()
        tickets = self.quick_tickets_var.get()
        seat = self.quick_seat_var.get()

        missing = [f for f, v in [("Movie", movie), ("Date", date),
                                   ("Showtime", showtime), ("Theater", theater)] if not v]
        if missing:
            messagebox.showerror("Missing Fields", "Please fill in: " + ", ".join(missing))
            return

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", date)
        date_str = date_match.group(1) if date_match else date

        self._reset_booking_flow()
        self.booking_flow.update({
            "step": 5,
            "movie": movie,
            "date": date_str,
            "time": showtime,
            "tickets": int(tickets),
            "theater": theater,
            "seat_type": seat,
        })

        summary = self.generate_booking_summary()
        self.add_message(
            f"⚡ **Quick Booking Summary**\n\n{summary}\n\n"
            "Type **confirm** to complete, or **cancel** to reset.",
            "bot"
        )

    # ── View / Cancel bookings ─────────────────────────────────────────────
    def view_my_bookings(self):
        data = safe_read_json(self.bookings_file, {"bookings": []})
        user_bookings = [b for b in data.get("bookings", [])
                         if b.get("username") == self.current_user]

        if not user_bookings:
            return "You have no bookings yet. Would you like to book your first movie? 🎬"

        lines = ["📋 **YOUR BOOKINGS** (last 5)\n"]
        for i, b in enumerate(user_bookings[-5:], 1):
            status_icon = "✅" if b.get("status") == "confirmed" else "❌"
            lines.append(
                f"**#{i} — {b.get('booking_id')}** {status_icon}\n"
                f"🎬 {b.get('movie')}  |  📅 {b.get('date')}  |  🕐 {b.get('time')}\n"
                f"🏢 {b.get('theater')}  |  🎫 {b.get('tickets')} ticket(s)\n"
                f"💰 ${float(b.get('total_price', 0)):.2f}  |  {b.get('status', 'confirmed').upper()}\n"
                + "─" * 30
            )
        lines.append("\nTo cancel: type 'cancel booking BK12345'")
        return "\n".join(lines)

    def _view_bookings_to_chat(self):
        self.add_message(self.view_my_bookings(), "bot")

    def handle_cancel_booking(self, message):
        m = re.search(r"\b(BK\d+)\b", message, re.IGNORECASE)
        if not m:
            return "Please include the booking ID, e.g. 'cancel booking BK12345'."

        booking_id = m.group(1).upper()
        data = safe_read_json(self.bookings_file, {"bookings": []})

        found = False
        for b in data.get("bookings", []):
            if (b.get("booking_id", "").upper() == booking_id
                    and b.get("username") == self.current_user):
                if b.get("status") == "cancelled":
                    return f"Booking **{booking_id}** is already cancelled."
                b["status"] = "cancelled"
                found = True
                break

        if not found:
            return f"Booking **{booking_id}** not found for your account."

        try:
            safe_write_json(self.bookings_file, data)
        except Exception as e:
            return f"❌ Error cancelling booking: {e}"

        return (
            f"✅ Booking **{booking_id}** cancelled.\n"
            "Refund will be processed within 5–7 business days."
        )

    # ── Informational handlers ─────────────────────────────────────────────
    def handle_show_movies(self):
        data = self._load_movies_data()
        movies = data.get("movies", [])
        if not movies:
            return "No movies available right now. Please check back soon!"

        lines = ["🎬 **NOW SHOWING**\n"]
        for m in movies:
            times_preview = ", ".join(m.get("showtimes", [])[:3])
            lines.append(
                f"**{m['title']}**  ⭐ {m.get('imdb')}/10\n"
                f"  {m.get('genre')} | {m.get('rating')} | {m.get('duration')}\n"
                f"  {m.get('description', '')}\n"
                f"  🕐 {times_preview}\n"
            )
        lines.append("Type 'book [movie name]' to get started!")
        return "\n".join(lines)

    def handle_price_query(self):
        return (
            "💰 **TICKET PRICES**\n\n"
            f"Standard:  ${self.ticket_price:.2f}\n"
            f"VIP:       ${self.ticket_price + self.vip_upcharge:.2f}\n"
            f"Tax:       {self.tax_rate * 100:.0f}%\n\n"
            "Would you like to book tickets?"
        )

    def handle_recommendation(self):
        data = self._load_movies_data()
        movies = sorted(data.get("movies", []),
                        key=lambda x: x.get("popularity", 0), reverse=True)

        genre_pref = self.user_preferences.get("genre")
        if genre_pref:
            preferred = [m for m in movies if genre_pref.lower() in m.get("genre", "").lower()]
            if preferred:
                movies = preferred + [m for m in movies if m not in preferred]

        lines = ["⭐ **RECOMMENDED FOR YOU**\n"]
        for i, m in enumerate(movies[:3], 1):
            lines.append(
                f"{i}. **{m['title']}**  ⭐ {m.get('imdb')}/10\n"
                f"   {m.get('genre')} | {m.get('rating')}\n"
                f"   {m.get('description', '')[:90]}...\n"
            )
        lines.append("Which one catches your eye?")
        return "\n".join(lines)

    def handle_help(self):
        return (
            "🤖 **AVAILABLE COMMANDS**\n\n"
            "**Booking**\n"
            "  • 'book tickets for [movie]'\n"
            "  • Use the Quick Booking form →\n\n"
            "**Browse**\n"
            "  • 'show movies'\n"
            "  • 'recommend something'\n"
            "  • 'ticket prices'\n\n"
            "**Manage**\n"
            "  • 'view my bookings'\n"
            "  • 'cancel booking BK12345'\n\n"
            "**Other**\n"
            "  • 'help' — show this message\n"
            "  • 'hello' — greet me\n\n"
            "What would you like to do? 😊"
        )

    # ── Automation callbacks ───────────────────────────────────────────────
    def toggle_automation(self):
        C = self.C
        self.automation_active = not self.automation_active
        if self.automation_active:
            self.automation_status.config(text=" LIVE", fg=C["teal"])
            self._status_dot_label.config(fg=C["teal"])
            self.auto_toggle_btn.config(text="● AUTO-MODE: ON", bg=C["teal"], fg=C["bg_deep"])
            self.add_message("Automation enabled — smart suggestions active! 🚀", "bot")
        else:
            self.automation_status.config(text=" PAUSED", fg=C["gold_dim"])
            self._status_dot_label.config(fg=C["gold_dim"])
            self.auto_toggle_btn.config(text="○ AUTO-MODE: OFF", bg=C["bg_card"], fg=C["text_mid"])
            self.add_message("Automation paused.", "bot")

    def auto_book_movie(self):
        data = self._load_movies_data()
        movies = sorted(data.get("movies", []),
                        key=lambda x: x.get("popularity", 0), reverse=True)
        if not movies:
            self.add_message("No movies available right now.", "bot")
            return
        best = movies[0]
        self.add_message(
            f"🚀  AUTO-BOOKING SUGGESTION\n\n"
            f"Most popular right now: {best['title']}\n"
            f"Genre: {best.get('genre')}  |  ⭐ {best.get('imdb')}/10\n\n"
            f"Suggested: Tomorrow at 6:30 PM @ City Center Cinemas\n\n"
            f"Type 'book {best['title']}' or fill the form to proceed!",
            "bot"
        )

    def smart_suggestions(self):
        self.add_message(f"💡  {self._random_suggestion()}", "bot")

    def auto_schedule(self):
        self.add_message(
            "📅  AUTO-SCHEDULE TIPS\n\n"
            "• Book 2–3 days ahead for best seat selection\n"
            "• Peak times: 6:30 PM – 9:00 PM (Fri–Sun)\n"
            "• Quieter slots: weekday matinees\n\n"
            "Want me to find a slot for this weekend?",
            "bot"
        )

    def quick_fill_booking(self):
        self.add_message(
            "⚡  QUICK FILL GUIDE\n\n"
            "1. Choose Film, Date, Showtime & Theater from the panel →\n"
            "2. Click  BOOK TICKETS\n"
            "3. Type  confirm  in chat to complete\n\n"
            "Give it a try!",
            "bot"
        )

    def learn_preferences(self):
        genre = self.user_preferences.get("genre") or "not set yet"
        tod   = self.user_preferences.get("time_preference") or "evening"
        self.add_message(
            f"🔄  YOUR PREFERENCES\n\n"
            f"Favourite genre : {genre}\n"
            f"Preferred time  : {tod}\n\n"
            "I'll use these to give better recommendations.\n"
            "Keep chatting and I'll keep learning! 📚",
            "bot"
        )

    # ── Chat display ───────────────────────────────────────────────────────
    def add_message(self, message, sender="user"):
        self.chat_display.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M")
        if sender == "user":
            self.chat_display.insert(tk.END, "\n", "divider")
            self.chat_display.insert(tk.END, f"  {ts}  YOU\n", "user_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_display.insert(tk.END, "\n", "divider")
            self.chat_display.insert(tk.END, f"  {ts}  CINEBOOK\n", "bot_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "bot_msg")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.conversation_history.append({
            "timestamp": ts, "sender": sender, "message": message
        })

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("🎬 Starting AI Movie Booking Assistant...")
    app = AutomatedMovieChatbot()
    app.run()