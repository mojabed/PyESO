"""Main linter orchestrator — ties together parsing, registry, and rules."""

from __future__ import annotations

import pathlib
from typing import Optional

from pyeso.loader import Loader
from pyeso.parser.lua_visitor import collect_calls
from pyeso.registry import Registry
from pyeso.rules.base import Diagnostic, Severity
from pyeso.rules.deprecated import DeprecatedAPIRule
from pyeso.rules.deprecated_constants import DeprecatedConstantRule
from pyeso.rules.event_validation import EventValidationRule
from pyeso.rules.global_leak import GlobalLeakRule
from pyeso.rules.method_validation import MethodValidationRule
from pyeso.rules.param_count import ParamCountRule
from pyeso.rules.string_localization import StringLocalizationRule
from pyeso.rules.unknown_api import UnknownAPIRule


def _find_bundled_esoui() -> Optional[pathlib.Path]:
    this_file = pathlib.Path(__file__).resolve()
    repo_root = this_file.parent.parent
    candidate = repo_root / "esoui" / "esoui"

    if candidate.is_dir() and list(candidate.rglob("*.lua")):
        return candidate

    return None


class ESOLinter:
    def __init__(self) -> None:
        loader = Loader()
        bundled = _find_bundled_esoui()

        if not bundled:
            import sys as _sys
            print(
                "\n  ERROR: ESOUI API source not found.\n"
                "  PyESO requires the full ESOUI API surface for accurate linting.\n"
                "  Run:\n\n"
                "      git submodule update --init --recursive\n",
                file=_sys.stderr,
            )
            _sys.exit(1)

        # The ESOUIDocumentation.txt is in the parent directory of the Lua source
        esoui_root = bundled.parent  # esoui/esoui/ -> esoui/
        self._registry = loader.load_from_esoui(esoui_root)

        self._rules = [
            UnknownAPIRule(),
            ParamCountRule(),
            DeprecatedAPIRule(),
            GlobalLeakRule(),
            DeprecatedConstantRule(),
            StringLocalizationRule(),
            EventValidationRule(),
            MethodValidationRule(),
        ]

    @property
    def db(self) -> Registry:
        return self._registry

    @property
    def registry(self) -> Registry:
        return self._registry

    def lint_file(self, filepath: pathlib.Path | str) -> list[Diagnostic]:
        """Lint a single LUA file."""
        visitor = collect_calls(filepath)
        diagnostics: list[Diagnostic] = []

        for rule in self._rules:
            diagnostics.extend(rule.check(visitor, self._registry))

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
                all_diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=f"Path not found: {p}",
                    file=p,
                    line=0,
                    code="E000",
                ))

        return all_diagnostics
