"""
Notes and Tasks tab methods for bot_gui.py
Insert these methods after _setup_settings_tab
"""

def _setup_notes_tab(self):
    """Setup notes manager tab"""
    import tkinter.scrolledtext as scrolledtext
    from tkinter import ttk
    
    # Header
    header = ttk.Label(
        self.notes_frame,
        text="Notes Manager",
        font=('Arial', 14, 'bold')
    )
    header.pack(pady=10)
    
    # Control buttons at top
    btn_frame_top = ttk.Frame(self.notes_frame)
    btn_frame_top.pack(fill='x', padx=10, pady=5)
    
    ttk.Button(btn_frame_top, text="Refresh Notes", command=self.refresh_notes).pack(side='left', padx=5)
    ttk.Button(btn_frame_top, text="Add Note", command=self.add_note_gui).pack(side='left', padx=5)
    ttk.Button(btn_frame_top, text="Delete Selected", command=self.delete_selected_note).pack(side='left', padx=5)
    
    # Search and filter
    search_frame = ttk.Frame(self.notes_frame)
    search_frame.pack(fill='x', padx=10, pady=5)
    
    ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
    self.note_search_var = tk.StringVar()
    ttk.Entry(search_frame, textvariable=self.note_search_var, width=30).pack(side='left', padx=5)
    ttk.Button(search_frame, text="Search", command=self.search_notes_gui).pack(side='left', padx=2)
    ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side='left', padx=2)
    
    ttk.Label(search_frame, text="Category:").pack(side='left', padx=10)
    self.note_category_var = tk.StringVar(value="all")
    categories = ['all', 'general', 'work', 'personal', 'ideas', 'reminders', 'shopping']
    ttk.Combobox(search_frame, textvariable=self.note_category_var, values=categories, 
                 width=15, state='readonly').pack(side='left', padx=5)
    ttk.Button(search_frame, text="Filter", command=self.filter_notes).pack(side='left', padx=2)
    
    # Notes table
    table_frame = ttk.Frame(self.notes_frame)
    table_frame.pack(fill='both', expand=True, padx=10, pady=5)
    
    # Scrollbars
    tree_scroll_y = ttk.Scrollbar(table_frame, orient='vertical')
    tree_scroll_x = ttk.Scrollbar(table_frame, orient='horizontal')
    
    # Treeview
    self.notes_tree = ttk.Treeview(
        table_frame,
        columns=('ID', 'Time', 'Category', 'Content', 'Priority'),
        show='headings',
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set,
        height=10
    )
    
    # Configure scrollbars
    tree_scroll_y.config(command=self.notes_tree.yview)
    tree_scroll_x.config(command=self.notes_tree.xview)
    
    # Column headings
    self.notes_tree.heading('ID', text='ID')
    self.notes_tree.heading('Time', text='Time Ago')
    self.notes_tree.heading('Category', text='Category')
    self.notes_tree.heading('Content', text='Content')
    self.notes_tree.heading('Priority', text='Priority')
    
    # Column widths
    self.notes_tree.column('ID', width=50)
    self.notes_tree.column('Time', width=100)
    self.notes_tree.column('Category', width=100)
    self.notes_tree.column('Content', width=300)
    self.notes_tree.column('Priority', width=80)
    
    # Pack
    self.notes_tree.pack(side='left', fill='both', expand=True)
    tree_scroll_y.pack(side='right', fill='y')
    tree_scroll_x.pack(side='bottom', fill='x')
    
    # Bind selection
    self.notes_tree.bind('<<TreeviewSelect>>', self.on_note_select)
    
    # Detail view
    detail_frame = ttk.LabelFrame(self.notes_frame, text="Note Details", padding=10)
    detail_frame.pack(fill='both', expand=True, padx=10, pady=5)
    
    self.note_detail_text = scrolledtext.ScrolledText(
        detail_frame,
        wrap=tk.WORD,
        height=6,
        font=('Arial', 10)
    )
    self.note_detail_text.pack(fill='both', expand=True)
    
    # Initial load
    self.refresh_notes()

