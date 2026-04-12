#!/usr/bin/env python3
"""Fast Note Sync (FNS) CLI - Interact with your Obsidian FNS service from terminal."""
import sys, json, subprocess
from pathlib import Path
from urllib.parse import urlencode
from datetime import datetime, timezone

__version__ = "0.2.0"

# Config directory: ~/.config/fns-cli/ (cross-platform, consistent with other CLI tools)
CONFIG_DIR = Path.home() / ".config" / "fns-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"

DEFAULT_BASE_URL = ""  # Configure via 'fns config url'
DEFAULT_VAULT = ""  # Auto-detected on first login

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
        print("⚠️ Vault not configured. Run one of these:")
        print("   fns vaults          # List available vaults")
        print("   fns config vault <name>  # Set your vault")
        sys.exit(1)
    return vault

def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    print("⚠️ Token not found. Run: fns login")
    sys.exit(1)

def curl_request(method, endpoint, params=None, json_data=None):
    cfg = load_config()
    base_url = cfg.get("base_url", "")
    if not base_url:
        print("⚠️ API URL not configured. Run: fns config url https://your-server/api")
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print(f"❌ curl error: {result.stderr.strip()}")
            sys.exit(1)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("❌ Request timed out")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {result.stdout[:200]}")
        sys.exit(1)

