#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpeedNetworkMapper - Ultra Fast Network Discovery Tool
Author: zioerenkl
GitHub: https://github.com/zioerenkl/SpeedNetworkMapper
Description: Lightning fast network discovery using native Linux tools and async Python
"""

import asyncio
import socket
import struct
import subprocess
import threading
import time
import sys
import os
import re
import json
import signal
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime
import ipaddress
import platform

@dataclass
class HostInfo:
    """Host information container"""
    ip: str
    hostname: str = ""
    mac: str = ""
    vendor: str = ""
    os: str = ""
    ports: List[int] = None
    services: Dict[int, str] = None
    response_time: float = 0.0
    last_seen: datetime = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []
        if self.services is None:
            self.services = {}
        if self.last_seen is None:
            self.last_seen = datetime.now()

class SpeedNetworkMapper:
    """Ultra-fast network discovery and mapping tool"""
    
    def __init__(self):
        self.discovered_hosts: Dict[str, HostInfo] = {}
        self.scan_active = False
        self.scan_start_time = None
        self.total_ips_scanned = 0
        self.total_ports_scanned = 0
        
        # Common ports for quick discovery
        self.quick_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1723, 3389, 5900, 8080]
        self.common_ports = list(range(1, 1025))  # Well-known ports
        self.all_ports = list(range(1, 65536))    # All ports
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Performance settings
        self.max_concurrent_hosts = 100
        self.max_concurrent_ports = 50
        self.ping_timeout = 1.0
        self.port_timeout = 0.5
        
        print(self._get_banner())
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.scan_active = False
        self._display_final_stats()
        sys.exit(0)
    
    def _get_banner(self):
        """Get application banner"""
        return """
