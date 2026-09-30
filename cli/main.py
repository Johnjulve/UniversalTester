"""
Master CLI dispatcher for UniversalTester (testx).
Dispatches subcommands or delegates to interactive terminal or Desktop GUI.
"""
import os
import sys
import json
from typing import List, Optional

from cli.parser import build_parser
from cli.interactive import run_interactive_loop, load_config
from core.service import TesterService
from core.models import RunRequest

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint for testx command."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.gui:
        try:
            from gui.main import main as gui_main
            return gui_main()
        except ImportError as e:
            print(f"Error launching GUI: {e}")
            return 1

    service = TesterService()

    if parsed.command == "run":
        config = load_config(_ROOT_DIR)
        proj_key = parsed.project
        proj_path = os.getcwd()

        if proj_key:
            if proj_key in config.get("projects", {}):
                proj_path = config["projects"][proj_key].get("path", proj_path)
            elif os.path.exists(proj_key):
                proj_path = os.path.abspath(proj_key)

        req = RunRequest(
            capability=parsed.pillar,
            project_path=proj_path,
            options={"concurrent_users": parsed.users}
        )
        res = service.run(req)

        if parsed.json:
            print(json.dumps(res.to_dict(), indent=2))
        return 0 if res.is_success else 1

    elif parsed.command == "bench":
        req = RunRequest(
            capability="algorithms",
            project_path=_ROOT_DIR,
            options={"runtime": parsed.runtime}
        )
        res = service.run(req)
        if parsed.json:
            print(json.dumps(res.to_dict(), indent=2))
        return 0 if res.is_success else 1

    elif parsed.command == "matrix":
        from Performance.algorithm_tester import run_cross_language_benchmarks
        matrix_res = run_cross_language_benchmarks()
        return 0 if matrix_res.is_success else 1

    elif parsed.command == "doctor":
        req = RunRequest(capability="health", project_path=_ROOT_DIR)
        res = service.run(req)
        return 0 if res.is_success else 1

    elif parsed.command == "interactive" or parsed.command is None:
        run_interactive_loop(service, _ROOT_DIR)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
