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

# ─────────────────────────────────────────────────────────────
# FIX #1: Removed `import time` — time.sleep() was being called
#          on the main thread, freezing the entire UI. All delays
#          now use root.after() (non-blocking).
# ─────────────────────────────────────────────────────────────


# ── Safe JSON helpers ────────────────────────────────────────────────────────
# These replace all bare open/json.load/json.dump calls on data files.
# safe_read_json  : never raises — returns `default` if file is missing OR corrupt.
# safe_write_json : atomic write via temp-file + os.replace, so a crash mid-write
#                   cannot leave a half-written (corrupt) file behind.

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
        os.replace(tmp_path, filepath)          # atomic on Windows & POSIX
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
# ────────────────────────────────────────────────────────────────────────────


class AutomatedMovieChatbot:
    def __init__(self):
        # Data files
        self.movies_file = "movies.json"
        self.bookings_file = "bookings.json"
        self.preferences_file = "preferences.json"

        # State
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

        # Automation
        self.automation_active = True
        self.suggestions_queue = queue.Queue()

        # Booking flow  (step 0 = idle … 5 = awaiting confirm)
        self._reset_booking_flow()

        # Pricing
        self.ticket_price = 12.50
        self.vip_upcharge = 5.00
        self.tax_rate = 0.08

        # Initialize data & preferences
        self.initialize_data()
        self.load_user_preferences()

        # Build UI
        self.create_gui()

        # Start background threads AFTER root exists
        self.start_automation()

        # Greet after 1 second (non-blocking)
        self.root.after(1000, self.auto_greeting)

    # ──────────────────────────────────────────────
    # FIX #2: Centralised booking-flow reset
    # ──────────────────────────────────────────────
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

    # ──────────────────────────────────────────────
    # Data initialisation
    # ──────────────────────────────────────────────
    def initialize_data(self):
        """Create sample JSON files if they don't exist."""
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

        # Auto-repair bookings file if missing or corrupt
        bdata = safe_read_json(self.bookings_file, None)
        if bdata is None or not isinstance(bdata.get("bookings"), list):
            safe_write_json(self.bookings_file, {"bookings": []})

        # Auto-repair preferences file if missing or corrupt
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
            pass   # non-critical — preferences will just not persist this save

    # ──────────────────────────────────────────────
    # GUI construction
    # ──────────────────────────────────────────────
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("🎬 AI Movie Booking Assistant")
        self.root.geometry("1200x820")
        self.root.configure(bg="#0d1117")
        self.root.resizable(True, True)

        # ── Style ttk widgets ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground="#21262d",
                        background="#21262d",
                        foreground="#c9d1d9",
                        selectbackground="#1f6feb",
                        selectforeground="#ffffff")
        style.map("TCombobox", fieldbackground=[("readonly", "#21262d")])

        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

        # Text tags (must run after root exists)
        self.chat_display.tag_config("user_tag", foreground="#58a6ff",
                                     font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#c9d1d9")
        self.chat_display.tag_config("bot_tag", foreground="#f0883e",
                                     font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("bot_msg", foreground="#c9d1d9")
        # FIX #3: error_tag was missing — used in error messages
        self.chat_display.tag_config("error_tag", foreground="#f85149")

    def _build_left_panel(self):
        left = tk.Frame(self.root, bg="#161b22")
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(left, bg="#161b22")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.automation_status = tk.Label(
            header,
            text="🤖 AI: ONLINE  |  🚀 AUTO-MODE: ACTIVE",
            font=("Segoe UI", 10, "bold"),
            bg="#161b22",
            fg="#3fb950",
        )
        self.automation_status.pack(side=tk.LEFT)

        tk.Label(header, text=f"👤 {self.current_user}",
                 font=("Segoe UI", 10), bg="#161b22", fg="#c9d1d9").pack(side=tk.RIGHT)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            left,
            font=("Segoe UI", 11),
            bg="#0d1117",
            fg="#c9d1d9",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            state=tk.DISABLED,
        )
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=10)

        # Thinking indicator
        self.thinking_indicator = tk.Label(
            left, text="", font=("Segoe UI", 9, "italic"),
            bg="#161b22", fg="#8b949e"
        )
        self.thinking_indicator.grid(row=2, column=0, sticky="w", padx=10, pady=(2, 0))

        # AI Suggestions bar
        sug_frame = tk.Frame(left, bg="#1c2128", bd=0)
        sug_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        tk.Label(sug_frame, text="💡 AI Suggestion: ", font=("Segoe UI", 9, "bold"),
                 bg="#1c2128", fg="#58a6ff").pack(side=tk.LEFT, padx=5)

        self.suggestions_text = tk.Label(
            sug_frame, text="Analyzing your preferences…",
            font=("Segoe UI", 9), bg="#1c2128", fg="#8b949e",
            anchor="w"
        )
        self.suggestions_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=4)

        # Quick-action buttons
        btn_frame = tk.Frame(left, bg="#161b22")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 6))

        actions = [
            ("🚀 Auto-Book", self.auto_book_movie, "#1f6feb"),
            ("⭐ Smart Suggest", self.smart_suggestions, "#1f6feb"),
            ("📅 Auto-Schedule", self.auto_schedule, "#1f6feb"),
            ("⚡ Quick Fill", self.quick_fill_booking, "#238636"),
            ("🔄 Learn Prefs", self.learn_preferences, "#238636"),
        ]
        for text, cmd, color in actions:
            tk.Button(btn_frame, text=text, command=cmd,
                      bg=color, fg="#ffffff",
                      font=("Segoe UI", 9), relief=tk.FLAT,
                      cursor="hand2", padx=8, pady=4
                      ).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = tk.Frame(left, bg="#161b22")
        input_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.user_input = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            bg="#21262d", fg="#c9d1d9",
            insertbackground="#c9d1d9",
            relief=tk.FLAT,
        )
        self.user_input.grid(row=0, column=0, sticky="ew", ipady=6)
        self.user_input.bind("<Return>", lambda e: self.process_input())

        tk.Button(
            input_frame, text="  Send  ",
            command=self.process_input,
            bg="#238636", fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
        ).grid(row=0, column=1, padx=(6, 0), ipady=6)

    def _build_right_panel(self):
        right = tk.Frame(self.root, bg="#161b22")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)

        # Title
        tk.Label(right, text="🤖 AUTOMATION CONTROLS",
                 font=("Segoe UI", 12, "bold"),
                 bg="#161b22", fg="#58a6ff").pack(padx=10, pady=(10, 6))

        # Toggle automation
        self.auto_toggle_btn = tk.Button(
            right, text="✅ Automation: ON",
            command=self.toggle_automation,
            bg="#238636", fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
        )
        self.auto_toggle_btn.pack(fill=tk.X, padx=10, pady=4)

        # Booking status
        self.booking_status = tk.Label(
            right, text="📝 No active booking",
            font=("Segoe UI", 9),
            bg="#161b22", fg="#8b949e",
            justify=tk.LEFT, wraplength=240,
        )
        self.booking_status.pack(fill=tk.X, padx=10, pady=4)

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)

        # ── Quick booking form ──
        tk.Label(right, text="⚡ QUICK BOOKING",
                 font=("Segoe UI", 11, "bold"),
                 bg="#161b22", fg="#58a6ff").pack(padx=10, pady=(0, 6))

        form = tk.Frame(right, bg="#161b22")
        form.pack(fill=tk.X, padx=10)

        def label(text):
            tk.Label(form, text=text, font=("Segoe UI", 9),
                     bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(6, 0))

        label("🎬 Movie:")
        self.quick_movie_var = tk.StringVar()
        self.quick_movie_combo = ttk.Combobox(form, textvariable=self.quick_movie_var,
                                               state="readonly", font=("Segoe UI", 10))
        self.quick_movie_combo.pack(fill=tk.X)
        # ── Binding: selecting a movie from dropdown starts/updates the booking flow
        self.quick_movie_combo.bind("<<ComboboxSelected>>",
                                    lambda e: self._combo_select_movie())

        label("📅 Date:")
        self.quick_date_var = tk.StringVar()
        self.quick_date_combo = ttk.Combobox(form, textvariable=self.quick_date_var,
                                              state="readonly", font=("Segoe UI", 10))
        self.quick_date_combo.pack(fill=tk.X)
        # ── Binding: selecting a date advances step 1 → 2
        self.quick_date_combo.bind("<<ComboboxSelected>>",
                                   lambda e: self._combo_select_date())

        label("🕐 Showtime:")
        self.quick_time_var = tk.StringVar()
        self.quick_time_combo = ttk.Combobox(form, textvariable=self.quick_time_var,
                                              state="readonly", font=("Segoe UI", 10))
        self.quick_time_combo.pack(fill=tk.X)
        # ── Binding: selecting a time advances step 2 → 3
        self.quick_time_combo.bind("<<ComboboxSelected>>",
                                   lambda e: self._combo_select_time())

        label("🏢 Theater:")
        self.quick_theater_var = tk.StringVar()
        self.quick_theater_combo = ttk.Combobox(form, textvariable=self.quick_theater_var,
                                                 state="readonly", font=("Segoe UI", 10))
        self.quick_theater_combo.pack(fill=tk.X)
        # ── Binding: selecting a theater advances step 3 or 4
        self.quick_theater_combo.bind("<<ComboboxSelected>>",
                                      lambda e: self._combo_select_theater())

        # Tickets row
        tk.Label(form, text="🎫 Tickets:", font=("Segoe UI", 9),
                 bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(6, 0))
        tk_row = tk.Frame(form, bg="#161b22")
        tk_row.pack(fill=tk.X)
        self.quick_tickets_var = tk.StringVar(value="1")
        tk.Spinbox(tk_row, from_=1, to=10, textvariable=self.quick_tickets_var,
                   font=("Segoe UI", 10), bg="#21262d", fg="#c9d1d9",
                   buttonbackground="#21262d", width=5).pack(side=tk.LEFT)

        # Seat type
        tk.Label(form, text="💺 Seat Type:", font=("Segoe UI", 9),
                 bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(6, 0))
        self.quick_seat_var = tk.StringVar(value="Standard")
        seat_row = tk.Frame(form, bg="#161b22")
        seat_row.pack(fill=tk.X)
        for seat in ("Standard", "VIP"):
            tk.Radiobutton(seat_row, text=seat, variable=self.quick_seat_var,
                           value=seat, bg="#161b22", fg="#c9d1d9",
                           selectcolor="#0d1117",
                           activebackground="#161b22").pack(side=tk.LEFT, padx=4)

        # Buttons
        tk.Button(form, text="🎫 Quick Book",
                  command=self.quick_book_tickets,
                  bg="#e34c26", fg="#ffffff",
                  font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2").pack(fill=tk.X, pady=(12, 4))

        tk.Button(form, text="📋 View My Bookings",
                  command=self._view_bookings_to_chat,
                  bg="#1f6feb", fg="#ffffff",
                  font=("Segoe UI", 10),
                  relief=tk.FLAT, cursor="hand2").pack(fill=tk.X, pady=4)

        self.update_quick_form()

    # ──────────────────────────────────────────────
    # Background threads
    # ──────────────────────────────────────────────
    def start_automation(self):
        threading.Thread(target=self._suggestion_loop, daemon=True).start()
        threading.Thread(target=self._status_loop, daemon=True).start()

    def _suggestion_loop(self):
        """Generate a suggestion every 12 s and push to queue."""
        import time
        while True:
            time.sleep(12)
            if self.automation_active:
                self.suggestions_queue.put(self._random_suggestion())

    def _status_loop(self):
        """Schedule UI refresh on the main thread every 4 s."""
        import time
        while True:
            time.sleep(4)
            # FIX #4: Use root.after to marshal back to main thread safely
            self.root.after(0, self._refresh_ui)

    def _refresh_ui(self):
        """Called on main thread — safe to touch widgets."""
        # Suggestions
        try:
            while not self.suggestions_queue.empty():
                msg = self.suggestions_queue.get_nowait()
                self.suggestions_text.config(text=msg)
        except queue.Empty:
            pass

        # Booking status label
        bf = self.booking_flow
        if bf["step"] > 0:
            lines = [f"📝 Booking in progress (Step {bf['step']}/5)"]
            if bf["movie"]:
                lines.append(f"🎬 {bf['movie']}")
            if bf["date"]:
                lines.append(f"📅 {bf['date']}")
            if bf["time"]:
                lines.append(f"🕐 {bf['time']}")
            self.booking_status.config(text="\n".join(lines), fg="#58a6ff")
        else:
            self.booking_status.config(text="📝 No active booking", fg="#8b949e")

    # ──────────────────────────────────────────────
    # Quick form helpers
    # ──────────────────────────────────────────────
    def update_quick_form(self):
        """Populate all combo boxes."""
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

        # FIX #5: Theater combo was missing from original quick form
        self.quick_theater_combo["values"] = [t["name"] for t in theaters]

    # ──────────────────────────────────────────────
    # ComboboxSelected handlers — bridge form ↔ chat
    # ──────────────────────────────────────────────
    def _combo_select_movie(self):
        """User picked a movie from the dropdown → start/update booking flow."""
        movie = self.quick_movie_var.get()
        if not movie:
            return
        # If no active flow, start one
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
            # Update movie in existing flow
            self.booking_flow["movie"] = movie
            self.add_message(f"🎬 Movie updated to **{movie}**.", "bot")

    def _combo_select_date(self):
        """User picked a date from the dropdown → advance to step 2."""
        raw = self.quick_date_var.get()
        if not raw:
            return
        # Ensure a movie is selected first
        if not self.booking_flow["movie"]:
            movie = self.quick_movie_var.get()
            if not movie:
                self.add_message("⚠️ Please select a Movie first.", "bot")
                return
            self._reset_booking_flow()
            self.booking_flow["step"] = 1
            self.booking_flow["movie"] = movie

        import re as _re
        m = _re.search(r"(\d{4}-\d{2}-\d{2})", raw)
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
        """User picked a showtime → advance to step 3."""
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
        """User picked a theater → advance to step 4/5."""
        theater = self.quick_theater_var.get()
        if not theater:
            return
        if not self.booking_flow["time"]:
            self.add_message("⚠️ Please select a Showtime first.", "bot")
            return

        self.booking_flow["theater"] = theater
        # Also grab tickets & seat from form
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

    # ──────────────────────────────────────────────
    # Inline chat option buttons
    # ──────────────────────────────────────────────
    def _add_option_buttons(self, options, callback):
        """
        Insert a row of clickable option buttons into the chat area.
        Clicking a button calls callback(option_text) and removes the row.
        """
        self.chat_display.config(state=tk.NORMAL)

        btn_frame = tk.Frame(self.chat_display, bg="#1c2128")

        def make_handler(opt, frame):
            def handler():
                frame.destroy()
                callback(opt)
            return handler

        for opt in options:
            btn = tk.Button(
                btn_frame,
                text=opt,
                command=make_handler(opt, btn_frame),
                bg="#1f6feb",
                fg="#ffffff",
                font=("Segoe UI", 9),
                relief=tk.FLAT,
                cursor="hand2",
                padx=6,
                pady=3,
            )
            btn.pack(side=tk.LEFT, padx=3, pady=4)

        self.chat_display.window_create(tk.END, window=btn_frame)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)


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

    # ──────────────────────────────────────────────
    # Input processing
    # ──────────────────────────────────────────────
    def process_input(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.user_input.delete(0, tk.END)
        self.add_message(user_text, "user")
        self.learn_from_input(user_text)

        # FIX #6: Removed time.sleep() here — was freezing the UI.
        # Show thinking indicator without blocking, then schedule response.
        self.thinking_indicator.config(text="🤖 Thinking…")
        self.root.after(300, lambda: self._deliver_response(user_text))

    def _deliver_response(self, user_text):
        response = self.understand_and_respond(user_text)
        # Button-driven handlers add messages themselves and return ""
        # Only add to chat if there's actual content to show
        if response:
            self.add_message(response, "bot")
        self.thinking_indicator.config(text="")

    # ──────────────────────────────────────────────
    # Preference learning
    # ──────────────────────────────────────────────
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

    # ──────────────────────────────────────────────
    # Intent router
    # ──────────────────────────────────────────────
    def understand_and_respond(self, message):
        ml = message.lower()

        # ── FIX: Active booking flow is checked FIRST ──────────────────────
        # Previously intents were checked first, so typing "2 tickets" during
        # step 3 triggered handle_book_ticket() instead of the flow handler,
        # breaking the entire conversation.  Only "cancel" and explicit new-movie
        # requests are allowed to escape the flow.
        if self.booking_flow["step"] > 0:
            # Allow user to explicitly abort
            if any(w in ml for w in ["cancel", "stop", "quit", "restart", "start over"]):
                self._reset_booking_flow()
                return "Booking cancelled. What else can I help you with? 😊"
            # Allow user to ask for help mid-flow without losing progress
            if ml.strip() in ["help", "?"]:
                return self.handle_help()
            return self.handle_booking_flow_response(message)
        # ───────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────
    # Booking handlers
    # ──────────────────────────────────────────────
    def handle_book_ticket(self, message):
        movie_title = self.extract_movie_title(message)

        # Warn if a different movie booking is already in progress
        if self.booking_flow["step"] > 0 and movie_title and movie_title != self.booking_flow.get("movie"):
            self._reset_booking_flow()
            self.add_message("⚠️ Previous booking cleared. Starting a new one…", "bot")

        if not movie_title:
            data = self._load_movies_data()
            titles = [m["title"] for m in data.get("movies", [])]
            self.add_message("🎬 Which movie would you like to book?", "bot")
            self._add_option_buttons(titles, lambda t: self._deliver_response(f"book {t}"))
            return ""  # message already sent

        self._reset_booking_flow()
        self.booking_flow["step"] = 1
        self.booking_flow["movie"] = movie_title
        self.quick_movie_var.set(movie_title)

        info = self._get_movie_info(movie_title)
        detail = ""
        if info:
            detail = (f"Genre: {info.get('genre')} | Rating: {info.get('rating')} | "
                      f"Duration: {info.get('duration')}\n\n")

        from datetime import datetime as _dt, timedelta as _td
        date_opts = []
        for i in range(7):
            d = _dt.now() + _td(days=i)
            lbl = "Today" if i == 0 else "Tomorrow" if i == 1 else d.strftime("%A")
            date_opts.append(f"{d.strftime('%Y-%m-%d')} ({lbl})")

        self.add_message(
            f"Great choice! 🎬 **{movie_title}**\n{detail}"
            "📅 **Which date?** Click a button or type it in chat:",
            "bot"
        )
        self._add_option_buttons(date_opts, lambda d: self._handle_inline_date(d))
        return ""  # message already sent

    def _handle_inline_date(self, date_str):
        """Called when user clicks a date button or when typed date is resolved."""
        import re as _re
        m = _re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
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
        """Called when user clicks a showtime button or types a valid time."""
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
        """Called when user clicks a theater button or types a theater name."""
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

        if step == 1:   # Waiting for typed date
            date = self.extract_date_info(message)
            if date:
                self._handle_inline_date(date)
                return ""
            return (
                "Please pick a date:\n"
                "  • Type 'today', 'tomorrow', or a day name (e.g. 'Friday')\n"
                "  • Or click one of the date buttons above"
            )

        if step == 2:   # Waiting for typed time
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

        if step == 3:   # Waiting for ticket count
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
                self.add_message(
                    f"🎫 **{count} ticket(s)** added.\n\n🏢 **Which theater?**",
                    "bot"
                )
                self._add_option_buttons(theater_names, lambda t: self._handle_inline_theater(t))
                return ""

            return "Please tell me how many tickets — type a number like '2' or 'two'."

        if step == 4:   # Waiting for typed theater name
            theater = self._extract_theater(message)
            if theater:
                self._handle_inline_theater(theater)
                return ""
            theaters = self._get_theaters()
            theater_names = [t["name"] for t in theaters]
            self.add_message("Please choose a theater:", "bot")
            self._add_option_buttons(theater_names, lambda t: self._handle_inline_theater(t))
            return ""

        if step == 5:   # Waiting for confirm / cancel
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



    # ──────────────────────────────────────────────
    # Data helpers
    # ──────────────────────────────────────────────
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
        """
        Match a movie title from free-form text.
        Handles: exact matches, partial names, extra words ('movie', 'film'),
        and typos via per-word Levenshtein distance (max 2 edits).
        """
        data = self._load_movies_data()
        movies = data.get("movies", [])

        # Strip common noise words so they don't skew scoring
        noise = {"book", "ticket", "tickets", "movie", "film", "watch",
                 "reserve", "buy", "for", "a", "the", "please", "i", "want", "to"}
        msg_words = [w for w in message.lower().split() if w not in noise]

        def _lev(a, b):
            """Levenshtein distance between two strings."""
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
                    score += 2          # exact word match — full points
                elif len(tw) > 3 and any(
                    _lev(tw, mw) <= 2 for mw in msg_words if len(mw) > 2
                ):
                    score += 1          # close-enough typo — half points

            normalised = score / (len(title_words) * 2)

            # Require at least 40% of title words to match (exact or fuzzy)
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
            # Next Saturday
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
        # FIX #7: Also try to parse YYYY-MM-DD directly from message
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
        if m:
            return m.group(1)
        return None

    def extract_time_info(self, message):
        # Match patterns like 6:30 PM, 6pm, 18:30
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

        # 24-hour
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
        # FIX #8: Also match by partial name / location keyword
        for t in theaters:
            parts = t.get("name", "").lower().split()
            if any(p in ml for p in parts if len(p) > 3):
                return t["name"]
        return None

    # ──────────────────────────────────────────────
    # Booking summary & confirmation
    # ──────────────────────────────────────────────
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
            # safe_read_json returns {"bookings":[]} if file is missing OR corrupt —
            # this is what was causing "Extra data: line 17 column 2" errors.
            data = safe_read_json(self.bookings_file, {"bookings": []})
            if not isinstance(data.get("bookings"), list):
                data = {"bookings": []}          # recover from structural corruption
            data["bookings"].append(record)
            safe_write_json(self.bookings_file, data)   # atomic — no partial writes
        except Exception as e:
            return f"❌ Could not save booking: {e}\nPlease try again."

        self._reset_booking_flow()

        # FIX #9: messagebox called AFTER resetting state so re-entrancy is safe
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

    # ──────────────────────────────────────────────
    # Quick Book (from right-panel form)
    # ──────────────────────────────────────────────
    def quick_book_tickets(self):
        movie = self.quick_movie_var.get()
        date = self.quick_date_var.get()
        showtime = self.quick_time_var.get()
        theater = self.quick_theater_var.get()
        tickets = self.quick_tickets_var.get()
        seat = self.quick_seat_var.get()

        # FIX #10: Validate ALL fields (theater was not validated before)
        missing = [f for f, v in [("Movie", movie), ("Date", date),
                                   ("Showtime", showtime), ("Theater", theater)] if not v]
        if missing:
            messagebox.showerror("Missing Fields",
                                 "Please fill in: " + ", ".join(missing))
            return

        # Parse date string — strip the "(Today)" etc. label
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

    # ──────────────────────────────────────────────
    # View / Cancel bookings
    # ──────────────────────────────────────────────
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

    # ──────────────────────────────────────────────
    # Informational handlers
    # ──────────────────────────────────────────────
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

        # Personalise if genre preference known
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
                f"   {m.get('description', '')[:90]}…\n"
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

    # ──────────────────────────────────────────────
    # Automation button callbacks
    # ──────────────────────────────────────────────
    def toggle_automation(self):
        self.automation_active = not self.automation_active
        if self.automation_active:
            self.automation_status.config(
                text="🤖 AI: ONLINE  |  🚀 AUTO-MODE: ACTIVE", fg="#3fb950")
            self.auto_toggle_btn.config(text="✅ Automation: ON", bg="#238636")
            self.add_message("Automation enabled — I'll offer smart suggestions! 🚀", "bot")
        else:
            self.automation_status.config(
                text="🤖 AI: ONLINE  |  ⏸ AUTO-MODE: OFF", fg="#da3633")
            self.auto_toggle_btn.config(text="⏸ Automation: OFF", bg="#6e3630")
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
            f"🚀 **AUTO-BOOKING SUGGESTION**\n\n"
            f"Most popular right now: **{best['title']}**\n"
            f"Genre: {best.get('genre')} | ⭐ {best.get('imdb')}/10\n\n"
            f"Suggested: Tomorrow at 6:30 PM @ City Center Cinemas\n\n"
            f"Type 'book {best['title']}' or fill the form to proceed!",
            "bot"
        )

    def smart_suggestions(self):
        self.add_message(f"💡 {self._random_suggestion()}", "bot")

    def auto_schedule(self):
        self.add_message(
            "📅 **AUTO-SCHEDULE TIPS**\n\n"
            "• Book 2–3 days ahead for best seat selection\n"
            "• Peak times: 6:30 PM – 9:00 PM (Fri–Sun)\n"
            "• Quieter slots: weekday matinees\n\n"
            "Want me to find a slot for this weekend?",
            "bot"
        )

    def quick_fill_booking(self):
        self.add_message(
            "⚡ **QUICK FILL GUIDE**\n\n"
            "1. Choose Movie, Date, Showtime & Theater from the form →\n"
            "2. Click **Quick Book**\n"
            "3. Type **confirm** in chat to complete\n\n"
            "Give it a try!",
            "bot"
        )

    def learn_preferences(self):
        genre = self.user_preferences.get("genre") or "not set yet"
        tod = self.user_preferences.get("time_preference") or "evening"
        self.add_message(
            f"🔄 **YOUR PREFERENCES**\n\n"
            f"Favourite genre: {genre}\n"
            f"Preferred time:  {tod}\n\n"
            "I'll use these to give better recommendations. "
            "Keep chatting and I'll keep learning! 📚",
            "bot"
        )

    # ──────────────────────────────────────────────
    # Suggestion engine
    # ──────────────────────────────────────────────
    def _random_suggestion(self):
        data = self._load_movies_data()
        movies = data.get("movies", [])
        tips = [
            "Try 'show movies' to see what's playing!",
            "Use the Quick Booking form for the fastest checkout →",
            "'recommend something' — let me pick for you!",
            "Type 'ticket prices' to see current rates.",
            "You can cancel any booking by its ID anytime.",
        ]
        if movies:
            top = max(movies, key=lambda x: x.get("popularity", 0))
            tips.append(f"Trending now: **{top['title']}** — book before it sells out!")
        genre = self.user_preferences.get("genre")
        if genre:
            match = next((m for m in movies if genre.lower() in m.get("genre","").lower()), None)
            if match:
                tips.append(f"You like {genre} — check out **{match['title']}**!")
        return random.choice(tips)

    # ──────────────────────────────────────────────
    # Chat display
    # ──────────────────────────────────────────────
    def add_message(self, message, sender="user"):
        self.chat_display.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M")

        if sender == "user":
            self.chat_display.insert(tk.END, f"\n[{ts}] 👤 You:\n", "user_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_display.insert(tk.END, f"\n[{ts}] 🤖 AI:\n", "bot_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "bot_msg")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

        self.conversation_history.append({
            "timestamp": ts, "sender": sender, "message": message
        })

    # ──────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("Starting AI Movie Booking Assistant…")
    app = AutomatedMovieChatbot()
    app.run()