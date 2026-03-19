import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import json
import os
import tempfile
from datetime import datetime, timedelta
import re
import random
import threading
from collections import defaultdict
import queue
import math


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
        self.root.after(800, self.auto_greeting)

    def _reset_booking_flow(self):
        self.booking_flow = {
            "step": 0, "movie": None, "date": None,
            "time": None, "tickets": 1, "theater": None, "seat_type": "Standard",
        }

    # ─── Hover helper ──────────────────────────────────────────────────────
    def _make_hover(self, widget, bg_normal, bg_hover, fg_normal=None, fg_hover=None):
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

    # ─── Data init ─────────────────────────────────────────────────────────
    def initialize_data(self):
        if not os.path.exists(self.movies_file):
            movies_data = {
                "movies": [
                    {"id":1,"title":"The Last Adventure","genre":"Action/Adventure","duration":"2h 15m","rating":"PG-13","description":"An epic journey through uncharted territories.","director":"Alex Rivera","cast":["Chris Evans","Zendaya","Idris Elba"],"imdb":7.8,"popularity":95,"showtimes":["10:00 AM","1:30 PM","4:00 PM","6:30 PM","9:00 PM"]},
                    {"id":2,"title":"Cosmic Dreams","genre":"Sci-Fi","duration":"2h 30m","rating":"PG","description":"A mind-bending journey through space and time.","director":"Lisa Chen","cast":["Tom Hanks","Millie Bobby Brown","Keanu Reeves"],"imdb":8.2,"popularity":98,"showtimes":["11:00 AM","2:30 PM","5:00 PM","8:30 PM"]},
                    {"id":3,"title":"Heartstrings","genre":"Romance/Drama","duration":"1h 50m","rating":"PG-13","description":"A love story that transcends time.","director":"Sophia Lee","cast":["Emma Stone","Timothée Chalamet","Viola Davis"],"imdb":7.5,"popularity":88,"showtimes":["12:00 PM","3:30 PM","7:00 PM","10:00 PM"]},
                    {"id":4,"title":"Midnight Mystery","genre":"Thriller/Mystery","duration":"2h 5m","rating":"R","description":"A detective races against time to solve a century-old mystery.","director":"James Nolan","cast":["Daniel Craig","Ana de Armas","Anthony Hopkins"],"imdb":8.0,"popularity":92,"showtimes":["1:00 PM","4:30 PM","9:00 PM"]},
                    {"id":5,"title":"Laugh Out Loud","genre":"Comedy","duration":"1h 45m","rating":"PG","description":"The funniest movie of the year!","director":"Kevin Hart","cast":["Ryan Reynolds","Tiffany Haddish","Jack Black"],"imdb":6.9,"popularity":85,"showtimes":["10:30 AM","2:00 PM","5:30 PM","9:30 PM"]},
                ],
                "theaters": [
                    {"id":1,"name":"City Center Cinemas","location":"Downtown","vip":True,"popularity":95},
                    {"id":2,"name":"Starlight Theater","location":"Westside Mall","vip":True,"popularity":88},
                    {"id":3,"name":"Grand Arena","location":"Eastgate Complex","vip":False,"popularity":82},
                    {"id":4,"name":"Royal IMAX","location":"North Plaza","vip":True,"popularity":92},
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

    # ─── GUI ───────────────────────────────────────────────────────────────
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("CINEBOOK  ·  AI Concierge")
        self.root.geometry("1340x880")
        self.root.configure(bg="#080810")
        self.root.resizable(True, True)
        self.root.minsize(960, 620)

        self.C = {
            # backgrounds
            "bg_root":    "#080810",
            "bg_panel":   "#0c0c18",
            "bg_card":    "#111120",
            "bg_input":   "#181828",
            "bg_hover":   "#1c1c2e",
            "bg_msg_bot": "#0f0f1e",
            "bg_msg_usr": "#120d20",
            # accents
            "gold":       "#f0c060",
            "gold_dim":   "#8a6820",
            "gold_glow":  "#ffe080",
            "gold_soft":  "#c89840",
            "amber":      "#e07030",
            "crimson":    "#c02840",
            "crimson_h":  "#e03050",
            "teal":       "#20c8a0",
            "teal_dim":   "#106850",
            "violet":     "#8060f0",
            "violet_dim": "#4030a0",
            # text
            "text_hi":    "#f0eadc",
            "text_mid":   "#9088708",
            "text_dim":   "#40384868",
            "text_gold":  "#f0c060",
            "text_teal":  "#20c8a0",
            "text_user":  "#a0c8f0",
            "text_bot":   "#dcd4bc",
            # borders
            "border":     "#20182e",
            "border_g":   "#302418",
            "sep":        "#1e1830",
        }
        # fix hex typos
        self.C["text_mid"] = "#908870"
        self.C["text_dim"] = "#403848"

        C = self.C
        style = ttk.Style()
        style.theme_use("clam")
        for w in ("TCombobox",):
            style.configure(w, fieldbackground=C["bg_input"], background=C["bg_input"],
                foreground=C["text_hi"], bordercolor=C["border_g"],
                lightcolor=C["bg_input"], darkcolor=C["bg_input"],
                selectbackground=C["gold_dim"], selectforeground=C["text_hi"],
                arrowcolor=C["gold"], insertcolor=C["gold"], padding=6)
            style.map(w, fieldbackground=[("readonly", C["bg_input"]), ("focus", C["bg_hover"])],
                bordercolor=[("focus", C["gold"])])
        style.configure("TScrollbar", background=C["bg_card"], troughcolor=C["bg_panel"],
            arrowcolor=C["gold_dim"], bordercolor=C["bg_panel"], width=8)

        self.root.grid_columnconfigure(0, weight=7)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

        # chat tags
        self.chat_display.tag_config("usr_label", foreground=C["text_user"],
            font=("Courier", 8, "bold"), spacing1=10)
        self.chat_display.tag_config("usr_msg", foreground=C["text_user"],
            lmargin1=16, lmargin2=16, spacing3=6)
        self.chat_display.tag_config("bot_label", foreground=C["gold"],
            font=("Courier", 8, "bold"), spacing1=10)
        self.chat_display.tag_config("bot_msg", foreground=C["text_bot"],
            lmargin1=16, lmargin2=16, spacing3=6)
        self.chat_display.tag_config("sys_msg", foreground=C["teal"],
            lmargin1=16, lmargin2=16, font=("Courier", 9, "italic"))
        self.chat_display.tag_config("err_msg", foreground=C["crimson_h"],
            lmargin1=16, lmargin2=16)

        self._dot_phase = 0
        self._ticker_chars = list("▸ ANALYSING YOUR PREFERENCES…")
        self._ticker_pos = 0
        self._animate_dot()
        self._animate_ticker()

    def _build_left_panel(self):
        C = self.C
        left = tk.Frame(self.root, bg=C["bg_panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # ── Cinematic header ──────────────────────────────────────────────
        hdr = tk.Frame(left, bg=C["bg_root"], height=70)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        # left gold accent stripe
        tk.Frame(hdr, bg=C["gold"], width=5).pack(side=tk.LEFT, fill=tk.Y)

        title_frame = tk.Frame(hdr, bg=C["bg_root"])
        title_frame.pack(side=tk.LEFT, padx=(14, 0), pady=8)
        tk.Label(title_frame, text="CINEBOOK", font=("Georgia", 22, "bold"),
                 bg=C["bg_root"], fg=C["gold"]).pack(anchor="w")
        tk.Label(title_frame, text="AI  ·  CONCIERGE  ·  TICKETING",
                 font=("Courier", 7), bg=C["bg_root"], fg=C["gold_dim"],
                 ).pack(anchor="w")

        # right status cluster
        status_frame = tk.Frame(hdr, bg=C["bg_root"])
        status_frame.pack(side=tk.RIGHT, padx=18)
        dot_row = tk.Frame(status_frame, bg=C["bg_root"])
        dot_row.pack(anchor="e")
        self._status_dot = tk.Label(dot_row, text="◉", font=("Courier", 13),
                                     bg=C["bg_root"], fg=C["teal"])
        self._status_dot.pack(side=tk.LEFT)
        self._status_lbl = tk.Label(dot_row, text=" LIVE", font=("Courier", 9, "bold"),
                                     bg=C["bg_root"], fg=C["teal"])
        self._status_lbl.pack(side=tk.LEFT)
        self.automation_status = self._status_lbl  # alias

        # ── Chat canvas ───────────────────────────────────────────────────
        chat_wrap = tk.Frame(left, bg=C["bg_root"])
        chat_wrap.grid(row=1, column=0, sticky="nsew")
        chat_wrap.grid_rowconfigure(0, weight=1)
        chat_wrap.grid_columnconfigure(0, weight=1)

        self.chat_display = tk.Text(
            chat_wrap, font=("Georgia", 11), bg=C["bg_root"], fg=C["text_hi"],
            wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=22, pady=16,
            state=tk.DISABLED, cursor="arrow",
            selectbackground=C["gold_dim"], selectforeground=C["text_hi"],
            spacing1=2, spacing3=2, insertbackground=C["gold"])
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(chat_wrap, orient=tk.VERTICAL, command=self.chat_display.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.chat_display.config(yscrollcommand=vsb.set)

        # ── Thinking bar ──────────────────────────────────────────────────
        self.thinking_var = tk.StringVar(value="")
        thinking_lbl = tk.Label(left, textvariable=self.thinking_var,
            font=("Courier", 9, "italic"), bg=C["bg_panel"], fg=C["gold_dim"],
            anchor="w", padx=22)
        thinking_lbl.grid(row=2, column=0, sticky="ew")

        # ── Suggestion ticker ─────────────────────────────────────────────
        ticker_frame = tk.Frame(left, bg=C["bg_card"], height=38)
        ticker_frame.grid(row=3, column=0, sticky="ew")
        ticker_frame.grid_propagate(False)
        tk.Frame(ticker_frame, bg=C["amber"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(ticker_frame, text="  ✦ ", font=("Georgia", 10),
                 bg=C["bg_card"], fg=C["amber"]).pack(side=tk.LEFT)
        self.suggestions_text = tk.Label(ticker_frame, text="",
            font=("Courier", 9), bg=C["bg_card"], fg=C["text_mid"], anchor="w")
        self.suggestions_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # ── Action toolbar ────────────────────────────────────────────────
        toolbar = tk.Frame(left, bg=C["bg_panel"], pady=6)
        toolbar.grid(row=4, column=0, sticky="ew", padx=10)
        actions = [
            ("⚡ AUTO-BOOK",  self.auto_book_movie,   C["gold_dim"],   C["gold"],     C["bg_root"], C["gold"]),
            ("✦ SUGGEST",    self.smart_suggestions,  C["bg_card"],    C["bg_hover"], C["gold_dim"],C["gold"]),
            ("◈ SCHEDULE",   self.auto_schedule,      C["bg_card"],    C["bg_hover"], C["gold_dim"],C["gold"]),
            ("▶ QUICK FILL", self.quick_fill_booking, C["violet_dim"], C["violet"],   C["text_hi"], C["text_hi"]),
            ("◎ PREFS",      self.learn_preferences,  C["bg_card"],    C["bg_hover"], C["text_mid"],C["text_hi"]),
        ]
        for text, cmd, bg, hbg, fg, hfg in actions:
            b = tk.Button(toolbar, text=text, command=cmd, bg=bg, fg=fg,
                          font=("Courier", 8, "bold"), relief=tk.FLAT,
                          cursor="hand2", padx=10, pady=6, bd=0,
                          activebackground=hbg, activeforeground=hfg)
            b.pack(side=tk.LEFT, padx=3)
            self._make_hover(b, bg, hbg, fg, hfg)

        # ── Input area ────────────────────────────────────────────────────
        inp_wrap = tk.Frame(left, bg=C["bg_card"])
        inp_wrap.grid(row=5, column=0, sticky="ew")
        inp_wrap.grid_columnconfigure(0, weight=1)
        # top border line (gold)
        tk.Frame(inp_wrap, bg=C["gold"], height=2).grid(row=0, column=0, columnspan=3, sticky="ew")

        self.user_input = tk.Entry(inp_wrap, font=("Georgia", 12),
            bg=C["bg_card"], fg=C["text_hi"], insertbackground=C["gold"],
            relief=tk.FLAT, bd=0, highlightthickness=0)
        self.user_input.grid(row=1, column=0, sticky="ew", padx=(20, 6), ipady=13)
        self.user_input.bind("<Return>", lambda e: self.process_input())

        # voice-mode placeholder label
        tk.Label(inp_wrap, text="↵", font=("Georgia", 11),
                 bg=C["bg_card"], fg=C["gold_dim"]).grid(row=1, column=1, padx=(0, 4))

        send_btn = tk.Button(inp_wrap, text="SEND", command=self.process_input,
            bg=C["gold"], fg=C["bg_root"], font=("Courier", 10, "bold"),
            relief=tk.FLAT, cursor="hand2", activebackground=C["gold_glow"],
            activeforeground=C["bg_root"], bd=0, padx=22)
        send_btn.grid(row=1, column=2, sticky="ns", pady=1, padx=(0, 1))
        self._make_hover(send_btn, C["gold"], C["gold_glow"], C["bg_root"], C["bg_root"])

    def _build_right_panel(self):
        C = self.C
        right = tk.Frame(self.root, bg=C["bg_panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.grid_columnconfigure(0, weight=1)

        # ── Panel header ──────────────────────────────────────────────────
        rh = tk.Frame(right, bg=C["bg_root"], height=70)
        rh.grid(row=0, column=0, sticky="ew")
        rh.grid_propagate(False)
        tk.Frame(rh, bg=C["crimson"], width=5).pack(side=tk.LEFT, fill=tk.Y)
        lf = tk.Frame(rh, bg=C["bg_root"])
        lf.pack(side=tk.LEFT, padx=14, pady=8)
        tk.Label(lf, text="BOOKING", font=("Georgia", 16, "bold"),
                 bg=C["bg_root"], fg=C["text_hi"]).pack(anchor="w")
        tk.Label(lf, text="QUICK  ·  PANEL", font=("Courier", 7),
                 bg=C["bg_root"], fg=C["text_mid"]).pack(anchor="w")

        # ── Auto-mode toggle ──────────────────────────────────────────────
        ctrl = tk.Frame(right, bg=C["bg_panel"])
        ctrl.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 4))
        self.auto_toggle_btn = tk.Button(ctrl, text="◉  AUTO-MODE  ON",
            command=self.toggle_automation, bg=C["teal_dim"], fg=C["teal"],
            font=("Courier", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            activebackground=C["teal"], activeforeground=C["bg_root"], bd=0, pady=7)
        self.auto_toggle_btn.pack(fill=tk.X)
        self._make_hover(self.auto_toggle_btn, C["teal_dim"], C["teal"], C["teal"], C["bg_root"])

        # ── Booking progress card ─────────────────────────────────────────
        prog = tk.Frame(right, bg=C["bg_card"], highlightbackground=C["border_g"], highlightthickness=1)
        prog.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 6))
        tk.Frame(prog, bg=C["gold"], height=2).pack(fill=tk.X)
        self.booking_status = tk.Label(prog, text="  No active booking",
            font=("Courier", 9), bg=C["bg_card"], fg=C["text_mid"],
            justify=tk.LEFT, wraplength=240, anchor="w", padx=10, pady=8)
        self.booking_status.pack(fill=tk.X)

        # ── Divider + section title ───────────────────────────────────────
        sec = tk.Frame(right, bg=C["bg_panel"])
        sec.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 0))
        tk.Frame(sec, bg=C["sep"], height=1).pack(fill=tk.X)
        tk.Label(sec, text="▸  QUICK BOOKING FORM", font=("Courier", 8, "bold"),
                 bg=C["bg_panel"], fg=C["gold_soft"]).pack(anchor="w", pady=(6, 2))

        # ── Form fields ───────────────────────────────────────────────────
        form = tk.Frame(right, bg=C["bg_panel"])
        form.grid(row=4, column=0, sticky="ew", padx=10)
        form.grid_columnconfigure(0, weight=1)

        def field_label(parent, text):
            tk.Label(parent, text=text, font=("Courier", 7, "bold"),
                     bg=C["bg_panel"], fg=C["gold_dim"]).pack(anchor="w", pady=(10, 2))

        field_label(form, "FILM")
        self.quick_movie_var = tk.StringVar()
        self.quick_movie_combo = ttk.Combobox(form, textvariable=self.quick_movie_var,
                                               state="readonly", font=("Georgia", 10))
        self.quick_movie_combo.pack(fill=tk.X)
        self.quick_movie_combo.bind("<<ComboboxSelected>>", lambda e: self._combo_select_movie())

        field_label(form, "DATE")
        self.quick_date_var = tk.StringVar()
        self.quick_date_combo = ttk.Combobox(form, textvariable=self.quick_date_var,
                                              state="readonly", font=("Georgia", 10))
        self.quick_date_combo.pack(fill=tk.X)
        self.quick_date_combo.bind("<<ComboboxSelected>>", lambda e: self._combo_select_date())

        field_label(form, "SHOWTIME")
        self.quick_time_var = tk.StringVar()
        self.quick_time_combo = ttk.Combobox(form, textvariable=self.quick_time_var,
                                              state="readonly", font=("Georgia", 10))
        self.quick_time_combo.pack(fill=tk.X)
        self.quick_time_combo.bind("<<ComboboxSelected>>", lambda e: self._combo_select_time())

        field_label(form, "THEATER")
        self.quick_theater_var = tk.StringVar()
        self.quick_theater_combo = ttk.Combobox(form, textvariable=self.quick_theater_var,
                                                 state="readonly", font=("Georgia", 10))
        self.quick_theater_combo.pack(fill=tk.X)
        self.quick_theater_combo.bind("<<ComboboxSelected>>", lambda e: self._combo_select_theater())

        # tickets + seat row
        mid = tk.Frame(form, bg=C["bg_panel"])
        mid.pack(fill=tk.X, pady=(10, 0))

        t_col = tk.Frame(mid, bg=C["bg_panel"])
        t_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(t_col, text="TICKETS", font=("Courier", 7, "bold"),
                 bg=C["bg_panel"], fg=C["gold_dim"]).pack(anchor="w")
        self.quick_tickets_var = tk.StringVar(value="1")
        tk.Spinbox(t_col, from_=1, to=10, textvariable=self.quick_tickets_var,
                   font=("Georgia", 11), bg=C["bg_input"], fg=C["gold"],
                   buttonbackground=C["bg_card"], insertbackground=C["gold"],
                   relief=tk.FLAT, bd=1, width=5).pack(anchor="w")

        s_col = tk.Frame(mid, bg=C["bg_panel"])
        s_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))
        tk.Label(s_col, text="SEAT TYPE", font=("Courier", 7, "bold"),
                 bg=C["bg_panel"], fg=C["gold_dim"]).pack(anchor="w")
        self.quick_seat_var = tk.StringVar(value="Standard")
        for seat in ("Standard", "VIP"):
            tk.Radiobutton(s_col, text=seat, variable=self.quick_seat_var, value=seat,
                           font=("Courier", 9), bg=C["bg_panel"], fg=C["text_hi"],
                           selectcolor=C["bg_root"], activebackground=C["bg_panel"],
                           activeforeground=C["gold"]).pack(anchor="w")

        # ── Action buttons ────────────────────────────────────────────────
        btn_area = tk.Frame(right, bg=C["bg_panel"])
        btn_area.grid(row=5, column=0, sticky="ew", padx=10, pady=(14, 6))
        btn_area.grid_columnconfigure(0, weight=1)

        book_btn = tk.Button(btn_area, text="🎫   BOOK TICKETS",
            command=self.quick_book_tickets, bg=C["crimson"], fg=C["text_hi"],
            font=("Courier", 11, "bold"), relief=tk.FLAT, cursor="hand2",
            activebackground=C["crimson_h"], activeforeground=C["text_hi"],
            bd=0, pady=11)
        book_btn.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._make_hover(book_btn, C["crimson"], C["crimson_h"])

        view_btn = tk.Button(btn_area, text="📋   MY BOOKINGS",
            command=self._view_bookings_to_chat, bg=C["bg_card"], fg=C["gold"],
            font=("Courier", 10), relief=tk.FLAT, cursor="hand2",
            activebackground=C["bg_hover"], activeforeground=C["gold_glow"],
            bd=0, pady=8, highlightbackground=C["border_g"], highlightthickness=1)
        view_btn.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self._make_hover(view_btn, C["bg_card"], C["bg_hover"], C["gold"], C["gold_glow"])

        cancel_btn = tk.Button(btn_area, text="✕   CANCEL A BOOKING",
            command=self._prompt_cancel_booking, bg=C["bg_card"], fg=C["crimson_h"],
            font=("Courier", 9), relief=tk.FLAT, cursor="hand2",
            activebackground=C["bg_hover"], activeforeground=C["crimson_h"],
            bd=0, pady=7, highlightbackground=C["crimson"], highlightthickness=1)
        cancel_btn.grid(row=2, column=0, sticky="ew")
        self._make_hover(cancel_btn, C["bg_card"], C["bg_hover"])

        self.update_quick_form()

    # ─── Animation helpers ─────────────────────────────────────────────────
    def _animate_dot(self):
        colours = [self.C["teal"], "#18a080", "#10604e"]
        self._dot_phase = (self._dot_phase + 1) % len(colours)
        if self.automation_active:
            self._status_dot.config(fg=colours[self._dot_phase])
        self.root.after(600, self._animate_dot)

    def _animate_ticker(self):
        try:
            # pull any new suggestion
            while not self.suggestions_queue.empty():
                msg = self.suggestions_queue.get_nowait()
                self._ticker_chars = list(msg)
                self._ticker_pos = 0
        except queue.Empty:
            pass

        visible = "".join(self._ticker_chars[:self._ticker_pos + 1])
        self.suggestions_text.config(text=visible)
        if self._ticker_pos < len(self._ticker_chars) - 1:
            self._ticker_pos += 1
            self.root.after(40, self._animate_ticker)
        else:
            self.root.after(5000, self._animate_ticker)

    def _random_suggestion(self):
        return random.choice([
            "✦  Cosmic Dreams trending — book before it sells out!",
            "✦  Midnight Mystery 8.0/10 — highly recommended tonight",
            "✦  Friday evenings fill fast — reserve your seats early",
            "✦  VIP seats still available for The Last Adventure",
            "✦  Weekend shows going quickly — grab yours now",
            "✦  New this week: Heartstrings — a must-watch romance",
            "✦  Group discount: 4+ tickets save 10% at Royal IMAX",
        ])

    # ─── Background threads ────────────────────────────────────────────────
    def start_automation(self):
        threading.Thread(target=self._suggestion_loop, daemon=True).start()
        threading.Thread(target=self._status_loop, daemon=True).start()

    def _suggestion_loop(self):
        import time
        while True:
            time.sleep(14)
            if self.automation_active:
                self.suggestions_queue.put(self._random_suggestion())

    def _status_loop(self):
        import time
        while True:
            time.sleep(4)
            self.root.after(0, self._refresh_booking_status)

    def _refresh_booking_status(self):
        bf = self.booking_flow
        if bf["step"] > 0:
            step_labels = ["", "Film selected", "Date chosen", "Showtime set",
                           "Theater chosen", "Ready to confirm"]
            lbl = step_labels[min(bf["step"], 5)]
            lines = [f"  Step {bf['step']}/5  —  {lbl}"]
            if bf["movie"]:  lines.append(f"  🎬  {bf['movie']}")
            if bf["date"]:   lines.append(f"  📅  {bf['date']}")
            if bf["time"]:   lines.append(f"  🕐  {bf['time']}")
            self.booking_status.config(text="\n".join(lines), fg=self.C["gold"])
        else:
            self.booking_status.config(text="  No active booking", fg=self.C["text_mid"])

    # ─── Quick form ────────────────────────────────────────────────────────
    def update_quick_form(self):
        data = safe_read_json(self.movies_file, {"movies": [], "theaters": []})
        movies = data.get("movies", [])
        theaters = data.get("theaters", [])
        self.quick_movie_combo["values"] = [m["title"] for m in movies]
        today = datetime.now()
        dates = []
        for i in range(7):
            d = today + timedelta(days=i)
            lbl = "(Today)" if i == 0 else "(Tomorrow)" if i == 1 else f"({d.strftime('%A')})"
            dates.append(f"{d.strftime('%Y-%m-%d')} {lbl}")
        self.quick_date_combo["values"] = dates
        all_times = sorted({t for m in movies for t in m.get("showtimes", [])})
        self.quick_time_combo["values"] = all_times or ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
        self.quick_theater_combo["values"] = [t["name"] for t in theaters]

    # ─── Combo handlers ────────────────────────────────────────────────────
    def _combo_select_movie(self):
        movie = self.quick_movie_var.get()
        if not movie: return
        if self.booking_flow["step"] == 0:
            self._reset_booking_flow()
            self.booking_flow["step"] = 1
            self.booking_flow["movie"] = movie
            info = self._get_movie_info(movie)
            g = info.get("genre","") if info else ""
            r = info.get("rating","") if info else ""
            d = info.get("duration","") if info else ""
            self.add_message(f"🎬  {movie}\n{g}  ·  {r}  ·  {d}\n\nNow pick a Date ↓", "bot")
        else:
            self.booking_flow["movie"] = movie
            self.add_message(f"🎬  Film updated → {movie}", "bot")

    def _combo_select_date(self):
        raw = self.quick_date_var.get()
        if not raw: return
        if not self.booking_flow["movie"]:
            movie = self.quick_movie_var.get()
            if not movie:
                self.add_message("⚠  Please select a Film first.", "bot"); return
            self._reset_booking_flow()
            self.booking_flow["step"] = 1
            self.booking_flow["movie"] = movie
        m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
        date_str = m.group(1) if m else raw
        self.booking_flow["date"] = date_str
        if self.booking_flow["step"] <= 1: self.booking_flow["step"] = 2
        info = self._get_movie_info(self.booking_flow["movie"])
        times = info.get("showtimes", []) if info else []
        ts = "  " + "  ·  ".join(times) if times else ""
        self.add_message(f"📅  {date_str}\n\nPick a Showtime ↓{chr(10)+ts if ts else ''}", "bot")

    def _combo_select_time(self):
        showtime = self.quick_time_var.get()
        if not showtime: return
        if not self.booking_flow["date"]:
            self.add_message("⚠  Please select a Date first.", "bot"); return
        self.booking_flow["time"] = showtime
        if self.booking_flow["step"] <= 2: self.booking_flow["step"] = 3
        self.add_message(f"🕐  {showtime}\n\nSet Tickets then choose a Theater ↓", "bot")

    def _combo_select_theater(self):
        theater = self.quick_theater_var.get()
        if not theater: return
        if not self.booking_flow["time"]:
            self.add_message("⚠  Please select a Showtime first.", "bot"); return
        self.booking_flow["theater"] = theater
        try: self.booking_flow["tickets"] = int(self.quick_tickets_var.get())
        except: self.booking_flow["tickets"] = 1
        self.booking_flow["seat_type"] = self.quick_seat_var.get() or "Standard"
        self.booking_flow["step"] = 5
        summary = self.generate_booking_summary()
        self.add_message(f"🏢  {theater}\n\n{summary}\n\nType  confirm  to book,  cancel  to start over.", "bot")

    # ─── Inline option buttons ─────────────────────────────────────────────
    def _add_option_buttons(self, options, callback):
        self.chat_display.config(state=tk.NORMAL)
        C = self.C
        btn_frame = tk.Frame(self.chat_display, bg=C["bg_root"], pady=4)

        def make_handler(opt, frame):
            def handler():
                frame.destroy()
                callback(opt)
            return handler

        for opt in options:
            b = tk.Button(btn_frame, text=opt, command=make_handler(opt, btn_frame),
                bg=C["bg_card"], fg=C["gold"], font=("Courier", 8, "bold"),
                relief=tk.FLAT, cursor="hand2", padx=10, pady=5, bd=0,
                activebackground=C["gold_dim"], activeforeground=C["bg_root"],
                highlightbackground=C["border_g"], highlightthickness=1)
            b.pack(side=tk.LEFT, padx=4, pady=3)
            self._make_hover(b, C["bg_card"], C["gold_dim"], C["gold"], C["bg_root"])

        self.chat_display.window_create(tk.END, window=btn_frame)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    # ─── Greeting ──────────────────────────────────────────────────────────
    def auto_greeting(self):
        h = datetime.now().hour
        tod = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        self.add_message(
            f"Good {tod} — I'm CineBook, your AI movie concierge.\n\n"
            "  🎬  Browse & discover what's showing\n"
            "  🎫  Book tickets in seconds\n"
            "  📋  View & cancel your bookings\n"
            "  ⭐  Get personalised recommendations\n\n"
            "Type  help  for all commands, or just tell me what you'd like.", "bot")

    # ─── Input processing ──────────────────────────────────────────────────
    def process_input(self):
        user_text = self.user_input.get().strip()
        if not user_text: return
        self.user_input.delete(0, tk.END)
        self.add_message(user_text, "user")
        self.learn_from_input(user_text)
        self.thinking_var.set("  ◌  thinking…")
        self.root.after(280, lambda: self._deliver_response(user_text))

    def _deliver_response(self, user_text):
        response = self.understand_and_respond(user_text)
        if response:
            self.add_message(response, "bot")
        self.thinking_var.set("")

    def learn_from_input(self, text):
        t = text.lower()
        for genre in ["action","comedy","drama","sci-fi","thriller","romance","mystery"]:
            if genre in t: self.user_preferences["genre"] = genre.capitalize()
        if "morning" in t: self.user_preferences["time_preference"] = "morning"
        elif "afternoon" in t: self.user_preferences["time_preference"] = "afternoon"
        elif "evening" in t or "night" in t: self.user_preferences["time_preference"] = "evening"
        self.save_user_preferences()

    # ─── Intent router ─────────────────────────────────────────────────────
    def understand_and_respond(self, message):
        ml = message.lower().strip()

        # ── FIX: "cancel booking BKxxxxx" must ALWAYS reach handle_cancel_booking
        # even mid-flow — check for BK pattern before flow interception.
        if re.search(r"\bbk\d+\b", ml, re.IGNORECASE):
            return self.handle_cancel_booking(message)

        if self.booking_flow["step"] > 0:
            if any(w in ml for w in ["cancel","stop","quit","restart","start over"]):
                self._reset_booking_flow()
                return "Booking cleared. What else can I help you with?"
            if ml in ["help", "?"]:
                return self.handle_help()
            return self.handle_booking_flow_response(message)

        if any(w in ml for w in ["hello","hi","hey","greet"]):
            return "Hello! 👋  What movie would you like to book today?"
        if any(w in ml for w in ["book","ticket","reserve","buy"]):
            return self.handle_book_ticket(message)
        if any(w in ml for w in ["show","movie","available","playing","list","what's on"]):
            return self.handle_show_movies()
        if any(w in ml for w in ["my booking","view booking","bookings","history"]):
            return self.view_my_bookings()
        if any(w in ml for w in ["cancel","delete","remove"]):
            return self.handle_cancel_booking(message)
        if any(w in ml for w in ["price","cost","how much","fee"]):
            return self.handle_price_query()
        if any(w in ml for w in ["recommend","suggestion","best","popular"]):
            return self.handle_recommendation()
        if any(w in ml for w in ["help","what can you","commands","?"]):
            return self.handle_help()
        if any(w in ml for w in ["thank","thanks","cheers"]):
            return random.choice(["You're welcome! 🎬","Happy to help — enjoy the show! 🍿","My pleasure!"])

        return "I didn't quite catch that.\nTry: 'show movies', 'book tickets', 'my bookings', or 'help'."

    # ─── Booking flow ──────────────────────────────────────────────────────
    def handle_book_ticket(self, message):
        movie_title = self.extract_movie_title(message)
        if self.booking_flow["step"] > 0 and movie_title and movie_title != self.booking_flow.get("movie"):
            self._reset_booking_flow()
            self.add_message("Previous booking cleared — starting fresh.", "bot")
        if not movie_title:
            data = self._load_movies_data()
            titles = [m["title"] for m in data.get("movies", [])]
            self.add_message("Which film would you like to book?", "bot")
            self._add_option_buttons(titles, lambda t: self._deliver_response(f"book {t}"))
            return ""
        self._reset_booking_flow()
        self.booking_flow["step"] = 1
        self.booking_flow["movie"] = movie_title
        self.quick_movie_var.set(movie_title)
        info = self._get_movie_info(movie_title)
        detail = ""
        if info:
            detail = f"{info.get('genre')}  ·  {info.get('rating')}  ·  {info.get('duration')}\n\n"
        date_opts = []
        for i in range(7):
            d = datetime.now() + timedelta(days=i)
            lbl = "Today" if i == 0 else "Tomorrow" if i == 1 else d.strftime("%A")
            date_opts.append(f"{d.strftime('%Y-%m-%d')} ({lbl})")
        self.add_message(f"Great choice — {movie_title}\n{detail}📅  Which date?", "bot")
        self._add_option_buttons(date_opts, lambda d: self._handle_inline_date(d))
        return ""

    def _handle_inline_date(self, date_str):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
        clean = m.group(1) if m else date_str
        self.add_message(f"📅  {date_str}", "user")
        self.booking_flow["date"] = clean
        self.booking_flow["step"] = 2
        self.quick_date_var.set(date_str)
        info = self._get_movie_info(self.booking_flow["movie"])
        times = info.get("showtimes", []) if info else ["10:00 AM","1:30 PM","4:00 PM","6:30 PM","9:00 PM"]
        self.add_message(f"📅  {clean}\n\n🕐  Which showtime?", "bot")
        self._add_option_buttons(times, lambda t: self._handle_inline_time(t))

    def _handle_inline_time(self, time_str):
        self.add_message(f"🕐  {time_str}", "user")
        self.booking_flow["time"] = time_str
        self.booking_flow["step"] = 3
        self.quick_time_var.set(time_str)
        self.add_message(f"🕐  {time_str}\n\n🎫  How many tickets? (type a number or use the spinner →)", "bot")

    def _handle_inline_theater(self, theater_name):
        self.add_message(f"🏢  {theater_name}", "user")
        self.booking_flow["theater"] = theater_name
        try: self.booking_flow["tickets"] = int(self.quick_tickets_var.get())
        except: pass
        self.booking_flow["seat_type"] = self.quick_seat_var.get() or "Standard"
        self.booking_flow["step"] = 5
        self.quick_theater_var.set(theater_name)
        summary = self.generate_booking_summary()
        self.add_message(f"🏢  {theater_name}\n\n{summary}\n\nType  confirm  to complete, or  cancel  to start over.", "bot")

    def handle_booking_flow_response(self, message):
        step = self.booking_flow["step"]

        if step == 1:
            date = self.extract_date_info(message)
            if date:
                self._handle_inline_date(date); return ""
            return "Please pick a date — type 'today', 'tomorrow', a day name, or click a button above."

        if step == 2:
            t = self.extract_time_info(message)
            if t:
                self._handle_inline_time(t); return ""
            info = self._get_movie_info(self.booking_flow["movie"])
            times = info.get("showtimes", []) if info else []
            ts = "  " + "  ·  ".join(times) if times else ""
            return f"Please type a showtime (e.g. '6:30 PM').{chr(10)+ts if ts else ''}"

        if step == 3:
            wmap = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
            ml3 = message.lower()
            count = None
            for word, val in wmap.items():
                if re.search(rf"\b{word}\b", ml3): count = val; break
            if count is None:
                m = re.search(r"\b(\d+)\b", message)
                if m: count = int(m.group(1))
            if count is not None:
                count = max(1, min(10, count))
                self.booking_flow["tickets"] = count
                self.booking_flow["step"] = 4
                self.quick_tickets_var.set(str(count))
                theaters = self._get_theaters()
                self.add_message(f"🎫  {count} ticket(s)\n\n🏢  Which theater?", "bot")
                self._add_option_buttons([t["name"] for t in theaters], lambda t: self._handle_inline_theater(t))
                return ""
            return "How many tickets? Type a number like '2' or 'two'."

        if step == 4:
            theater = self._extract_theater(message)
            if theater:
                self._handle_inline_theater(theater); return ""
            theaters = self._get_theaters()
            self.add_message("Choose a theater:", "bot")
            self._add_option_buttons([t["name"] for t in theaters], lambda t: self._handle_inline_theater(t))
            return ""

        if step == 5:
            if message.lower() in ["confirm","yes","book it","proceed","ok"]:
                return self.confirm_booking()
            if message.lower() in ["cancel","no","stop","quit"]:
                self._reset_booking_flow()
                return "Booking cancelled — let me know if you'd like to try again!"
            return self.generate_booking_summary() + "\n\nType  confirm  to book,  cancel  to start over."

        return "What film would you like to book? 🎬"

    # ─── Data helpers ──────────────────────────────────────────────────────
    def _load_movies_data(self):
        return safe_read_json(self.movies_file, {"movies": [], "theaters": []})

    def _get_movie_info(self, title):
        data = self._load_movies_data()
        return next((m for m in data.get("movies", []) if m.get("title","").lower() == title.lower()), None)

    def _get_theaters(self):
        return self._load_movies_data().get("theaters", [])

    def extract_movie_title(self, message):
        data = self._load_movies_data()
        movies = data.get("movies", [])
        noise = {"book","ticket","tickets","movie","film","watch","reserve","buy","for","a","the","please","i","want","to"}
        msg_words = [w for w in message.lower().split() if w not in noise]

        def _lev(a, b):
            if len(a) < len(b): a, b = b, a
            if not b: return len(a)
            prev = list(range(len(b)+1))
            for ca in a:
                curr = [prev[0]+1]
                for j, cb in enumerate(b):
                    curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(ca!=cb)))
                prev = curr
            return prev[-1]

        best_title, best_score = None, 0.0
        for movie in movies:
            title_words = movie.get("title","").lower().split()
            score = 0.0
            for tw in title_words:
                if tw in msg_words: score += 2
                elif len(tw) > 3 and any(_lev(tw, mw) <= 2 for mw in msg_words if len(mw) > 2): score += 1
            normalised = score / (len(title_words) * 2)
            if normalised > best_score and normalised >= 0.4:
                best_score = normalised; best_title = movie["title"]
        return best_title

    def extract_date_info(self, message):
        ml = message.lower()
        if "today" in ml: return datetime.now().strftime("%Y-%m-%d") + " (Today)"
        if "tomorrow" in ml: return (datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d") + " (Tomorrow)"
        if "weekend" in ml:
            days_ahead = (5 - datetime.now().weekday()) % 7 or 7
            d = datetime.now() + timedelta(days=days_ahead)
            return d.strftime("%Y-%m-%d") + " (Saturday)"
        for day in ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]:
            if day in ml:
                diff = (["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].index(day) - datetime.now().weekday()) % 7 or 7
                d = datetime.now() + timedelta(days=diff)
                return d.strftime("%Y-%m-%d") + f" ({day.capitalize()})"
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
        return m.group(1) if m else None

    def extract_time_info(self, message):
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", message, re.IGNORECASE)
        if m:
            hour = int(m.group(1)); minute = m.group(2) or "00"; period = m.group(3).lower()
            if period == "pm" and hour != 12: hour += 12
            elif period == "am" and hour == 12: hour = 0
            return f"{hour%12 or 12}:{minute} {'AM' if hour < 12 else 'PM'}"
        m24 = re.search(r"\b(\d{2}):(\d{2})\b", message)
        if m24:
            h, mn = int(m24.group(1)), m24.group(2)
            return f"{h%12 or 12}:{mn} {'AM' if h < 12 else 'PM'}"
        for word, val in {"morning":"10:00 AM","afternoon":"2:00 PM","evening":"6:30 PM","night":"9:00 PM"}.items():
            if word in message.lower(): return val
        return None

    def _extract_theater(self, message):
        theaters = self._get_theaters()
        ml = message.lower()
        for t in theaters:
            if t.get("name","").lower() in ml: return t["name"]
        for t in theaters:
            parts = t.get("name","").lower().split()
            if any(p in ml for p in parts if len(p) > 3): return t["name"]
        return None

    # ─── Summary & confirm ─────────────────────────────────────────────────
    def generate_booking_summary(self):
        bf = self.booking_flow
        total = self._calculate_total()
        return (
            "─" * 34 + "\n"
            "  BOOKING SUMMARY\n"
            "─" * 34 + "\n"
            f"  Film      {bf['movie']}\n"
            f"  Date      {bf['date']}\n"
            f"  Time      {bf['time']}\n"
            f"  Tickets   {bf['tickets']}\n"
            f"  Theater   {bf['theater']}\n"
            f"  Seats     {bf['seat_type']}\n"
            f"  Total     ${total:.2f}\n"
            + "─" * 34
        )

    def _calculate_total(self):
        base = self.ticket_price + (self.vip_upcharge if self.booking_flow["seat_type"] == "VIP" else 0)
        return round(base * self.booking_flow["tickets"] * (1 + self.tax_rate), 2)

    def confirm_booking(self):
        booking_id = f"BK{random.randint(10000, 99999)}"
        total = self._calculate_total()
        record = {
            "booking_id": booking_id, "username": self.current_user,
            **{k: self.booking_flow[k] for k in ("movie","date","time","tickets","theater","seat_type")},
            "total_price": total,
            "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "confirmed",
        }
        try:
            data = safe_read_json(self.bookings_file, {"bookings": []})
            if not isinstance(data.get("bookings"), list): data = {"bookings": []}
            data["bookings"].append(record)
            safe_write_json(self.bookings_file, data)
        except Exception as e:
            return f"Could not save booking: {e}"

        self._reset_booking_flow()
        self.root.after(120, lambda: messagebox.showinfo(
            "Booking Confirmed!", f"Booking {booking_id} confirmed!\n\nEnjoy the movie 🍿"))

        return (
            "─" * 34 + "\n"
            f"  ✅  CONFIRMED  —  {booking_id}\n"
            "─" * 34 + "\n"
            f"  Film      {record['movie']}\n"
            f"  Date      {record['date']}  at  {record['time']}\n"
            f"  Theater   {record['theater']}\n"
            f"  Tickets   {record['tickets']}  ({record['seat_type']})\n"
            f"  Total     ${total:.2f}\n"
            "─" * 34 + "\n\n"
            "Enjoy the show — don't forget the popcorn 🍿\n"
            "Would you like to book another film?"
        )

    # ─── Quick book (right panel) ──────────────────────────────────────────
    def quick_book_tickets(self):
        movie = self.quick_movie_var.get(); date = self.quick_date_var.get()
        showtime = self.quick_time_var.get(); theater = self.quick_theater_var.get()
        tickets = self.quick_tickets_var.get(); seat = self.quick_seat_var.get()
        missing = [f for f, v in [("Film",movie),("Date",date),("Showtime",showtime),("Theater",theater)] if not v]
        if missing:
            messagebox.showerror("Missing Fields", "Please fill in: " + ", ".join(missing)); return
        m = re.search(r"(\d{4}-\d{2}-\d{2})", date)
        date_str = m.group(1) if m else date
        self._reset_booking_flow()
        self.booking_flow.update({"step":5,"movie":movie,"date":date_str,"time":showtime,
                                   "tickets":int(tickets),"theater":theater,"seat_type":seat})
        summary = self.generate_booking_summary()
        self.add_message(f"⚡  Quick Booking\n\n{summary}\n\nType  confirm  to complete,  cancel  to reset.", "bot")

    # ─── View / Cancel bookings ────────────────────────────────────────────
    def view_my_bookings(self):
        data = safe_read_json(self.bookings_file, {"bookings": []})
        ub = [b for b in data.get("bookings", []) if b.get("username") == self.current_user]
        if not ub:
            return "No bookings yet — type 'book tickets' to make your first reservation!"
        lines = ["─"*34 + "\n  YOUR BOOKINGS  (last 5)\n" + "─"*34]
        for i, b in enumerate(ub[-5:], 1):
            icon = "✅" if b.get("status") == "confirmed" else "❌"
            lines.append(
                f"\n  {icon}  {b.get('booking_id')}  —  #{i}\n"
                f"  🎬  {b.get('movie')}\n"
                f"  📅  {b.get('date')}   🕐  {b.get('time')}\n"
                f"  🏢  {b.get('theater')}   🎫  {b.get('tickets')} ticket(s)\n"
                f"  💰  ${float(b.get('total_price',0)):.2f}   {b.get('status','confirmed').upper()}\n"
                + "  " + "·"*30
            )
        lines.append("\nTo cancel: type  cancel booking BK12345")
        return "\n".join(lines)

    def _view_bookings_to_chat(self):
        self.add_message(self.view_my_bookings(), "bot")

    def _prompt_cancel_booking(self):
        """Button on right panel — shows bookings then prompts for ID."""
        data = safe_read_json(self.bookings_file, {"bookings": []})
        ub = [b for b in data.get("bookings", []) if b.get("username") == self.current_user
              and b.get("status") == "confirmed"]
        if not ub:
            self.add_message("You have no confirmed bookings to cancel.", "bot"); return
        self.add_message("Which booking would you like to cancel?", "bot")
        opts = [f"{b['booking_id']} — {b['movie']}" for b in ub[-5:]]
        def _do_cancel(opt):
            booking_id = opt.split(" — ")[0].strip()
            result = self.handle_cancel_booking(f"cancel booking {booking_id}")
            self.add_message(result, "bot")
        self._add_option_buttons(opts, _do_cancel)

    def handle_cancel_booking(self, message):
        # ── FIX: robust BK extraction, case-insensitive ────────────────────
        m = re.search(r"\b(BK\d+)\b", message, re.IGNORECASE)
        if not m:
            return (
                "To cancel a booking, include the Booking ID — e.g.\n"
                "  cancel booking BK12345\n\n"
                "You can find your booking IDs by typing  my bookings."
            )
        booking_id = m.group(1).upper()
        data = safe_read_json(self.bookings_file, {"bookings": []})
        found = False
        for b in data.get("bookings", []):
            if b.get("booking_id","").upper() == booking_id and b.get("username") == self.current_user:
                if b.get("status") == "cancelled":
                    return f"Booking {booking_id} is already cancelled."
                b["status"] = "cancelled"
                found = True
                break
        if not found:
            return f"Booking {booking_id} not found for your account."
        try:
            safe_write_json(self.bookings_file, data)
        except Exception as e:
            return f"Error cancelling booking: {e}"
        return (
            f"✅  Booking {booking_id} cancelled.\n"
            "Refund will be processed within 5–7 business days."
        )

    # ─── Informational ─────────────────────────────────────────────────────
    def handle_show_movies(self):
        data = self._load_movies_data()
        movies = data.get("movies", [])
        if not movies: return "No films available right now — check back soon!"
        lines = ["─"*34 + "\n  NOW SHOWING\n" + "─"*34]
        for m in movies:
            ts = "  " + "  ·  ".join(m.get("showtimes",[])[:3])
            lines.append(
                f"\n  {m['title']}  ⭐ {m.get('imdb')}/10\n"
                f"  {m.get('genre')}  ·  {m.get('rating')}  ·  {m.get('duration')}\n"
                f"  {m.get('description','')}\n"
                f"{ts}\n  " + "·"*30
            )
        lines.append("\nType  book [film name]  to get started!")
        return "\n".join(lines)

    def handle_price_query(self):
        return (
            "─"*34 + "\n  TICKET PRICES\n" + "─"*34 + "\n"
            f"  Standard    ${self.ticket_price:.2f}\n"
            f"  VIP         ${self.ticket_price+self.vip_upcharge:.2f}\n"
            f"  Tax         {self.tax_rate*100:.0f}%\n"
            + "─"*34 + "\n\nWould you like to book tickets?"
        )

    def handle_recommendation(self):
        data = self._load_movies_data()
        movies = sorted(data.get("movies",[]), key=lambda x: x.get("popularity",0), reverse=True)
        gp = self.user_preferences.get("genre")
        if gp:
            pref = [m for m in movies if gp.lower() in m.get("genre","").lower()]
            if pref: movies = pref + [m for m in movies if m not in pref]
        lines = ["─"*34 + "\n  RECOMMENDED FOR YOU\n" + "─"*34]
        for i, m in enumerate(movies[:3], 1):
            lines.append(
                f"\n  {i}.  {m['title']}  ⭐ {m.get('imdb')}/10\n"
                f"      {m.get('genre')}  ·  {m.get('rating')}\n"
                f"      {m.get('description','')[:80]}…"
            )
        lines.append("\n\nWhich one catches your eye?")
        return "\n".join(lines)

    def handle_help(self):
        return (
            "─"*34 + "\n  AVAILABLE COMMANDS\n" + "─"*34 + "\n\n"
            "  BOOKING\n"
            "    book tickets for [film]\n"
            "    confirm  /  cancel\n\n"
            "  BROWSE\n"
            "    show movies\n"
            "    recommend something\n"
            "    ticket prices\n\n"
            "  MANAGE\n"
            "    my bookings\n"
            "    cancel booking BK12345\n\n"
            "  OTHER\n"
            "    help     —  this message\n"
            "    hello    —  greet me\n"
            + "─"*34
        )

    # ─── Automation callbacks ──────────────────────────────────────────────
    def toggle_automation(self):
        C = self.C
        self.automation_active = not self.automation_active
        if self.automation_active:
            self._status_lbl.config(text=" LIVE", fg=C["teal"])
            self._status_dot.config(fg=C["teal"])
            self.auto_toggle_btn.config(text="◉  AUTO-MODE  ON", bg=C["teal_dim"], fg=C["teal"])
            self.add_message("Automation enabled — smart suggestions active!", "bot")
        else:
            self._status_lbl.config(text=" PAUSED", fg=C["gold_dim"])
            self._status_dot.config(fg=C["gold_dim"])
            self.auto_toggle_btn.config(text="○  AUTO-MODE  OFF", bg=C["bg_card"], fg=C["text_mid"])
            self.add_message("Automation paused.", "bot")

    def auto_book_movie(self):
        data = self._load_movies_data()
        movies = sorted(data.get("movies",[]), key=lambda x: x.get("popularity",0), reverse=True)
        if not movies: self.add_message("No films available right now.", "bot"); return
        best = movies[0]
        self.add_message(
            f"⚡  AUTO-BOOKING SUGGESTION\n\n"
            f"  Most popular:  {best['title']}\n"
            f"  {best.get('genre')}  ·  ⭐ {best.get('imdb')}/10\n\n"
            f"  Suggested:  Tomorrow at 6:30 PM @ City Center Cinemas\n\n"
            f"Type  book {best['title']}  or use the form to proceed!", "bot")

    def smart_suggestions(self):
        self.add_message(self._random_suggestion(), "bot")

    def auto_schedule(self):
        self.add_message(
            "📅  SCHEDULING TIPS\n\n"
            "  · Book 2–3 days ahead for best seat selection\n"
            "  · Peak: 6:30 PM – 9:00 PM  Fri–Sun\n"
            "  · Quieter: weekday matinees\n\n"
            "Want me to find a slot for this weekend?", "bot")

    def quick_fill_booking(self):
        self.add_message(
            "▶  QUICK FILL GUIDE\n\n"
            "  1.  Choose Film, Date, Showtime & Theater in the panel →\n"
            "  2.  Click  BOOK TICKETS\n"
            "  3.  Type  confirm  in chat to complete\n\n"
            "Give it a try!", "bot")

    def learn_preferences(self):
        genre = self.user_preferences.get("genre") or "not set"
        tod   = self.user_preferences.get("time_preference") or "evening"
        self.add_message(
            f"◎  YOUR PREFERENCES\n\n"
            f"  Favourite genre   {genre}\n"
            f"  Preferred time    {tod}\n\n"
            "I use these for better recommendations.\n"
            "Keep chatting — I keep learning.", "bot")

    # ─── Chat display ──────────────────────────────────────────────────────
    def add_message(self, message, sender="user"):
        C = self.C
        self.chat_display.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M")

        # draw bubble background via a full-width frame embedded in the text widget
        bubble_bg = C["bg_msg_usr"] if sender == "user" else C["bg_msg_bot"]
        bubble_fg_label = C["text_user"] if sender == "user" else C["gold"]
        label_text = f" ▸ YOU  {ts} " if sender == "user" else f" ◈ CINEBOOK  {ts} "
        label_tag  = "usr_label" if sender == "user" else "bot_label"
        msg_tag    = "usr_msg"   if sender == "user" else "bot_msg"

        # spacer
        self.chat_display.insert(tk.END, "\n")

        # label row embedded as a coloured frame
        lbl_frame = tk.Frame(self.chat_display, bg=bubble_bg, pady=2)
        tk.Label(lbl_frame, text=label_text, font=("Courier", 8, "bold"),
                 bg=bubble_bg, fg=bubble_fg_label, padx=10).pack(side=tk.LEFT)
        self.chat_display.window_create(tk.END, window=lbl_frame)
        self.chat_display.insert(tk.END, "\n")

        # message text
        self.chat_display.insert(tk.END, f"{message}\n", msg_tag)

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.conversation_history.append({"timestamp": ts, "sender": sender, "message": message})

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("🎬  Starting CineBook — AI Concierge…")
    app = AutomatedMovieChatbot()
    app.run()