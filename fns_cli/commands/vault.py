"""Fast Note Sync CLI - Vault commands."""
import json

import click

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx, get_token, require_vault
from fns_cli.formatting import echo


@click.command()
def vaults():
    """List available vaults."""
    data = curl_request("GET", "/vault")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    vault_list = []
    if isinstance(data.get("data"), list):
        vault_list = data["data"]
    elif isinstance(data.get("data"), dict):
        vault_list = data["data"].get("list", [data["data"]])

    if vault_list:
        echo("📦 Available vaults:")
        for v in vault_list:
            name = v.get("vault", v.get("name", v.get("vault_name", v.get("id", "unknown"))))
            echo(f"  🗄️  {name}")
    else:
        echo("📭 No vaults found.")


@click.command()
@click.argument("vault_name", required=False, default="")
def vault_info(vault_name):
    """Show vault details."""
    if not vault_name:
        vault_name = require_vault()

    data = curl_request("GET", "/vault")
    vaults_list = []
    if isinstance(data.get("data"), list):
        vaults_list = data["data"]
    elif isinstance(data.get("data"), dict):
        vaults_list = data["data"].get("list", [data["data"]])

    target = None
    for v in vaults_list:
        name = v.get("vault", v.get("name", v.get("vault_name", "")))
        if name == vault_name:
            target = v
            break

    if not target:
        echo(f"❌ Vault '{vault_name}' not found.", err=True)
        return

    if _ctx.get("json_output"):
        click.echo(json.dumps(target, indent=2, ensure_ascii=False))
        return

    echo(f"📦 Vault info for '{vault_name}':")
    for key in ("vault", "name", "noteCount", "noteSize", "fileCount", "fileSize", "size", "createdAt", "updatedAt"):
        if key in target and target[key]:
            echo(f"  {key}: {target[key]}")


@click.command("vault-create")
@click.argument("name")
def vault_create(name):
    """Create a new vault (requires confirmation)."""
    get_token()
    click.confirm(f"⚠️ Create new vault '{name}'? This action cannot be undone", abort=True)

    data = curl_request("POST", "/vault", json_data={"vault": name})
    handle_response(data, success_msg=f"✅ Vault '{name}' created.")


@click.command("vault-delete")
@click.argument("vault_id")
def vault_delete(vault_id):
    """Delete a vault by ID (requires double confirmation)."""
    click.confirm(f"⚠️ WARNING: This will permanently delete vault ID '{vault_id}' and ALL its data!", abort=True)
    click.confirm("🚨 Are you absolutely sure? This action CANNOT be undone!", abort=True)

    data = curl_request("DELETE", "/vault", params={"id": vault_id})
    handle_response(data, success_msg=f"✅ Vault '{vault_id}' deleted permanently.")
