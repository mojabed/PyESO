from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class MethodValidationRule(LintRule):
    """Validates object method calls against the ESOUI Object API."""

    code = "W006"
    description = "Unknown or incorrect object method call"

    # Known ESOUI singleton globals that have their methods validated by other rules
    _SKIP_SOURCES = {
        "EVENT_MANAGER", "CALLBACK_MANAGER", "SCENE_MANAGER",
        "ANIMATION_MANAGER", "KEYBIND_STRIP", "CHAT_ROUTER",
        "SCREEN_NARRATION_MANAGER", "SYSTEMS",
    }

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []

        for call in visitor.function_calls:
            name = call["name"]
            if ":" not in name:
                continue

            source, method = name.split(":", 1)
            line = call["line"]
            source_path = call["source"]
            arg_count = call["arg_count"]

            if source in self._SKIP_SOURCES:
                continue
            if db.is_known(name):
                continue
            if source == "self":
                continue

            if db.is_known_method(method):
                sig = db.find_method(method)
                if sig:
                    expected_min = sig.min_params
                    user_args = arg_count - 1

                    # Only flag when clearly wrong (0 args for 1+ required,
                    # or fewer than half the minimum)
                    if user_args < expected_min:
                        if user_args == 0 and expected_min >= 1:
                            diagnostics.append(Diagnostic(
                                severity=Severity.WARNING,
                                message=(
                                    f"'{method}' expects at least {expected_min} "
                                    f"argument(s), but none were provided."
                                ),
                                file=source_path,
                                line=line,
                                code=self.code,
                                source_line=name,
                            ))
                        elif expected_min >= 3 and user_args < expected_min / 2:
                            diagnostics.append(Diagnostic(
                                severity=Severity.WARNING,
                                message=(
                                    f"'{method}' expects at least {expected_min} "
                                    f"argument(s), but {user_args} were provided."
                                ),
                                file=source_path,
                                line=line,
                                code=self.code,
                                source_line=name,
                            ))
                    elif not sig.has_varargs and user_args > len(sig.params) + 1:
                        diagnostics.append(Diagnostic(
                            severity=Severity.WARNING,
                            message=(
                                f"'{method}' expects at most {len(sig.params)} "
                                f"argument(s), but {user_args} were provided."
                            ),
                            file=source_path,
                            line=line,
                            code=self.code,
                            source_line=name,
                        ))
                continue

            if source[0].isupper() and not db.is_known(source):
                continue

            if self._looks_like_api_method(method):
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=(
                        f"Unknown method '{method}' — not found in ESOUI Object API. "
                        f"Verify the method name or object type."
                    ),
                    file=source_path,
                    line=line,
                    code=self.code,
                    source_line=name,
                ))

        return diagnostics

    @staticmethod
    def _looks_like_api_method(method: str) -> bool:
        """Heuristic: does this method name look like it's trying to call
        an ESOUI API method? PascalCase methods starting with Set/Get/Is/Are
        are strong indicators."""
        if not method:
            return False
        prefixes = (
            "Set", "Get", "Is", "Are", "Has", "Can", "Should",
            "Register", "Unregister", "Add", "Remove", "Clear",
            "Show", "Hide", "Toggle", "Enable", "Disable",
            "Update", "Refresh", "Create", "Destroy",
        )
        return any(method.startswith(p) for p in prefixes)
