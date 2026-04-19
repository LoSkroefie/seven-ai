    def select_tool(self, intent: Intent, user_input: str) -> Optional[Any]:
        """
        Select appropriate tool based on intent - NOW WITH 20 TOOLS!
        
        Args:
            intent: Detected intent
            user_input: Original user input
            
        Returns:
            Tool object or None
        """
        if not self.tool_library:
            return None
        
        text = user_input.lower()
        
        # System queries
        if intent.category == "SYSTEM_QUERY":
            # Disk/Storage
            if any(word in text for word in ["disk", "space", "storage", "drive"]):
                if "all" in text or "list" in text:
                    return self.tool_library.get_tool("list_drives")
                return self.tool_library.get_tool("disk_space")
            
            # Memory/RAM
            elif any(word in text for word in ["memory", "ram"]):
                return self.tool_library.get_tool("memory_usage")
            
            # CPU
            elif "cpu" in text or "processor" in text:
                return self.tool_library.get_tool("cpu_info")
            
            # Processes
            elif any(word in text for word in ["process", "program", "task", "running"]):
                return self.tool_library.get_tool("list_processes")
            
            # Network/IP
            elif any(word in text for word in ["network", "ip", "internet", "connected"]):
                return self.tool_library.get_tool("network_info")
            
            # Battery
            elif any(word in text for word in ["battery", "charge"]):
                return self.tool_library.get_tool("battery_status")
            
            # Uptime
            elif any(word in text for word in ["uptime", "running", "restart", "reboot"]):
                return self.tool_library.get_tool("uptime")
            
            # WiFi
            elif any(word in text for word in ["wifi", "wireless", "networks"]):
                return self.tool_library.get_tool("wifi_networks")
            
            # Services
            elif "service" in text:
                return self.tool_library.get_tool("running_services")
            
            # General system info
            elif any(word in text for word in ["system", "computer", "pc"]):
                return self.tool_library.get_tool("system_info")
        
        # File operations
        elif intent.category == "FILE_OPERATION":
            if "find" in text or "search" in text or "locate" in text:
                return self.tool_library.get_tool("find_file")
            elif "list" in text or "show" in text:
                return self.tool_library.get_tool("list_files")
            elif "size" in text or "big" in text:
                return self.tool_library.get_tool("folder_size")
            elif "info" in text or "details" in text:
                return self.tool_library.get_tool("file_info")
        
        # Calculations
        elif intent.category == "CALCULATION":
            return self.tool_library.get_tool("calculate")
        
        # Time/date
        elif intent.category == "TIME_DATE":
            if "time" in text:
                return self.tool_library.get_tool("current_time")
            elif "date" in text:
                return self.tool_library.get_tool("current_date")
        
        return None
