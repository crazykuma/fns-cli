"""Fast Note Sync CLI - Share commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, require_vault
from fns_cli.formatting import echo
from fns_cli.hashing import compute_path_hash


def _get_note_hash(path, vault):
    """Get note's actual pathHash from server."""
    path_hash = compute_path_hash(path)
    note_data = curl_request("GET", "/note", params={
        "vault": vault, "path": path, "pathHash": path_hash
    })
    if not note_data or not note_data.get("data"):
        return None
    return note_data.get("data", {}).get("pathHash", "")


@click.command()
@click.argument("path")
@click.option("--expire", help="Expiration time (ISO 8601 or duration like 24h)")
@click.option("--password", help="Access password for the shared link")
def share(path, expire, password):
    """Create a shareable link for a note."""
    vault = require_vault()
    actual_hash = _get_note_hash(path, vault)
    if not actual_hash:
        echo(f"❌ Could not find note '{path}'.", err=True)
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
        try:
            share_data = json.loads(share_data)
        except Exception:
            share_data = {}
    if isinstance(share_data, list) and share_data:
        share_data = share_data[0]
    if isinstance(share_data, dict) and share_data:
        token = share_data.get("token", share_data.get("shareToken", ""))
        url = share_data.get("url", share_data.get("shareUrl", ""))
        echo(f"🔗 Share link created for '{path}':")
        if url:
            echo(f"  URL: {url}")
        if token:
            echo(f"  Token: {token}")
        if expire:
            echo(f"  Expires: {expire}")
    else:
        echo(f"❌ Failed to create share link: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)


@click.command()
@click.argument("path")
def unshare(path):
    """Remove sharing for a note."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    note_data = curl_request("GET", "/note", params={
        "vault": vault, "path": path, "pathHash": path_hash
    })
    actual_hash = note_data.get("data", {}).get("pathHash", "")
    if not actual_hash:
        echo(f"❌ Note '{path}' not found.", err=True)
        return

    del_data = curl_request("DELETE", "/share", json_data={
        "vault": vault, "path": path, "pathHash": actual_hash
    })
    handle_response(del_data, success_msg=f"✅ Sharing removed for '{path}'.")


@click.command("shares")
def shares_list():
    """List all active share links."""
    data = curl_request("GET", "/shares", params={"page": 1, "pageSize": 50})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", data.get("data", []))
    if isinstance(items, dict):
        items = items.get("list", [])
    if items:
        echo("🔗 Active shares:\n")
        for s in items:
            spath = s.get("path", s.get("notePath", "unknown"))
            stoken = s.get("token", s.get("shareToken", ""))
            sexpire = s.get("expire", s.get("expiresAt", ""))
            echo(f"  📄 {spath}")
            echo(f"     Token: {stoken} | Expires: {sexpire}")
        echo(f"\nTotal: {len(items)}")
    else:
        echo("📭 No active shares.")


@click.command("share-password")
@click.argument("path")
@click.argument("password")
def share_password(path, password):
    """Set or change the access password for a shared note."""
    vault = require_vault()
    path_hash = compute_path_hash(path)
    data = curl_request("POST", "/share/password", json_data={
        "vault": vault, "path": path, "pathHash": path_hash, "password": password
    })
    handle_response(data, success_msg=f"✅ Password set for sharing '{path}'.")


@click.command("share-paths")
def share_paths():
    """List paths of all shared notes in current vault."""
    vault = require_vault()
    data = curl_request("GET", "/notes/share-paths", params={"vault": vault})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    paths_data = data.get("data", [])
    if isinstance(paths_data, dict):
        paths_data = paths_data.get("list", paths_data.get("paths", []))
    if paths_data:
        echo(f"🔗 Shared notes in '{vault}':\n")
        for p in paths_data:
            path = p if isinstance(p, str) else p.get("path", p.get("notePath", "unknown"))
            echo(f"  📄 {path}")
        echo(f"\nTotal: {len(paths_data)}")
    else:
        echo("📭 No shared notes.")


@click.command("share-link")
@click.argument("path")
def share_link(path):
    """Generate a short share link for a note."""
    vault = require_vault()
    actual_hash = _get_note_hash(path, vault)
    if not actual_hash:
        echo(f"❌ Could not find note '{path}'.", err=True)
        return

    data = curl_request("POST", "/share/short_link", json_data={
        "vault": vault, "path": path, "pathHash": actual_hash
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    link_data = data.get("data", {})
    if isinstance(link_data, str):
        try:
            link_data = json.loads(link_data)
        except Exception:
            link_data = {}
    short_url = link_data.get("url", link_data.get("shortUrl", link_data.get("link", "")))
    if short_url:
        echo(f"🔗 Short link for '{path}':\n  {short_url}")
    else:
        echo(f"❌ Failed to generate short link: {json.dumps(data, indent=2, ensure_ascii=False)}", err=True)
