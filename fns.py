#!/usr/bin/env python3
"""Fast Note Sync (FNS) CLI - Interact with your Obsidian FNS service from terminal."""
import sys, json, subprocess, os
from pathlib import Path
from urllib.parse import urlencode
from datetime import datetime, timezone

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click

__version__ = "0.6.0"

def _compute_path_hash(path_str):
    """Compute 32-bit path hash matching FNS server implementation.
    
    Uses polynomial rolling hash: h = h * 31 + byte, then convert to signed int32.
    """
    h = 0
    for byte in path_str.encode("utf-8"):
        h = ((h * 31) + byte) & 0xFFFFFFFF
    # Convert to signed 32-bit integer
    if h >= 0x80000000:
        h -= 0x100000000
    return str(h)

# Config directory: ~/.config/fns-cli/ (cross-platform, consistent with other CLI tools)
CONFIG_DIR = Path.home() / ".config" / "fns-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"

DEFAULT_BASE_URL = ""  # Configure via 'fns config url'
DEFAULT_VAULT = ""  # Auto-detected on first login

# Global state for output mode
_ctx = {}

def _echo(text, **kwargs):
    """Print unless quiet mode is enabled."""
    if not _ctx.get("quiet"):
        click.echo(text, **kwargs)


def _format_size(num_bytes):
    """Format file size in bytes to human readable string."""
    if num_bytes is None:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_timestamp(ts_ms):
    """Convert millisecond Unix timestamp to human-readable local time."""
    if not ts_ms:
        return ""
    try:
        dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return str(ts_ms)

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"base_url": DEFAULT_BASE_URL, "vault": DEFAULT_VAULT}

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def require_vault():
    """Check if vault is configured, print hint if not."""
    cfg = load_config()
    vault = cfg.get("vault", "")
    if not vault:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Vault not configured", "hint": "Run: fns vaults or fns config vault <name>"}))
            sys.exit(1)
        click.echo("⚠️ Vault not configured. Run one of these:")
        click.echo("   fns vaults          # List available vaults")
        click.echo("   fns config vault <name>  # Set your vault")
        sys.exit(1)
    return vault

def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    if _ctx.get("json_output"):
        click.echo(json.dumps({"error": "Token not found", "hint": "Run: fns login"}))
        sys.exit(1)
    _echo("⚠️ Token not found. Run: fns login", err=True)
    sys.exit(1)

def _handle_response(data, success_msg=None, error_prefix="Failed"):
    """Handle API response, print success or error based on code/status."""
    code = data.get("code", 0)
    status = data.get("status", False)

    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        # Don't exit in JSON mode for errors, let caller handle
        return data

    # Success: code 1-6 OR status is True
    if code in range(1, 7) or status is True:
        if success_msg:
            _echo(success_msg)
        return data
    else:
        msg = data.get("message", json.dumps(data, indent=2, ensure_ascii=False))
        _echo(f"❌ {error_prefix}: {msg}", err=True)
        sys.exit(1)

