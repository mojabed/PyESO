"""ESOUI API Extractor - builds API database from ESOUI source code.

Usage:
    from pyeso.api.extractor import ESOUIExtractor
    extractor = ESOUIExtractor()
    db = extractor.extract_from_directory("/path/to/esoui/esoui")
"""

from __future__ import annotations

import pathlib
import re
from typing import Optional

from pyeso.api.builtins import (
    ESO_STRING_EXTENSIONS,
    ESO_ZO_WRAPPERS,
    LUA_BUILTIN_GLOBALS,
    LUA_KEYWORDS,
)
from pyeso.api.db import APIDatabase, FunctionSignature


class ESOUIExtractor:
    """Extracts API surface information from ESOUI source files."""

    # Regex for global function definitions
    #   function SomeName(params...)  or  function some.table.Func(params...)
    _FUNC_DEF_RE = re.compile(
        r"^\s*function\s+([A-Za-z_][\w.]*[A-Za-z_])\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Regex for global assignments
    #   SOME_CONSTANT = 42  or  SomeTable = {}
    _GLOBAL_ASSIGN_RE = re.compile(
        r"^(?!.*\bfunction\b)(?:local\s+)?([A-Z][\w]*)\s*=\s*",
        re.MULTILINE,
    )

    # Regex for deprecated aliases
    #   OldName = NewName  (simple alias)
    _DEPRECATED_ALIAS_RE = re.compile(
        r"^([A-Z][\w.]*)\s*=\s*([A-Z][\w.]+)\s*$",
        re.MULTILINE,
    )

    # Regex for functions defined as table fields
    #   function SomeTable:Method(params...)
    _METHOD_DEF_RE = re.compile(
        r"^\s*function\s+([A-Za-z_][\w.]*):(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    def __init__(self) -> None:
        self._db = APIDatabase()

    def build_default_database(self) -> APIDatabase:
        """Build a default database with standard Lua + ESO builtins.

        Does not require ESOUI source; loads the seed API definitions
        that ship with PyESO.
        """
        self._db = APIDatabase()
        self._register_builtins()
        self._register_seed_api()
        return self._db

    def extract_from_directory(self, esoui_dir: str | pathlib.Path) -> APIDatabase:
        """Extract API surface from an ESOUI source directory."""
        self.build_default_database()
        root = pathlib.Path(esoui_dir)

        if not root.exists():
            raise FileNotFoundError(f"ESOUI directory not found: {esoui_dir}")

        # Process alias files first (they document deprecations)
        for alias_file in root.rglob("*addoncompatibilityaliases*.lua"):
            self._extract_deprecations(alias_file)

        # Process all .lua files for function definitions
        for lua_file in root.rglob("*.lua"):
            self._extract_functions(lua_file)

        return self._db

    def _register_builtins(self) -> None:
        """Register standard Lua and ESO builtins."""
        for name in LUA_BUILTIN_GLOBALS:
            self._db.register_builtin(name)
        for name in LUA_KEYWORDS:
            self._db.register_builtin(name)
        for name in ESO_ZO_WRAPPERS:
            self._db.register_builtin(name)
        for name in ESO_STRING_EXTENSIONS:
            self._db.register_builtin(name)

    def _register_seed_api(self) -> None:
        """Register the curated seed API (common ESO C-side and Lua-side APIs).

        These are functions called from Lua but defined in the C engine,
        so they cannot be extracted from source.
        """
        seeded = _SEED_API_FUNCTIONS
        for entry in seeded:
            name = entry["name"]
            params = entry.get("params", [])
            min_params = entry.get("min_params", len(params))
            has_varargs = entry.get("varargs", False)
            is_method = entry.get("method", False)

            sig = FunctionSignature(
                name=name,
                params=params,
                min_params=min_params,
                has_varargs=has_varargs,
                is_method=is_method,
            )
            self._db.register_function(sig)

        # Register known deprecated APIs from seed data
        for entry in _SEED_DEPRECATED:
            self._db.register_deprecated(
                old_name=entry["old"],
                new_name=entry["new"],
                message=entry.get("message", ""),
            )

        # Register known global variables/constants
        for name in _SEED_VARIABLES:
            self._db.register_variable(name)

    def _extract_functions(self, filepath: pathlib.Path) -> None:
        """Extract global function definitions from a LUA file."""
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        # Find global function definitions
        for match in self._FUNC_DEF_RE.finditer(source):
            name = match.group(1)
            params_str = match.group(2).strip()
            params = self._parse_params(params_str)
            # Skip local/small functions, focus on ZO_* and CamelCase globals
            if self._is_public_api(name):
                sig = FunctionSignature(
                    name=name,
                    params=params,
                    min_params=sum(1 for p in params if "?" not in p),
                    has_varargs="..." in params_str,
                )
                self._db.register_function(sig)

        # Find method definitions (SomeTable:Method)
        for match in self._METHOD_DEF_RE.finditer(source):
            table = match.group(1)
            method = match.group(2)
            params_str = match.group(3).strip()
            full_name = f"{table}:{method}"
            params = self._parse_params(params_str)
            if self._is_public_api(table):
                sig = FunctionSignature(
                    name=full_name,
                    params=params,
                    min_params=sum(1 for p in params if "?" not in p),
                    has_varargs="..." in params_str,
                    is_method=True,
                )
                self._db.register_function(sig)

        # Find non-function global assignments (for variable registration)
        for match in self._GLOBAL_ASSIGN_RE.finditer(source):
            name = match.group(1)
            if self._is_public_api(name) and name not in self._db._known_names:
                # Check it's not actually a function definition
                if "function" not in match.group(0):
                    self._db.register_variable(name)

    def _extract_deprecations(self, filepath: pathlib.Path) -> None:
        """Extract deprecated API aliases from compatibility files."""
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        # Look for comment blocks about deprecation + alias
        for match in self._DEPRECATED_ALIAS_RE.finditer(source):
            old_name = match.group(1)
            new_name = match.group(2)

            # Skip obvious non-deprecation assignments
            if old_name == new_name:
                continue
            if old_name.startswith("local "):
                continue
            if not self._is_public_api(old_name):
                continue

            self._db.register_deprecated(
                old_name=old_name,
                new_name=new_name,
                message=f"'{old_name}' is deprecated; use '{new_name}' instead.",
            )

    @staticmethod
    def _parse_params(params_str: str) -> list[str]:
        """Parse a LUA parameter list string into individual parameter names."""
        if not params_str.strip():
            return []
        params = []
        depth = 0
        current = ""
        for ch in params_str:
            if ch == "," and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                if ch in "({[":
                    depth += 1
                elif ch in ")}]":
                    depth -= 1
                current += ch
        if current.strip():
            params.append(current.strip())
        # Clean up param names (remove type hints in comments, etc.)
        cleaned = []
        for p in params:
            # Handle "self" parameter
            p = p.strip()
            if p:
                cleaned.append(p)
        return cleaned

    @staticmethod
    def _is_public_api(name: str) -> bool:
        """Check if a name looks like a public ESOUI API identifier."""
        if not name:
            return False
        # Must start with uppercase or zo_
        if name[0].isupper() or name.startswith("zo_"):
            return True
        return False

# Format: {"name": "...", "params": ["p1", "p2"], "min_params": N, "varargs": bool}
_SEED_API_FUNCTIONS: list[dict] = [
    # --- Unit / Player ---
    {"name": "GetUnitName", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitDisplayName", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitRaceId", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitClassId", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitLevel", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitChampionPoints", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitGender", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitAlliance", "params": ["unitTag"], "min_params": 1},
    {"name": "IsUnitPlayer", "params": ["unitTag"], "min_params": 1},
    {"name": "IsUnitOnline", "params": ["unitTag"], "min_params": 1},
    {"name": "IsUnitGrouped", "params": ["unitTag"], "min_params": 1},
    {"name": "GetUnitPowerInfo", "params": ["unitTag", "powerType"], "min_params": 2},
    {"name": "GetUnitEffectivePower", "params": ["unitTag", "powerType"], "min_params": 2},
    {"name": "GetUnitPowerMax", "params": ["unitTag", "powerType"], "min_params": 2},
    {"name": "GetNumCombatEvents", "params": [], "min_params": 0},
    {"name": "GetPlayerBuffInfo", "params": ["buffIndex"], "min_params": 1},
    {"name": "GetNumBuffs", "params": ["unitTag"], "min_params": 1},
    {"name": "GetBuffInfo", "params": ["unitTag", "buffIndex"], "min_params": 2},
    {"name": "GetAbilityName", "params": ["abilityId"], "min_params": 1},
    {"name": "GetAbilityDescription", "params": ["abilityId"], "min_params": 1},
    {"name": "GetAbilityIcon", "params": ["abilityId"], "min_params": 1},
    {"name": "GetAbilityDuration", "params": ["abilityId"], "min_params": 1},

    # --- Inventory / Items ---
    {"name": "GetItemLink", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemName", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemInfo", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemLinkName", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkInfo", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkItemType", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkQuality", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkItemStyle", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkTraitInfo", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkEnchantInfo", "params": ["itemLink"], "min_params": 1},
    {"name": "GetItemLinkSetInfo", "params": ["itemLink"], "min_params": 1},
    {"name": "GetNumBagUsedSlots", "params": ["bagId"], "min_params": 1},
    {"name": "GetBagSize", "params": ["bagId"], "min_params": 1},
    {"name": "IsItemStolen", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemCreatorName", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemCondition", "params": ["bagId", "slotIndex"], "min_params": 2},
    {"name": "GetItemMaxCondition", "params": ["bagId", "slotIndex"], "min_params": 2},

    # --- Currency ---
    {"name": "GetCurrencyAmount", "params": ["currencyType", "currencyLocation"], "min_params": 2},
    {"name": "GetCurrencyName", "params": ["currencyType", "plural", "upper"], "min_params": 1},
    {"name": "IsCurrencyValid", "params": ["currencyType"], "min_params": 1},

    # --- Map / World ---
    {"name": "GetMapName", "params": [], "min_params": 0},
    {"name": "GetMapType", "params": [], "min_params": 0},
    {"name": "GetCurrentMapIndex", "params": [], "min_params": 0},
    {"name": "GetCurrentZoneIndex", "params": [], "min_params": 0},
    {"name": "GetZoneId", "params": ["zoneIndex"], "min_params": 1},
    {"name": "GetZoneNameByIndex", "params": ["zoneIndex"], "min_params": 1},
    {"name": "GetMapInfoByIndex", "params": ["mapIndex"], "min_params": 1},
    {"name": "GetMapNumTiles", "params": [], "min_params": 0},
    {"name": "SetMapToPlayerLocation", "params": [], "min_params": 0},
    {"name": "GetPlayerLocationName", "params": [], "min_params": 0},
    {"name": "GetPlayerRawName", "params": [], "min_params": 0},
    {"name": "GetDisplayName", "params": [], "min_params": 0},
    {"name": "GetUnitWorldPosition", "params": ["unitTag"], "min_params": 1},
    {"name": "GetMapPlayerPosition", "params": ["unitTag"], "min_params": 1},

    # --- Quest / Journal ---
    {"name": "GetJournalQuestName", "params": ["questIndex"], "min_params": 1},
    {"name": "GetJournalQuestDescription", "params": ["questIndex"], "min_params": 1},
    {"name": "GetNumJournalQuests", "params": [], "min_params": 0},
    {"name": "IsQuestComplete", "params": ["questId"], "min_params": 1},
    {"name": "GetCompletedQuestInfo", "params": ["completedIndex"], "min_params": 1},
    {"name": "GetQuestName", "params": ["questId"], "min_params": 1},

    # --- Achievement ---
    {"name": "GetAchievementInfo", "params": ["achievementId"], "min_params": 1},
    {"name": "GetAchievementName", "params": ["achievementId"], "min_params": 1},
    {"name": "GetAchievementDescription", "params": ["achievementId"], "min_params": 1},
    {"name": "IsAchievementComplete", "params": ["achievementId"], "min_params": 1},
    {"name": "GetNumCompletedAchievements", "params": [], "min_params": 0},

    # --- Skill / Ability ---
    {"name": "GetSkillLineInfo", "params": ["skillType", "skillLineIndex"], "min_params": 2},
    {"name": "GetSkillAbilityInfo", "params": ["skillType", "skillLineIndex", "abilityIndex"], "min_params": 3},
    {"name": "GetNumSkillLines", "params": ["skillType"], "min_params": 1},
    {"name": "GetNumSkillAbilities", "params": ["skillType", "skillLineIndex"], "min_params": 2},
    {"name": "GetActiveAbilitySlotInfo", "params": ["slotIndex"], "min_params": 1},
    {"name": "GetSlotBoundId", "params": ["slotIndex"], "min_params": 1},

    # --- Guild ---
    {"name": "GetNumGuilds", "params": [], "min_params": 0},
    {"name": "GetGuildId", "params": ["guildIndex"], "min_params": 1},
    {"name": "GetGuildName", "params": ["guildId"], "min_params": 1},
    {"name": "GetGuildNumMembers", "params": ["guildId"], "min_params": 1},
    {"name": "GetGuildMemberInfo", "params": ["guildId", "memberIndex"], "min_params": 2},
    {"name": "GetGuildMemberCharacterInfo", "params": ["guildId", "memberIndex"], "min_params": 2},

    # --- Group ---
    {"name": "GetGroupSize", "params": [], "min_params": 0},
    {"name": "GetGroupMemberInfo", "params": ["memberIndex"], "min_params": 1},
    {"name": "GetGroupLeaderName", "params": [], "min_params": 0},
    {"name": "IsUnitGroupLeader", "params": ["unitTag"], "min_params": 1},
    {"name": "GetNumGroupMembers", "params": [], "min_params": 0},

    # --- Chat / Messaging ---
    {"name": "GetChatCategoryName", "params": ["categoryIndex"], "min_params": 1},
    {"name": "GetChatContainerInfo", "params": ["containerId"], "min_params": 1},
    {"name": "SendChatMessage", "params": ["text", "channel"], "min_params": 1},
    {"name": "StartChatInput", "params": ["text", "channel"], "min_params": 0},

    # --- Settings ---
    {"name": "GetSetting_Bool", "params": ["settingType", "settingId"], "min_params": 2},
    {"name": "GetSetting_Int", "params": ["settingType", "settingId"], "min_params": 2},
    {"name": "GetSetting_String", "params": ["settingType", "settingId"], "min_params": 2},
    {"name": "SetSetting", "params": ["settingType", "settingId", "value"], "min_params": 3},

    # --- Events ---
    {"name": "EVENT_MANAGER", "params": [], "min_params": 0},
    {"name": "EVENT_ADD_ON_LOADED", "params": [], "min_params": 0},
    {"name": "RegisterForEvent", "params": ["eventName", "eventCode", "callback"], "min_params": 3},
    {"name": "UnregisterForEvent", "params": ["eventName"], "min_params": 1},

    # --- Saved Variables ---
    {"name": "ZO_SavedVars", "params": [], "min_params": 0},

    # --- UI / Controls ---
    {"name": "GetWindowManager", "params": [], "min_params": 0},
    {"name": "GetAnimationManager", "params": [], "min_params": 0},
    {"name": "GetEventManager", "params": [], "min_params": 0},
    {"name": "GetControlByName", "params": ["name"], "min_params": 1},
    {"name": "GuiRoot", "params": [], "min_params": 0},

    # --- Strings / Localization ---
    {"name": "GetString", "params": ["stringConstant", "..."], "min_params": 1, "varargs": True},
    {"name": "GetFontStyleString", "params": ["style"], "min_params": 1},
    {"name": "SI_FORMAT_BULLET_TEXT", "params": [], "min_params": 0},
    {"name": "SI_FORMAT_BULLET_SPACING", "params": [], "min_params": 0},

    # --- Time ---
    {"name": "GetSecondsSinceMidnight", "params": [], "min_params": 0},
    {"name": "GetFrameTimeSeconds", "params": [], "min_params": 0},
    {"name": "GetGameTimeMilliseconds", "params": [], "min_params": 0},
    {"name": "GetTimeString", "params": [], "min_params": 0},
    {"name": "GetDate", "params": [], "min_params": 0},
    {"name": "GetTimeStamp", "params": [], "min_params": 0},

    # --- Combat ---
    {"name": "GetCombatEventInfo", "params": ["eventIndex"], "min_params": 1},

    # --- Crafting ---
    {"name": "GetTradeskillType", "params": [], "min_params": 0},

    # --- Misc ---
    {"name": "IsInGamepadPreferredMode", "params": [], "min_params": 0},
    {"name": "IsInKeyboardMode", "params": [], "min_params": 0},
    {"name": "PlaySound", "params": ["soundId"], "min_params": 1},
    {"name": "GetUIMousePosition", "params": [], "min_params": 0},
    {"name": "d", "params": ["..."], "min_params": 0, "varargs": True},
    {"name": "df", "params": ["formatter", "..."], "min_params": 1, "varargs": True},
    {"name": "zo_strformat", "params": ["formatString", "..."], "min_params": 1, "varargs": True},
    {"name": "zo_iconFormat", "params": ["path", "width", "height"], "min_params": 3},
    {"name": "zo_iconFormatInheritColor", "params": ["path", "width", "height"], "min_params": 3},
    {"name": "zo_iconTextFormat", "params": ["path", "width", "height", "text"], "min_params": 4},
]

# Deprecated APIs (old -> new)
_SEED_DEPRECATED: list[dict] = [
    # Veteran Rank -> Champion
    {"old": "GetUnitVeteranRank", "new": "GetUnitChampionPoints"},
    {"old": "IsUnitVeteran", "new": "IsUnitChampion"},
    {"old": "GetVeteranRankIcon", "new": "ZO_GetChampionPointsIcon"},
    {"old": "GetMaxVeteranRank", "new": "GetChampionPointsPlayerProgressionCap"},
    # Alliance -> Team (Battlegrounds)
    {"old": "GetUnitBattlegroundAlliance", "new": "GetUnitBattlegroundTeam"},
    {"old": "GetBattlegroundAllianceName", "new": "GetBattlegroundTeamName"},
    # Currency
    {"old": "GetCurrentMoney", "new": "GetCurrencyAmount(CURT_MONEY, CURRENCY_LOCATION_CHARACTER)"},
    {"old": "GetBankedMoney", "new": "GetCurrencyAmount(CURT_MONEY, CURRENCY_LOCATION_BANK)"},
    {"old": "GetAlliancePoints", "new": "GetCurrencyAmount(CURT_ALLIANCE_POINTS, CURRENCY_LOCATION_CHARACTER)"},
    # Weapon Power -> Weapon and Spell Damage
    {"old": "STAT_WEAPON_POWER", "new": "STAT_WEAPON_AND_SPELL_DAMAGE"},
    # Activity Finder
    {"old": "GetCurrentLFGActivity", "new": "GetCurrentLFGActivityId"},
    {"old": "GetNumLFGOptions", "new": "GetNumActivitiesByType"},
    # Nameplate
    {"old": "NAMEPLATE_CHOICE_OFF", "new": "NAMEPLATE_CHOICE_NEVER"},
    {"old": "NAMEPLATE_CHOICE_ON", "new": "NAMEPLATE_CHOICE_ALWAYS"},
    # Map
    {"old": "ZO_WorldMapPins", "new": "ZO_WorldMapPins_Manager"},
    {"old": "ZO_MapLocations", "new": "ZO_MapLocationPins_Manager"},
    # Money
    {"old": "MONEY_INPUT", "new": "CURRENCY_INPUT"},
    # Resurrect
    {"old": "RESURRECT_FAILURE_REASON_ALREADY_CONSIDERING", "new": "RESURRECT_RESULT_ALREADY_CONSIDERING"},
    # Traits
    {"old": "ITEM_TRAIT_TYPE_ARMOR_EXPLORATION", "new": "ITEM_TRAIT_TYPE_ARMOR_PROSPEROUS"},
]

# Known global variables (tables, constants) that aren't callable
_SEED_VARIABLES: list[str] = [
    "WINDOW_MANAGER", "ANIMATION_MANAGER", "CALLBACK_MANAGER",
    "SCENE_MANAGER", "CHAT_ROUTER", "KEYBIND_STRIP",
    "SCREEN_NARRATION_MANAGER", "SYSTEMS",
    "ZO_PI", "ZO_TWO_PI", "ZO_HALF_PI",
    "MOUSE_BUTTON_INDEX_LEFT", "MOUSE_BUTTON_INDEX_RIGHT",
    "INTERACTION_TRIBUTE", "INTERACTION_NONE",
    "TEXT_ALIGN_LEFT", "TEXT_ALIGN_CENTER", "TEXT_ALIGN_RIGHT",
    "TOP", "BOTTOM", "LEFT", "RIGHT", "CENTER",
    "ANCHOR_CONSTRAINS_XY", "ANCHOR_CONSTRAINS_X", "ANCHOR_CONSTRAINS_Y",
    "CT_TOPLEVELCONTROL", "CT_LABEL", "CT_TEXTURE", "CT_BUTTON",
    "CURRENCY_LOCATION_CHARACTER", "CURRENCY_LOCATION_BANK",
    "CURRENCY_LOCATION_GUILD_BANK", "CURRENCY_LOCATION_ACCOUNT",
    "CURT_MONEY", "CURT_ALLIANCE_POINTS", "CURT_TELVAR_STONES",
    "BAG_BACKPACK", "BAG_BANK", "BAG_GUILDBANK", "BAG_WORN",
    "EVENT_ADD_ON_LOADED", "EVENT_PLAYER_ACTIVATED",
    "SETTING_TYPE_ACCESSIBILITY", "SETTING_TYPE_UI", "SETTING_TYPE_GAMEPLAY",
    "SCENE_SHOWING", "SCENE_SHOWN", "SCENE_HIDING", "SCENE_HIDDEN",
    "SCENE_FRAGMENT_SHOWING", "SCENE_FRAGMENT_SHOWN",
    "SCENE_FRAGMENT_HIDING", "SCENE_FRAGMENT_HIDDEN",
    "MAP_MODE_AVA_RESPAWN",
    "SI_OK", "SI_DIALOG_CANCEL", "SI_DIALOG_EXIT", "SI_DIALOG_ACCEPT",
    "SI_GAME_MENU_ADDONS", "SI_GAME_MENU_LOGOUT",
]
