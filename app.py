# # Multiprocess-Alarm-Schedule

import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import datetime
import time
import threading
import queue as thread_queue
import winsound

class ManagedProcess:
    def __init__(self, pid, name, sleep_time, priority, queue):
        self.pid = pid
        self.name = name
        self.sleep_time = sleep_time
        self.priority = priority
        self.queue = queue
        self.status = "Waiting"
        self.start_time = None
        self.end_time = None
        self.progress = 0
        self.remaining = sleep_time
        self.thread = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.is_running = False

    def run(self):
        self.start_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.queue.put(("gantt_start", self.pid, time.time()))
        self.is_running = True
        
        while self.remaining > 0 and self.is_running:
            self.pause_event.wait()  # Wait if paused
            if not self.is_running:  # Check if stopped
                break
            time.sleep(1)
            if self.is_running:  # Double check before decrementing
                self.remaining -= 1
                self.progress = int(100 * (self.sleep_time - self.remaining) / self.sleep_time)
                self.queue.put(("update", self.pid, self.progress))
        
        if self.remaining <= 0:
            self.end_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.status = "Completed"
            self.is_running = False
            self.queue.put(("completed", self.pid))
            self.queue.put(("gantt_end", self.pid, time.time()))

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()

    def pause(self):
        self.pause_event.clear()
        if self.status != "Completed":
            self.status = "Paused"

    def resume(self):
        self.pause_event.set()
        if self.status != "Completed":
            self.status = "Running"

    def stop(self):
        self.is_running = False
        self.pause_event.set()  # Unblock if waiting

class ModernSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Modern Process Scheduler - Thor UI")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f8fafc')
        
        # Modern color scheme
        self.colors = {
            'primary': '#6366f1',      # Indigo
            'secondary': '#8b5cf6',    # Purple  
            'success': '#10b981',      # Green
            'warning': '#f59e0b',      # Yellow
            'danger': '#ef4444',       # Red
            'info': '#06b6d4',         # Cyan
            'light': '#f8fafc',        # Light gray
            'dark': '#1e293b',         # Dark gray
            'white': '#ffffff',
            'running': '#10b981',      # Green
            'paused': '#f59e0b',       # Yellow
            'waiting': '#06b6d4',      # Cyan
            'completed': '#8b5cf6'     # Purple
        }
        
        self.process_list = []
        self.running_processes = []
        self.paused_processes = []
        self.pid_counter = 1
        self.max_running = 2
        self.queue = thread_queue.Queue()
        self.preemptive_enabled = tk.BooleanVar(value=False)
        self.selected_pid = None
        self.gantt_data = {}
        self.last_update_time = 0

        self.setup_styles()
        self.build_modern_ui()
        self.update_gui()

    def setup_styles(self):
        """Setup modern ttk styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure modern button styles
        self.style.configure('Primary.TButton',
                           background=self.colors['primary'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(20, 10))
        
        self.style.configure('Success.TButton',
                           background=self.colors['success'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(15, 8))
        
        self.style.configure('Warning.TButton',
                           background=self.colors['warning'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(15, 8))
        
        # Configure modern frame styles
        self.style.configure('Card.TFrame',
                           background='white',
                           relief='flat',
                           borderwidth=1)
        
        # Configure modern label styles
        self.style.configure('Title.TLabel',
                           background='white',
                           foreground=self.colors['dark'],
                           font=('Segoe UI', 14, 'bold'))
        
        self.style.configure('Subtitle.TLabel',
                           background='white',
                           foreground=self.colors['dark'],
                           font=('Segoe UI', 10))
        
        self.style.configure('Header.TLabel',
                           background=self.colors['primary'],
                           foreground='white',
                           font=('Segoe UI', 12, 'bold'),
                           padding=(10, 10))

    def create_card_frame(self, parent, title, bg_color='white', title_bg=None):
        """Create a modern card-style frame"""
        card_frame = tk.Frame(parent, bg=bg_color, relief='flat', bd=1)
        card_frame.configure(highlightbackground='#e2e8f0', highlightthickness=1)
        
        if title:
            title_frame = tk.Frame(card_frame, bg=title_bg or self.colors['primary'], height=40)
            title_frame.pack(fill='x', padx=2, pady=(2, 0))
            title_frame.pack_propagate(False)
            
            title_label = tk.Label(title_frame, text=title, 
                                 bg=title_bg or self.colors['primary'], 
                                 fg='white',
                                 font=('Segoe UI', 12, 'bold'))
            title_label.pack(pady=10)
        
        content_frame = tk.Frame(card_frame, bg=bg_color)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        return card_frame, content_frame

    def create_modern_button(self, parent, text, command, bg_color, hover_color=None):
        """Create a modern styled button"""
        button = tk.Button(parent, text=text, command=command,
                          bg=bg_color, fg='white',
                          font=('Segoe UI', 10, 'bold'),
                          relief='flat', bd=0,
                          padx=20, pady=8,
                          cursor='hand2')
        
        # Add hover effect
        if hover_color:
            def on_enter(e):
                button.configure(bg=hover_color)
            def on_leave(e):
                button.configure(bg=bg_color)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        return button

    def build_modern_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['light'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg=self.colors['light'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(header_frame, 
                              text="🚀 Modern Process Scheduler",
                              bg=self.colors['light'],
                              fg=self.colors['primary'],
                              font=('Segoe UI', 24, 'bold'))
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame,
                                 text="Advanced Multi-Process Management System",
                                 bg=self.colors['light'],
                                 fg=self.colors['dark'],
                                 font=('Segoe UI', 12))
        subtitle_label.pack()

        # Add Process Card
        add_card, add_content = self.create_card_frame(main_container, "➕ Add New Process")
        add_card.pack(fill='x', pady=(0, 15))
        
        form_frame = tk.Frame(add_content, bg='white')
        form_frame.pack(fill='x', pady=10)
        
        # Form fields in a grid
        tk.Label(form_frame, text="Process Name:", bg='white', 
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.name_entry = tk.Entry(form_frame, font=('Segoe UI', 10), width=15, relief='flat', bd=5)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Time (seconds):", bg='white',
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.sleep_entry = tk.Entry(form_frame, font=('Segoe UI', 10), width=8, relief='flat', bd=5)
        self.sleep_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Priority:", bg='white',
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=4, padx=5, pady=5, sticky='w')
        self.priority_box = ttk.Combobox(form_frame, values=list(range(1, 11)), width=5, font=('Segoe UI', 10))
        self.priority_box.grid(row=0, column=5, padx=5, pady=5)
        self.priority_box.set(5)

        add_btn = self.create_modern_button(form_frame, "➕ Add Process", self.add_process, 
                                          self.colors['primary'], '#5856eb')
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        preemptive_check = tk.Checkbutton(form_frame, text="🔄 Preemptive Mode", 
                                        variable=self.preemptive_enabled,
                                        bg='white', font=('Segoe UI', 10),
                                        command=self.on_preemptive_change)
        preemptive_check.grid(row=0, column=7, padx=10, pady=5)

        # Priority Change Card
        priority_card, priority_content = self.create_card_frame(main_container, "⚙️ Change Process Priority", 
                                                               title_bg=self.colors['warning'])
        priority_card.pack(fill='x', pady=(0, 15))
        
        priority_form = tk.Frame(priority_content, bg='white')
        priority_form.pack(fill='x', pady=10)
        
        tk.Label(priority_form, text="Process ID:", bg='white',
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.pid_change_entry = tk.Entry(priority_form, font=('Segoe UI', 10), width=8, relief='flat', bd=5)
        self.pid_change_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(priority_form, text="New Priority:", bg='white',
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.new_priority_entry = tk.Entry(priority_form, font=('Segoe UI', 10), width=8, relief='flat', bd=5)
        self.new_priority_entry.grid(row=0, column=3, padx=5, pady=5)

        change_btn = self.create_modern_button(priority_form, "🔄 Update Priority", self.change_priority,
                                             self.colors['warning'], '#f59e0b')
        change_btn.grid(row=0, column=4, padx=10, pady=5)

        # Sorting Options Card
        sort_card, sort_content = self.create_card_frame(main_container, "📊 Sorting Options",
                                                       title_bg=self.colors['info'])
        sort_card.pack(fill='x', pady=(0, 15))
        
        sort_frame = tk.Frame(sort_content, bg='white')
        sort_frame.pack(fill='x', pady=10)
        
        self.sort_var = tk.StringVar(value="priority")
        
        sort_options = [
            ("🎯 Priority", "priority"),
            ("📈 Status", "status"), 
            ("⏰ Start Time", "start_time")
        ]
        
        for i, (text, value) in enumerate(sort_options):
            rb = tk.Radiobutton(sort_frame, text=text, variable=self.sort_var, value=value,
                               bg='white', font=('Segoe UI', 10))
            rb.grid(row=0, column=i, padx=20, pady=5, sticky='w')

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, pady=(0, 15))

        # Process Grid Tab
        grid_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(grid_frame, text="📋 Process Grid")
        
        # Process grid with modern styling
        grid_container = tk.Frame(grid_frame, bg='white')
        grid_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create treeview with modern styling
        self.process_tree = ttk.Treeview(grid_container, 
                                       columns=("PID", "Name", "Priority", "Status", "Progress", "Start", "End"),
                                       show="headings", height=12)
        
        # Configure column headings
        headings = ["PID", "Name", "Priority", "Status", "Progress", "Start Time", "End Time"]
        for i, heading in enumerate(headings):
            col = self.process_tree["columns"][i]
            self.process_tree.heading(col, text=heading)
            self.process_tree.column(col, anchor="center", width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(grid_container, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        self.process_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind tree selection
        self.process_tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # Process Info Tab
        info_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(info_frame, text="ℹ️ Process Info")
        
        self.info_text = tk.Text(info_frame, height=15, width=80, wrap=tk.WORD,
                                font=('Segoe UI', 11), relief='flat', bd=10,
                                bg='#f8fafc', fg=self.colors['dark'])
        self.info_text.pack(fill='both', expand=True, padx=10, pady=10)

        # System Logs Tab
        logs_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(logs_frame, text="📝 System Logs")
        
        self.log_box = tk.Text(logs_frame, height=15, width=80, wrap=tk.WORD,
                              font=('Consolas', 10), relief='flat', bd=10,
                              bg='#1e293b', fg='#e2e8f0')
        self.log_box.pack(fill='both', expand=True, padx=10, pady=10)

        # Gantt Chart Tab
        gantt_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(gantt_frame, text="📊 Gantt Chart")
        
        self.gantt_canvas = Canvas(gantt_frame, width=1200, height=400, bg='white', relief='flat')
        self.gantt_canvas.pack(fill='both', expand=True, padx=10, pady=10)

        # Statistics Cards
        stats_frame = tk.Frame(main_container, bg=self.colors['light'])
        stats_frame.pack(fill='x', pady=(15, 0))
        
        self.create_stats_cards(stats_frame)

    def create_stats_cards(self, parent):
        """Create modern statistics cards"""
        stats_container = tk.Frame(parent, bg=self.colors['light'])
        stats_container.pack(fill='x')
        
        # Statistics data
        stats = [
            ("🟢 Running", "running", self.colors['running']),
            ("🟡 Paused", "paused", self.colors['paused']),
            ("🔵 Waiting", "waiting", self.colors['waiting']),
            ("🟣 Completed", "completed", self.colors['completed'])
        ]
        
        self.stat_labels = {}
        
        for i, (title, key, color) in enumerate(stats):
            card = tk.Frame(stats_container, bg=color, relief='flat', bd=0)
            card.pack(side='left', fill='both', expand=True, padx=5)
            
            # Add some padding
            content = tk.Frame(card, bg=color)
            content.pack(fill='both', expand=True, padx=15, pady=15)
            
            title_label = tk.Label(content, text=title, bg=color, fg='white',
                                 font=('Segoe UI', 12, 'bold'))
            title_label.pack()
            
            count_label = tk.Label(content, text="0", bg=color, fg='white',
                                 font=('Segoe UI', 24, 'bold'))
            count_label.pack()
            
            self.stat_labels[key] = count_label

    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.process_tree.selection()
        if selection:
            item = selection[0]
            pid = self.process_tree.item(item, 'values')[0]
            try:
                self.selected_pid = int(pid)
            except (ValueError, IndexError):
                self.selected_pid = None

    def on_preemptive_change(self):
        """Handle preemptive mode change"""
        self.schedule()

    def update_stats(self):
        """Update statistics cards"""
        stats = {
            'running': len([p for p in self.process_list if p.status == "Running"]),
            'paused': len([p for p in self.process_list if p.status == "Paused"]),
            'waiting': len([p for p in self.process_list if p.status == "Waiting"]),
            'completed': len([p for p in self.process_list if p.status == "Completed"])
        }
        
        for key, count in stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].configure(text=str(count))

    def get_status_color(self, status):
        """Get color for process status"""
        status_colors = {
            "Running": "#10b981",
            "Paused": "#f59e0b", 
            "Waiting": "#06b6d4",
            "Completed": "#8b5cf6"
        }
        return status_colors.get(status, "#6b7280")

    def add_process(self):
        name = self.name_entry.get().strip()
        try:
            time_ = int(self.sleep_entry.get())
            priority = int(self.priority_box.get())
        except ValueError:
            messagebox.showerror("❌ Invalid Input", "Time and priority must be numbers.")
            return
        
        if not name:
            messagebox.showerror("❌ Invalid Input", "Process name cannot be empty.")
            return
            
        proc = ManagedProcess(self.pid_counter, name, time_, priority, self.queue)
        self.process_list.append(proc)
        self.log(f"✅ Process {proc.pid} ({proc.name}) added with priority {priority}")
        self.notify(f"🎉 Process {proc.pid} added successfully!")
        self.pid_counter += 1
        
        # Clear form
        self.name_entry.delete(0, tk.END)
        self.sleep_entry.delete(0, tk.END)
        self.priority_box.set(5)
        
        # Schedule immediately
        self.root.after(100, self.schedule)

    def change_priority(self):
        try:
            pid = int(self.pid_change_entry.get())
            new_priority = int(self.new_priority_entry.get())
        except ValueError:
            messagebox.showerror("❌ Invalid Input", "Priority and PID must be numbers.")
            return
            
        for p in self.process_list:
            if p.pid == pid:
                old_priority = p.priority
                p.priority = new_priority
                self.log(f"🔄 Process {pid} priority changed from {old_priority} to {new_priority}")
                self.notify(f"✅ Priority of Process {pid} updated!")
                
                # Clear form
                self.pid_change_entry.delete(0, tk.END)
                self.new_priority_entry.delete(0, tk.END)
                
                # Reschedule
                self.root.after(100, self.schedule)
                return
        
        messagebox.showerror("❌ Process Not Found", f"Process with PID {pid} not found.")

    def schedule(self):
        """Improved scheduling logic"""
        # Get current process states
        running = [p for p in self.process_list if p.status == "Running"]
        paused = [p for p in self.process_list if p.status == "Paused"]
        waiting = [p for p in self.process_list if p.status == "Waiting"]
        completed = [p for p in self.process_list if p.status == "Completed"]
        
        # Available slots
        available_slots = self.max_running - len(running)
        
        if self.preemptive_enabled.get():
            # Preemptive scheduling - priority based
            all_active = running + paused + waiting
            all_active = [p for p in all_active if p.status != "Completed"]
            all_active.sort(key=lambda x: x.priority)
            
            # Stop all currently running processes
            for p in running:
                p.pause()
            
            # Start/resume top priority processes
            for i, process in enumerate(all_active[:self.max_running]):
                if process.status in ["Paused", "Waiting"]:
                    if process.status == "Waiting":
                        process.start()
                    process.resume()
                    process.status = "Running"
            
            # Pause remaining processes
            for process in all_active[self.max_running:]:
                if process.status == "Running":
                    process.pause()
                process.status = "Paused"
                
        else:
            # Non-preemptive scheduling - FIFO with priority
            if available_slots > 0 and waiting:
                # Sort waiting processes by priority
                waiting.sort(key=lambda x: x.priority)
                
                # Start processes up to available slots
                for process in waiting[:available_slots]:
                    process.start()
                    process.status = "Running"
                    self.log(f"🚀 Process {process.pid} ({process.name}) started")
            
            # If there are paused processes and available slots, resume them
            if available_slots > len([p for p in waiting if p.status == "Running"]) and paused:
                remaining_slots = available_slots - len([p for p in waiting if p.status == "Running"])
                paused.sort(key=lambda x: x.priority)
                
                for process in paused[:remaining_slots]:
                    process.resume()
                    process.status = "Running"
                    self.log(f"▶️ Process {process.pid} ({process.name}) resumed")

        # Update process lists
        self.running_processes = [p.pid for p in self.process_list if p.status == "Running"]
        self.paused_processes = [p.pid for p in self.process_list if p.status == "Paused"]

    def update_gui(self):
        """Improved GUI update with better state management"""
        current_time = time.time()
        
        # Process queue messages
        messages_processed = 0
        try:
            while messages_processed < 10:  # Limit messages per update to prevent flooding
                msg = self.queue.get_nowait()
                messages_processed += 1
                
                if msg[0] == "update":
                    pid, progress = msg[1], msg[2]
                    for p in self.process_list:
                        if p.pid == pid:
                            p.progress = progress
                            break
                            
                elif msg[0] == "completed":
                    pid = msg[1]
                    for p in self.process_list:
                        if p.pid == pid and p.status != "Completed":
                            p.status = "Completed"
                            p.is_running = False
                            self.log(f"🎉 Process {pid} ({p.name}) completed successfully!")
                            self.notify(f"✅ Process {pid} finished execution!")
                            # Schedule after a short delay to allow UI to update
                            self.root.after(200, self.schedule)
                            break
                            
                elif msg[0] == "gantt_start":
                    if msg[1] not in self.gantt_data:
                        self.gantt_data[msg[1]] = [msg[2], None]
                        
                elif msg[0] == "gantt_end":
                    if msg[1] in self.gantt_data:
                        self.gantt_data[msg[1]][1] = msg[2]
                        
        except thread_queue.Empty:
            pass

        # Update UI only if enough time has passed (reduce flickering)
        if current_time - self.last_update_time >= 0.5:  # Update every 500ms
            self.update_process_tree()
            self.update_process_info()
            self.draw_modern_gantt_chart()
            self.update_stats()
            self.last_update_time = current_time

        # Schedule next update
        self.root.after(500, self.update_gui)

    def update_process_tree(self):
        """Update process tree with reduced flickering"""
        # Store current selection
        current_selection = self.process_tree.selection()
        selected_pid = None
        if current_selection:
            try:
                selected_pid = int(self.process_tree.item(current_selection[0], 'values')[0])
            except (ValueError, IndexError):
                pass

        # Clear and repopulate tree
        self.process_tree.delete(*self.process_tree.get_children())

        # Get sorted processes
        sorted_list = self.get_sorted_processes()

        # Insert processes
        for p in sorted_list:
            status_emoji = {"Running": "🟢", "Paused": "🟡", "Waiting": "🔵", "Completed": "🟣"}
            status_text = f"{status_emoji.get(p.status, '⚪')} {p.status}"
            
            values = (
                p.pid,
                p.name,
                f"⭐ {p.priority}",
                status_text,
                f"{p.progress}%",
                p.start_time or "Not started",
                p.end_time or "Not completed"
            )
            
            item = self.process_tree.insert("", "end", values=values)
            
            # Restore selection if it was the same process
            if selected_pid and p.pid == selected_pid:
                self.process_tree.selection_set(item)

    def get_sorted_processes(self):
        """Get processes sorted by current criteria"""
        sorted_list = self.process_list.copy()
        
        if self.sort_var.get() == "priority":
            sorted_list.sort(key=lambda x: x.priority)
        elif self.sort_var.get() == "status":
            order = {"Running": 0, "Paused": 1, "Waiting": 2, "Completed": 3}
            sorted_list.sort(key=lambda x: order.get(x.status, 99))
        elif self.sort_var.get() == "start_time":
            sorted_list.sort(key=lambda x: x.start_time or "")
            
        return sorted_list

    def update_process_info(self):
        """Update process information display"""
        if self.selected_pid is not None:
            for p in self.process_list:
                if p.pid == self.selected_pid:
                    info_text = f"""
