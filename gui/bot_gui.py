"""
Enhanced Bot GUI - Settings and Visual Feedback
Runs alongside the bot without interfering
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

class BotGUI:
    """GUI for bot settings and visual feedback"""
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.root = tk.Tk()
        self.root.title("Enhanced Bot Control Panel")
        self.root.geometry("900x700")
        
        # Message queue for thread-safe updates
        self.message_queue = queue.Queue()
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._setup_ui()
        self._start_update_loop()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Conversation Monitor
        self.monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_frame, text="Conversation Monitor")
        self._setup_monitor_tab()
        
        # Tab 2: Settings
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self._setup_settings_tab()
        
        # Tab 3: Notes Manager
        self.notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notes_frame, text="Notes Manager")
        self._setup_notes_tab()
        
        # Tab 4: Tasks & Projects
        self.tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_frame, text="Tasks & Projects")
        self._setup_tasks_tab()
        
        # Tab 5: System Status
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="System Status")
        self._setup_status_tab()
        
        # Tab 5: Quick Actions
        self.actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.actions_frame, text="Quick Actions")
        self._setup_actions_tab()
    
    def _setup_monitor_tab(self):
        """Setup conversation monitor"""
        # Header
        header = ttk.Label(
            self.monitor_frame,
            text="Live Conversation Feed",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=10)
        
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(
            self.monitor_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10)
        )
        self.conversation_text.pack(padx=10, pady=5, fill='both', expand=True)
        
        # Configure tags for coloring
        self.conversation_text.tag_config('user', foreground='#2196F3', font=('Consolas', 10, 'bold'))
        self.conversation_text.tag_config('bot', foreground='#4CAF50', font=('Consolas', 10, 'bold'))
        self.conversation_text.tag_config('system', foreground='#FF9800', font=('Consolas', 10, 'italic'))
        self.conversation_text.tag_config('emotion', foreground='#9C27B0', font=('Consolas', 9))
        
        # Control buttons
        btn_frame = ttk.Frame(self.monitor_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Clear Log", command=self.clear_conversation).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Save Log", command=self.save_conversation).pack(side='left', padx=5)
    
    def _setup_settings_tab(self):
        """Setup settings controls"""
        # Header
        header = ttk.Label(
            self.settings_frame,
            text="Bot Configuration",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.settings_frame)
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Sentience Features
        sentience_frame = ttk.LabelFrame(scrollable_frame, text="Sentience Features", padding=10)
        sentience_frame.pack(fill='x', padx=10, pady=5)
        
        self.sentience_vars = {}
        sentience_features = [
            ('ENABLE_SLEEP_MODE', 'Sleep Mode (bye = sleep)'),
            ('ENABLE_DREAM_STATE', 'Dream State'),
            ('ENABLE_MOOD_DRIFT', 'Mood Drift'),
            ('ENABLE_MEMORY_TRIGGERS', 'Memory Triggers'),
            ('ENABLE_INTERNAL_DIALOGUE', 'Internal Dialogue'),
            ('ENABLE_GOAL_TRACKING', 'Goal Tracking'),
            ('ENABLE_TEMPORAL_AWARENESS', 'Temporal Awareness'),
            ('ENABLE_UNCERTAINTY_EXPRESSION', 'Uncertainty Expression'),
            ('ENABLE_OPINION_FORMATION', 'Opinion Formation'),
            ('ENABLE_CONVERSATION_THREADING', 'Conversation Threading'),
        ]
        
        for i, (key, label) in enumerate(sentience_features):
            var = tk.BooleanVar(value=getattr(config, key, True))
            self.sentience_vars[key] = var
            cb = ttk.Checkbutton(sentience_frame, text=label, variable=var)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=2)
        
        # Advanced Features
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Features", padding=10)
        advanced_frame.pack(fill='x', padx=10, pady=5)
        
        self.advanced_vars = {}
        advanced_features = [
            ('USE_VECTOR_MEMORY', 'Vector Memory'),
            ('USE_STREAMING', 'Streaming Responses'),
            ('USE_BACKGROUND_TASKS', 'Background Tasks'),
            ('USE_LEARNING_SYSTEM', 'Learning System'),
            ('USE_USER_MODELING', 'User Modeling'),
        ]
        
        for i, (key, label) in enumerate(advanced_features):
            var = tk.BooleanVar(value=getattr(config, key, True))
            self.advanced_vars[key] = var
            cb = ttk.Checkbutton(advanced_frame, text=label, variable=var)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=2)
        
        # Voice Settings
        voice_frame = ttk.LabelFrame(scrollable_frame, text="Voice Settings", padding=10)
        voice_frame.pack(fill='x', padx=10, pady=5)
        
        row = 0
        
        # TTS Engine selector
        ttk.Label(voice_frame, text="TTS Engine:").grid(row=row, column=0, sticky='w', padx=5)
        self.tts_engine_var = tk.StringVar(value=getattr(config, 'TTS_ENGINE', 'edge'))
        engine_combo = ttk.Combobox(
            voice_frame, textvariable=self.tts_engine_var,
            values=['edge', 'pyttsx3'], state='readonly', width=18
        )
        engine_combo.grid(row=row, column=1, padx=5, sticky='w')
        ttk.Label(voice_frame, text="edge = natural, pyttsx3 = offline").grid(row=row, column=2, sticky='w', padx=5)
        row += 1
        
        # Edge-TTS Voice selector
        ttk.Label(voice_frame, text="Voice:").grid(row=row, column=0, sticky='w', padx=5)
        self.edge_voice_var = tk.StringVar(value=getattr(config, 'EDGE_TTS_VOICE', 'en-US-AriaNeural'))
        voice_options = [
            'en-US-AriaNeural', 'en-US-JennyNeural', 'en-GB-SoniaNeural',
            'en-AU-NatashaNeural', 'en-US-GuyNeural', 'en-US-AndrewNeural',
            'en-GB-RyanNeural',
        ]
        voice_combo = ttk.Combobox(
            voice_frame, textvariable=self.edge_voice_var,
            values=voice_options, state='readonly', width=24
        )
        voice_combo.grid(row=row, column=1, padx=5, sticky='w')
        row += 1
        
        # Legacy pyttsx3 Speech Rate (also used as fallback)
        ttk.Label(voice_frame, text="Fallback Rate:").grid(row=row, column=0, sticky='w', padx=5)
        self.speech_rate_var = tk.IntVar(value=config.DEFAULT_SPEECH_RATE)
        rate_scale = ttk.Scale(
            voice_frame, from_=80, to=250,
            variable=self.speech_rate_var, orient='horizontal', length=200
        )
        rate_scale.grid(row=row, column=1, padx=5)
        ttk.Label(voice_frame, textvariable=self.speech_rate_var).grid(row=row, column=2)
        row += 1
        
        # Volume
        ttk.Label(voice_frame, text="Volume:").grid(row=row, column=0, sticky='w', padx=5)
        self.volume_var = tk.DoubleVar(value=config.DEFAULT_VOLUME)
        vol_scale = ttk.Scale(
            voice_frame, from_=0.0, to=1.0,
            variable=self.volume_var, orient='horizontal', length=200
        )
        vol_scale.grid(row=row, column=1, padx=5)
        vol_label = ttk.Label(voice_frame, text="")
        vol_label.grid(row=row, column=2)
        
        def update_vol_label(*args):
            vol_label.config(text=f"{self.volume_var.get():.2f}")
        self.volume_var.trace('w', update_vol_label)
        update_vol_label()
        row += 1
        
        # Voice Barge-In
        self.barge_in_var = tk.BooleanVar(value=getattr(config, 'VOICE_BARGE_IN', True))
        ttk.Checkbutton(
            voice_frame, text="Voice Barge-In (interrupt by speaking)",
            variable=self.barge_in_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1
        
        # Barge-In Sensitivity
        ttk.Label(voice_frame, text="Barge-In Sensitivity:").grid(row=row, column=0, sticky='w', padx=5)
        self.barge_sensitivity_var = tk.DoubleVar(value=getattr(config, 'BARGE_IN_SENSITIVITY', 2.0))
        sens_scale = ttk.Scale(
            voice_frame, from_=1.0, to=4.0,
            variable=self.barge_sensitivity_var, orient='horizontal', length=200
        )
        sens_scale.grid(row=row, column=1, padx=5)
        sens_label = ttk.Label(voice_frame, text="")
        sens_label.grid(row=row, column=2)
        
        def update_sens_label(*args):
            sens_label.config(text=f"{self.barge_sensitivity_var.get():.1f}x")
        self.barge_sensitivity_var.trace('w', update_sens_label)
        update_sens_label()
        
        # Proactive Behavior Settings
        proactive_frame = ttk.LabelFrame(scrollable_frame, text="Proactive Behavior", padding=10)
        proactive_frame.pack(fill='x', padx=10, pady=5)
        
        self.proactive_enabled = tk.BooleanVar(value=config.ENABLE_PROACTIVE_BEHAVIOR)
        ttk.Checkbutton(
            proactive_frame,
            text="Enable Proactive Thoughts",
            variable=self.proactive_enabled
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        ttk.Label(proactive_frame, text="Min Interval (seconds):").grid(row=1, column=0, sticky='w', padx=5)
        self.proactive_min_var = tk.IntVar(value=config.PROACTIVE_INTERVAL_MIN)
        ttk.Entry(proactive_frame, textvariable=self.proactive_min_var, width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(proactive_frame, text="Max Interval (seconds):").grid(row=2, column=0, sticky='w', padx=5)
        self.proactive_max_var = tk.IntVar(value=config.PROACTIVE_INTERVAL_MAX)
        ttk.Entry(proactive_frame, textvariable=self.proactive_max_var, width=10).grid(row=2, column=1, padx=5)
        
        # Apply button
        ttk.Button(
            scrollable_frame,
            text="Apply Settings",
            command=self.apply_settings,
            style='Accent.TButton'
        ).pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _setup_notes_tab(self):
        """Setup notes manager tab"""
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
    
    def _setup_status_tab(self):
        """Setup system status display"""
        # Header
        header = ttk.Label(
            self.status_frame,
            text="System Status",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=10)
        
        # Status display
        self.status_text = scrolledtext.ScrolledText(
            self.status_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10)
        )
        self.status_text.pack(padx=10, pady=5, fill='both', expand=True)
        
        # Refresh button
        ttk.Button(
            self.status_frame,
            text="Refresh Status",
            command=self.update_status
        ).pack(pady=5)
        
        # Initial status
        self.update_status()
    
    def _setup_actions_tab(self):
        """Setup quick actions"""
        # Header
        header = ttk.Label(
            self.actions_frame,
            text="Quick Actions",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=10)
        
        # Program Control
        prog_frame = ttk.LabelFrame(self.actions_frame, text="Program Control", padding=10)
        prog_frame.pack(fill='x', padx=10, pady=5)
        
        programs = ['Calculator', 'Notepad', 'Chrome', 'Explorer', 'Terminal', 'VS Code']
        for i, prog in enumerate(programs):
            row_frame = ttk.Frame(prog_frame)
            row_frame.pack(fill='x', pady=5)
            
            ttk.Label(row_frame, text=prog, width=15).pack(side='left', padx=5)
            ttk.Button(
                row_frame,
                text="Open",
                command=lambda p=prog: self.quick_open(p)
            ).pack(side='left', padx=2)
            ttk.Button(
                row_frame,
                text="Close",
                command=lambda p=prog: self.quick_close(p)
            ).pack(side='left', padx=2)
        
        # Bot Control
        bot_frame = ttk.LabelFrame(self.actions_frame, text="Bot Control", padding=10)
        bot_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(bot_frame, text="Put Bot to Sleep", command=self.sleep_bot).pack(pady=5)
        ttk.Button(bot_frame, text="Wake Bot", command=self.wake_bot).pack(pady=5)
        ttk.Button(bot_frame, text="Clear Bot Memory", command=self.clear_memory).pack(pady=5)
    
    def _start_update_loop(self):
        """Start the GUI update loop"""
        self.root.after(100, self._process_queue)
    
    def _process_queue(self):
        """Process messages from the queue"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)
    
    def _handle_message(self, message):
        """Handle a message from the bot"""
        msg_type = message.get('type')
        
        if msg_type == 'conversation':
            self._add_conversation(
                message.get('speaker'),
                message.get('text'),
                message.get('emotion', '')
            )
        elif msg_type == 'system':
            self._add_system_message(message.get('text'))
    
    def _add_conversation(self, speaker: str, text: str, emotion: str = ''):
        """Add conversation to monitor"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        self.conversation_text.insert('end', f"[{timestamp}] ", 'system')
        
        if speaker.lower() == 'user':
            self.conversation_text.insert('end', "USER: ", 'user')
        else:
            if emotion:
                self.conversation_text.insert('end', f"{speaker} ", 'bot')
                self.conversation_text.insert('end', f"({emotion}): ", 'emotion')
            else:
                self.conversation_text.insert('end', f"{speaker}: ", 'bot')
        
        self.conversation_text.insert('end', f"{text}\n\n")
        self.conversation_text.see('end')
    
    def _add_system_message(self, text: str):
        """Add system message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.conversation_text.insert('end', f"[{timestamp}] ", 'system')
        self.conversation_text.insert('end', f"SYSTEM: {text}\n", 'system')
        self.conversation_text.see('end')
    
    def add_message(self, msg_type: str, **kwargs):
        """Thread-safe method to add messages"""
        self.message_queue.put({'type': msg_type, **kwargs})
    
    def clear_conversation(self):
        """Clear conversation log"""
        self.conversation_text.delete('1.0', 'end')
    
    def save_conversation(self):
        """Save conversation to file"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.conversation_text.get('1.0', 'end'))
            self._add_system_message(f"Saved to {filename}")
    
    def apply_settings(self):
        """Apply settings changes"""
        # Update config (note: some require restart)
        for key, var in {**self.sentience_vars, **self.advanced_vars}.items():
            setattr(config, key, var.get())
        
        config.DEFAULT_SPEECH_RATE = self.speech_rate_var.get()
        config.DEFAULT_VOLUME = self.volume_var.get()
        config.ENABLE_PROACTIVE_BEHAVIOR = self.proactive_enabled.get()
        config.PROACTIVE_INTERVAL_MIN = self.proactive_min_var.get()
        config.PROACTIVE_INTERVAL_MAX = self.proactive_max_var.get()
        
        # Push TTS engine + voice settings to config
        config.TTS_ENGINE = self.tts_engine_var.get()
        config.EDGE_TTS_VOICE = self.edge_voice_var.get()
        config.VOICE_BARGE_IN = self.barge_in_var.get()
        config.BARGE_IN_SENSITIVITY = self.barge_sensitivity_var.get()
        
        # Push to live NaturalVoiceEngine (edge-tts path)
        if self.bot and hasattr(self.bot, 'voice_engine') and self.bot.voice_engine:
            ve = self.bot.voice_engine
            ve.voice = self.edge_voice_var.get()
            ve.barge_in_enabled = self.barge_in_var.get()
            ve.barge_in_multiplier = self.barge_sensitivity_var.get()
        
        # Push to legacy pyttsx3 voice manager (fallback path)
        if self.bot and hasattr(self.bot, 'voice_input') and self.bot.voice_input:
            try:
                engine = getattr(self.bot.voice_input, 'engine', None)
                if engine:
                    engine.setProperty('rate', self.speech_rate_var.get())
                    engine.setProperty('volume', self.volume_var.get())
            except Exception:
                pass
        
        self._add_system_message("Settings applied! Voice settings updated live. TTS engine change takes effect on next speech.")
    
    def update_status(self):
        """Update system status"""
        self.status_text.delete('1.0', 'end')
        
        # Build V2.2 sentience status
        v22_status = "Not Available"
        if self.bot:
            v22_parts = []
            if hasattr(self.bot, 'emotional_complexity') and self.bot.emotional_complexity:
                v22_parts.append("Emotional Complexity (LLM)")
            if hasattr(self.bot, 'metacognition') and self.bot.metacognition:
                v22_parts.append("Metacognition (LLM)")
            if hasattr(self.bot, 'vulnerability') and self.bot.vulnerability:
                v22_parts.append("Vulnerability (LLM)")
            if hasattr(self.bot, 'os_awareness') and self.bot.os_awareness:
                v22_parts.append("OS Awareness")
            v22_status = ", ".join(v22_parts) if v22_parts else "None active"
        
        # Build Phase 5 status
        phase5_status = "Not Available"
        if self.bot and hasattr(self.bot, 'phase5') and self.bot.phase5:
            p5_parts = []
            if hasattr(self.bot.phase5, 'theory_of_mind'): p5_parts.append("Theory of Mind (LLM)")
            if hasattr(self.bot.phase5, 'dream_system'): p5_parts.append("Dream System (LLM)")
            if hasattr(self.bot.phase5, 'ethics'): p5_parts.append("Ethical Reasoning (LLM)")
            if hasattr(self.bot.phase5, 'homeostasis'): p5_parts.append("Homeostasis (LLM)")
            if hasattr(self.bot.phase5, 'motivation'): p5_parts.append("Intrinsic Motivation")
            if hasattr(self.bot.phase5, 'promises'): p5_parts.append("Promise Tracking")
            phase5_status = ", ".join(p5_parts) if p5_parts else "None active"
        
        status = f"""=== Seven AI v2.2 System Status ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATABASE:
  Location: {config.DB_PATH}
  Status: {'Connected' if config.DB_PATH.exists() else 'Not Found'}

