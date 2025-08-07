#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpeedNetworkMapper Installer
Author: zioerenkl
GitHub: https://github.com/zioerenkl/SpeedNetworkMapper
Description: Professional installer for SpeedNetworkMapper with global command setup
"""

import os
import sys
import subprocess
import shutil
import stat
from pathlib import Path

class SNMInstaller:
    """Professional installer for SpeedNetworkMapper"""
    
    def __init__(self):
        self.script_name = "speed_network_mapper.py"
        self.command_name = "snm"
        self.install_dir = Path("/opt/speednetworkmapper")
        self.bin_path = Path("/usr/local/bin") / self.command_name
        self.completion_script = Path("/etc/bash_completion.d/snm")
        
    def print_banner(self):
        """Display installer banner"""
        banner = """
╔════════════════════════════════════════════════════════════════╗
║              ⚡ SpeedNetworkMapper Installer                    ║
║           Ultra-Fast Network Discovery Tool Setup             ║
╠════════════════════════════════════════════════════════════════╣
║  • Global command installation (snm)                          ║
║  • System requirements checking                               ║
║  • Bash completion setup                                      ║
║  • Performance optimization                                   ║
╚════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_prerequisites(self):
        """Check system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check if running on Linux
        if sys.platform != 'linux':
            print("❌ SpeedNetworkMapper is optimized for Linux systems")
            return False
        
        # Check if running as root/sudo
        if os.geteuid() != 0:
            print("❌ This installer must be run with sudo privileges")
            print("   Usage: sudo python3 installer.py")
            return False
        
        # Check Python version
        if sys.version_info < (3.7):
            print("❌ Python 3.7 or higher is required")
            print(f"   Current version: {sys.version}")
            return False
        
        print(f"✅ Linux system detected")
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        print(f"✅ Running with sufficient privileges")
        
        return True
    
    def check_system_tools(self):
        """Check and install required system tools"""
        print("🔧 Checking system tools...")
        
        required_tools = ['ping', 'arp', 'netstat']
        optional_tools = ['nmap', 'dig', 'whois']
        
        missing_required = []
        missing_optional = []
        
        # Check required tools
        for tool in required_tools:
            try:
                subprocess.run(['which', tool], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ {tool} found")
            except subprocess.CalledProcessError:
                missing_required.append(tool)
                print(f"❌ {tool} missing (required)")
        
        # Check optional tools
        for tool in optional_tools:
            try:
                subprocess.run(['which', tool], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ {tool} found (optional)")
            except subprocess.CalledProcessError:
                missing_optional.append(tool)
                print(f"⚠️  {tool} missing (optional)")
        
        # Install missing tools
        if missing_required or missing_optional:
            missing_all = missing_required + missing_optional
            print(f"📦 Installing missing tools: {', '.join(missing_all)}")
            
            try:
                # Update package list
                subprocess.run(['apt', 'update'], check=True, 
                             stdout=subprocess.DEVNULL)
                
                # Install net-tools (contains arp, netstat)
                if any(tool in missing_all for tool in ['arp', 'netstat']):
                    subprocess.run(['apt', 'install', '-y', 'net-tools'], 
                                 check=True)
                
                # Install iputils-ping
                if 'ping' in missing_all:
                    subprocess.run(['apt', 'install', '-y', 'iputils-ping'], 
                                 check=True)
                
                # Install optional tools
                if 'nmap' in missing_optional:
                    subprocess.run(['apt', 'install', '-y', 'nmap'], 
                                 check=True)
                
                if any(tool in missing_optional for tool in ['dig', 'whois']):
                    subprocess.run(['apt', 'install', '-y', 'dnsutils', 'whois'], 
                                 check=True)
                
                print("✅ System tools installed successfully")
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Could not install some tools: {e}")
                if missing_required:
                    print("❌ Required tools missing - installation may not work properly")
                    return False
        
        return True
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        print("🐍 Installing Python dependencies...")
        
        requirements_file = Path("requirements.txt")
        
        if not requirements_file.exists():
            print("⚠️  requirements.txt not found, installing basic dependencies...")
            # Install minimal dependencies manually
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 
                    'colorama', 'tqdm', 'psutil', '--upgrade'
                ], check=True, stdout=subprocess.DEVNULL)
                print("✅ Basic dependencies installed")
            except subprocess.CalledProcessError:
                print("⚠️  Could not install optional dependencies (will work without them)")
            return True
        
        try:
            # Install from requirements.txt
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                '-r', str(requirements_file), '--upgrade'
            ], check=True, stdout=subprocess.DEVNULL)
            print("✅ Python dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not install some Python dependencies: {e}")
            print("   SpeedNetworkMapper will work with reduced functionality")
            return True  # Continue anyway
    
    def create_installation_directory(self):
        """Create installation directory"""
        print(f"📁 Creating installation directory...")
        
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.install_dir.chmod(0o755)
            print(f"✅ Directory created: {self.install_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return False
    
    def install_main_script(self):
        """Install the main script"""
        print("📄 Installing SpeedNetworkMapper script...")
        
        source_script = Path(self.script_name)
        if not source_script.exists():
            print(f"❌ Source script '{self.script_name}' not found")
            print("   Make sure you're in the SpeedNetworkMapper directory")
            return False
        
        try:
            dest_script = self.install_dir / self.script_name
            shutil.copy2(source_script, dest_script)
            dest_script.chmod(0o755)
            print(f"✅ Script installed: {dest_script}")
            return True
        except Exception as e:
            print(f"❌ Failed to install script: {e}")
            return False
    
    def create_command_wrapper(self):
        """Create global command wrapper"""
        print(f"🔗 Creating global command: {self.command_name}")
        
        wrapper_content = f'''#!/bin/bash
# SpeedNetworkMapper Global Command Wrapper
# Usage: snm [options]

SCRIPT_DIR="{self.install_dir}"
PYTHON_SCRIPT="$SCRIPT_DIR/{self.script_name}"

# Check if script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: SpeedNetworkMapper not found at $PYTHON_SCRIPT"
    echo "   Try reinstalling: sudo python3 installer.py"
    exit 1
fi

# Check if running as root for certain operations
if [ "$EUID" -ne 0 ] && [[ "$1" != "quick" ]] && [[ "$1" != "--help" ]] && [[ "$1" != "-h" ]]; then
    echo "⚠️  Some network operations may require root privileges"
    echo "   For full functionality, try: sudo snm $@"
fi

# Execute the Python script
exec python3 "$PYTHON_SCRIPT" "$@"
'''
        
        try:
            with open(self.bin_path, 'w') as f:
                f.write(wrapper_content)
            
            self.bin_path.chmod(0o755)
            print(f"✅ Global command created: {self.bin_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create command: {e}")
            return False
    
    def setup_bash_completion(self):
        """Setup bash completion for snm command"""
        print("⚡ Setting up bash completion...")
        
        completion_content = '''# SpeedNetworkMapper bash completion
_snm_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    if [[ ${COMP_CWORD} == 1 ]]; then
        opts="quick full all stealth --help -h"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    # Options for export
    if [[ ${prev} == "--export" ]]; then
        opts="json csv"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    # Network suggestions (common private ranges)
    if [[ ${COMP_CWORD} == 2 ]]; then
        local networks="192.168.1.0/24 192.168.0.0/24 10.0.0.0/16 172.16.0.0/12"
        COMPREPLY=( $(compgen -W "${networks}" -- ${cur}) )
        return 0
    fi

    # General options
    opts="--export --help"
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

complete -F _snm_completion snm
'''
        
        try:
            with open(self.completion_script, 'w') as f:
                f.write(completion_content)
            
            self.completion_script.chmod(0o644)
            print(f"✅ Bash completion installed")
            print("   Restart your terminal or run: source /etc/bash_completion.d/snm")
        except Exception as e:
            print(f"⚠️  Could not install bash completion: {e}")
        
        return True
    
    def optimize_performance(self):
        """Apply performance optimizations"""
        print("🚀 Applying performance optimizations...")
        
        optimizations = []
        
        # Check if we can increase file descriptor limits
        try:
            import resource
            current_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
            if current_limit < 65536:
                optimizations.append(f"Consider increasing file descriptor limit: ulimit -n 65536")
        except:
            pass
        
        # Check available memory
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb < 4:
                        optimizations.append(f"Low memory detected ({mem_gb:.1f}GB) - consider reducing concurrent scans")
                    break
        except:
            pass
        
        # Check if we can optimize network stack
        sysctl_optimizations = [
            "net.core.rmem_max=134217728",
            "net.core.wmem_max=134217728", 
            "net.ipv4.tcp_rmem=4096 65536 134217728",
            "net.ipv4.tcp_wmem=4096 65536 134217728"
        ]
        
        print("✅ Performance analysis completed")
        
        if optimizations:
            print("💡 Performance recommendations:")
            for opt in optimizations:
                print(f"   • {opt}")
        
        print("💡 For maximum performance, consider:")
        print("   • Run with root privileges: sudo snm")
        print("   • Increase file descriptors: ulimit -n 65536")
        print("   • Use SSD storage for better I/O")
        
        return True
    
    def test_installation(self):
        """Test the installation"""
        print("🧪 Testing installation...")
        
        try:
            # Test command availability
            result = subprocess.run([str(self.bin_path), '--help'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'SpeedNetworkMapper' in result.stdout:
                print("✅ Installation test passed")
                return True
            else:
                print("⚠️  Installation test had issues")
                print(f"   Return code: {result.returncode}")
                print(f"   Output: {result.stdout[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Installation test timed out")
            return False
        except Exception as e:
            print(f"⚠️  Could not test installation: {e}")
            return False
    
    def display_completion_message(self):
        """Display installation completion message"""
        print("\n" + "="*70)
        print("🎉 SpeedNetworkMapper Installation Complete!")
        print("="*70)
        
        print(f"\n🚀 Quick Start Commands:")
        print(f"   snm --help                    # Show help")
        print(f"   snm quick 192.168.1.0/24      # Quick network scan")
        print(f"   sudo snm full 10.0.0.0/16     # Full network scan")
        print(f"   snm stealth 172.16.0.0/12     # Stealth scan")
        
        print(f"\n📁 Installation Details:")
        print(f"   • Command: {self.bin_path}")
        print(f"   • Scripts: {self.install_dir}")
        print(f"   • Completion: {self.completion_script}")
        
        print(f"\n⚡ Performance Tips:")
        print(f"   • Use 'sudo' for maximum performance")
        print(f"   • Start with 'snm quick' for local network")
        print(f"   • Export results: snm quick 192.168.1.0/24 --export json")
        
        print(f"\n🔧 Advanced Usage:")
        print(f"   • All ports: snm all 192.168.1.100/32")
        print(f"   • Stealth mode: snm stealth 10.0.0.0/24")
        print(f"   • Large networks: sudo snm full 10.0.0.0/8")
        
        print(f"\n🗑️  To Uninstall:")
        print(f"   sudo python3 installer.py uninstall")
        
        print("\n✨ Happy Network Mapping!")
    
    def install(self):
        """Main installation process"""
        self.print_banner()
        
        if not self.check_prerequisites():
            return False
        
        if not self.check_system_tools():
            return False
        
        if not self.install_python_dependencies():
            return False
        
        if not self.create_installation_directory():
            return False
        
        if not self.install_main_script():
            return False
        
        if not self.create_command_wrapper():
            return False
        
        self.setup_bash_completion()
        self.optimize_performance()
        
        if self.test_installation():
            self.display_completion_message()
            return True
        else:
            print("⚠️  Installation completed with warnings")
            return True
    
    def uninstall(self):
        """Uninstall SpeedNetworkMapper"""
        print("🗑️  Uninstalling SpeedNetworkMapper...")
        
        try:
            # Remove command
            if self.bin_path.exists():
                self.bin_path.unlink()
                print(f"✅ Removed: {self.bin_path}")
            
            # Remove installation directory
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                print(f"✅ Removed: {self.install_dir}")
            
            # Remove bash completion
            if self.completion_script.exists():
                self.completion_script.unlink()
                print(f"✅ Removed: {self.completion_script}")
            
            print("✅ SpeedNetworkMapper uninstalled successfully")
            print("💡 You may want to restart your terminal to clear bash completion")
            return True
            
        except Exception as e:
            print(f"❌ Error during uninstallation: {e}")
            return False

def main():
    """Main installer entry point"""
    installer = SNMInstaller()
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
SpeedNetworkMapper Installer

Usage:
  sudo python3 installer.py [option]

Options:
  install     Install SpeedNetworkMapper (default)
  uninstall   Remove SpeedNetworkMapper
  -h, --help  Show this help message

Installation Features:
  • Global 'snm' command installation
  • System tools verification and installation
  • Python dependencies management
  • Bash completion setup
  • Performance optimization
  • Installation testing

Requirements:
  • Linux operating system
  • Python 3.7 or higher
  • Root/sudo privileges for installation
  • Internet connection for package installation

After installation, use:
  snm --help              # Show SpeedNetworkMapper help
  snm quick 192.168.1.0/24  # Quick network scan
            """)
            return
        
        elif sys.argv[1] == 'uninstall':
            if os.geteuid() != 0:
                print("❌ Uninstall requires sudo privileges")
                print("   Usage: sudo python3 installer.py uninstall")
                sys.exit(1)
            
            if installer.uninstall():
                print("\n👋 SpeedNetworkMapper has been uninstalled!")
            else:
                print("\n❌ Uninstallation failed!")
                sys.exit(1)
            return
    
    # Default action: install
    if os.geteuid() != 0:
        print("❌ Installation requires sudo privileges")
        print("   Usage: sudo python3 installer.py")
        sys.exit(1)
    
    try:
        if installer.install():
            print(f"\n🎊 Ready to go! Try: snm --help")
        else:
            print("\n❌ Installation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Installation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
