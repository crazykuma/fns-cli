"""Fast Note Sync CLI - Note commands."""
import json
import sys

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, get_token, load_config, require_vault, save_config, TOKEN_FILE
from fns_cli.formatting import echo, format_timestamp
from fns_cli.hashing import compute_path_hash
from pathlib import Path


@click.command()
@click.argument("path")
def read(path):
    """Read a note."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    data = curl_request("GET", "/note", params={"vault": vault, "path": path, "pathHash": path_hash})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    content = data.get("data", {}).get("content") if isinstance(data.get("data"), dict) else None
    if content is not None:
        echo(f"📄 {path}\n{'-'*40}\n{content}")
    else:
        echo(f"❌ Unexpected response: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)


@click.command()
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
            echo(f"❌ File not found: {file_path}", err=True)
            return
    elif Path(content_or_file).exists():
        content = Path(content_or_file).read_text(encoding="utf-8")
    else:
        content = content_or_file

    data = curl_request("POST", "/note", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path), "content": content
    })
    handle_response(data, success_msg=f"✅ Note '{path}' updated. Syncing to all devices...")


@click.command()
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
            echo(f"❌ File not found: {file_path}", err=True)
            return

    data = curl_request("POST", "/note/append", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path), "content": content
    })
    handle_response(data, success_msg=f"✅ Appended to '{path}'.")


@click.command()
@click.argument("path")
def delete(path):
    """Delete a note (move to recycle bin)."""
    vault = require_vault()
    data = curl_request("DELETE", "/note", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    handle_response(data, success_msg=f"✅ Note '{path}' deleted (moved to recycle bin).")


@click.command()
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
            echo(f"❌ File not found: {file_path}", err=True)
            return
    else:
        content = content_or_file

    data = curl_request("POST", "/note/prepend", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path), "content": content
    })
    handle_response(data, success_msg=f"✅ Prepended to '{path}'.")


@click.command()
@click.argument("path")
@click.argument("search")
@click.argument("replace_text")
def replace(path, search, replace_text):
    """Find and replace in note."""
    vault = require_vault()
    data = curl_request("POST", "/note/replace", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path),
        "find": search, "replace": replace_text
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if data.get("code", 0) >= 1 or data.get("status"):
        # FIX: backend returns "matchCount" not "count"
        replacements = data.get("data", {}).get("matchCount", "?")
        echo(f"✅ Replaced {replacements} occurrence(s) in '{path}'.")
    else:
        echo(f"❌ Failed to replace: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)


@click.command(name="move")
@click.argument("old_path")
@click.argument("new_path")
def move_note(old_path, new_path):
    """Move/rename a note."""
    vault = require_vault()
    data = curl_request("POST", "/note/move", json_data={
        "vault": vault, "path": old_path, "pathHash": compute_path_hash(old_path),
        "destination": new_path
    })
    handle_response(data, success_msg=f"✅ Moved '{old_path}' → '{new_path}'.")


@click.command()
@click.argument("path")
@click.option("--page", default=1, help="Page number")
def history(path, page):
    """Show note history."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
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
        echo(f"📜 History for '{path}':\n")
        for h in histories:
            hid = h.get("id", h.get("historyId", ""))
            mtime = h.get("mtime", h.get("updatedTimestamp", h.get("createdTimestamp", "")))
            readable = format_timestamp(mtime) if mtime else ""
            size = h.get("size", h.get("contentLength", ""))
            echo(f"  📄 [{hid}] {readable} ({size} bytes)")
        echo("")
    else:
        echo(f"📭 No history found for '{path}'.")


