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

__version__ = "0.3.0"

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
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
@click.argument("credentials")
@click.argument("password")
def login(credentials, password):
    """Login and save token."""
    cfg = load_config()
    base_url = cfg.get("base_url", "")
    if not base_url:
        _echo("⚠️ API URL not configured. Run: fns config url https://your-server/api", err=True)
        sys.exit(1)

    url = f"{base_url}/user/login"
    cmd = ["curl", "-s", "-X", "POST", url,
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"Credentials": credentials, "Password": password})]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        resp = json.loads(result.stdout)
        if _ctx.get("json_output"):
            click.echo(json.dumps(resp, indent=2, ensure_ascii=False))
            return

        if resp.get("status") or resp.get("code", 0) >= 1:
            token = resp.get("data", {}).get("token")
            if token:
                TOKEN_FILE.write_text(token)
                _echo(f"✅ Login successful. Token saved to {TOKEN_FILE}")

                # Auto-fetch vaults and set default if not configured
                if not cfg.get("vault"):
                    vault_data = curl_request("GET", "/vault")
                    vaults = []
                    if isinstance(vault_data.get("data"), list):
                        vaults = vault_data["data"]
                    elif isinstance(vault_data.get("data"), dict):
                        vaults = vault_data["data"].get("list", [vault_data["data"]])

                    if len(vaults) == 1:
                        vault_name = vaults[0].get("name", vaults[0].get("vault_name", vaults[0].get("id", "")))
                        cfg["vault"] = vault_name
                        save_config(cfg)
                        _echo(f"📦 Auto-set vault to '{vault_name}'")
                    elif vaults:
                        _echo("📦 Multiple vaults available. Choose one with: fns config vault <name>")
                        vault_names = ", ".join(
                            v.get("name", v.get("vault_name", v.get("id", ""))) for v in vaults
                        )
                        _echo(f"   Available vaults: {vault_names}")
            else:
                _echo(f"❌ No token in response: {json.dumps(resp, indent=2)}", err=True)
        else:
            _echo(f"❌ Login failed: {resp.get('message', json.dumps(resp, indent=2))}", err=True)
    except Exception as e:
        _echo(f"❌ Error: {e}", err=True)

@cli.command()
@click.argument("path")
def read(path):
    """Read a note."""
    vault = require_vault()
    data = curl_request("GET", "/note", params={"vault": vault, "path": path})
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

    data = curl_request("POST", "/note", json_data={"vault": vault, "path": path, "content": content})
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

    params = {"vault": vault, "path": path}
    read_resp = curl_request("GET", "/note", params=params)
    existing = ""
    if isinstance(read_resp.get("data"), dict):
        existing = read_resp["data"].get("content", "")

    if existing and not existing.endswith("\n\n"):
        if existing.endswith("\n"):
            content = "\n" + content
        else:
            content = "\n\n" + content

    data = curl_request("POST", "/note/append", json_data={"vault": vault, "path": path, "content": content})
    _handle_response(data, success_msg=f"✅ Appended to '{path}'.")

@cli.command()
@click.argument("path")
def delete(path):
    """Delete a note (move to recycle bin)."""
    vault = require_vault()
    data = curl_request("DELETE", "/note", params={"vault": vault, "path": path})
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

    data = curl_request("POST", "/note/prepend", json_data={"vault": vault, "path": path, "content": content})
    _handle_response(data, success_msg=f"✅ Prepended to '{path}'.")

@cli.command()
@click.argument("path")
@click.argument("search")
@click.argument("replace_text")
def replace(path, search, replace_text):
    """Find and replace in note."""
    vault = require_vault()
    data = curl_request("POST", "/note/replace", json_data={
        "vault": vault, "path": path, "find": search, "replace": replace_text
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
        "vault": vault, "path": old_path, "destination": new_path
    })
    _handle_response(data, success_msg=f"✅ Moved '{old_path}' → '{new_path}'.")

@cli.command()
@click.argument("path")
@click.option("--page", default=1, help="Page number")
def history(path, page):
    """Show note history."""
    vault = require_vault()
    data = curl_request("GET", "/note/histories", params={
        "vault": vault, "path": path, "page": page, "pageSize": 20
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
        _echo()
    else:
        _echo(f"📭 No history found for '{path}'.")

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

@cli.command()
@click.argument("key")
@click.argument("value")
def config(key, value):
    """Set vault or url."""
    cfg = load_config()
    if key == "vault":
        cfg["vault"] = value
        save_config(cfg)
        _echo(f"✅ Vault set to '{value}'")
    elif key == "url":
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        cfg["base_url"] = url
        save_config(cfg)
        _echo(f"✅ API URL set to '{url}'")
    else:
        _echo("⚠️ Unknown key. Use 'vault' or 'url'.", err=True)

if __name__ == "__main__":
    cli()
