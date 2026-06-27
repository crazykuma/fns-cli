"""Fast Note Sync CLI - Backup commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, require_vault
from fns_cli.formatting import echo, format_size, format_timestamp


@click.command("backup-list")
def backup_list():
    """List backup configurations."""
    data = curl_request("GET", "/backup/configs")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if isinstance(items, dict):
        items = items.get("list", [])
    if items:
        echo("💾 Backup configurations:\n")
        for b in items:
            bid = b.get("id", "unknown")
            vault = b.get("vault", "")
            btype = b.get("type", "")
            enabled = "enabled" if b.get("isEnabled") else "disabled"
            echo(f"  📦 #{bid} - {vault} ({btype}, {enabled})")
        echo(f"\nTotal: {len(items)}")
    else:
        echo("📭 No backup configurations found.")


@click.command("backup-create")
@click.argument("vault")
@click.option("--storage-ids", "storage_ids", required=True, help="Storage IDs (comma-separated, e.g. 1,2)")
@click.option("--cron", "cron_strategy", required=True, type=click.Choice(["daily", "weekly", "monthly", "custom"]), help="Backup schedule")
@click.option("--type", "backup_type", default="sync", type=click.Choice(["full", "incremental", "sync"]), help="Backup type")
@click.option("--cron-expr", "cron_expr", help="Custom cron expression (required if cron=custom)")
@click.option("--retention", "retention_days", default=7, help="Retention days (-1 for forever)")
@click.option("--enabled/--disabled", "is_enabled", default=True, help="Enable backup")
def backup_create(vault, storage_ids, cron_strategy, backup_type, cron_expr, retention_days, is_enabled):
    """Create a new backup configuration.

    STORAGE_IDS: Comma-separated storage IDs (e.g. 1,2)
    CRON: daily, weekly, monthly, or custom (requires --cron-expr)
    """
    if cron_strategy == "custom" and not cron_expr:
        echo("❌ --cron-expr is required when --cron=custom", err=True)
        return

    data = curl_request("POST", "/backup/config", json_data={
        "vault": vault,
        "type": backup_type,
        "storageIds": f"[{storage_ids}]",
        "cronStrategy": cron_strategy,
        "cronExpression": cron_expr or "0 0 * * *",
        "retentionDays": retention_days,
        "isEnabled": is_enabled,
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg=f"✅ Backup config created for vault '{vault}'.")


@click.command("backup-delete")
@click.argument("config_id", type=int)
def backup_delete(config_id):
    """Delete a backup configuration by ID."""
    click.confirm(f"⚠️ Delete backup config #{config_id}?", abort=True)
    data = curl_request("DELETE", "/backup/config", params={"id": config_id})
    handle_response(data, success_msg=f"✅ Backup config #{config_id} deleted.")


@click.command("backup-run")
@click.argument("config_id", type=int)
def backup_run(config_id):
    """Manually trigger a backup by config ID."""
    data = curl_request("POST", "/backup/execute", json_data={"id": config_id})
    handle_response(data, success_msg=f"✅ Backup #{config_id} triggered.")


@click.command("backup-history")
@click.argument("config_id", type=int)
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", "page_size", default=20, help="Items per page")
def backup_history(config_id, page, page_size):
    """View backup execution history by config ID."""
    data = curl_request("GET", "/backup/historys", params={
        "configId": config_id, "page": page, "pageSize": page_size
    })
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", {}).get("list", [])
    if items:
        echo(f"💾 Backup history for config #{config_id} (Page {page}):\n")
        for b in items:
            ts = b.get("startTime", "")
            if ts:
                ts = ts.get("$date", ts) if isinstance(ts, dict) else ts
            status = b.get("status", "unknown")
            status_map = {0: "Idle", 1: "Running", 2: "Success", 3: "Failed", 4: "Stopped"}
            status_str = status_map.get(status, str(status))
            size = b.get("fileSize", 0)
            count = b.get("fileCount", 0)
            echo(f"  📦 {ts} - {status_str} ({format_size(size)}, {count} files)")
        echo(f"\nTotal: {len(items)} records")
    else:
        echo(f"📭 No backup history for config #{config_id}.")
