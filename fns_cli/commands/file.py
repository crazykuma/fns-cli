"""Fast Note Sync CLI - File/Attachment commands."""
import json
import subprocess
import sys

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, require_vault
from fns_cli.formatting import echo, format_size
from fns_cli.hashing import compute_path_hash
from pathlib import Path


@click.command("file-info")
@click.argument("path")
def file_info(path):
    """Get file/attachment metadata."""
    vault = require_vault()
    data = curl_request("GET", "/file/info", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", {})
    if info:
        echo(f"📎 File Info for '{path}':")
        for key in ("path", "size", "contentType", "contentHash", "createdAt", "updatedAt"):
            if key in info and info[key]:
                echo(f"  {key}: {info[key]}")
    else:
        echo(f"❌ File not found: {data.get('message', 'Unknown')}", err=True)


@click.command("file-download")
@click.argument("path")
@click.option("-o", "--output", "output_path", help="Output file path")
def file_download(path, output_path):
    """Download a file/attachment."""
    vault = require_vault()
    from fns_cli.config import get_token, load_config
    import urllib.parse

    cfg = load_config()
    base_url = cfg.get("base_url", "")
    token = get_token()

    url = f"{base_url}/file?vault={urllib.parse.quote(vault)}&path={urllib.parse.quote(path)}"
    if output_path:
        url += f"&output={urllib.parse.quote(output_path)}"

    cmd = ["curl", "-s", "-X", "GET", url,
           "-H", f"Authorization: Bearer {token}",
           "-H", "X-Client: WebGui",
           "-H", "User-Agent: Mozilla/5.0"]

    if output_path:
        cmd.extend(["-o", output_path])
    else:
        cmd.extend(["-O"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            echo(f"❌ Download failed: {result.stderr.strip()}", err=True)
            sys.exit(1)
        echo(f"✅ File downloaded successfully.")
    except subprocess.TimeoutExpired:
        echo("❌ Download timed out.", err=True)
        sys.exit(1)


@click.command("file-list")
@click.argument("keyword", required=False, default="")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
@click.option("--recycle", is_flag=True, help="Show deleted files in recycle bin")
@click.option("--sort-by", "sort_by", default="", help="Sort field: path, size, updatedAt, createdAt")
@click.option("--sort-order", "sort_order", default="", help="Sort order: asc or desc")
def file_list(keyword, page, page_size, recycle, sort_by, sort_order):
    """List files/attachments. Optionally filter by keyword."""
    vault = require_vault()
    params = {"vault": vault, "page": page, "pageSize": page_size}
    if keyword:
        params["keyword"] = keyword
    if recycle:
        params["isRecycle"] = "true"
    if sort_by:
        params["sortBy"] = sort_by
    if sort_order:
        params["sortOrder"] = sort_order

    data = curl_request("GET", "/files", params=params)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        label = "🗑️ Recycle bin files" if recycle else "📎 Files"
        echo(f"{label} (Page {page}):\n")
        for f in items:
            fpath = f.get("path", "unknown")
            size = f.get("size", 0)
            size_str = format_size(size)
            echo(f"  📄 {fpath} ({size_str})")
        total = data.get("data", {}).get("pager", {}).get("totalRows", len(items))
        echo(f"\nTotal: {total} files")
    else:
        echo("📭 No files found.")


@click.command("file-delete")
@click.argument("path")
def file_delete(path):
    """Delete a file/attachment (soft delete to recycle bin)."""
    vault = require_vault()
    click.confirm(f"⚠️ Move file '{path}' to recycle bin?", abort=True)
    data = curl_request("DELETE", "/file", params={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    handle_response(data, success_msg=f"✅ File '{path}' moved to recycle bin.")


@click.command("file-rename")
@click.argument("old_path")
@click.argument("new_path")
def file_rename(old_path, new_path):
    """Rename a file/attachment."""
    vault = require_vault()
    data = curl_request("POST", "/file/rename", json_data={
        "vault": vault,
        "oldPath": old_path,
        "oldPathHash": compute_path_hash(old_path),
        "path": new_path,
        "pathHash": compute_path_hash(new_path),
    })
    handle_response(data, success_msg=f"✅ Renamed '{old_path}' → '{new_path}'.")


@click.command("file-restore")
@click.argument("path")
def file_restore(path):
    """Restore a file from the recycle bin."""
    vault = require_vault()
    data = curl_request("PUT", "/file/restore", json_data={
        "vault": vault, "path": path, "pathHash": compute_path_hash(path)
    })
    handle_response(data, success_msg=f"✅ Restored file '{path}' from recycle bin.")


@click.command("file-recycle-clear")
@click.argument("paths", required=False, nargs=-1)
def file_recycle_clear(paths):
    """Permanently delete files from recycle bin."""
    vault = require_vault()
    if paths:
        for p in paths:
            data = curl_request("DELETE", "/file/recycle-clear", json_data={
                "vault": vault, "path": p, "pathHash": compute_path_hash(p)
            })
            handle_response(data, success_msg=f"✅ Permanently deleted '{p}'.")
    else:
        click.confirm("⚠️ Permanently delete ALL files in recycle bin?", abort=True)
        data = curl_request("DELETE", "/file/recycle-clear", json_data={"vault": vault})
        handle_response(data, success_msg="✅ Recycle bin cleared.")
