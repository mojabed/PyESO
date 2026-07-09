# Changelog

## [0.1.0] — 2026-07-09

### Added
- **E001**: Unknown API detection — flags calls to functions not in the ESOUI API surface
- **W001**: Parameter count checking — warns when API functions are called with wrong number of arguments
- **W002**: Deprecated API detection — identifies renamed/removed ESOUI APIs with replacement suggestions
- ESOUI source extraction (`--esoui`) for building richer API databases
- CLI with `--stats`, `--no-color`, `--help` options
