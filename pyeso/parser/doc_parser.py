"""Parser for ESOUIDocumentation.txt — the canonical typed API reference.

Parses the structured Textile-like markup into typed models for:
- Game API: C-side functions with full typed signatures
- Object API: UI control classes with typed methods
- Events: EVENT_* events with typed parameter signatures
- Global Variables: typed constants organized by enum category
"""

from __future__ import annotations

import pathlib
import re
from typing import Optional

from pyeso.models import EventInfo, Function, Param
from pyeso.registry import Registry


class DocParser:
    """Parses ESOUIDocumentation.txt and populates a Registry."""

    # Regex patterns
    _H2_RE = re.compile(r"^h2\.\s+(.+)$")
    _H3_RE = re.compile(r"^h3\.\s+(.+)$")
    _H5_RE = re.compile(r"^h5\.\s+(.+)$")

    # Function/event definition: * Name(typed params)
    _FUNC_DEF_RE = re.compile(
        r"^\*\s+"                           # leading * and spaces
        r"(?:\[(.+?)\]\s+)?"                # optional [Category|#Category] link
        r"([A-Za-z_][\w.]*)"                # function name
        r"(?:\s+\*(?:private|protected(?:-attributes)?)\*)?"  # optional *private* / *protected* marker
        r"\s*\(([^)]*)\)"                    # params in parens
    )

    # Simple param: *type* _name_  or  *type* _name_, *type* _name_
    _TYPED_PARAM_RE = re.compile(
        r"\*([^*]+?)\*\s*_(\w+)_"
    )

    # Return value line
    _RETURNS_RE = re.compile(
        r"^\*\*\s+_Returns:_\s+(.+)$"
    )

    # Return type: *type* _name_
    _RETURN_TYPE_RE = re.compile(
        r"\*([^*]+?)\*\s*_(\w+)_"
    )

    # Constant definition under h5: * CONSTANT_NAME
    _CONSTANT_RE = re.compile(r"^\*\s+([A-Z][A-Z_0-9]+)\s*$")

    # Event definition (may have no params)
    _EVENT_RE = re.compile(
        r"^\*\s+(EVENT_\w+)"
        r"(?:\s*\(([^)]*)\))?"               # optional params
    )

    # public API 
    def parse(self, doc_path: pathlib.Path, reg: Registry) -> None:
        """Parse ESOUIDocumentation.txt and populate the registry."""
        if not doc_path.exists():
            raise FileNotFoundError(f"Documentation file not found: {doc_path}")

        source = doc_path.read_text(encoding="utf-8", errors="replace")

        current_h2: str = ""
        current_h3: str = ""
        current_h5: str = ""

        for line in source.splitlines():
            # Section tracking
            m2 = self._H2_RE.match(line)
            if m2:
                current_h2 = m2.group(1).strip()
                current_h3 = ""
                current_h5 = ""
                continue

            m3 = self._H3_RE.match(line)
            if m3:
                current_h3 = m3.group(1).strip()
                current_h5 = ""
                continue

            m5 = self._H5_RE.match(line)
            if m5:
                current_h5 = m5.group(1).strip()
                continue

            # Dispatch based on section
            if current_h2 == "Game API":
                self._parse_game_api_line(line, reg)
            elif current_h2 == "Object API" and current_h3:
                self._parse_object_api_line(line, current_h3, reg)
            elif current_h2 == "Events":
                self._parse_event_line(line, reg)
            elif current_h2 == "Global Variables" and current_h5:
                self._parse_global_var_line(line, current_h5, reg)

    # Game API
    _current_game_func: Optional[Function] = None

    def _parse_game_api_line(self, line: str, reg: Registry) -> None:
        """Parse a line in the Game API section."""
        # Check if this is a return-value continuation line
        ret = self._RETURNS_RE.match(line)
        if ret and self._current_game_func:
            # We could store return types here; skip for now
            return

        # Check for function definition
        m = self._FUNC_DEF_RE.match(line)
        if not m:
            return

        # m.group(1) is optional category link — ignore
        func_name = m.group(2)
        params_str = m.group(3) if m.group(3) else ""

        params = self._parse_typed_params(params_str)
        min_params = sum(1 for p in params if not p.optional)

        fn = Function(
            name=func_name,
            params=params,
            min_params=min_params,
            has_varargs="..." in params_str or "variable returns" in params_str.lower(),
            source_file="ESOUIDocumentation.txt (Game API)",
        )
        self._current_game_func = fn
        reg.add_function(fn)

    # Object API
    def _parse_object_api_line(self, line: str, class_name: str, reg: Registry) -> None:
        """Parse a method line in the Object API section."""
        # Skip return-value continuations
        if line.startswith("**"):
            return

        m = self._FUNC_DEF_RE.match(line)
        if not m:
            return

        method_name = m.group(2)
        params_str = m.group(3) if m.group(3) else ""

        params = self._parse_typed_params(params_str)
        min_params = sum(1 for p in params if not p.optional)

        fn = Function(
            name=f"{class_name}:{method_name}",
            params=params,
            min_params=min_params,
            has_varargs="..." in params_str,
            is_method=True,
            source_file="ESOUIDocumentation.txt (Object API)",
        )
        reg.add_function(fn)
        # Also register as a known method on this class
        reg.add_method(class_name, method_name, fn)

    # Events 
    def _parse_event_line(self, line: str, reg: Registry) -> None:
        """Parse an event definition line.

        ESO Lua convention: every event callback receives eventId (integer)
        as the first parameter, even though ESOUIDocumentation.txt doesn't
        document it. We prepend it here to match actual ESO runtime behavior.
        """
        m = self._EVENT_RE.match(line)
        if not m:
            return

        event_name = m.group(1)
        params_str = m.group(2) if m.group(2) else ""

        doc_params = self._parse_typed_params(params_str)

        params = [Param(name="eventId", type_hint="integer", optional=False)]
        params.extend(doc_params)

        min_params = 1 + sum(1 for p in doc_params if not p.optional)

        ev = EventInfo(
            name=event_name,
            params=params,
            min_params=min_params,
        )
        reg.add_event_info(ev)
        reg.add_name(event_name)

    # Global Variables
    def _parse_global_var_line(self, line: str, category: str, reg: Registry) -> None:
        """Parse a constant definition line under an h5 enum category."""
        m = self._CONSTANT_RE.match(line)
        if not m:
            return

        const_name = m.group(1)
        if not reg.is_known(const_name):
            reg.add_constant_name(const_name)

    # Helpers
    def _parse_typed_params(self, params_str: str) -> list[Param]:
        """Parse typed parameters like '*integer* _count_, *string* _name_'."""
        params: list[Param] = []

        for m in self._TYPED_PARAM_RE.finditer(params_str):
            type_hint = m.group(1).strip()
            name = m.group(2)
            optional = "nilable" in type_hint or "?" in name
            params.append(Param(
                name=name,
                type_hint=type_hint,
                optional=optional,
            ))

        return params
