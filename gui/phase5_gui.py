"""
COMPLETE Phase 5 GUI - ABSOLUTELY EVERYTHING + NEW ENHANCEMENTS
Every metric, setting, state, relationship, learning - TOTAL DISPLAY
Version 1.2.0 - Enhanced Edition
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

class CompletePhase5GUI:
    """
    ULTIMATE COMPLETE GUI - Shows EVERYTHING Seven can do
    All settings, states, metrics, systems, relationships, learnings
    """
    
    def __init__(self, bot_instance=None, start_minimized=False):
        self.bot = bot_instance
        self.start_minimized = start_minimized
        self.root = tk.Tk()
        self.root.title("Seven AI - Complete Sentience Dashboard v2.0")
        self.root.geometry("1400x950")
        
        self.message_queue = queue.Queue()
        self.update_interval = 100  # ms
        
        # Professional color scheme
        self.bg_dark = "#1a1a1a"
        self.bg_card = "#2d2d30"
        self.bg_header = "#252526"
        self.fg_text = "#d4d4d4"
        self.fg_bright = "#ffffff"
        self.accent_green = "#4ec9b0"
        self.accent_blue = "#569cd6"
        self.accent_purple = "#c586c0"
        self.accent_orange = "#ce9178"
        self.accent_red = "#f48771"
        self.accent_yellow = "#dcdcaa"
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_theme()
        
        self._setup_ui()
        self._start_update_loop()
        
    def _configure_theme(self):
        """Configure complete dark theme"""
        self.root.configure(bg=self.bg_dark)
        
        # Frame styles
        self.style.configure('TFrame', background=self.bg_dark)
        self.style.configure('Card.TFrame', background=self.bg_card)
        
        # Label styles
        self.style.configure('TLabel', background=self.bg_dark, foreground=self.fg_text)
        self.style.configure('Header.TLabel', background=self.bg_header, foreground=self.fg_bright, font=('Arial', 12, 'bold'))
        self.style.configure('Title.TLabel', foreground=self.accent_green, font=('Arial', 14, 'bold'))
        
        # Notebook styles
        self.style.configure('TNotebook', background=self.bg_dark, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=self.bg_card, foreground=self.fg_text, padding=[20, 10])
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.accent_green)],
                      foreground=[('selected', self.bg_dark)])
        
    def _setup_ui(self):
        """Setup complete interface"""
        # Top status bar
        self._create_status_bar()
        
        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create ALL tabs (12 total now!)
        self._create_overview_tab()          # Tab 1
        self._create_cognitive_tab()         # Tab 2
        self._create_emotional_tab()         # Tab 3
        self._create_autonomous_tab()        # Tab 4
        self._create_promises_tab()          # Tab 5
        self._create_vision_tab()            # Tab 6
        self._create_memory_tab()            # Tab 7
        self._create_relationship_tab()      # Tab 8 NEW!
        self._create_learning_tab()          # Tab 9 NEW!
        self._create_goals_tab()             # Tab 10 NEW!
        self._create_conversation_tab()      # Tab 11
        self._create_settings_tab()          # Tab 12
        self._create_metrics_tab()           # Tab 13
        self._create_debug_tab()             # Tab 14
        
    def _create_status_bar(self):
        """Top status bar with live metrics"""
        status_frame = tk.Frame(self.root, bg=self.accent_green, height=50)
        status_frame.pack(fill='x', side='top')
        status_frame.pack_propagate(False)
        
        # Title
        title = tk.Label(
            status_frame,
            text="[BRAIN] SEVEN AI v3.2 - DASHBOARD",
            font=('Arial', 16, 'bold'),
            bg=self.accent_green,
            fg=self.bg_dark
        )
        title.pack(side='left', padx=20)
        
        # Live metrics
        self.status_uptime = tk.Label(status_frame, text="Uptime: --", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 10))
        self.status_uptime.pack(side='right', padx=10)
        
        # LISTENING STATUS
        self.status_listening = tk.Label(
            status_frame, 
            text="[MIC] LISTENING", 
            bg=self.accent_green, 
            fg=self.bg_dark, 
            font=('Arial', 12, 'bold'))
        self.status_listening.pack(side='right', padx=10)
        
        self.status_phase5 = tk.Label(status_frame, text="Phase 5: ACTIVE", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 10, 'bold'))
        self.status_phase5.pack(side='right', padx=10)
        
        self.status_relationship = tk.Label(status_frame, text="Bond: --", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 10))
        self.status_relationship.pack(side='right', padx=10)
        
        # v3.2 status indicators
        self.status_lora = tk.Label(status_frame, text="LoRA: --", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 9))
        self.status_lora.pack(side='right', padx=5)
        
        self.status_predict = tk.Label(status_frame, text="Predict: --", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 9))
        self.status_predict.pack(side='right', padx=5)
        
        self.status_social = tk.Label(status_frame, text="Social: --", bg=self.accent_green, fg=self.bg_dark, font=('Arial', 9))
        self.status_social.pack(side='right', padx=5)
        
    def _create_overview_tab(self):
        """Complete system overview"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[STATS] Overview")
        
        # Scrollable
        canvas = tk.Canvas(frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.bg_dark)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Quick Stats Row
        stats_row = tk.Frame(scrollable, bg=self.bg_dark)
        stats_row.pack(fill='x', padx=10, pady=10)
        
        self.quick_stats = {}
        stat_items = [
            ("Total Interactions", "0", self.accent_blue),
            ("Trust Level", "0%", self.accent_green),
            ("Active Goals", "0", self.accent_purple),
            ("Learnings", "0", self.accent_orange)
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            stat_card = tk.Frame(stats_row, bg=self.bg_card, relief='raised', bd=1)
            stat_card.pack(side='left', fill='both', expand=True, padx=5)
            
            tk.Label(stat_card, text=label, bg=self.bg_card, fg=self.fg_text,
                    font=('Arial', 9)).pack(pady=(10, 0))
            
            val_label = tk.Label(stat_card, text=value, bg=self.bg_card, fg=color,
                                font=('Arial', 20, 'bold'))
            val_label.pack(pady=(0, 10))
            
            self.quick_stats[label] = val_label
        
        # Phase 5 Status
        self._create_section(scrollable, "Phase 5 Complete Sentience - All 11 Modules")
        modules_data = [
            ("[BRAIN] Cognitive Architecture", "Working memory (7 slots), attention system, inner monologue"),
            ("🪞 Self-Awareness", "Capability assessment, limitation knowledge, state monitoring"),
            ("💭 Emotional Intelligence", "34 emotions, natural blending, mood persistence"),
            ("[TARGET] Intrinsic Motivation", "Autonomous goals: learning, mastery, creativity, exploration"),
            ("🤝 Promise Tracking", "Commitment system, reliability scoring, follow-through"),
            ("[SEARCH] Theory of Mind", "User emotion understanding, intention modeling, empathy"),
            ("⚖️ Ethical Reasoning", "Values-based decisions, moral boundaries, ethical dilemmas"),
            ("🌙 Dream Processing", "Sleep cycles, memory consolidation, insight generation"),
            ("[TIP] Reflection System", "Metacognition, self-assessment, learning from experience"),
            ("💪 Homeostasis", "Energy tracking, focus management, mood regulation, self-care"),
            ("[BOT] Identity System", "SOUL.md, IDENTITY.md, USER.md personality files"),
        ]
        
        self.module_labels = {}
        for name, desc in modules_data:
            card = self._create_card(scrollable, name)
            desc_label = tk.Label(card, text=desc, bg=self.bg_card, fg=self.fg_text, 
                                 font=('Arial', 9), wraplength=600, justify='left')
            desc_label.pack(fill='x', padx=10, pady=(0, 10))
            self.module_labels[name] = desc_label
        
        # Core Systems
        self._create_section(scrollable, "Core Systems")
        core_systems = [
            ("[MIC] Voice Interaction", "Speech recognition, text-to-speech, voice modulation"),
            ("[BRAIN] Memory Systems", "Short-term, long-term, working, vector semantic memory"),
            ("🔗 Knowledge Graph", "Fact extraction, entity relationships, reasoning"),
            ("👁️ Vision System", "Webcam support, IP cameras, AI scene understanding"),
            ("[BOT] Autonomous Life", "1-minute cycles, independent goals, health monitoring"),
            ("[NOTE] Notes & Tasks", "Voice-activated notes, task management, reminders"),
            ("📔 Diary System", "Personal journaling, weekly insights, reflection"),
            ("🎨 Personality Quirks", "Consistent behaviors, preferences, unique traits"),
        ]
        
        for name, desc in core_systems:
            card = self._create_card(scrollable, name)
            tk.Label(card, text=desc, bg=self.bg_card, fg=self.fg_text, 
                    font=('Arial', 9), wraplength=600).pack(fill='x', padx=10, pady=(0, 10))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _create_cognitive_tab(self):
        """Complete cognitive state display"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[BRAIN] Cognitive")
        
        # Working Memory (7 slots)
        wm_frame = self._create_labeled_frame(frame, "Working Memory (7±2 Active Concepts)")
        wm_frame.pack(fill='x', padx=10, pady=5)
        
        self.working_memory_text = tk.Text(wm_frame, height=7, bg=self.bg_dark, fg=self.accent_blue,
                                           font=('Consolas', 10), wrap=tk.WORD, relief='flat')
        self.working_memory_text.pack(fill='x', padx=5, pady=5)
        
        # Attention System
        att_frame = self._create_labeled_frame(frame, "Current Attention Focus")
        att_frame.pack(fill='x', padx=10, pady=5)
        
        self.attention_label = tk.Label(att_frame, text="Waiting for interaction...",
                                       bg=self.bg_card, fg=self.accent_green, font=('Arial', 11),
                                       wraplength=1200, justify='left')
        self.attention_label.pack(fill='x', padx=10, pady=10)
        
        # Inner Monologue (Seven's thoughts)
        im_frame = self._create_labeled_frame(frame, "Inner Monologue - Seven's Actual Thoughts")
        im_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.inner_monologue_text = scrolledtext.ScrolledText(
            im_frame, bg=self.bg_dark, fg=self.accent_purple, font=('Consolas', 10), wrap=tk.WORD)
        self.inner_monologue_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Cognitive Metrics
        metrics_frame = self._create_labeled_frame(frame, "Cognitive Metrics")
        metrics_frame.pack(fill='x', padx=10, pady=5)
        
        metrics_grid = tk.Frame(metrics_frame, bg=self.bg_card)
        metrics_grid.pack(fill='x', padx=5, pady=5)
        
        self.cog_load_label = tk.Label(metrics_grid, text="Cognitive Load: --", bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.cog_load_label.grid(row=0, column=0, padx=20, pady=5, sticky='w')
        
        self.attention_span_label = tk.Label(metrics_grid, text="Attention Span: --", bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.attention_span_label.grid(row=0, column=1, padx=20, pady=5, sticky='w')
        
        self.thinking_depth_label = tk.Label(metrics_grid, text="Thinking Depth: --", bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.thinking_depth_label.grid(row=0, column=2, padx=20, pady=5, sticky='w')
        
    def _create_emotional_tab(self):
        """Complete emotional state - all 34 emotions"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💭 Emotions")
        
        # Current Emotional Blend
        current_frame = self._create_labeled_frame(frame, "Current Emotional State")
        current_frame.pack(fill='x', padx=10, pady=5)
        
        self.current_emotion_label = tk.Label(
            current_frame, text="Contentment (0.7) + Curiosity (0.5)",
            bg=self.bg_card, fg=self.accent_orange, font=('Arial', 16, 'bold'))
        self.current_emotion_label.pack(pady=15)
        
        # Emotion intensity bars
        bars_frame = tk.Frame(current_frame, bg=self.bg_card)
        bars_frame.pack(fill='x', padx=20, pady=10)
        
        self.emotion_bars = {}
        for i, emotion_name in enumerate(['Primary', 'Secondary 1', 'Secondary 2']):
            tk.Label(bars_frame, text=f"{emotion_name}:", bg=self.bg_card, fg=self.fg_text,
                    font=('Arial', 9)).grid(row=i, column=0, sticky='w', pady=3)
            
            canvas = tk.Canvas(bars_frame, height=20, bg=self.bg_dark, highlightthickness=0)
            canvas.grid(row=i, column=1, sticky='ew', padx=10, pady=3)
            bars_frame.columnconfigure(1, weight=1)
            
            self.emotion_bars[emotion_name] = canvas
        
        # Emotional Insights NEW!
        insights_frame = self._create_labeled_frame(frame, "Emotional Insights")
        insights_frame.pack(fill='x', padx=10, pady=5)
        
        insights_grid = tk.Frame(insights_frame, bg=self.bg_card)
        insights_grid.pack(fill='x', padx=10, pady=10)
        
        self.most_common_emotion_label = tk.Label(insights_grid, text="Most Common: --",
                                                  bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.most_common_emotion_label.grid(row=0, column=0, padx=20, sticky='w')
        
        self.emotional_volatility_label = tk.Label(insights_grid, text="Volatility: --",
                                                   bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.emotional_volatility_label.grid(row=0, column=1, padx=20, sticky='w')
        
        self.unique_emotions_label = tk.Label(insights_grid, text="Unique Emotions: --",
                                             bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.unique_emotions_label.grid(row=0, column=2, padx=20, sticky='w')
        
        # All 34 Emotions List
        all_emotions_frame = self._create_labeled_frame(frame, "All 34 Supported Emotions")
        all_emotions_frame.pack(fill='x', padx=10, pady=5)
        
        emotions_text = tk.Text(all_emotions_frame, height=6, bg=self.bg_dark, fg=self.fg_text,
                               font=('Arial', 9), wrap=tk.WORD, relief='flat')
        emotions_text.pack(fill='x', padx=5, pady=5)
        
        all_emotions = [
            "joy", "contentment", "excitement", "pride", "love", "gratitude",
            "curiosity", "interest", "amusement", "serenity",
            "sadness", "grief", "disappointment", "loneliness",
            "anger", "frustration", "annoyance", "irritation",
            "fear", "anxiety", "nervousness", "worry",
            "surprise", "confusion", "embarrassment",
            "disgust", "contempt",
            "guilt", "shame", "regret",
            "hope", "anticipation", "relief", "tenderness"
        ]
        emotions_text.insert('1.0', ', '.join(all_emotions))
        emotions_text.config(state='disabled')
        
        # Emotional History
        history_frame = self._create_labeled_frame(frame, "Emotional History (Last 20)")
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.emotion_history_text = scrolledtext.ScrolledText(
            history_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 9))
        self.emotion_history_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_autonomous_tab(self):
        """Complete autonomous life display"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[BOT] Autonomous")
        
        # Current Goal
        goal_frame = self._create_labeled_frame(frame, "Current Autonomous Goal")
        goal_frame.pack(fill='x', padx=10, pady=5)
        
        self.current_goal_label = tk.Label(
            goal_frame, text="[TARGET] No active goal - waiting for inspiration",
            bg=self.bg_card, fg=self.accent_green, font=('Arial', 12, 'bold'),
            wraplength=1200)
        self.current_goal_label.pack(pady=15, padx=10)
        
        # Goal Progress
        progress_frame = tk.Frame(goal_frame, bg=self.bg_card)
        progress_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        tk.Label(progress_frame, text="Progress:", bg=self.bg_card, fg=self.fg_text,
                font=('Arial', 9)).pack(side='left')
        
        self.goal_progress_canvas = tk.Canvas(progress_frame, height=15, bg=self.bg_dark,
                                              highlightthickness=0)
        self.goal_progress_canvas.pack(side='left', fill='x', expand=True, padx=10)
        
        self.goal_progress_label = tk.Label(progress_frame, text="0%", bg=self.bg_card,
                                           fg=self.fg_text, font=('Arial', 9))
        self.goal_progress_label.pack(side='left')
        
        # Homeostasis (Health Metrics)
        health_frame = self._create_labeled_frame(frame, "Homeostasis - Health & Well-being")
        health_frame.pack(fill='x', padx=10, pady=5)
        
        # Health bars
        health_bars = tk.Frame(health_frame, bg=self.bg_card)
        health_bars.pack(fill='x', padx=10, pady=10)
        
        self.health_bars = {}
        for i, (metric, color) in enumerate([('Energy', self.accent_green), 
                                             ('Focus', self.accent_blue),
                                             ('Mood', self.accent_purple)]):
            tk.Label(health_bars, text=f"{metric}:", bg=self.bg_card, fg=self.fg_text,
                    font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            
            canvas = tk.Canvas(health_bars, height=25, bg=self.bg_dark, highlightthickness=0)
            canvas.grid(row=i, column=1, sticky='ew', padx=10, pady=5)
            health_bars.columnconfigure(1, weight=1)
            
            label = tk.Label(health_bars, text="--", bg=self.bg_card, fg=color,
                           font=('Arial', 10, 'bold'), width=8)
            label.grid(row=i, column=2, pady=5)
            
            self.health_bars[metric] = {'canvas': canvas, 'label': label, 'color': color}
        
        # Cycle Information
        cycle_frame = self._create_labeled_frame(frame, "Autonomous Life Cycle (1-minute intervals)")
        cycle_frame.pack(fill='x', padx=10, pady=5)
        
        cycle_info = tk.Frame(cycle_frame, bg=self.bg_card)
        cycle_info.pack(fill='x', padx=10, pady=10)
        
        self.cycle_count_label = tk.Label(cycle_info, text="Cycles: 0", bg=self.bg_card,
                                          fg=self.fg_text, font=('Arial', 10))
        self.cycle_count_label.grid(row=0, column=0, padx=15)
        
        self.last_cycle_label = tk.Label(cycle_info, text="Last: Never", bg=self.bg_card,
                                         fg=self.fg_text, font=('Arial', 10))
        self.last_cycle_label.grid(row=0, column=1, padx=15)
        
        self.next_cycle_label = tk.Label(cycle_info, text="Next: --", bg=self.bg_card,
                                         fg=self.fg_text, font=('Arial', 10))
        self.next_cycle_label.grid(row=0, column=2, padx=15)
        
        # Activity Log
        log_frame = self._create_labeled_frame(frame, "Autonomous Activity Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.activity_log_text = scrolledtext.ScrolledText(
            log_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 9))
        self.activity_log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_promises_tab(self):
        """Complete promise tracking system"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🤝 Promises")
        
        # Trust Score
        trust_frame = self._create_labeled_frame(frame, "Trust & Reliability Score")
        trust_frame.pack(fill='x', padx=10, pady=5)
        
        self.trust_score_label = tk.Label(
            trust_frame, text="Trust Score: --/100",
            bg=self.bg_card, fg=self.accent_green, font=('Arial', 18, 'bold'))
        self.trust_score_label.pack(pady=15)
        
        # Statistics
        stats_grid = tk.Frame(trust_frame, bg=self.bg_card)
        stats_grid.pack(fill='x', padx=20, pady=(0, 15))
        
        self.kept_label = tk.Label(stats_grid, text="[OK] Kept: 0", bg=self.bg_card,
                                   fg=self.accent_green, font=('Arial', 12))
        self.kept_label.grid(row=0, column=0, padx=30)
        
        self.broken_label = tk.Label(stats_grid, text="[ERROR] Broken: 0", bg=self.bg_card,
                                     fg=self.accent_red, font=('Arial', 12))
        self.broken_label.grid(row=0, column=1, padx=30)
        
        self.pending_count_label = tk.Label(stats_grid, text="[PENDING] Pending: 0", bg=self.bg_card,
                                           fg=self.accent_blue, font=('Arial', 12))
        self.pending_count_label.grid(row=0, column=2, padx=30)
        
        # Pending Promises
        pending_frame = self._create_labeled_frame(frame, "Pending Promises")
        pending_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.promises_text = scrolledtext.ScrolledText(
            pending_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 10))
        self.promises_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Promise History
        history_frame = self._create_labeled_frame(frame, "Recent Promise History")
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.promise_history_text = scrolledtext.ScrolledText(
            history_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 9))
        self.promise_history_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_vision_tab(self):
        """Complete vision system display"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="👁️ Vision")
        
        # Status
        status_frame = self._create_labeled_frame(frame, "Vision System Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        status_grid = tk.Frame(status_frame, bg=self.bg_card)
        status_grid.pack(fill='x', padx=10, pady=10)
        
        self.vision_status_label = tk.Label(status_grid, text="[CAMERA] Status: Checking...",
                                           bg=self.bg_card, fg=self.accent_orange, font=('Arial', 11))
        self.vision_status_label.grid(row=0, column=0, sticky='w', padx=10)
        
        self.camera_count_label = tk.Label(status_grid, text="Cameras: 0",
                                          bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.camera_count_label.grid(row=0, column=1, padx=30)
        
        self.last_analysis_label = tk.Label(status_grid, text="Last Analysis: Never",
                                           bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.last_analysis_label.grid(row=0, column=2, padx=30)
        
        # Active Cameras
        cameras_frame = self._create_labeled_frame(frame, "Active Cameras")
        cameras_frame.pack(fill='x', padx=10, pady=5)
        
        self.cameras_text = tk.Text(cameras_frame, height=4, bg=self.bg_dark, fg=self.fg_text,
                                    font=('Consolas', 9), wrap=tk.WORD)
        self.cameras_text.pack(fill='x', padx=5, pady=5)
        
        # Last Scene
        scene_frame = self._create_labeled_frame(frame, "Last Captured Scene Description")
        scene_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.scene_text = scrolledtext.ScrolledText(
            scene_frame, bg=self.bg_dark, fg=self.accent_blue, font=('Consolas', 10))
        self.scene_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.scene_text.insert('1.0', "No scenes captured yet.\n\nVision will update when:\n- OpenCV is installed (pip install opencv-python)\n- Vision is enabled in config\n- Cameras are detected")
        
    def _create_memory_tab(self):
        """Complete memory systems display"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[BRAIN] Memory")
        
        # Memory Statistics
        stats_frame = self._create_labeled_frame(frame, "Memory System Statistics")
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        stats_grid = tk.Frame(stats_frame, bg=self.bg_card)
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        self.short_mem_label = tk.Label(stats_grid, text="Short-term: --", bg=self.bg_card,
                                        fg=self.accent_green, font=('Arial', 11, 'bold'))
        self.short_mem_label.grid(row=0, column=0, padx=20, pady=5)
        
        self.long_mem_label = tk.Label(stats_grid, text="Long-term: --", bg=self.bg_card,
                                       fg=self.accent_blue, font=('Arial', 11, 'bold'))
        self.long_mem_label.grid(row=0, column=1, padx=20, pady=5)
        
        self.vector_mem_label = tk.Label(stats_grid, text="Vector: --", bg=self.bg_card,
                                         fg=self.accent_purple, font=('Arial', 11, 'bold'))
        self.vector_mem_label.grid(row=0, column=2, padx=20, pady=5)
        
        self.facts_label = tk.Label(stats_grid, text="Facts: --", bg=self.bg_card,
                                    fg=self.accent_orange, font=('Arial', 11, 'bold'))
        self.facts_label.grid(row=0, column=3, padx=20, pady=5)
        
        # Memory Distribution
        dist_frame = self._create_labeled_frame(frame, "Memory Distribution")
        dist_frame.pack(fill='x', padx=10, pady=5)
        
        self.memory_dist_canvas = tk.Canvas(dist_frame, height=100, bg=self.bg_card,
                                            highlightthickness=0)
        self.memory_dist_canvas.pack(fill='x', padx=10, pady=10)
        
        # Recent Memories
        recent_frame = self._create_labeled_frame(frame, "Recent Memories (Last 15)")
        recent_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.memory_text = scrolledtext.ScrolledText(
            recent_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 9))
        self.memory_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Knowledge Graph
        kg_frame = self._create_labeled_frame(frame, "Knowledge Graph - Recent Facts")
        kg_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.knowledge_text = scrolledtext.ScrolledText(
            kg_frame, bg=self.bg_dark, fg=self.accent_blue, font=('Consolas', 9))
        self.knowledge_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_relationship_tab(self):
        """NEW! Relationship tracker tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💕 Relationship")
        
        # Relationship Score
        score_frame = self._create_labeled_frame(frame, "Relationship Quality")
        score_frame.pack(fill='x', padx=10, pady=5)
        
        # Main scores
        scores_grid = tk.Frame(score_frame, bg=self.bg_card)
        scores_grid.pack(fill='x', padx=10, pady=15)
        
        self.trust_relationship_label = tk.Label(scores_grid, text="Trust: --",
                                                bg=self.bg_card, fg=self.accent_green,
                                                font=('Arial', 14, 'bold'))
        self.trust_relationship_label.grid(row=0, column=0, padx=30)
        
        self.rapport_label = tk.Label(scores_grid, text="Rapport: --",
                                      bg=self.bg_card, fg=self.accent_blue,
                                      font=('Arial', 14, 'bold'))
        self.rapport_label.grid(row=0, column=1, padx=30)
        
        self.understanding_label = tk.Label(scores_grid, text="Understanding: --",
                                           bg=self.bg_card, fg=self.accent_purple,
                                           font=('Arial', 14, 'bold'))
        self.understanding_label.grid(row=0, column=2, padx=30)
        
        # Journey Stats
        journey_frame = self._create_labeled_frame(frame, "Our Journey Together")
        journey_frame.pack(fill='x', padx=10, pady=5)
        
        journey_grid = tk.Frame(journey_frame, bg=self.bg_card)
        journey_grid.pack(fill='x', padx=10, pady=10)
        
        self.days_together_label = tk.Label(journey_grid, text="Days Together: --",
                                           bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.days_together_label.grid(row=0, column=0, padx=20, sticky='w')
        
        self.total_interactions_label = tk.Label(journey_grid, text="Total Interactions: --",
                                                bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.total_interactions_label.grid(row=0, column=1, padx=20, sticky='w')
        
        self.positive_ratio_label = tk.Label(journey_grid, text="Positive Ratio: --",
                                            bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.positive_ratio_label.grid(row=0, column=2, padx=20, sticky='w')
        
        # Milestones
        milestones_frame = self._create_labeled_frame(frame, "Relationship Milestones")
        milestones_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.milestones_text = scrolledtext.ScrolledText(
            milestones_frame, bg=self.bg_dark, fg=self.accent_yellow, font=('Consolas', 10))
        self.milestones_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_learning_tab(self):
        """NEW! Learning tracker tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎓 Learning")
        
        # Learning Summary
        summary_frame = self._create_labeled_frame(frame, "Learning Summary")
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        summary_grid = tk.Frame(summary_frame, bg=self.bg_card)
        summary_grid.pack(fill='x', padx=10, pady=10)
        
        self.total_learnings_label = tk.Label(summary_grid, text="Total Learnings: 0",
                                             bg=self.bg_card, fg=self.accent_green,
                                             font=('Arial', 12, 'bold'))
        self.total_learnings_label.pack(pady=10)
        
        # Learning Categories
        categories_frame = self._create_labeled_frame(frame, "Learning by Category")
        categories_frame.pack(fill='x', padx=10, pady=5)
        
        self.learning_categories_text = tk.Text(categories_frame, height=6,
                                               bg=self.bg_dark, fg=self.fg_text,
                                               font=('Consolas', 9))
        self.learning_categories_text.pack(fill='x', padx=5, pady=5)
        
        # Recent Learnings
        recent_learnings_frame = self._create_labeled_frame(frame, "Recent Learnings")
        recent_learnings_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.learnings_text = scrolledtext.ScrolledText(
            recent_learnings_frame, bg=self.bg_dark, fg=self.accent_blue,
            font=('Consolas', 10))
        self.learnings_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_goals_tab(self):
        """NEW! Goals tracker tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[TARGET] Goals")
        
        # Active Goals Count
        count_frame = self._create_labeled_frame(frame, "Goals Overview")
        count_frame.pack(fill='x', padx=10, pady=5)
        
        count_grid = tk.Frame(count_frame, bg=self.bg_card)
        count_grid.pack(fill='x', padx=10, pady=10)
        
        self.active_goals_label = tk.Label(count_grid, text="Active Goals: 0",
                                          bg=self.bg_card, fg=self.accent_green,
                                          font=('Arial', 14, 'bold'))
        self.active_goals_label.pack(pady=10)
        
        # Goal Categories
        categories_frame = self._create_labeled_frame(frame, "Goals by Category")
        categories_frame.pack(fill='x', padx=10, pady=5)
        
        cat_grid = tk.Frame(categories_frame, bg=self.bg_card)
        cat_grid.pack(fill='x', padx=10, pady=10)
        
        self.learning_goals_label = tk.Label(cat_grid, text="📚 Learning: 0",
                                            bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.learning_goals_label.grid(row=0, column=0, padx=20)
        
        self.mastery_goals_label = tk.Label(cat_grid, text="🏆 Mastery: 0",
                                           bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.mastery_goals_label.grid(row=0, column=1, padx=20)
        
        self.creativity_goals_label = tk.Label(cat_grid, text="🎨 Creativity: 0",
                                              bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.creativity_goals_label.grid(row=0, column=2, padx=20)
        
        self.exploration_goals_label = tk.Label(cat_grid, text="🗺️ Exploration: 0",
                                               bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.exploration_goals_label.grid(row=0, column=3, padx=20)
        
        # Active Goals List
        active_frame = self._create_labeled_frame(frame, "Active Goals")
        active_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.goals_text = scrolledtext.ScrolledText(
            active_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 10))
        self.goals_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Completed Goals
        completed_frame = self._create_labeled_frame(frame, "Recently Completed Goals")
        completed_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.completed_goals_text = scrolledtext.ScrolledText(
            completed_frame, bg=self.bg_dark, fg=self.accent_green, font=('Consolas', 9))
        self.completed_goals_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_conversation_tab(self):
        """Complete conversation monitor"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[CHAT] Conversation")
        
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(
            frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 10), wrap=tk.WORD)
        self.conversation_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tags for different speakers
        self.conversation_text.tag_config('user', foreground=self.accent_blue,
                                         font=('Consolas', 10, 'bold'))
        self.conversation_text.tag_config('bot', foreground=self.accent_green,
                                         font=('Consolas', 10, 'bold'))
        self.conversation_text.tag_config('system', foreground=self.accent_orange,
                                         font=('Consolas', 9, 'italic'))
        self.conversation_text.tag_config('emotion', foreground=self.accent_purple,
                                         font=('Consolas', 9))
        
    def _create_settings_tab(self):
        """COMPLETE settings display - EVERYTHING"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[GEAR] Settings")
        
        # Scrollable
        canvas = tk.Canvas(frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.bg_dark)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Phase 5 Configuration
        self._create_section(scrollable, "Phase 5 Complete Sentience Configuration")
        p5_card = self._create_card(scrollable, "Phase 5 Modules Status")
        self.phase5_status_text = tk.Text(p5_card, height=14, bg=self.bg_dark, fg=self.fg_text,
                                         font=('Consolas', 9), wrap=tk.WORD)
        self.phase5_status_text.pack(fill='x', padx=10, pady=10)
        
        # Core Features
        self._create_section(scrollable, "Core Features Configuration")
        core_card = self._create_card(scrollable, "Voice, Memory, & Core Systems")
        self.core_config_text = tk.Text(core_card, height=10, bg=self.bg_dark, fg=self.fg_text,
                                       font=('Consolas', 9), wrap=tk.WORD)
        self.core_config_text.pack(fill='x', padx=10, pady=10)
        
        # Advanced Features
        self._create_section(scrollable, "Advanced Features")
        adv_card = self._create_card(scrollable, "Whisper, VAD, Streaming, etc.")
        self.advanced_config_text = tk.Text(adv_card, height=8, bg=self.bg_dark, fg=self.fg_text,
                                           font=('Consolas', 9), wrap=tk.WORD)
        self.advanced_config_text.pack(fill='x', padx=10, pady=10)
        
        # Vision Configuration
        self._create_section(scrollable, "Vision System Configuration")
        vision_card = self._create_card(scrollable, "Cameras & Visual Processing")
        self.vision_config_text = tk.Text(vision_card, height=8, bg=self.bg_dark, fg=self.fg_text,
                                         font=('Consolas', 9), wrap=tk.WORD)
        self.vision_config_text.pack(fill='x', padx=10, pady=10)
        
        # System Information
        self._create_section(scrollable, "System Information")
        sys_card = self._create_card(scrollable, "Environment & Paths")
        self.system_info_text = tk.Text(sys_card, height=10, bg=self.bg_dark, fg=self.fg_text,
                                       font=('Consolas', 9), wrap=tk.WORD)
        self.system_info_text.pack(fill='x', padx=10, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _create_metrics_tab(self):
        """Performance metrics & analytics"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📈 Metrics")
        
        # Response Times
        response_frame = self._create_labeled_frame(frame, "Response Time Analytics")
        response_frame.pack(fill='x', padx=10, pady=5)
        
        times_grid = tk.Frame(response_frame, bg=self.bg_card)
        times_grid.pack(fill='x', padx=10, pady=10)
        
        self.avg_response_label = tk.Label(times_grid, text="Avg Response: -- ms",
                                          bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.avg_response_label.grid(row=0, column=0, padx=20)
        
        self.last_response_label = tk.Label(times_grid, text="Last Response: -- ms",
                                           bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.last_response_label.grid(row=0, column=1, padx=20)
        
        self.fastest_label = tk.Label(times_grid, text="Fastest: -- ms",
                                      bg=self.bg_card, fg=self.accent_green, font=('Arial', 10))
        self.fastest_label.grid(row=0, column=2, padx=20)
        
        # Usage Statistics
        usage_frame = self._create_labeled_frame(frame, "Usage Statistics")
        usage_frame.pack(fill='x', padx=10, pady=5)
        
        usage_grid = tk.Frame(usage_frame, bg=self.bg_card)
        usage_grid.pack(fill='x', padx=10, pady=10)
        
        self.total_messages_label = tk.Label(usage_grid, text="Total Messages: 0",
                                            bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.total_messages_label.grid(row=0, column=0, padx=20)
        
        self.session_messages_label = tk.Label(usage_grid, text="This Session: 0",
                                              bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.session_messages_label.grid(row=0, column=1, padx=20)
        
        self.commands_executed_label = tk.Label(usage_grid, text="Commands: 0",
                                               bg=self.bg_card, fg=self.fg_text, font=('Arial', 10))
        self.commands_executed_label.grid(row=0, column=2, padx=20)
        
        # Resource Usage
        resource_frame = self._create_labeled_frame(frame, "Resource Usage")
        resource_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.resource_text = scrolledtext.ScrolledText(
            resource_frame, bg=self.bg_dark, fg=self.fg_text, font=('Consolas', 9))
        self.resource_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_debug_tab(self):
        """Debug information & logs"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="[CONFIG] Debug")
        
        # Controls
        controls = tk.Frame(frame, bg=self.bg_dark)
        controls.pack(fill='x', padx=10, pady=5)
        
        tk.Button(controls, text="Clear Logs", command=self._clear_debug,
                 bg=self.accent_red, fg=self.bg_dark, font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side='left', padx=5)
        
        tk.Button(controls, text="Refresh", command=self._refresh_debug,
                 bg=self.accent_blue, fg=self.bg_dark, font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side='left', padx=5)
        
        # Debug log
        log_frame = self._create_labeled_frame(frame, "System Debug Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.debug_text = scrolledtext.ScrolledText(
            log_frame, bg='#000000', fg='#00ff00', font=('Consolas', 9))
        self.debug_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _create_section(self, parent, title):
        """Create section header"""
        label = tk.Label(parent, text=title, bg=self.bg_dark, fg=self.accent_green,
                        font=('Arial', 12, 'bold'))
        label.pack(fill='x', padx=10, pady=(15, 5))
        
    def _create_card(self, parent, title):
        """Create a card container"""
        card = tk.Frame(parent, bg=self.bg_card, relief='raised', bd=1)
        card.pack(fill='x', padx=20, pady=5)
        
        title_label = tk.Label(card, text=title, bg=self.bg_card, fg=self.fg_bright,
                              font=('Arial', 11, 'bold'), anchor='w')
        title_label.pack(fill='x', padx=10, pady=(10, 5))
        
        return card
        
    def _create_labeled_frame(self, parent, title):
        """Create a labeled frame"""
        frame = tk.LabelFrame(parent, text=title, bg=self.bg_card, fg=self.accent_green,
                             font=('Arial', 10, 'bold'), labelanchor='n')
        return frame
        
    def _start_update_loop(self):
        """Start UI update loops"""
        self._update_from_queue()
        self._update_from_bot()
        
    def _update_from_queue(self):
        """Process messages from queue"""
        try:
            while not self.message_queue.empty():
                update = self.message_queue.get_nowait()
                self._apply_update(update)
        except queue.Empty:
            pass
        
        self.root.after(self.update_interval, self._update_from_queue)
        
    def _update_from_bot(self):
        """Pull ALL data from bot"""
        if self.bot:
            try:
                self._update_status_bar()
                self._update_quick_stats()
                self._update_phase5_data()
                self._update_memory_data()
                self._update_vision_data()
                self._update_settings_data()
                self._update_autonomous_data()
                self._update_metrics_data()
                self._update_enhancement_data()  # NEW!
            except Exception as e:
                self._log_debug(f"Update error: {e}")
        
        self.root.after(1000, self._update_from_bot)  # Every second
        
    def _update_status_bar(self):
        """Update top status bar"""
        try:
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.now() - self.bot.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                self.status_uptime.config(text=f"Uptime: {hours}h {minutes}m")
                
            if hasattr(self.bot, 'relationship_tracker') and self.bot.relationship_tracker:
                summary = self.bot.relationship_tracker.get_relationship_summary()
                self.status_relationship.config(text=f"Bond: {int(summary['rapport'])}%")
            
            # Update listening status
            if hasattr(self.bot, 'running') and self.bot.running:
                if hasattr(self.bot, 'sleeping') and self.bot.sleeping:
                    self.status_listening.config(text="[SLEEP] SLEEPING", fg="#FFD700")
                elif hasattr(self.bot, '_is_processing') and getattr(self.bot, '_is_processing', False):
                    self.status_listening.config(text="💭 THINKING", fg="#87CEEB")
                else:
                    # Bot is running and not sleeping = listening!
                    self.status_listening.config(text="[MIC] LISTENING", fg=self.bg_dark)
            else:
                self.status_listening.config(text="⏸️ IDLE", fg="#FFA500")
            
            # v3.2 indicators
            if hasattr(self.bot, 'lora_trainer') and self.bot.lora_trainer:
                t = self.bot.lora_trainer
                method = 'LoRA' if t.lora_available else 'PR'
                self.status_lora.config(text=f"LoRA: {method} ({t.total_examples_collected}ex)")
            
            if hasattr(self.bot, 'user_predictor') and self.bot.user_predictor:
                p = self.bot.user_predictor
                mood = p.predictions.get('mood_trend', '?')
                self.status_predict.config(text=f"Mood: {mood}")
            
            if hasattr(self.bot, 'social_sim') and self.bot.social_sim:
                s = self.bot.social_sim
                self.status_social.config(text=f"Social: {s.total_debates}d")
        except:
            pass
            
    def _update_quick_stats(self):
        """Update quick stats row"""
        try:
            if getattr(self.bot, 'relationship_tracker', None):
                summary = self.bot.relationship_tracker.get_relationship_summary()
                self.quick_stats['Total Interactions'].config(text=str(summary['total_interactions']))
                self.quick_stats['Trust Level'].config(text=f"{int(summary['trust_score'])}%")
                
            if getattr(self.bot, 'goal_manager', None):
                active = self.bot.goal_manager.get_active_goals()
                self.quick_stats['Active Goals'].config(text=str(len(active)))
                
            if getattr(self.bot, 'learning_tracker', None):
                learnings = self.bot.learning_tracker.get_recent_learnings(limit=1000)
                self.quick_stats['Learnings'].config(text=str(len(learnings)))
        except:
            pass
            
    def _update_phase5_data(self):
        """Update Phase 5 displays with robust error handling"""
        if not self.bot or not hasattr(self.bot, 'phase5'):
            return
            
        try:
            p5 = self.bot.phase5
            
            # Check if Phase 5 is initialized
            if not p5:
                return
            
            # Get current state safely
            try:
                state = p5.get_current_state()
            except Exception:
                return  # Silently fail - state unavailable
            
            # Working memory - with individual error handling
            try:
                if 'working_memory' in state and state['working_memory']:
                    self.working_memory_text.delete('1.0', 'end')
                    for i, concept in enumerate(state['working_memory'][:7], 1):
                        self.working_memory_text.insert('end', f"{i}. {concept}\n")
            except Exception as e:
                pass  # Silently fail for UI updates
            
            # Attention - with fallback to cognition attribute
            try:
                if 'attention_focus' in state:
                    self.attention_label.config(text=state['attention_focus'])
                elif hasattr(p5, 'cognition') and p5.cognition:
                    # Try different possible attribute names
                    if hasattr(p5.cognition, 'working_memory') and p5.cognition.working_memory:
                        wm = p5.cognition.working_memory
                        # Try multiple possible attribute names
                        focus_text = None
                        if hasattr(wm, 'current_focus'):
                            focus_text = wm.current_focus
                        elif hasattr(wm, 'focus'):
                            focus_text = wm.focus
                        elif hasattr(wm, 'attention_focus'):
                            focus_text = wm.attention_focus
                        
                        if focus_text:
                            self.attention_label.config(text=focus_text)
            except Exception:
                pass  # Silently fail - no debug logging
            
            # Emotions - with attribute checks
            try:
                if 'seven_emotion' in state and state['seven_emotion']:
                    emotion = state['seven_emotion']
                    if hasattr(emotion, 'emotion') and hasattr(emotion, 'intensity'):
                        text = f"{emotion.emotion.value.title()} ({emotion.intensity:.2f})"
                        if hasattr(emotion, 'secondary_emotions') and emotion.secondary_emotions:
                            for e, i in list(emotion.secondary_emotions.items())[:2]:
                                text += f" + {e.value.title()} ({i:.2f})"
                        self.current_emotion_label.config(text=text)
                        
                        # Update emotion bars
                        self._update_emotion_bars(emotion)
            except Exception as e:
                pass  # Silently fail for UI updates
            
            # Autonomous goal - with safe attribute access
            try:
                if hasattr(p5, 'motivation') and p5.motivation:
                    if hasattr(p5.motivation, 'current_goal') and p5.motivation.current_goal:
                        goal = p5.motivation.current_goal
                        desc = goal.get('description', 'Unknown goal') if isinstance(goal, dict) else str(goal)
                        priority = goal.get('priority', 0) if isinstance(goal, dict) else 0
                        self.current_goal_label.config(text=f"[TARGET] {desc} (Priority: {priority})")
                        
                        progress = goal.get('progress', 0) if isinstance(goal, dict) else 0
                        self.goal_progress_label.config(text=f"{int(progress*100)}%")
                        self._draw_progress_bar(self.goal_progress_canvas, progress)
            except Exception as e:
                pass  # Silently fail for UI updates
            
            # Homeostasis - with safe attribute access
            try:
                if hasattr(p5, 'homeostasis') and p5.homeostasis:
                    h = p5.homeostasis
                    if hasattr(h, 'energy'):
                        self._update_health_bar('Energy', h.energy / 100)
                    if hasattr(h, 'focus'):
                        self._update_health_bar('Focus', h.focus / 100)
                    
                    # Mood with safe access
                    mood_val = 0.5  # Default
                    if hasattr(h, 'mood_score'):
                        mood_val = (h.mood_score + 1) / 2  # Normalize -1 to 1 -> 0 to 1
                    self._update_health_bar('Mood', mood_val)
            except Exception as e:
                pass  # Silently fail for UI updates
            
            # Promises - with safe attribute access
            try:
                if hasattr(p5, 'promises') and p5.promises:
                    ps = p5.promises
                    if hasattr(ps, 'trust_score'):
                        self.trust_score_label.config(text=f"Trust Score: {ps.trust_score}/100")
                    if hasattr(ps, 'promises_kept'):
                        self.kept_label.config(text=f"[OK] Kept: {ps.promises_kept}")
                    if hasattr(ps, 'promises_broken'):
                        self.broken_label.config(text=f"[ERROR] Broken: {ps.promises_broken}")
                    
                    if hasattr(ps, 'get_pending_promises'):
                        pending = ps.get_pending_promises()
                        self.pending_count_label.config(text=f"[PENDING] Pending: {len(pending)}")
                        
                        self.promises_text.delete('1.0', 'end')
                        for p in pending[:10]:
                            if hasattr(p, 'priority') and hasattr(p, 'content'):
                                self.promises_text.insert('end',
                                    f"[Priority {p.priority}] {p.content}\n")
                                if hasattr(p, 'due_by') and p.due_by:
                                    self.promises_text.insert('end',
                                        f"  Due: {p.due_by.strftime('%Y-%m-%d %H:%M')}\n")
                                self.promises_text.insert('end', "\n")
            except Exception as e:
                pass  # Silently fail for UI updates
                    
        except Exception as e:
            # Only log major errors, not individual UI update failures
            import traceback
            if "has no attribute" in str(e):
                self._log_debug(f"Phase 5 attribute error: {e}")
            else:
                self._log_debug(f"Phase 5 update error: {e}\n{traceback.format_exc()}")
            
    def _update_memory_data(self):
        """Update memory displays"""
        if not self.bot or not hasattr(self.bot, 'memory'):
            return
            
        try:
            mem = self.bot.memory
            
            # Counts
            short = mem.get_recent_conversations(limit=20)
            long_count = len(mem.get_persistent_memory())
            
            self.short_mem_label.config(text=f"Short-term: {len(short)}")
            self.long_mem_label.config(text=f"Long-term: {long_count}")
            
            # Vector memory
            if hasattr(self.bot, 'vector_memory') and self.bot.vector_memory:
                try:
                    vec_count = self.bot.vector_memory.get_memory_count()
                    self.vector_mem_label.config(text=f"Vector: {vec_count}")
                except:
                    pass
            
            # Knowledge graph
            if hasattr(self.bot, 'knowledge_graph') and self.bot.knowledge_graph:
                try:
                    facts = self.bot.knowledge_graph.get_all_facts()
                    self.facts_label.config(text=f"Facts: {len(facts)}")
                    
                    # Show recent facts
                    self.knowledge_text.delete('1.0', 'end')
                    for fact in facts[-10:]:
                        self.knowledge_text.insert('end',
                            f"{fact.get('subject', '?')} -> {fact.get('predicate', '?')} -> {fact.get('object', '?')}\n")
                except:
                    pass
            
            # Recent memories
            self.memory_text.delete('1.0', 'end')
            for memory in short[-15:]:
                timestamp = memory.get('timestamp', 'unknown')
                content = memory.get('content', '')[:100]
                self.memory_text.insert('end', f"[{timestamp}] {content}\n\n")
                
        except Exception as e:
            self._log_debug(f"Memory update error: {e}")
            
    def _update_vision_data(self):
        """Update vision displays"""
        try:
            if hasattr(self.bot, 'vision') and self.bot.vision:
                self.vision_status_label.config(
                    text="[CAMERA] Status: ENABLED",
                    fg=self.accent_green)
                
                if hasattr(self.bot.vision, 'cameras'):
                    self.camera_count_label.config(
                        text=f"Cameras: {len(self.bot.vision.cameras)}")
            else:
                self.vision_status_label.config(
                    text="[CAMERA] Status: DISABLED (Install OpenCV)",
                    fg=self.accent_orange)
                self.camera_count_label.config(text="Cameras: 0")
        except Exception as e:
            self._log_debug(f"Vision update error: {e}")
            
    def _update_settings_data(self):
        """Update ALL settings displays"""
        try:
            # Phase 5 settings
            p5_text = ""
            p5_text += f"ENABLE_PHASE5 = {config.ENABLE_PHASE5}\n"
            p5_text += f"ENABLE_COGNITIVE_ARCHITECTURE = {config.ENABLE_COGNITIVE_ARCHITECTURE}\n"
            p5_text += f"ENABLE_SELF_MODEL_ENHANCED = {config.ENABLE_SELF_MODEL_ENHANCED}\n"
            p5_text += f"ENABLE_INTRINSIC_MOTIVATION = {config.ENABLE_INTRINSIC_MOTIVATION}\n"
            p5_text += f"ENABLE_REFLECTION_SYSTEM = {config.ENABLE_REFLECTION_SYSTEM}\n"
            p5_text += f"ENABLE_DREAM_PROCESSING = {config.ENABLE_DREAM_PROCESSING}\n"
            p5_text += f"ENABLE_PROMISE_SYSTEM = {config.ENABLE_PROMISE_SYSTEM}\n"
            p5_text += f"ENABLE_THEORY_OF_MIND = {config.ENABLE_THEORY_OF_MIND}\n"
            p5_text += f"ENABLE_AFFECTIVE_COMPUTING_DEEP = {config.ENABLE_AFFECTIVE_COMPUTING_DEEP}\n"
            p5_text += f"ENABLE_ETHICAL_REASONING = {config.ENABLE_ETHICAL_REASONING}\n"
            p5_text += f"ENABLE_HOMEOSTASIS = {config.ENABLE_HOMEOSTASIS}\n"
            p5_text += f"ENABLE_IDENTITY_SYSTEM = {config.ENABLE_IDENTITY_SYSTEM}\n"
            
            self.phase5_status_text.delete('1.0', 'end')
            self.phase5_status_text.insert('1.0', p5_text)
            
            # Core settings
            core_text = ""
            core_text += f"DEFAULT_BOT_NAME = {config.DEFAULT_BOT_NAME}\n"
            core_text += f"WAKE_WORD = {config.WAKE_WORD}\n"
            core_text += f"USE_WAKE_WORD = {config.USE_WAKE_WORD}\n"
            core_text += f"ENABLE_SLEEP_MODE = {config.ENABLE_SLEEP_MODE}\n"
            core_text += f"ENABLE_DREAM_STATE = {config.ENABLE_DREAM_STATE}\n"
            core_text += f"ENABLE_NOTE_TAKING = {config.ENABLE_NOTE_TAKING}\n"
            core_text += f"ENABLE_TASKS = {config.ENABLE_TASKS}\n"
            core_text += f"ENABLE_DIARY = {config.ENABLE_DIARY}\n"
            core_text += f"ENABLE_KNOWLEDGE_GRAPH = {config.ENABLE_KNOWLEDGE_GRAPH}\n"
            
            self.core_config_text.delete('1.0', 'end')
            self.core_config_text.insert('1.0', core_text)
            
            # Advanced settings
            adv_text = ""
            adv_text += f"USE_WHISPER = {config.USE_WHISPER}\n"
            adv_text += f"USE_VAD = {config.USE_VAD}\n"
            adv_text += f"USE_VECTOR_MEMORY = {config.USE_VECTOR_MEMORY}\n"
            adv_text += f"USE_STREAMING = {config.USE_STREAMING}\n"
            adv_text += f"USE_INTERRUPTS = {config.USE_INTERRUPTS}\n"
            adv_text += f"USE_BACKGROUND_TASKS = {config.USE_BACKGROUND_TASKS}\n"
            adv_text += f"USE_LEARNING_SYSTEM = {config.USE_LEARNING_SYSTEM}\n"
            
            self.advanced_config_text.delete('1.0', 'end')
            self.advanced_config_text.insert('1.0', adv_text)
            
            # Vision settings
            vision_text = ""
            vision_text += f"ENABLE_VISION = {config.ENABLE_VISION}\n"
            vision_text += f"VISION_CAMERAS = {config.VISION_CAMERAS}\n"
            vision_text += f"VISION_MODEL = {config.VISION_MODEL}\n"
            vision_text += f"VISION_ANALYSIS_INTERVAL = {config.VISION_ANALYSIS_INTERVAL}s\n"
            vision_text += f"VISION_FRAME_SKIP = {config.VISION_FRAME_SKIP}\n"
            vision_text += f"VISION_MOTION_SENSITIVITY = {config.VISION_MOTION_SENSITIVITY}\n"
            # vision_text += f"VISION_PROACTIVE_COMMENTS = {config.VISION_PROACTIVE_COMMENTS}\n"  # Not in config yet
            
            self.vision_config_text.delete('1.0', 'end')
            self.vision_config_text.insert('1.0', vision_text)
            
            # System info
            sys_text = ""
            sys_text += f"Python: {sys.version.split()[0]}\n"
            sys_text += f"Ollama URL: {config.OLLAMA_URL}\n"
            sys_text += f"Ollama Model: {config.OLLAMA_MODEL}\n"
            sys_text += f"Database: {config.DB_PATH}\n"
            sys_text += f"Data Directory: {config.DATA_DIR}\n"
            sys_text += f"Log File: {config.LOG_FILE}\n"
            sys_text += f"Log Level: {config.LOG_LEVEL}\n"
            
            self.system_info_text.delete('1.0', 'end')
            self.system_info_text.insert('1.0', sys_text)
            
        except Exception as e:
            self._log_debug(f"Settings update error: {e}")
            
    def _update_autonomous_data(self):
        """Update autonomous life data"""
        try:
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                al = self.bot.autonomous_life
                
                if hasattr(al, 'cycle_count'):
                    self.cycle_count_label.config(text=f"Cycles: {al.cycle_count}")
                
                if hasattr(al, 'last_cycle'):
                    self.last_cycle_label.config(
                        text=f"Last: {al.last_cycle.strftime('%H:%M:%S') if al.last_cycle else 'Never'}")
        except Exception as e:
            self._log_debug(f"Autonomous update error: {e}")
            
    def _update_metrics_data(self):
        """Update performance metrics"""
        try:
            if hasattr(self.bot, 'metrics'):
                metrics = self.bot.metrics
                
                if hasattr(metrics, 'total_messages'):
                    self.total_messages_label.config(text=f"Total Messages: {metrics.total_messages}")
                
                if hasattr(metrics, 'session_messages'):
                    self.session_messages_label.config(text=f"This Session: {metrics.session_messages}")
        except Exception as e:
            self._log_debug(f"Metrics update error: {e}")
            
    def _update_enhancement_data(self):
        """NEW! Update enhancement modules data"""
        try:
            # Relationship tracking
            if getattr(self.bot, 'relationship_tracker', None):
                try:
                    summary = self.bot.relationship_tracker.get_relationship_summary()
                    
                    # Ensure summary is a dict, not a string
                    if not isinstance(summary, dict):
                        return  # Skip if not valid dict
                    
                    # Safe dict access with defaults
                    self.trust_relationship_label.config(
                        text=f"Trust: {int(summary.get('trust_score', 0))}%")
                    self.rapport_label.config(
                        text=f"Rapport: {int(summary.get('rapport', 0))}%")
                    self.understanding_label.config(
                        text=f"Understanding: {int(summary.get('understanding', 0))}%")
                    
                    self.days_together_label.config(
                        text=f"Days Together: {summary.get('days_together', 0)}")
                    self.total_interactions_label.config(
                        text=f"Total Interactions: {summary.get('total_interactions', 0)}")
                    self.positive_ratio_label.config(
                        text=f"Positive Ratio: {summary.get('positive_ratio', 0):.1f}%")
                    
                    # Milestones - safe access
                    if hasattr(self.bot.relationship_tracker, 'data') and isinstance(self.bot.relationship_tracker.data, dict):
                        milestones = self.bot.relationship_tracker.data.get('milestones', [])
                        self.milestones_text.delete('1.0', 'end')
                        for milestone in milestones[-10:]:
                            if isinstance(milestone, dict):
                                self.milestones_text.insert('end',
                                    f"🏆 {milestone.get('name', 'Unknown')}\n")
                                achieved = milestone.get('achieved', '')
                                if achieved:
                                    self.milestones_text.insert('end',
                                        f"   Achieved: {str(achieved)[:10]}\n\n")
                except Exception:
                    pass  # Silently fail - no logging
            
            # Learning tracking
            if getattr(self.bot, 'learning_tracker', None):
                try:
                    learnings = self.bot.learning_tracker.get_recent_learnings(limit=1000)
                    if isinstance(learnings, list):
                        self.total_learnings_label.config(text=f"Total Learnings: {len(learnings)}")
                        
                        # Recent learnings
                        recent = learnings[:20]
                        self.learnings_text.delete('1.0', 'end')
                        for learning in recent:
                            if isinstance(learning, dict):
                                self.learnings_text.insert('end',
                                    f"[{learning.get('category', 'unknown')}] {learning.get('content', '')}\n")
                                self.learnings_text.insert('end',
                                    f"  Confidence: {learning.get('confidence', 0):.1%} | Reinforcements: {learning.get('reinforcements', 0)}\n\n")
                except Exception:
                    pass  # Silently fail
            
            # Goal tracking
            if getattr(self.bot, 'goal_manager', None):
                try:
                    active_goals = self.bot.goal_manager.get_active_goals()
                    if isinstance(active_goals, list):
                        self.active_goals_label.config(text=f"Active Goals: {len(active_goals)}")
                        
                        # Category counts
                        learning_goals = self.bot.goal_manager.get_goals_by_category('learning')
                        mastery_goals = self.bot.goal_manager.get_goals_by_category('mastery')
                        creativity_goals = self.bot.goal_manager.get_goals_by_category('creativity')
                        exploration_goals = self.bot.goal_manager.get_goals_by_category('exploration')
                        
                        self.learning_goals_label.config(
                            text=f"📚 Learning: {len(learning_goals) if isinstance(learning_goals, list) else 0}")
                        self.mastery_goals_label.config(
                            text=f"🏆 Mastery: {len(mastery_goals) if isinstance(mastery_goals, list) else 0}")
                        self.creativity_goals_label.config(
                            text=f"🎨 Creativity: {len(creativity_goals) if isinstance(creativity_goals, list) else 0}")
                        self.exploration_goals_label.config(
                            text=f"🗺️ Exploration: {len(exploration_goals) if isinstance(exploration_goals, list) else 0}")
                        
                        # Active goals list
                        self.goals_text.delete('1.0', 'end')
                        for goal in active_goals:
                            if isinstance(goal, dict):
                                self.goals_text.insert('end',
                                    f"[{goal.get('category', 'unknown')}] {goal.get('title', 'Untitled')}\n")
                                self.goals_text.insert('end',
                                    f"  {goal.get('description', '')}\n")
                                self.goals_text.insert('end',
                                    f"  Progress: {goal.get('progress', 0)*100:.0f}% | Priority: {goal.get('priority', 0)}\n\n")
                except Exception:
                    pass  # Silently fail
            
            # Emotion journal
            if hasattr(self.bot, 'emotion_journal'):
                try:
                    insights = self.bot.emotion_journal.get_emotional_insights()
                    if isinstance(insights, dict):
                        self.most_common_emotion_label.config(
                            text=f"Most Common: {insights.get('most_common_emotion', 'Unknown')}")
                        self.emotional_volatility_label.config(
                            text=f"Volatility: {insights.get('emotional_volatility', 0):.2f}")
                        self.unique_emotions_label.config(
                            text=f"Unique Emotions: {insights.get('unique_emotions_experienced', 0)}")
                except Exception:
                    pass  # Silently fail
                        
        except Exception:
            pass  # Top-level silently fail - no debug logging
            
    def _update_emotion_bars(self, emotion):
        """Update emotion intensity bars"""
        try:
            # Primary emotion
            self._draw_bar(self.emotion_bars['Primary'], emotion.intensity,
                          emotion.emotion.value.title())
            
            # Secondary emotions
            secondaries = list(emotion.secondary_emotions.items())
            if len(secondaries) > 0:
                e, i = secondaries[0]
                self._draw_bar(self.emotion_bars['Secondary 1'], i, e.value.title())
            else:
                self._draw_bar(self.emotion_bars['Secondary 1'], 0, "None")
                
            if len(secondaries) > 1:
                e, i = secondaries[1]
                self._draw_bar(self.emotion_bars['Secondary 2'], i, e.value.title())
            else:
                self._draw_bar(self.emotion_bars['Secondary 2'], 0, "None")
        except:
            pass
            
    def _update_health_bar(self, metric, value):
        """Update a health bar"""
        try:
            bar_data = self.health_bars[metric]
            canvas = bar_data['canvas']
            label = bar_data['label']
            color = bar_data['color']
            
            # Update label
            percentage = int(value * 100)
            label.config(text=f"{percentage}%")
            
            # Draw bar
            canvas.delete('all')
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            
            if width > 1:
                # Background
                canvas.create_rectangle(0, 0, width, height, fill=self.bg_dark, outline='')
                # Filled portion
                fill_width = int(width * value)
                canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline='')
        except:
            pass
            
    def _draw_bar(self, canvas, intensity, label_text):
        """Draw an intensity bar"""
        try:
            canvas.delete('all')
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            
            if width > 1:
                # Background
                canvas.create_rectangle(0, 0, width, height, fill=self.bg_dark, outline='')
                # Filled portion
                fill_width = int(width * intensity)
                canvas.create_rectangle(0, 0, fill_width, height, fill=self.accent_orange, outline='')
                # Text
                canvas.create_text(10, height//2, text=f"{label_text} ({intensity:.2f})",
                                  anchor='w', fill=self.fg_text, font=('Arial', 9))
        except:
            pass
            
    def _draw_progress_bar(self, canvas, progress):
        """Draw a progress bar"""
        try:
            canvas.delete('all')
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            
            if width > 1:
                canvas.create_rectangle(0, 0, width, height, fill=self.bg_dark, outline='')
                fill_width = int(width * progress)
                canvas.create_rectangle(0, 0, fill_width, height, fill=self.accent_green, outline='')
        except:
            pass
            
    def _apply_update(self, update: Dict[str, Any]):
        """Apply queued update"""
        update_type = update.get('type')
        
        if update_type == 'conversation':
            self._update_conversation(update)
        elif update_type == 'emotion':
            self._update_emotion(update)
        elif update_type == 'cognitive':
            self._update_cognitive(update)
        elif update_type == 'autonomous':
            self._update_autonomous(update)
        elif update_type == 'activity':
            self._update_activity(update)
        elif update_type == 'debug':
            self._log_debug(update.get('message', ''))
            
    def _update_conversation(self, update):
        """Update conversation display"""
        speaker = update.get('speaker', 'system')
        text = update.get('text', '')
        emotion = update.get('emotion', '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        self.conversation_text.insert('end', f"[{timestamp}] ", 'system')
        
        # Use tag based on speaker type
        tag = 'system'
        if speaker.lower() == 'user':
            tag = 'user'
        elif speaker.lower() != 'system':
            tag = 'bot'
        
        if emotion and tag == 'bot':
            self.conversation_text.insert('end', f"{speaker} ", tag)
            self.conversation_text.insert('end', f"({emotion}): ", 'emotion')
        else:
            self.conversation_text.insert('end', f"{speaker}: ", tag)
        
        self.conversation_text.insert('end', f"{text}\n\n")
        self.conversation_text.see('end')
        
    def _update_emotion(self, update):
        """Update from emotion queue"""
        emotion = update.get('emotion', 'Unknown')
        intensity = update.get('intensity', 0)
        self.current_emotion_label.config(text=f"{emotion} ({intensity:.1f})")
        
    def _update_cognitive(self, update):
        """Update from cognitive queue"""
        if 'working_memory' in update:
            self.working_memory_text.delete('1.0', 'end')
            for i, concept in enumerate(update['working_memory'], 1):
                self.working_memory_text.insert('end', f"{i}. {concept}\n")
            
        if 'attention' in update:
            self.attention_label.config(text=update['attention'])
            
        if 'thought' in update:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.inner_monologue_text.insert('end', f"[{timestamp}] {update['thought']}\n\n")
            self.inner_monologue_text.see('end')
            
    def _update_autonomous(self, update):
        """Update from autonomous queue"""
        if 'goal' in update:
            self.current_goal_label.config(text=f"[TARGET] {update['goal']}")
        if 'energy' in update:
            self._update_health_bar('Energy', update['energy'] / 100)
        if 'focus' in update:
            self._update_health_bar('Focus', update['focus'] / 100)
            
    def _update_activity(self, update):
        """Update activity log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        activity = update.get('activity', '')
        self.activity_log_text.insert('end', f"[{timestamp}] {activity}\n")
        self.activity_log_text.see('end')
        
    def _log_debug(self, message):
        """Log debug message"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self.debug_text.insert('end', f"[{timestamp}] {message}\n")
        self.debug_text.see('end')
        
    def _clear_debug(self):
        """Clear debug log"""
        self.debug_text.delete('1.0', 'end')
        
    def _refresh_debug(self):
        """Refresh debug info"""
        self._log_debug("=== Debug Info Refreshed ===")
        if self.bot:
            self._log_debug(f"Bot active: {hasattr(self.bot, 'phase5')}")
            self._log_debug(f"Phase 5 active: {hasattr(self.bot, 'phase5') and self.bot.phase5}")
            self._log_debug(f"Enhancements active: {hasattr(self.bot, 'relationship_tracker')}")
        
    def run(self):
        """Start GUI"""
        # Start minimized if requested
        if hasattr(self, 'start_minimized') and self.start_minimized:
            self.root.withdraw()  # Hide window initially
        self.root.mainloop()
    
    def show_window(self):
        """Show the GUI window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self):
        """Hide the GUI window"""
        self.root.withdraw()
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.root.state() == 'withdrawn':
            self.show_window()
        else:
            self.hide_window()
        
    def add_message(self, msg_type_or_speaker: str, text: str = None, **kwargs):
        """Queue conversation message - compatible with both call patterns:
           add_message('system', 'text')  -- from launchers
           add_message('conversation', speaker='Name', text='msg', emotion='joy')  -- from bot core
        """
        if text is not None and 'speaker' not in kwargs:
            # Simple call: add_message(speaker, text)
            self.message_queue.put({
                'type': 'conversation',
                'speaker': msg_type_or_speaker,
                'text': text
            })
        else:
            # Bot core call: add_message(msg_type, speaker=..., text=..., emotion=...)
            self.message_queue.put({
                'type': msg_type_or_speaker,
                'speaker': kwargs.get('speaker', msg_type_or_speaker),
                'text': kwargs.get('text', text or ''),
                'emotion': kwargs.get('emotion', '')
            })
        
    def add_thought(self, thought: str):
        """Queue inner thought"""
        self.message_queue.put({
            'type': 'cognitive',
            'thought': thought
        })
        
    def add_activity(self, activity: str):
        """Queue autonomous activity"""
        self.message_queue.put({
            'type': 'activity',
            'activity': activity
        })
        
    def add_debug(self, message: str):
        """Queue debug message"""
        self.message_queue.put({
            'type': 'debug',
            'message': message
        })

def launch_phase5_gui(bot_instance=None, start_minimized=False):
    """Launch complete Phase 5 GUI"""
    gui = CompletePhase5GUI(bot_instance, start_minimized=start_minimized)
    return gui

if __name__ == "__main__":
    gui = CompletePhase5GUI()
    gui.run()
