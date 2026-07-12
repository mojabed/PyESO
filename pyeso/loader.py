"""Loads the ESOUI API surface into a Registry from source files and documentation.
"""

from __future__ import annotations

import pathlib
import re

from pyeso.api.builtins import (
    ESO_STRING_EXTENSIONS,
    ESO_ZO_WRAPPERS,
    LUA_BUILTIN_GLOBALS,
    LUA_KEYWORDS,
)
from pyeso.models import Constant, Deprecation, Function, Param
from pyeso.parser.doc_parser import DocParser
from pyeso.registry import Registry


class Loader:
    """Populates a Registry from ESOUI source files and documentation."""

    _FUNC_DEF_RE = re.compile(
        r"^\s*function\s+([A-Za-z_][\w.]*[A-Za-z_])\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    _METHOD_DEF_RE = re.compile(
        r"^\s*function\s+([A-Za-z_][\w.]*):(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    _GLOBAL_ASSIGN_RE = re.compile(
        r"^(?!.*\bfunction\b)(?:local\s+)?([A-Z][\w]*)\s*=\s*",
        re.MULTILINE,
    )

    _DEPRECATED_ALIAS_RE = re.compile(
        r"^([A-Z][\w.]*)\s*=\s*([A-Z][\w.]+)\s*$",
        re.MULTILINE,
    )

    # public API 

    def load_from_esoui(self, esoui_dir: str | pathlib.Path) -> Registry:
        """Build registry from ESOUI Lua source + ESOUIDocumentation.txt.

        esoui_dir should be the root of the ESOUI repository, which contains
        ESOUIDocumentation.txt at the top level and Lua source under esoui/.
        """
        reg = Registry()
        reg._source = "esoui"
        root = pathlib.Path(esoui_dir)

        if not root.exists():
            raise FileNotFoundError(f"ESOUI directory not found: {esoui_dir}")

        lua_root = root / "esoui"

        # Step 1: Register Lua builtins
        self._register_builtins(reg)

        # Step 2: Parse ESOUIDocumentation.txt for typed API signatures
        doc_file = root / "ESOUIDocumentation.txt"
        if doc_file.exists():
            doc_parser = DocParser()
            doc_parser.parse(doc_file, reg)
        else:
            raise FileNotFoundError(
                f"ESOUIDocumentation.txt not found at {doc_file}. "
                f"The full ESOUI API documentation is required."
            )

        # Step 3: Extract additional functions/constants from Lua source
        if lua_root.exists():
            for alias_file in lua_root.rglob("*addoncompatibilityaliases*.lua"):
                self._extract_deprecations(reg, alias_file)

            for lua_file in lua_root.rglob("*.lua"):
                self._extract_functions(reg, lua_file)

        self._supplement_varargs(reg)

        return reg

    @staticmethod
    def _supplement_varargs(reg: Registry) -> None:
        """Fix varargs flag for known C-side functions that accept extra args."""
        _VARARGS_FUNCTIONS = {
            "GetString",        
            "d",                
            "df",               
            "zo_strformat",     
        }
        for name in _VARARGS_FUNCTIONS:
            fn = reg.get_function(name)
            if fn:
                fn.has_varargs = True

    def _register_builtins(self, reg: Registry) -> None:
        for name in LUA_BUILTIN_GLOBALS:
            reg.add_name(name)
        for name in LUA_KEYWORDS:
            reg.add_name(name)
        for name in ESO_ZO_WRAPPERS:
            reg.add_name(name)
        for name in ESO_STRING_EXTENSIONS:
            reg.add_name(name)

    def _extract_functions(self, reg: Registry, filepath: pathlib.Path) -> None:
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        rel = str(filepath.relative_to(filepath.parents[3])) if len(filepath.parents) > 3 else filepath.name

        for match in self._FUNC_DEF_RE.finditer(source):
            name = match.group(1)
            params_str = match.group(2).strip()
            params = self._parse_params(params_str)
            if self._is_public_api(name):
                fn = Function(
                    name=name,
                    params=[Param(name=p) for p in params],
                    min_params=sum(1 for p in params if "?" not in p),
                    has_varargs="..." in params_str,
                    source_file=rel,
                )
                reg.add_function(fn)

        for match in self._METHOD_DEF_RE.finditer(source):
            table = match.group(1)
            method = match.group(2)
            params_str = match.group(3).strip()
            full_name = f"{table}:{method}"
            params = self._parse_params(params_str)
            if self._is_public_api(table):
                fn = Function(
                    name=full_name,
                    params=[Param(name=p) for p in params],
                    min_params=sum(1 for p in params if "?" not in p),
                    has_varargs="..." in params_str,
                    is_method=True,
                    source_file=rel,
                )
                reg.add_function(fn)

        for match in self._GLOBAL_ASSIGN_RE.finditer(source):
            name = match.group(1)
            if self._is_public_api(name) and not reg.is_known(name):
                if "function" not in match.group(0):
                    reg.add_constant(Constant(name=name, source_file=rel))

    def _extract_deprecations(self, reg: Registry, filepath: pathlib.Path) -> None:
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        # Pattern 1: Simple aliases like OLD_NAME = NEW_NAME
        for match in self._DEPRECATED_ALIAS_RE.finditer(source):
            old_name = match.group(1)
            new_name = match.group(2)
            if old_name == new_name:
                continue
            if old_name.startswith("local "):
                continue
            if not self._is_public_api(old_name):
                continue
            reg.add_deprecation(Deprecation(
                old_name=old_name,
                new_name=new_name,
                message=f"'{old_name}' is deprecated; use '{new_name}' instead.",
            ))

        # Pattern 2: Function wrappers like function GetCurrentMoney()
        # Any function defined in an addoncompatibilityaliases file is a
        # deprecated backwards-compat wrapper.
        for match in self._FUNC_DEF_RE.finditer(source):
            old_name = match.group(1)
            if not self._is_public_api(old_name):
                continue
            if reg.is_deprecated(old_name):
                continue
            body = source[match.end():]
            replacement = self._guess_replacement(body)

            reg.add_deprecation(Deprecation(
                old_name=old_name,
                new_name=replacement,
                message=f"'{old_name}' is deprecated; use '{replacement}' instead.",
            ))

    # helpers 

    @staticmethod
    def _parse_params(params_str: str) -> list[str]:
        if not params_str.strip():
            return []
        params = []
        depth = 0
        current = ""
        for ch in params_str:
            if ch == "," and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                if ch in "({[":
                    depth += 1
                elif ch in ")}]":
                    depth -= 1
                current += ch
        if current.strip():
            params.append(current.strip())
        return [p.strip() for p in params if p.strip()]

    @staticmethod
    def _is_public_api(name: str) -> bool:
        if not name:
            return False
        return name[0].isupper() or name.startswith("zo_")

    @staticmethod
    def _guess_replacement(body: str) -> str:
        """Try to guess the replacement API from a wrapper function body.
        Looks for the first function call in the body (excluding 'local')."""
        calls = re.findall(r"(?<!\blocal\s)([A-Z][\w]*)\s*\(", body)
        if calls:
            return calls[0]

        any_call = re.search(r"([A-Za-z_]\w*)\s*\(", body)
        if any_call:
            return any_call.group(1)

        return "unknown"
