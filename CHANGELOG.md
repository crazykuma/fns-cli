# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-04-12

### Added
- **13 new commands** for comprehensive FNS API coverage:
  - `tree [path]` — Vault folder tree structure view
  - `backlinks <path>` — Notes linking to this note
  - `outlinks <path>` — Notes this note links to
  - `restore <path>` — Recover note from recycle bin
  - `frontmatter <path>` — View/edit note metadata
  - `share <path>` — Create shareable links (with optional password/expiry)
  - `unshare <path>` — Remove sharing
  - `vault-info [id]` — Show vault details
  - `recycle-bin [path]` — View recycle bin contents
  - `version` — Show server version
  - `health` — Check server health
  - `vault-create <name>` — Create new vault (with confirmation)
  - `vault-delete <id>` — Delete vault (with double confirmation)
- URL auto-append `/api` suffix in `fns config url`
- Auto-vault detection on login (shows numbered menu for selection)
- Windows console UTF-8 encoding support for emoji output

### Changed
- `login` command now guides through full setup when URL is not configured
- Password input is now hidden (`hide_input=True`)
- Vault selection uses numbered menu instead of free-text input
- Proper API field names: `find` for replace, `destination` for move, `vault` for vault list

### Fixed
- `list` command renamed to `list_notes` to avoid shadowing built-in
- Response handling properly distinguishes success codes (1-6) from errors

## [0.3.0] - 2026-04-12

### Added
- **Click-based CLI framework** with subcommand auto-discovery and `--help`
- **`--json` flag** for machine-readable output (AI Agent friendly)
- **`-q` / `--quiet` flag** for silent operation
- **`fns --version` / `-v`** to display version
- **Vault requirement check** before making API requests
  - Helpful hints: `fns vaults` or `fns config vault <name>`
- **6 new commands**: `delete`, `prepend`, `replace`, `move`, `history`, `info`, `vaults`
- **URL normalization**: auto-appends `/api` suffix if missing
- **Auto-vault detection** on login (sets default if only one vault exists)

### Changed
- Error code handling now properly distinguishes success (`1-6`) from errors
- `DEFAULT_VAULT` removed; vault is now auto-detected or user-configured
- Tests refactored for click-based CLI

## [0.2.0] - 2026-04-12

### Added
- Cross-platform config directory support
  - Windows: `%APPDATA%/fns-cli/`
  - Linux/macOS: `~/.config/fns-cli/`
- Automatic legacy token migration (`~/.fns_token` → new config directory)
- 15 unit tests covering timestamp formatting, config, file upload prefix,
  argument validation, URL encoding, and token migration

### Fixed
- URL parameter encoding using `urllib.parse.urlencode` (fixes Chinese characters,
  spaces, and special characters in note paths)
- `@file.txt` prefix for local file upload in `write` and `append` commands
- Missing argument count validation for `read`, `write`, `append`, and `config`
  commands (prevents `IndexError` crashes)
- Human-readable timestamps in `list` output (was raw millisecond Unix timestamp)

### Changed
- Token storage moved from `~/.fns_token` to `<config_dir>/fns-cli/token`
  for consistency with config file location

## [0.1.0] - 2026-03-20

### Added
- Initial release with basic CLI commands: `login`, `read`, `write`, `append`,
  `list`, `config`, `help`
- Smart newline handling in `append` command
- Zero-dependency design (Python standard library + `curl`)
