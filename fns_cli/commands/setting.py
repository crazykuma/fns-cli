"""Fast Note Sync CLI - Setting commands."""
import json
from pathlib import Path

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, require_vault
from fns_cli.formatting import echo, format_size
from fns_cli.hashing import compute_path_hash


@click.command("setting-list")
@click.argument("keyword", required=False, default="")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
def setting_list(keyword, page, page_size):
    """List user settings. Optionally filter by keyword."""
    vault = require_vault()
    params = {"vault": vault, "page": page, "pageSize": page_size}
    if keyword:
        params["keyword"] = keyword

    data = curl_request("GET", "/settings", params=params)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        echo(f"⚙️ Settings (Page {page}):\n")
        for s in items:
            spath = s.get("path", "unknown")
            size = s.get("size", 0)
            size_str = format_size(size)
            echo(f"  📄 {spath} ({size_str})")
        total = data.get("data", {}).get("pager", {}).get("totalRows", len(items))
        echo(f"\nTotal: {total} settings")
    else:
        echo("📭 No settings found.")


@click.command("setting-get")
@click.argument("path")
def setting_get(path):
    """Get a setting by path."""
    vault = require_vault()
    data = curl_request("GET", "/setting", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", {})
    if info:
        content = info.get("content", "")
        if content:
            echo(content)
        else:
            echo(f"⚙️ Setting '{path}':")
            for key in ("path", "size", "contentHash", "createdAt", "updatedAt"):
                if key in info and info[key]:
                    echo(f"  {key}: {info[key]}")
    else:
        echo(f"❌ Setting not found: {data.get('message', 'Unknown')}", err=True)


@click.command("setting-create")
@click.argument("path")
@click.argument("content")
def setting_create(path, content):
    """Create or update a setting."""
    vault = require_vault()
    if content.startswith("@"):
        file_path = content[1:]
        if Path(file_path).exists():
            content = Path(file_path).read_text(encoding="utf-8")
        else:
            echo(f"❌ File not found: {file_path}", err=True)
            return

    data = curl_request("POST", "/setting", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path), "content": content
    })
    handle_response(data, success_msg=f"✅ Setting '{path}' updated.")


@click.command("setting-delete")
@click.argument("path")
def setting_delete(path):
    """Delete a setting (soft delete)."""
    vault = require_vault()
    click.confirm(f"⚠️ Delete setting '{path}'?", abort=True)
    data = curl_request("DELETE", "/setting", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    handle_response(data, success_msg=f"✅ Setting '{path}' deleted.")


@click.command("setting-rename")
@click.argument("old_path")
@click.argument("new_path")
def setting_rename(old_path, new_path):
    """Rename a setting."""
    vault = require_vault()
    data = curl_request("POST", "/setting/rename", json_data={
        "vault": vault,
        "oldPath": old_path,
        "oldPathHash": compute_path_hash(old_path),
        "newPath": new_path,
        "newPathHash": compute_path_hash(new_path),
    })
    handle_response(data, success_msg=f"✅ Renamed '{old_path}' → '{new_path}'.")
