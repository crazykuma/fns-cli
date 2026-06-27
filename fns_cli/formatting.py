"""Fast Note Sync CLI - Output formatting."""
from datetime import datetime, timezone

import click


def format_size(num_bytes):
    """Format file size in bytes to human readable string."""
    if num_bytes is None:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_timestamp(ts_ms):
    """Convert millisecond Unix timestamp to human-readable local time."""
    if not ts_ms:
        return ""
    try:
        dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return str(ts_ms)


def echo(text, **kwargs):
    """Print unless quiet mode is enabled."""
    # Lazy import to avoid circular dependency: config -> formatting -> config
    from fns_cli.config import _ctx
    if not _ctx.get("quiet"):
        click.echo(text, **kwargs)
