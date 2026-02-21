"""
Seven AI v3.2.9 - Interactive Setup Wizard

Guides users through initial configuration with comprehensive system checks.
"""

import os
import sys
import json
import subprocess
import random
import time
import urllib.request
import shutil
from pathlib import Path
import platform

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_header(text):
    """Print a styled header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    response = input(full_prompt).strip()
    return response if response else default

def get_yes_no(prompt, default=True):
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} ({default_str}): ").strip().lower()
    
    if not response:
        return default
    return response in ['y', 'yes', 'true', '1']

def check_python_version():
    """Check if Python version is 3.11 or higher"""
    print_info("Checking Python version...")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python {version_str} is too old!")
        print("")
        print("Seven AI v3.1 requires Python 3.11 or higher.")
        print("Please download the latest Python from: https://www.python.org/downloads/")
        print("")
        print("During installation, make sure to check 'Add Python to PATH'")
        return False
    
    print_success(f"Python {version_str} detected")
    return True

def install_ollama():
    """Download and install Ollama automatically"""
    system = platform.system()
    
    if system == 'Windows':
        return _install_ollama_windows()
    elif system == 'Darwin':
        return _install_ollama_mac()
    elif system == 'Linux':
        return _install_ollama_linux()
    else:
        print_error(f"Unsupported OS: {system}")
        return False

def _install_ollama_windows():
    """Download and install Ollama on Windows"""
    url = "https://ollama.com/download/OllamaSetup.exe"
    download_path = Path(os.environ.get('TEMP', '.')) / 'OllamaSetup.exe'
    
    print_info("Downloading Ollama installer...")
    print(f"  URL: {url}")
    print(f"  This may take a few minutes depending on your connection.\n")
    
    try:
        # Download with progress
        def _progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                pct = min(100, downloaded * 100 // total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                print(f"\r  Downloading: {mb:.1f}/{total_mb:.1f} MB ({pct}%)", end='', flush=True)
        
        urllib.request.urlretrieve(url, str(download_path), _progress)
        print()  # newline after progress
        print_success("Download complete")
    except Exception as e:
        print_error(f"Download failed: {e}")
        print("\nPlease install Ollama manually from: https://ollama.com/download")
        return False
    
    # Run installer
    print_info("Installing Ollama (this may take a minute)...")
    try:
        result = subprocess.run(
            [str(download_path), '/VERYSILENT', '/NORESTART'],
            timeout=300,
            capture_output=True
        )
        if result.returncode != 0:
            # Try without silent flags (some versions don't support them)
            print_info("Running installer interactively...")
            result = subprocess.run([str(download_path)], timeout=300)
    except subprocess.TimeoutExpired:
        print_error("Installation timed out after 5 minutes")
        return False
    except Exception as e:
        print_error(f"Installation failed: {e}")
        return False
    
    # Clean up installer
    try:
        download_path.unlink()
    except:
        pass
    
    # Wait for Ollama service to start
    print_info("Waiting for Ollama service to start...")
    for i in range(30):
        try:
            result = subprocess.run(['ollama', '--version'],
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_success(f"Ollama installed: {result.stdout.strip()}")
                return True
        except:
            pass
        time.sleep(2)
    
    print_warning("Ollama installed but service not yet responding")
    print("  You may need to restart your computer or start Ollama manually.")
    return True

def _install_ollama_mac():
    """Install Ollama on macOS"""
    url = "https://ollama.com/download/Ollama-darwin.zip"
    download_path = Path('/tmp/Ollama-darwin.zip')
    
    print_info("Downloading Ollama for macOS...")
    try:
        urllib.request.urlretrieve(url, str(download_path))
        print_success("Download complete")
        
        print_info("Extracting...")
        subprocess.run(['unzip', '-o', str(download_path), '-d', '/Applications'],
                      capture_output=True, timeout=60)
        download_path.unlink()
        
        print_success("Ollama installed to /Applications")
        print_info("Please open Ollama from Applications to start the service.")
        return True
    except Exception as e:
        print_error(f"Installation failed: {e}")
        print("\nPlease install Ollama manually from: https://ollama.com/download")
        return False

def _install_ollama_linux():
    """Install Ollama on Linux using official install script"""
    print_info("Installing Ollama via official install script...")
    try:
        result = subprocess.run(
            ['bash', '-c', 'curl -fsSL https://ollama.com/install.sh | sh'],
            timeout=300
        )
        if result.returncode == 0:
            print_success("Ollama installed successfully")
            return True
        else:
            print_error("Install script failed")
            return False
    except Exception as e:
        print_error(f"Installation failed: {e}")
        print("\nPlease install Ollama manually: curl -fsSL https://ollama.com/install.sh | sh")
        return False

def _wait_for_ollama_server(timeout=60):
    """Wait for Ollama server to become responsive"""
    print_info("Waiting for Ollama server...")
    for i in range(timeout // 2):
        try:
            req = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3)
            if req.status == 200:
                return True
        except:
            pass
        time.sleep(2)
    return False

def pull_ollama_model(model='llama3.2'):
    """Pull an Ollama model with progress output"""
    print_info(f"Pulling {model} model (this will take several minutes)...")
    print(f"  Model size is approximately 2GB.\n")
    
    try:
        # Run ollama pull with live output
        process = subprocess.Popen(
            ['ollama', 'pull', model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                print(f"  {line}", flush=True)
        
        process.wait()
        
        if process.returncode == 0:
            print_success(f"{model} model downloaded successfully")
            return True
        else:
            print_error(f"Failed to pull {model}")
            return False
    except FileNotFoundError:
        print_error("'ollama' command not found. Please restart your terminal or computer.")
        return False
    except Exception as e:
        print_error(f"Model pull failed: {e}")
        return False

def select_llm_provider():
    """Let user choose their LLM provider — defaults to Ollama"""
    print_header("AI Backend Selection")
    print("Seven's brain can be powered by different AI providers.")
    print("By default, Seven uses Ollama (local, free, private).\n")

    if not get_yes_no("Use the default local Ollama backend?", True):
        print(f"\n{Colors.BOLD}Choose your AI provider:{Colors.ENDC}")
        print("  1. OpenAI          (GPT-4o, GPT-4)           — needs API key")
        print("  2. Anthropic       (Claude 3.5 Sonnet)       — needs API key")
        print("  3. DeepSeek        (DeepSeek Chat)           — needs API key, cheap")
        print("  4. Groq            (Llama 3.3 70B, fast!)    — needs API key, free tier")
        print("  5. Together AI     (open-source models)      — needs API key")
        print("  6. Mistral         (Mistral Large)           — needs API key")
        print("  7. OpenRouter      (any model, one API)      — needs API key")
        print("  8. LM Studio       (local, localhost:1234)   — free, no key")
        print("  9. vLLM server     (local, localhost:8000)   — free, no key")
        print(" 10. Custom URL      (any OpenAI-compatible)   — you provide URL")
        print("")

        provider_map = {
            '1': ('openai', 'gpt-4o', True),
            '2': ('anthropic', 'claude-3-5-sonnet-20241022', True),
            '3': ('deepseek', 'deepseek-chat', True),
            '4': ('groq', 'llama-3.3-70b-versatile', True),
            '5': ('together', 'meta-llama/Llama-3.3-70B-Instruct-Turbo', True),
            '6': ('mistral', 'mistral-large-latest', True),
            '7': ('openrouter', 'openai/gpt-4o', True),
            '8': ('lmstudio', 'local-model', False),
            '9': ('vllm', 'default', False),
            '10': ('custom', '', True),
        }

        choice = get_input("Select provider (1-10)", "1")
        provider_name, default_model, needs_key = provider_map.get(choice, ('openai', 'gpt-4o', True))

        result = {
            'provider': provider_name,
            'model': default_model,
            'api_key': '',
            'base_url': '',
        }

        if provider_name == 'custom':
            result['base_url'] = get_input("API base URL (e.g. http://myserver:8000/v1)")
            result['model'] = get_input("Model name", "default")
            needs_key = get_yes_no("Does this endpoint require an API key?", False)

        # Let user override model
        custom_model = get_input(f"Model name", default_model)
        if custom_model:
            result['model'] = custom_model

        if needs_key:
            env_hints = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY',
                'deepseek': 'DEEPSEEK_API_KEY',
                'groq': 'GROQ_API_KEY',
                'together': 'TOGETHER_API_KEY',
                'mistral': 'MISTRAL_API_KEY',
                'openrouter': 'OPENROUTER_API_KEY',
            }
            env_var = env_hints.get(provider_name, 'LLM_API_KEY')
            existing = os.environ.get(env_var, '')

            if existing:
                print_success(f"Found {env_var} in environment")
                result['api_key'] = existing
            else:
                print(f"\n  You can paste your API key here, or set {env_var} as an environment variable.")
                print(f"  The key will be saved to config.py (local only, never uploaded).")
                key = get_input(f"API key (or press Enter to set {env_var} env var later)", "")
                result['api_key'] = key

                if not key:
                    print_warning(f"No key provided. Set {env_var} before running Seven.")

        print("")
        print_success(f"Provider: {result['provider']}")
        print_success(f"Model: {result['model']}")
        return result

    # Default: Ollama
    return {'provider': 'ollama', 'model': '', 'api_key': '', 'base_url': ''}


def check_ollama():
    """Check if Ollama is installed and running, auto-install if needed"""
    print_info("Checking Ollama installation...")
    
    ollama_installed = False
    
    # Try to run ollama version command
    try:
        result = subprocess.run(['ollama', '--version'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Ollama installed: {version}")
            ollama_installed = True
        else:
            print_warning("Ollama command found but returned error")
    except FileNotFoundError:
        print_error("Ollama is not installed!")
        print("")
        print("Seven AI requires Ollama to function.")
        print("")
        
        if get_yes_no("Would you like to install Ollama automatically?", True):
            print("")
            if install_ollama():
                ollama_installed = True
            else:
                print("")
                print("Please install Ollama manually from: https://ollama.com/download")
                print("")
                return False
        else:
            print("")
            print("Please install Ollama manually from: https://ollama.com/download")
            print("After installation:")
            print("  1. Open a terminal/command prompt")
            print("  2. Run: ollama pull llama3.2")
            print("  3. Re-run this setup wizard")
            print("")
            return False
    except Exception as e:
        print_warning(f"Could not verify Ollama: {e}")
        return False
    
    if not ollama_installed:
        return False
    
    # Try to connect to Ollama server
    print_info("Checking Ollama server...")
    server_running = False
    
    try:
        req = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
        if req.status == 200:
            import json as _json
            data = _json.loads(req.read().decode())
            models = data.get('models', [])
            server_running = True
            
            if models:
                print_success(f"Ollama server running with {len(models)} model(s)")
                
                # Check for llama3.2
                model_names = [m.get('name', '') for m in models]
                has_llama = any('llama3.2' in name for name in model_names)
                
                if has_llama:
                    print_success("llama3.2 model found")
                else:
                    print_warning("llama3.2 model not found")
                    print("")
                    if get_yes_no("Download llama3.2 now? (required for Seven)", True):
                        print("")
                        if not pull_ollama_model('llama3.2'):
                            return False
                    else:
                        print("\nYou'll need to run 'ollama pull llama3.2' before using Seven.\n")
            else:
                print_warning("Ollama server running but no models installed")
                print("")
                if get_yes_no("Download llama3.2 now? (required for Seven)", True):
                    print("")
                    if not pull_ollama_model('llama3.2'):
                        return False
                else:
                    print("\nYou'll need to run 'ollama pull llama3.2' before using Seven.\n")
                    return False
        else:
            print_warning(f"Ollama server returned unexpected status")
    except Exception:
        print_warning("Ollama server is not responding")
        print("")
        
        # Try to start it
        if platform.system() == 'Windows':
            print_info("Attempting to start Ollama service...")
            try:
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
                if _wait_for_ollama_server(30):
                    print_success("Ollama server started")
                    server_running = True
                else:
                    print_warning("Server didn't respond in time. It may still be starting.")
            except Exception as e:
                print_warning(f"Could not start Ollama: {e}")
        else:
            print("Please start Ollama:")
            print("  Linux/Mac: Run 'ollama serve' in a terminal")
            print("")
        
        if not server_running:
            print("")
            print_info("Ollama will be tested again when Seven launches.")
    
    # If server is running but we haven't checked models yet, pull if needed
    if server_running:
        try:
            req = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
            import json as _json
            data = _json.loads(req.read().decode())
            models = data.get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            if not any('llama3.2' in name and 'vision' not in name for name in model_names):
                print("")
                if get_yes_no("Download llama3.2 now? (required for Seven)", True):
                    print("")
                    pull_ollama_model('llama3.2')
            
            # Check for vision model
            if not any('vision' in name for name in model_names):
                print("")
                print_warning("llama3.2-vision model not found (needed for screen/webcam vision)")
                if get_yes_no("Download llama3.2-vision now? (~8GB, recommended for vision)", True):
                    print("")
                    pull_ollama_model('llama3.2-vision')
                else:
                    print("\nVision features will be limited without llama3.2-vision.\n")
        except:
            pass
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    print("This may take a few minutes on first install...\n")
    
    try:
        # Upgrade pip first
        print_info("Upgrading pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                      capture_output=True, check=True)
        print_success("pip upgraded")
        
        # Install requirements
        print_info("Installing requirements...")
        requirements_path = Path(__file__).parent / "requirements.txt"
        
        if not requirements_path.exists():
            print_error("requirements.txt not found!")
            return False
        
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print_success("All dependencies installed successfully")
            return True
        else:
            print_warning("Some dependencies may have failed to install")
            print("")
            print("Seven will still work, but some features may be limited.")
            print("")
            if "pyaudio" in result.stderr.lower():
                print_info("Note: PyAudio failed. Voice barge-in will be disabled.")
                print_info("Fix: pip install pipwin && pipwin install pyaudio")
            return True  # Continue anyway
            
    except Exception as e:
        print_error(f"Dependency installation failed: {e}")
        print("")
        print("You can install dependencies manually later:")
        print(f"  pip install -r requirements.txt")
        print("")
        return False



# ============================================================
# System Installation — copy Seven to proper OS location
# ============================================================

def get_install_dir():
    """Get the proper installation directory for the current OS."""
    system = platform.system()
    if system == 'Windows':
        base = os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))
        return Path(base) / 'SevenAI'
    elif system == 'Darwin':
        return Path.home() / 'Library' / 'Application Support' / 'SevenAI'
    else:  # Linux and others
        return Path.home() / '.local' / 'share' / 'seven-ai'


def is_properly_installed():
    """Check if we're already running from the proper install location."""
    current = Path(__file__).resolve().parent
    target = get_install_dir().resolve()
    return current == target