def _setup_tasks_tab(self):
    """Setup tasks and projects tab"""
    import tkinter.scrolledtext as scrolledtext
    from tkinter import ttk
    
    # Header
    header = ttk.Label(
        self.tasks_frame,
        text="Tasks & Projects",
        font=('Arial', 14, 'bold')
    )
    header.pack(pady=10)
    
    # Tasks section
    tasks_section = ttk.LabelFrame(self.tasks_frame, text="Active Tasks", padding=10)
    tasks_section.pack(fill='both', expand=True, padx=10, pady=5)
    
    # Tasks list
    self.tasks_text = scrolledtext.ScrolledText(
        tasks_section,
        wrap=tk.WORD,
        height=10,
        font=('Arial', 10)
    )
    self.tasks_text.pack(fill='both', expand=True)
    
    # Task buttons
    task_btn_frame = ttk.Frame(tasks_section)
    task_btn_frame.pack(fill='x', pady=5)
    
    ttk.Button(task_btn_frame, text="Refresh Tasks", command=self.refresh_tasks).pack(side='left', padx=5)
    ttk.Button(task_btn_frame, text="Add Task", command=self.add_task_gui).pack(side='left', padx=5)
    
    # Projects section
    projects_section = ttk.LabelFrame(self.tasks_frame, text="Active Projects", padding=10)
    projects_section.pack(fill='both', expand=True, padx=10, pady=5)
    
    # Projects list
    self.projects_text = scrolledtext.ScrolledText(
        projects_section,
        wrap=tk.WORD,
        height=8,
        font=('Arial', 10)
    )
    self.projects_text.pack(fill='both', expand=True)
    
    # Project buttons
    proj_btn_frame = ttk.Frame(projects_section)
    proj_btn_frame.pack(fill='x', pady=5)
    
    ttk.Button(proj_btn_frame, text="Refresh Projects", command=self.refresh_projects).pack(side='left', padx=5)
    
    # Initial load
    self.refresh_tasks()
    self.refresh_projects()

# Notes management methods
def refresh_notes(self):
    """Refresh notes display"""
    if not self.bot or not hasattr(self.bot, 'notes') or not self.bot.notes:
        return
    
    try:
        # Clear existing
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        # Get notes
        notes = self.bot.notes.get_all_notes(limit=100)
        
        # Populate tree
        for note in notes:
            time_ago = self.bot.notes.format_time_ago(note['timestamp'])
            priority_stars = '[OK]' * note['importance']
            content_preview = note['content'][:50] + '...' if len(note['content']) > 50 else note['content']
            
            self.notes_tree.insert('', 'end', values=(
                note['id'],
                time_ago,
                note['category'],
                content_preview,
                priority_stars
            ))
    except Exception as e:
        print(f"Error refreshing notes: {e}")

def add_note_gui(self):
    """Add note via GUI"""
    from tkinter import simpledialog
    content = simpledialog.askstring("Add Note", "Enter note content:")
    if content and self.bot and hasattr(self.bot, 'notes'):
        try:
            self.bot.notes.add_note(content)
            self.refresh_notes()
            self._add_system_message(f"Note added")
        except Exception as e:
            self._add_system_message(f"Failed to add note: {e}")

def delete_selected_note(self):
    """Delete selected note"""
    selection = self.notes_tree.selection()
    if not selection:
        return
    
    try:
        values = self.notes_tree.item(selection[0], 'values')
        note_id = int(values[0])
        
        if self.bot and hasattr(self.bot, 'notes'):
            self.bot.notes.delete_note(note_id)
            self.refresh_notes()
            self._add_system_message(f"Note deleted")
    except Exception as e:
        self._add_system_message(f"Failed to delete note: {e}")

def search_notes_gui(self):
    """Search notes"""
    query = self.note_search_var.get()
    if not query:
        self.refresh_notes()
        return
    
    if not self.bot or not hasattr(self.bot, 'notes'):
        return
    
    try:
        # Clear existing
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        # Search
        notes = self.bot.notes.search_notes(query)
        
        # Populate
        for note in notes:
            time_ago = self.bot.notes.format_time_ago(note['timestamp'])
            priority_stars = '[OK]' * note['importance']
            content_preview = note['content'][:50] + '...' if len(note['content']) > 50 else note['content']
            
            self.notes_tree.insert('', 'end', values=(
                note['id'],
                time_ago,
                note['category'],
                content_preview,
                priority_stars
            ))
    except Exception as e:
        print(f"Error searching notes: {e}")

