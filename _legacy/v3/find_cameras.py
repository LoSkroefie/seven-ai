"""
IP Camera Discovery Tool

This script scans your local network to find IP cameras.
Use this to discover your nanny cam's IP address.

Usage:
    python find_cameras.py
"""

import socket
import sys
import cv2
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_port(ip, port, timeout=0.5):
    """Check if a port is open on an IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_rtsp_url(url, timeout=5):
    """Test if an RTSP URL works"""
    try:
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_TIMEOUT, timeout * 1000)
        
        if not cap.isOpened():
            cap.release()
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        return ret
    except:
        return False

def scan_ip(ip, common_ports, credentials):
    """Scan a single IP for cameras"""
    results = []
    
    for port in common_ports:
        if check_port(ip, port):
            print(f"  Found open port: {ip}:{port}")
            
            # Try common RTSP/HTTP URLs
            for username, password in credentials:
                # RTSP URLs
                rtsp_urls = [
                    f"rtsp://{username}:{password}@{ip}:{port}/stream",
                    f"rtsp://{username}:{password}@{ip}:{port}/",
                    f"rtsp://{username}:{password}@{ip}:{port}/h264",
                    f"rtsp://{username}:{password}@{ip}:{port}/live",
                    f"rtsp://{username}:{password}@{ip}:{port}/cam/realmonitor",
                ]
                
                for url in rtsp_urls:
                    print(f"    Testing: {url}")
                    if test_rtsp_url(url):
                        results.append({
                            'ip': ip,
                            'port': port,
                            'url': url,
                            'username': username,
                            'password': password,
                            'type': 'rtsp',
                            'status': 'WORKING ✓'
                        })
                        print(f"      ✓ WORKING!")
                        return results  # Found a working URL, stop trying
    
    return results

def discover_cameras(network='192.168.1', start=1, end=254):
    """
    Discover IP cameras on local network
    
    Args:
        network: Network prefix (e.g., '192.168.1')
        start: Start of IP range (default: 1)
        end: End of IP range (default: 254)
    """
    print("=" * 60)
    print("IP CAMERA DISCOVERY TOOL")
    print("=" * 60)
    print()
    print(f"Scanning network: {network}.{start}-{end}")
    print()
    
    # Common camera ports
    common_ports = [
        554,   # RTSP
        8080,  # HTTP alternative
        8081,  # HTTP alternative
        80,    # HTTP
        81,    # HTTP alternative
        8554,  # RTSP alternative
    ]
    
    # Load credentials from config (or use defaults)
    try:
        import config as cfg
        credentials = getattr(cfg, 'VISION_DISCOVERY_CREDENTIALS', [])
    except ImportError:
        credentials = []
    if not credentials:
        credentials = [
            ('admin', 'admin'),
            ('admin', ''),
            ('admin', '12345'),
            ('root', 'root'),
            ('user', 'user'),
        ]
    
    print(f"Checking ports: {common_ports}")
    print(f"Testing {len(credentials)} credential combinations")
    print()
    print("This may take a few minutes...")
    print()
    
    discovered = []
    
    # Scan IPs in parallel for speed
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        
        for i in range(start, end + 1):
            ip = f"{network}.{i}"
            future = executor.submit(scan_ip, ip, common_ports, credentials)
            futures[future] = ip
        
        for future in as_completed(futures):
            ip = futures[future]
            try:
                results = future.result()
                if results:
                    discovered.extend(results)
            except Exception as e:
                print(f"Error scanning {ip}: {e}")
    
    print()
    print("=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print()
    
    if discovered:
        print(f"✓ Found {len(discovered)} camera(s)!")
        print()
        
        for i, cam in enumerate(discovered, 1):
            print(f"Camera #{i}:")
            print(f"  IP: {cam['ip']}")
            print(f"  Port: {cam['port']}")
            print(f"  Username: {cam['username']}")
            print(f"  Password: {cam['password']}")
            print(f"  Type: {cam['type'].upper()}")
            print(f"  URL: {cam['url']}")
            print(f"  Status: {cam['status']}")
            print()
        
        print("=" * 60)
        print("ADD TO config.py:")
        print("=" * 60)
        print()
        print("VISION_IP_CAMERAS = [")
        for i, cam in enumerate(discovered, 1):
            cam_name = f"camera_{i}"
            if 'nanny' in cam['url'].lower() or cam['username'] == 'admin' and cam['password'] == 'admin123456':
                cam_name = 'nanny_cam'
            
            print(f"    {{")
            print(f"        'name': '{cam_name}',")
            print(f"        'url': '{cam['url']}',")
            print(f"        'type': '{cam['type']}'")
            print(f"    }},")
        print("]")
        print()
        
    else:
        print("✗ No cameras found")
        print()
        print("Troubleshooting:")
        print("  1. Make sure camera is powered on")
        print("  2. Make sure camera is on same network")
        print("  3. Check if camera uses different credentials")
        print("  4. Check if camera uses non-standard ports")
        print("  5. Try accessing camera web interface first")
        print()
    
    return discovered

if __name__ == "__main__":
    print()
    print("Scanning local network for IP cameras...")
    print()
    
    # Get network from user
    network = input("Enter network prefix (default: 192.168.1): ").strip()
    if not network:
        network = '192.168.1'
    
    print()
    
    # Discover cameras
    cameras = discover_cameras(network)
    
    print()
    input("Press Enter to exit...")
