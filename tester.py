#!/usr/bin/env python
"""
Universal Test & Simulation CLI.
Interactive terminal application for multi-framework test running and concurrency simulation.
"""
import os
import sys
import json
from typing import Dict, Any, Optional

# Ensure UniversalTester directory is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

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
from adapters import get_adapter, detect_adapter


def load_config() -> Dict[str, Any]:
    """Load configuration from tester_config.json with fallback to example config."""
    config_path = os.path.join(_CURRENT_DIR, 'tester_config.json')
    example_path = os.path.join(_CURRENT_DIR, 'tester_config.example.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
            
    if os.path.exists(example_path):
        try:
            with open(example_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "version": "1.0.0",
        "app_name": "Universal Tester",
        "projects": {},
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
            
        print_menu_option("C", "Custom Project Path...")
        print_menu_option("0", "Exit", "Close testing application")
        print()
        
        choice = get_user_input(f"{os.getcwd()}> ")
        
        if choice == "0":
            return None
        elif choice in projects:
            return projects[choice]
        elif choice.lower() in ("c", "custom"):
            custom_path = get_user_input("Enter absolute project path: ").strip().strip('"').strip("'")
            if os.path.exists(custom_path):
                norm_custom = os.path.abspath(custom_path)
                base_name = os.path.basename(norm_custom).lower()

                # If user entered a /backend or /frontend subfolder directly, infer root
                if base_name in ('backend', 'server', 'api'):
                    project_root = os.path.dirname(norm_custom)
                    backend_dir = norm_custom
                    frontend_cand = os.path.join(project_root, "frontend")
                    frontend_dir = frontend_cand if os.path.exists(frontend_cand) else project_root
                    display_name = os.path.basename(project_root) or "Custom Project"
                elif base_name in ('frontend', 'client', 'web', 'ui'):
                    project_root = os.path.dirname(norm_custom)
                    frontend_dir = norm_custom
                    backend_cand = os.path.join(project_root, "backend")
                    backend_dir = backend_cand if os.path.exists(backend_cand) else project_root
                    display_name = os.path.basename(project_root) or "Custom Project"
                else:
                    project_root = norm_custom
                    backend_cand = os.path.join(norm_custom, "backend")
                    frontend_cand = os.path.join(norm_custom, "frontend")
                    backend_dir = backend_cand if os.path.exists(backend_cand) else norm_custom
                    frontend_dir = frontend_cand if os.path.exists(frontend_cand) else norm_custom
                    display_name = os.path.basename(norm_custom) or "Custom Project"

                detected_cls = detect_adapter(backend_dir) or detect_adapter(project_root)
                proj_type = detected_cls.adapter_id() if detected_cls else "python"
                
                return {
                    "id": "custom",
                    "name": display_name,
                    "type": proj_type,
                    "path": project_root,
                    "backend_dir": backend_dir,
                    "frontend_dir": frontend_dir,
                    "python_env": ""
                }

            else:
                error_msg = f"Path does not exist: {custom_path}"
        else:
            error_msg = f"Invalid option: '{choice}'. Please select from the menu above."


from core.orchestrator import TestOrchestrator
import argparse


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
        print_prompt_title("Select Testing Pillar to Execute:")
        
        print_menu_option("1", "Adaptive Tester (Unit & Component Tests)", "Delegates to project runner (pytest / vitest / jest)")
        print_menu_option("2", "Algorithm Tester (Correctness & Edge Cases)", "Pure CS correctness assertions & test vectors")
        print_menu_option("3", "Performance Tester (Speed & Memory Profiling)", "CPU latency benchmarks & tracemalloc memory profiling")
        print_menu_option("4", "Reliability Tester (Concurrency & Load Capacity)", "Analytical peak traffic simulation & degradation envelope")
        print_menu_option("5", "Security Tester (Vulnerabilities & Dependencies)", "Static AST vulnerability scan & ecosystem audit")
        print_menu_option("6", "Full 5-Pillar Assessment (Comprehensive Suite)", "Complete run across all 5 official testing pillars")
        print_menu_option("0", "Back to Project Selection")
        print()
        
        choice = get_user_input(f"{os.getcwd()}> ")
        
        if choice in ("0", "1", "2", "3", "4", "5", "6"):
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
            
        print_prompt_title("Select concurrent user volume to simulate:")
        
        print_menu_option("1", "50", "Light load (50 concurrent users/reqs)")
        print_menu_option("2", "100", "Moderate load (100 concurrent users/reqs)")
        print_menu_option("3", "500", "High traffic rush (500 concurrent users/reqs)")
        print_menu_option("4", "1000", "Surge capacity peak (1,000 concurrent users/reqs)")
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
    """Main interactive terminal loop."""
    config = load_config()
    
    while True:
        # Step 1: Project Selection
        project = select_project(config)
        if not project:
            print(f"\n{Colors.BRIGHT_GREEN}Exiting Universal Tester. Goodbye!{Colors.RESET}\n")
            sys.exit(0)
            
        adapter = get_adapter(project)
        orchestrator = TestOrchestrator(adapter)
        
        while True:
            # Step 2: Test Type Selection
            test_type = select_test_type(project.get("name", "Target"))
            if test_type == "0":
                break  # Back to project selection
                
            # Clear terminal before test execution starts
            clear_screen()
            
            if test_type == "1":
                orchestrator.run_adaptive()
            elif test_type == "2":
                orchestrator.run_algorithms()
            elif test_type == "3":
                orchestrator.run_performance()
            elif test_type == "4":
                users = select_concurrency()
                if users is None:
                    continue  # Back to test selection
                clear_screen()
                orchestrator.run_reliability(users)
            elif test_type == "5":
                orchestrator.run_security()
            elif test_type == "6":
                orchestrator.run_all_pillars(concurrent_users=500)
                
            print_divider()
            again = get_user_input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
            if again == 'q':
                print(f"\n{Colors.BRIGHT_GREEN}Exiting Universal Tester. Goodbye!{Colors.RESET}\n")
                sys.exit(0)


def run_cli():
    """Parse CLI arguments and execute non-interactive subcommand or launch interactive menu."""
    parser = argparse.ArgumentParser(
        description="⚡ UNIVERSAL TEST & SIMULATION ENGINE",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'pillar',
        nargs='?',
        choices=['adaptive', 'algo', 'algorithms', 'perf', 'performance', 'reliability', 'rel', 'security', 'sec', 'all'],
        help="Direct testing pillar to execute non-interactively"
    )
    parser.add_argument(
        '--project', '-p',
        type=str,
        default=None,
        help="Target project ID from tester_config.json or absolute filesystem path"
    )
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        default=500,
        help="Concurrent simulated users for reliability testing (default: 500)"
    )

    args = parser.parse_args()

    # Non-interactive CLI dispatch
    if args.pillar:
        config = load_config()
        projects = config.get("projects", {})

        target_project = None
        if args.project:
            if args.project in projects:
                target_project = projects[args.project]
            elif os.path.exists(args.project):
                from adapters import detect_adapter
                norm_p = os.path.abspath(args.project)
                detected = detect_adapter(norm_p)
                target_project = {
                    "id": "cli_custom",
                    "name": os.path.basename(norm_p) or "CLI Target",
                    "type": detected.adapter_id() if detected else "python",
                    "path": norm_p
                }
            else:
                print(f"{Colors.BRIGHT_RED}Error: Project '{args.project}' not found in configuration or filesystem.{Colors.RESET}")
                sys.exit(1)
        elif projects:
            # Default to first configured project
            first_key = list(projects.keys())[0]
            target_project = projects[first_key]
        else:
            # Fallback to current working directory
            target_project = {
                "id": "cwd",
                "name": os.path.basename(os.getcwd()) or "Local Project",
                "type": "python",
                "path": os.getcwd()
            }

        adapter = get_adapter(target_project)
        orchestrator = TestOrchestrator(adapter)

        try:
            result = orchestrator.dispatch(args.pillar, concurrent_users=args.concurrent)
            # Exit code 0 if tests passed or capability is unavailable; 1 on failure
            sys.exit(0 if (result.is_success or result.is_unavailable) else 1)
        except Exception as e:
            print(f"\n{Colors.BRIGHT_RED}Error during orchestrator dispatch: {e}{Colors.RESET}\n")
            sys.exit(1)

    # Interactive terminal loop
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
        sys.exit(0)


if __name__ == '__main__':
    run_cli()

