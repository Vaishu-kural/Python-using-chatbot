import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime, timedelta
import re
import random
import time
import threading
from collections import defaultdict
import queue

class AutomatedMovieChatbot:
    def __init__(self):
        # Initialize data files
        self.movies_file = "movies.json"
        self.bookings_file = "bookings.json"
        self.users_file = "users.json"
        self.preferences_file = "preferences.json"
        
        # Current state
        self.current_user = "guest"
        self.conversation_history = []
        self.context = defaultdict(lambda: None)
        self.user_preferences = {
            "genre": None,
            "time_preference": "evening",
            "theater_preference": None,
            "seat_type": "Standard",
            "favorite_movies": []
        }
        
        # Automation state
        self.automation_active = True
        self.suggestions_queue = queue.Queue()
        self.auto_booking_mode = False
        self.reminder_timer = None
        
        # Booking flow state
        self.booking_flow = {
            "step": 0,  # 0: idle, 1: movie selected, 2: date selected, 3: time selected, 4: tickets selected, 5: theater selected, 6: confirmation
            "movie": None,
            "date": None,
            "time": None,
            "tickets": 1,
            "theater": None,
            "seat_type": "Standard",
            "auto_fill": False
        }
        
        # Pricing
        self.ticket_price = 12.50
        self.vip_upcharge = 5.00
        self.tax_rate = 0.08
        
        # Load or create data
        self.initialize_data()
        self.load_user_preferences()
        
        # Create GUI
        self.create_gui()
        
        # Start automation threads
        self.start_automation()
        
        # Start conversation
        self.root.after(1000, self.auto_greeting)
    
    def initialize_data(self):
        """Initialize data files with sample data"""
        # Movies data
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
                        "showtimes": ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
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
                        "showtimes": ["11:00 AM", "2:30 PM", "5:00 PM", "8:30 PM"]
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
                        "showtimes": ["12:00 PM", "3:30 PM", "7:00 PM", "10:00 PM"]
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
                        "showtimes": ["1:00 PM", "4:30 PM", "9:00 PM"]
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
                        "showtimes": ["10:30 AM", "2:00 PM", "5:30 PM", "9:30 PM"]
                    }
                ],
                "theaters": [
                    {"id": 1, "name": "City Center Cinemas", "location": "Downtown", "vip": True, "popularity": 95},
                    {"id": 2, "name": "Starlight Theater", "location": "Westside Mall", "vip": True, "popularity": 88},
                    {"id": 3, "name": "Grand Arena", "location": "Eastgate Complex", "vip": False, "popularity": 82},
                    {"id": 4, "name": "Royal IMAX", "location": "North Plaza", "vip": True, "popularity": 92}
                ]
            }
            with open(self.movies_file, 'w') as f:
                json.dump(movies_data, f, indent=4)
        
        # Bookings data
        if not os.path.exists(self.bookings_file):
            with open(self.bookings_file, 'w') as f:
                json.dump({"bookings": []}, f, indent=4)
        
        # Preferences data
        if not os.path.exists(self.preferences_file):
            with open(self.preferences_file, 'w') as f:
                json.dump({"preferences": {}}, f, indent=4)
    
    def load_user_preferences(self):
        """Load user preferences from file"""
        try:
            with open(self.preferences_file, 'r') as f:
                data = json.load(f)
            
            if self.current_user in data.get("preferences", {}):
                self.user_preferences = data["preferences"][self.current_user]
        except:
            pass
    
    def save_user_preferences(self):
        """Save user preferences to file"""
        try:
            with open(self.preferences_file, 'r') as f:
                data = json.load(f)
        except:
            data = {"preferences": {}}
        
        data["preferences"][self.current_user] = self.user_preferences
        
        with open(self.preferences_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def create_gui(self):
        """Create the automated GUI"""
        self.root = tk.Tk()
        self.root.title("🤖 Automated AI Movie Booking Chatbot")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0d1117")
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Left panel - Chat interface
        left_frame = tk.Frame(self.root, bg="#161b22")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Chat header
        header_frame = tk.Frame(left_frame, bg="#161b22")
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.automation_status = tk.Label(
            header_frame,
            text="🤖 AI: ONLINE | 🚀 AUTO-MODE: ACTIVE",
            font=("Segoe UI", 10, "bold"),
            bg="#161b22",
            fg="#3fb950"
        )
        self.automation_status.pack(side=tk.LEFT)
        
        self.user_label = tk.Label(
            header_frame,
            text=f"👤 {self.current_user}",
            font=("Segoe UI", 10),
            bg="#161b22",
            fg="#c9d1d9"
        )
        self.user_label.pack(side=tk.RIGHT)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            left_frame,
            height=22,
            font=("Segoe UI", 11),
            bg="#0d1117",
            fg="#c9d1d9",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)
        
        # Thinking indicator
        self.thinking_indicator = tk.Label(
            left_frame,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg="#0d1117",
            fg="#8b949e"
        )
        self.thinking_indicator.pack(padx=10, pady=(0, 5))
        
        # Suggestions panel
        suggestions_frame = tk.Frame(left_frame, bg="#161b22")
        suggestions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(
            suggestions_frame,
            text="🤔 AI Suggestions:",
            font=("Segoe UI", 9, "bold"),
            bg="#161b22",
            fg="#58a6ff"
        ).pack(anchor=tk.W)
        
        self.suggestions_text = tk.Label(
            suggestions_frame,
            text="Analyzing your preferences...",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#8b949e",
            justify=tk.LEFT,
            wraplength=600
        )
        self.suggestions_text.pack(fill=tk.X, pady=(5, 0))
        
        # Quick action buttons
        quick_actions = [
            ("🚀 Auto-Book", self.auto_book_movie),
            ("🎬 Smart Suggest", self.smart_suggestions),
            ("📅 Auto-Schedule", self.auto_schedule),
            ("⚡ Quick Fill", self.quick_fill_booking),
            ("🔄 Learn Preferences", self.learn_preferences)
        ]
        
        quick_frame = tk.Frame(left_frame, bg="#161b22")
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        for text, command in quick_actions:
            btn = tk.Button(
                quick_frame,
                text=text,
                command=command,
                bg="#1f6feb",
                fg="#ffffff",
                font=("Segoe UI", 9),
                relief=tk.FLAT,
                cursor="hand2",
                padx=10
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Input area
        input_frame = tk.Frame(left_frame, bg="#161b22")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.user_input = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            bg="#21262d",
            fg="#c9d1d9",
            insertbackground="#c9d1d9",
            relief=tk.FLAT
        )
        self.user_input.pack(fill=tk.X, pady=(0, 5))
        self.user_input.bind("<Return>", lambda e: self.process_input())
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="🤖 Send & Learn",
            command=self.process_input,
            bg="#238636",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30
        )
        send_btn.pack(pady=5)
        
        # Right panel - Automation dashboard
        right_frame = tk.Frame(self.root, bg="#161b22")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        # Automation controls
        controls_frame = tk.Frame(right_frame, bg="#161b22")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            controls_frame,
            text="🤖 AUTOMATION CONTROLS",
            font=("Segoe UI", 12, "bold"),
            bg="#161b22",
            fg="#58a6ff"
        ).pack(pady=(0, 10))
        
        # Toggle automation
        auto_toggle = tk.Button(
            controls_frame,
            text="✅ Automation: ON",
            command=self.toggle_automation,
            bg="#238636",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        auto_toggle.pack(fill=tk.X, pady=5)
        
        # Booking status
        self.booking_status = tk.Label(
            controls_frame,
            text="📝 No active booking",
            font=("Segoe UI", 10),
            bg="#161b22",
            fg="#8b949e",
            justify=tk.LEFT,
            wraplength=250
        )
        self.booking_status.pack(fill=tk.X, pady=5)
        
        # Quick booking form
        form_frame = tk.Frame(right_frame, bg="#161b22")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            form_frame,
            text="⚡ QUICK BOOKING",
            font=("Segoe UI", 11, "bold"),
            bg="#161b22",
            fg="#58a6ff"
        ).pack(pady=(0, 10))
        
        # Movie selection
        tk.Label(
            form_frame,
            text="🎬 Movie:",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9"
        ).pack(anchor=tk.W)
        
        self.quick_movie_var = tk.StringVar()
        self.quick_movie_combo = ttk.Combobox(
            form_frame,
            textvariable=self.quick_movie_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=25
        )
        self.quick_movie_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Date selection
        tk.Label(
            form_frame,
            text="📅 Date:",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9"
        ).pack(anchor=tk.W)
        
        self.quick_date_var = tk.StringVar()
        self.quick_date_combo = ttk.Combobox(
            form_frame,
            textvariable=self.quick_date_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=25
        )
        self.quick_date_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Time selection
        tk.Label(
            form_frame,
            text="🕐 Time:",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9"
        ).pack(anchor=tk.W)
        
        self.quick_time_var = tk.StringVar()
        self.quick_time_combo = ttk.Combobox(
            form_frame,
            textvariable=self.quick_time_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=25
        )
        self.quick_time_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Tickets selection
        tickets_frame = tk.Frame(form_frame, bg="#161b22")
        tickets_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            tickets_frame,
            text="🎫 Tickets:",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9"
        ).pack(side=tk.LEFT)
        
        self.quick_tickets_var = tk.StringVar(value="1")
        self.quick_tickets_spinbox = tk.Spinbox(
            tickets_frame,
            from_=1,
            to=10,
            textvariable=self.quick_tickets_var,
            font=("Segoe UI", 10),
            bg="#21262d",
            fg="#c9d1d9",
            width=5
        )
        self.quick_tickets_spinbox.pack(side=tk.RIGHT)
        
        # Quick book button
        quick_book_btn = tk.Button(
            form_frame,
            text="🎫 Quick Book",
            command=self.quick_book_tickets,
            bg="#e34c26",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        quick_book_btn.pack(pady=10)
        
        # View bookings button
        view_bookings_btn = tk.Button(
            form_frame,
            text="📋 View My Bookings",
            command=self.view_my_bookings,
            bg="#1f6feb",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2"
        )
        view_bookings_btn.pack(pady=5)
        
        # Update quick form
        self.update_quick_form()
    
    def start_automation(self):
        """Start automation threads"""
        self.suggestion_thread = threading.Thread(target=self.suggestion_engine, daemon=True)
        self.suggestion_thread.start()
        
        self.update_thread = threading.Thread(target=self.auto_update_thread, daemon=True)
        self.update_thread.start()
    
    def suggestion_engine(self):
        """Background suggestion engine"""
        while True:
            if self.automation_active:
                suggestion = self.generate_smart_suggestion()
                if suggestion:
                    self.suggestions_queue.put(suggestion)
            time.sleep(10)
    
    def auto_update_thread(self):
        """Auto-update thread"""
        while True:
            if self.automation_active:
                self.root.after(0, self.update_suggestions_display)
                self.root.after(0, self.update_booking_status)
                self.root.after(0, self.update_quick_form)
            time.sleep(5)
    
    def update_suggestions_display(self):
        """Update suggestions display"""
        try:
            if not self.suggestions_queue.empty():
                suggestion = self.suggestions_queue.get_nowait()
                self.suggestions_text.config(text=suggestion)
        except:
            pass
    
    def update_booking_status(self):
        """Update booking status display"""
        if self.booking_flow["step"] > 0:
            status = f"📝 Booking in progress... (Step {self.booking_flow['step']}/6)\n"
            if self.booking_flow["movie"]:
                status += f"Movie: {self.booking_flow['movie']}\n"
            if self.booking_flow["date"]:
                status += f"Date: {self.booking_flow['date']}\n"
            if self.booking_flow["time"]:
                status += f"Time: {self.booking_flow['time']}\n"
            if self.booking_flow["tickets"] > 0:
                status += f"Tickets: {self.booking_flow['tickets']}"
            self.booking_status.config(text=status, fg="#58a6ff")
        else:
            self.booking_status.config(text="📝 No active booking", fg="#8b949e")
    
    def update_quick_form(self):
        """Update quick booking form"""
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            movies = movies_data.get("movies", [])
            
            # Update movie combo
            movie_titles = [m.get("title") for m in movies]
            self.quick_movie_combo['values'] = movie_titles
            
            # Update date combo
            dates = []
            today = datetime.now()
            for i in range(7):
                date = today + timedelta(days=i)
                day_name = date.strftime("%A")
                date_str = date.strftime("%Y-%m-%d")
                if i == 0:
                    dates.append(f"{date_str} (Today)")
                elif i == 1:
                    dates.append(f"{date_str} (Tomorrow)")
                else:
                    dates.append(f"{date_str} ({day_name})")
            
            self.quick_date_combo['values'] = dates
            
            # Update time combo
            times = ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
            self.quick_time_combo['values'] = times
            
        except:
            pass
    
    def auto_greeting(self):
        """Automated greeting"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "Good morning! "
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon! "
        elif 17 <= current_hour < 22:
            greeting = "Good evening! "
        else:
            greeting = "Hello! "
        
        greeting += "I'm your AI Movie Assistant. 🤖\n\n"
        greeting += "I can help you:\n"
        greeting += "• Book movie tickets 🎫\n"
        greeting += "• Show available movies 🎬\n"
        greeting += "• Manage your bookings 📋\n"
        greeting += "• Get recommendations ⭐\n\n"
        greeting += "What would you like to do today?"
        
        self.add_message(greeting, "bot")
    
    def show_thinking(self, message):
        """Show thinking indicator"""
        self.thinking_indicator.config(text=message)
        self.root.update()
    
    def process_input(self):
        """Process user input"""
        user_text = self.user_input.get().strip()
        
        if not user_text:
            return
        
        self.user_input.delete(0, tk.END)
        self.add_message(user_text, "user")
        
        # Learn from input
        self.learn_from_input(user_text)
        
        # Process with thinking indicator
        self.show_thinking("🤖 Processing...")
        time.sleep(0.5)
        
        # Get response
        response = self.understand_and_respond(user_text)
        self.add_message(response, "bot")
        
        # Clear thinking indicator
        self.thinking_indicator.config(text="")
    
    def learn_from_input(self, user_text):
        """Learn from user input"""
        text_lower = user_text.lower()
        
        # Learn genre preferences
        genres = ["action", "comedy", "drama", "sci-fi", "thriller", "romance", "mystery"]
        for genre in genres:
            if genre in text_lower:
                self.user_preferences["genre"] = genre.capitalize()
        
        # Learn time preferences
        if "morning" in text_lower:
            self.user_preferences["time_preference"] = "morning"
        elif "afternoon" in text_lower:
            self.user_preferences["time_preference"] = "afternoon"
        elif "evening" in text_lower or "night" in text_lower:
            self.user_preferences["time_preference"] = "evening"
        
        # Save preferences
        self.save_user_preferences()
    
    def understand_and_respond(self, message):
        """Understand and respond to user message"""
        message_lower = message.lower()
        
        # Intent detection
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello again! How can I assist you with movie booking today? 🎬"
        
        elif any(word in message_lower for word in ["book", "ticket", "reserve"]):
            return self.handle_book_ticket(message)
        
        elif any(word in message_lower for word in ["show", "movie", "available", "playing"]):
            return self.handle_show_movies(message)
        
        elif any(word in message_lower for word in ["my booking", "view booking", "bookings"]):
            return self.handle_view_bookings(message)
        
        elif any(word in message_lower for word in ["cancel", "delete"]):
            return self.handle_cancel_booking(message)
        
        elif any(word in message_lower for word in ["price", "cost", "how much"]):
            return self.handle_price_query(message)
        
        elif any(word in message_lower for word in ["recommend", "suggestion"]):
            return self.handle_recommendation(message)
        
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return self.handle_help(message)
        
        elif any(word in message_lower for word in ["thank", "thanks"]):
            return random.choice([
                "You're welcome! 😊",
                "Happy to help! 🎬",
                "My pleasure! Enjoy your movie! 🍿"
            ])
        
        # Handle booking flow responses
        elif self.booking_flow["step"] > 0:
            return self.handle_booking_flow_response(message)
        
        else:
            return "I'm not sure I understand. You can ask me to book tickets, show movies, or check your bookings. 😊"
    
    def handle_book_ticket(self, message):
        """Handle book ticket intent"""
        # Extract movie title
        movie_title = self.extract_movie_title(message)
        
        if not movie_title:
            # Ask for movie
            return "I'd love to help you book tickets! 🎫 Which movie would you like to watch? You can also select from the quick booking form on the right."
        
        # Start booking flow
        self.booking_flow = {
            "step": 1,
            "movie": movie_title,
            "date": None,
            "time": None,
            "tickets": 1,
            "theater": None,
            "seat_type": "Standard",
            "auto_fill": False
        }
        
        # Update quick form with selected movie
        self.quick_movie_var.set(movie_title)
        
        # Get movie details
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            
            movie_info = next((m for m in movies_data.get("movies", []) 
                             if m.get("title", "").lower() == movie_title.lower()), None)
        except:
            movie_info = None
        
        if movie_info:
            response = f"Great choice! 🎬 **{movie_title}**\n\n"
            response += f"Genre: {movie_info.get('genre', 'N/A')}\n"
            response += f"Rating: {movie_info.get('rating', 'N/A')}\n"
            response += f"Duration: {movie_info.get('duration', 'N/A')}\n\n"
            response += "**When would you like to watch it?**\n"
            response += "You can:\n"
            response += "• Select a date from the quick booking form\n"
            response += "• Say 'tomorrow', 'this weekend', or a specific date\n"
            response += "• Click the 'Quick Book' button after filling the form"
        else:
            response = f"Great! Let's book tickets for **{movie_title}**.\n\n"
            response += "**When would you like to watch it?**"
        
        return response
    
    def handle_booking_flow_response(self, message):
        """Handle responses during booking flow"""
        step = self.booking_flow["step"]
        
        if step == 1:  # Need date
            date_info = self.extract_date_info(message)
            if date_info:
                self.booking_flow["date"] = date_info
                self.booking_flow["step"] = 2
                self.quick_date_var.set(date_info)
                
                response = f"Perfect! 📅 You've selected **{date_info}**.\n\n"
                response += "**What time would you prefer?**\n"
                response += "You can select from the quick booking form or say a time like '6:30 PM'."
            else:
                response = "Please select a date. You can use the quick booking form or tell me a date."
        
        elif step == 2:  # Need time
            time_info = self.extract_time_info(message)
            if time_info:
                self.booking_flow["time"] = time_info
                self.booking_flow["step"] = 3
                self.quick_time_var.set(time_info)
                
                response = f"Excellent! 🕐 You've selected **{time_info}**.\n\n"
                response += "**How many tickets would you like?**\n"
                response += "Use the spinner in the quick booking form or tell me a number."
            else:
                response = "Please select a showtime. Available times are in the quick booking form."
        
        elif step == 3:  # Need tickets
            ticket_match = re.search(r'(\d+)\s*ticket', message.lower())
            if ticket_match:
                tickets = int(ticket_match.group(1))
                self.booking_flow["tickets"] = tickets
                self.booking_flow["step"] = 4
                self.quick_tickets_var.set(str(tickets))
                
                response = f"Got it! 🎫 **{tickets} ticket(s)**\n\n"
                response += "**Now, which theater would you prefer?**\n"
                response += "Available theaters:\n"
                
                try:
                    with open(self.movies_file, 'r') as f:
                        movies_data = json.load(f)
                    
                    for theater in movies_data.get("theaters", []):
                        name = theater.get("name", "Unknown Theater")
                        location = theater.get("location", "Unknown Location")
                        response += f"• {name} ({location})\n"
                except:
                    response += "• City Center Cinemas (Downtown)\n"
                    response += "• Starlight Theater (Westside Mall)\n"
                    response += "• Grand Arena (Eastgate Complex)\n"
                    response += "• Royal IMAX (North Plaza)\n"
            
            else:
                response = "How many tickets would you like? Please enter a number."
        
        elif step == 4:  # Need theater
            # Extract theater name
            theater_name = None
            try:
                with open(self.movies_file, 'r') as f:
                    movies_data = json.load(f)
                
                for theater in movies_data.get("theaters", []):
                    name = theater.get("name", "").lower()
                    if name in message.lower():
                        theater_name = theater.get("name")
                        break
            except:
                pass
            
            if theater_name:
                self.booking_flow["theater"] = theater_name
                self.booking_flow["step"] = 5
                
                response = f"Great choice! 🏢 **{theater_name}**\n\n"
                response += self.generate_booking_summary()
                response += "\n**Type 'confirm' to book or 'cancel' to start over.**"
            else:
                response = "Please select a theater from the list above."
        
        elif step == 5:  # Need confirmation
            if message.lower() in ["confirm", "yes", "book it", "proceed"]:
                return self.confirm_booking()
            elif message.lower() in ["cancel", "no", "stop"]:
                self.booking_flow = {"step": 0}
                return "Booking cancelled. Let me know if you'd like to book another movie! 😊"
            else:
                response = self.generate_booking_summary()
                response += "\n\n**Type 'confirm' to book or 'cancel' to start over.**"
        
        else:
            response = "Let's start a new booking! What movie would you like to watch?"
        
        return response
    
    def extract_movie_title(self, message):
        """Extract movie title from message"""
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            movies = movies_data.get("movies", [])
            
            for movie in movies:
                title = movie.get("title", "").lower()
                if title in message.lower():
                    return movie.get("title")
        except:
            pass
        
        return None
    
    def extract_date_info(self, message):
        """Extract date information"""
        message_lower = message.lower()
        
        if "today" in message_lower:
            return "today"
        elif "tomorrow" in message_lower:
            return "tomorrow"
        elif "weekend" in message_lower:
            return "this weekend"
        
        # Check for day names
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in message_lower:
                return f"this {day}"
        
        return None
    
    def extract_time_info(self, message):
        """Extract time information"""
        # Pattern for times like 6:30 PM, 2pm, 14:30
        time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?'
        matches = re.findall(time_pattern, message)
        
        if matches:
            for match in matches:
                hour = int(match[0])
                minute = match[1] if match[1] else "00"
                period = match[2].lower() if match[2] else ""
                
                # Convert to standard format
                if period == "pm" and hour < 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                
                return f"{hour:02d}:{minute}"
        
        # Check for time words
        time_words = {
            "morning": "10:00 AM",
            "afternoon": "2:00 PM", 
            "evening": "6:30 PM",
            "night": "9:00 PM"
        }
        
        for word, time_str in time_words.items():
            if word in message.lower():
                return time_str
        
        return None
    
    def generate_booking_summary(self):
        """Generate booking summary"""
        summary = "📋 **BOOKING SUMMARY**\n"
        summary += "═" * 30 + "\n"
        summary += f"🎬 Movie: {self.booking_flow['movie']}\n"
        summary += f"📅 Date: {self.booking_flow['date']}\n"
        summary += f"🕐 Time: {self.booking_flow['time']}\n"
        summary += f"🎫 Tickets: {self.booking_flow['tickets']}\n"
        summary += f"🏢 Theater: {self.booking_flow['theater']}\n"
        summary += f"💺 Seat Type: {self.booking_flow['seat_type']}\n"
        
        # Calculate price
        total_price = self.calculate_total_price()
        summary += f"💰 Total Price: ${total_price:.2f}\n"
        summary += "═" * 30
        
        return summary
    
    def calculate_total_price(self):
        """Calculate total price"""
        tickets = self.booking_flow["tickets"]
        seat_type = self.booking_flow["seat_type"]
        
        base_price = self.ticket_price
        if seat_type == "VIP":
            base_price += self.vip_upcharge
        
        subtotal = base_price * tickets
        tax = subtotal * self.tax_rate
        total = subtotal + tax
        
        return round(total, 2)
    
    def confirm_booking(self):
        """Confirm and save booking"""
        # Generate booking ID
        booking_id = f"BK{random.randint(10000, 99999)}"
        total_price = self.calculate_total_price()
        
        booking_data = {
            "booking_id": booking_id,
            "username": self.current_user,
            "movie": self.booking_flow["movie"],
            "date": self.booking_flow["date"],
            "time": self.booking_flow["time"],
            "tickets": self.booking_flow["tickets"],
            "theater": self.booking_flow["theater"],
            "seat_type": self.booking_flow["seat_type"],
            "total_price": total_price,
            "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "confirmed"
        }
        
        # Save booking
        try:
            with open(self.bookings_file, 'r') as f:
                data = json.load(f)
            data["bookings"].append(booking_data)
            
            with open(self.bookings_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Reset booking flow
            self.booking_flow = {"step": 0}
            
            response = f"✅ **BOOKING CONFIRMED!**\n\n"
            response += f"**Booking ID:** {booking_id}\n"
            response += f"**Movie:** {booking_data['movie']}\n"
            response += f"**Date & Time:** {booking_data['date']} at {booking_data['time']}\n"
            response += f"**Theater:** {booking_data['theater']}\n"
            response += f"**Tickets:** {booking_data['tickets']} ({booking_data['seat_type']})\n"
            response += f"**Total Paid:** ${total_price:.2f}\n\n"
            response += "🎬 Enjoy your movie! Don't forget the popcorn! 🍿\n\n"
            response += "Would you like to book another movie or check your bookings?"
            
            # Show success message
            messagebox.showinfo("Booking Confirmed", 
                              f"Booking {booking_id} confirmed successfully!\n\n"
                              f"Check your email for confirmation details.")
            
            return response
            
        except Exception as e:
            return f"❌ Error saving booking: {str(e)}\nPlease try again."
    
    def quick_book_tickets(self):
        """Quick book tickets from form"""
        movie = self.quick_movie_var.get()
        date = self.quick_date_var.get()
        time = self.quick_time_var.get()
        tickets = self.quick_tickets_var.get()
        
        if not movie or not date or not time:
            messagebox.showerror("Error", "Please fill all fields!")
            return
        
        # Extract date from string
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date)
        if date_match:
            date_str = date_match.group(1)
        else:
            if "today" in date.lower():
                date_str = datetime.now().strftime("%Y-%m-%d")
            elif "tomorrow" in date.lower():
                date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                date_str = date
        
        # Set booking flow
        self.booking_flow = {
            "step": 5,  # Skip to confirmation
            "movie": movie,
            "date": date_str,
            "time": time,
            "tickets": int(tickets),
            "theater": "City Center Cinemas",  # Default
            "seat_type": "Standard",
            "auto_fill": True
        }
        
        # Ask for confirmation
        response = f"⚡ **Quick Booking Summary**\n\n"
        response += self.generate_booking_summary()
        response += "\n\n**Type 'confirm' to book or 'cancel' to start over.**"
        
        self.add_message(response, "bot")
    
    def view_my_bookings(self):
        """View user's bookings"""
        try:
            with open(self.bookings_file, 'r') as f:
                data = json.load(f)
            
            user_bookings = [b for b in data.get("bookings", []) 
                           if b.get("username") == self.current_user]
            
            if not user_bookings:
                return "You don't have any bookings yet. Would you like to book your first movie? 🎬"
            
            response = "📋 **YOUR BOOKINGS**\n\n"
            
            for i, booking in enumerate(user_bookings[-5:], 1):  # Show last 5 bookings
                response += f"**Booking #{i}**\n"
                response += f"ID: {booking.get('booking_id', 'N/A')}\n"
                response += f"Movie: {booking.get('movie', 'N/A')}\n"
                response += f"Date: {booking.get('date', 'N/A')} at {booking.get('time', 'N/A')}\n"
                response += f"Theater: {booking.get('theater', 'N/A')}\n"
                response += f"Tickets: {booking.get('tickets', 'N/A')}\n"
                response += f"Total: ${booking.get('total_price', '0.00')}\n"
                response += f"Status: {booking.get('status', 'confirmed')}\n"
                response += "-" * 30 + "\n\n"
            
            response += "To cancel a booking, say: 'Cancel booking [Booking ID]'"
            
            return response
            
        except:
            return "Could not load bookings. Please try again later."
    
    def handle_view_bookings(self, message):
        """Handle view bookings intent"""
        return self.view_my_bookings()
    
    def handle_cancel_booking(self, message):
        """Handle cancel booking intent"""
        # Extract booking ID
        id_match = re.search(r'booking\s*#?\s*(\w+)', message)
        booking_id = id_match.group(1) if id_match else None
        
        if not booking_id:
            return "Please specify which booking to cancel. For example: 'Cancel booking BK12345'"
        
        try:
            with open(self.bookings_file, 'r') as f:
                data = json.load(f)
            
            # Find and update booking
            found = False
            for booking in data.get("bookings", []):
                if booking.get("booking_id") == booking_id and booking.get("username") == self.current_user:
                    booking["status"] = "cancelled"
                    found = True
                    break
            
            if found:
                with open(self.bookings_file, 'w') as f:
                    json.dump(data, f, indent=4)
                
                return f"✅ Booking {booking_id} has been cancelled. Refund will be processed within 5-7 business days."
            else:
                return f"❌ Booking {booking_id} not found or you don't have permission to cancel it."
                
        except:
            return "Error cancelling booking. Please try again later."
    
    def handle_show_movies(self, message):
        """Handle show movies intent"""
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            movies = movies_data.get("movies", [])
        except:
            movies = []
        
        response = "🎬 **NOW SHOWING**\n\n"
        
        for movie in movies:
            response += f"**{movie.get('title', 'Unknown Movie')}**\n"
            response += f"Genre: {movie.get('genre', 'N/A')} | "
            response += f"Rating: {movie.get('rating', 'N/A')} | "
            response += f"Duration: {movie.get('duration', 'N/A')}\n"
            response += f"⭐ IMDb: {movie.get('imdb', 'N/A')}/10\n"
            response += f"{movie.get('description', 'No description available.')}\n"
            response += f"Showtimes: {', '.join(movie.get('showtimes', ['N/A'])[:3])}\n\n"
        
        response += "Which movie would you like to book?"
        
        return response
    
    def handle_price_query(self, message):
        """Handle price query intent"""
        response = "💰 **TICKET PRICES**\n\n"
        response += f"Standard Ticket: ${self.ticket_price:.2f}\n"
        response += f"VIP Ticket: ${self.ticket_price + self.vip_upcharge:.2f}\n"
        response += f"Tax: {self.tax_rate * 100}%\n\n"
        response += "Would you like to book tickets?"
        
        return response
    
    def handle_recommendation(self, message):
        """Handle recommendation intent"""
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            movies = movies_data.get("movies", [])
        except:
            movies = []
        
        # Sort by popularity
        movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        
        response = "⭐ **RECOMMENDATIONS**\n\n"
        
        for i, movie in enumerate(movies[:3], 1):
            response += f"{i}. **{movie.get('title', 'Unknown Movie')}**\n"
            response += f"   Genre: {movie.get('genre', 'N/A')}\n"
            response += f"   Rating: {movie.get('rating', 'N/A')} | "
            response += f"IMDb: {movie.get('imdb', 'N/A')}/10\n"
            response += f"   {movie.get('description', '')[:100]}...\n\n"
        
        response += "Which one interests you?"
        
        return response
    
    def handle_help(self, message):
        """Handle help intent"""
        response = "🤖 **HOW I CAN HELP**\n\n"
        response += "**Booking Tickets:**\n"
        response += "• 'Book tickets for [movie name]'\n"
        response += "• Use the quick booking form on the right\n"
        response += "• 'Auto-book' for AI suggestions\n\n"
        
        response += "**Viewing Information:**\n"
        response += "• 'Show movies'\n"
        response += "• 'View my bookings'\n"
        response += "• 'Get recommendations'\n\n"
        
        response += "**Managing Bookings:**\n"
        response += "• 'Cancel booking [ID]'\n"
        response += "• 'Check booking status'\n\n"
        
        response += "**Other Commands:**\n"
        response += "• 'Help' - Show this message\n"
        response += "• 'Price' - Check ticket prices\n"
        response += "• 'Hello' - Greet me\n\n"
        
        response += "What would you like to do?"
        
        return response
    
    def generate_smart_suggestion(self):
        """Generate smart suggestion"""
        suggestions = [
            "Looking for something to watch? Try 'Get recommendations'!",
            "Ready to book? Use the quick booking form on the right!",
            "Check out the latest movies with 'Show movies'",
            "Need help? Just type 'Help' for all available commands",
            "View your booking history with 'View my bookings'"
        ]
        
        return random.choice(suggestions)
    
    def toggle_automation(self):
        """Toggle automation"""
        self.automation_active = not self.automation_active
        
        if self.automation_active:
            self.automation_status.config(text="🤖 AI: ONLINE | 🚀 AUTO-MODE: ACTIVE", fg="#3fb950")
            self.add_message("Automation activated! I'll provide smart suggestions.", "bot")
        else:
            self.automation_status.config(text="🤖 AI: ONLINE | 🚀 AUTO-MODE: OFF", fg="#da3633")
            self.add_message("Automation deactivated.", "bot")
    
    def auto_book_movie(self):
        """Auto-book movie"""
        try:
            with open(self.movies_file, 'r') as f:
                movies_data = json.load(f)
            movies = movies_data.get("movies", [])
            
            # Get most popular movie
            if movies:
                movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                best_movie = movies[0]
                
                response = f"🚀 **AUTO-BOOKING SUGGESTION**\n\n"
                response += f"Based on popularity, I recommend:\n\n"
                response += f"🎬 **{best_movie.get('title')}**\n"
                response += f"Genre: {best_movie.get('genre')}\n"
                response += f"Rating: {best_movie.get('rating')}\n"
                response += f"⭐ IMDb: {best_movie.get('imdb')}/10\n\n"
                response += f"**Suggested Booking:**\n"
                response += f"• Date: Tomorrow\n"
                response += f"• Time: 6:30 PM\n"
                response += f"• Theater: City Center Cinemas\n"
                response += f"• Tickets: 2\n\n"
                response += f"Use the quick booking form or type 'Book {best_movie.get('title')}'!"
                
                self.add_message(response, "bot")
            else:
                self.add_message("No movies available. Please check back later.", "bot")
                
        except:
            self.add_message("Error getting movie suggestions. Please try again.", "bot")
    
    def smart_suggestions(self):
        """Show smart suggestions"""
        suggestion = self.generate_smart_suggestion()
        self.add_message(f"💡 **Smart Suggestion**\n\n{suggestion}", "bot")
    
    def auto_schedule(self):
        """Auto-schedule"""
        self.add_message("📅 **Auto-Schedule**\n\n"
                        "Based on patterns:\n"
                        "• Best booking time: 2-3 days in advance\n"
                        "• Popular showtimes: 6:30 PM - 8:30 PM\n"
                        "• Best seats: Middle rows, center seats\n\n"
                        "Want to book for this weekend?", "bot")
    
    def quick_fill_booking(self):
        """Quick fill booking"""
        self.add_message("⚡ **Quick Fill**\n\n"
                        "Quick booking features:\n"
                        "1. Use the quick booking form on the right\n"
                        "2. Click 'Quick Book' after filling\n"
                        "3. Type 'confirm' to complete booking\n\n"
                        "Try it now!", "bot")
    
    def learn_preferences(self):
        """Learn preferences"""
        self.add_message("🔄 **Learning Preferences**\n\n"
                        "I'm learning from:\n"
                        "• Movies you book\n"
                        "• Times you prefer\n"
                        "• Theaters you choose\n\n"
                        "Keep booking, and I'll get better at suggestions!", "bot")
    
    def add_message(self, message, sender="user"):
        """Add message to chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "user":
            self.chat_display.insert(tk.END, f"\n[{timestamp}] 👤 You: ", "user_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_display.insert(tk.END, f"\n[{timestamp}] 🤖 AI: ", "bot_tag")
            self.chat_display.insert(tk.END, f"{message}\n", "bot_msg")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        # Store in history
        self.conversation_history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })
    
    def run(self):
        """Run the application"""
        # Configure text tags
        self.chat_display.tag_config("user_tag", foreground="#58a6ff", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#c9d1d9")
        self.chat_display.tag_config("bot_tag", foreground="#e34c26", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("bot_msg", foreground="#c9d1d9")
        
        self.root.mainloop()

# Run the chatbot
if __name__ == "__main__":
    print("🎬 Starting Automated AI Movie Booking Chatbot...")
    chatbot = AutomatedMovieChatbot()
    chatbot.run()