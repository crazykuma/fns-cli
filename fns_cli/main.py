"""Fast Note Sync CLI - Main entry point."""
import json
import subprocess
import sys

import click

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fns_cli.config import _ctx, load_config, save_config, require_vault, TOKEN_FILE
from fns_cli.formatting import echo, format_timestamp
from fns_cli.api import curl_request, handle_response
from fns_cli.hashing import compute_path_hash
from pathlib import Path

__version__ = "0.9.1"


@click.group()
@click.version_option(__version__, prog_name="fns")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-essential output")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, quiet, json_output):
    """📝 Fast Note Sync CLI - Interact with your Obsidian FNS service."""
    _ctx["quiet"] = quiet
    _ctx["json_output"] = json_output


# ==================== Auth & Config ====================

@cli.command()
@click.argument("credentials", required=False)
@click.argument("password", required=False)
@click.option("-u", "--url", "api_url", help="Set API URL before login")
def login(credentials, password, api_url):
    """Login and save token (password will be hidden if not provided)."""
    cfg = load_config()

    # Step 1: Ensure URL is configured
    base_url = cfg.get("base_url", "")
    if api_url:
        url_val = api_url.rstrip("/")
        if not url_val.endswith("/api"):
            url_val += "/api"
        cfg["base_url"] = url_val
        save_config(cfg)
        echo(f"✅ API URL set to '{url_val}'")
        base_url = url_val
    elif not base_url:
        base_url = click.prompt("Enter FNS server URL (e.g., https://your-server)")
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api"):
            base_url += "/api"
        cfg["base_url"] = base_url
        save_config(cfg)
        echo(f"✅ API URL set to '{base_url}'")

    # Step 2: Prompt for credentials if not provided
    if not credentials:
        credentials = click.prompt("Username or email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    # Step 3: Authenticate
    url = f"{base_url}/user/login"
    cmd = ["curl", "-s", "-X", "POST", url,
           "-H", "Content-Type: application/json",
           "-H", "X-Client: WebGui",
           "-H", "User-Agent: Mozilla/5.0",
           "-d", json.dumps({"credentials": credentials, "password": password})]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
        resp = json.loads(result.stdout)
        if _ctx.get("json_output"):
            click.echo(json.dumps(resp, indent=2, ensure_ascii=False))
            return

        if resp.get("status") is True:
            token = resp.get("data", {}).get("token") if isinstance(resp.get("data"), dict) else None
            if token:
                TOKEN_FILE.write_text(token)
                echo(f"✅ Login successful. Token saved to {TOKEN_FILE}")

                # Step 4: Handle vault selection
                if not cfg.get("vault"):
                    vault_data = curl_request("GET", "/vault")
                    vaults_list = []
                    if isinstance(vault_data.get("data"), list):
                        vaults_list = vault_data["data"]
                    elif isinstance(vault_data.get("data"), dict):
                        vaults_list = vault_data["data"].get("list", [vault_data["data"]])

                    if len(vaults_list) == 1:
                        v = vaults_list[0]
                        vault_name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                        cfg["vault"] = vault_name
                        save_config(cfg)
                        echo(f"📦 Auto-set vault to '{vault_name}'")
                    elif vaults_list:
                        echo("📦 Available vaults:")
                        choices = []
                        for i, v in enumerate(vaults_list, 1):
                            name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                            choices.append(str(i))
                            echo(f"  {i}. {name}")
                        selected = click.prompt("Select vault", type=click.Choice(choices), default=choices[0])
                        idx = int(selected) - 1
                        v = vaults_list[idx]
                        vault_name = v.get("vault", v.get("name", v.get("vault_name", str(v.get("id", "")))))
                        cfg["vault"] = vault_name
                        save_config(cfg)
                        echo(f"📦 Vault set to '{vault_name}'")
                echo("🎉 Ready! Try: fns list")
            else:
                echo("❌ No token in response.", err=True)
        else:
            echo(f"❌ Login failed: {resp.get('message', 'Unknown error')}", err=True)
    except Exception as e:
        echo(f"❌ Error: {e}", err=True)


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()
    base_url = cfg.get("base_url", "(not configured)")
    vault = cfg.get("vault", "(not configured)")

    echo("📋 Current configuration:")
    echo(f"  API URL : {base_url}")
    echo(f"  Vault   : {vault}")

    # Fetch user info if token exists
    if TOKEN_FILE.exists():
        try:
            data = curl_request("GET", "/user/info")
            user = data.get("data", {})
            if user:
                username = user.get("username", user.get("email", user.get("displayName", "")))
                if username:
                    echo(f"  User    : {username}")
                else:
                    echo("  User    : (logged in, no username)")
            else:
                echo("  User    : (token invalid)")
        except SystemExit:
            echo("  User    : (could not fetch)")
    else:
        echo("  User    : (not logged in)")


@config.command()
@click.argument("value")
def vault(value):
    """Set vault name."""
    cfg = load_config()
    cfg["vault"] = value
    save_config(cfg)
    echo(f"✅ Vault set to '{value}'")


@config.command()
@click.argument("value")
def url(value):
    """Set API URL."""
    url_val = value.rstrip("/")
    if not url_val.endswith("/api"):
        url_val += "/api"
    cfg = load_config()
    cfg["base_url"] = url_val
    save_config(cfg)
    echo(f"✅ API URL set to '{url_val}'")


# ==================== User Commands ====================

@cli.group()
def user():
    """User management."""
    pass


@user.command("info")
def user_info():
    """Show current user info."""
    data = curl_request("GET", "/user/info")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    user = data.get("data", {})
    if user:
        echo("👤 Current user:")
        for key in ("username", "email", "displayName", "id", "role"):
            if key in user and user[key]:
                echo(f"  {key}: {user[key]}")
    else:
        echo("❌ Failed to fetch user info.", err=True)


@user.command("change-password")
@click.argument("old_password")
@click.argument("new_password")
def change_password(old_password, new_password):
    """Change your account password."""
    click.confirm("⚠️ Change password? This action cannot be undone.", abort=True)
    data = curl_request("POST", "/user/change_password", json_data={
        "oldPassword": old_password,
        "password": new_password,
        "confirmPassword": new_password,
    })
    handle_response(data, success_msg="✅ Password changed successfully.")


# ==================== System Commands ====================

@cli.command()
def version():
    """Show server version."""
    data = curl_request("GET", "/version")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    info = data.get("data", data)
    if info:
        echo("📋 Server version:")
        for key in ("version", "gitTag", "buildTime", "goVersion"):
            if key in info and info[key]:
                echo(f"  {key}: {info[key]}")
    else:
        echo("❌ Failed to get version info.", err=True)


@cli.command()
def health():
    """Check server health status."""
    data = curl_request("GET", "/health")
    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    status = data.get("status", data.get("code", 0))
    if status is True or (isinstance(status, int) and status >= 1):
        echo("✅ Server is healthy.")
    else:
        echo(f"⚠️ Server health check: {json.dumps(data, indent=2, ensure_ascii=False)}")


# ==================== Register Commands ====================

from fns_cli.commands import note as note_cmds
from fns_cli.commands import folder as folder_cmds
from fns_cli.commands import file as file_cmds
from fns_cli.commands import share as share_cmds
from fns_cli.commands import setting as setting_cmds
from fns_cli.commands import backup as backup_cmds
from fns_cli.commands import vault as vault_cmds
from fns_cli.commands import storage as storage_cmds
from fns_cli.commands import git_sync as git_sync_cmds
from fns_cli.commands import admin as admin_cmds


def register_commands():
    """Register all commands with the main CLI."""
    # Note commands
    cli.add_command(note_cmds.read)
    cli.add_command(note_cmds.write)
    cli.add_command(note_cmds.append)
    cli.add_command(note_cmds.delete)
    cli.add_command(note_cmds.prepend)
    cli.add_command(note_cmds.replace)
    cli.add_command(note_cmds.move_note)
    cli.add_command(note_cmds.history)
    cli.add_command(note_cmds.history_view)
    cli.add_command(note_cmds.history_restore)
    cli.add_command(note_cmds.rename)
    cli.add_command(note_cmds.recycle_clear)
    cli.add_command(note_cmds.restore)
    cli.add_command(note_cmds.frontmatter)
    cli.add_command(note_cmds.list_notes)
    cli.add_command(note_cmds.tree)
    cli.add_command(note_cmds.backlinks)
    cli.add_command(note_cmds.outlinks)
    cli.add_command(note_cmds.recycle_bin)

    # Folder commands
    cli.add_command(folder_cmds.mkdir)
    cli.add_command(folder_cmds.folder)
    cli.add_command(folder_cmds.folder_files)
    cli.add_command(folder_cmds.folder_notes)
    cli.add_command(folder_cmds.folder_list)
    cli.add_command(folder_cmds.folder_delete)
    cli.add_command(folder_cmds.folder_tree)

    # File commands
    cli.add_command(file_cmds.file_info)
    cli.add_command(file_cmds.file_download)
    cli.add_command(file_cmds.file_list)
    cli.add_command(file_cmds.file_delete)
    cli.add_command(file_cmds.file_rename)
    cli.add_command(file_cmds.file_restore)
    cli.add_command(file_cmds.file_recycle_clear)

    # Share commands
    cli.add_command(share_cmds.share)
    cli.add_command(share_cmds.unshare)
    cli.add_command(share_cmds.shares_list)
    cli.add_command(share_cmds.share_password)
    cli.add_command(share_cmds.share_paths)
    cli.add_command(share_cmds.share_link)

    # Setting commands
    cli.add_command(setting_cmds.setting_list)
    cli.add_command(setting_cmds.setting_get)
    cli.add_command(setting_cmds.setting_create)
    cli.add_command(setting_cmds.setting_delete)
    cli.add_command(setting_cmds.setting_rename)

    # Backup commands
    cli.add_command(backup_cmds.backup_list)
    cli.add_command(backup_cmds.backup_create)
    cli.add_command(backup_cmds.backup_delete)
    cli.add_command(backup_cmds.backup_run)
    cli.add_command(backup_cmds.backup_history)

    # Vault commands
    cli.add_command(vault_cmds.vaults)
    cli.add_command(vault_cmds.vault_info)
    cli.add_command(vault_cmds.vault_create)
    cli.add_command(vault_cmds.vault_delete)

    # Storage commands
    cli.add_command(storage_cmds.storage_list)
    cli.add_command(storage_cmds.storage_add)
    cli.add_command(storage_cmds.storage_remove)
    cli.add_command(storage_cmds.storage_validate)
    cli.add_command(storage_cmds.storage_enabled)

    # Git Sync commands (group)
    cli.add_command(git_sync_cmds.git_sync)

    # Admin commands
    cli.add_command(admin_cmds.admin_info)
    cli.add_command(admin_cmds.admin_restart)
    cli.add_command(admin_cmds.admin_upgrade)
    cli.add_command(admin_cmds.admin_gc)
    cli.add_command(admin_cmds.admin_ws_clients)


# Auto-register on import
register_commands()


if __name__ == "__main__":
    cli()