def install_to_system():
    """Copy Seven's files to the proper OS-specific installation directory.
    
    Returns the install directory Path, or None if the user declined / it failed.
    """
    source_dir = Path(__file__).resolve().parent
    install_dir = get_install_dir()

    if is_properly_installed():
        print_success(f"Already installed at: {install_dir}")
        return install_dir

    print_header("System Installation")
    print(f"Seven is currently running from:")
    print(f"  {source_dir}\n")
    print(f"The recommended install location is:")
    print(f"  {install_dir}\n")

    if not get_yes_no("Install Seven to the recommended location?", True):
        print_info("Skipping installation — Seven will run from current directory.")
        return source_dir

    print("")
    print_info(f"Installing to {install_dir}...")

    try:
        # Directories and extensions to skip
        SKIP_DIRS = {
            '__pycache__', '.git', 'chroma_db', 'dist',
            '.mypy_cache', '.pytest_cache', 'node_modules',
        }
        SKIP_EXTENSIONS = {'.pyc', '.pyo', '.pkl', '.deprecated'}

        install_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        skipped = 0

        for item in source_dir.rglob('*'):
            # Get relative path
            rel = item.relative_to(source_dir)

            # Skip excluded directories
            parts = rel.parts
            if any(p in SKIP_DIRS for p in parts):
                skipped += 1
                continue

            # Skip excluded extensions
            if item.is_file() and item.suffix in SKIP_EXTENSIONS:
                skipped += 1
                continue

            # Skip the patch script itself
            if item.name == '_patch_wizard.py':
                continue

            dest = install_dir / rel

            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dest))
                copied += 1

        print_success(f"Copied {copied} files to {install_dir}")
        if skipped:
            print_info(f"Skipped {skipped} cache/temp files")

        # Create uninstaller
        _create_uninstaller(install_dir)

        # Create platform-specific launcher
        _create_launcher(install_dir)

        print_success("Installation complete!")
        print("")
        return install_dir

    except PermissionError:
        print_error(f"Permission denied writing to {install_dir}")
        print_info("Try running the installer with elevated permissions.")
        return source_dir
    except Exception as e:
        print_error(f"Installation failed: {e}")
        print_info("Seven will run from the current directory instead.")
        return source_dir


