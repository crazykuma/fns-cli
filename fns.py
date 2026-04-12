#!/usr/bin/env python3
"""Fast Note Sync (FNS) CLI - Interact with your Obsidian FNS service from terminal."""
import os, sys, json, subprocess
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fns-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = Path.home() / ".fns_token"

DEFAULT_BASE_URL = ""  # Configure via 'fns config url'
DEFAULT_VAULT = "Main"

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"base_url": DEFAULT_BASE_URL, "vault": DEFAULT_VAULT}

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

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
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += f"?{qs}"
    
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
            else:
                print(f"❌ No token in response: {json.dumps(resp, indent=2)}")
        else:
            print(f"❌ Login failed: {resp.get('message', json.dumps(resp, indent=2))}")
    except Exception as e:
        print(f"❌ Error: {e}")

def cmd_read(path):
    data = curl_request("GET", "/note", params={"vault": load_config()["vault"], "path": path})
    content = data.get("data", {}).get("content") if isinstance(data.get("data"), dict) else None
    if content is not None:
        print(f"📄 {path}\n{'-'*40}\n{content}")
    else:
        print(f"❌ Unexpected response: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_write(path, content_or_file):
    if Path(content_or_file).exists():
        content = Path(content_or_file).read_text()
    else:
        content = content_or_file
    data = curl_request("POST", "/note", json_data={"vault": load_config()["vault"], "path": path, "content": content})
    if data.get("code", 0) >= 1:
        print(f"✅ Note '{path}' updated. Syncing to all devices...")
    else:
        print(f"❌ Failed to write: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_append(path, content):
    if Path(content).exists():
        content = Path(content).read_text()
    
    cfg = load_config()
    params = {"vault": cfg["vault"], "path": path}
    
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
    
    data = curl_request("POST", "/note/append", json_data={"vault": cfg["vault"], "path": path, "content": content})
    if data.get("code", 0) >= 1 or data.get("status"):
        print(f"✅ Appended to '{path}'.")
    else:
        print(f"❌ Failed to append: {json.dumps(data, indent=2, ensure_ascii=False)}")

def cmd_list(keyword="", page=1):
    data = curl_request("GET", "/notes", params={"vault": load_config()["vault"], "keyword": keyword, "page": page, "pageSize": 20})
    
    notes = []
    pager_info = {}
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
        pager_info = data["data"].get("pager", {})
    elif isinstance(data, dict):
        notes = data.get("list", data.get("notes", []))
    
    if notes:
        vault = load_config()["vault"]
        total = pager_info.get("totalRows", len(notes)) if pager_info else len(notes)
        
        print(f"📚 Notes in '{vault}' (Page {page}):\n")
        for n in notes:
            path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            if mtime:
                print(f"  📄 {path} ({mtime})")
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
        cfg["base_url"] = value
        save_config(cfg)
        print(f"✅ API URL set to '{value}'")
    else:
        print("⚠️ Unknown key. Use 'vault' or 'url'.")

def print_help():
    print("""
📝 Fast Note Sync CLI (fns)
Usage: fns <command> [args]

Commands:
  login <user> <pass>   Login and save token
  read <path>           Read a note
  write <path> <text>   Create/Update note (use @file.txt for local file)
  append <path> <text>  Append text to a note
  list [keyword]        List notes
  config <key> <val>    Set vault or url
  help                  Show this help
    """)

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"
    
    if cmd == "help": print_help()
    elif cmd == "login": 
        if len(args) < 3:
            print("❌ Usage: fns login <username_or_email> <password>")
        else:
            cmd_login(args[1], args[2])
    elif cmd == "read": cmd_read(args[1])
    elif cmd == "write": cmd_write(args[1], args[2])
    elif cmd == "append": cmd_append(args[1], args[2])
    elif cmd == "list": cmd_list(keyword=args[1] if len(args) > 1 else "")
    elif cmd == "config": cmd_config(args[1], args[2])
    else: print(f"❌ Unknown command: {cmd}")

if __name__ == "__main__":
    main()
