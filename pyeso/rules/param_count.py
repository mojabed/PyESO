"""Rule: detect wrong parameter counts in API function calls.

ESO Lua conventions: trailing parameters are often optional even when not
documented as nilable. This rule is conservative — it only flags clearly
wrong calls (0 args when 1+ required, or args exceeding max by >1).
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class ParamCountRule(LintRule):
    """Flags function calls with clearly wrong number of arguments."""

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

            # Only flag too-few-args when truly egregious:
            # - 0 args given but function requires at least 1
            # - Fewer than half the required minimum params
            if arg_count < expected_min:
                if arg_count == 0 and expected_min >= 1:
                    diagnostics.append(Diagnostic(
                        severity=Severity.WARNING,
                        message=(
                            f"'{name}' expects at least {expected_min} argument(s), "
                            f"but none were provided."
                        ),
                        file=call["source"],
                        line=call["line"],
                        code=self.code,
                        source_line=name,
                    ))
                elif expected_min >= 3 and arg_count < expected_min / 2:
                    diagnostics.append(Diagnostic(
                        severity=Severity.WARNING,
                        message=(
                            f"'{name}' expects at least {expected_min} argument(s), "
                            f"but only {arg_count} were provided."
                        ),
                        file=call["source"],
                        line=call["line"],
                        code=self.code,
                        source_line=name,
                    ))

            # Only flag too-many-args when >1 extra (ESO functions accept extra args)
            elif not sig.has_varargs and arg_count > expected_max + 1:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=(
                        f"'{name}' expects at most {expected_max} argument(s), "
                        f"but {arg_count} were provided."
                    ),
                    file=call["source"],
                    line=call["line"],
                    code=self.code,
                    source_line=name,
                ))

        return diagnostics
