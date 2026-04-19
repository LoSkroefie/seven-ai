    
    def _init_tools(self):
        """Initialize all tools"""
        
        # 1. Disk Space (PowerShell - works!)
        self.tools["disk_space"] = Tool(
            name="disk_space",
            command="powershell -Command \"Get-PSDrive C | Select-Object Name,Used,Free\"",
            description="Check disk space on C drive",
            parser=self._parse_disk_space_ps
        )
        
        # 2. Memory Usage (PowerShell - works!)
        self.tools["memory_usage"] = Tool(
            name="memory_usage",
            command="powershell -Command \"$os = Get-CimInstance Win32_OperatingSystem; $free = [math]::Round($os.FreePhysicalMemory/1MB,1); $total = [math]::Round($os.TotalVisibleMemorySize/1MB,1); Write-Output \\\"$free GB free of $total GB\\\"\"",
            description="Check RAM usage"
        )
        
        # 3. CPU Info (PowerShell - works!)
        self.tools["cpu_info"] = Tool(
            name="cpu_info",
            command="powershell -Command \"$cpu = Get-CimInstance Win32_Processor; Write-Output \\\"$($cpu.Name), $($cpu.NumberOfCores) cores\\\"\"",
            description="Get CPU information"
        )
        
        # 4. List Processes (tasklist - works!)
        self.tools["list_processes"] = Tool(
            name="list_processes",
            command="tasklist /FO CSV /NH",
            description="List running processes",
            parser=self._parse_processes
        )
        
        # 5. Network Info (ipconfig - works!)
        self.tools["network_info"] = Tool(
            name="network_info",
            command="ipconfig | findstr /i \"IPv4\"",
            description="Get IP address",
            parser=self._parse_network
        )
        
        # 6. Current Time
        self.tools["current_time"] = Tool(
            name="current_time",
            command="powershell -Command \"Get-Date -Format 'HH:mm:ss'\"",
            description="Get current time"
        )
        
        # 7. Current Date
        self.tools["current_date"] = Tool(
            name="current_date",
            command="powershell -Command \"Get-Date -Format 'yyyy-MM-dd'\"",
            description="Get current date"
        )
        
        # 8. List Files
        self.tools["list_files"] = Tool(
            name="list_files",
            command="dir \"{path}\" /B 2>nul",
            description="List files in directory"
        )
        
        # 9. Find File
        self.tools["find_file"] = Tool(
            name="find_file",
            command="where /r C:\\Users\\USER-PC {filename} 2>nul",
            description="Search for files"
        )
        
        # 10. System Info
        self.tools["system_info"] = Tool(
            name="system_info",
            command="systeminfo | findstr /B /C:\"OS Name\" /C:\"System Type\"",
            description="Get operating system info"
        )
