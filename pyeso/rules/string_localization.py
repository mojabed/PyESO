"""Rule: suggest GetString() for hardcoded user facing strings.

In ESO addons, user facing text should use GetString(SI_*) for localization
support. Hardcoded English strings won't be translated for non-English clients.

However, many strings in ESO Lua are NOT localizable by design:
- Debug output: d("msg"), df("fmt", ...)
- Sound IDs: PlaySound("sound_id")
- CVar keys: SetCVar("key", val), GetCVar("key")
- Control/window names: WINDOW_MANAGER:CreateTopLevelWindow("name")
- Saved variable names: ZO_SavedVars:New("name", ...)
- Event registration names: EVENT_MANAGER:RegisterForEvent("name", ...)
- Already-localized: GetString(SI_CONSTANT)
- String formatting: zo_strformat("...", ...)
- File paths, XML names, control virtual paths
"""

from pyeso.registry import Registry
from pyeso.parser.lua_visitor import LuaCallVisitor
from pyeso.rules.base import Diagnostic, LintRule, Severity

# Functions whose string arguments are NEVER localizable text
_NON_LOCALIZABLE_CALLEES = {
    # Debug / logging
    "d", "df",
    # Sound
    "PlaySound",
    # Settings / CVars
    "SetCVar", "GetCVar",
    # Already using GetString
    "GetString",
    # String formatting (already localization-aware)
    "zo_strformat", "zo_iconFormat", "zo_iconFormatInheritColor",
    "zo_iconTextFormat",
}

# Method calls whose string arguments are never localizable
_NON_LOCALIZABLE_METHOD_CALLS = {
    # Event registration — the first string arg is an addon/namespace name
    ("EVENT_MANAGER", "RegisterForEvent"),
    ("EVENT_MANAGER", "UnregisterForEvent"),
    # Saved variables
    ("ZO_SavedVars", "New"),
    ("ZO_SavedVars", "NewAccountWide"),
    ("ZO_SavedVars", "NewCharacterIdSettings"),
    ("ZO_SavedVars", "NewProfile"),
    # Window creation
    ("WINDOW_MANAGER", "CreateTopLevelWindow"),
    ("WINDOW_MANAGER", "CreateControlFromVirtual"),
    ("WINDOW_MANAGER", "CreateControl"),
}

_NON_TEXT_SUBSTRINGS = (
    ".lua", ".xml", ".dds", ".png", ".tga",
    "http://", "https://",
    "/esoui/", "/art/", "/fonts/", "/sounds/",
)


class StringLocalizationRule(LintRule):
    """Suggests GetString() for strings that look like user-facing text."""

    code = "I001"
    description = "Hardcoded string may need GetString() for localization"

    def check(self, visitor: LuaCallVisitor, db: Registry) -> list[Diagnostic]:
        diagnostics = []

        # Build a set of (line, value) pairs that are arguments to
        # non-localizable functions — these should be skipped.
        non_loc_strings: set[tuple[int, str]] = set()
        for call in visitor.function_calls:
            name = call["name"]
            line = call["line"]
            args = call.get("args", [])

            if ":" in name:
                source, method = name.split(":", 1)
                if (source, method) in _NON_LOCALIZABLE_METHOD_CALLS:
                    for arg in args:
                        if isinstance(arg, str):
                            non_loc_strings.add((line, arg))
            elif name in _NON_LOCALIZABLE_CALLEES:
                for arg in args:
                    if isinstance(arg, str):
                        non_loc_strings.add((line, arg))

        for s in visitor.string_literals:
            value = s["value"]
            line = s["line"]

            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")

            # Skip strings that are arguments to non-localizable calls
            if (line, value) in non_loc_strings:
                continue

            # Skip short strings
            if len(value) < 10:
                continue

            val_lower = value.lower()

            # Skip paths and technical identifiers
            if any(p in val_lower for p in _NON_TEXT_SUBSTRINGS):
                continue

            # Skip purely uppercase/underscore (SI_ constants, enums)
            if value.replace("_", "").isupper():
                continue

            # Must contain at least one space to be "text-like"
            if " " not in value:
                continue

            # Skip strings that are obviously format strings (contain %s, %d, etc.)
            if "%" in value and any(
                value.find(f"%{c}") != -1
                for c in "sdfgixuoeEc"
            ):
                continue

            # Skip very repetitive/single-char patterns (not text)
            unique_chars = len(set(val_lower.replace(" ", "")))
            if unique_chars <= 3 and len(value) > 10:
                continue

            display = value[:60] + "..." if len(value) > 60 else value
            diagnostics.append(Diagnostic(
                severity=Severity.INFO,
                message=(
                    f"Hardcoded string '{display}' may need localization. "
                    f"Consider using GetString(SI_*) for non-English client support."
                ),
                file=s["source"],
                line=line,
                code=self.code,
                source_line=value,
            ))

        return diagnostics
