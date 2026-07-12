"""LUA AST visitor for extracting function calls and references from addon source."""

from __future__ import annotations

import pathlib
from typing import Any, Optional

from luaparser import ast
from luaparser.astnodes import (
    Assign,
    Call,
    Index,
    Invoke,
    LocalAssign,
    LocalFunction,
    Name,
    Node,
    String,
)


class LuaCallVisitor(ast.ASTVisitor):
    def __init__(self, source_path: pathlib.Path | str = "<input>") -> None:
        super().__init__()
        self.source_path = str(source_path)
        self.function_calls: list[dict[str, Any]] = []      # {name, arg_count, line, source, args}
        self.local_definitions: dict[str, int] = {}           # name -> line
        self.global_assignments: dict[str, int] = {}          # name -> line (non-local)
        self.variable_references: list[dict[str, Any]] = []   # {name, line, source}
        self.string_literals: list[dict[str, Any]] = []       # {value, line, source}
        self._assign_targets: set[str] = set()               # track current assignment targets

    #  Method calls: obj:Method(args)

    def visit_Invoke(self, node: Invoke) -> None:
        """Record a method call like obj:Method()."""
        source_name = self._resolve_name(node.source)
        method_name = self._resolve_name(node.func)
        args = node.args or []
        line = getattr(node, "line", 0) or 0

        if source_name and method_name:
            full_name = f"{source_name}:{method_name}"
            self.function_calls.append({
                "name": full_name,
                "arg_count": len(args) + 1,
                "line": line,
                "source": self.source_path,
                "args": [self._resolve_arg_value(a) for a in args],
            })

    #  Regular function calls: Func(args) 

    def visit_Call(self, node: Call) -> None:
        """Record a regular function call."""
        func_name = self._resolve_name(node.func)
        args = node.args or []
        line = getattr(node, "line", 0) or 0

        if func_name:
            self.function_calls.append({
                "name": func_name,
                "arg_count": len(args),
                "line": line,
                "source": self.source_path,
                "args": [self._resolve_arg_value(a) for a in args],
            })

        for arg in args:
            self._collect_references(arg, line)

    #  Local definitions 

    def visit_LocalAssign(self, node: LocalAssign) -> None:
        """Record local variable definitions."""
        line = getattr(node, "line", 0) or 0
        for target in node.targets or []:
            name = self._resolve_name(target)
            if name and self._is_trackable(name):
                self.local_definitions[name] = line
                self._assign_targets.add(name)

        for value in node.values or []:
            self._collect_references(value, line)

    def visit_LocalFunction(self, node: LocalFunction) -> None:
        """Record local function definitions (they shadow globals)."""
        line = getattr(node, "line", 0) or 0
        name = self._resolve_name(node.name)
        if name and self._is_trackable(name):
            self.local_definitions[name] = line
            self._assign_targets.add(name)

    #  Global (non-local) assignments 

    def visit_Assign(self, node: Assign) -> None:
        """Record global assignments and variable references on the RHS."""
        line = getattr(node, "line", 0) or 0
        for target in node.targets or []:
            name = self._resolve_name(target)
            if name and self._is_trackable(name):
                self.global_assignments[name] = line
                self._assign_targets.add(name)

        for value in node.values or []:
            self._collect_references(value, line)

    #  String literals 
    def visit_String(self, node: String) -> None:
        """Record string literals for localization checking."""
        line = getattr(node, "line", 0) or 0
        value = node.s
        if value and len(value) > 1:  # skip empty/single-char strings
            self.string_literals.append({
                "value": value,
                "line": line,
                "source": self.source_path,
            })

    #  Helpers 

    def _collect_references(self, node: Any, line: int) -> None:
        """Recursively collect Name references from a subtree."""
        if node is None:
            return
        if isinstance(node, Name):
            name = node.id
            if self._is_trackable(name) and name not in self._assign_targets:
                self.variable_references.append({
                    "name": name,
                    "line": line,
                    "source": self.source_path,
                })
        elif isinstance(node, Index):
            self._collect_references(getattr(node, "value", None), line)
            self._collect_references(getattr(node, "idx", None), line)
        elif isinstance(node, (list, tuple)):
            for child in node:
                self._collect_references(child, line)
        elif hasattr(node, "args"):
            for child in (node.args or []):
                self._collect_references(child, line)
        elif hasattr(node, "values"):
            for child in (node.values or []):
                self._collect_references(child, line)

    @staticmethod
    def _resolve_name(node: Node) -> Optional[str]:
        """Resolve a node to its full dotted/method name string."""
        if node is None:
            return None
        if isinstance(node, Name):
            return node.id
        if isinstance(node, Index):
            left = LuaCallVisitor._resolve_name(node.value)
            idx_name = LuaCallVisitor._resolve_name(node.idx) if hasattr(node, "idx") else None
            if left and idx_name:
                return f"{left}.{idx_name}"
            return left
        if isinstance(node, String):
            return node.s
        return None

    @staticmethod
    def _resolve_arg_value(node: Node) -> Optional[str]:
        """Resolve a simple argument to its string value.
        Returns the string for String nodes, the id for Name nodes, or None."""
        if node is None:
            return None
        if isinstance(node, String):
            val = node.s
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace")
            return val
        if isinstance(node, Name):
            return node.id
        return None

    @staticmethod
    def _is_trackable(name: str) -> bool:
        """Check if a name should be tracked (uppercase or zo_ prefix)."""
        return bool(name and (name[0].isupper() or name.startswith("zo_")))


def parse_lua_file(filepath: pathlib.Path | str) -> Optional[Node]:
    """Parse a LUA file and return its AST (Chunk node), or None on parse error."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        return ast.parse(source)
    except Exception:
        return None


def collect_calls(filepath: pathlib.Path | str) -> LuaCallVisitor:
    """Parse a LUA file and collect all function calls."""
    tree = parse_lua_file(filepath)
    visitor = LuaCallVisitor(filepath)
    if tree:
        visitor.visit(tree)
    return visitor