╔════════════════════════════════════════════════════════════════╗
║              ⚡ SpeedNetworkMapper v1.0                         ║
║           Lightning Fast Network Discovery Tool                ║
╠════════════════════════════════════════════════════════════════╣
║  • Ultra-fast async scanning                                  ║
║  • Native Linux tools integration                             ║
║  • Real-time host discovery                                   ║
║  • Service detection and OS fingerprinting                    ║
║  • Zero external dependencies                                 ║
╚════════════════════════════════════════════════════════════════╝
        """
    
    def _check_requirements(self) -> bool:
        """Check if running on Linux with required tools"""
        if platform.system() != 'Linux':
            print("❌ This tool is optimized for Linux systems")
            return False
        
        required_tools = ['ping', 'nmap', 'arp', 'netstat']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run(['which', tool], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"⚠️  Optional tools not found: {', '.join(missing_tools)}")
            print("   Install with: sudo apt install nmap net-tools")
        
        return True
    
    async def _ping_host(self, ip: str) -> Optional[Tuple[str, float]]:
        """Fast ping using async subprocess"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=2.0)
            
            if proc.returncode == 0:
                # Extract response time
                output = stdout.decode()
                time_match = re.search(r'time=(\d+\.?\d*)', output)
                response_time = float(time_match.group(1)) if time_match else 0.0
                return ip, response_time
            
        except (asyncio.TimeoutError, Exception):
            pass
        
        return None
    
    async def _scan_port(self, ip: str, port: int) -> Optional[Tuple[int, str]]:
        """Fast TCP port scan"""
        try:
            # Create connection with timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.port_timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            # Try to grab banner for service detection
            service = await self._detect_service(ip, port)
            return port, service
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            pass
        
        return None
    
    async def _detect_service(self, ip: str, port: int) -> str:
        """Detect service running on port"""
        service_map = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
            443: "HTTPS", 993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3389: "RDP",
            5900: "VNC", 8080: "HTTP-Alt"
        }
        
        # Quick service mapping
        if port in service_map:
            return service_map[port]
        
        # Try banner grabbing for unknown services
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=1.0
            )
            
            # Send HTTP request for web services
            if port in [80, 8080, 8000, 8443]:
                writer.write(b"GET / HTTP/1.0\r\n\r\n")
                await writer.drain()
            
            # Read banner
            banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
            writer.close()
            
            banner_str = banner.decode('utf-8', errors='ignore').strip()
            if banner_str:
                # Extract service info from banner
                if 'SSH' in banner_str:
                    return f"SSH ({banner_str[:50]})"
                elif 'HTTP' in banner_str:
                    return f"HTTP ({banner_str[:50]})"
                elif 'FTP' in banner_str:
                    return f"FTP ({banner_str[:50]})"
                else:
                    return f"Unknown ({banner_str[:30]})"
            
        except Exception:
            pass
        
        return "Unknown"
    
    def _get_arp_info(self, ip: str) -> Tuple[str, str]:
        """Get MAC address and vendor info from ARP table"""
        try:
            # Check ARP table
            result = subprocess.run(['arp', '-n', ip], 
                                  capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Parse ARP output: IP (MAC) at MAC [ether] on interface
                mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', output)
                if mac_match:
                    mac = mac_match.group(0)
                    vendor = self._get_vendor_from_mac(mac)
                    return mac, vendor
            
        except Exception:
            pass
        
        return "", ""
    
    def _get_vendor_from_mac(self, mac: str) -> str:
        """Get vendor info from MAC address (simplified)"""
        # OUI database lookup (simplified version)
        oui_map = {
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox",
            "52:54:00": "QEMU/KVM",
            "00:0C:29": "VMware",
            "00:1C:42": "Parallels",
            "00:15:5D": "Microsoft Hyper-V",
            "A0:36:9F": "Apple",
            "B8:27:EB": "Raspberry Pi",
            "DC:A6:32": "Raspberry Pi",
        }
        
        oui = mac[:8].upper()
        return oui_map.get(oui, "Unknown")
    
    def _detect_os(self, host_info: HostInfo) -> str:
        """Simple OS detection based on open ports and TTL"""
        open_ports = set(host_info.ports)
        
        # Windows indicators
        if {135, 139, 445} & open_ports:
            if 3389 in open_ports:
                return "Windows (RDP enabled)"
            return "Windows"
        
        # Linux indicators
        if 22 in open_ports:
            if {80, 443} & open_ports:
                return "Linux (Web server)"
            return "Linux/Unix"
        
        # Router/Network device indicators
        if {23, 80, 443} & open_ports and len(open_ports) < 5:
            return "Network Device/Router"
        
        # Mac indicators
        if {548, 631} & open_ports:
            return "macOS"
        
        return "Unknown"
    
    async def _scan_host_ports(self, ip: str, port_list: List[int]) -> HostInfo:
        """Scan all ports for a specific host"""
        host_info = HostInfo(ip=ip)
        
        # Get hostname
        try:
            host_info.hostname = socket.gethostbyaddr(ip)[0]
        except:
            host_info.hostname = ""
        
        # Get MAC and vendor info
        host_info.mac, host_info.vendor = self._get_arp_info(ip)
        
        # Scan ports concurrently
        semaphore = asyncio.Semaphore(self.max_concurrent_ports)
        
        async def scan_with_semaphore(port):
            async with semaphore:
                return await self._scan_port(ip, port)
        
        tasks = [scan_with_semaphore(port) for port in port_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, tuple) and result:
                port, service = result
                host_info.ports.append(port)
                host_info.services[port] = service
                self.total_ports_scanned += 1
        
        # Sort ports
        host_info.ports.sort()
        
        # OS detection
        host_info.os = self._detect_os(host_info)
        
        return host_info
    
    async def _discovery_scan(self, network: str) -> List[str]:
        """Fast host discovery using ping sweep"""
        print(f"🔍 Discovering hosts in {network}...")
        
        try:
            network_obj = ipaddress.IPv4Network(network, strict=False)
            ip_list = [str(ip) for ip in network_obj.hosts()]
        except ValueError:
            print(f"❌ Invalid network format: {network}")
            return []
        
        # Limit IP range for performance
        if len(ip_list) > 1000:
            print(f"⚠️  Large network detected ({len(ip_list)} IPs). Limiting to first 1000.")
            ip_list = ip_list[:1000]
        
        # Concurrent ping sweep
        semaphore = asyncio.Semaphore(self.max_concurrent_hosts)
        
        async def ping_with_semaphore(ip):
            async with semaphore:
                return await self._ping_host(ip)
        
        print(f"⚡ Pinging {len(ip_list)} hosts...")
        tasks = [ping_with_semaphore(ip) for ip in ip_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect alive hosts
        alive_hosts = []
        for result in results:
            if isinstance(result, tuple) and result:
                ip, response_time = result
                alive_hosts.append(ip)
                self.total_ips_scanned += 1
                print(f"✅ {ip} ({response_time:.1f}ms)")
        
        print(f"🎯 Found {len(alive_hosts)} alive hosts")
        return alive_hosts
    
    async def _full_scan(self, hosts: List[str], port_mode: str = 'quick'):
        """Perform full port scan on discovered hosts"""
        if not hosts:
            return
        
        port_lists = {
            'quick': self.quick_ports,
            'common': self.common_ports,
            'all': self.all_ports
        }
        
        port_list = port_lists.get(port_mode, self.quick_ports)
        print(f"🔎 Scanning {len(port_list)} ports on {len(hosts)} hosts...")
        
        # Concurrent host scanning
        semaphore = asyncio.Semaphore(self.max_concurrent_hosts // 2)  # Reduced for port scanning
        
        async def scan_host_with_semaphore(ip):
            async with semaphore:
                return await self._scan_host_ports(ip, port_list)
        
        tasks = [scan_host_with_semaphore(ip) for ip in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Store results
        for result in results:
            if isinstance(result, HostInfo):
                self.discovered_hosts[result.ip] = result
                if result.ports:
                    print(f"🖥️  {result.ip} - {len(result.ports)} open ports - {result.os}")
    
    def _display_results(self):
        """Display scan results in formatted output"""
        if not self.discovered_hosts:
            print("❌ No hosts discovered")
            return
        
        print("\n" + "="*80)
        print("📊 SCAN RESULTS SUMMARY")
        print("="*80)
        
        total_hosts = len(self.discovered_hosts)
        total_open_ports = sum(len(host.ports) for host in self.discovered_hosts.values())
        
        print(f"🎯 Total Hosts Discovered: {total_hosts}")
        print(f"🔓 Total Open Ports Found: {total_open_ports}")
        print(f"⏱️  Scan Duration: {time.time() - self.scan_start_time:.1f} seconds")
        print(f"📡 IPs Scanned: {self.total_ips_scanned}")
        print(f"🔍 Ports Tested: {self.total_ports_scanned}")
        
        print("\n" + "-"*80)
        print("🖥️  DETAILED HOST INFORMATION")
        print("-"*80)
        
        for ip, host in sorted(self.discovered_hosts.items(), key=lambda x: ipaddress.IPv4Address(x[0])):
            print(f"\n🔸 Host: {ip}")
            
            if host.hostname:
                print(f"   Hostname: {host.hostname}")
            
            if host.mac:
                print(f"   MAC: {host.mac}")
                if host.vendor:
                    print(f"   Vendor: {host.vendor}")
            
            if host.os:
                print(f"   OS: {host.os}")
            
            if host.ports:
                print(f"   Open Ports ({len(host.ports)}): {', '.join(map(str, host.ports[:10]))}")
                if len(host.ports) > 10:
                    print(f"   ... and {len(host.ports) - 10} more")
                
                # Show top services
                if host.services:
                    top_services = list(host.services.items())[:5]
                    services_str = ", ".join([f"{port}/{service}" for port, service in top_services])
                    print(f"   Services: {services_str}")
            else:
                print("   Status: Host alive (no open ports in scanned range)")
    
    def _display_final_stats(self):
        """Display final statistics"""
        if self.scan_start_time:
            duration = time.time() - self.scan_start_time
            print(f"\n📈 Final Stats:")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Hosts found: {len(self.discovered_hosts)}")
            print(f"   Average speed: {self.total_ips_scanned / duration:.1f} IPs/sec")
    
    def _export_results(self, format_type: str = 'json'):
        """Export results to file"""
        if not self.discovered_hosts:
            print("❌ No results to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            filename = f"network_scan_{timestamp}.json"
            data = {}
            
            for ip, host in self.discovered_hosts.items():
                data[ip] = {
                    'hostname': host.hostname,
                    'mac': host.mac,
                    'vendor': host.vendor,
                    'os': host.os,
                    'ports': host.ports,
                    'services': host.services,
                    'response_time': host.response_time,
                    'last_seen': host.last_seen.isoformat()
                }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Results exported to {filename}")
        
        elif format_type == 'csv':
            filename = f"network_scan_{timestamp}.csv"
            with open(filename, 'w') as f:
                f.write("IP,Hostname,MAC,Vendor,OS,OpenPorts,Services\n")
                
                for ip, host in self.discovered_hosts.items():
                    ports_str = ';'.join(map(str, host.ports))
                    services_str = ';'.join([f"{p}:{s}" for p, s in host.services.items()])
                    
                    f.write(f"{ip},{host.hostname},{host.mac},{host.vendor},"
                           f"{host.os},{ports_str},{services_str}\n")
            
            print(f"💾 Results exported to {filename}")
    
    async def quick_scan(self, network: str):
        """Quick network scan - discovery + quick port scan"""
        self.scan_active = True
        self.scan_start_time = time.time()
        
        print(f"🚀 Starting quick scan of {network}")
        
        # Host discovery
        alive_hosts = await self._discovery_scan(network)
        
        if alive_hosts:
            # Quick port scan
            await self._full_scan(alive_hosts, 'quick')
        
        self.scan_active = False
        self._display_results()
    
    async def full_scan(self, network: str, port_mode: str = 'common'):
        """Full network scan - discovery + comprehensive port scan"""
        self.scan_active = True
        self.scan_start_time = time.time()
        
        print(f"🚀 Starting full scan of {network} (ports: {port_mode})")
        
        # Host discovery
        alive_hosts = await self._discovery_scan(network)
        
        if alive_hosts:
            # Full port scan
            await self._full_scan(alive_hosts, port_mode)
        
        self.scan_active = False
        self._display_results()
    
    async def stealth_scan(self, network: str):
        """Stealth scan with reduced speed for evasion"""
        print("🥷 Stealth mode - slower scan for evasion")
        
        # Reduce concurrency for stealth
        original_hosts = self.max_concurrent_hosts
        original_ports = self.max_concurrent_ports
        
        self.max_concurrent_hosts = 10
        self.max_concurrent_ports = 5
        self.ping_timeout = 2.0
        self.port_timeout = 1.0
        
        try:
            await self.quick_scan(network)
        finally:
            # Restore original settings
            self.max_concurrent_hosts = original_hosts
            self.max_concurrent_ports = original_ports
            self.ping_timeout = 1.0
            self.port_timeout = 0.5

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("""
🚀 SpeedNetworkMapper Usage:

Basic Commands:
  python3 speed_mapper.py quick <network>     # Quick scan (common ports)
  python3 speed_mapper.py full <network>      # Full scan (1-1024 ports)  
  python3 speed_mapper.py stealth <network>   # Stealth scan (slower)
  python3 speed_mapper.py all <network>       # All ports scan (1-65535)

Examples:
  python3 speed_mapper.py quick 192.168.1.0/24
  python3 speed_mapper.py full 10.0.0.0/16
  python3 speed_mapper.py stealth 172.16.0.0/12

Options:
  --export json    Export results to JSON
  --export csv     Export results to CSV
  --help          Show this help
        """)
        return
    
    scanner = SpeedNetworkMapper()
    
    if not scanner._check_requirements():
        return
    
    command = sys.argv[1].lower()
    
    if command == '--help' or command == '-h':
        main()
        return
    
    if len(sys.argv) < 3:
        print("❌ Network parameter required")
        return
    
    network = sys.argv[2]
    export_format = None
    
    # Check for export option
    if '--export' in sys.argv:
        try:
            export_idx = sys.argv.index('--export')
            export_format = sys.argv[export_idx + 1]
        except (IndexError, ValueError):
            export_format = 'json'
    
    try:
        if command == 'quick':
            asyncio.run(scanner.quick_scan(network))
        elif command == 'full':
            asyncio.run(scanner.full_scan(network, 'common'))
        elif command == 'all':
            asyncio.run(scanner.full_scan(network, 'all'))
        elif command == 'stealth':
            asyncio.run(scanner.stealth_scan(network))
        else:
            print(f"❌ Unknown command: {command}")
            return
        
        # Export results if requested
        if export_format:
            scanner._export_results(export_format)
            
    except KeyboardInterrupt:
        print("\n🛑 Scan interrupted by user")
    except Exception as e:
        print(f"❌ Error during scan: {e}")

if __name__ == "__main__":
    main()
