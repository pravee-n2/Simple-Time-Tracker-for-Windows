import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from tkinter.colorchooser import askcolor
from datetime import datetime, date
import csv

ACTIVITIES = [
    "Bath",
    "Breakfast",
    "Brush",
    "Chill",
    "Cycling",
    "Dinner",
    "Drop In",
    "Household Work",
    "Journal",
    "Knowledge",
    "Lunch",
    "Meditation",
    "Miscellaneous",
    "Nature's Call",
    "Sleep",
    "Study",
    "Time waste"
]

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, radius=15, bg="#4a90e2", **kwargs):
        super().__init__(parent, borderwidth=0, highlightthickness=0, **kwargs)
        self.command = command
        self.radius = radius
        self.text = text
        self.bg = bg
        self.bind("<Button-1>", self.on_click)
        self.draw_button()

    def draw_button(self):
        w = 120
        h = 50
        r = self.radius
        self.config(width=w, height=h)
        self.delete("all")
        self.create_round_rect(2, 2, w-2, h-2, r, fill=self.bg)
        self.create_text(w//2, h//2, text=self.text, fill="white", font=("Segoe UI", 12, "bold"))

    def create_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_click(self, event):
        if self.command:
            self.command()

class ActivityWithDelete(ttk.Frame):
    def __init__(self, parent, activity_name, color, start_callback, color_pick_callback, delete_callback):
        super().__init__(parent)
        self.activity_name = activity_name
        self.color = color
        self.start_callback = start_callback
        self.color_pick_callback = color_pick_callback
        self.delete_callback = delete_callback

        self.button = RoundedButton(self, activity_name, command=self.on_click, bg=color)
        self.button.grid(row=0, column=0)
        self.button.bind("<Button-3>", self.on_right_click)

        self.del_btn = ttk.Button(self, text="×", width=2, command=self.on_delete)
        self.del_btn.grid(row=0, column=1, sticky="nsew", padx=(3,0))

    def on_click(self):
        self.start_callback(self.activity_name)

    def on_right_click(self, event):
        self.color_pick_callback(event, self.activity_name, self.button)

    def on_delete(self):
        if messagebox.askyesno("Delete Activity", f"Are you sure you want to delete '{self.activity_name}'?"):
            self.delete_callback(self.activity_name)

class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Time Tracker")
        self.geometry("850x730")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tasks = []
        self.current_task = None
        self.today_date = date.today()

        self.activity_colors = {act: "#4a90e2" for act in ACTIVITIES}

        self.activity_frame = ttk.Frame(self)
        self.activity_frame.pack(pady=10)
        self.activity_widgets = {}  # activity_name -> ActivityWithDelete widget
        self.create_activity_widgets()

        self.add_activity_btn = ttk.Button(self, text="+ Add Activity", command=self.add_activity)
        self.add_activity_btn.pack(pady=(0, 15))

        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=5, pady=5)

        self.records_label = ttk.Label(self, text=f"Today - {self.today_date.isoformat()} Records:")
        self.records_label.pack(anchor="w", padx=10)

        self.records_frame = ttk.Frame(self)
        self.records_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.records_scrollbar = ttk.Scrollbar(self.records_frame, orient="vertical")
        self.records_listbox = tk.Listbox(self.records_frame, yscrollcommand=self.records_scrollbar.set, selectmode=tk.EXTENDED,
                                          height=10, font=("Segoe UI", 10))
        self.records_scrollbar.config(command=self.records_listbox.yview)
        self.records_listbox.pack(side="left", fill="both", expand=True)
        self.records_scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 10))

        self.export_txt_btn = ttk.Button(btn_frame, text="Export Text File", command=self.export_txt)
        self.export_txt_btn.grid(row=0, column=0, padx=10)

        self.export_csv_btn = ttk.Button(btn_frame, text="Export CSV File", command=self.export_csv)
        self.export_csv_btn.grid(row=0, column=1, padx=10)

        self.clear_btn = ttk.Button(btn_frame, text="Clear Records", command=self.clear_records)
        self.clear_btn.grid(row=0, column=2, padx=10)

        self.delete_record_btn = ttk.Button(btn_frame, text="Delete Selected Record(s)", command=self.delete_selected_records)
        self.delete_record_btn.grid(row=0, column=3, padx=10)

        self.timer_window = None

        self.creator_label = ttk.Label(self, text="Created by Praveen", font=("Segoe UI", 9, "italic"))
        self.creator_label.pack(side="bottom", pady=5)

        # Menubar with File and Help (Info + How to use?)
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Info", command=self.show_info)
        helpmenu.add_command(label="How to use?", command=self.show_how_to_use)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)

    def create_activity_widgets(self):
        # Clear previous widgets
        for widget in self.activity_frame.winfo_children():
            widget.destroy()
        self.activity_widgets.clear()

        cols = 5   # 5 per row as requested
        i = 0
        for act, col in self.activity_colors.items():
            widget = ActivityWithDelete(self.activity_frame, act, col, self.start_task, self.pick_color, self.delete_activity)
            widget.grid(row=i // cols, column=i % cols, padx=5, pady=5)
            self.activity_widgets[act] = widget
            i += 1

    def add_activity(self):
        new_act = simpledialog.askstring("Add Activity", "Enter new activity name:", parent=self)
        if new_act:
            new_act = new_act.strip()
            if new_act == "":
                messagebox.showwarning("Invalid Input", "Activity name cannot be empty.")
                return
            if new_act in self.activity_colors:
                messagebox.showwarning("Duplicate Activity", "This activity already exists.")
                return
            self.activity_colors[new_act] = "#4a90e2"
            self.create_activity_widgets()

    def pick_color(self, event, activity, button_widget):
        color_code = askcolor(title=f"Choose color for {activity}")
        if color_code and color_code[1]:
            self.activity_colors[activity] = color_code[1]
            button_widget.bg = color_code[1]
            button_widget.draw_button()

    def delete_activity(self, activity):
        # Remove from colors dict
        if activity in self.activity_colors:
            if self.current_task and self.current_task['activity'] == activity:
                messagebox.showwarning("Cannot Delete", "This activity is currently running. End it first.")
                return
            # Remove tasks from that activity
            self.tasks = [t for t in self.tasks if t['activity'] != activity]
            self.activity_colors.pop(activity)
            self.create_activity_widgets()
            self.refresh_records_listbox()

    def start_task(self, activity):
        if self.current_task:
            messagebox.showwarning("Activity running", "Please end current activity before starting a new one.")
            return

        self.current_task = {
            "activity": activity,
            "start": datetime.now(),
            "end": None,
            "comment": ""
        }
        self.show_timer_window()

    def show_timer_window(self):
        if self.timer_window:
            self.timer_window.destroy()

        self.timer_window = tk.Toplevel(self)
        self.timer_window.title("Activity Timer")
        self.timer_window.geometry("320x170")
        self.timer_window.attributes("-topmost", True)
        self.timer_window.resizable(False, False)

        self.label_activity = ttk.Label(self.timer_window, text=f"Activity: {self.current_task['activity']}", font=("Segoe UI", 14))
        self.label_activity.pack(pady=10)

        self.label_time = ttk.Label(self.timer_window, text="Elapsed Time: 00:00:00", font=("Segoe UI", 12))
        self.label_time.pack(pady=5)

        btn_frame = ttk.Frame(self.timer_window)
        btn_frame.pack(pady=10)

        btn_comment = ttk.Button(btn_frame, text="Add/Edit Comment", command=self.add_comment)
        btn_comment.grid(row=0, column=0, padx=10)

        btn_end = ttk.Button(btn_frame, text="End Activity", command=self.end_task)
        btn_end.grid(row=0, column=1, padx=10)

        self.update_timer()

    def update_timer(self):
        if not self.current_task:
            return
        elapsed = datetime.now() - self.current_task['start']
        h, rem = divmod(elapsed.seconds, 3600)
        m, s = divmod(rem, 60)
        self.label_time.config(text=f"Elapsed Time: {h:02d}:{m:02d}:{s:02d}")
        self.timer_window.after(1000, self.update_timer)

    def add_comment(self):
        if not self.current_task:
            return
        comment = simpledialog.askstring("Comment", "Add or edit comment for this activity:",
                                         initialvalue=self.current_task.get('comment', ''), parent=self.timer_window)
        if comment is not None:
            self.current_task['comment'] = comment

    def end_task(self):
        if not self.current_task:
            return
        self.current_task['end'] = datetime.now()
        self.tasks.append(self.current_task)
        self.add_task_to_listbox(self.current_task)
        self.current_task = None
        self.timer_window.destroy()
        self.timer_window = None
        messagebox.showinfo("Activity ended", "Activity ended and recorded.")

    def add_task_to_listbox(self, task):
        start_str = task["start"].strftime("%H:%M:%S")
        end_str = task["end"].strftime("%H:%M:%S")
        comment_preview = task["comment"][:20] + ("..." if len(task["comment"]) > 20 else "")
        display_text = f'{task["activity"]} | {start_str} - {end_str} | {comment_preview}'
        self.records_listbox.insert(tk.END, display_text)

    def refresh_records_listbox(self):
        self.records_listbox.delete(0, tk.END)
        for task in self.tasks:
            self.add_task_to_listbox(task)

    def export_txt(self):
        if self.current_task:
            messagebox.showwarning("Activity running", "Please end current activity before exporting.")
            return
        if not self.tasks:
            messagebox.showwarning("No activities", "No activities recorded to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, mode='w', encoding='utf-8') as f:
                for t in self.tasks:
                    line = f'"{t["activity"]}",{t["start"].strftime("%Y-%m-%d %H:%M:%S")},{t["end"].strftime("%Y-%m-%d %H:%M:%S")},"{t["comment"]}"\n'
                    f.write(line)
            messagebox.showinfo("Exported", f"Activities exported successfully to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def export_csv(self):
        if self.current_task:
            messagebox.showwarning("Activity running", "Please end current activity before exporting.")
            return
        if not self.tasks:
            messagebox.showwarning("No activities", "No activities recorded to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow(["Activity", "Start Time", "End Time", "Comment"])
                for t in self.tasks:
                    writer.writerow([
                        t["activity"],
                        t["start"].strftime("%Y-%m-%d %H:%M:%S"),
                        t["end"].strftime("%Y-%m-%d %H:%M:%S"),
                        t["comment"]
                    ])
            messagebox.showinfo("Exported", f"Activities exported successfully to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def clear_records(self):
        if messagebox.askyesno("Clear Records", "Are you sure you want to clear all records?"):
            self.tasks.clear()
            self.records_listbox.delete(0, tk.END)

    def delete_selected_records(self):
        selected = list(self.records_listbox.curselection())
        if not selected:
            messagebox.showinfo("No selection", "Please select one or more records to delete.")
            return
        if not messagebox.askyesno("Delete Records", f"Are you sure you want to delete {len(selected)} selected record(s)?"):
            return
        for index in reversed(selected):
            self.records_listbox.delete(index)
            self.tasks.pop(index)

    def show_info(self):
        messagebox.showinfo("Info", 
            "This is a simple time tracking solution app.\n\n"
            "Main purpose:\n"
            "If you are using Simple Time Tracker by Razeeman and you don't have your phone now, "
            "use this on your Windows PC and get the text file so you can import into Razeeman's Android application."
        )

    def show_how_to_use(self):
        messagebox.showinfo("How to use?",
            "1. Click an activity button to start tracking time for that activity.\n"
            "2. While activity runs, you can add/edit a comment.\n"
            "3. Click 'End Activity' to stop tracking and save the record.\n"
            "4. Records appear below with activity name, time range, and comment preview.\n"
            "5. You can delete activities or individual records if needed.\n"
            "6. Use 'Export Text File' to save all records in a format compatible with Simple Time Tracker by Razeeman.\n"
            "7. Use 'Export CSV File' to save all records in a general CSV format.\n"
            "8. Use 'Clear Records' to remove all saved records.\n"
            "9. Add new activities using '+ Add Activity' button.\n\n"
            "Enjoy tracking your time!"
        )

    def on_close(self):
        if self.current_task:
            if not messagebox.askyesno("Quit", "An activity is currently running. Are you sure you want to quit?"):
                return
        self.destroy()

if __name__ == "__main__":
    app = TimeTrackerApp()
    app.mainloop()
