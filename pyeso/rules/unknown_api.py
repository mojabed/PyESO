"""Rule: detect calls to unknown/non-existent API functions."""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class UnknownAPIRule(LintRule):
    """Flags function calls to identifiers not in the known ESOUI API."""

    code = "E001"
    description = "Call to unknown API function"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        for call in visitor.function_calls:
            name = call["name"]

            # Skip known APIs
            if db.is_known(name):
                continue

            # Skip Lua builtin module calls like string.format, table.insert
            parts = name.split(".")
            if len(parts) == 2 and parts[0] in ("string", "table", "math", "os", "coroutine", "debug"):
                continue

            # Skip purely lowercase names (likely local helpers)
            if name.islower():
                continue

            # Skip lowerCamelCase that are clearly local helpers
            if name[0].islower():
                continue

            # Skip method calls on local objects (self:Method pattern)
            if ":" in name:
                continue

            # Skip if it's defined locally in this file
            if name in visitor.local_definitions or name in visitor.global_assignments:
                continue

            # Skip if the last segment starts with lowercase (table.method, but method is local)
            segments = name.rsplit(".", 1)
            if len(segments) == 2 and segments[1] and segments[1][0].islower():
                continue

            diagnostics.append(Diagnostic(
                severity=Severity.WARNING,
                message=f"Unknown function '{name}' - not found in ESOUI API surface. "
                        f"This may be a typo or a locally-defined function that should use a different naming convention.",
                file=call["source"],
                line=call["line"],
                code=self.code,
                source_line=name,
            ))

        return diagnostics
