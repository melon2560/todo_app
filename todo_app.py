import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from tkinter import messagebox

class TodoApp:
    def __init__(self):
        self.current_filter_status = None
        self.root = tk.Tk()
        self.root.title("TODOアプリ")
        self.root.geometry("400x300")
        
        self.create_table()
        self.create_gui()
        
    def connect_db(self):
        return sqlite3.connect('todo.db')

    def create_table(self):
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                due_date TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_tasks(self, filter_status=None, sort_by_date=False):
        connection = self.connect_db()
        cursor = connection.cursor()
        
        if filter_status is None and not sort_by_date:
            cursor.execute("SELECT * FROM tasks")
        elif filter_status is None and sort_by_date:
            cursor.execute("SELECT * FROM tasks ORDER BY due_date ASC")
        elif filter_status is not None and sort_by_date:
            cursor.execute("SELECT * FROM tasks WHERE done=? ORDER BY due_date ASC", (filter_status,))
        else:
            cursor.execute("SELECT * FROM tasks WHERE done=?", (filter_status,))
            
        tasks = cursor.fetchall()
        connection.close()
        return tasks

    def display_tasks(self, tasks=None):
        if tasks is None:
            tasks = self.get_tasks()
            
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        today = datetime.now().date()

        for task in tasks:
            task_id, title, done, due_date = task
            status = "完了" if done else "未完了"
            
            color, formatted_due_date = self.format_due_date(due_date, today)

            self.create_task_widgets(task_id, title, status, formatted_due_date, done, color)

    def format_due_date(self, due_date, today):
        try:
            if due_date:
                due_date_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                color = "red" if due_date_date < today else "black"
                formatted_due_date = due_date_date.strftime("%Y-%m-%d")
            else:
                color = "black"
                formatted_due_date = "未設定"
        except ValueError:
            color = "black"
            formatted_due_date = "不正な日付"
        return color, formatted_due_date

    def create_task_widgets(self, task_id, title, status, due_date, done, color):
        task_label = tk.Label(
            self.task_frame,
            text=f"{title} - {status} - 締切日: {due_date}",
            fg=color
        )
        task_label.pack(anchor="w")

        toggle_button = tk.Button(
            self.task_frame,
            text="Toggle Status",
            command=lambda: self.toggle_task_status(task_id, done)
        )
        toggle_button.pack(anchor="w")

        delete_button = tk.Button(
            self.task_frame,
            text="Delete",
            command=lambda: self.delete_task(task_id)
        )
        delete_button.pack(anchor="w")

    def set_placeholder(self, entry, placeholder):
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(foreground="black")

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(foreground="grey")

        entry.insert(0, placeholder)
        entry.config(foreground="grey")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def add_task(self):
        task_title = self.task_entry.get()
        due_date = self.due_date_entry.get()

        try:
            due_date = datetime.strptime(due_date, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror("エラー", "日付は 'YYYY-MM-DD' または 'YYYYMMDD' の形式で入力してください。")
                return

        if task_title and due_date:
            connection = self.connect_db()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO tasks (title, done, due_date) VALUES (?, ?, ?)", 
                         (task_title, 0, due_date))
            connection.commit()
            connection.close()
            
            messagebox.showinfo("情報", "タスクが追加されました！")
            self.task_entry.delete(0, tk.END)
            self.due_date_entry.delete(0, tk.END)
            self.display_tasks()
        else:
            messagebox.showwarning("警告", "タスク名と締切日を入力してください。")

    def delete_task(self, task_id):
        connection = self.connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        connection.commit()
        connection.close()
        self.display_tasks()

    def toggle_task_status(self, task_id, current_status):
        new_status = 1 if current_status == 0 else 0
        connection = self.connect_db()
        cursor = connection.cursor()
        cursor.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_status, task_id))
        connection.commit()
        connection.close()
        self.display_tasks()

    def refresh_tasks(self, filter_status=None):
        self.current_filter_status = filter_status
        tasks = self.get_tasks(filter_status)
        self.display_tasks(tasks)

    def display_sorted_tasks(self):
        tasks = self.get_tasks(self.current_filter_status, sort_by_date=True)
        self.display_tasks(tasks)

    def create_gui(self):
        self.task_entry = ttk.Entry(self.root, width=40)
        self.task_entry.pack(pady=10)
        self.set_placeholder(self.task_entry, "タスク名を入力してください。")

        self.due_date_entry = ttk.Entry(self.root, width=40)
        self.due_date_entry.pack(pady=10)
        self.set_placeholder(self.due_date_entry, "日付を'YYYY-MM-DD'形式で入力してください。")

        add_button = tk.Button(self.root, text="タスクを追加", command=self.add_task)
        add_button.pack(pady=5)

        filter_frame = tk.Frame(self.root)
        filter_frame.pack(pady=10)

        show_all_button = tk.Button(filter_frame, text="全て表示", 
                                  command=lambda: self.refresh_tasks())
        show_all_button.pack(side=tk.LEFT, padx=5)

        show_incomplete_button = tk.Button(filter_frame, text="未完了のみ表示", 
                                         command=lambda: self.refresh_tasks(0))
        show_incomplete_button.pack(side=tk.LEFT, padx=5)

        show_complete_button = tk.Button(filter_frame, text="完了のみ表示", 
                                       command=lambda: self.refresh_tasks(1))
        show_complete_button.pack(side=tk.LEFT, padx=5)

        sort_by_due_date_button = tk.Button(filter_frame, text="締切日順に表示", 
                                          command=self.display_sorted_tasks)
        sort_by_due_date_button.pack(side=tk.LEFT, padx=5)

        self.task_frame = tk.Frame(self.root)
        self.task_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.display_tasks()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TodoApp()
    app.run()