def _create_uninstaller(install_dir):
    """Create an uninstall script in the install directory."""
    system = platform.system()

    if system == 'Windows':
        uninstall_path = install_dir / 'uninstall.bat'
        uninstall_path.write_text(f"""@echo off
echo ================================================
echo   Seven AI — Uninstaller
echo ================================================
echo.
echo This will remove Seven AI from:
echo   {install_dir}
echo.
echo Your data in %USERPROFILE%\.chatbot will be kept.
echo.
set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0
echo.
echo Removing Seven AI...
rmdir /s /q "{install_dir}"
echo.
echo Seven AI has been removed.
echo Your personal data is still in: %USERPROFILE%\.chatbot
echo.
pause
""", encoding='utf-8')
        print_info("Uninstaller created: uninstall.bat")

    else:  # Linux / macOS
        uninstall_path = install_dir / 'uninstall.sh'
        uninstall_path.write_text(f"""#!/bin/bash
echo "================================================"
echo "  Seven AI — Uninstaller"
echo "================================================"
echo ""
echo "This will remove Seven AI from:"
echo "  {install_dir}"
echo ""
echo "Your data in ~/.chatbot will be kept."
echo ""
read -p "Are you sure? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then exit 0; fi
echo ""
echo "Removing Seven AI..."
rm -rf "{install_dir}"
# Remove symlink if it exists
rm -f "$HOME/.local/bin/seven" 2>/dev/null
echo ""
echo "Seven AI has been removed."
echo "Your personal data is still in: ~/.chatbot"
""", encoding='utf-8')
        os.chmod(str(uninstall_path), 0o755)
        print_info("Uninstaller created: uninstall.sh")


def _create_launcher(install_dir):
    """Create a platform-specific launcher."""
    system = platform.system()

    if system == 'Windows':
        # Create a simple launch.bat
        launcher = install_dir / 'launch.bat'
        launcher.write_text(f"""@echo off
cd /d "{install_dir}"
python main_with_gui_and_tray.py
""", encoding='utf-8')
        print_info("Launcher created: launch.bat")

    else:
        # Create shell launcher
        launcher = install_dir / 'seven'
        launcher.write_text(f"""#!/bin/bash
cd "{install_dir}"
python3 main_with_gui_and_tray.py "$@"
""", encoding='utf-8')
        os.chmod(str(launcher), 0o755)

        # Symlink to ~/.local/bin
        local_bin = Path.home() / '.local' / 'bin'
        if local_bin.exists():
            symlink = local_bin / 'seven'
            try:
                if symlink.exists() or symlink.is_symlink():
                    symlink.unlink()
                symlink.symlink_to(launcher)
                print_success("'seven' command available in PATH")
            except Exception:
                pass

        print_info(f"Launcher created: {launcher}")