def clear_search(self):
    """Clear search and show all notes"""
    self.note_search_var.set('')
    self.refresh_notes()

def filter_notes(self):
    """Filter notes by category"""
    category = self.note_category_var.get()
    
    if category == 'all':
        self.refresh_notes()
        return
    
    if not self.bot or not hasattr(self.bot, 'notes'):
        return
    
    try:
        # Clear existing
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        # Get all and filter
        notes = self.bot.notes.get_all_notes(limit=1000)
        filtered = [n for n in notes if n['category'] == category]
        
        # Populate
        for note in filtered:
            time_ago = self.bot.notes.format_time_ago(note['timestamp'])
            priority_stars = '[OK]' * note['importance']
            content_preview = note['content'][:50] + '...' if len(note['content']) > 50 else note['content']
            
            self.notes_tree.insert('', 'end', values=(
                note['id'],
                time_ago,
                note['category'],
                content_preview,
                priority_stars
            ))
    except Exception as e:
        print(f"Error filtering notes: {e}")

def on_note_select(self, event):
    """Show full note details when selected"""
    selection = self.notes_tree.selection()
    if not selection:
        return
    
    try:
        values = self.notes_tree.item(selection[0], 'values')
        note_id = int(values[0])
        
        if self.bot and hasattr(self.bot, 'notes'):
            # Find note by ID
            notes = self.bot.notes.get_all_notes(limit=1000)
            for note in notes:
                if note['id'] == note_id:
                    detail_text = f"Category: {note['category']}\n"
                    detail_text += f"Created: {note['timestamp']}\n"
                    detail_text += f"Importance: {'[OK]' * note['importance']}\n"
                    detail_text += f"\nContent:\n{note['content']}"
                    
                    self.note_detail_text.delete('1.0', tk.END)
                    self.note_detail_text.insert('1.0', detail_text)
                    break
    except Exception as e:
        pass

# Tasks and Projects methods
def refresh_tasks(self):
    """Refresh tasks display"""
    if not self.bot or not hasattr(self.bot, 'tasks') or not self.bot.tasks:
        self.tasks_text.delete('1.0', tk.END)
        self.tasks_text.insert('1.0', "Task management not available")
        return
    
    try:
        tasks = self.bot.tasks.get_active_tasks(limit=20)
        self.tasks_text.delete('1.0', tk.END)
        
        if not tasks:
            self.tasks_text.insert('1.0', "No active tasks")
        else:
            for i, task in enumerate(tasks, 1):
                priority_stars = '[OK]' * task['priority']
                task_text = f"{i}. {task['title']} {priority_stars}\n"
                if task['due_date']:
                    task_text += f"   Due: {task['due_date']}\n"
                self.tasks_text.insert('end', task_text)
    except Exception as e:
        self.tasks_text.delete('1.0', tk.END)
        self.tasks_text.insert('1.0', f"Error loading tasks: {e}")

def add_task_gui(self):
    """Add task via GUI"""
    from tkinter import simpledialog
    title = simpledialog.askstring("Add Task", "Enter task title:")
    if title and self.bot and hasattr(self.bot, 'tasks'):
        try:
            self.bot.tasks.add_task(title)
            self.refresh_tasks()
            self._add_system_message(f"Task added: {title}")
        except Exception as e:
            self._add_system_message(f"Failed to add task: {e}")

def refresh_projects(self):
    """Refresh projects display"""
    if not self.bot or not hasattr(self.bot, 'projects') or not self.bot.projects:
        self.projects_text.delete('1.0', tk.END)
        self.projects_text.insert('1.0', "Project tracking not available")
        return
    
    try:
        projects = self.bot.projects.get_active_projects()
        self.projects_text.delete('1.0', tk.END)
        
        if not projects:
            self.projects_text.insert('1.0', "No active projects")
        else:
            for i, proj in enumerate(projects, 1):
                proj_text = f"{i}. {proj['name']} - {proj['progress']}% complete\n"
                proj_text += f"   Last updated: {proj['last_updated']}\n"
                self.projects_text.insert('end', proj_text)
    except Exception as e:
        self.projects_text.delete('1.0', tk.END)
        self.projects_text.insert('1.0', f"Error loading projects: {e}")
