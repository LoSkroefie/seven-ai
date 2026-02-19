"""
Clawdbot Integration for Seven
Allows Seven to execute complex tasks through Clawdbot's skills and gateway
"""
import json
import subprocess
import asyncio
import websockets
from typing import Optional, Dict, Any
from pathlib import Path
import os
import time

class ClawdbotClient:
    """Client to interact with Clawdbot gateway"""
    
    def __init__(self, gateway_url: str = "ws://127.0.0.1:18789", logger=None):
        """
        Initialize Clawdbot client
        
        Args:
            gateway_url: WebSocket URL for Clawdbot gateway
            logger: Logger instance
        """
        self.gateway_url = gateway_url
        self.logger = logger
        self.clawdbot_path = os.getenv("CLAWDBOT_PATH", "clawdbot")
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY", "ollama-local")
        
        # Ensure Node.js and clawdbot are in PATH
        node_path = r"C:\Program Files\nodejs"
        npm_path = r"C:\Users\USER-PC\AppData\Roaming\npm"
        os.environ["PATH"] = f"{node_path};{npm_path};" + os.environ.get("PATH", "")
        
        if self.logger:
            self.logger.info(f"Clawdbot client initialized (gateway: {gateway_url})")
    
    async def send_message_async(self, message: str, timeout: int = 30) -> Optional[str]:
        """
        Send a message to Clawdbot via WebSocket gateway
        
        Args:
            message: User message/command
            timeout: Response timeout in seconds
            
        Returns:
            Response from Clawdbot or None if error
        """
        try:
            async with websockets.connect(self.gateway_url, timeout=timeout) as ws:
                # Send message
                await ws.send(json.dumps({
                    "type": "chat",
                    "content": message,
                    "agent": "main"
                }))
                
                # Wait for response
                response = await ws.recv()
                data = json.loads(response)
                
                if self.logger:
                    self.logger.debug(f"Clawdbot response: {data}")
                
                return data.get("content", data.get("text", str(data)))
                
        except websockets.exceptions.WebSocketException as e:
            if self.logger:
                self.logger.error(f"WebSocket error: {e}")
            return None
        except asyncio.TimeoutError:
            if self.logger:
                self.logger.error("Clawdbot gateway timeout")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Clawdbot error: {e}")
            return None
    
    def send_message(self, message: str, timeout: int = 30) -> Optional[str]:
        """
        Synchronous wrapper for send_message_async
        
        Args:
            message: User message/command
            timeout: Response timeout in seconds
            
        Returns:
            Response from Clawdbot or None if error
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message_async(message, timeout))
            loop.close()
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in synchronous send: {e}")
            return None
    
    def execute_command(self, command: str, timeout: int = 30) -> Optional[str]:
        """
        Execute a Clawdbot CLI command directly
        
        Args:
            command: Clawdbot command (e.g., "skills list", "doctor")
            timeout: Command timeout in seconds
            
        Returns:
            Command output or None if error
        """
        try:
            # Set environment
            env = os.environ.copy()
            env["OLLAMA_API_KEY"] = self.ollama_api_key
            
            # Build full command
            full_cmd = f"{self.clawdbot_path} {command}"
            
            if self.logger:
                self.logger.debug(f"Executing: {full_cmd}")
            
            # Execute command
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                if self.logger:
                    self.logger.error(f"Clawdbot command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Command timeout: {command}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Command execution error: {e}")
            return None
    
    def check_gateway_status(self) -> bool:
        """
        Check if Clawdbot gateway is running
        
        Returns:
            True if gateway is accessible, False otherwise
        """
        try:
            result = self.execute_command("doctor", timeout=5)
            return result is not None
        except Exception:
            return False
    
    def get_skills(self) -> Optional[str]:
        """
        Get list of available Clawdbot skills
        
        Returns:
            Skills list or None if error
        """
        return self.execute_command("skills list")
    
    def process_task(self, task_description: str) -> Optional[str]:
        """
        Process a complex task through Clawdbot
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Task result or None if error
        """
        if self.check_gateway_status():
            # Use gateway for interactive tasks
            return self.send_message(task_description)
        else:
            if self.logger:
                self.logger.warning("Gateway not available, trying CLI fallback")
            # Fallback to CLI for simple queries
            return self.execute_command(f"run {task_description}")


def detect_clawdbot_intent(text: str) -> Optional[str]:
    """
    Detect if user's message should be handled by Clawdbot
    
    Args:
        text: User's spoken text
        
    Returns:
        Intent type or None if no Clawdbot intent detected
    """
    text_lower = text.lower()
    
    # Keywords that suggest Clawdbot should handle it
    clawdbot_keywords = [
        "whatsapp", "send message", "check messages",
        "github", "git", "repository",
        "complex task", "advanced task",
        "code review", "analyze code",
        "deploy", "deployment",
        "search codebase", "find in code",
        "notion", "slack",
        "file system", "organize files",
        "run command", "execute",
    ]
    
    for keyword in clawdbot_keywords:
        if keyword in text_lower:
            return "clawdbot_task"
    
    return None


# Example usage
if __name__ == "__main__":
    # Test Clawdbot connection
    client = ClawdbotClient()
    
    print("Testing Clawdbot integration...")
    
    # Check status
    if client.check_gateway_status():
        print("[OK] Clawdbot gateway is running")
        
        # Test message
        response = client.send_message("What can you help me with?")
        if response:
            print(f"[OK] Response: {response}")
        else:
            print("[ERROR] No response from gateway")
    else:
        print("[ERROR] Clawdbot gateway not accessible")
        print("Make sure gateway is running: clawdbot gateway --port 18789")
