"""Curated seed API data — common ESO C-side and Lua-side APIs.

These are APIs called from Lua but defined in the C engine, so they
cannot be extracted from ESOUI Lua source files. They supplement the
auto-extracted API surface from the ESOUI submodule.
"""

# Format: {"name": "...", "params": ["p1", "p2"], "min_params": N, "varargs": bool}
SEED_API_FUNCTIONS: list[dict] = [
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

SEED_DEPRECATED: list[dict] = [
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
    # Weapon Power
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

SEED_VARIABLES: list[str] = [
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
