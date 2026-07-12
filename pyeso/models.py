"""Typed models for the ESOUI API surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

@dataclass
class Param:
    """A single parameter in a function signature."""
    name: str
    type_hint: str = ""
    description: str = ""
    optional: bool = False

    def __str__(self) -> str:
        if self.optional:
            return f"{self.name}?"
        return self.name

@dataclass
class Function:
    """A known ESOUI API function with full signature information."""

    name: str
    params: list[Param] = field(default_factory=list)
    is_method: bool = False
    has_varargs: bool = False
    description: str = ""
    source_file: str = ""
    min_params: int = 0

    @property
    def param_names(self) -> list[str]:
        """Flat list of parameter names."""
        return [p.name for p in self.params]

    @property
    def required_params(self) -> list[Param]:
        """Non-optional parameters."""
        return [p for p in self.params if not p.optional]

    @property
    def optional_params(self) -> list[Param]:
        """Optional parameters."""
        return [p for p in self.params if p.optional]

    @property
    def max_params(self) -> int | float:
        """Maximum parameter count (infinity if varargs)."""
        if self.has_varargs:
            return float("inf")
        return len(self.params)

    @property
    def signature(self) -> str:
        """Human-readable signature string."""
        parts = [self.name, "("]
        if self.is_method and self.params:
            parts.append("self")
            if len(self.params) > 1:
                parts.append(", ")
        param_strs = [str(p) for p in self.params]
        parts.append(", ".join(param_strs))
        if self.has_varargs:
            if param_strs:
                parts.append(", ")
            parts.append("...")
        parts.append(")")
        return "".join(parts)

    @property
    def lua_call(self) -> str:
        """Minimal Lua call syntax."""
        return f"{self.name}({', '.join(self.param_names)})"

    def __repr__(self) -> str:
        return f"Function({self.signature})"

@dataclass
class Constant:
    """A known ESOUI global constant or variable."""
    name: str
    type_hint: str = ""
    description: str = ""
    source_file: str = ""

    def __repr__(self) -> str:
        return f"Constant({self.name})"

@dataclass
class Deprecation:
    """Maps a deprecated API name to its replacement."""
    old_name: str
    new_name: str
    message: str = ""
    since_api_version: int = 0

    def __repr__(self) -> str:
        return f"Deprecation({self.old_name} -> {self.new_name})"

@dataclass
class Event:
    """An ESOUI event that addons can register for."""
    name: str
    params: list[Param] = field(default_factory=list)
    description: str = ""

    @property
    def signature(self) -> str:
        return f"{self.name}({', '.join(str(p) for p in self.params)})"

    def __repr__(self) -> str:
        return f"Event({self.name})"


@dataclass
class EventInfo:
    """Full event signature with typed parameters (from ESOUIDocumentation.txt)."""
    name: str
    params: list[Param] = field(default_factory=list)
    min_params: int = 0
    description: str = ""

    @property
    def max_params(self) -> int | float:
        return len(self.params)

    @property
    def signature(self) -> str:
        return f"{self.name}({', '.join(str(p) for p in self.params)})"

    def __repr__(self) -> str:
        return f"EventInfo({self.signature})"

@dataclass
class Table:
    """An ESOUI global table (object-like namespace)."""
    name: str
    methods: list[Function] = field(default_factory=list)
    description: str = ""

    def __repr__(self) -> str:
        return f"Table({self.name}, {len(self.methods)} methods)"

class Domain(str, Enum):
    """High-level ESOUI API domain categories."""
    UNIT = "unit"
    ITEM = "item"
    CURRENCY = "currency"
    MAP = "map"
    QUEST = "quest"
    GUILD = "guild"
    GROUP = "group"
    COMBAT = "combat"
    CRAFTING = "crafting"
    CHAT = "chat"
    UI = "ui"
    EVENT = "event"
    SETTINGS = "settings"
    TIME = "time"
    LOCALIZATION = "localization"
    MISC = "misc"

ApiEntry = Function | Constant | Event | Table | Deprecation
