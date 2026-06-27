"""Fast Note Sync CLI - HTTP API layer."""
import json
import subprocess
import sys

import click

from fns_cli.config import _ctx, get_token, load_config


def curl_request(method, endpoint, params=None, json_data=None):
    """Make an HTTP request via curl subprocess.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        endpoint: API endpoint path (e.g., "/note")
        params: Query parameters dict
        json_data: JSON body dict

    Returns:
        Parsed JSON response dict
    """
    cfg = load_config()
    base_url = cfg.get("base_url", "")
    if not base_url:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "API URL not configured", "hint": "Run: fns config url <url>"}))
            sys.exit(1)
        click.echo("⚠️ API URL not configured. Run: fns config url https://your-server/api", err=True)
        sys.exit(1)

    url = f"{base_url}{endpoint}"
    if params:
        from urllib.parse import urlencode
        url += f"?{urlencode(params)}"

    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {get_token()}",
           "-H", "X-Client: WebGui",
           "-H", "User-Agent: Mozilla/5.0"]

    if json_data is not None:
        cmd.extend(["-H", "Content-Type: application/json",
                    "-d", json.dumps(json_data)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            if _ctx.get("json_output"):
                click.echo(json.dumps({"error": "curl error", "detail": result.stderr.strip()}))
                sys.exit(1)
            click.echo(f"❌ curl error: {result.stderr.strip()}", err=True)
            sys.exit(1)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Request timed out"}))
            sys.exit(1)
        click.echo("❌ Request timed out", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        if _ctx.get("json_output"):
            click.echo(json.dumps({"error": "Invalid JSON response", "detail": result.stdout[:200]}))
            sys.exit(1)
        click.echo(f"❌ Invalid JSON response: {result.stdout[:200]}", err=True)
        sys.exit(1)


def handle_response(data, success_msg=None, error_prefix="Failed"):
    """Handle API response, print success or error based on code/status.

    Args:
        data: Parsed JSON response dict
        success_msg: Message to print on success (text mode only)
        error_prefix: Prefix for error messages

    Returns:
        The data dict (for chaining in JSON mode)
    """
    code = data.get("code", 0)
    status = data.get("status", False)

    if _ctx.get("json_output"):
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return data

    # Success: code 1-6 OR status is True
    if code in range(1, 7) or status is True:
        if success_msg:
            from fns_cli.formatting import echo
            echo(success_msg)
        return data
    else:
        msg = data.get("message", json.dumps(data, indent=2, ensure_ascii=False))
        from fns_cli.formatting import echo
        echo(f"❌ {error_prefix}: {msg}", err=True)
        sys.exit(1)
