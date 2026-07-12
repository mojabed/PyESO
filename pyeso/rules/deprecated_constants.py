"""Rule: detect usage of deprecated ESOUI constants and variables.

Extends deprecation detection to cover constant/variable references,
not just function calls (which W002 already handles).
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class DeprecatedConstantRule(LintRule):
    """Flags references to deprecated ESOUI constants and variables."""

    code = "W005"
    description = "Reference to deprecated constant or variable"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        # Check variable references (e.g. local x = NAMEPLATE_CHOICE_OFF)
        for ref in visitor.variable_references:
            name = ref["name"]
            if db.is_deprecated(name):
                dep = db.get_deprecated(name)
                if dep:
                    diagnostics.append(Diagnostic(
                        severity=Severity.WARNING,
                        message=dep.message or (
                            f"'{name}' is deprecated; use '{dep.new_name}' instead."
                        ),
                        file=ref["source"],
                        line=ref["line"],
                        code=self.code,
                        source_line=name,
                    ))

        return diagnostics
