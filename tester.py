#!/usr/bin/env python
"""
Universal Test & Simulation CLI.
Interactive terminal application for multi-framework test running and concurrency simulation.
"""
import os
import sys
import json
from typing import Dict, Any, Optional

# Ensure project root & Testing directory are in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

try:
    from Testing.core.ui import (
        Colors,
        clear_screen,
        print_banner,
        print_prompt_title,
        print_menu_option,
        get_user_input,
        print_divider,
        print_status
    )
    from Testing.adapters import get_adapter
except ImportError:
    from core.ui import (
        Colors,
        clear_screen,
        print_banner,
        print_prompt_title,
        print_menu_option,
        get_user_input,
        print_divider,
        print_status
    )
    from adapters import get_adapter


def load_config() -> Dict[str, Any]:
    """Load configuration from tester_config.json with fallback defaults."""
    config_path = os.path.join(_CURRENT_DIR, 'tester_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default fallback
    return {
        "projects": {
            "1": {
                "id": "e_botar",
                "name": "E_Botar",
                "type": "django",
                "path": _PROJECT_ROOT,
                "backend_dir": os.path.join(_PROJECT_ROOT, "backend"),
                "python_env": os.path.join(_PROJECT_ROOT, "env", "Scripts", "python.exe")
            },
            "2": {
                "id": "e_botar_lite",
                "name": "E_Botar lite",
                "type": "django",
                "path": "d:/System Projects/E_Botar-Lite",
                "backend_dir": "d:/System Projects/E_Botar-Lite/backend",
                "python_env": os.path.join(_PROJECT_ROOT, "env", "Scripts", "python.exe")
            }
        },
        "default_concurrency_options": [50, 100, 500, 1000, 2000]
    }


def select_project(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Prompt user to select project."""
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
            
        print_menu_option("3", "Custom Project Path...")
        print_menu_option("0", "Exit", "Close testing application")
        print()
        
        choice = get_user_input(f"{os.getcwd()}> ")
        
        if choice == "0":
            return None
        elif choice in projects:
            return projects[choice]
        elif choice == "3":
            custom_path = get_user_input("Enter absolute project path: ").strip()
            if os.path.exists(custom_path):
                return {
                    "id": "custom",
                    "name": os.path.basename(custom_path) or "Custom Project",
                    "type": "django",
                    "path": custom_path,
                    "backend_dir": os.path.join(custom_path, "backend"),
                    "python_env": config.get("projects", {}).get("1", {}).get("python_env", sys.executable)
                }
            else:
                error_msg = f"Path does not exist: {custom_path}"
        else:
            error_msg = f"Invalid option: '{choice}'. Please select from the menu above."


def select_test_type(project_name: str) -> Optional[str]:
    """Prompt user to select test or simulation type."""
    error_msg = ""
    
    while True:
        clear_screen()
        print_banner()
        if error_msg:
            print(f"{Colors.BRIGHT_RED}⚠️  {error_msg}{Colors.RESET}\n")
            error_msg = ""
            
        print(f"{Colors.DIM}Target Project: {Colors.BOLD}{Colors.BRIGHT_CYAN}{project_name}{Colors.RESET}\n")
        print_prompt_title("What type of Test/Simulation:")
        
        print_menu_option("1", "Overall Test", "Full suite: Components + Algorithms + Simulation")
        print_menu_option("2", "Simulation test", "Analytical concurrent voter load")
        print_menu_option("3", "Components Test", "Fast Tier 1 unit & API tests")
        print_menu_option("4", "Performance Benchmark", "API latency & database query test")
        print_menu_option("5", "Algorithm Benchmarks", "Sorting, Searching, Cryptography & Aggregations")
        print_menu_option("0", "Back to Project Selection")
        print()
        
        choice = get_user_input(f"{os.getcwd()}> ")
        
        if choice in ("0", "1", "2", "3", "4", "5"):
            return choice
        else:
            error_msg = f"Invalid option: '{choice}'. Please select from the menu above."


def select_concurrency() -> Optional[int]:
    """Prompt user to select concurrency volume for simulation."""
    error_msg = ""
    
    while True:
        clear_screen()
        print_banner()
        if error_msg:
            print(f"{Colors.BRIGHT_RED}⚠️  {error_msg}{Colors.RESET}\n")
            error_msg = ""
            
        print_prompt_title("How much users would you simulate:")
        
        print_menu_option("1", "50", "Light traffic (2.5% of sample)")
        print_menu_option("2", "100", "Moderate peak (5% of sample)")
        print_menu_option("3", "500", "High rush hour (25% of sample)")
        print_menu_option("4", "1000", "Campus-wide surge (50% of sample)")
        print_menu_option("5", "Custom count...")
        print_menu_option("0", "Back to Test Selection")
        print()
        
        choice = get_user_input(f"{os.getcwd()}> ")
        
        if choice == "0":
            return None
        elif choice == "1":
            return 50
        elif choice == "2":
            return 100
        elif choice == "3":
            return 500
        elif choice == "4":
            return 1000
        elif choice == "5":
            custom_str = get_user_input("Enter number of concurrent users: ")
            try:
                val = int(custom_str)
                if val > 0:
                    return val
                error_msg = "Please enter a positive number."
            except ValueError:
                error_msg = f"Invalid number: '{custom_str}'"
        else:
            error_msg = f"Invalid option: '{choice}'. Please select from the menu above."


def main():
    """Main terminal loop."""
    config = load_config()
    
    while True:
        # Step 1: Project Selection
        project = select_project(config)
        if not project:
            print(f"\n{Colors.BRIGHT_GREEN}Exiting Universal Tester. Goodbye!{Colors.RESET}\n")
            sys.exit(0)
            
        adapter = get_adapter(project)
        
        while True:
            # Step 2: Test Type Selection
            test_type = select_test_type(project.get("name", "Target"))
            if test_type == "0":
                break  # Back to project selection
                
            # Clear terminal before test execution starts
            clear_screen()
            
            if test_type == "1":
                # Overall Test
                adapter.run_overall_test()
            elif test_type == "2":
                # Simulation Test
                users = select_concurrency()
                if users is None:
                    continue  # Back to test selection
                clear_screen()
                adapter.run_simulation_test(users)
            elif test_type == "3":
                # Components Test
                adapter.run_components_test()
            elif test_type == "4":
                # Performance Benchmark
                adapter.run_benchmarks()
            elif test_type == "5":
                # Algorithm Benchmarks
                adapter.run_algorithms_test()
                
            print_divider()
            again = get_user_input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
            if again == 'q':
                print(f"\n{Colors.BRIGHT_GREEN}Exiting Universal Tester. Goodbye!{Colors.RESET}\n")
                sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
        sys.exit(0)
