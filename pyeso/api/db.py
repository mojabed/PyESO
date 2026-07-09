"""ESOUI API database - stores known functions, their signatures, and deprecations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FunctionSignature:
    """Represents a known ESOUI API function signature."""
    name: str
    params: list[str] = field(default_factory=list)
    is_method: bool = False
    min_params: int = 0  # minimum required params (excluding self)
    has_varargs: bool = False  # function uses `...`


@dataclass
class DeprecatedAPI:
    """Maps a deprecated name to its replacement."""
    old_name: str
    new_name: str
    message: str = ""


class APIDatabase:
    """In-memory database of ESOUI API surface."""

    def __init__(self) -> None:
        self._functions: dict[str, FunctionSignature] = {}
        self._deprecated: dict[str, DeprecatedAPI] = {}
        self._known_names: set[str] = set()
        self._known_variables: set[str] = set()

    def register_function(self, sig: FunctionSignature) -> None:
        """Register a function in the database."""
        self._functions[sig.name] = sig
        self._known_names.add(sig.name)

    def register_variable(self, name: str) -> None:
        """Register a known global variable (constant, table, etc.)."""
        self._known_variables.add(name)
        self._known_names.add(name)

    def register_deprecated(self, old_name: str, new_name: str, message: str = "") -> None:
        """Register a deprecated API alias."""
        self._deprecated[old_name] = DeprecatedAPI(old_name, new_name, message)
        self._known_names.add(old_name)

    def register_builtin(self, name: str) -> None:
        """Register a name as known (Lua builtin, keyword, etc.) without a signature."""
        self._known_names.add(name)

    def is_known(self, name: str) -> bool:
        """Check if a name is in the known API surface."""
        return name in self._known_names

    def is_variable(self, name: str) -> bool:
        """Check if a name is a known variable (not callable)."""
        return name in self._known_variables

    def get_signature(self, name: str) -> Optional[FunctionSignature]:
        """Get the function signature for a name, if it's a known function."""
        return self._functions.get(name)

    def get_deprecated(self, name: str) -> Optional[DeprecatedAPI]:
        """Check if a name is deprecated and get the replacement info."""
        return self._deprecated.get(name)

    def is_deprecated(self, name: str) -> bool:
        """Check if a name is deprecated."""
        return name in self._deprecated

    @property
    def function_count(self) -> int:
        return len(self._functions)

    @property
    def deprecated_count(self) -> int:
        return len(self._deprecated)

    @property
    def total_known(self) -> int:
        return len(self._known_names)
