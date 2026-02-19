"""
IP Camera Discovery Tool

Finds IP cameras on your local network.
Useful for finding cameras when you don't know the IP address.
"""

import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_port(ip, port, timeout=0.5):
    """Check if a port is open on an IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def scan_ip(ip, ports):
    """Scan an IP for common camera ports"""
    open_ports = []
    
    for port in ports:
        if check_port(ip, port):
            open_ports.append(port)
    
    return ip, open_ports

def discover_cameras(network="192.168.1", start=1, end=254):
    """
    Discover IP cameras on network
    
    Args:
        network: Network prefix (e.g., "192.168.1")
        start: Start IP suffix
        end: End IP suffix
    
    Returns:
        List of discovered devices with open camera ports
    """
    # Common camera ports
    camera_ports = [
        554,   # RTSP
        8080,  # HTTP (common)
        8081,  # HTTP (alternate)
        80,    # HTTP
        81,    # HTTP (alternate)
        8554,  # RTSP (alternate)
        5000,  # HTTP
        8888,  # HTTP (Hikvision, etc.)
    ]
    
    print(f"\n[SEARCH] Scanning network {network}.{start}-{end} for IP cameras...")
    print(f"   Checking ports: {camera_ports}")
    print(f"   This may take 1-2 minutes...\n")
    
    discovered = []
    
    # Scan IPs in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        
        for i in range(start, end + 1):
            ip = f"{network}.{i}"
            future = executor.submit(scan_ip, ip, camera_ports)
            futures[future] = ip
        
        completed = 0
        total = end - start + 1
        
        for future in as_completed(futures):
            completed += 1
            ip, open_ports = future.result()
            
            # Progress indicator
            if completed % 10 == 0:
                print(f"   Progress: {completed}/{total} IPs scanned...")
            
            if open_ports:
                device = {
                    'ip': ip,
                    'ports': open_ports,
                    'possible_urls': []
                }
                
                # Load credentials from config
                try:
                    import config as cfg
                    credentials = getattr(cfg, 'VISION_DISCOVERY_CREDENTIALS', [])
                except ImportError:
                    credentials = []
                if not credentials:
                    credentials = [('admin', 'admin'), ('admin', ''), ('admin', '12345'), ('root', 'root')]
                
                # Generate possible URLs from credential pairs
                for port in open_ports:
                    for username, password in credentials:
                        cred = f"{username}:{password}@" if password else f"{username}@"
                        if port == 554 or port == 8554:
                            device['possible_urls'].append(f"rtsp://{cred}{ip}:{port}/stream")
                        else:
                            device['possible_urls'].append(f"http://{cred}{ip}:{port}/video")
                    # Also try without credentials
                    if port == 554 or port == 8554:
                        device['possible_urls'].extend([
                            f"rtsp://{ip}:{port}/",
                            f"rtsp://{ip}:{port}/h264",
                            f"rtsp://{ip}:{port}/live",
                        ])
                    else:
                        device['possible_urls'].extend([
                            f"http://{ip}:{port}/video",
                            f"http://{ip}:{port}/",
                        ])
                
                discovered.append(device)
                
                print(f"\n✓ Found device at {ip}")
                print(f"  Open ports: {open_ports}")
    
    print(f"\n[OK] Scan complete!")
    return discovered

def print_results(discovered):
    """Print discovered cameras in a nice format"""
    if not discovered:
        print("\n[ERROR] No devices found with camera ports open.")
        print("\nTroubleshooting:")
        print("  1. Make sure camera is powered on")
        print("  2. Check camera is connected to same network")
        print("  3. Try different network prefix (e.g., 192.168.0)")
        print("  4. Check camera manual for default port")
        return
    
    print(f"\n📹 Found {len(discovered)} potential camera(s):\n")
    print("=" * 80)
    
    for idx, device in enumerate(discovered, 1):
        print(f"\nDevice #{idx}:")
        print(f"  IP Address: {device['ip']}")
        print(f"  Open Ports: {', '.join(map(str, device['ports']))}")
        print(f"\n  Try these URLs (common credentials):")
        
        for url in device['possible_urls'][:6]:  # Show first 6
            print(f"    - {url}")
        
        if len(device['possible_urls']) > 6:
            print(f"    ... and {len(device['possible_urls']) - 6} more")
        
        print("\n" + "-" * 80)
    
    print("\n[TIP] Tips:")
    print("  - Most cameras use: admin/admin, admin/admin123456, or admin/12345")
    print("  - Try URLs in VLC or web browser to test")
    print("  - Check camera manual for exact URL path")
    print("  - Once you find working URL, add to config.py VISION_IP_CAMERAS")

def generate_config_entry(ip, url, name="nanny_cam"):
    """Generate config entry for found camera"""
    camera_type = 'rtsp' if url.startswith('rtsp') else 'http'
    
    config = f"""
# Add this to config.py VISION_IP_CAMERAS list:
{{
    'name': '{name}',
    'url': '{url}',
    'type': '{camera_type}'
}},
"""
    return config

def main():
    """Main discovery function"""
    print("\n" + "=" * 80)
    print("  IP CAMERA DISCOVERY TOOL")
    print("  Find cameras on your local network")
    print("=" * 80)
    
    # Get network from user
    print("\nWhat is your network prefix?")
    print("  Common options:")
    print("    1. 192.168.1 (most common)")
    print("    2. 192.168.0")
    print("    3. 10.0.0")
    print("    4. Custom")
    
    choice = input("\nChoice (1-4, or press Enter for default): ").strip()
    
    if choice == "2":
        network = "192.168.0"
    elif choice == "3":
        network = "10.0.0"
    elif choice == "4":
        network = input("Enter network prefix (e.g., 192.168.1): ").strip()
    else:
        network = "192.168.1"  # Default
    
    print(f"\nUsing network: {network}.0/24")
    
    # Scan
    discovered = discover_cameras(network)
    
    # Print results
    print_results(discovered)
    
    # Offer to generate config
    if discovered:
        print("\n" + "=" * 80)
        print("Would you like to generate config.py entries?")
        choice = input("(y/n): ").strip().lower()
        
        if choice == 'y':
            print("\n[NOTE] Configuration entries:\n")
            print("# Copy these to config.py VISION_IP_CAMERAS = [...]")
            print("-" * 80)
            
            for idx, device in enumerate(discovered, 1):
                if device['possible_urls']:
                    url = device['possible_urls'][0]  # Use first URL
                    name = input(f"\nName for device #{idx} at {device['ip']} (default: camera_{idx}): ").strip()
                    if not name:
                        name = f"camera_{idx}"
                    
                    config = generate_config_entry(device['ip'], url, name)
                    print(config)
    
    print("\n" + "=" * 80)
    print("Discovery complete!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING]  Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)
