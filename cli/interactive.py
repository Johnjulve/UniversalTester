"""
Interactive terminal interface for UniversalTester.
Dynamically displays menus generated from TesterService.list_capabilities().
"""
import os
import sys
import json
from typing import Dict, Any, Optional

from core.ui import (
    Colors, clear_screen, print_banner, print_prompt_title,
    print_menu_option, get_user_input, print_divider
)
from core.models import RunRequest
from core.service import TesterService
from adapters.registry import detect_adapter


def load_config(root_dir: str) -> Dict[str, Any]:
    """Load configuration from tester_config.json with fallback to example config."""
    for filename in ('tester_config.json', 'tester_config.example.json'):
        path = os.path.join(root_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return {"version": "2.0.0", "projects": {}, "default_concurrency_options": [50, 100, 500, 1000]}


def select_project(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Prompt user to select a target project or enter custom path."""
    projects = config.get("projects", {})
    error_msg = ""

    while True:
        clear_screen()
        print_banner()
        if error_msg:
            print(f"{Colors.BRIGHT_RED}⚠️  {error_msg}{Colors.RESET}\n")
            error_msg = ""

        print_prompt_title("Choose project for testing:")
        for key, proj in projects.items():
            print_menu_option(key, proj.get("name", f"Project {key}"))

        print_menu_option("C", "Custom Project Path...")
        print_menu_option("0", "Exit", "Close testing application")
        print()

        choice = get_user_input(f"{os.getcwd()}> ").strip()
        if choice == "0":
            return None
        elif choice in projects:
            return projects[choice]
        elif choice.lower() in ("c", "custom"):
            custom_path = get_user_input("Enter absolute project path: ").strip().strip('"').strip("'")
            if os.path.exists(custom_path):
                norm = os.path.abspath(custom_path)
                return {
                    "id": "custom",
                    "name": os.path.basename(norm) or "Custom Project",
                    "path": norm
                }
            error_msg = f"Path does not exist: {custom_path}"
        else:
            error_msg = f"Invalid option: '{choice}'"


def select_concurrency() -> int:
    """Prompt user to choose concurrent user load."""
    print_prompt_title("Select concurrent user volume:")
    options = {"1": 50, "2": 100, "3": 500, "4": 1000}
    for k, v in options.items():
        print_menu_option(k, f"{v} concurrent users")
    choice = get_user_input("Select [1-4, default 500]: ").strip()
    return options.get(choice, 500)


def run_interactive_loop(service: TesterService, root_dir: str) -> None:
    """Run interactive terminal menu driven dynamically by TesterService capabilities."""
    config = load_config(root_dir)

    while True:
        project = select_project(config)
        if not project:
            print(f"\n{Colors.DIM}Exiting UniversalTester. Goodbye!{Colors.RESET}")
            break

        proj_path = project.get("path", "")
        proj_name = project.get("name", "Target Project")

        while True:
            clear_screen()
            print_banner()
            print(f"{Colors.DIM}Target Project: {Colors.BOLD}{Colors.BRIGHT_CYAN}{proj_name}{Colors.RESET}\n")
            print_prompt_title("Select Testing Capability:")

            capabilities = service.list_capabilities(proj_path)
            cap_map = {}

            for idx, cap in enumerate(capabilities, 1):
                key = str(idx)
                cap_map[key] = cap
                status_note = "" if cap.get("available", True) else " [○ UNAVAILABLE]"
                print_menu_option(key, cap["name"] + status_note, cap.get("description", ""))

            print_menu_option("0", "Back to Project Selection")
            print()

            choice = get_user_input(f"{os.getcwd()}> ").strip()
            if choice == "0":
                break

            selected = cap_map.get(choice)
            if not selected:
                continue

            opts = {}
            if selected["id"] in ("simulation", "full_suite"):
                opts["concurrent_users"] = select_concurrency()

            req = RunRequest(capability=selected["id"], project_path=proj_path, options=opts)
            print_divider()
            service.run(req)

            print()
            get_user_input(f"{Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
