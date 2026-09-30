"""
CLI Argument Parser definition for UniversalTester (testx).
Supports headless subcommands, automation flags, and Desktop GUI invocation.
"""
import argparse
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    """Build and return the master argument parser."""
    parser = argparse.ArgumentParser(
        prog="testx",
        description="UniversalTester: Multi-framework 5-pillar software testing & benchmark engine."
    )
    parser.add_argument("-v", "--version", action="version", version="UniversalTester 1.2.0")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch the cross-platform Desktop GUI application.")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # testx run [PROJECT] [--pillar P] [--users N] [--json]
    run_parser = subparsers.add_parser("run", help="Run testing pillars on a project.")
    run_parser.add_argument("project", nargs="?", default="", help="Project path or project key from config.")
    run_parser.add_argument("-p", "--pillar", default="all", help="Pillar to execute: 1..5, adaptive, algo, perf, rel, sec, all (default: all)")
    run_parser.add_argument("-u", "--users", type=int, default=500, help="Concurrent user volume for reliability simulation (default: 500)")
    run_parser.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # testx bench [--runtime R]
    bench_parser = subparsers.add_parser("bench", help="Run algorithm benchmarks.")
    bench_parser.add_argument("-r", "--runtime", default="all", choices=["python", "node", "dart", "all"], help="Target runtime environment.")
    bench_parser.add_argument("--json", action="store_true", help="Output benchmark results in JSON format.")

    # testx matrix
    subparsers.add_parser("matrix", help="Run cross-language comparative benchmark matrix.")

    # testx doctor
    subparsers.add_parser("doctor", help="Inspect host system environment, runtimes, and health.")

    # testx interactive
    subparsers.add_parser("interactive", help="Start the interactive terminal application.")

    return parser