@click.command("history-view")
@click.argument("path")
@click.argument("history_id")
def history_view(path, history_id):
    """View a specific historical version of a note."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    data = curl_request("GET", "/note/history", params={
        "vault": vault, "path": path, "pathHash": path_hash, "id": history_id
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    content = data.get("data", {}).get("content")
    diffs = data.get("data", {}).get("diffs", [])

    if diffs:
        echo(f"📜 History #{history_id} of '{path}':\n{'-'*40}")
        for diff in diffs:
            diff_type = diff.get("Type", diff.get("type", 0))
            diff_text = diff.get("Text", diff.get("text", ""))
            prefix = "+" if diff_type == 1 else "-" if diff_type == 2 else " "
            echo(f"{prefix} {diff_text}")
    elif content:
        echo(f"📜 History #{history_id} of '{path}':\n{'-'*40}\n{content}")
    else:
        echo(f"❌ History #{history_id} not found or has no content.")


@click.command("history-restore")
@click.argument("path")
@click.argument("history_id")
def history_restore(path, history_id):
    """Restore a note to a specific historical version."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    click.confirm(f"⚠️ Restore '{path}' to version #{history_id}? Current content will be overwritten.", abort=True)

    data = curl_request("PUT", "/note/history/restore", json_data={
        "vault": vault, "path": path, "pathHash": path_hash, "historyId": int(history_id)
    })
    handle_response(data, success_msg=f"✅ Restored '{path}' to version #{history_id}.")


@click.command("rename")
@click.argument("old_path")
@click.argument("new_path")
def rename(old_path, new_path):
    """Rename a note to a new path."""
    vault = require_vault()
    old_path_hash = compute_path_hash(old_path)
    note_data = curl_request("GET", "/note", params={
        "vault": vault, "path": old_path, "pathHash": old_path_hash
    })
    actual_hash = note_data.get("data", {}).get("pathHash", "")
    if not actual_hash:
        echo(f"❌ Note '{old_path}' not found.", err=True)
        return

    new_path_hash = compute_path_hash(new_path)

    data = curl_request("POST", "/note/rename", json_data={
        "vault": vault,
        "oldPath": old_path,
        "oldPathHash": actual_hash,
        "path": new_path,
        "pathHash": new_path_hash
    })
    handle_response(data, success_msg=f"✅ Renamed '{old_path}' → '{new_path}'.")


@click.command("recycle-clear")
@click.argument("paths", nargs=-1, required=False)
def recycle_clear(paths):
    """Permanently delete notes in recycle bin. Without args, clears entire bin."""
    vault = require_vault()
    if not paths:
        click.confirm("⚠️ Permanently delete ALL notes in recycle bin?", abort=True)
        data = curl_request("DELETE", "/note/recycle-clear", json_data={"vault": vault})
        handle_response(data, success_msg="✅ Recycle bin cleared.")
    else:
        for p in paths:
            data = curl_request("DELETE", "/note/recycle-clear", json_data={
                "vault": vault, "path": p, "pathHash": compute_path_hash(p)
            })
            handle_response(data, success_msg=f"✅ Permanently deleted '{p}'.")


@click.command()
@click.argument("path")
def restore(path):
    """Restore a note from the recycle bin."""
    vault = require_vault()
    data = curl_request("GET", "/notes", params={
        "vault": vault, "isRecycle": "true", "page": 1, "pageSize": 100
    })
    notes = []
    if isinstance(data.get("data"), dict):
        notes = data["data"].get("list", [])
    actual_hash = None
    for n in notes:
        if n.get("path") == path:
            actual_hash = n.get("pathHash")
            break
    if not actual_hash:
        echo(f"❌ Note '{path}' not found in recycle bin.", err=True)
        return

    del_data = curl_request("PUT", "/note/restore", json_data={
        "vault": vault, "path": path, "pathHash": actual_hash
    })
    handle_response(del_data, success_msg=f"✅ Restored '{path}' from recycle bin.")


@click.command()
@click.argument("path")
@click.option("--set", "set_pairs", multiple=True, help="Set frontmatter key=value (can be repeated)")
@click.option("--remove", "remove_keys", multiple=True, help="Remove frontmatter keys (can be repeated)")
def frontmatter(path, set_pairs, remove_keys):
    """View or edit note frontmatter."""
    vault = require_vault()

    if not set_pairs and not remove_keys:
        data = curl_request("GET", "/note", params={
            "vault": vault, "path": path, "pathHash": compute_path_hash(path)
        })
        if _ctx.get("json_output"):
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
            return
        content = data.get("data", {}).get("content", "")
        if content:
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1].strip()
                    echo(f"📋 Frontmatter for '{path}':\n{fm}")
                    return
            echo(f"📋 No frontmatter found for '{path}'.")
        return

    # Build updates dict from --set key=value pairs
    updates = {}
    for pair in set_pairs:
        if "=" in pair:
            key, val = pair.split("=", 1)
            updates[key.strip()] = val.strip()

    # FIX: backend expects "updates" and "remove" fields
    data = curl_request("PATCH", "/note/frontmatter", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path),
        "updates": updates, "remove": list(remove_keys)
    })
    handle_response(data, success_msg=f"✅ Frontmatter updated for '{path}'.")


