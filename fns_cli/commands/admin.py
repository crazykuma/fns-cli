"""Fast Note Sync CLI - Admin operations."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx
from fns_cli.formatting import echo


@click.command("admin-info")
def admin_info():
    """Show system and runtime info (requires admin)."""
    data = curl_request("GET", "/admin/systeminfo")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", {})
    if info:
        echo("🖥️  System Information:")
        for key in ("version", "goVersion", "gitTag", "buildTime", "uptime",
                     "goroutineCount", "memoryAlloc", "memorySys", "gcCount"):
            if key in info and info[key]:
                echo(f"  {key}: {info[key]}")
    else:
        echo("❌ Failed to get system info.", err=True)


@click.command("admin-restart")
def admin_restart():
    """Gracefully restart the server (requires admin)."""
    click.confirm("⚠️ Restart the server? All clients will be temporarily disconnected.", abort=True)
    data = curl_request("GET", "/admin/restart")
    handle_response(data, success_msg="✅ Server restart initiated.")


@click.command("admin-upgrade")
@click.argument("version")
def admin_upgrade(version):
    """Trigger server upgrade (requires admin)."""
    click.confirm(f"⚠️ Upgrade server to version {version}? Server will restart.", abort=True)
    data = curl_request("GET", "/admin/upgrade", params={"version": version})
    handle_response(data, success_msg=f"✅ Server upgrade to {version} initiated.")


@click.command("admin-gc")
def admin_gc():
    """Trigger manual GC (requires admin)."""
    data = curl_request("GET", "/admin/gc")
    handle_response(data, success_msg="✅ GC triggered.")


@click.command("admin-ws-clients")
def admin_ws_clients():
    """List connected WebSocket clients (requires admin)."""
    data = curl_request("GET", "/admin/ws_clients")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    clients = data.get("data", [])
    if isinstance(clients, dict):
        clients = clients.get("list", [])
    if clients:
        echo("🔌 Connected WebSocket clients:\n")
        for c in clients:
            uid = c.get("uid", c.get("userId", "unknown"))
            addr = c.get("addr", c.get("remoteAddr", "unknown"))
            device = c.get("device", c.get("clientName", "unknown"))
            echo(f"  👤 {uid} - {device} ({addr})")
        echo(f"\nTotal: {len(clients)} clients")
    else:
        echo("📭 No WebSocket clients connected.")