def cmd_delete(path):
    """Move a note to recycle bin."""
    vault = require_vault()
    data = curl_request("DELETE", "/note", params={"vault": vault, "path": path})
    if data.get("code", 0) >= 1 or data.get("status"):
        print(f"✅ Note '{path}' deleted (moved to recycle bin).")
    else:
        print(f"❌ Failed to delete: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_prepend(path, content_or_file):
    """Prepend content to a note (after frontmatter)."""
    vault = require_vault()
    if content_or_file.startswith("@"):
        file_path = content_or_file[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            print(f"❌ File not found: {file_path}")
            return
    else:
        content = content_or_file

    data = curl_request("POST", "/note/prepend", json_data={"vault": vault, "path": path, "content": content})
    if data.get("code", 0) >= 1 or data.get("status"):
        print(f"✅ Prepended to '{path}'.")
    else:
        print(f"❌ Failed to prepend: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_replace(path, search, replace):
    """Find and replace content in a note."""
    vault = require_vault()
    data = curl_request("POST", "/note/replace", json_data={
        "vault": vault, "path": path, "search": search, "replace": replace
    })
    if data.get("code", 0) >= 1 or data.get("status"):
        replacements = data.get("data", {}).get("count", "?")
        print(f"✅ Replaced {replacements} occurrence(s) in '{path}'.")
    else:
        print(f"❌ Failed to replace: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_move(old_path, new_path):
    """Move or rename a note."""
    vault = require_vault()
    data = curl_request("POST", "/note/move", json_data={
        "vault": vault, "path": old_path, "newPath": new_path
    })
    if data.get("code", 0) >= 1 or data.get("status"):
        print(f"✅ Moved '{old_path}' → '{new_path}'.")
    else:
        print(f"❌ Failed to move: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_history(path, page=1):
    """Show note history."""
    vault = require_vault()
    data = curl_request("GET", "/note/histories", params={
        "vault": vault, "path": path, "page": page, "pageSize": 20
    })
    histories = []
    if isinstance(data.get("data"), dict):
        histories = data["data"].get("list", [])
    elif isinstance(data.get("data"), list):
        histories = data["data"]

    if histories:
        print(f"📜 History for '{path}':\n")
        for h in histories:
            hid = h.get("id", h.get("historyId", ""))
            mtime = h.get("mtime", h.get("updatedTimestamp", h.get("createdTimestamp", "")))
            readable = format_timestamp(mtime) if mtime else ""
            size = h.get("size", h.get("contentLength", ""))
            print(f"  📄 [{hid}] {readable} ({size} bytes)")
        print()
    else:
        print(f"📭 No history found for '{path}'.")

def cmd_info():
    """Show current user info."""
    data = curl_request("GET", "/user/info")
    user = data.get("data", {})
    if user:
        print("👤 Current user:")
        for key in ("username", "email", "displayName", "id", "role"):
            if key in user and user[key]:
                print(f"  {key}: {user[key]}")
    else:
        print(f"❌ Failed to fetch user info: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_vaults():
    """List all available vaults from server."""
    data = curl_request("GET", "/vault")
    vaults = []
    if isinstance(data.get("data"), list):
        vaults = data["data"]
    elif isinstance(data.get("data"), dict):
        vaults = data["data"].get("list", [data["data"]])

    if vaults:
        print("📦 Available vaults:")
        for v in vaults:
            name = v.get("name", v.get("vault_name", v.get("id", "unknown")))
            print(f"  🗄️  {name}")
    else:
        print(f"📭 No vaults found. Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_login(credentials, password):
    cfg = load_config()
    base_url = cfg.get("base_url", "")
    if not base_url:
        print("⚠️ API URL not configured. Run: fns config url https://your-server/api")
        sys.exit(1)

    url = f"{base_url}/user/login"
    cmd = ["curl", "-s", "-X", "POST", url,
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"Credentials": credentials, "Password": password})]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        resp = json.loads(result.stdout)
        if resp.get("status") or resp.get("code", 0) >= 1:
            token = resp.get("data", {}).get("token")
            if token:
                TOKEN_FILE.write_text(token)
                print(f"✅ Login successful. Token saved to {TOKEN_FILE}")

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
                        print(f"📦 Auto-set vault to '{vault_name}'")
                    elif vaults:
                        print("📦 Multiple vaults available. Choose one with: fns config vault <name>")
                        vault_names = ", ".join(
                            v.get("name", v.get("vault_name", v.get("id", ""))) for v in vaults
                        )
                        print(f"   Available vaults: {vault_names}")
            else:
                print(f"❌ No token in response: {json.dumps(resp, indent=2)}")
        else:
            print(f"❌ Login failed: {resp.get('message', json.dumps(resp, indent=2))}")
    except Exception as e:
        print(f"❌ Error: {e}")

def cmd_read(path):
    vault = require_vault()
    data = curl_request("GET", "/note", params={"vault": vault, "path": path})
    content = data.get("data", {}).get("content") if isinstance(data.get("data"), dict) else None
    if content is not None:
        print(f"📄 {path}\n{'-'*40}\n{content}")
    else:
        print(f"❌ Unexpected response: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_write(path, content_or_file):
    vault = require_vault()
    # Support @file.txt prefix for local file upload
    if content_or_file.startswith("@"):
        file_path = content_or_file[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            print(f"❌ File not found: {file_path}")
            return
    elif Path(content_or_file).exists():
        content = Path(content_or_file).read_text(encoding="utf-8")
    else:
        content = content_or_file
    data = curl_request("POST", "/note", json_data={"vault": vault, "path": path, "content": content})
    if data.get("code", 0) >= 1:
        print(f"✅ Note '{path}' updated. Syncing to all devices...")
    else:
        print(f"❌ Failed to write: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_append(path, content):
    vault = require_vault()
    # Support @file.txt prefix for local file upload
    if content.startswith("@"):
        file_path = content[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            print(f"❌ File not found: {file_path}")
            return

    params = {"vault": vault, "path": path}

    # Smart newline: Read existing content to ensure we don't merge lines
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
    if data.get("code", 0) >= 1 or data.get("status"):
        print(f"✅ Appended to '{path}'.")
    else:
        print(f"❌ Failed to append: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_list(keyword="", page=1):
    vault = require_vault()
    data = curl_request("GET", "/notes", params={"vault": vault, "keyword": keyword, "page": page, "pageSize": 20})

    notes = []
    pager_info = {}
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
        pager_info = data["data"].get("pager", {})
    elif isinstance(data, dict):
        notes = data.get("list", data.get("notes", []))

    if notes:
        total = pager_info.get("totalRows", len(notes)) if pager_info else len(notes)
        
        print(f"📚 Notes in '{vault}' (Page {page}):\n")
        for n in notes:
            path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            if mtime:
                readable_time = format_timestamp(mtime)
                print(f"  📄 {path} ({readable_time})")
            else:
                print(f"  📄 {path}")
        print(f"\nTotal: {total}")
    else:
        print(f"📭 No notes found.")
        print(json.dumps(data, indent=2, ensure_ascii=False))

def cmd_config(key, value):
    cfg = load_config()
    if key == "vault":
        cfg["vault"] = value
        save_config(cfg)
        print(f"✅ Vault set to '{value}'")
    elif key == "url":
        # Auto-append /api suffix if missing
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        cfg["base_url"] = url
        save_config(cfg)
        print(f"✅ API URL set to '{url}'")
    else:
        print("⚠️ Unknown key. Use 'vault' or 'url'.")

def print_help():
    print(f"""
📝 Fast Note Sync CLI (fns) v{__version__}
Usage: fns <command> [args]

Commands:
  login <user> <pass>   Login and save token
  read <path>           Read a note
  write <path> <text>   Create/Update note (use @file.txt for local file)
  append <path> <text>  Append text to a note
  delete <path>         Delete a note (move to recycle bin)
  prepend <path> <text> Prepend text to a note (after frontmatter)
  replace <path> <old> <new>  Find and replace in note
  move <old> <new>      Move/rename a note
  history <path>        Show note history
  list [keyword]        List notes
  vaults                List available vaults
  info                  Show current user info
  config <key> <val>    Set vault or url
  help                  Show this help
  -v, --version         Show version
    """)

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    if cmd in ("--version", "-v"):
        print(f"fns-cli v{__version__}")
        return
    elif cmd == "help": print_help()
    elif cmd == "login":
        if len(args) < 3:
            print("❌ Usage: fns login <username_or_email> <password>")
        else:
            cmd_login(args[1], args[2])
    elif cmd == "read":
        if len(args) < 2:
            print("❌ Usage: fns read <note_path>")
        else:
            cmd_read(args[1])
    elif cmd == "write":
        if len(args) < 3:
            print("❌ Usage: fns write <note_path> <content|@file.txt>")
        else:
            cmd_write(args[1], args[2])
    elif cmd == "append":
        if len(args) < 3:
            print("❌ Usage: fns append <note_path> <content|@file.txt>")
        else:
            cmd_append(args[1], args[2])
    elif cmd == "delete":
        if len(args) < 2:
            print("❌ Usage: fns delete <note_path>")
        else:
            cmd_delete(args[1])
    elif cmd == "prepend":
        if len(args) < 3:
            print("❌ Usage: fns prepend <note_path> <content|@file.txt>")
        else:
            cmd_prepend(args[1], args[2])
    elif cmd == "replace":
        if len(args) < 4:
            print("❌ Usage: fns replace <note_path> <search> <replace>")
        else:
            cmd_replace(args[1], args[2], args[3])
    elif cmd == "move":
        if len(args) < 3:
            print("❌ Usage: fns move <old_path> <new_path>")
        else:
            cmd_move(args[1], args[2])
    elif cmd == "history":
        if len(args) < 2:
            print("❌ Usage: fns history <note_path>")
        else:
            cmd_history(args[1])
    elif cmd == "list":
        cmd_list(keyword=args[1] if len(args) > 1 else "")
    elif cmd == "vaults":
        cmd_vaults()
    elif cmd == "info":
        cmd_info()
    elif cmd == "config":
        if len(args) < 3:
            print("❌ Usage: fns config <url|vault> <value>")
        else:
            cmd_config(args[1], args[2])
    else:
        print(f"❌ Unknown command: {cmd}")

if __name__ == "__main__":
    main()
