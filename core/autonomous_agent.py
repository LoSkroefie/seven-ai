"""
Autonomous Agent v2.0 - Seven's Enhanced Tool-Using Intelligence

NOW WITH:
- 20 tools (10 base + 10 advanced)
- Expanded natural language patterns
- Better tool selection logic
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Intent:
    """Detected user intent"""
    category: str
    confidence: float
    keywords: list
    needs_tool: bool
    
    def __repr__(self):
        return f"Intent({self.category}, confidence={self.confidence:.2f})"


class AutonomousAgent:
    """Autonomous decision-making for Seven"""
    
    def __init__(self, tool_library=None):
        """Initialize with tool library"""
        self.tool_library = tool_library
        
        # EXPANDED intent patterns for natural conversation
        self.patterns = {
            "SYSTEM_QUERY": [
                # Disk/Storage
                r"(how much|check|show me) .*(disk|storage|space)",
                r"(what'?s|what is|do i have) (my |the )?(disk|storage|space)",
                r"check (my |the )?(disk|storage|space|drive)",
                
                # Memory/RAM
                r"(what'?s|check|show me) (my |the )?(memory|ram)",
                r"memory usage",
                r"what(?:'?s| is) (eating|using|hogging|taking) (my |all |the )?(ram|memory)",
                r"(why is|what(?:'?s| is) making) (my )?(computer|pc|system) slow",
                
                # CPU
                r"(what'?s|show me|tell me about|check) (my |the )?cpu",
                r"cpu (info|stats|usage)",
                
                # Processes/Programs
                r"(list|show|what|check) (processes|programs|tasks|running)",
                r"what'?s? running",
                r"(top|biggest) (memory|ram|cpu) (consumers|hogs|users)",
                
                # Network
                r"(what'?s|show me|check) (my |the )?(ip|network)",
                r"(am i|check) (connected|online)",
                
                # Battery
                r"(battery|charge) (level|status)",
                r"how much (battery|charge)",
                
                # Uptime
                r"(how long|uptime|been running)",
                r"(when did|last) (restart|reboot)",
                
                # System
                r"(system|computer|pc) (info|stats|details|status)",
                r"tell me about (my |this )?(system|computer)",
                r"check (my |this |the )?(system|computer|pc)",
                
                # Drives
                r"(list|show|check) (all |my )?(drives|disks)",
                
                # Services
                r"(list|show|check) (running )?services",
                
                # WiFi
                r"(list|show|check) (wifi|wireless) networks",
                r"available (wifi|wireless)",
            ],
            "FILE_OPERATION": [
                r"(find|search|locate|where is) .+ (file|folder|document)",
                r"(list|show) files (in|at|from)",
                r"(how big|size of) .+ (folder|file)",
                r"file (info|details)",
            ],
            "CALCULATION": [
                r"(what'?s|calculate|compute) \d+",
                r"\d+ (plus|\+|minus|\-|times|\*|divided) \d+",
                r"what'?s? \d+%? of \d+",
            ],
            "TIME_DATE": [
                r"(what'?s|what is|tell me) the (time|date)",
                r"what (time|date) is it",
                r"current (time|date)",
            ],
        }
    
    def detect_intent(self, user_input: str) -> Intent:
        """Detect what the user wants"""
        text = user_input.lower().strip()
        
        # Check each category
        for category, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text):
                    keywords = text.split()[:3]  # First 3 words
                    
                    return Intent(
                        category=category,
                        confidence=0.9,
                        keywords=keywords,
                        needs_tool=True
                    )
        
        # Default: conversation
        return Intent(
            category="CONVERSATION",
            confidence=1.0,
            keywords=[],
            needs_tool=False
        )
    
    def select_tool(self, intent: Intent, user_input: str) -> Optional[Any]:
        """Select appropriate tool - NOW WITH 20 TOOLS!"""
        if not self.tool_library:
            return None
        
        text = user_input.lower()
        
        # System queries
        if intent.category == "SYSTEM_QUERY":
            # Disk/Storage
            if "disk" in text or "space" in text or "storage" in text:
                if "all" in text or ("list" in text and "drive" in text):
                    return self.tool_library.get_tool("list_drives")
                return self.tool_library.get_tool("disk_space")
            
            # Memory
            elif "memory" in text or "ram" in text:
                return self.tool_library.get_tool("memory_usage")
            
            # CPU
            elif "cpu" in text or "processor" in text:
                return self.tool_library.get_tool("cpu_info")
            
            # Processes
            elif any(w in text for w in ["process", "program", "task", "running"]):
                return self.tool_library.get_tool("list_processes")
            
            # Network
            elif any(w in text for w in ["network", "ip", "internet", "connected"]):
                return self.tool_library.get_tool("network_info")
            
            # Battery
            elif "battery" in text or "charge" in text:
                return self.tool_library.get_tool("battery_status")
            
            # Uptime
            elif "uptime" in text or ("how long" in text and "running" in text):
                return self.tool_library.get_tool("uptime")
            
            # WiFi
            elif "wifi" in text or "wireless" in text:
                return self.tool_library.get_tool("wifi_networks")
            
            # Services
            elif "service" in text:
                return self.tool_library.get_tool("running_services")
            
            # General system
            else:
                return self.tool_library.get_tool("system_info")
        
        # File operations
        elif intent.category == "FILE_OPERATION":
            if "find" in text or "search" in text or "locate" in text:
                return self.tool_library.get_tool("find_file")
            elif "size" in text or "big" in text:
                return self.tool_library.get_tool("folder_size")
            elif "info" in text or "details" in text:
                return self.tool_library.get_tool("file_info")
            else:
                return self.tool_library.get_tool("list_files")
        
        # Calculations
        elif intent.category == "CALCULATION":
            return self.tool_library.get_tool("calculate")
        
        # Time/Date
        elif intent.category == "TIME_DATE":
            if "time" in text:
                return self.tool_library.get_tool("current_time")
            else:
                return self.tool_library.get_tool("current_date")
        
        return None
    
    def extract_parameters(self, intent: Intent, user_input: str) -> Dict[str, Any]:
        """Extract parameters from user input"""
        params = {}
        text = user_input.lower()
        
        # File operations
        if intent.category == "FILE_OPERATION":
            # Extract filename
            patterns = [
                r"find (my |the )?(['\"]?[\w\s]+['\"]?)",
                r"search for (my |the )?(['\"]?[\w\s]+['\"]?)",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    params['filename'] = match.group(2).strip('\'"')
                    break
            
            # Extract path
            if " in " in text:
                parts = text.split(" in ")
                if len(parts) > 1:
                    params['path'] = parts[1].strip()
        
        # Calculations
        elif intent.category == "CALCULATION":
            # Extract math expression
            expr = text.replace("what's", "").replace("what is", "")
            expr = expr.replace("calculate", "").replace("compute", "").strip()
            params['expression'] = expr
        
        return params
    
    def can_execute_autonomously(self, tool) -> bool:
        """Check if tool can auto-execute"""
        if not tool:
            return False
        
        # Lazy load permission manager
        if not hasattr(self, 'permission_manager'):
            from core.permission_manager import PermissionManager
            self.permission_manager = PermissionManager()
        
        return self.permission_manager.is_safe(tool)
