"""Main linter orchestrator ties together parsing, API database, and rules."""

from __future__ import annotations

import pathlib
from typing import Optional

from pyeso.api.db import APIDatabase
from pyeso.api.extractor import ESOUIExtractor
from pyeso.parser.lua_visitor import LuaCallVisitor, collect_calls
from pyeso.rules.base import Diagnostic
from pyeso.rules.unknown_api import UnknownAPIRule
from pyeso.rules.param_count import ParamCountRule
from pyeso.rules.deprecated import DeprecatedAPIRule


class ESOLinter:
    def __init__(self, esoui_source_dir: Optional[str | pathlib.Path] = None) -> None:
        """Initialize the linter.

        If esoui_source_dir is given, extracts API definitions from the
        ESOUI source. Otherwise uses the built-in seed database.
        """
        self._extractor = ESOUIExtractor()

        if esoui_source_dir:
            self._db = self._extractor.extract_from_directory(esoui_source_dir)
        else:
            self._db = self._extractor.build_default_database()

        self._rules = [
            UnknownAPIRule(),
            ParamCountRule(),
            DeprecatedAPIRule(),
        ]

    @property
    def db(self) -> APIDatabase:
        return self._db

    def lint_file(self, filepath: pathlib.Path | str) -> list[Diagnostic]:
        """Lint a single LUA file."""
        visitor = collect_calls(filepath)
        diagnostics: list[Diagnostic] = []

        for rule in self._rules:
            diagnostics.extend(rule.check(visitor, self._db))

        return diagnostics

    def lint_directory(self, directory: pathlib.Path | str) -> list[Diagnostic]:
        """Lint all .lua files in a directory (recursive)."""
        root = pathlib.Path(directory)
        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        all_diagnostics: list[Diagnostic] = []
        for lua_file in root.rglob("*.lua"):
            all_diagnostics.extend(self.lint_file(lua_file))

        return all_diagnostics

    def lint_paths(self, paths: list[str]) -> list[Diagnostic]:
        """Lint a mix of files and directories."""
        all_diagnostics: list[Diagnostic] = []

        for p in paths:
            path = pathlib.Path(p)
            if path.is_dir():
                all_diagnostics.extend(self.lint_directory(path))
            elif path.is_file():
                all_diagnostics.extend(self.lint_file(path))
            else:
                # Could be a glob pattern or missing path
                all_diagnostics.append(Diagnostic(
                    severity="warning",
                    message=f"Path not found: {p}",
                    file=p,
                    line=0,
                    code="E000",
                ))

        return all_diagnostics
