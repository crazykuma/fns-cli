**Languages**: 🇺🇸 English | [🇨🇳 中文](README.zh.md)

---

# FNS CLI (Fast Note Sync CLI)

> **From Local to Cloud**: Transform Obsidian notes from locally-managed files into **cloud-managed, AI-accessible knowledge**. Edit once, sync everywhere.

FNS CLI is a powerful command-line tool for interacting with the **[Fast Note Sync (FNS)](https://github.com/haierkeys/fast-note-sync-service)** service. Manage, read, write, and sync your Obsidian notes directly from the terminal — optimized for both **human workflows** and **AI Agent integration**.

## 🎯 Design Philosophy

This tool bridges the gap between **local Obsidian editing** and **cloud-based AI knowledge management**:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Obsidian App   │────▶│  FNS Service     │◀────│  FNS CLI (this) │
│  (Desktop/Mobile│     │  (Cloud Server)  │     │  (Terminal/AI)  │
│   Editor)       │◀────│                  │────▶│  (read/write)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  AI Agents           │
                                              │  Claude Code,        │
                                              │  OpenCode, Cursor... │
                                              └─────────────────────┘
```

**One edit/update → all devices synced.** Whether you write in Obsidian on your desktop or manage notes via CLI/AI on a server, everything stays in sync through the FNS cloud service.

## ✨ Features

### Core
- **Full Note CRUD** — Create, read, update, append, prepend, move, delete
- **Smart Append** — Automatically handles newlines to prevent content merging
- **Local File Upload** — Use `@file.txt` prefix to upload any local file
- **Note History** — View and restore previous versions
- **Recycle Bin** — Recover deleted notes
- **Find & Replace** — Search and replace content (supports regex)
- **Cross-Platform** — macOS / Linux / Windows (Python 3.6+)

### Knowledge Graph
- **Backlinks** — See which notes link to the current note
- **Outlinks** — See which notes the current note links to
- **Folder Tree** — Browse your vault's directory structure

### Sharing & Metadata
- **Share Links** — Create shareable URLs with optional password and expiry
- **Frontmatter Editing** — View and modify note metadata (tags, title, etc.)

### AI Agent Friendly
- **`--json` Mode** — Machine-readable output for AI parsing
- **`--quiet` Mode** — Silent operation for scripting
- **Zero interactive prompts** when arguments are provided

### Administration
- **Vault Management** — List, view details, create, delete vaults
- **Server Status** — Check version and health
- **Storage Management** — Add/remove/validate storage backends (S3, OSS, WebDAV, etc.)
- **Git Sync** — Manage git sync configurations, trigger syncs, view history
- **Admin Operations** — System info, restart, upgrade, GC, WebSocket clients (requires admin privileges)
- **Auto-Setup** — Interactive guide on first login (URL → credentials → vault selection)

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install fns-cli
```

This installs the `fns` command globally on your system.

### From Source

```bash
git clone https://github.com/crazykuma/fns-cli.git
cd fns-cli
pip install -e .
```

**Dependencies**: `click>=8.1` (installed automatically) + `curl` (pre-installed on most systems)

After installation, the `fns` command is available globally.

## ⚙️ Quick Setup

### First-Time (Interactive Guide)

```bash
fns login
# Enter FNS server URL: https://your-server
# Username or email: you@example.com
# Password: **** (hidden)
# 📦 Available vaults:
#   1. defaultVault
# Select vault [1]: 1
# 🎉 Ready! Try: fns list
```

### Script-Friendly (Non-Interactive)

```bash
fns login -u https://your-server username password
```

### Manual Configuration

```bash
fns config url "https://your-server/api"
```

## 🚀 Command Reference

### Authentication & Setup
```bash
fns login [user] [pass] [-u URL]  # Login (interactive if args omitted)
fns config show                    # Show current configuration
fns config url <value>             # Set API URL
fns config vault <value>           # Set vault name
```

### Note CRUD
```bash
fns read <path>                    # Read a note
fns write <path> <text|@file>      # Create/overwrite (use @ to upload local file)
fns append <path> <text|@file>     # Append content (smart newline handling)
fns prepend <path> <text|@file>    # Prepend content (after frontmatter)
fns delete <path>                  # Delete note (moves to recycle bin)
fns move <old> <new>               # Move/rename a note
fns replace <path> <find> <replace> # Find and replace (supports regex)
fns history <path>                 # View revision history
fns restore <path>                 # Restore note from recycle bin
```

### Knowledge & Links
```bash
fns list [keyword]                 # List/search notes
fns tree [path]                    # View folder tree structure
fns backlinks <path>               # Notes linking to this one
fns outlinks <path>                # Notes this one links to
```

### Folder Management
- **Create & Delete** — `mkdir`, `folder-delete`
- **Browse** — `folder-list`, `folder-tree`
- **List Content** — `folder-files`, `folder-notes`
- **Metadata** — `folder`

### File/Attachment Management
- **View & Download** — `file-info`, `file-download [-o output]`
- **List** — `file-list [keyword]`
- **Delete & Restore** — `file-delete`, `file-restore`
- **Rename** — `file-rename <old> <new>`
- **Recycle** — `file-recycle-clear [paths]`

### User Settings & Backup
- **Settings** — `setting-list`, `setting-get`, `setting-create`, `setting-delete`, `setting-rename`
- **Backup** — `backup-list`, `backup-create`, `backup-delete`, `backup-run`, `backup-history`
- **Short Links** — `share-link <path>`
- **Password** — `change-password <old> <new>`

### Sharing & Metadata
```bash
fns share <path> [--expire 24h] [--password secret]  # Create share link
fns unshare <path>                 # Remove sharing
fns frontmatter <path>             # View frontmatter
fns frontmatter <path> --set key=value --remove key  # Edit frontmatter
```

### Folder Management
```bash
fns mkdir <path>                     # Create a new folder
fns folder <path>                    # Get folder metadata
fns folder-list [path]               # List sub-folders (root if empty)
fns folder-files <path>              # List files in a folder
fns folder-notes <path>              # List notes in a folder
fns folder-tree [--depth N]          # View folder tree
fns folder-delete <path>             # Delete folder (soft delete)
```

### File/Attachment Management
```bash
fns file-info <path>                 # View file metadata
fns file-download <path> [-o file]   # Download file to local
fns file-list [keyword]              # List files with pagination
fns file-delete <path>               # Delete file (to recycle bin)
fns file-rename <old> <new>          # Rename file
fns file-restore <path>              # Restore file from recycle bin
fns file-recycle-clear [paths]       # Clear file recycle bin
```

### User Settings & Backup
```bash
fns setting-list [keyword]           # List settings with pagination
fns setting-get <path>               # Get setting content
fns setting-create <path> <content>  # Create/update setting
fns setting-delete <path>            # Soft delete setting
fns setting-rename <old> <new>       # Rename setting

fns backup-list                      # List backup configurations
fns backup-create <vault> --storage-ids N --cron daily  # Create backup config
fns backup-delete <config_id>        # Delete backup config by ID
fns backup-run <config_id>           # Trigger backup
fns backup-history <config_id>       # View backup history

fns share-link <path>                # Generate short share URL
fns change-password <old> <new>      # Change account password
```

### Vault & Server
```bash
fns vaults                         # List available vaults
fns vault-info [id]                # Show vault details
fns vault-create <name>            # Create vault (with confirmation)
fns vault-delete <id>              # Delete vault (double confirmation)
fns recycle-bin [keyword]          # View recycle bin
fns version                        # Show server version
fns health                         # Check server health
fns info                           # Show current user info
fns change-password <old> <new>    # Change account password
```

### Storage Management (v0.9+)
```bash
fns storage-list                   # List storage configurations
fns storage-add <name> <type>      # Add storage (localfs/s3/oss/r2/minio/webdav)
fns storage-remove <id>            # Remove storage by ID
fns storage-validate <type>        # Test storage connection
fns storage-enabled                # List enabled storage types
```

### Git Sync Management (v0.9+)
```bash
fns git-sync list                  # List git sync configurations
fns git-sync add <name> --repo-url <url> [--branch main] [--interval 5m]
fns git-sync remove <id>           # Remove configuration
fns git-sync validate <id>         # Validate configuration
fns git-sync run <id>              # Manually trigger sync
fns git-sync clean <id>            # Clean local workspace
fns git-sync history <id>          # View sync history
```

### Admin Operations (v0.9+, requires admin privileges)
```bash
fns admin-info                     # Show system and runtime info
fns admin-restart                  # Gracefully restart server
fns admin-upgrade <version>        # Trigger server upgrade
fns admin-gc                       # Trigger manual GC
fns admin-ws-clients               # List connected WebSocket clients
```

### Global Flags
```bash
fns --json <command>               # Output as JSON (for AI/script parsing)
fns --quiet <command>              # Suppress non-essential output
fns --version / -v                 # Show version
fns --help                         # Show help
```

## 🤖 AI Agent Integration

This tool is designed to give AI agents **long-term memory and knowledge access**:

- **Read Context**: `fns read` specific notes before coding tasks
- **Auto-Documentation**: `fns append` changelogs to daily notes
- **Knowledge Retrieval**: `fns list` / `fns tree` to discover relevant files
- **Knowledge Graph**: `fns backlinks` / `fns outlinks` to find related notes

**Example with AI Agent:**
```bash
# Ask AI to read context, work, then document
fns read "projects/architecture.md" --json
# ... AI works ...
fns append "daily/2024-05-20.md" "- Completed architecture review"
```

## 📁 Project Structure

```
fns-cli/
├── pyproject.toml           # Package definition + fns command entry point
├── fns_cli/                 # Python CLI package
│   ├── __init__.py
│   ├── main.py              # Click entry point + global options + login/config/health/version
│   ├── api.py               # HTTP request layer (curl subprocess)
│   ├── config.py            # Config management (load/save/require_vault)
│   ├── hashing.py           # Path hash computation (32-bit rolling hash)
│   ├── formatting.py        # Output formatting (timestamp/size/echo)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── note.py          # read/write/delete/append/prepend/replace/move/rename/restore/frontmatter/backlinks/outlinks
│   │   ├── folder.py        # mkdir/folder/folder-files/notes/list/delete/tree
│   │   ├── file.py          # file-info/list/delete/rename/restore/download
│   │   ├── share.py         # share/unshare/shares/password/paths/link
│   │   ├── setting.py       # setting-list/get/create/delete/rename
│   │   ├── backup.py        # backup-list/create/delete/run/history
│   │   ├── vault.py         # vaults/info/create/delete
│   │   ├── storage.py       # storage-list/add/remove/validate/enabled
│   │   ├── git_sync.py      # git-sync list/add/remove/validate/run/clean/history
│   │   └── admin.py         # admin-info/restart/upgrade/gc/ws-clients
│   └── tests/
│       ├── __init__.py
│       ├── test_api.py
│       ├── test_formatting.py
│       ├── test_hashing.py
│       └── commands/
│           └── test_note.py
├── fns-source/              # FNS Go backend server (submodule)
├── fns-skill/               # AI Agent Skill (portable)
│   └── SKILL.md
├── types.ts                 # Obsidian plugin types
├── websocket_client.ts      # Obsidian plugin WebSocket client
├── operator_file.ts         # Obsidian plugin file sync
├── operator_config.ts       # Obsidian plugin config sync
├── helpers.ts               # Obsidian plugin utilities
├── websocket_action.ts      # Obsidian plugin WebSocket actions
├── concurrency_limiter.ts   # Obsidian plugin concurrency control
├── reasonix.toml            # AI agent reasoning config
└── .github/workflows/ci.yml # CI for Python CLI
```

## 📖 Usage Examples

For detailed examples, see the portable Skill at [`fns-skill/SKILL.md`](fns-skill/SKILL.md). You can copy the entire `fns-skill/` directory into your own AI agent's Skills folder (Qwen Code, Claude Code, etc.).

## 🧪 Running Tests

```bash
python -m pytest fns_cli/tests/ -v
# or
python -m unittest discover -s fns_cli/tests -v
```

## 🔗 Related Projects

- **[fast-note-sync-service](https://github.com/haierkeys/fast-note-sync-service)** — The FNS backend server
- **[obsidian-fast-note-sync](https://github.com/haierkeys/obsidian-fast-note-sync)** — Obsidian plugin

## 📜 License

MIT License — see [LICENSE](LICENSE).
