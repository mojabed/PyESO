"""Rule: suggest GetString() for hardcoded user-facing strings.

In ESO addons, user-facing text should use GetString(SI_*) for localization
support. Hardcoded English strings won't be translated for non-English clients.
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity

_NON_TEXT_SUBSTRINGS = (
    ".lua", ".xml", ".dds", ".png",
    "http://", "https://",
)

class StringLocalizationRule(LintRule):
    """Suggests GetString() for strings that look like user-facing text."""

    code = "I001"
    description = "Hardcoded string may need GetString() for localization"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        for s in visitor.string_literals:
            value = s["value"]

            # luaparser may return bytes — normalize
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")

            # Skip short / technical strings
            if len(value) < 10:
                continue

            # Skip strings that look like paths or technical identifiers
            val_lower = value.lower()
            if any(p in val_lower for p in _NON_TEXT_SUBSTRINGS):
                continue

            # Skip strings that are purely uppercase/underscore (SI_ constants, etc.)
            if value.replace("_", "").isupper():
                continue

            # Must contain at least one space to be "text-like"
            if " " not in value:
                continue

            # This looks like user-facing text
            display = value[:60] + "..." if len(value) > 60 else value
            diagnostics.append(Diagnostic(
                severity=Severity.INFO,
                message=(
                    f"Hardcoded string '{display}' may need localization. "
                    f"Consider using GetString(SI_*) for non-English client support."
                ),
                file=s["source"],
                line=s["line"],
                code=self.code,
                source_line=value,
            ))

        return diagnostics
