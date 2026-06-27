"""Fast Note Sync CLI - Storage management commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx
from fns_cli.formatting import echo


@click.command("storage-list")
def storage_list():
    """List all storage configurations."""
    data = curl_request("GET", "/storage")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    items = data.get("data", [])
    if isinstance(items, dict):
        items = items.get("list", [])
    if items:
        echo("💾 Storage configurations:\n")
        for s in items:
            sid = s.get("id", "unknown")
            name = s.get("name", s.get("path", "unknown"))
            stype = s.get("type", "unknown")
            enabled = "enabled" if s.get("isEnabled") else "disabled"
            echo(f"  📦 #{sid} - {name} ({stype}, {enabled})")
        echo(f"\nTotal: {len(items)}")
    else:
        echo("📭 No storage configurations found.")


@click.command("storage-add")
@click.argument("name")
@click.argument("stype", type=click.Choice(["localfs", "s3", "oss", "r2", "minio", "webdav"]))
@click.option("--config", "config_json", help="Storage config as JSON string")
def storage_add(name, stype, config_json):
    """Add a new storage configuration."""
    config = {}
    if config_json:
        import json as json_mod
        try:
            config = json_mod.loads(config_json)
        except json_mod.JSONDecodeError:
            echo(f"❌ Invalid JSON config: {config_json}", err=True)
            return

    payload = {
        "name": name,
        "type": stype,
        "isEnabled": True,
    }
    # Extract common config fields from JSON
    for key in ("endpoint", "region", "bucket", "accessKey", "secretKey", "path", "url"):
        if key in config:
            payload[key] = config[key]

    data = curl_request("POST", "/storage", json_data=payload)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg=f"✅ Storage '{name}' ({stype}) added.")


@click.command("storage-remove")
@click.argument("storage_id", type=int)
def storage_remove(storage_id):
    """Remove a storage configuration by ID."""
    click.confirm(f"⚠️ Remove storage #{storage_id}?", abort=True)
    data = curl_request("DELETE", "/storage", params={"id": storage_id})
    handle_response(data, success_msg=f"✅ Storage #{storage_id} removed.")


@click.command("storage-validate")
@click.argument("stype", type=click.Choice(["localfs", "s3", "oss", "r2", "minio", "webdav"]))
@click.option("--config", "config_json", required=True, help="Storage config as JSON string")
def storage_validate(stype, config_json):
    """Validate storage connection."""
    import json as json_mod
    try:
        config = json_mod.loads(config_json)
    except json_mod.JSONDecodeError:
        echo(f"❌ Invalid JSON config: {config_json}", err=True)
        return

    payload = {"type": stype}
    for key in ("endpoint", "region", "bucket", "accessKey", "secretKey", "path", "url"):
        if key in config:
            payload[key] = config[key]

    data = curl_request("POST", "/storage/validate", json_data=payload)
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    handle_response(data, success_msg="✅ Storage connection validated.")


@click.command("storage-enabled")
def storage_enabled():
    """List enabled storage types."""
    data = curl_request("GET", "/storage/enabled_types")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    types = data.get("data", [])
    if types:
        echo("📦 Enabled storage types:")
        for t in types:
            echo(f"  ✅ {t}")
    else:
        echo("📭 No storage types enabled.")
