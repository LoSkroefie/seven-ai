    def _init_tools(self):
        """Initialize all tools - ALL WORKING NOW!"""
        
        # 1. Disk Space - PowerShell
        self.tools["disk_space"] = Tool(
            name="disk_space",
            command='powershell -Command "Get-PSDrive C | Select-Object Name, @{n=\'FreeGB\';e={[math]::Round(`$_.Free/1GB,1)}}, @{n=\'TotalGB\';e={[math]::Round((`$_.Used+`$_.Free)/1GB,1)}} | ForEach-Object { `$free = `$_.FreeGB; `$total = `$_.TotalGB; `$used = `$total - `$free; Write-Output \'C: drive has \' + `$free + \' GB free of \' + `$total + \' GB (\' + `$used + \' GB used)\' }"',
            description="Check disk space"
        )
        
        # 2. Memory - PowerShell
        self.tools["memory_usage"] = Tool(
            name="memory_usage",
            command='powershell -Command "`$os=Get-CimInstance Win32_OperatingSystem; `$free=[math]::Round(`$os.FreePhysicalMemory/1MB,1); `$total=[math]::Round(`$os.TotalVisibleMemorySize/1MB,1); `$used=[math]::Round(`$total-`$free,1); Write-Output (\'RAM: \' + `$used + \' GB used of \' + `$total + \' GB (\' + `$free + \' GB free)\')"',
            description="Check RAM usage"
        )
        
        # 3. CPU - PowerShell
        self.tools["cpu_info"] = Tool(
            name="cpu_info",
            command='powershell -Command "`$cpu=Get-CimInstance Win32_Processor; `$ghz=[math]::Round(`$cpu.MaxClockSpeed/1000,1); Write-Output (\'CPU: \' + `$cpu.Name + \', \' + `$cpu.NumberOfCores + \' cores, \' + `$ghz + \' GHz\')"',
            description="Get CPU info"
        )
        
        # 4. Processes - tasklist (works!)
        self.tools["list_processes"] = Tool(
            name="list_processes",
            command="tasklist /FO CSV /NH",
            description="List running processes",
            parser=self._parse_processes
        )
        
        # 5. Network - ipconfig (works!)
        self.tools["network_info"] = Tool(
            name="network_info",
            command="ipconfig | findstr /i \"IPv4\"",
            description="Get IP address",
            parser=self._parse_network
        )
        
        # 6. Time - PowerShell
        self.tools["current_time"] = Tool(
            name="current_time",
            command='powershell -Command "Get-Date -Format HH:mm:ss"',
            description="Get current time"
        )
        
        # 7. Date - PowerShell
        self.tools["current_date"] = Tool(
            name="current_date",
            command='powershell -Command "Get-Date -Format yyyy-MM-dd"',
            description="Get current date"
        )
        
        # 8. System Info - systeminfo (works!)
        self.tools["system_info"] = Tool(
            name="system_info",
            command='systeminfo | findstr /B /C:"OS Name" /C:"System Type"',
            description="Get OS info"
        )
        
        # 9. List Files - dir (works!)
        self.tools["list_files"] = Tool(
            name="list_files",
            command="dir \"{path}\" /B 2>nul",
            description="List files"
        )
        
        # 10. Find File - where (works!)
        self.tools["find_file"] = Tool(
            name="find_file",
            command="where /r C:\\Users\\USER-PC {filename} 2>nul",
            description="Find files"
        )
