"""
Terminal UI aesthetics and input helpers for the Universal Test & Simulation CLI.
Supports Windows terminal with ANSI color fallback and box drawing.
"""
import os
import sys
import shutil

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI color tokens
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Foreground
    GREEN = '\033[32m'
    BRIGHT_GREEN = '\033[92m'
    BLUE = '\033[34m'
    BRIGHT_BLUE = '\033[94m'
    CYAN = '\033[36m'
    BRIGHT_CYAN = '\033[96m'
    YELLOW = '\033[33m'
    BRIGHT_YELLOW = '\033[93m'
    RED = '\033[31m'
    BRIGHT_RED = '\033[91m'
    MAGENTA = '\033[35m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'

    # Background
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_DARK = '\033[40m'


def clear_screen():
    """Clear terminal screen reliably across all Windows and Unix shells."""
    try:
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
        # ANSI escape sequence to clear buffer and place cursor at 0,0
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()
    except Exception:
        pass


def get_terminal_width() -> int:
    """Return terminal column width or default 75."""
    try:
        return min(shutil.get_terminal_size().columns, 85)
    except Exception:
        return 75


def print_banner(title: str = "⚡ UNIVERSAL TEST & SIMULATION ENGINE"):
    """Print the clean application banner."""
    w = get_terminal_width()
    print(f"\n{Colors.BRIGHT_GREEN}╔{'═' * (w - 2)}╗{Colors.RESET}")
    subtitle = "Multi-Framework Test Runner • Concurrency Simulator • Benchmarks"
    print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{title.center(w - 4)}{Colors.RESET} {Colors.BRIGHT_GREEN}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET} {Colors.DIM}{Colors.CYAN}{subtitle.center(w - 4)}{Colors.RESET} {Colors.BRIGHT_GREEN}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}╚{'═' * (w - 2)}╝{Colors.RESET}\n")


def print_section_header(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {title}{Colors.RESET}")
    print(f"{Colors.GRAY}{'─' * len(title) * 2}{Colors.RESET}\n")


def print_prompt_title(prompt: str):
    """Print the interactive question prompt."""
    print(f"{Colors.BOLD}{Colors.WHITE}{prompt}{Colors.RESET}\n")


def print_menu_option(key: str, label: str, description: str = ""):
    """Print a numbered menu option."""
    desc_str = f" {Colors.GRAY}- {description}{Colors.RESET}" if description else ""
    print(f"  {Colors.BOLD}{Colors.BRIGHT_GREEN}[{key}]{Colors.RESET} {Colors.WHITE}{label}{Colors.RESET}{desc_str}")


def print_status(tag: str, message: str, color: str = Colors.BRIGHT_GREEN):
    """Print a color-coded status badge."""
    print(f"  {color}{Colors.BOLD}[{tag}]{Colors.RESET} {message}")


def print_divider():
    """Print a horizontal dividing line."""
    w = get_terminal_width()
    print(f"{Colors.GRAY}{'─' * w}{Colors.RESET}")


def get_user_input(prompt_text: str = "> ") -> str:
    """Get input with styled prompt."""
    try:
        val = input(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{prompt_text}{Colors.RESET}").strip()
        return val
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
        sys.exit(0)
