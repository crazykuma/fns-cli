# FNS CLI (Fast Note Sync CLI)

A powerful command-line interface for interacting with the **Fast Note Sync (FNS)** service for Obsidian. Manage, read, write, and sync your notes directly from your terminal.

## ✨ Features

- **Sync Notes**: Instantly read/write notes to your Obsidian vault via FNS.
- **Smart Append**: Automatically adds newlines to separate appended content from existing text.
- **Cross-Platform**: Works on macOS/Linux/Windows (Python 3.6+).
- **Local File Upload**: Supports uploading local files directly to your vault.
- **Zero Dependencies**: Uses standard library and `curl` (pre-installed on most systems).

## 📦 Installation

### From Source (Recommended)

```bash
git clone https://github.com/crazykuma/fns-cli.git
cd fns-cli
pip install -e .
```

This installs the `fns` command globally on your system.

## ⚙️ Configuration

**Important**: Before logging in, you must configure your FNS server URL.

```bash
# Set the API URL (Required)
fns config url "https://your-fns-server.com/api"
```

## 🚀 Quick Start

### 1. Login
Connect to your FNS server instance.
```bash
fns login <username_or_email> <password>
```

### 2. List Notes
Browse your vault's file tree.
```bash
fns list
# Search for specific notes
fns list "daily"
```

### 3. Read & Write
Interact with specific notes.
```bash
# Read a note
fns read "daily/2024-05-20.md"

# Create or overwrite a note
fns write "drafts/ideas.md" "Here is my brilliant idea..."

# Append to a note (auto-formats newlines)
fns append "daily/2024-05-20.md" "- [x] Completed task"
```

### 4. Upload Local Files
Use the `@` prefix to upload a file from your machine.
```bash
fns write "backup/meeting-notes.md" @/path/to/meeting-notes.txt
```

### 5. Vault Configuration (Optional)
If you need to change the default Vault name (matches your Obsidian vault name on the server):
```bash
fns config vault "My Vault"
```

## 📁 File Structure

```
fns-cli/
├── fns.py        # Main CLI logic
├── setup.py      # Installation script
├── README.md     # This file
└── LICENSE       # MIT License
```

## 🔗 Related Projects

- **[obsidian-fast-note-sync](https://github.com/haierkeys/obsidian-fast-note-sync)**: The original FNS service and Obsidian plugin that powers this CLI.

## 📜 License

MIT License - see the [LICENSE](LICENSE) file for details.
