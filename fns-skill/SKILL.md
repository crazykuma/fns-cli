---
name: fns
description: Use the FNS CLI (Fast Note Sync) to read, write, manage, and sync Obsidian notes via the FNS cloud service. Use when working with Obsidian vaults, managing knowledge bases, reading/writing notes from terminal, or integrating AI agents with Obsidian.
---

# FNS CLI Skill

This Skill provides instructions and examples for using the **FNS CLI** (Fast Note Sync) tool to interact with Obsidian notes via the FNS cloud service.

## Overview

FNS CLI enables cloud-based management of Obsidian notes. The core workflow is:

```
Obsidian App ←→ FNS Cloud Server ←→ FNS CLI (Terminal / AI Agent)
```

**One edit, all synced.** Whether you write in Obsidian or manage notes via CLI/AI, everything stays in sync through the FNS cloud service.

## Installation

```bash
git clone https://github.com/crazykuma/fns-cli.git
cd fns-cli
pip install -e .
```

Or use directly without installation:
```bash
python fns.py <command> [args]
```

## Setup

### First-time login (interactive)
```bash
fns login
```
This guides you through: server URL → username → password → vault selection.

### Script-friendly login
```bash
fns login -u https://your-server username password
```

### View current configuration
```bash
fns config show
```

## Core Commands

### Read notes
```bash
fns read "path/to/note.md"
fns read "path/to/note.md" --json    # Machine-readable output
```

### Write notes
```bash
fns write "path/to/note.md" "Content here"
fns write "path/to/note.md" @local-file.txt   # Upload local file
```

### Append content (smart newline handling)
```bash
fns append "path/to/note.md" "- [x] Task completed"
```

### Prepend content (after frontmatter)
```bash
fns prepend "path/to/note.md" "---\ntags: [important]\n---\n\n"
```

### Delete and restore
```bash
fns delete "path/to/note.md"        # Moves to recycle bin
fns recycle-bin                     # View recycle bin
fns restore "path/to/note.md"       # Restore from recycle bin
```

### Move/rename notes
```bash
fns move "old/path.md" "new/path.md"
```

### Find and replace
```bash
fns replace "path/to/note.md" "old text" "new text"
```

## Knowledge Discovery

### List and search notes
```bash
fns list
fns list "keyword"
```

### View folder tree
```bash
fns tree
fns tree "subfolder"
```

### Find related notes
```bash
fns backlinks "path/to/note.md"     # Notes linking TO this one
fns outlinks "path/to/note.md"      # Notes this one links TO
```

### View note history
```bash
fns history "path/to/note.md"
```

## Frontmatter Management

### View frontmatter
```bash
fns frontmatter "path/to/note.md"
```

### Edit frontmatter
```bash
fns frontmatter "path/to/note.md" --set tags=important --set status=draft
fns frontmatter "path/to/note.md" --remove outdated-field
```

## Sharing

### Create shareable links
```bash
fns share "path/to/note.md"
fns share "path/to/note.md" --expire 24h --password secret
```

### Remove sharing
```bash
fns unshare "path/to/note.md"
```

## Vault & Server Management

```bash
fns vaults                         # List available vaults
fns vault-info [id]                # Show vault details
fns version                        # Show server version
fns health                         # Check server health
fns info                           # Show current user info
```

## Global Flags

```bash
fns --json <command>               # Output as JSON (for AI/script parsing)
fns --quiet <command>              # Suppress non-essential output
fns --version / -v                 # Show version
```

## AI Agent Workflows

### Read context before working
```bash
fns read "projects/architecture.md" --json
```

### Document changes after working
```bash
fns append "daily/$(date +%Y-%m-%d).md" "- Completed task X"
```

### Discover relevant notes
```bash
fns list "API design"
fns backlinks "api/design.md"
```

## File Upload

Use `@` prefix to upload local files:
```bash
fns write "backup/notes.md" @/path/to/local-file.txt
fns append "daily/notes.md" @todo-list.md
```

## v0.6 Folder Management
- `fns mkdir <path>`: Create a folder.
- `fns folder <path>`: Get folder info.
- `fns folder-list [path]`: List sub-folders.
- `fns folder-files <path>`: List files.
- `fns folder-notes <path>`: List notes.
- `fns folder-tree`: Show tree.
- `fns folder-delete <path>`: Delete folder.

## v0.7 File/Attachment Management
- `fns file-info <path>`: View file metadata (path, size, contentHash).
- `fns file-download <path> [-o file]`: Download file to local disk.
- `fns file-list [keyword]`: List files with pagination.
- `fns file-delete <path>`: Soft delete file to recycle bin.
- `fns file-rename <old> <new>`: Rename file.
- `fns file-restore <path>`: Restore file from recycle bin.
- `fns file-recycle-clear [paths]`: Permanently delete files from recycle bin.

## v0.8 User Settings, Backup & Sharing
- `fns setting-list [keyword]`: List user settings with pagination.
- `fns setting-get <path>`: Get setting content.
- `fns setting-create <path> <content>`: Create or update a setting.
- `fns setting-delete <path>`: Soft delete a setting.
- `fns setting-rename <old> <new>`: Rename a setting.
- `fns backup-list`: List backup configurations.
- `fns backup-create <vault> --storage-ids N --cron daily`: Create backup config.
- `fns backup-delete <config_id>`: Delete backup config by ID.
- `fns backup-run <config_id>`: Manually trigger a backup.
- `fns backup-history <config_id>`: View backup execution history.
- `fns share-link <path>`: Generate a short share URL.
- `fns change-password <old> <new>`: Change account password.
