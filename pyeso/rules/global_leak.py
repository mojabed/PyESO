"""Rule: detect global variable leakage (missing 'local' keyword).

In ESO's shared Lua environment, accidentally creating a global variable
can overwrite another addon's variable or leak into the global namespace.
This rule flags assignments to PascalCase names that are not prefixed with
'local' and are not known ESOUI APIs.
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


# Names that are conventionally used as addon level globals
_CONVENTION_GLOBALS = {
    "ADDON_NAME", "ADDON", "AUTHOR", "VERSION",
}


class GlobalLeakRule(LintRule):
    """Flags non-local assignments that create globals."""

    code = "W003"
    description = "Assignment without 'local' creates a global variable"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        for name, line in visitor.global_assignments.items():
            if db.is_known(name):
                continue
            if name in _CONVENTION_GLOBALS:
                continue
            if name in visitor.local_definitions:
                continue

            diagnostics.append(Diagnostic(
                severity=Severity.WARNING,
                message=(
                    f"'{name}' is assigned without 'local' — this creates "
                    f"a global variable. Did you forget 'local {name} = ...'?"
                ),
                file=visitor.source_path,
                line=line,
                code=self.code,
                source_line=name,
            ))

        return diagnostics
