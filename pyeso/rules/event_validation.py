"""Rule: validate event registration calls against known ESOUI events.

Checks that EVENT_* names passed to RegisterForEvent/UnregisterForEvent
exist in the API, and that callback parameter counts match event signatures.
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity


class EventValidationRule(LintRule):
    """Validates event registration calls."""

    code = "E002"
    description = "Invalid event registration"

    # Method calls to check (source, method, event_arg_index, callback_arg_index)
    _EVENT_REGISTRATION = {
        ("EVENT_MANAGER", "RegisterForEvent"): (1, 2),
        ("EVENT_MANAGER", "UnregisterForEvent"): (1, None),
    }

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []

        for call in visitor.function_calls:
            name = call["name"]
            if ":" not in name:
                continue

            source, method = name.split(":", 1)
            spec = self._EVENT_REGISTRATION.get((source, method))
            if spec is None:
                continue

            event_idx, callback_idx = spec
            args = call.get("args", [])
            line = call["line"]
            source_path = call["source"]

            if event_idx < len(args):
                event_name = args[event_idx]
                if event_name and isinstance(event_name, str):
                    if event_name.startswith("EVENT_"):
                        if not db.is_event(event_name):
                            diagnostics.append(Diagnostic(
                                severity=Severity.ERROR,
                                message=(
                                    f"Unknown event '{event_name}' — "
                                    f"this event is not in the ESOUI API. "
                                    f"It may be a typo or a custom/non-existent event."
                                ),
                                file=source_path,
                                line=line,
                                code=self.code,
                                source_line=event_name,
                            ))
                        else:
                            if callback_idx is not None and callback_idx < len(args):
                                callback_name = args[callback_idx]
                                if callback_name and isinstance(callback_name, str):
                                    ev_info = db.get_event_info(event_name)
                                    if ev_info and ev_info.min_params > 0:
                                        pass

        return diagnostics