@click.command()
@click.argument("path")
@click.option("--page", default=1, help="Page number")
def list_notes(path, page):
    """List notes (optional keyword search)."""
    vault = require_vault()
    data = curl_request("GET", "/notes", params={
        "vault": vault, "keyword": path, "page": page, "pageSize": 20
    })

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
        echo(f"📚 Notes in '{vault}' (Page {page}):\n")
        for n in notes:
            note_path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            if mtime:
                echo(f"  📄 {note_path} ({format_timestamp(mtime)})")
            else:
                echo(f"  📄 {note_path}")
        echo(f"\nTotal: {total}")
    else:
        echo("📭 No notes found.")


@click.command()
@click.argument("path", required=False, default="")
def tree(path):
    """Show vault folder tree structure."""
    vault = require_vault()
    params = {"vault": vault}
    if path:
        params["path"] = path
        params["pathHash"] = compute_path_hash(path)
    data = curl_request("GET", "/folder/tree", params=params)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    tree_data = data.get("data", {})
    if tree_data:
        echo(f"📂 Vault tree for '{vault}'" + (f" > {path}" if path else "") + ":\n")
        _print_tree(tree_data, indent=0)
    else:
        echo("📭 No tree data found.")


def _print_tree(node, indent=0):
    """Recursively print tree structure."""
    prefix = "  " * indent + ("├─ " if indent > 0 else "")
    name = node.get("name", node.get("path", "unknown"))
    node_type = node.get("type", node.get("isFolder", "file"))
    icon = "📁" if node_type in ("folder", True) or node.get("isFolder") else "📄"
    echo(f"{prefix}{icon} {name}")
    children = node.get("children", node.get("sub", []))
    if children:
        for child in children:
            _print_tree(child, indent + 1)


@click.command("recycle-bin")
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
        echo("🗑️  Recycle bin:\n")
        for n in notes:
            note_path = n.get("path", n.get("name", n.get("title", "unknown")))
            mtime = n.get("mtime", n.get("modified", ""))
            readable = format_timestamp(mtime) if mtime else ""
            echo(f"  📄 {note_path} ({readable})")
        echo(f"\nTotal: {len(notes)}")
    else:
        echo("📭 Recycle bin is empty.")


@click.command()
@click.argument("path")
def backlinks(path):
    """Show notes that link to this note (backlinks)."""
    vault = require_vault()
    data = curl_request("GET", "/note/backlinks", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data:
        echo(f"📭 No backlinks found for '{path}'.")
        return
    data_section = data.get("data")
    if not data_section:
        echo(f"📭 No backlinks found for '{path}'.")
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
        echo(f"🔗 Backlinks for '{path}':\n")
        for link in links:
            link_path = link.get("path", link.get("name", "unknown"))
            context = link.get("context", "")
            if context:
                echo(f"  📄 {link_path}")
                echo(f"     {context}")
            else:
                echo(f"  📄 {link_path}")
        echo(f"\nTotal: {len(links)}")
    else:
        echo(f"📭 No backlinks found for '{path}'.")


@click.command()
@click.argument("path")
def outlinks(path):
    """Show notes that this note links to (outlinks)."""
    vault = require_vault()
    data = curl_request("GET", "/note/outlinks", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data:
        echo(f"📭 No outlinks found for '{path}'.")
        return
    data_section = data.get("data")
    if not data_section:
        echo(f"📭 No outlinks found for '{path}'.")
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
        echo(f"🔗 Outlinks from '{path}':\n")
        for link in links:
            link_path = link.get("path", link.get("name", "unknown"))
            context = link.get("context", "")
            if context:
                echo(f"  📄 {link_path}")
                echo(f"     {context}")
            else:
                echo(f"  📄 {link_path}")
        echo(f"\nTotal: {len(links)}")
    else:
        echo(f"📭 No outlinks found for '{path}'.")
