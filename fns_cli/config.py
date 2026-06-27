"""Fast Note Sync CLI - Config management."""
import json
import sys
from pathlib import Path

import click

# Config directory: ~/.config/fns-cli/
CONFIG_DIR = Path.home() / ".config" / "fns-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"

DEFAULT_BASE_URL = ""  # Configure via 'fns config url'
DEFAULT_VAULT = ""  # Auto-detected on first login

# Global state for output mode
_ctx = {}


def load_config():
    """Load config from ~/.config/fns-cli/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"base_url": DEFAULT_BASE_URL, "vault": DEFAULT_VAULT}


def save_config(cfg):
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def require_vault():
    """Check if vault is configured, print hint if not."""
    cfg = load_config()
    vault = cfg.get("vault", "")
    if not vault:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Vault not configured", "hint": "Run: fns vaults or fns config vault <name>"}))
            sys.exit(1)
        click.echo("⚠️ Vault not configured. Run one of these:")
        click.echo("   fns vaults          # List available vaults")
        click.echo("   fns config vault <name>  # Set your vault")
        sys.exit(1)
    return vault


def get_token():
    """Read token from file."""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    if _ctx.get("json_output"):
        click.echo(json.dumps({"error": "Token not found", "hint": "Run: fns login"}))
        sys.exit(1)
    click.echo("⚠️ Token not found. Run: fns login", err=True)
    sys.exit(1)
