"""Base definitions for linter rules and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    """A single lint diagnostic."""
    severity: Severity
    message: str
    file: str
    line: int
    code: str  # e.g. "E001", "W002"
    column: int = 0
    source_line: str = ""

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} [{self.severity.value.upper()}] {self.code}: {self.message}"


class LintRule:
    """Base class for a lint rule."""

    code: str = ""
    description: str = ""

    def check(self, visitor, db) -> list[Diagnostic]:
        """Run this rule against a parsed file. Returns diagnostics."""
        raise NotImplementedError
