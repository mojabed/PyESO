#!/usr/bin/env python3
"""pyeso — ESO addon linter.

    pyeso MyAddon.lua          # lint a single file
    pyeso MyAddon/             # lint a directory
    pyeso MyAddon/ Lib/        # lint multiple paths

Output goes to the terminal (with colors) and to pyeso_report.txt.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import sys
from typing import TextIO

from pyeso import ESOLinter
from pyeso.rules.base import Diagnostic

# ANSI color codes
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

_ICON = {"error": "X", "warning": "!", "info": "i"}


def main() -> int:
    frozen = getattr(sys, "frozen", False)
    if frozen and len(sys.argv) < 2:
        _double_click_help()
        return 0

    if len(sys.argv) < 2:
        print("Usage: pyeso <file.lua | directory/> [...]")
        return 1

    linter = ESOLinter()
    all_diags = linter.lint_paths(sys.argv[1:])

    use_color = sys.stdout.isatty()
    log_path = pathlib.Path("pyeso_report.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        _write(f"\n{_BOLD}  PyESO Report{_RESET}", log, use_color)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write(f"  {ts}\n", log, use_color)

        if not all_diags:
            _write(f"\n  {_GREEN}No issues found.{_RESET}\n", log, use_color)
            return 0

        # Group by file
        by_file: dict[str, list[Diagnostic]] = {}
        for d in all_diags:
            by_file.setdefault(d.file, []).append(d)

        errors = warnings = infos = 0
        for filepath, diags in sorted(by_file.items()):
            _write(f"\n{_BOLD}  {filepath}{_RESET}\n", log, use_color)

            for d in sorted(diags, key=lambda d: (d.line, d.code)):
                if d.code.startswith("E"):
                    errors += 1
                    clr = _RED
                    icon = "X"
                elif d.code.startswith("W"):
                    warnings += 1
                    clr = _YELLOW
                    icon = "!"
                else:
                    infos += 1
                    clr = _CYAN
                    icon = "i"
                _write(
                    f"    {clr}{icon} [{d.code}]{_RESET} line {d.line}: {d.message}\n",
                    log, use_color,
                )

        # Summary
        _write("\n  " + "─" * 48 + "\n", log, use_color)
        parts = []
        if errors:
            parts.append(f"{_RED}{errors} error(s){_RESET}")
        if warnings:
            parts.append(f"{_YELLOW}{warnings} warning(s){_RESET}")
        if infos:
            parts.append(f"{_CYAN}{infos} info(s){_RESET}")
        _write(f"  {len(all_diags)} issue(s): {', '.join(parts)}\n", log, use_color)
        _write(f"  Log saved to {log_path}\n", log, use_color)

    return 1 if errors else 0


def _write(text: str, log: TextIO, color: bool) -> None:
    if color:
        print(text, end="")
    else:
        print(_strip_ansi(text), end="")
    log.write(_strip_ansi(text))


def _strip_ansi(text: str) -> str:
    return re.sub(r"\033\[\d*(;\d*)?m", "", text)


def _double_click_help() -> None:
    print(f"""
  {_BOLD}PyESO -- ESO Addon Linter{_RESET}
  Catches typos, wrong args, deprecated APIs, and more
  before your addon ever runs in-game.

  This is a command-line tool.  Open a terminal and run:

      pyeso MyAddon.lua
      pyeso MyAddon\\

  Output goes to the terminal and {_CYAN}pyeso_report.txt{_RESET}.

  Press Enter to close...
""")
    input()


if __name__ == "__main__":
    sys.exit(main())
