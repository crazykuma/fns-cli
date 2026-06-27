"""Fast Note Sync CLI - Git Sync management commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx
from fns_cli.formatting import echo, format_timestamp


@click.group()
def git_sync():
    """Manage Git synchronization configurations."""
    pass


@git_sync.command("list")
def git_sync_list():
    """List git sync configurations."""
    data = curl_request("GET", "/git-sync/configs")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if isinstance(items, dict):
        items = items.get("list", [])
    if items:
        echo("🔄 Git sync configurations:\n")
        for c in items:
            cid = c.get("id", "unknown")
            name = c.get("name", c.get("repoName", "unknown"))
            branch = c.get("branch", "main")
            enabled = "enabled" if c.get("isEnabled") else "disabled"
            echo(f"  📦 #{cid} - {name} (branch: {branch}, {enabled})")
        echo(f"\nTotal: {len(items)}")
    else:
        echo("📭 No git sync configurations found.")


@git_sync.command("add")
@click.argument("name")
@click.option("--repo-url", required=True, help="Git repository URL")
@click.option("--branch", default="main", help="Git branch")
@click.option("--path", help="Local path within vault")
@click.option("--interval", default="5m", help="Sync interval (e.g., 5m, 1h)")
@click.option("--enabled/--disabled", default=True, help="Enable sync")
def git_sync_add(name, repo_url, branch, path, interval, enabled):
    """Add a new git sync configuration."""
    payload = {
        "name": name,
        "repoUrl": repo_url,
        "branch": branch,
        "interval": interval,
        "isEnabled": enabled,
    }
    if path:
        payload["path"] = path

    data = curl_request("POST", "/git-sync/config", json_data=payload)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg=f"✅ Git sync config '{name}' added.")


@git_sync.command("remove")
@click.argument("config_id", type=int)
def git_sync_remove(config_id):
    """Remove a git sync configuration."""
    click.confirm(f"⚠️ Remove git sync config #{config_id}?", abort=True)
    data = curl_request("DELETE", "/git-sync/config", json_data={"id": config_id})
    handle_response(data, success_msg=f"✅ Git sync config #{config_id} removed.")


@git_sync.command("validate")
@click.argument("config_id", type=int)
def git_sync_validate(config_id):
    """Validate a git sync configuration."""
    data = curl_request("POST", "/git-sync/validate", json_data={"id": config_id})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg="✅ Git sync config validated.")


@git_sync.command("run")
@click.argument("config_id", type=int)
def git_sync_run(config_id):
    """Manually trigger a git sync."""
    data = curl_request("POST", "/git-sync/config/execute", json_data={"id": config_id})
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg=f"✅ Git sync #{config_id} triggered.")


@git_sync.command("clean")
@click.argument("config_id", type=int)
def git_sync_clean(config_id):
    """Clean local git workspace."""
    click.confirm(f"⚠️ Clean workspace for git sync #{config_id}? This removes local files.", abort=True)
    data = curl_request("DELETE", "/git-sync/config/clean", json_data={"configId": config_id})
    handle_response(data, success_msg=f"✅ Workspace cleaned for git sync #{config_id}.")


@git_sync.command("history")
@click.argument("config_id", type=int)
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
def git_sync_history(config_id, page, page_size):
    """View git sync history."""
    data = curl_request("GET", "/git-sync/histories", params={
        "configId": config_id, "page": page, "pageSize": page_size
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        echo(f"🔄 Git sync history for config #{config_id} (Page {page}):\n")
        for h in items:
            ts = h.get("startTime", h.get("createdAt", ""))
            if ts:
                ts = ts.get("$date", ts) if isinstance(ts, dict) else ts
            status = h.get("status", "unknown")
            status_map = {0: "Idle", 1: "Running", 2: "Success", 3: "Failed"}
            status_str = status_map.get(status, str(status))
            message = h.get("message", "")
            echo(f"  📦 {ts} - {status_str}")
            if message:
                echo(f"     {message}")
        echo(f"\nTotal: {len(items)} records")
    else:
        echo(f"📭 No git sync history for config #{config_id}.")