def curl_request(method, endpoint, params=None, json_data=None):
    cfg = load_config()
    base_url = cfg.get("base_url", "")
    if not base_url:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "API URL not configured", "hint": "Run: fns config url <url>"}))
            sys.exit(1)
        _echo("⚠️ API URL not configured. Run: fns config url https://your-server/api", err=True)
        sys.exit(1)

    url = f"{base_url}{endpoint}"
    if params:
        url += f"?{urlencode(params)}"

    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {get_token()}"]

    if json_data is not None:
        cmd.extend(["-H", "Content-Type: application/json",
                    "-d", json.dumps(json_data)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            if _ctx.get("json_output"):
                click.echo(json.dumps({"error": "curl error", "detail": result.stderr.strip()}))
                sys.exit(1)
            _echo(f"❌ curl error: {result.stderr.strip()}", err=True)
            sys.exit(1)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Request timed out"}))
            sys.exit(1)
        _echo("❌ Request timed out", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Invalid JSON response", "detail": result.stdout[:200]}))
            sys.exit(1)
        _echo(f"❌ Invalid JSON response: {result.stdout[:200]}", err=True)
        sys.exit(1)

# ==================== Click CLI ====================

@click.group()
@click.version_option(__version__, prog_name="fns-cli")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-essential output")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, quiet, json_output):
    """📝 Fast Note Sync CLI - Interact with your Obsidian FNS service."""
    _ctx["quiet"] = quiet
    _ctx["json_output"] = json_output

@cli.command()
@click.argument("credentials", required=False)
@click.argument("password", required=False)
@click.option("-u", "--url", "api_url", help="Set API URL before login")
def login(credentials, password, api_url):
    """Login and save token (password will be hidden if not provided)."""
    cfg = load_config()

    # Step 1: Ensure URL is configured
    base_url = cfg.get("base_url", "")
    if api_url:
        url_val = api_url.rstrip("/")
        if not url_val.endswith("/api"):
            url_val += "/api"
        cfg["base_url"] = url_val
        save_config(cfg)
        _echo(f"✅ API URL set to '{url_val}'")
        base_url = url_val
    elif not base_url:
        base_url = click.prompt("Enter FNS server URL (e.g., https://your-server)")
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api"):
            base_url += "/api"
        cfg["base_url"] = base_url
        save_config(cfg)
        _echo(f"✅ API URL set to '{base_url}'")

    # Step 2: Prompt for credentials if not provided
    if not credentials:
        credentials = click.prompt("Username or email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    # Step 3: Authenticate
    url = f"{base_url}/user/login"
    cmd = ["curl", "-s", "-X", "POST", url,
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"Credentials": credentials, "Password": password})]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
        resp = json.loads(result.stdout)
        if _ctx.get("json_output"):
            click.echo(json.dumps(resp, indent=2, ensure_ascii=False))
            return

        if resp.get("status") or resp.get("code", 0) >= 1:
            token = resp.get("data", {}).get("token")
            if token:
                TOKEN_FILE.write_text(token)
                _echo(f"✅ Login successful. Token saved to {TOKEN_FILE}")

                # Step 4: Handle vault selection
                if not cfg.get("vault"):
                    vault_data = curl_request("GET", "/vault")
                    vaults_list = []
                    if isinstance(vault_data.get("data"), list):
                        vaults_list = vault_data["data"]
                    elif isinstance(vault_data.get("data"), dict):
                        vaults_list = vault_data["data"].get("list", [vault_data["data"]])

                    if len(vaults_list) == 1:
                        v = vaults_list[0]
                        vault_name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                        cfg["vault"] = vault_name
                        save_config(cfg)
                        _echo(f"📦 Auto-set vault to '{vault_name}'")
                    elif vaults_list:
                        _echo("📦 Available vaults:")
                        choices = []
                        for i, v in enumerate(vaults_list, 1):
                            name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                            choices.append(str(i))
                            _echo(f"  {i}. {name}")
                        selected = click.prompt("Select vault", type=click.Choice(choices), default=choices[0])
                        idx = int(selected) - 1
                        v = vaults_list[idx]
                        vault_name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                        cfg["vault"] = vault_name
                        save_config(cfg)
                        _echo(f"📦 Vault set to '{vault_name}'")
                _echo("🎉 Ready! Try: fns list")
            else:
                _echo("❌ No token in response.", err=True)
        else:
            _echo(f"❌ Login failed: {resp.get('message', 'Unknown error')}", err=True)
    except Exception as e:
        _echo(f"❌ Error: {e}", err=True)

@cli.command()
@click.argument("path")
def read(path):
    """Read a note."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    data = curl_request("GET", "/note", params={"vault": vault, "path": path, "pathHash": path_hash})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    content = data.get("data", {}).get("content") if isinstance(data.get("data"), dict) else None
    if content is not None:
        _echo(f"📄 {path}\n{'-'*40}\n{content}")
    else:
        _echo(f"❌ Unexpected response: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)

@cli.command()
@click.argument("path")
@click.argument("content_or_file")
def write(path, content_or_file):
    """Create/Update note (use @file.txt for local file)."""
    vault = require_vault()
    if content_or_file.startswith("@"):
        file_path = content_or_file[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            _echo(f"❌ File not found: {file_path}", err=True)
            return
    elif Path(content_or_file).exists():
        content = Path(content_or_file).read_text(encoding="utf-8")
    else:
        content = content_or_file

    data = curl_request("POST", "/note", json_data={"vault": vault, "path": path, "pathHash": _compute_path_hash(path), "content": content})
    _handle_response(data, success_msg=f"✅ Note '{path}' updated. Syncing to all devices...")

@cli.command()
@click.argument("path")
@click.argument("content")
def append(path, content):
    """Append text to a note (use @file.txt for local file)."""
    vault = require_vault()
    if content.startswith("@"):
        file_path = content[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            _echo(f"❌ File not found: {file_path}", err=True)
            return

    params = {"vault": vault, "path": path, "pathHash": _compute_path_hash(path)}
    read_resp = curl_request("GET", "/note", params=params)
    existing = ""
    if isinstance(read_resp.get("data"), dict):
        existing = read_resp["data"].get("content", "")

    if existing and not existing.endswith("\n\n"):
        if existing.endswith("\n"):
            content = "\n" + content
        else:
            content = "\n\n" + content

    data = curl_request("POST", "/note/append", json_data={"vault": vault, "path": path, "pathHash": _compute_path_hash(path), "content": content})
    _handle_response(data, success_msg=f"✅ Appended to '{path}'.")

@cli.command()
@click.argument("path")
def delete(path):
    """Delete a note (move to recycle bin)."""
    vault = require_vault()
    data = curl_request("DELETE", "/note", params={"vault": vault, "path": path, "pathHash": _compute_path_hash(path)})
    _handle_response(data, success_msg=f"✅ Note '{path}' deleted (moved to recycle bin).")

@cli.command()
@click.argument("path")
@click.argument("content_or_file")
def prepend(path, content_or_file):
    """Prepend text to a note (after frontmatter, use @file.txt for local file)."""
    vault = require_vault()
    if content_or_file.startswith("@"):
        file_path = content_or_file[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            _echo(f"❌ File not found: {file_path}", err=True)
            return
    else:
        content = content_or_file

    data = curl_request("POST", "/note/prepend", json_data={"vault": vault, "path": path, "pathHash": _compute_path_hash(path), "content": content})
    _handle_response(data, success_msg=f"✅ Prepended to '{path}'.")

@cli.command()
@click.argument("path")
@click.argument("search")
@click.argument("replace_text")
def replace(path, search, replace_text):
    """Find and replace in note."""
    vault = require_vault()
    data = curl_request("POST", "/note/replace", json_data={
        "vault": vault, "path": path, "pathHash": _compute_path_hash(path), "find": search, "replace": replace_text
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if data.get("code", 0) >= 1 or data.get("status"):
        replacements = data.get("data", {}).get("count", "?")
        _echo(f"✅ Replaced {replacements} occurrence(s) in '{path}'.")
    else:
        _echo(f"❌ Failed to replace: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)

@cli.command(name="move")
@click.argument("old_path")
@click.argument("new_path")
def move_note(old_path, new_path):
    """Move/rename a note."""
    vault = require_vault()
    data = curl_request("POST", "/note/move", json_data={
        "vault": vault, "path": old_path, "pathHash": _compute_path_hash(old_path), "destination": new_path
    })
    _handle_response(data, success_msg=f"✅ Moved '{old_path}' → '{new_path}'.")

@cli.command()
@click.argument("path")
@click.option("--page", default=1, help="Page number")
def history(path, page):
    """Show note history."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    data = curl_request("GET", "/note/histories", params={
        "vault": vault, "path": path, "pathHash": path_hash, "page": page, "pageSize": 20
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    histories = []
    if isinstance(data.get("data"), dict):
        histories = data["data"].get("list", [])
    elif isinstance(data.get("data"), list):
        histories = data["data"]

    if histories:
        _echo(f"📜 History for '{path}':\n")
        for h in histories:
            hid = h.get("id", h.get("historyId", ""))
            mtime = h.get("mtime", h.get("updatedTimestamp", h.get("createdTimestamp", "")))
            readable = format_timestamp(mtime) if mtime else ""
            size = h.get("size", h.get("contentLength", ""))
            _echo(f"  📄 [{hid}] {readable} ({size} bytes)")
        _echo("")
    else:
        _echo(f"📭 No history found for '{path}'.")

@cli.command("history-view")
@click.argument("path")
@click.argument("history_id")
def history_view(path, history_id):
    """View a specific historical version of a note."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    data = curl_request("GET", "/note/history", params={
        "vault": vault, "path": path, "pathHash": path_hash, "id": history_id
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    content = data.get("data", {}).get("content")
    diffs = data.get("data", {}).get("diffs", [])

    if diffs:
        # Show diffs from API
        _echo(f"📜 History #{history_id} of '{path}':\n{'-'*40}")
        for diff in diffs:
            diff_type = diff.get("Type", diff.get("type", 0))
            diff_text = diff.get("Text", diff.get("text", ""))
            prefix = "+" if diff_type == 1 else "-" if diff_type == 2 else " "
            _echo(f"{prefix} {diff_text}")
    elif content:
        _echo(f"📜 History #{history_id} of '{path}':\n{'-'*40}\n{content}")
    else:
        _echo(f"❌ History #{history_id} not found or has no content.")

@cli.command("history-restore")
@click.argument("path")
@click.argument("history_id")
def history_restore(path, history_id):
    """Restore a note to a specific historical version."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    click.confirm(f"⚠️ Restore '{path}' to version #{history_id}? Current content will be overwritten.", abort=True)

    data = curl_request("PUT", "/note/history/restore", json_data={
        "vault": vault, "path": path, "pathHash": path_hash, "historyId": int(history_id)
    })
    _handle_response(data, success_msg=f"✅ Restored '{path}' to version #{history_id}.")

@cli.command("rename")
@click.argument("old_path")
@click.argument("new_path")
def rename(old_path, new_path):
    """Rename a note to a new path."""
    vault = require_vault()
    # Get current note's pathHash
    old_path_hash = _compute_path_hash(old_path)
    note_data = curl_request("GET", "/note", params={"vault": vault, "path": old_path, "pathHash": old_path_hash})
    actual_hash = note_data.get("data", {}).get("pathHash", "")
    if not actual_hash:
        _echo(f"❌ Note '{old_path}' not found.", err=True)
        return

    new_path_hash = _compute_path_hash(new_path)

    data = curl_request("POST", "/note/rename", json_data={
        "vault": vault,
        "oldPath": old_path,
        "oldPathHash": actual_hash,
        "path": new_path,
        "pathHash": new_path_hash
    })
    _handle_response(data, success_msg=f"✅ Renamed '{old_path}' → '{new_path}'.")

@cli.command("recycle-clear")
@click.argument("paths", nargs=-1, required=False)
def recycle_clear(paths):
    """Permanently delete notes in recycle bin. Without args, clears entire bin."""
    vault = require_vault()
    if not paths:
        click.confirm("⚠️ Permanently delete ALL notes in recycle bin?", abort=True)
        data = curl_request("DELETE", "/note/recycle-clear", json_data={"vault": vault})
        _handle_response(data, success_msg="✅ Recycle bin cleared.")
    else:
        for p in paths:
            data = curl_request("DELETE", "/note/recycle-clear", json_data={"vault": vault, "path": p, "pathHash": _compute_path_hash(p)})
            _handle_response(data, success_msg=f"✅ Permanently deleted '{p}'.")

@cli.command("list")
@click.argument("keyword", required=False, default="")
@click.option("--page", default=1, help="Page number")
def list_notes(keyword, page):
    """List notes (optional keyword search)."""
    vault = require_vault()
    data = curl_request("GET", "/notes", params={"vault": vault, "keyword": keyword, "page": page, "pageSize": 20})

    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    notes = []
    pager_info = {}
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
        pager_info = data["data"].get("pager", {})
    elif isinstance(data, dict):
        notes = data.get("list", data.get("notes", []))

    if notes:
        total = pager_info.get("totalRows", len(notes)) if pager_info else len(notes)
        _echo(f"📚 Notes in '{vault}' (Page {page}):\n")
        for n in notes:
            path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            if mtime:
                _echo(f"  📄 {path} ({format_timestamp(mtime)})")
            else:
                _echo(f"  📄 {path}")
        _echo(f"\nTotal: {total}")
    else:
        _echo("📭 No notes found.")

@cli.command()
def vaults():
    """List available vaults."""
    data = curl_request("GET", "/vault")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    vault_list = []
    if isinstance(data.get("data"), list):
        vault_list = data["data"]
    elif isinstance(data.get("data"), dict):
        vault_list = data["data"].get("list", [data["data"]])

    if vault_list:
        _echo("📦 Available vaults:")
        for v in vault_list:
            name = v.get("vault", v.get("name", v.get("vault_name", v.get("id", "unknown"))))
            _echo(f"  🗄️  {name}")
    else:
        _echo(f"📭 No vaults found.")

@cli.command()
def info():
    """Show current user info."""
    data = curl_request("GET", "/user/info")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    user = data.get("data", {})
    if user:
        _echo("👤 Current user:")
        for key in ("username", "email", "displayName", "id", "role"):
            if key in user and user[key]:
                _echo(f"  {key}: {user[key]}")
    else:
        _echo(f"❌ Failed to fetch user info.", err=True)

@cli.group()
def config():
    """Manage configuration."""
    pass

@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()
    base_url = cfg.get("base_url", "(not configured)")
    vault = cfg.get("vault", "(not configured)")

    _echo("📋 Current configuration:")
    _echo(f"  API URL : {base_url}")
    _echo(f"  Vault   : {vault}")

    # Fetch user info if token exists
    if TOKEN_FILE.exists():
        try:
            data = curl_request("GET", "/user/info")
            user = data.get("data", {})
            if user:
                username = user.get("username", user.get("email", user.get("displayName", "")))
                if username:
                    _echo(f"  User    : {username}")
                else:
                    _echo("  User    : (logged in, no username)")
            else:
                _echo("  User    : (token invalid)")
        except SystemExit:
            _echo("  User    : (could not fetch)")
    else:
        _echo("  User    : (not logged in)")

@config.command()
@click.argument("value")
def vault(value):
    """Set vault name."""
    cfg = load_config()
    cfg["vault"] = value
    save_config(cfg)
    _echo(f"✅ Vault set to '{value}'")

@config.command()
@click.argument("value")
def url(value):
    """Set API URL."""
    url_val = value.rstrip("/")
    if not url_val.endswith("/api"):
        url_val += "/api"
    cfg = load_config()
    cfg["base_url"] = url_val
    save_config(cfg)
    _echo(f"✅ API URL set to '{url_val}'")

@cli.command()
@click.argument("path", required=False, default="")
def tree(path):
    """Show vault folder tree structure."""
    vault = require_vault()
    params = {"vault": vault}
    if path:
        params["path"] = path
        params["pathHash"] = _compute_path_hash(path)
    data = curl_request("GET", "/folder/tree", params=params)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    tree_data = data.get("data", {})
    if tree_data:
        _echo(f"📂 Vault tree for '{vault}'" + (f" > {path}" if path else "") + ":\n")
        _print_tree(tree_data, indent=0)
    else:
        _echo("📭 No tree data found.")

def _print_tree(node, indent=0):
    """Recursively print tree structure."""
    prefix = "  " * indent + ("├─ " if indent > 0 else "")
    name = node.get("name", node.get("path", "unknown"))
    node_type = node.get("type", node.get("isFolder", "file"))
    icon = "📁" if node_type in ("folder", True) or node.get("isFolder") else "📄"
    _echo(f"{prefix}{icon} {name}")
    children = node.get("children", node.get("sub", []))
    if children:
        for child in children:
            _print_tree(child, indent + 1)

@cli.command()
@click.argument("path")
def backlinks(path):
    """Show notes that link to this note (backlinks)."""
    vault = require_vault()
    data = curl_request("GET", "/note/backlinks", params={"vault": vault, "path": path, "pathHash": _compute_path_hash(path)})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data:
        _echo(f"📭 No backlinks found for '{path}'.")
        return
    data_section = data.get("data")
    if not data_section:
        _echo(f"📭 No backlinks found for '{path}'.")
        return
    if isinstance(data_section, list):
        links = data_section
    elif isinstance(data_section, dict):
        links = data_section.get("list", [])
    else:
        links = []
    if isinstance(links, dict):
        links = links.get("list", [])
    if links:
        _echo(f"🔗 Backlinks for '{path}':\n")
        for link in links:
            link_path = link.get("path", link.get("name", "unknown"))
            context = link.get("context", "")
            if context:
                _echo(f"  📄 {link_path}")
                _echo(f"     {context}")
            else:
                _echo(f"  📄 {link_path}")
        _echo(f"\nTotal: {len(links)}")
    else:
        _echo(f"📭 No backlinks found for '{path}'.")

@cli.command()
@click.argument("path")
def outlinks(path):
    """Show notes that this note links to (outlinks)."""
    vault = require_vault()
    data = curl_request("GET", "/note/outlinks", params={"vault": vault, "path": path, "pathHash": _compute_path_hash(path)})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data:
        _echo(f"📭 No outlinks found for '{path}'.")
        return
    data_section = data.get("data")
    if not data_section:
        _echo(f"📭 No outlinks found for '{path}'.")
        return
    if isinstance(data_section, list):
        links = data_section
    elif isinstance(data_section, dict):
        links = data_section.get("list", [])
    else:
        links = []
    if isinstance(links, dict):
        links = links.get("list", [])
    if links:
        _echo(f"🔗 Outlinks from '{path}':\n")
        for link in links:
            link_path = link.get("path", link.get("name", "unknown"))
            context = link.get("context", "")
            if context:
                _echo(f"  📄 {link_path}")
                _echo(f"     {context}")
            else:
                _echo(f"  📄 {link_path}")
        _echo(f"\nTotal: {len(links)}")
    else:
        _echo(f"📭 No outlinks found for '{path}'.")

@cli.command()
@click.argument("path")
def restore(path):
    """Restore a note from the recycle bin."""
    vault = require_vault()
    # Get actual pathHash from recycle bin
    data = curl_request("GET", "/notes", params={"vault": vault, "isRecycle": "true", "page": 1, "pageSize": 100})
    notes = []
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
    actual_hash = None
    for n in notes:
        if n.get("path") == path:
            actual_hash = n.get("pathHash")
            break
    if not actual_hash:
        _echo(f"❌ Note '{path}' not found in recycle bin.", err=True)
        return

    del_data = curl_request("PUT", "/note/restore", json_data={"vault": vault, "path": path, "pathHash": actual_hash})
    _handle_response(del_data, success_msg=f"✅ Restored '{path}' from recycle bin.")

@cli.command()
@click.argument("path")
@click.option("--set", "set_pairs", multiple=True, help="Set frontmatter key=value (can be repeated)")
@click.option("--remove", "remove_keys", multiple=True, help="Remove frontmatter keys (can be repeated)")
def frontmatter(path, set_pairs, remove_keys):
    """View or edit note frontmatter."""
    vault = require_vault()

    # If no changes, just display current frontmatter
    if not set_pairs and not remove_keys:
        data = curl_request("GET", "/note", params={"vault": vault, "path": path, "pathHash": _compute_path_hash(path)})
        if _ctx.get("json_output"):
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
            return
        content = data.get("data", {}).get("content", "")
        if content:
            # Extract frontmatter (between --- markers)
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1].strip()
                    _echo(f"📋 Frontmatter for '{path}':\n{fm}")
                    return
            _echo(f"📋 No frontmatter found for '{path}'.")
        return

    # Apply changes
    fm_data = {}
    for pair in set_pairs:
        if "=" in pair:
            key, val = pair.split("=", 1)
            fm_data[key.strip()] = val.strip()

    data = curl_request("PATCH", "/note/frontmatter", json_data={
        "vault": vault, "path": path, "pathHash": _compute_path_hash(path), "frontmatter": fm_data, "removeKeys": list(remove_keys)
    })
    _handle_response(data, success_msg=f"✅ Frontmatter updated for '{path}'.")

@cli.command()
@click.argument("path")
@click.option("--expire", help="Expiration time (ISO 8601 or duration like 24h)")
@click.option("--password", help="Access password for the shared link")
def share(path, expire, password):
    """Create a shareable link for a note."""
    vault = require_vault()
    # Get note's pathHash first
    path_hash = _compute_path_hash(path)
    note_data = curl_request("GET", "/note", params={"vault": vault, "path": path, "pathHash": path_hash})
    if not note_data or not note_data.get("data"):
        _echo(f"❌ Could not find note '{path}'.", err=True)
        return
    actual_hash = note_data.get("data", {}).get("pathHash", "")
    if not actual_hash:
        _echo(f"❌ Could not find note '{path}'.", err=True)
        return

    payload = {"vault": vault, "path": path, "pathHash": actual_hash}
    if expire:
        payload["expire"] = expire
    if password:
        payload["password"] = password

    data = curl_request("POST", "/share", json_data=payload)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    share_data = data.get("data", {})
    if isinstance(share_data, str):
        try: share_data = json.loads(share_data)
        except: share_data = {}
    if isinstance(share_data, list) and share_data:
        share_data = share_data[0]
    if isinstance(share_data, dict) and share_data:
        token = share_data.get("token", share_data.get("shareToken", ""))
        url = share_data.get("url", share_data.get("shareUrl", ""))
        _echo(f"🔗 Share link created for '{path}':")
        if url:
            _echo(f"  URL: {url}")
        if token:
            _echo(f"  Token: {token}")
        if expire:
            _echo(f"  Expires: {expire}")
    else:
        _echo(f"❌ Failed to create share link: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)

@cli.command()
@click.argument("path")
def unshare(path):
    """Remove sharing for a note."""
    vault = require_vault()
    # Get note's pathHash
    path_hash = _compute_path_hash(path)
    note_data = curl_request("GET", "/note", params={"vault": vault, "path": path, "pathHash": path_hash})
    actual_hash = note_data.get("data", {}).get("pathHash", "")
    if not actual_hash:
        _echo(f"❌ Note '{path}' not found.", err=True)
        return

    del_data = curl_request("DELETE", "/share", json_data={
        "vault": vault, "path": path, "pathHash": path_hash
    })
    _handle_response(del_data, success_msg=f"✅ Sharing removed for '{path}'.")

@cli.command("shares")
def shares_list():
    """List all active share links."""
    vault = require_vault()
    data = curl_request("GET", "/shares", params={"page": 1, "pageSize": 50})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", data.get("data", []))
    if isinstance(items, dict):
        items = items.get("list", [])
    if items:
        _echo("🔗 Active shares:\n")
        for s in items:
            spath = s.get("path", s.get("notePath", "unknown"))
            stoken = s.get("token", s.get("shareToken", ""))
            sexpire = s.get("expire", s.get("expiresAt", ""))
            _echo(f"  📄 {spath}")
            _echo(f"     Token: {stoken} | Expires: {sexpire}")
        _echo(f"\nTotal: {len(items)}")
    else:
        _echo("📭 No active shares.")

@cli.command("share-password")
@click.argument("path")
@click.argument("password")
def share_password(path, password):
    """Set or change the access password for a shared note."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    data = curl_request("POST", "/share/password", json_data={
        "vault": vault, "path": path, "pathHash": path_hash, "password": password
    })
    _handle_response(data, success_msg=f"✅ Password set for sharing '{path}'.")

@cli.command("share-paths")
def share_paths():
    """List paths of all shared notes in current vault."""
    vault = require_vault()
    data = curl_request("GET", "/notes/share-paths", params={"vault": vault})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # API returns data as a list of strings directly
    paths_data = data.get("data", [])
    if isinstance(paths_data, dict):
        paths_data = paths_data.get("list", paths_data.get("paths", []))
    if paths_data:
        _echo(f"🔗 Shared notes in '{vault}':\n")
        for p in paths_data:
            path = p if isinstance(p, str) else p.get("path", p.get("notePath", "unknown"))
            _echo(f"  📄 {path}")
        _echo(f"\nTotal: {len(paths_data)}")
    else:
        _echo("📭 No shared notes.")

@cli.command()
@click.argument("vault_id", required=False, default="")
def vault_info(vault_name):
    """Show vault details."""
    if not vault_name:
        # If no name provided, show current vault info
        vault_name = require_vault()

    # Get vault list and find by name
    data = curl_request("GET", "/vault")
    vaults_list = []
    if isinstance(data.get("data"), list):
        vaults_list = data["data"]
    elif isinstance(data.get("data"), dict):
        vaults_list = data["data"].get("list", [data["data"]])

    target = None
    for v in vaults_list:
        name = v.get("vault", v.get("name", v.get("vault_name", "")))
        if name == vault_name:
            target = v
            break

    if not target:
        _echo(f"❌ Vault '{vault_name}' not found.", err=True)
        return

    if _ctx.get("json_output"):
        click.echo(json.dumps(target, indent=2, ensure_ascii=False))
        return

    _echo(f"📦 Vault info for '{vault_name}':")
    for key in ("vault", "name", "noteCount", "noteSize", "fileCount", "fileSize", "size", "createdAt", "updatedAt"):
        if key in target and target[key]:
            _echo(f"  {key}: {target[key]}")

@cli.command("recycle-bin")
@click.argument("path", required=False, default="")
def recycle_bin(path):
    """Show notes in the recycle bin."""
    vault = require_vault()
    params = {"vault": vault, "isRecycle": "true", "page": 1, "pageSize": 50}
    if path:
        params["keyword"] = path
    data = curl_request("GET", "/notes", params=params)

    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    notes = []
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
    elif isinstance(data, dict):
        notes = data.get("list", data.get("notes", []))

    if notes:
        _echo("🗑️  Recycle bin:\n")
        for n in notes:
            note_path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            readable = format_timestamp(mtime) if mtime else ""
            _echo(f"  📄 {note_path} ({readable})")
        _echo(f"\nTotal: {len(notes)}")
    else:
        _echo("📭 Recycle bin is empty.")

@cli.command()
def version():
    """Show server version."""
    data = curl_request("GET", "/version")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", data)
    if info:
        _echo("📋 Server version:")
        for key in ("version", "gitTag", "buildTime", "goVersion"):
            if key in info and info[key]:
                _echo(f"  {key}: {info[key]}")
    else:
        _echo(f"❌ Failed to get version info.", err=True)

@cli.command()
def health():
    """Check server health status."""
    data = curl_request("GET", "/health")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    status = data.get("status", data.get("code", 0))
    if status is True or (isinstance(status, int) and status >= 1):
        _echo("✅ Server is healthy.")
    else:
        _echo(f"⚠️ Server health check: {json.dumps(data, indent=2, ensure_ascii=False)}")

@cli.command("vault-create")
@click.argument("name")
def vault_create(name):
    """Create a new vault (requires confirmation)."""
    # API only requires token authentication, not vault config
    get_token()
    click.confirm(f"⚠️ Create new vault '{name}'? This action cannot be undone", abort=True)

    data = curl_request("POST", "/vault", json_data={"vault": name})
    _handle_response(data, success_msg=f"✅ Vault '{name}' created.")

@cli.command("vault-delete")
@click.argument("vault_id")
def vault_delete(vault_id):
    """Delete a vault by ID (requires double confirmation)."""
    # First confirmation
    click.confirm(f"⚠️ WARNING: This will permanently delete vault ID '{vault_id}' and ALL its data!", abort=True)
    # Second confirmation
    click.confirm("🚨 Are you absolutely sure? This action CANNOT be undone!", abort=True)

    data = curl_request("DELETE", "/vault", params={"id": vault_id})
    _handle_response(data, success_msg=f"✅ Vault '{vault_id}' deleted permanently.")


# ==================== Folder Commands (v0.6) ====================

@cli.command("mkdir")
@click.argument("path")
def mkdir(path):
    """Create a new folder or restore a deleted one."""
    vault = require_vault()
    path_hash = _compute_path_hash(path)
    data = curl_request("POST", "/folder", json_data={"path": path, "vault": vault, "pathHash": path_hash})
    _handle_response(data, success_msg=f"✅ Folder '{path}' created/restored.")

@cli.command("folder")
@click.argument("path")
def folder(path):
    """Get folder info by path."""
    vault = require_vault()
    # pathHash is optional for GET /folder; omitting it avoids hash mismatch errors
    data = curl_request("GET", "/folder", params={"vault": vault, "path": path})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    
    info = data.get("data", {})
    if info:
        _echo(f"📂 Folder Info for '{path}':")
        _echo(f"  Path: {info.get('path', 'N/A')}")
        _echo(f"  Created: {info.get('createdAt', 'N/A')}")
        _echo(f"  Updated: {info.get('updatedAt', 'N/A')}")
    else:
        _echo(f"❌ Folder not found or error: {data.get('message', 'Unknown')}", err=True)

@cli.command("folder-files")
@click.argument("path")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
def folder_files(path, page, page_size):
    """List files in a specific folder."""
    vault = require_vault()
    data = curl_request("GET", "/folder/files", params={
        "vault": vault, "path": path, "page": page, "pageSize": page_size
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        _echo(f"📁 Files in '{path}' (Page {page}):\n")
        for f in items:
            name = f.get("path", "N/A")
            size = f.get("size", 0)
            mtime = f.get("updatedAt", f.get("mtime", ""))
            _echo(f"  📄 {name} ({_format_size(size)})")
            if mtime: _echo(f"     └─ Modified: {mtime}")
        _echo(f"\nTotal: {len(items)} items on this page.")
    else:
        _echo(f"📭 No files found in '{path}'.")

@cli.command("folder-notes")
@click.argument("path")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
def folder_notes(path, page, page_size):
    """List notes in a specific folder."""
    vault = require_vault()
    data = curl_request("GET", "/folder/notes", params={
        "vault": vault, "path": path, "page": page, "pageSize": page_size
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        _echo(f"📝 Notes in '{path}' (Page {page}):\n")
        for n in items:
            name = n.get("path", "N/A")
            size = n.get("size", 0)
            version = n.get("version", "")
            mtime = n.get("updatedAt", "")
            _echo(f"  📄 {name} ({_format_size(size)})")
            if version: _echo(f"     └─ v{version} | Updated: {mtime}")
        _echo(f"\nTotal: {len(items)} notes on this page.")
    else:
        _echo(f"📭 No notes found in '{path}'.")

@cli.command("folder-list")
@click.argument("path", required=False, default="")
def folder_list(path):
    """List sub-folders. If no path given, lists root folders."""
    vault = require_vault()
    params = {"vault": vault}
    if path:
        params["path"] = path
    
    data = curl_request("GET", "/folders", params=params)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    folders = data.get("data", [])
    # Handle case where data might be a dict with a list inside
    if isinstance(data.get("data"), dict):
        folders = data["data"].get("list", [data["data"]])
        
    target = path if path else "Root"
    if folders:
        _echo(f"📂 Sub-folders in '{target}':\n")
        for f in folders:
            name = f.get("path", "N/A")
            mtime = f.get("updatedAt", f.get("mtime", ""))
            _echo(f"  📂 {name}")
            if mtime: _echo(f"     └─ Modified: {mtime}")
        _echo(f"\nTotal: {len(folders)} sub-folders.")
    else:
        _echo(f"📭 No sub-folders found in '{target}'.")

@cli.command("folder-delete")
@click.argument("path")
def folder_delete(path):
    """Delete a folder (soft delete)."""
    vault = require_vault()
    click.confirm(f"⚠️ Move folder '{path}' to recycle bin?", abort=True)
    data = curl_request("DELETE", "/folder", json_data={"path": path, "vault": vault})
    _handle_response(data, success_msg=f"✅ Folder '{path}' moved to recycle bin.")

@cli.command("folder-tree")
@click.option("--depth", default=3, help="Max depth of the tree")
def folder_tree(depth):
    """Display the folder tree structure."""
    vault = require_vault()
    data = curl_request("GET", "/folder/tree", params={"vault": vault, "depth": depth})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    
    tree_data = data.get("data", {})
    folders = tree_data.get("folders", [])
    
    _echo(f"🌳 Folder Tree (Vault: {vault}, Depth: {depth}):\n")
    
    def _print_tree(nodes, indent=0):
        for node in nodes:
            name = node.get("name", node.get("path", "N/A"))
            note_count = node.get("noteCount", 0)
            file_count = node.get("fileCount", 0)
            counts = ""
            if note_count or file_count:
                counts = f" ({note_count} notes, {file_count} files)"
            
            prefix = "  " * indent + ("└── " if indent > 0 else "")
            _echo(f"{prefix}📂 {name}{counts}")
            
            children = node.get("children", [])
            if children:
                _print_tree(children, indent + 1)

    _print_tree(folders)
    _echo(f"\n📊 Root Stats: {tree_data.get('rootNoteCount', 0)} notes, {tree_data.get('rootFileCount', 0)} files")


if __name__ == "__main__":
    cli()
