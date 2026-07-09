# PyESO - ESO Addon Linter

A Python-based static analysis and linting tool for **Elder Scrolls Online** addon developers.  
Checks your addon's LUA code against the known ESOUI API surface to catch issues **before** the
addon ever runs in-game.

## Features

- **Unknown API Detection** — Flags calls to functions not in the ESOUI API surface (typos, missing imports).
- **Parameter Count Checking** — Warns when an API function is called with the wrong number of arguments.
- **Deprecated API Detection** — Identifies usage of renamed or removed ESOUI APIs and suggests replacements.
- **ESOUI Source Extraction** — Optionally point at a local clone of the [ESOUI source](https://github.com/esoui/esoui) to build a richer API database.

## Installation

```bash
pip install -e .
```

Requires Python 3.10+. The only dependency is `luaparser` for LUA AST parsing.
Optional EXE provided.

## Usage

### Quick Start

```bash
# Lint a single addon file
pyeso path/to/MyAddon.lua

# Lint an entire addon directory (recursive)
pyeso path/to/MyAddon/

# Lint multiple paths
pyeso MyAddon/ MyOtherAddon/Utils.lua
```

### With ESOUI Source

If you have a local clone of the ESOUI source, you can use it to build a richer API database:

```bash
git clone https://github.com/esoui/esoui.git
pyeso --esoui ./esoui/esoui MyAddon/
```

### Options

| Flag | Description |
|------|-------------|
| `--esoui PATH` | Path to ESOUI source directory for API extraction |
| `--no-color` | Disable colored output |
| `--stats` | Print API database statistics before linting |
| `--version` | Show version |
| `--help` | Show help |

## How It Works

1. **API Database**: PyESO ships with a curated seed database of ~150+ ESOUI API functions, constants, and deprecated aliases. If you provide `--esoui`, it also parses ESOUI source `.lua` files to extract additional function definitions.

2. **Parsing**: Your addon's `.lua` files are parsed into an AST using `luaparser`. The AST is walked to collect all function calls.

3. **Linting**: Three rules are applied:
   - **E001 (Unknown API)**: Each function call is checked against the known API surface. Calls to unknown identifiers are flagged.
   - **W001 (Param Count)**: Function calls are compared against known signatures; mismatched argument counts are flagged.
   - **W002 (Deprecated API)**: Deprecated function/variable names are flagged with their replacement.

4. **Reporting**: Diagnostics are printed with file, line number, severity, and a descriptive message.

## Example Output

```
MyAddon/MyAddon.lua:45 [WARNING] E001: Unknown function 'GetUniteName' - not found in ESOUI API surface. This may be a typo.
MyAddon/MyAddon.lua:72 [WARNING] W002: 'GetCurrentMoney' is deprecated; use 'GetCurrencyAmount(CURT_MONEY, CURRENCY_LOCATION_CHARACTER)' instead.
MyAddon/Lib.lua:120 [WARNING] W001: 'GetUnitName' expects at least 1 argument(s), but 0 were provided.

3 file(s) scanned, 3 warning(s)
```

## Extending the API Database

The seed API database is in `pyeso/api/extractor.py` (`_SEED_API_FUNCTIONS`, `_SEED_DEPRECATED`, `_SEED_VARIABLES`). To add more APIs:

1. Add entries to the appropriate seed list
2. Or point `--esoui` at an ESOUI source checkout for automatic extraction

## License

MIT