OLLAMA:
  URL: {config.OLLAMA_URL}
  Model: {config.OLLAMA_MODEL}

SENTIENCE FEATURES (Core):
  Sleep Mode: {'Enabled' if config.ENABLE_SLEEP_MODE else 'Disabled'}
  Mood Drift: {'Enabled' if config.ENABLE_MOOD_DRIFT else 'Disabled'}
  Memory Triggers: {'Enabled' if config.ENABLE_MEMORY_TRIGGERS else 'Disabled'}
  Internal Dialogue: {'Enabled' if config.ENABLE_INTERNAL_DIALOGUE else 'Disabled'}
  Goal Tracking: {'Enabled' if config.ENABLE_GOAL_TRACKING else 'Disabled'}

V2.2 ENHANCED SENTIENCE (LLM-Powered):
  {v22_status}

PHASE 5 SYSTEMS (LLM-Powered):
  {phase5_status}

ADVANCED FEATURES:
  Vector Memory: {'Enabled' if config.USE_VECTOR_MEMORY else 'Disabled'}
  Streaming: {'Enabled' if config.USE_STREAMING else 'Disabled'}
  Background Tasks: {'Enabled' if config.USE_BACKGROUND_TASKS else 'Disabled'}
  Learning System: {'Enabled' if config.USE_LEARNING_SYSTEM else 'Disabled'}

