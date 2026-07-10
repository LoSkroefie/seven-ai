"""
System Tray GUI for Enhanced Bot
Minimize to tray with right-click menu and visual indicators
"""
import pystray
from PIL import Image, ImageDraw
import threading
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

class SystemTrayApp:
    """System tray application for bot control"""
    
    def __init__(self, bot_instance=None, main_gui=None):
        self.bot = bot_instance
        self.main_gui = main_gui
        self.icon = None
        self.current_state = 'idle'  # idle, listening, speaking, sleeping
        
    def create_icon_image(self, color='green', pulse=False):
        """Create icon image with color indicator"""
        # Create 64x64 image
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='black')
        dc = ImageDraw.Draw(image)
        
        # Color mapping
        color_map = {
            'green': '#4CAF50',    # Idle
            'blue': '#2196F3',     # Listening
            'purple': '#9C27B0',   # Speaking
            'gray': '#757575',     # Sleeping
            'yellow': '#FFC107',   # Processing
        }
        
        fill_color = color_map.get(color, '#4CAF50')
        
        # Draw circle
        padding = 8
        dc.ellipse([padding, padding, width-padding, height-padding], 
                   fill=fill_color, outline='white', width=2)
        
        # Add "S" for Seven
        font_size = 32
        text = "S"
        # Simple text position (center)
        text_bbox = dc.textbbox((0, 0), text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2 - 5
        dc.text((text_x, text_y), text, fill='white')
        
        return image
    
    def show_main_window(self, icon, item):
        """Show the main GUI window"""
        if self.main_gui:
            try:
                if hasattr(self.main_gui, 'show_window'):
                    self.main_gui.show_window()
                else:
                    self.main_gui.root.deiconify()
                    self.main_gui.root.lift()
                    self.main_gui.root.focus_force()
            except Exception as e:
                logging.debug(f"Show window error: {e}")
    
    def hide_main_window(self, icon, item):
        """Hide the main GUI window"""
        if self.main_gui:
            try:
                if hasattr(self.main_gui, 'hide_window'):
                    self.main_gui.hide_window()
                else:
                    self.main_gui.root.withdraw()
            except Exception as e:
                logging.debug(f"Hide window error: {e}")
    
    def toggle_listening(self, icon, item):
        """Toggle bot listening state"""
        if self.bot:
            if hasattr(self.bot, 'sleeping') and self.bot.sleeping:
                # Wake up
                self.bot.sleeping = False
                self.update_icon_state('idle')
            else:
                # Sleep
                self.bot.sleeping = True
                self.update_icon_state('sleeping')
    
    def show_recent_notes(self, icon, item):
        """Show recent notes in notification"""
        if self.bot and hasattr(self.bot, 'notes'):
            try:
                notes = self.bot.notes.get_all_notes(limit=3)
                if notes:
                    note_text = "\n".join([f"- {note['content'][:50]}..." for note in notes])
                    self.icon.notify(f"Recent Notes:\n{note_text}", "Seven - Notes")
                else:
                    self.icon.notify("No notes yet", "Seven - Notes")
            except Exception as e:
                logging.debug(f"Show notes error: {e}")
    
    def show_stats(self, icon, item):
        """Show bot statistics"""
        if self.bot:
            try:
                stats = []
                if hasattr(self.bot, 'bot_name'):
                    stats.append(f"Name: {self.bot.bot_name}")
                if hasattr(self.bot, 'current_emotion'):
                    stats.append(f"Mood: {self.bot.current_emotion.value}")
                if hasattr(self.bot, 'notes'):
                    total, active = self.bot.notes.get_note_count()
                    stats.append(f"Notes: {active} active")
                
                self.icon.notify("\n".join(stats), "Seven - Status")
            except Exception as e:
                logging.debug(f"Show stats error: {e}")
    
    def open_settings(self, icon, item):
        """Open settings window"""
        if self.main_gui:
            try:
                self.main_gui.root.deiconify()
                self.main_gui.notebook.select(1)  # Switch to settings tab
            except Exception as e:
                logging.debug(f"Open settings error: {e}")
    
    def quit_app(self, icon, item):
        """Quit the application"""
        if self.bot:
            self.bot.running = False
        if self.icon:
            self.icon.stop()
        sys.exit(0)
    
    def create_menu(self):
        """Create right-click menu"""
        return pystray.Menu(
            pystray.MenuItem("Show Window", self.show_main_window, default=True),
            pystray.MenuItem("Hide Window", self.hide_main_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pause/Resume Listening", self.toggle_listening),
            pystray.MenuItem("Recent Notes", self.show_recent_notes),
            pystray.MenuItem("Statistics", self.show_stats),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self.open_settings),
            pystray.MenuItem("Quit", self.quit_app),
        )
    
    def update_icon_state(self, state):
        """Update icon appearance based on state"""
        self.current_state = state
        
        color_map = {
            'idle': 'green',
            'listening': 'blue',
            'speaking': 'purple',
            'sleeping': 'gray',
            'processing': 'yellow',
        }
        
        if self.icon:
            try:
                new_image = self.create_icon_image(color_map.get(state, 'green'))
                self.icon.icon = new_image
            except Exception as e:
                logging.debug(f"Icon update error: {e}")
    
    def run(self):
        """Run the system tray application"""
        # Create initial icon
        image = self.create_icon_image('green')
        
        # Create system tray icon
        self.icon = pystray.Icon(
            "SevenBot",
            image,
            "Seven - Voice Assistant",
            menu=self.create_menu()
        )
        
        # Run (blocking)
        self.icon.run()
    
    def run_async(self):
        """Run system tray in background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop the system tray"""
        if self.icon:
            self.icon.stop()


def launch_system_tray(bot_instance=None, main_gui=None):
    """Launch system tray application"""
    tray_app = SystemTrayApp(bot_instance, main_gui)
    return tray_app
