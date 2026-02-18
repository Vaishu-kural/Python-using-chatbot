import tkinter as tk
from tkinter import ttk, messagebox

root = tk.Tk()
root.title("Quick Movie Booking")
root.geometry("400x350")

# Variables
movie_var = tk.StringVar()
date_var = tk.StringVar()
time_var = tk.StringVar()
tickets_var = tk.StringVar(value="1")

# Frame
frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

# Movie
tk.Label(frame, text="🎬 Movie").pack(anchor="w")
movie_combo = ttk.Combobox(
    frame,
    textvariable=movie_var,
    values=["The Last Adventure", "Cosmic Dreams", "Heartstrings","Leo", "Remo", "Sita Ramam"],
    state="readonly"
)
movie_combo.pack(fill="x", pady=5)

# Date
tk.Label(frame, text="📅 Date").pack(anchor="w")
date_combo = ttk.Combobox(
    frame,
    textvariable=date_var,
    values=["Today", "Tomorrow", "This Weekend"],
    state="readonly"
)
date_combo.pack(fill="x", pady=5)

# Time
tk.Label(frame, text="🕐 Time").pack(anchor="w")
time_combo = ttk.Combobox(
    frame,
    textvariable=time_var,
    values=["10:00 AM", "2:00 PM", "6:30 PM", "9:00 PM"],
    state="readonly"
)
time_combo.pack(fill="x", pady=5)

# Tickets
tk.Label(frame, text="🎫 Tickets").pack(anchor="w")
ticket_spin = tk.Spinbox(frame, from_=1, to=20, textvariable=tickets_var)
ticket_spin.pack(fill="x", pady=5)

# Button action
def quick_book():
    if not movie_var.get() or not date_var.get() or not time_var.get():
        messagebox.showerror("Error", "Please fill all details")
        return

    messagebox.showinfo(
        "Booking Summary",
        f"Movie: {movie_var.get()}\n"
        f"Date: {date_var.get()}\n"
        f"Time: {time_var.get()}\n"
        f"Tickets: {tickets_var.get()}"
    )

# Button
tk.Button(frame, text="🎫 Quick Book", command=quick_book).pack(pady=15)

root.mainloop()