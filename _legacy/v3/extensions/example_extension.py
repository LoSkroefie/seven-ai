"""
Example Extension for Seven AI

This is a template showing how to create extensions.
Copy this file and modify it to create your own.

Extensions are auto-discovered from the extensions/ directory.
"""

from utils.plugin_loader import SevenExtension


class ExampleExtension(SevenExtension):
    """Example extension that logs a greeting"""
    
    name = "Example Extension"
    version = "1.0"
    description = "A simple example extension"
    author = "Seven AI"
    
    # Run every 60 minutes (set to 0 to disable scheduling)
    schedule_interval_minutes = 0
    
    def init(self, bot=None):
        """Called once when loaded"""
        self.bot = bot
        self.greetings_sent = 0
    
    def run(self, context: dict = None) -> dict:
        """Main execution — called on schedule or manually"""
        self.greetings_sent += 1
        return {
            "message": f"Hello from Example Extension! (run #{self.greetings_sent})",
            "status": "ok"
        }
    
    def on_message(self, user_message: str, bot_response: str):
        """React to user messages (optional)"""
        # Return None to not modify anything
        return None
    
    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "greetings_sent": self.greetings_sent,
            "running": True
        }
