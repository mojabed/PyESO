# PyESO — ESO Addon Linter

Lint your Elder Scrolls Online addon Lua code before it ever runs in-game. Catches typos, wrong argument counts, deprecated APIs, global variable leaks, and hardcoded strings.

## Installation

### Option 1: Download the EXE (no Python needed)

Download `pyeso.exe` from [releases](https://github.com/mojabed/PyESO/releases) and run from terminal

```bash
pyeso MyAddon.lua
pyeso MyAddon/
```

### Option 2: From source (requires Python 3.10+)

```bash
git clone --recurse-submodules https://github.com/mojabed/PyESO.git
cd PyESO
pip install -e .
```

Then:

```bash
pyeso MyAddon.lua
# or
python -m pyeso MyAddon/
```

## What it checks

| Code | What |
|------|------|
| E001 | Unknown function — typo or missing import |
| E002 | Unknown event — `RegisterForEvent` with non-existent event |
| W001 | Wrong number of arguments |
| W002 | Deprecated function call |
| W003 | Global variable leak — missing `local` |
| W005 | Deprecated constant reference |
| W006 | Unknown object method — method not found in ESOUI Object API |
| I001 | Hardcoded string — should use `GetString()` |

## Requirements

PyESO requires the full ESOUI API source. Clone with submodules:

```bash
git clone --recurse-submodules https://github.com/mojabed/PyESO.git
```

## Example

```bash
$ pyeso MyAddon/

MyAddon/main.lua:7  [ERR] E001: Unknown function 'GetUniteName' ...
MyAddon/main.lua:10 [WRN] W002: 'GetCurrentMoney' is deprecated ...
MyAddon/main.lua:15 [WRN] W001: 'GetUnitName' expects at least 1 argument ...
MyAddon/main.lua:20 [WRN] W003: 'MyGlobal' is assigned without 'local' ...
MyAddon/main.lua:25 [WRN] W005: 'NAMEPLATE_CHOICE_OFF' is deprecated ...
MyAddon/main.lua:30 [INF] I001: Hardcoded string may need localization ...
MyAddon/main.lua:35 [ERR] E002: Unknown event 'EVENT_FAKE_THING' ...
MyAddon/main.lua:40 [WRN] W006: Unknown method 'SetHiden' ...

8 issue(s): 2 error(s), 4 warning(s), 2 info(s)
```

## Python API

```python
from pyeso import ESOLinter

linter = ESOLinter()
diags = linter.lint_file("MyAddon.lua")
diags = linter.lint_directory("MyAddon/")

for d in diags:
    print(f"{d.file}:{d.line} [{d.code}] {d.message}")
```

## How it works

The ESOUI source is parsed to build a registry of functions, events, UI class methods,
constants, and deprecation mappings. The `ESOUIDocumentation.txt` canonical API reference
provides typed signatures for C-side functions (Game API), UI control methods (Object API),
and events. Additional Lua-level APIs and deprecations are extracted from the ESOUI Lua
source. Your addon's Lua files are parsed into an AST and checked against this registry.

## License

MIT