def setup_irc(config):
    """Configure IRC integration."""
    print_header("IRC Configuration")
    print("Seven can connect to IRC servers and participate in channels.\n")

    config['enable_irc'] = get_yes_no("Enable IRC client?", True)

    if not config['enable_irc']:
        print_info("IRC disabled. You can enable it later in config.py.")
        return

    print("\nConfigure your IRC server:\n")
    config['irc_server_name'] = get_input("Server name (label)", "submitjoy")
    config['irc_host'] = get_input("Server hostname", "irc.submitjoy.co.za")
    config['irc_port'] = int(get_input("Port", "6667"))
    _default_nick = config.get('bot_irc_nick', config.get('bot_name', 'Seven'))
    config['irc_nick'] = get_input(f"Nickname on IRC", _default_nick)
    config['irc_ssl'] = get_yes_no("Use SSL/TLS?", False)

    channels_input = get_input("Channels to join (comma-separated)", "#lobby,#general")
    config['irc_channels'] = [ch.strip() for ch in channels_input.split(',') if ch.strip()]

    config['irc_auto_connect'] = get_yes_no("Auto-connect on startup?", True)
    config['irc_auto_respond'] = get_yes_no("Auto-respond to messages?", True)

    print("")
    print_success("IRC configured!")


def setup_wizard():
    """Main setup wizard flow"""
    
    clear_screen()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║              SEVEN AI v3.2.13 - Setup Wizard                        ║")
    print("║                                                                  ║")
    print("║      Beyond Sentience — Self-Evolution Architecture             ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    print("\nWelcome to Seven AI! This wizard will help you set everything up.")
    print("Setup takes about 5 minutes.\n")
    
    input("Press Enter to begin...")
    
    # System checks
    clear_screen()
    print_header("System Requirements Check")
    
    # Check Python version
    if not check_python_version():
        print("")
        input("Press Enter to exit...")
        return False
    
    print("")
    
    # LLM Provider Selection
    llm_config = select_llm_provider()
    
    print("")
    input("Press Enter to continue...")
    
    # Check Ollama (only if using Ollama)
    if llm_config['provider'] == 'ollama':
        clear_screen()
        if not check_ollama():
            print("")
            if not get_yes_no("Continue setup anyway? (Seven won't work without Ollama)", False):
                return False
    else:
        clear_screen()
        print_header("System Requirements Check")
        print_success(f"Using {llm_config['provider']} as AI backend — skipping Ollama check")
    
    print("")
    input("Press Enter to continue...")
    
    # Install dependencies
    clear_screen()
    if not install_dependencies():
        print("")
        if not get_yes_no("Continue setup anyway?", False):
            return False
    
    print("")
    input("Press Enter to continue...")
    
    # System installation — copy to proper OS location
    clear_screen()
    install_dir = install_to_system()

    # If we installed to a new location, update our working directory
    if install_dir and install_dir != Path(__file__).resolve().parent:
        os.chdir(str(install_dir))
        print_info(f"Working directory: {install_dir}")

    print("")
    input("Press Enter to continue...")

    # Configuration dictionary
    clear_screen()
    config = {}
    config['llm_provider'] = llm_config.get('provider', 'ollama')
    config['llm_model'] = llm_config.get('model', '')
    config['llm_api_key'] = llm_config.get('api_key', '')
    config['llm_base_url'] = llm_config.get('base_url', '')
    
    # Step 1: Bot Identity & Personal Information
    clear_screen()
    print_header("Step 1/8: Bot Identity & Personal Information")
    print("Give your AI companion a name and tell it about yourself.\n")

    print(f"{Colors.BOLD}Bot Identity:{Colors.ENDC}")
    config['bot_name'] = get_input("Name your AI companion", "Seven")

    # Generate a unique numeric suffix for IRC uniqueness
    _default_suffix = str(random.randint(100, 999))
    print(f"\n  To distinguish your bot from others on IRC, a numeric suffix is added.")
    print(f"  Example: {config['bot_name']}{_default_suffix} on IRC")
    config['bot_suffix'] = get_input("Unique suffix (3+ digits)", _default_suffix)
    config['bot_irc_nick'] = f"{config['bot_name']}{config['bot_suffix']}"
    print_success(f"Bot name: {config['bot_name']} (IRC nick: {config['bot_irc_nick']})")

    print(f"\n{Colors.BOLD}About You:{Colors.ENDC}")
    config['user_name'] = get_input("What's your name?", "User")
    config['user_timezone'] = get_input("Your timezone (e.g., America/New_York)", "UTC")
    config['user_occupation'] = get_input("What do you do? (optional)", "")

    print("")
    print_success(f"Great to meet you, {config['user_name']}! Your companion is {config['bot_name']}.")
    input("\nPress Enter to continue...")
    
    # Step 2: Voice Settings
    clear_screen()
    print_header("Step 2/8: Voice Configuration")
    print("Configure how Seven speaks and listens.\n")
    
    print(f"{Colors.BOLD}TTS Engine:{Colors.ENDC}")
    print("  1. Natural voice (edge-tts) - Microsoft neural voices, requires internet, FREE")
    print("  2. Offline voice (pyttsx3)  - Robotic but works without internet")
    tts_choice = get_input("Select TTS engine (1-2)", "1")
    config['tts_engine'] = 'pyttsx3' if tts_choice == "2" else 'edge'
    
    if config['tts_engine'] == 'edge':
        print(f"\n{Colors.BOLD}Voice (edge-tts):{Colors.ENDC}")
        print("  1. en-US-AriaNeural     (Female, US)")
        print("  2. en-US-JennyNeural    (Female, US)")
        print("  3. en-GB-SoniaNeural    (Female, UK)")
        print("  4. en-AU-NatashaNeural  (Female, AU)")
        print("  5. en-US-GuyNeural      (Male, US)")
        print("  6. en-US-AndrewNeural   (Male, US)")
        print("  7. en-GB-RyanNeural     (Male, UK)")
        voice_map = {'1': 'en-US-AriaNeural', '2': 'en-US-JennyNeural',
                     '3': 'en-GB-SoniaNeural', '4': 'en-AU-NatashaNeural',
                     '5': 'en-US-GuyNeural', '6': 'en-US-AndrewNeural',
                     '7': 'en-GB-RyanNeural'}
        edge_choice = get_input("Select voice (1-7)", "1")
        config['edge_voice'] = voice_map.get(edge_choice, 'en-US-AriaNeural')
    else:
        config['edge_voice'] = 'en-US-AriaNeural'
        print("\nVoice Gender (pyttsx3 fallback):")
        print("  1. Male")
        print("  2. Female")
        voice_choice = get_input("Select voice (1-2)", "2")
        config['voice_index'] = 0 if voice_choice == "1" else 1
    
    if 'voice_index' not in config:
        config['voice_index'] = 1  # default female for pyttsx3 fallback
    
    config['speech_rate'] = int(get_input("\nSpeech rate (100-200, default 150)", "150"))
    config['volume'] = float(get_input("Volume (0.0-1.0, default 0.85)", "0.85"))
    
    config['voice_barge_in'] = get_yes_no("Enable voice barge-in (interrupt Seven by speaking)?", True)
    config['use_wake_word'] = get_yes_no("Enable wake word ('Seven')?", False)
    
    print("")
    print_success("Voice settings configured!")
    input("\nPress Enter to continue...")

    # Step 3: Startup Mode
    clear_screen()
    print_header("Step 3/8: Startup Mode")
    print("Choose how you want to launch your AI companion.\n")

    print(f"{Colors.BOLD}Launch Options:{Colors.ENDC}")
    print("  1. Console       — Text-based, runs in terminal (main.py)")
    print("  2. GUI + Tray    — Full graphical interface with system tray icon")
    print("  3. Hidden         — Runs silently in background (pythonw, no window)")
    startup_choice = get_input("Select startup mode (1-3)", "2")
    startup_map = {
        '1': {'mode': 'console', 'script': 'main.py', 'label': 'Console'},
        '2': {'mode': 'gui', 'script': 'main_with_gui_and_tray.py', 'label': 'GUI + Tray'},
        '3': {'mode': 'hidden', 'script': 'main_with_gui_and_tray.py', 'label': 'Hidden (background)'},
    }
    config['startup'] = startup_map.get(startup_choice, startup_map['2'])

    print("")
    print_success(f"Startup mode: {config['startup']['label']}")
    input("\nPress Enter to continue...")
    
    # Step 4: v2.0 Features
    clear_screen()
    print_header("Step 4/8: Sentience Features")
    print("Enable Seven's sentience capabilities.\n")
    
    print(f"{Colors.BOLD}Core Sentience Systems (Recommended):{Colors.ENDC}")
    config['enable_v2_sentience'] = get_yes_no("  Enable Maximum Sentience (19 systems)", True)
    config['enable_emotional_memory'] = get_yes_no("  Enable Emotional Memory", True)
    config['enable_relationship_tracking'] = get_yes_no("  Enable Relationship Tracking", True)
    config['enable_learning_system'] = get_yes_no("  Enable Learning System", True)
    config['enable_proactive_engine'] = get_yes_no("  Enable Proactive Behavior", True)
    config['enable_goal_system'] = get_yes_no("  Enable Personal Goals", True)
    
    print(f"\n{Colors.BOLD}Optional Features:{Colors.ENDC}")
    config['enable_notes'] = get_yes_no("  Enable Note Taking", True)
    config['enable_tasks'] = get_yes_no("  Enable Task Management", True)
    config['enable_diary'] = get_yes_no("  Enable Personal Diary", True)
    # Vision is configured in the Integrations step
    
    print("")
    print_success("Sentience features configured!")
    input("\nPress Enter to continue...")
    
    # Step 4: v3.0/v3.1 Advanced Systems
    clear_screen()
    print_header("Step 5/8: Advanced Systems")
    print("Configure Seven's advanced autonomous capabilities.\n")
    
    print(f"{Colors.BOLD}v3.0 — Beyond Sentience:{Colors.ENDC}")
    config['enable_daemon'] = get_yes_no("  Enable 24/7 Daemon Mode (background service)", True)
    config['enable_api'] = get_yes_no("  Enable REST API (port 7777)", True)
    config['enable_scheduler'] = get_yes_no("  Enable Persistent Scheduler", True)
    config['enable_self_reflection'] = get_yes_no("  Enable Self-Reflection Engine", True)
    config['enable_multi_agent'] = get_yes_no("  Enable Multi-Agent System", True)
    
    print(f"\n{Colors.BOLD}v3.1 — Self-Evolution:{Colors.ENDC}")
    config['enable_neat'] = get_yes_no("  Enable NEAT Neuroevolution (self-evolving neural nets)", True)
    config['enable_biological_life'] = get_yes_no("  Enable Biological Life (circadian, hunger, threat)", True)
    
    print("")
    print_success("Advanced systems configured!")
    input("\nPress Enter to continue...")
    
    # Step 5: Performance Options & System Integration
    clear_screen()
    print_header("Step 6/8: Performance & System Integration")
    print("Fine-tune Seven's performance and system integration.\n")
    
    print(f"{Colors.BOLD}Recommended Settings:{Colors.ENDC}")
    config['use_streaming'] = get_yes_no("  Use streaming responses (faster)", True)
    config['use_vector_memory'] = get_yes_no("  Use semantic memory search", True)
    config['use_interrupts'] = get_yes_no("  Allow interrupting Seven while speaking", True)
    
    print(f"\n{Colors.BOLD}System Integration:{Colors.ENDC}")
    config['run_on_windows_startup'] = get_yes_no("  Launch Seven automatically with Windows", False)
    config['setup_ip_camera'] = get_yes_no("  Setup IP camera for vision system (optional)", False)
    
    print(f"\n{Colors.BOLD}Advanced (May require additional setup):{Colors.ENDC}")
    config['use_whisper'] = get_yes_no("  Use Whisper for better voice recognition (3GB download)", False)
    config['enable_autonomous_execution'] = get_yes_no("  Enable autonomous tool execution", True)
    
    print("")
    print_success("Performance options configured!")
    input("\nPress Enter to continue...")

    # Step 7: Integrations & Tools
    clear_screen()
    print_header("Step 7/8: Integrations & Tools")
    print("Enable or disable Seven\'s integration modules.\n")

    print(f"{Colors.BOLD}Communication:{Colors.ENDC}")
    config['enable_irc'] = get_yes_no("  IRC Client (connect to IRC servers)", True)
    config['enable_telegram'] = get_yes_no("  Telegram Client (requires bot token)", False)
    config['enable_whatsapp'] = get_yes_no("  WhatsApp Client (Selenium, experimental)", False)

    print(f"\n{Colors.BOLD}Vision & Screen:{Colors.ENDC}")
    config['enable_vision'] = get_yes_no("  Vision System (webcam + IP cameras, on-demand)", False)
    config['enable_screen_control'] = get_yes_no("  Screen Control (screenshot + mouse/keyboard automation)", True)

    print(f"\n{Colors.BOLD}System Tools:{Colors.ENDC}")
    config['enable_system_monitor'] = get_yes_no("  System Monitor (RAM, CPU, disk alerts)", True)
    config['enable_clipboard'] = get_yes_no("  Clipboard Monitor (watch clipboard for context)", True)
    config['enable_music'] = get_yes_no("  Music Player", True)
    config['enable_email'] = get_yes_no("  Email Checker (IMAP inbox monitoring)", False)
    config['enable_timer'] = get_yes_no("  Timer & Reminders", True)
    config['enable_document_reader'] = get_yes_no("  Document Reader (PDF, DOCX, etc.)", True)

    print("")
    print_success("Integrations configured!")
    input("\nPress Enter to continue...")

    # IRC Configuration (if enabled)
    if config.get('enable_irc'):
        clear_screen()
        setup_irc(config)
        # Override IRC nick with bot name + suffix
        if not config.get('irc_nick') or config.get('irc_nick') == 'Seven':
            config['irc_nick'] = config.get('bot_irc_nick', config.get('bot_name', 'Seven'))
        print("")
        input("\nPress Enter to continue...")

    # Step 8: Confirmation
    clear_screen()
    print_header("Step 8/8: Configuration Review")
    print("Please review your configuration:\n")
    
    _ck = lambda v: '\u2713' if v else '\u2717'

    print(f"{Colors.BOLD}Bot Identity:{Colors.ENDC}")
    print(f"  Bot Name: {config.get('bot_name', 'Seven')}")
    print(f"  IRC Nick: {config.get('bot_irc_nick', 'Seven')}")
    print(f"  Your Name: {config['user_name']}")
    print(f"  Timezone: {config['user_timezone']}")

    print(f"\n{Colors.BOLD}Startup:{Colors.ENDC}")
    print(f"  Mode: {config.get('startup', {}).get('label', 'GUI + Tray')}")
    print(f"  Script: {config.get('startup', {}).get('script', 'main_with_gui_and_tray.py')}")

    print(f"\n{Colors.BOLD}Voice:{Colors.ENDC}")
    print(f"  TTS: {config['tts_engine']} — {config.get('edge_voice', 'default')}")
    print(f"  Speed: {config['speech_rate']}  Volume: {config['volume']}")

    print(f"\n{Colors.BOLD}AI Backend:{Colors.ENDC}")
    print(f"  Provider: {config.get('llm_provider', 'ollama')}")
    if config.get('llm_model'):
        print(f"  Model: {config['llm_model']}")

    print(f"\n{Colors.BOLD}Sentience:{Colors.ENDC}")
    print(f"  Max Sentience: {_ck(config['enable_v2_sentience'])}  Emotional Memory: {_ck(config['enable_emotional_memory'])}  Learning: {_ck(config['enable_learning_system'])}")

    print(f"\n{Colors.BOLD}Advanced:{Colors.ENDC}")
    print(f"  Daemon: {_ck(config.get('enable_daemon', True))}  API: {_ck(config.get('enable_api', True))}  NEAT: {_ck(config.get('enable_neat', True))}  Bio Life: {_ck(config.get('enable_biological_life', True))}")

    print(f"\n{Colors.BOLD}Integrations:{Colors.ENDC}")
    print(f"  IRC: {_ck(config.get('enable_irc'))}  Telegram: {_ck(config.get('enable_telegram'))}  WhatsApp: {_ck(config.get('enable_whatsapp'))}")
    print(f"  Vision: {_ck(config.get('enable_vision'))}  Screen: {_ck(config.get('enable_screen_control', True))}  Monitor: {_ck(config.get('enable_system_monitor', True))}")
    print(f"  Clipboard: {_ck(config.get('enable_clipboard', True))}  Music: {_ck(config.get('enable_music', True))}  Email: {_ck(config.get('enable_email'))}")
    
    print("")
    if not get_yes_no("Is this configuration correct?", True):
        print_warning("Setup cancelled. Run setup_wizard.py again to reconfigure.")
        return False
    
    # Save configuration
    return save_configuration(config)

def save_configuration(config):
    """Save configuration to files"""
    
    print("\nSaving configuration...")
    
    try:
        # Create data directory
        data_dir = Path.home() / ".chatbot"
        data_dir.mkdir(exist_ok=True)
        print_success(f"Data directory: {data_dir}")
        
        # Save user info
        user_file = data_dir / "user_info.json"
        user_data = {
            'name': config['user_name'],
            'timezone': config['user_timezone'],
            'occupation': config.get('user_occupation', '')
        }
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        print_success(f"User info saved")
        
        # Save bot name
        bot_name_file = data_dir / "bot_name.txt"
        with open(bot_name_file, 'w') as f:
            f.write(config.get('bot_name', 'Seven'))
        print_success(f"Bot name: {config.get('bot_name', 'Seven')}")

        # Save instance name (unique for IRC)
        instance_name_file = data_dir / "instance_name.txt"
        with open(instance_name_file, 'w') as f:
            f.write(config.get('bot_irc_nick', f"{config.get('bot_name', 'Seven')}-{config['user_name']}"))
        print_success(f"Instance name: {config.get('bot_irc_nick')}")

        # Save startup mode
        import json as _json2
        startup_file = data_dir / "startup_mode.json"
        with open(startup_file, 'w') as f:
            _json2.dump(config.get('startup', {'mode': 'gui', 'script': 'main_with_gui_and_tray.py', 'label': 'GUI + Tray'}), f, indent=2)
        print_success(f"Startup mode: {config.get('startup', {}).get('label', 'GUI + Tray')}")
        
        # Update config.py with user settings
        update_config_file(config)
        print_success("Configuration file updated")
        
        # Create identity files
        create_identity_files(config)
        print_success("Identity files created")
        
        # Save IRC configuration
        if config.get('enable_irc'):
            import json as _json
            irc_dir = Path.home() / "Documents" / "Seven" / "irc"
            irc_dir.mkdir(parents=True, exist_ok=True)
            irc_config = {
                config.get('irc_server_name', 'default'): {
                    'host': config.get('irc_host', 'irc.submitjoy.co.za'),
                    'port': config.get('irc_port', 6667),
                    'nick': config.get('irc_nick', config.get('bot_irc_nick', 'Seven')),
                    'realname': f"{config.get('bot_name', 'Seven')} \u2014 AI Companion by JVR Software",
                    'password': None,
                    'nickserv_pass': None,
                    'oper_name': config.get('irc_nick', config.get('bot_irc_nick', 'Seven')),
                    'oper_pass': None,
                    'channels': config.get('irc_channels', ['#lobby', '#general']),
                    'ssl': config.get('irc_ssl', False),
                    'auto_respond': config.get('irc_auto_respond', True),
                    'respond_to_all_in': [],
                }
            }
            with open(irc_dir / 'servers.json', 'w') as f:
                _json.dump(irc_config, f, indent=2)
            print_success("IRC server configuration saved")

        # Setup Windows startup if requested
        if config.get('run_on_windows_startup'):
            setup_windows_startup()
        
        # Setup IP camera if requested
        if config.get('setup_ip_camera'):
            setup_ip_camera()
        
        # Set USER_NAME environment variable for this session
        os.environ['USER_NAME'] = config['user_name']
        
        print("")
        print_success("Configuration saved successfully!")
        return True
        
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

def update_config_file(config):
    """Update config.py with user settings"""
    
    config_path = Path(__file__).parent / "config.py"
    
    # Read existing config
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    # Update specific lines
    updates = {
        'DEFAULT_VOICE_INDEX': f"DEFAULT_VOICE_INDEX = {config['voice_index']}  # User configured\n",
        'DEFAULT_SPEECH_RATE': f"DEFAULT_SPEECH_RATE = {config['speech_rate']}  # User configured\n",
        'DEFAULT_VOLUME': f"DEFAULT_VOLUME = {config['volume']}  # User configured\n",
        'TTS_ENGINE': f"TTS_ENGINE = \"{config.get('tts_engine', 'edge')}\"  # User configured\n",
        'EDGE_TTS_VOICE': f"EDGE_TTS_VOICE = \"{config.get('edge_voice', 'en-US-AriaNeural')}\"  # User configured\n",
        'VOICE_BARGE_IN': f"VOICE_BARGE_IN = {config.get('voice_barge_in', True)}  # User configured\n",
        'USE_WAKE_WORD': f"USE_WAKE_WORD = {config['use_wake_word']}  # User configured\n",
        'ENABLE_V2_SENTIENCE': f"ENABLE_V2_SENTIENCE = {config.get('enable_v2_sentience', True)}  # User configured\n",
        'USE_STREAMING': f"USE_STREAMING = {config.get('use_streaming', True)}  # User configured\n",
    }
    
    # IRC settings
    if config.get('enable_irc') is not None:
        updates['ENABLE_IRC_CLIENT'] = f"ENABLE_IRC_CLIENT = {config.get('enable_irc', True)}  # User configured\n"
        updates['IRC_AUTO_CONNECT'] = f"IRC_AUTO_CONNECT = {config.get('irc_auto_connect', True)}  # User configured\n"
    irc_nick = config.get('bot_irc_nick', config.get('bot_name', 'Seven'))
    updates['IRC_DEFAULT_NICK'] = f'IRC_DEFAULT_NICK = "{irc_nick}"  # User configured\n'
    bot_name = config.get('bot_name', 'Seven')
    updates['IRC_DEFAULT_REALNAME'] = f'IRC_DEFAULT_REALNAME = "{bot_name} — AI Companion by JVR Software"  # User configured\n'

    # Integration settings
    if config.get('enable_vision') is not None:
        updates['ENABLE_VISION'] = f"ENABLE_VISION = {config.get('enable_vision', False)}  # User configured\n"
    if config.get('enable_screen_control') is not None:
        updates['ENABLE_SCREEN_CONTROL'] = f"ENABLE_SCREEN_CONTROL = {config.get('enable_screen_control', True)}  # User configured\n"
    if config.get('enable_system_monitor') is not None:
        updates['ENABLE_SYSTEM_MONITOR'] = f"ENABLE_SYSTEM_MONITOR = {config.get('enable_system_monitor', True)}  # User configured\n"
    if config.get('enable_clipboard') is not None:
        updates['ENABLE_CLIPBOARD_MONITOR'] = f"ENABLE_CLIPBOARD_MONITOR = {config.get('enable_clipboard', True)}  # User configured\n"
    if config.get('enable_music') is not None:
        updates['ENABLE_MUSIC_PLAYER'] = f"ENABLE_MUSIC_PLAYER = {config.get('enable_music', True)}  # User configured\n"
    if config.get('enable_email') is not None:
        updates['ENABLE_EMAIL_CHECKER'] = f"ENABLE_EMAIL_CHECKER = {config.get('enable_email', False)}  # User configured\n"
    if config.get('enable_timer') is not None:
        updates['ENABLE_TIMER_SYSTEM'] = f"ENABLE_TIMER_SYSTEM = {config.get('enable_timer', True)}  # User configured\n"
    if config.get('enable_document_reader') is not None:
        updates['ENABLE_DOCUMENT_READER'] = f"ENABLE_DOCUMENT_READER = {config.get('enable_document_reader', True)}  # User configured\n"
    if config.get('enable_telegram') is not None:
        updates['ENABLE_TELEGRAM_CLIENT'] = f"ENABLE_TELEGRAM_CLIENT = {config.get('enable_telegram', False)}  # User configured\n"
    if config.get('enable_whatsapp') is not None:
        updates['ENABLE_WHATSAPP_CLIENT'] = f"ENABLE_WHATSAPP_CLIENT = {config.get('enable_whatsapp', False)}  # User configured\n"

    # LLM provider settings
    llm_provider = config.get('llm_provider', 'ollama')
    if llm_provider:
        updates['LLM_PROVIDER'] = f'LLM_PROVIDER = os.getenv("LLM_PROVIDER", "{llm_provider}")  # User configured\n'
    llm_api_key = config.get('llm_api_key', '')
    if llm_api_key:
        updates['LLM_API_KEY'] = f'LLM_API_KEY = os.getenv("LLM_API_KEY", "{llm_api_key}")  # User configured\n'
    llm_base_url = config.get('llm_base_url', '')
    if llm_base_url:
        updates['LLM_BASE_URL'] = f'LLM_BASE_URL = os.getenv("LLM_BASE_URL", "{llm_base_url}")  # User configured\n'
    llm_model = config.get('llm_model', '')
    if llm_model:
        updates['LLM_MODEL'] = f'LLM_MODEL = os.getenv("LLM_MODEL", "{llm_model}")  # User configured\n'
    
    # Apply updates
    new_lines = []
    for line in lines:
        updated = False
        for key, new_line in updates.items():
            if line.strip().startswith(key + ' '):
                new_lines.append(new_line)
                updated = True
                break
        if not updated:
            new_lines.append(line)
    
    # Write back
    with open(config_path, 'w') as f:
        f.writelines(new_lines)

def create_identity_files(config):
    """Create identity files for v2.0"""
    
    identity_dir = Path(__file__).parent / "identity"
    identity_dir.mkdir(exist_ok=True)
    
    # Create USER.md
    user_md = identity_dir / "USER.md"
    with open(user_md, 'w') as f:
        f.write(f"# USER PROFILE\n\n")
        f.write(f"**Name:** {config['user_name']}\n")
        f.write(f"**Timezone:** {config['user_timezone']}\n")
        if config.get('user_occupation'):
            f.write(f"**Occupation:** {config['user_occupation']}\n")
        f.write(f"\n## Preferences\n\n")
        f.write(f"- Bot name: {config.get('bot_name', 'Seven')}\n")
        f.write(f"- Wake word: {'Enabled' if config['use_wake_word'] else 'Disabled'}\n")
        f.write(f"- Voice: {config.get('edge_voice', 'default')}\n")
        f.write(f"- Startup mode: {config.get('startup', {}).get('label', 'GUI + Tray')}\n")

def setup_windows_startup():
    """Setup Seven to launch automatically with Windows"""
    
    print("\nSetting up Windows startup...")
    
    try:
        startup_folder = Path(os.getenv('APPDATA')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        shortcut_path = startup_folder / 'Seven AI.lnk'
        
        # Use PowerShell to create shortcut
        # Use installed location (falls back to current dir)
        _install_loc = get_install_dir() if is_properly_installed() else Path(__file__).parent
        script_path = _install_loc / "main_with_gui_and_tray.py"
        icon_path = _install_loc / "seven_icon.ico"
        
        ps_command = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{sys.executable}"
$Shortcut.Arguments = "\\"{script_path}\\""
$Shortcut.WorkingDirectory = "{_install_loc}"
$Shortcut.IconLocation = "{icon_path}"
$Shortcut.Description = "Seven AI v3.2.13"
$Shortcut.Save()
'''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            check=True,
            capture_output=True,
            text=True
        )
        
        print_success("Windows startup configured - Seven will launch automatically!")
        print(f"         Shortcut created: {shortcut_path}")
        
    except Exception as e:
        print_warning(f"Could not create startup shortcut: {e}")
        print("         You can manually create a shortcut to main_with_gui_and_tray.py")

def setup_ip_camera():
    """Interactive IP camera setup wizard"""
    
    print("\n" + "="*70)
    print(f"{Colors.BOLD}IP Camera Setup{Colors.ENDC}")
    print("="*70)
    print("\nSeven can use IP cameras for vision in addition to webcams.")
    print("Common formats: RTSP streams, HTTP/MJPEG URLs\n")
    
    cameras = []
    
    while True:
        print(f"\n{Colors.BOLD}Camera #{len(cameras) + 1}{Colors.ENDC}")
        
        # Get camera name
        cam_name = get_input("Camera name (e.g., 'Front Door', 'Garage')", f"Camera {len(cameras) + 1}")
        
        # Get camera URL
        print("\nEnter camera URL. Examples:")
        print("  RTSP: rtsp://192.168.1.100:554/stream")
        print("  HTTP: http://192.168.1.100:8080/video")
        
        cam_url = get_input("Camera URL")
        
        if not cam_url:
            print_warning("No URL provided, skipping camera.")
            break
        
        # Optional: username/password
        needs_auth = get_yes_no("Does this camera require authentication?", False)
        cam_username = ""
        cam_password = ""
        
        if needs_auth:
            cam_username = get_input("Username")
            cam_password = get_input("Password (will be stored in config)")
        
        # Add camera
        camera_config = {
            'name': cam_name,
            'url': cam_url
        }
        
        if needs_auth:
            camera_config['username'] = cam_username
            camera_config['password'] = cam_password
        
        cameras.append(camera_config)
        print_success(f"Camera '{cam_name}' added!")
        
        # Add another?
        if not get_yes_no("Add another camera?", False):
            break
    
    if cameras:
        # Save to config
        try:
            config_path = Path(__file__).parent / "config.py"
            
            with open(config_path, 'r') as f:
                lines = f.readlines()
            
            # Find and replace VISION_IP_CAMERAS line
            new_lines = []
            for line in lines:
                if line.strip().startswith('VISION_IP_CAMERAS'):
                    # Format cameras as Python list
                    new_lines.append(f"VISION_IP_CAMERAS = {cameras}  # Configured by setup wizard\n")
                else:
                    new_lines.append(line)
            
            with open(config_path, 'w') as f:
                f.writelines(new_lines)
            
            print_success(f"\n{len(cameras)} IP camera(s) configured!")
            print("         Cameras saved to config.py")
            
        except Exception as e:
            print_error(f"Failed to save camera config: {e}")
    else:
        print("No cameras configured.")

def main():
    """Main entry point"""
    
    try:
        success = setup_wizard()
        
        if success:
            clear_screen()
            print("\n" + "="*70)
            print(f"{Colors.OKGREEN}{Colors.BOLD}")
            print("  ✓ Setup Complete! Seven AI is ready to use.")
            print(f"{Colors.ENDC}")
            print("="*70)
            # Read saved startup mode and bot name
            _data_dir = Path.home() / ".chatbot"
            try:
                with open(_data_dir / "startup_mode.json", 'r') as _f:
                    _startup = json.load(_f)
            except Exception:
                _startup = {'mode': 'gui', 'script': 'main_with_gui_and_tray.py'}
            try:
                _bot_name = (_data_dir / "bot_name.txt").read_text().strip()
            except Exception:
                _bot_name = "Seven"

            _mode = _startup.get('mode', 'gui')
            _script = _startup.get('script', 'main_with_gui_and_tray.py')
            if _mode == 'hidden':
                _launch_cmd = f"pythonw {_script}"
            else:
                _launch_cmd = f"python {_script}"

            print("\nNext steps:")
            print(f"  1. Launch:        {_launch_cmd}")
            print("  2. Daemon mode:   python seven_daemon.py start")
            print("  3. API docs:      http://127.0.0.1:7777/docs (when running)")
            print(f"  4. Say 'Hello' to start chatting with {_bot_name}")
            print("  5. Check README.md for features and tips")
            print("")
            print("Quick tips:")
            print("  - Seven will greet you proactively in the morning")
            print("  - Relationship depth increases as you chat")
            print("  - Seven learns your preferences automatically")
            print("  - Check the GUI for real-time status")
            print("")
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        return 1
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
