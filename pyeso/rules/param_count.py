"""Rule: detect wrong parameter counts in API function calls."""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class ParamCountRule(LintRule):
    """Flags function calls with wrong number of arguments."""

    code = "W001"
    description = "Function call has unexpected number of arguments"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        for call in visitor.function_calls:
            name = call["name"]
            sig = db.get_signature(name)
            if sig is None:
                continue

            arg_count = call["arg_count"]
            expected_min = sig.min_params
            expected_max = len(sig.params) if not sig.has_varargs else float("inf")

            if arg_count < expected_min:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=f"'{name}' expects at least {expected_min} argument(s), but {arg_count} were provided.",
                    file=call["source"],
                    line=call["line"],
                    code=self.code,
                    source_line=name,
                ))
            elif arg_count > expected_max and not sig.has_varargs:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=f"'{name}' expects at most {expected_max} argument(s), but {arg_count} were provided.",
                    file=call["source"],
                    line=call["line"],
                    code=self.code,
                    source_line=name,
                ))

        return diagnostics