🔍 PROCESS INFORMATION
{'='*50}

📋 Basic Details:
   • Process ID: {p.pid}
   • Name: {p.name}
   • Priority: ⭐ {p.priority}
   • Status: {p.status}

📊 Execution Details:
   • Progress: {p.progress}%
   • Total Time: {p.sleep_time} seconds
   • Remaining: {p.remaining} seconds

⏰ Timing Information:
   • Start Time: {p.start_time or 'Not started'}
   • End Time: {p.end_time or 'Not completed'}

{'='*50}
                    """
                    self.info_text.delete("1.0", tk.END)
                    self.info_text.insert(tk.END, info_text)
                    break

    def draw_modern_gantt_chart(self):
        """Draw a modern, colorful Gantt chart"""
        self.gantt_canvas.delete("all")
        
        if not self.process_list:
            # Show empty state
            self.gantt_canvas.create_text(600, 200, text="📊 No processes to display", 
                                        font=('Segoe UI', 16), fill='#6b7280')
            self.gantt_canvas.create_text(600, 230, text="Add processes to see the Gantt chart", 
                                        font=('Segoe UI', 12), fill='#9ca3af')
            return
        
        y_start = 50
        bar_height = 30
        bar_spacing = 40
        x_start = 100
        scale = 20  # pixels per second
        
        # Draw title
        self.gantt_canvas.create_text(600, 20, text="📊 Process Execution Timeline", 
                                    font=('Segoe UI', 16, 'bold'), fill=self.colors['primary'])
        
        # Draw processes
        for i, process in enumerate(self.process_list):
            y = y_start + i * bar_spacing
            
            # Process label
            self.gantt_canvas.create_text(50, y + bar_height//2, 
                                        text=f"P{process.pid}: {process.name}", 
                                        font=('Segoe UI', 10, 'bold'),
                                        anchor='e', fill=self.colors['dark'])
            
            # Background bar
            total_width = process.sleep_time * scale
            self.gantt_canvas.create_rectangle(x_start, y, x_start + total_width, y + bar_height,
                                             fill='#e5e7eb', outline='#d1d5db', width=1)
            
            # Progress bar
            if process.progress > 0:
                progress_width = (process.progress / 100) * total_width
                color = self.get_status_color(process.status)
                
                self.gantt_canvas.create_rectangle(x_start, y, x_start + progress_width, y + bar_height,
                                                 fill=color, outline=color, width=0)
                
                # Add gradient effect (simple)
                gradient_color = self.lighten_color(color)
                self.gantt_canvas.create_rectangle(x_start, y, x_start + progress_width, y + bar_height//3,
                                                 fill=gradient_color, outline='', width=0)
            
            # Progress text
            if process.progress > 0:
                self.gantt_canvas.create_text(x_start + total_width//2, y + bar_height//2,
                                            text=f"{process.progress}%",
                                            font=('Segoe UI', 9, 'bold'),
                                            fill='white' if process.progress > 20 else self.colors['dark'])
            
            # Status indicator
            status_colors = {
                "Running": "🟢", "Paused": "🟡", "Waiting": "🔵", "Completed": "🟣"
            }
            status_emoji = status_colors.get(process.status, "⚪")
            self.gantt_canvas.create_text(x_start + total_width + 20, y + bar_height//2,
                                        text=f"{status_emoji} {process.status}",
                                        font=('Segoe UI', 9), anchor='w',
                                        fill=self.colors['dark'])

    def lighten_color(self, color):
        """Lighten a hex color for gradient effect"""
        # Simple color lightening
        color_map = {
            '#10b981': '#34d399',  # Green
            '#f59e0b': '#fbbf24',  # Yellow
            '#06b6d4': '#22d3ee',  # Cyan
            '#8b5cf6': '#a78bfa'   # Purple
        }
        return color_map.get(color, color)

    def log(self, msg):
        """Add message to log with modern formatting"""
        ts = datetime.datetime.now().strftime("[%H:%M:%S]")
        formatted_msg = f"{ts} {msg}\n"
        
        self.log_box.insert(tk.END, formatted_msg)
        self.log_box.see(tk.END)
        
        # Color coding for different message types
        if "✅" in msg or "🎉" in msg:
            # Success messages in green
            start_line = self.log_box.index(tk.END + "-2l linestart")
            end_line = self.log_box.index(tk.END + "-1l lineend")
            self.log_box.tag_add("success", start_line, end_line)
            self.log_box.tag_config("success", foreground="#10b981")
        elif "🔄" in msg or "🚀" in msg or "▶️" in msg:
            # Update messages in blue
            start_line = self.log_box.index(tk.END + "-2l linestart")
            end_line = self.log_box.index(tk.END + "-1l lineend")
            self.log_box.tag_add("info", start_line, end_line)
            self.log_box.tag_config("info", foreground="#06b6d4")

    def notify(self, message):
        """Show modern notification"""
        try:
            winsound.MessageBeep()
        except:
            pass  # Handle case where winsound is not available
        
        # Create a modern messagebox style notification
        messagebox.showinfo("🔔 Notification", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernSchedulerApp(root)
    root.mainloop()

# import tkinter as tk
# from tkinter import ttk, messagebox, Canvas
# import datetime
# import time
# import threading
# import queue as thread_queue
# import winsound

# class ManagedProcess:
#     def __init__(self, pid, name, sleep_time, priority, queue):
#         self.pid = pid
#         self.name = name
#         self.sleep_time = sleep_time
#         self.priority = priority
#         self.queue = queue
#         self.status = "Waiting"
#         self.start_time = None 
#         self.end_time = None
#         self.progress = 0
#         self.remaining = sleep_time
#         self.thread = None
#         self.pause_event = threading.Event()
#         self.pause_event.set()

#     def run(self):
#         self.start_time = datetime.datetime.now().strftime("%H:%M:%S")
#         self.queue.put(("gantt_start", self.pid, time.time()))
#         while self.remaining > 0:
#             self.pause_event.wait()
#             time.sleep(1)
#             self.remaining -= 1
#             self.progress = int(100 * (self.sleep_time - self.remaining) / self.sleep_time)
#             self.queue.put(("update", self.pid, self.progress))
#         self.end_time = datetime.datetime.now().strftime("%H:%M:%S")
#         self.status = "Completed"
#         self.queue.put(("completed", self.pid))
#         self.queue.put(("gantt_end", self.pid, time.time()))

#     def start(self):
#         self.thread = threading.Thread(target=self.run)
#         self.thread.start()

#     def pause(self):
#         self.pause_event.clear()

#     def resume(self):
#         self.pause_event.set()

# class SchedulerApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Multi Process Alarm Scheduler")
#         self.process_list = []
#         self.running_processes = []
#         self.paused_processes = []
#         self.pid_counter = 1
#         self.max_running = 2
#         self.queue = thread_queue.Queue()
#         self.preemptive_enabled = tk.BooleanVar(value=False)
#         self.selected_pid = None
#         self.gantt_data = {}

#         self.build_scrollable_ui()
#         self.update_gui()

#     def build_scrollable_ui(self):
#         canvas = Canvas(self.root)
#         scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
#         self.scroll_frame = ttk.Frame(canvas)

#         self.scroll_frame.bind(
#             "<Configure>",
#             lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
#         )

#         canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
#         canvas.configure(yscrollcommand=scrollbar.set)

#         canvas.pack(side="left", fill="both", expand=True)
#         scrollbar.pack(side="right", fill="y")

#         self.setup_ui(self.scroll_frame)

#     def setup_ui(self, frame):
#         ttk.Label(frame, text="Add New Process", font=('Helvetica', 12, 'bold')).pack(anchor='w')
#         form = ttk.Frame(frame)
#         form.pack(anchor='w', pady=5)
#         ttk.Label(form, text="Name:").grid(row=0, column=0)
#         self.name_entry = ttk.Entry(form, width=15)
#         self.name_entry.grid(row=0, column=1)

#         ttk.Label(form, text="Time (s):").grid(row=0, column=2)
#         self.sleep_entry = ttk.Entry(form, width=5)
#         self.sleep_entry.grid(row=0, column=3)

#         ttk.Label(form, text="Priority:").grid(row=0, column=4)
#         self.priority_box = ttk.Combobox(form, values=list(range(1, 11)), width=3)
#         self.priority_box.grid(row=0, column=5)
#         self.priority_box.set(5)

#         ttk.Button(form, text="Add", command=self.add_process).grid(row=0, column=6, padx=5)
#         ttk.Checkbutton(form, text="Primitive (Preemptive)", variable=self.preemptive_enabled).grid(row=0, column=7)

#         ttk.Label(frame, text="Sorting Options", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
#         sort_frame = ttk.Frame(frame)
#         sort_frame.pack(anchor='w')
#         self.sort_var = tk.StringVar(value="priority")
#         ttk.Radiobutton(sort_frame, text="Priority", variable=self.sort_var, value="priority").pack(side=tk.LEFT)
#         ttk.Radiobutton(sort_frame, text="Status", variable=self.sort_var, value="status").pack(side=tk.LEFT)
#         ttk.Radiobutton(sort_frame, text="Start Time", variable=self.sort_var, value="start_time").pack(side=tk.LEFT)

#         ttk.Label(frame, text="All Processes", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
#         self.process_table = tk.Text(frame, height=10, width=150)
#         self.process_table.pack()

#         ttk.Label(frame, text="Process Information", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
#         info_frame = ttk.Frame(frame)
#         info_frame.pack()
#         self.info_table = tk.Text(info_frame, height=5, width=150, wrap=tk.WORD)
#         self.info_scroll = ttk.Scrollbar(info_frame, command=self.info_table.yview)
#         self.info_table.configure(yscrollcommand=self.info_scroll.set)
#         self.info_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
#         self.info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

#         change_frame = ttk.Frame(frame)
#         change_frame.pack(anchor='w', pady=5)
#         ttk.Label(change_frame, text="Change Priority for PID:").pack(side=tk.LEFT)
#         self.pid_change_entry = ttk.Entry(change_frame, width=5)
#         self.pid_change_entry.pack(side=tk.LEFT)
#         ttk.Label(change_frame, text=" to ").pack(side=tk.LEFT)
#         self.new_priority_entry = ttk.Entry(change_frame, width=5)
#         self.new_priority_entry.pack(side=tk.LEFT)
#         ttk.Button(change_frame, text="Change", command=self.change_priority).pack(side=tk.LEFT, padx=5)

#         ttk.Label(frame, text="Process Logs", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
#         self.log_box = tk.Text(frame, height=8, width=150)
#         self.log_box.pack()

#         ttk.Label(frame, text="Gantt Chart", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
#         self.gantt_scroll_canvas = Canvas(frame, width=1000, height=220, bg="white")
#         self.gantt_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.gantt_scroll_canvas.yview)
#         self.gantt_inner_frame = ttk.Frame(self.gantt_scroll_canvas)
#         self.gantt_inner_frame.bind("<Configure>", lambda e: self.gantt_scroll_canvas.configure(scrollregion=self.gantt_scroll_canvas.bbox("all")))
#         self.gantt_scroll_canvas.create_window((0, 0), window=self.gantt_inner_frame, anchor="nw")
#         self.gantt_scroll_canvas.configure(yscrollcommand=self.gantt_scrollbar.set)
#         self.gantt_scroll_canvas.pack(side="left", fill="both", expand=True)
#         self.gantt_scrollbar.pack(side="right", fill="y")

#         self.gantt_canvas = Canvas(self.gantt_inner_frame, width=1000, height=1000, bg="white")
#         self.gantt_canvas.pack()

#         self.process_table.bind("<Button-1>", self.select_process)

#     def add_process(self):
#         name = self.name_entry.get()
#         try:
#             time_ = int(self.sleep_entry.get())
#             priority = int(self.priority_box.get())
#         except ValueError:
#             messagebox.showerror("Invalid Input", "Time and priority must be numbers.")
#             return
#         proc = ManagedProcess(self.pid_counter, name, time_, priority, self.queue)
#         self.process_list.append(proc)
#         self.log(f"Process {proc.pid} added with priority {priority}")
#         self.notify(f"Process {proc.pid} added.")
#         self.pid_counter += 1
#         self.schedule()

#     def change_priority(self):
#         try:
#             pid = int(self.pid_change_entry.get())
#             new_priority = int(self.new_priority_entry.get())
#         except ValueError:
#             messagebox.showerror("Invalid Input", "Priority and PID must be numbers.")
#             return
#         for p in self.process_list:
#             if p.pid == pid:
#                 old_priority = p.priority
#                 p.priority = new_priority
#                 self.log(f"Process {pid} priority changed from {old_priority} to {new_priority}")
#                 self.notify(f"Priority of Process {pid} changed.")
#                 self.schedule()
#                 break

#     def schedule(self):
#         self.running_processes = [p for p in self.process_list if p.status == "Running"]
#         self.paused_processes = [p for p in self.process_list if p.status == "Paused"]
#         waiting = [p for p in self.process_list if p.status == "Waiting"]

#         if self.preemptive_enabled.get():
#             all_active = self.running_processes + self.paused_processes + waiting
#             all_active.sort(key=lambda x: x.priority)
#             self.running_processes.clear()
#             self.paused_processes.clear()
#             for proc in all_active:
#                 if proc.status == "Completed":
#                     continue
#                 if len(self.running_processes) < self.max_running:
#                     if not proc.thread or not proc.thread.is_alive():
#                         proc.start()
#                     proc.resume()
#                     proc.status = "Running"
#                     self.running_processes.append(proc)
#                 else:
#                     proc.pause()
#                     proc.status = "Paused"
#                     self.paused_processes.append(proc)
#         else:
#             for p in waiting:
#                 if len(self.running_processes) < self.max_running:
#                     p.start()
#                     p.status = "Running"
#                     self.running_processes.append(p)

#     def update_gui(self):
#         try:
#             while True:
#                 msg = self.queue.get_nowait()
#                 if msg[0] == "update":
#                     pid, progress = msg[1], msg[2]
#                     for p in self.process_list:
#                         if p.pid == pid:
#                             p.progress = progress
#                 elif msg[0] == "completed":
#                     pid = msg[1]
#                     for p in self.process_list:
#                         if p.pid == pid:
#                             p.status = "Completed"
#                             self.log(f"Process {pid} completed.")
#                             self.notify(f"Process {pid} completed.")
#                             self.schedule()
#                 elif msg[0] == "gantt_start":
#                     self.gantt_data[msg[1]] = [msg[2], None]
#                 elif msg[0] == "gantt_end":
#                     self.gantt_data[msg[1]][1] = msg[2]
#         except thread_queue.Empty:
#             pass

#         self.process_table.delete("1.0", tk.END)
#         sorted_list = self.process_list
#         if self.sort_var.get() == "priority":
#             sorted_list = sorted(self.process_list, key=lambda x: x.priority)
#         elif self.sort_var.get() == "status":
#             order = {"Running": 0, "Paused": 1, "Waiting": 2, "Completed": 3}
#             sorted_list = sorted(self.process_list, key=lambda x: order.get(x.status, 99))
#         elif self.sort_var.get() == "start_time":
#             sorted_list = sorted(self.process_list, key=lambda x: x.start_time or "")

#         for p in sorted_list:
#             self.process_table.insert(tk.END, f"PID {p.pid} | {p.name} | Priority: {p.priority} | Status: {p.status} | Progress: {p.progress}%\n")

#         if self.selected_pid is not None:
#             for p in self.process_list:
#                 if p.pid == self.selected_pid:
#                     current_scroll = self.info_table.yview()
#                     self.info_table.delete("1.0", tk.END)
#                     self.info_table.insert(tk.END, f"Process #{p.pid}\nName: {p.name}\nPriority: {p.priority}\nStatus: {p.status}\nProgress: {p.progress}%\nStart: {p.start_time}\nEnd: {p.end_time}\nRemaining: {p.remaining}s")
#                     self.info_table.yview_moveto(current_scroll[0])
#                     break

#         self.draw_gantt_chart()
#         self.root.after(1000, self.update_gui)

#     def draw_gantt_chart(self):
#         self.gantt_canvas.delete("all")
#         x = 10
#         y = 20
#         height = 20
#         scale = 10

#         for pid, (start, end) in self.gantt_data.items():
#             if end is None:
#                 end = time.time()
#             width = (end - start) * scale
#             self.gantt_canvas.create_rectangle(x, y, x + width, y + height, fill="skyblue")
#             self.gantt_canvas.create_text(x + width / 2, y + 10, text=f"P{pid}")
#             y += 30

#     def select_process(self, event):
#         try:
#             index = self.process_table.index(f"@{event.x},{event.y}")
#             line = self.process_table.get(f"{index} linestart", f"{index} lineend")
#             pid = int(line.split()[1])
#             self.selected_pid = pid
#         except Exception:
#             pass

#     def log(self, msg):
#         ts = datetime.datetime.now().strftime("[%H:%M:%S]")
#         self.log_box.insert(tk.END, f"{ts} {msg}\n")
#         self.log_box.see(tk.END)

#     def notify(self, message):
#         winsound.MessageBeep()
#         messagebox.showinfo("Notification", message)

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = SchedulerApp(root)
#     root.mainloop()
