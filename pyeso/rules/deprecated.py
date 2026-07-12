"""Rule: detect usage of deprecated ESOUI APIs."""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class DeprecatedAPIRule(LintRule):
    """Flags usage of deprecated ESOUI API functions and variables."""

    code = "W002"
    description = "Usage of deprecated API"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        for call in visitor.function_calls:
            name = call["name"]
            if db.is_deprecated(name):
                dep = db.get_deprecated(name)
                if dep:
                    msg = dep.message or f"'{name}' is deprecated; use '{dep.new_name}' instead."
                    diagnostics.append(Diagnostic(
                        severity=Severity.WARNING,
                        message=msg,
                        file=call["source"],
                        line=call["line"],
                        code=self.code,
                        source_line=name,
                    ))

        return diagnostics