VOICE:
  Speech Rate: {config.DEFAULT_SPEECH_RATE}
  Volume: {config.DEFAULT_VOLUME}

PROACTIVE BEHAVIOR:
  Enabled: {'Yes' if config.ENABLE_PROACTIVE_BEHAVIOR else 'No'}
  Interval: {config.PROACTIVE_INTERVAL_MIN}-{config.PROACTIVE_INTERVAL_MAX}s
"""
        self.status_text.insert('1.0', status)
    
    def quick_open(self, program: str):
        """Quick open program"""
        if self.bot and self.bot.commands:
            result = self.bot.commands.open_program(program.lower())
            self._add_system_message(f"Open {program}: {result}")
        else:
            self._add_system_message(f"Bot not connected - cannot open {program}")
    
    def quick_close(self, program: str):
        """Quick close program"""
        if self.bot and self.bot.commands:
            result = self.bot.commands.close_program(program.lower())
            self._add_system_message(f"Close {program}: {result}")
        else:
            self._add_system_message(f"Bot not connected - cannot close {program}")
    
    def sleep_bot(self):
        """Put bot to sleep"""
        if self.bot and hasattr(self.bot, '_enter_sleep_mode'):
            self.bot._enter_sleep_mode()
            self._add_system_message("Bot entering sleep mode")
        else:
            self._add_system_message("Bot not connected")
    
    def wake_bot(self):
        """Wake bot"""
        if self.bot and hasattr(self.bot, '_wake_from_sleep'):
            self.bot._wake_from_sleep()
            self._add_system_message("Bot waking up")
        else:
            self._add_system_message("Bot not connected")
    
    def clear_memory(self):
        """Clear bot memory"""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm", "Clear all bot memory? This cannot be undone."):
            if self.bot and hasattr(self.bot, 'memory'):
                try:
                    self.bot.memory.clear_all_sessions()
                    self._add_system_message("Memory cleared")
                except Exception as e:
                    self._add_system_message(f"Failed to clear memory: {e}")
            else:
                self._add_system_message("Bot not connected")
    
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
    
    def run(self):
        """Start the GUI (blocking)"""
        self.root.mainloop()
    
    def run_async(self):
        """Start the GUI in a separate thread"""
        gui_thread = threading.Thread(target=self.run, daemon=True)
        gui_thread.start()
        return gui_thread

def launch_gui(bot_instance=None):
    """Launch the GUI"""
    gui = BotGUI(bot_instance)
    return gui
