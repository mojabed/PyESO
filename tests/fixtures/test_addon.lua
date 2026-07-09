-- Test Addon - exercises all three lint rules

local ADDON_NAME = "TestAddon"

-- ✓ Valid API call (correct params)
local playerName = GetUnitName("player")

-- ✗ Unknown function (typo)
local wrongName = GetUniteName("player")

-- ✗ Deprecated API
local money = GetCurrentMoney()

-- ✗ Wrong param count - too few args
local item = GetItemLink()

-- ✓ Valid with right params
local itemLink = GetItemLink(BAG_BACKPACK, 1)

-- ✗ Deprecated API (constant)
local plateSetting = NAMEPLATE_CHOICE_OFF

-- ✓ Valid standard library call
local s = string.format("Hello %s", playerName)

-- ✓ Valid zo_ wrapper
local ceil = zo_ceil(3.14)

-- ✗ Unknown function with CamelCase that looks like API
local result = SomeRandomThing("test")

-- Local function - should NOT be flagged
local function myHelper(x)
    return x * 2
end

local doubled = myHelper(5)

function TestAddon:OnLoad()
    -- ✓ Method on self
    self:RegisterEvents()
end

function TestAddon:RegisterEvents()
    EVENT_MANAGER:RegisterForEvent(ADDON_NAME, EVENT_ADD_ON_LOADED, function()
        d("Addon loaded")
    end)
end
