"""Fast Note Sync CLI - Folder commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, require_vault
from fns_cli.formatting import echo
from fns_cli.hashing import compute_path_hash


@click.command("mkdir")
@click.argument("path")
def mkdir(path):
    """Create a new folder or restore a deleted one."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    data = curl_request("POST", "/folder", json_data={
        "path": path, "vault": vault, "pathHash": path_hash
    })
    handle_response(data, success_msg=f"✅ Folder '{path}' created/restored.")


@click.command("folder")
@click.argument("path")
def folder(path):
    """Get folder info by path."""
    vault = require_vault()
    data = curl_request("GET", "/folder", params={"vault": vault, "path": path})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", {})
    if info:
        echo(f"📂 Folder Info for '{path}':")
        echo(f"  Path: {info.get('path', 'N/A')}")
        echo(f"  Created: {info.get('createdAt', 'N/A')}")
        echo(f"  Updated: {info.get('updatedAt', 'N/A')}")
    else:
        echo(f"❌ Folder not found or error: {data.get('message', 'Unknown')}", err=True)


@click.command("folder-files")
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
        echo(f"📁 Files in '{path}' (Page {page}):\n")
        for f in items:
            name = f.get("path", "N/A")
            size = f.get("size", 0)
            mtime = f.get("updatedAt", f.get("mtime", ""))
            echo(f"  📄 {name} ({size} bytes)")
            if mtime:
                echo(f"     └─ Modified: {mtime}")
        echo(f"\nTotal: {len(items)} items on this page.")
    else:
        echo(f"📭 No files found in '{path}'.")


@click.command("folder-notes")
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
        echo(f"📝 Notes in '{path}' (Page {page}):\n")
        for n in items:
            name = n.get("path", "N/A")
            size = n.get("size", 0)
            version = n.get("version", "")
            mtime = n.get("updatedAt", "")
            echo(f"  📄 {name} ({size} bytes)")
            if version:
                echo(f"     └─ v{version} | Updated: {mtime}")
        echo(f"\nTotal: {len(items)} notes on this page.")
    else:
        echo(f"📭 No notes found in '{path}'.")


@click.command("folder-list")
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
    if isinstance(data.get("data"), dict):
        folders = data["data"].get("list", [data["data"]])

    target = path if path else "Root"
    if folders:
        echo(f"📂 Sub-folders in '{target}':\n")
        for f in folders:
            name = f.get("path", "N/A")
            mtime = f.get("updatedAt", f.get("mtime", ""))
            echo(f"  📂 {name}")
            if mtime:
                echo(f"     └─ Modified: {mtime}")
        echo(f"\nTotal: {len(folders)} sub-folders.")
    else:
        echo(f"📭 No sub-folders found in '{target}'.")


@click.command("folder-delete")
@click.argument("path")
def folder_delete(path):
    """Delete a folder (soft delete)."""
    vault = require_vault()
    click.confirm(f"⚠️ Move folder '{path}' to recycle bin?", abort=True)
    data = curl_request("DELETE", "/folder", json_data={"path": path, "vault": vault})
    handle_response(data, success_msg=f"✅ Folder '{path}' moved to recycle bin.")


@click.command("folder-tree")
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

    echo(f"🌳 Folder Tree (Vault: {vault}, Depth: {depth}):\n")

    def _print_tree(nodes, indent=0):
        for node in nodes:
            name = node.get("name", node.get("path", "N/A"))
            note_count = node.get("noteCount", 0)
            file_count = node.get("fileCount", 0)
            counts = ""
            if note_count or file_count:
                counts = f" ({note_count} notes, {file_count} files)"

            prefix = "  " * indent + ("└── " if indent > 0 else "")
            echo(f"{prefix}📂 {name}{counts}")

            children = node.get("children", [])
            if children:
                _print_tree(children, indent + 1)

    _print_tree(folders)
    echo(f"\n📊 Root Stats: {tree_data.get('rootNoteCount', 0)} notes, {tree_data.get('rootFileCount', 0)} files")
