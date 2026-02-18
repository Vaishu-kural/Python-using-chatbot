import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime, timedelta
import re
import random

class MovieBookingChatbot:
    def __init__(self):
        # Initialize data files
        self.movies_file = "movies.json"
        self.bookings_file = "bookings.json"
        self.users_file = "users.json"
        
        # Initialize data
        self.current_user = None
        self.booking_state = {}
        self.initialize_data_files()
        
        # Ticket price configuration
        self.ticket_price = 12.50
        self.vip_upcharge = 5.00
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AI Movie Ticket Booking Chatbot")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a2e")
        
        # Set up GUI
        self.setup_gui()
        
    def initialize_data_files(self):
        """Initialize JSON data files with sample data if they don't exist"""
        
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
                        "description": "An epic journey through uncharted territories."
                    },
                    {
                        "id": 2,
                        "title": "Cosmic Dreams",
                        "genre": "Sci-Fi",
                        "duration": "2h 30m",
                        "rating": "PG",
                        "description": "A mind-bending journey through space and time."
                    },
                    {
                        "id": 3,
                        "title": "Heartstrings",
                        "genre": "Romance/Drama",
                        "duration": "1h 50m",
                        "rating": "PG-13",
                        "description": "A love story that transcends time."
                    },
                    {
                        "id": 4,
                        "title": "Mystery at Midnight",
                        "genre": "Thriller/Mystery",
                        "duration": "2h 5m",
                        "rating": "R",
                        "description": "A detective races against time to solve a century-old mystery."
                    },
                    {
                        "id": 5,
                        "title": "Laugh Out Loud",
                        "genre": "Comedy",
                        "duration": "1h 45m",
                        "rating": "PG",
                        "description": "The funniest movie of the year!"
                    }
                ],
                "theaters": [
                    {"id": 1, "name": "City Center Cinemas", "location": "Downtown"},
                    {"id": 2, "name": "Starlight Theater", "location": "Westside Mall"},
                    {"id": 3, "name": "Grand Arena", "location": "Eastgate Complex"}
                ],
                "showtimes": ["10:00 AM", "1:30 PM", "4:00 PM", "6:30 PM", "9:00 PM"]
            }
            with open(self.movies_file, 'w') as f:
                json.dump(movies_data, f, indent=4)
        
        # Bookings data
        if not os.path.exists(self.bookings_file):
            with open(self.bookings_file, 'w') as f:
                json.dump({"bookings": []}, f, indent=4)
        
        # Users data
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({"users": [{"username": "demo", "password": "demo123"}]}, f, indent=4)
    
    def setup_gui(self):
        """Set up the GUI components"""
        
        # Title
        title_label = tk.Label(
            self.root, 
            text="🎬 AI Movie Ticket Booking Chatbot", 
            font=("Arial", 24, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        title_label.pack(pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#16213e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left panel - Chat interface
        left_frame = tk.Frame(main_frame, bg="#0f3460")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Chat display
        chat_label = tk.Label(
            left_frame, 
            text="🤖 Chat with AI Assistant", 
            font=("Arial", 14, "bold"),
            bg="#0f3460",
            fg="#e94560"
        )
        chat_label.pack(pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            left_frame, 
            height=20,
            width=50,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            wrap=tk.WORD
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)
        
        # User input
        input_frame = tk.Frame(left_frame, bg="#0f3460")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.user_input = tk.Entry(
            input_frame,
            font=("Arial", 12),
            bg="#1a1a2e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self.process_user_input())
        
        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.process_user_input,
            bg="#e94560",
            fg="#ffffff",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        send_button.pack(side=tk.RIGHT)
        
        # Right panel - Booking interface
        right_frame = tk.Frame(main_frame, bg="#0f3460")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Booking panel title
        booking_label = tk.Label(
            right_frame, 
            text="📝 Quick Booking Panel", 
            font=("Arial", 14, "bold"),
            bg="#0f3460",
            fg="#e94560"
        )
        booking_label.pack(pady=10)
        
        # Booking form
        form_frame = tk.Frame(right_frame, bg="#0f3460")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Movie selection
        tk.Label(
            form_frame, 
            text="Select Movie:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.movie_var = tk.StringVar()
        self.movie_combo = ttk.Combobox(
            form_frame,
            textvariable=self.movie_var,
            state="readonly",
            font=("Arial", 11)
        )
        self.movie_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Theater selection
        tk.Label(
            form_frame, 
            text="Select Theater:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.theater_var = tk.StringVar()
        self.theater_combo = ttk.Combobox(
            form_frame,
            textvariable=self.theater_var,
            state="readonly",
            font=("Arial", 11)
        )
        self.theater_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Date selection
        tk.Label(
            form_frame, 
            text="Select Date:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(
            form_frame,
            textvariable=self.date_var,
            state="readonly",
            font=("Arial", 11)
        )
        self.date_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Showtime selection
        tk.Label(
            form_frame, 
            text="Select Showtime:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.time_var = tk.StringVar()
        self.time_combo = ttk.Combobox(
            form_frame,
            textvariable=self.time_var,
            state="readonly",
            font=("Arial", 11)
        )
        self.time_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Number of tickets
        tk.Label(
            form_frame, 
            text="Number of Tickets:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.tickets_var = tk.StringVar(value="1")
        tickets_spinbox = tk.Spinbox(
            form_frame,
            from_=1,
            to=10,
            textvariable=self.tickets_var,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        tickets_spinbox.pack(fill=tk.X, pady=(0, 10))
        
        # Seat type
        tk.Label(
            form_frame, 
            text="Seat Type:", 
            font=("Arial", 11, "bold"),
            bg="#0f3460",
            fg="#ffffff"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.seat_type_var = tk.StringVar(value="Standard")
        seat_frame = tk.Frame(form_frame, bg="#0f3460")
        seat_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(
            seat_frame,
            text="Standard",
            variable=self.seat_type_var,
            value="Standard",
            bg="#0f3460",
            fg="#ffffff",
            selectcolor="#1a1a2e",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Radiobutton(
            seat_frame,
            text="VIP",
            variable=self.seat_type_var,
            value="VIP",
            bg="#0f3460",
            fg="#ffffff",
            selectcolor="#1a1a2e",
            font=("Arial", 10)
        ).pack(side=tk.LEFT)
        
        # Price display
        self.price_label = tk.Label(
            form_frame,
            text="Total Price: $0.00",
            font=("Arial", 12, "bold"),
            bg="#0f3460",
            fg="#e94560"
        )
        self.price_label.pack(pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(form_frame, bg="#0f3460")
        button_frame.pack(fill=tk.X, pady=20)
        
        # Book button
        book_button = tk.Button(
            button_frame,
            text="🎫 Book Tickets",
            command=self.book_from_form,
            bg="#e94560",
            fg="#ffffff",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        book_button.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        
        # View bookings button
        view_button = tk.Button(
            button_frame,
            text="📋 View Bookings",
            command=self.view_bookings,
            bg="#4e9de6",
            fg="#ffffff",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        view_button.pack(side=tk.RIGHT, expand=True, padx=(5, 0))
        
        # Load data into comboboxes
        self.load_booking_data()
        
        # Start chatbot conversation
        self.chatbot_greeting()
        
        # Update price when selections change
        for var in [self.movie_var, self.theater_var, self.date_var, 
                   self.time_var, self.tickets_var, self.seat_type_var]:
            var.trace_add("write", lambda *args: self.update_price_display())
    
    def load_booking_data(self):
        """Load data into comboboxes"""
        with open(self.movies_file, 'r') as f:
            data = json.load(f)
        
        # Load movies
        movies = [movie["title"] for movie in data["movies"]]
        self.movie_combo['values'] = movies
        
        # Load theaters
        theaters = [theater["name"] for theater in data["theaters"]]
        self.theater_combo['values'] = theaters
        
        # Load dates (today + next 7 days)
        dates = []
        for i in range(8):
            date = datetime.now() + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d (%A)"))
        self.date_combo['values'] = dates
        
        # Load showtimes
        self.time_combo['values'] = data["showtimes"]
    
    def update_price_display(self):
        """Update the price display based on selections"""
        try:
            num_tickets = int(self.tickets_var.get())
            seat_type = self.seat_type_var.get()
            
            base_price = self.ticket_price
            if seat_type == "VIP":
                base_price += self.vip_upcharge
            
            total_price = base_price * num_tickets
            self.price_label.config(text=f"Total Price: ${total_price:.2f}")
        except:
            pass
    
    def chatbot_greeting(self):
        """Display chatbot greeting message"""
        greeting = "🤖 Hello! I'm your AI Movie Ticket Assistant.\n\n"
        greeting += "I can help you with:\n"
        greeting += "• Booking movie tickets\n"
        greeting += "• Showing available movies\n"
        greeting += "• Viewing or canceling bookings\n"
        greeting += "• Answering questions\n\n"
        greeting += "Type 'help' for available commands or use the booking panel on the right!\n"
        greeting += "="*50
        
        self.add_to_chat(greeting, "bot")
    
    def add_to_chat(self, message, sender="user"):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        if sender == "user":
            self.chat_display.insert(tk.END, "You: ", "user_tag")
            self.chat_display.insert(tk.END, message + "\n\n")
        else:
            self.chat_display.insert(tk.END, "Assistant: ", "bot_tag")
            self.chat_display.insert(tk.END, message + "\n\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def process_user_input(self):
        """Process user input from chat"""
        user_text = self.user_input.get().strip()
        
        if not user_text:
            return
        
        self.add_to_chat(user_text, "user")
        self.user_input.delete(0, tk.END)
        
        # Process the user's message
        response = self.understand_message(user_text.lower())
        self.add_to_chat(response, "bot")
    
    def understand_message(self, message):
        """Natural language processing for user messages"""
        # Greeting patterns
        if any(word in message for word in ["hello", "hi", "hey", "greetings"]):
            return random.choice([
                "Hello! How can I assist you with movie tickets today?",
                "Hi there! Ready to book some movies?",
                "Hey! I'm here to help you with your movie booking needs."
            ])
        
        # Help command
        elif "help" in message:
            return self.get_help_response()
        
        # Book tickets patterns
        elif any(word in message for word in ["book", "reserve", "buy ticket"]):
            return self.process_booking_request(message)
        
        # Show movies patterns
        elif any(word in message for word in ["show movie", "available", "what's playing", "list movie"]):
            return self.show_available_movies()
        
        # View bookings patterns
        elif any(word in message for word in ["view booking", "my booking", "previous booking"]):
            return self.view_bookings_chat()
        
        # Cancel booking patterns
        elif any(word in message for word in ["cancel", "delete booking"]):
            return self.process_cancel_request(message)
        
        # Thank you patterns
        elif any(word in message for word in ["thank", "thanks", "appreciate"]):
            return random.choice([
                "You're welcome! Enjoy your movie! 🎬",
                "My pleasure! Let me know if you need anything else.",
                "Happy to help! 🍿"
            ])
        
        # Price query
        elif any(word in message for word in ["price", "cost", "how much"]):
            return f"Ticket prices:\nStandard: ${self.ticket_price}\nVIP: ${self.ticket_price + self.vip_upcharge}\n\nYou can also use the booking panel on the right to calculate exact prices."
        
        # Default response
        else:
            return "I'm not sure I understood. You can:\n1. Book tickets\n2. View available movies\n3. Check your bookings\n4. Cancel a booking\n\nType 'help' for more options or use the booking panel."
    
    def get_help_response(self):
        """Return help message"""
        help_text = "Here's what I can help you with:\n\n"
        help_text += "🎬 **Booking Tickets**\n"
        help_text += "• 'Book 2 tickets for The Last Adventure tomorrow'\n"
        help_text += "• 'I want to reserve tickets for Cosmic Dreams'\n"
        help_text += "• Or use the booking panel on the right\n\n"
        help_text += "📋 **Viewing Information**\n"
        help_text += "• 'Show available movies'\n"
        help_text += "• 'What's playing?'\n"
        help_text += "• 'View my bookings'\n\n"
        help_text += "❌ **Canceling Bookings**\n"
        help_text += "• 'Cancel my booking'\n"
        help_text += "• 'Delete booking for Cosmic Dreams'\n\n"
        help_text += "💬 **Other Commands**\n"
        help_text += "• 'Hello' - Greet me\n"
        help_text += "• 'Thank you' - Express gratitude\n"
        help_text += "• 'What's the price?' - Check ticket prices"
        
        return help_text
    
    def process_booking_request(self, message):
        """Process natural language booking request"""
        # Extract movie title
        movie_title = None
        with open(self.movies_file, 'r') as f:
            movies_data = json.load(f)
        
        for movie in movies_data["movies"]:
            if movie["title"].lower() in message:
                movie_title = movie["title"]
                break
        
        if not movie_title:
            return "Which movie would you like to book? You can say something like 'Book tickets for The Last Adventure'"
        
        # Extract number of tickets
        ticket_match = re.search(r'(\d+)\s*ticket', message)
        num_tickets = int(ticket_match.group(1)) if ticket_match else 1
        
        # Extract date (simplified)
        date_str = "tomorrow"
        if "today" in message:
            date_str = "today"
        
        response = f"I'll help you book {num_tickets} ticket(s) for '{movie_title}' {date_str}.\n\n"
        response += "Please use the booking panel on the right to select:\n"
        response += "1. Theater\n2. Exact date\n3. Showtime\n4. Seat type\n\n"
        response += "Or you can type: 'Book {num_tickets} tickets for {movie_title} at 6:30 PM' for more specific booking."
        
        # Auto-fill the form
        self.movie_var.set(movie_title)
        self.tickets_var.set(str(num_tickets))
        
        return response
    
    def show_available_movies(self):
        """Show available movies in chat"""
        with open(self.movies_file, 'r') as f:
            data = json.load(f)
        
        response = "🎬 **Now Showing:**\n\n"
        
        for movie in data["movies"]:
            response += f"**{movie['title']}**\n"
            response += f"Genre: {movie['genre']} | Duration: {movie['duration']} | Rating: {movie['rating']}\n"
            response += f"{movie['description']}\n\n"
        
        response += "**Available Theaters:**\n"
        for theater in data["theaters"]:
            response += f"• {theater['name']} ({theater['location']})\n"
        
        response += "\n**Showtimes:**\n"
        for time in data["showtimes"]:
            response += f"• {time}\n"
        
        return response
    
    def view_bookings_chat(self):
        """View bookings in chat format"""
        if not self.current_user:
            return "Please log in first to view your bookings. Use the 'Login' button above."
        
        with open(self.bookings_file, 'r') as f:
            data = json.load(f)
        
        user_bookings = [b for b in data["bookings"] if b.get("username") == self.current_user]
        
        if not user_bookings:
            return "You don't have any bookings yet. Would you like to book a movie?"
        
        response = "📋 **Your Bookings:**\n\n"
        
        for i, booking in enumerate(user_bookings, 1):
            response += f"**Booking #{i}**\n"
            response += f"Movie: {booking['movie']}\n"
            response += f"Theater: {booking['theater']}\n"
            response += f"Date: {booking['date']} at {booking['time']}\n"
            response += f"Tickets: {booking['tickets']} ({booking['seat_type']})\n"
            response += f"Total: ${booking['total_price']}\n"
            response += f"Booking ID: {booking['booking_id']}\n"
            response += "-"*30 + "\n"
        
        response += "\nTo cancel a booking, say: 'Cancel booking [Booking ID]'"
        
        return response
    
    def process_cancel_request(self, message):
        """Process cancel booking request"""
        # Extract booking ID
        id_match = re.search(r'booking\s*#?\s*(\w+)', message)
        booking_id = id_match.group(1) if id_match else None
        
        if booking_id:
            return self.cancel_booking(booking_id)
        else:
            return "Please specify which booking to cancel. For example: 'Cancel booking #ABC123' or use the view bookings to see your booking IDs."
    
    def book_from_form(self):
        """Book tickets from the form"""
        # Validate all fields
        if not all([self.movie_var.get(), self.theater_var.get(), 
                   self.date_var.get(), self.time_var.get(), self.tickets_var.get()]):
            messagebox.showerror("Error", "Please fill in all fields!")
            return
        
        # Create booking
        booking_data = {
            "movie": self.movie_var.get(),
            "theater": self.theater_var.get(),
            "date": self.date_var.get(),
            "time": self.time_var.get(),
            "tickets": int(self.tickets_var.get()),
            "seat_type": self.seat_type_var.get()
        }
        
        # Calculate price
        base_price = self.ticket_price
        if booking_data["seat_type"] == "VIP":
            base_price += self.vip_upcharge
        
        total_price = base_price * booking_data["tickets"]
        booking_data["total_price"] = round(total_price, 2)
        
        # Generate booking ID
        booking_data["booking_id"] = f"BK{random.randint(10000, 99999)}"
        booking_data["booking_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        booking_data["username"] = self.current_user or "guest"
        
        # Save booking
        self.save_booking(booking_data)
        
        # Show confirmation
        confirmation = f"✅ **Booking Confirmed!**\n\n"
        confirmation += f"**Booking ID:** {booking_data['booking_id']}\n"
        confirmation += f"**Movie:** {booking_data['movie']}\n"
        confirmation += f"**Theater:** {booking_data['theater']}\n"
        confirmation += f"**Date & Time:** {booking_data['date']} at {booking_data['time']}\n"
        confirmation += f"**Tickets:** {booking_data['tickets']} ({booking_data['seat_type']})\n"
        confirmation += f"**Total Price:** ${booking_data['total_price']}\n\n"
        confirmation += "Enjoy your movie! 🎬🍿"
        
        messagebox.showinfo("Booking Confirmed", confirmation)
        self.add_to_chat(f"I've booked {booking_data['tickets']} ticket(s) for {booking_data['movie']}!", "bot")
        
        # Clear form
        self.tickets_var.set("1")
        self.seat_type_var.set("Standard")
    
    def save_booking(self, booking_data):
        """Save booking to JSON file"""
        with open(self.bookings_file, 'r') as f:
            data = json.load(f)
        
        data["bookings"].append(booking_data)
        
        with open(self.bookings_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def view_bookings(self):
        """View bookings in a new window"""
        view_window = tk.Toplevel(self.root)
        view_window.title("Your Bookings")
        view_window.geometry("600x500")
        view_window.configure(bg="#1a1a2e")
        
        # Title
        title = tk.Label(
            view_window,
            text="📋 Your Movie Bookings",
            font=("Arial", 18, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        title.pack(pady=20)
        
        # Bookings display
        bookings_frame = tk.Frame(view_window, bg="#0f3460")
        bookings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Load bookings
        with open(self.bookings_file, 'r') as f:
            data = json.load(f)
        
        user_bookings = [b for b in data["bookings"] if b.get("username") == (self.current_user or "guest")]
        
        if not user_bookings:
            no_bookings = tk.Label(
                bookings_frame,
                text="You don't have any bookings yet.\n\nUse the booking panel to book your first movie!",
                font=("Arial", 14),
                bg="#0f3460",
                fg="#ffffff",
                justify=tk.CENTER
            )
            no_bookings.pack(expand=True)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(bookings_frame, bg="#0f3460", highlightthickness=0)
        scrollbar = tk.Scrollbar(bookings_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#0f3460")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display each booking
        for i, booking in enumerate(user_bookings):
            booking_frame = tk.Frame(
                scrollable_frame,
                bg="#1a1a2e",
                relief=tk.RAISED,
                borderwidth=2
            )
            booking_frame.pack(fill=tk.X, pady=10, padx=10)
            
            # Booking info
            info_text = f"🎬 {booking['movie']}\n"
            info_text += f"🏢 {booking['theater']}\n"
            info_text += f"📅 {booking['date']} at {booking['time']}\n"
            info_text += f"🎫 {booking['tickets']} ticket(s) ({booking['seat_type']})\n"
            info_text += f"💰 ${booking['total_price']}\n"
            info_text += f"🆔 Booking ID: {booking['booking_id']}"
            
            info_label = tk.Label(
                booking_frame,
                text=info_text,
                font=("Arial", 11),
                bg="#1a1a2e",
                fg="#ffffff",
                justify=tk.LEFT
            )
            info_label.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Cancel button
            cancel_btn = tk.Button(
                booking_frame,
                text="Cancel",
                command=lambda b_id=booking['booking_id']: self.cancel_booking_gui(b_id, view_window),
                bg="#e94560",
                fg="#ffffff",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                cursor="hand2"
            )
            cancel_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def cancel_booking_gui(self, booking_id, window):
        """Cancel booking from GUI"""
        if messagebox.askyesno("Confirm Cancellation", 
                               f"Are you sure you want to cancel booking {booking_id}?"):
            result = self.cancel_booking(booking_id)
            messagebox.showinfo("Cancellation", result)
            window.destroy()
            self.view_bookings()
    
    def cancel_booking(self, booking_id):
        """Cancel a booking by ID"""
        with open(self.bookings_file, 'r') as f:
            data = json.load(f)
        
        # Find and remove booking
        original_count = len(data["bookings"])
        data["bookings"] = [b for b in data["bookings"] if b.get("booking_id") != booking_id]
        
        if len(data["bookings"]) < original_count:
            with open(self.bookings_file, 'w') as f:
                json.dump(data, f, indent=4)
            return f"✅ Booking {booking_id} has been cancelled successfully. Refund will be processed within 5-7 business days."
        else:
            return f"❌ Booking {booking_id} not found. Please check the booking ID and try again."
    
    def run(self):
        """Run the application"""
        # Configure text tags for chat
        self.chat_display.tag_config("user_tag", foreground="#4e9de6", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("bot_tag", foreground="#e94560", font=("Arial", 11, "bold"))
        
        self.root.mainloop()

# Run the application
if __name__ == "__main__":
    print("Starting AI Movie Ticket Booking Chatbot...")
    chatbot = MovieBookingChatbot()
    chatbot.run()