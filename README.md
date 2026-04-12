**Languages**: 🇺🇸 English | [🇨🇳 中文](README.zh.md)

---

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

# Prepend content (after frontmatter)
fns prepend "daily/2024-05-20.md" "---\ntags: [reviewed]\n---"

# Find and replace
fns replace "drafts/ideas.md" "TODO" "DONE"

# Move/rename a note
fns move "drafts/ideas.md" "archive/ideas.md"

# Delete a note (moves to recycle bin)
fns delete "drafts/ideas.md"

# View note history
fns history "daily/2024-05-20.md"
```

### 4. Upload Local Files
Use the `@` prefix to upload a file from your machine.
```bash
fns write "backup/meeting-notes.md" @/path/to/meeting-notes.txt
fns append "daily/2024-05-20.md" @/path/to/todo-list.md
```

### 5. Manage Vault & User
```bash
# List available vaults
fns vaults

# Set a specific vault
fns config vault "My Vault"

# Show current user info
fns info
```

## 🤖 AI Agent Integration

You can use `fns` with any AI coding agent (OpenCode, Claude Code, OpenClaw, etc.) to manage your knowledge base:

- **Read Context**: Ask agents to `fns read` specific notes to give them long-term memory or context before coding.
- **Auto-Documentation**: Have agents `fns append` changelogs or summaries to your daily notes automatically.
- **Knowledge Retrieval**: Use `fns list` to let agents discover relevant files before starting a task.

**Example with OpenCode/Claude Code:**
```bash
# Ask OpenCode to summarize a note and update it
opencode "Read 'drafts/ideas.md', summarize the key points, and append the summary to the bottom."
```

## 📁 File Structure

```
fns-cli/
├── fns.py          # Main CLI logic
├── setup.py        # Installation script
├── tests/          # Unit tests (unittest)
│   └── test_fns.py
├── .gitignore
├── README.md       # English documentation
├── README.zh.md    # Chinese documentation
└── LICENSE         # MIT License
```

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -v
```

## 📜 License

MIT License - see the [LICENSE](LICENSE) file for details.
