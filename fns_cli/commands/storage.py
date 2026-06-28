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
@click.option("--endpoint", help="Storage endpoint URL (e.g. https://<account>.r2.cloudflarestorage.com)")
@click.option("--region", help="Storage region (e.g. us-east-1, auto for R2)")
@click.option("--bucket", "bucket_name", help="Bucket name")
@click.option("--account-id", "account_id", help="Account ID (required for R2)")
@click.option("--access-key", "access_key_id", help="Access Key ID")
@click.option("--secret-key", "access_key_secret", help="Secret Access Key")
@click.option("--path", "custom_path", help="Custom path prefix (e.g. /backups)")
@click.option("--url", "access_url_prefix", help="Public access URL prefix")
@click.option("--user", help="Username (for WebDAV)")
@click.option("--password", help="Password (for WebDAV)")
@click.option("--disabled", "is_disabled", is_flag=True, help="Create as disabled")
def storage_add(name, stype, endpoint, region, bucket_name, account_id,
                access_key_id, access_key_secret, custom_path,
                access_url_prefix, user, password, is_disabled):
    """Add a new storage configuration.

    Examples:

    \b
    # Cloudflare R2
    fns storage-add my-r2 r2 \\
      --endpoint https://<ACCOUNT_ID>.r2.cloudflarestorage.com \\
      --region auto --bucket my-bucket \\
      --access-key <KEY> --secret-key <SECRET>

    \b
    # AWS S3
    fns storage-add my-s3 s3 \\
      --endpoint https://s3.us-east-1.amazonaws.com \\
      --region us-east-1 --bucket my-bucket \\
      --access-key <KEY> --secret-key <SECRET>

    \b
    # WebDAV
    fns storage-add my-webdav webdav \\
      --url https://webdav.example.com --user admin --password pass

    \b
    # Local filesystem
    fns storage-add my-local localfs --path /mnt/storage
    """
    payload = {
        "type": stype,
        "isEnabled": 0 if is_disabled else 1,
    }
    if endpoint:
        payload["endpoint"] = endpoint
    if region:
        payload["region"] = region
    if bucket_name:
        payload["bucketName"] = bucket_name
    if account_id:
        payload["accountId"] = account_id
    if access_key_id:
        payload["accessKeyId"] = access_key_id
    if access_key_secret:
        payload["accessKeySecret"] = access_key_secret
    if custom_path:
        payload["customPath"] = custom_path
    if access_url_prefix:
        payload["accessUrlPrefix"] = access_url_prefix
    if user:
        payload["user"] = user
    if password:
        payload["password"] = password

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
@click.option("--endpoint", help="Storage endpoint URL")
@click.option("--region", help="Storage region")
@click.option("--bucket", "bucket_name", help="Bucket name")
@click.option("--account-id", "account_id", help="Account ID (R2)")
@click.option("--access-key", "access_key_id", help="Access Key ID")
@click.option("--secret-key", "access_key_secret", help="Secret Access Key")
@click.option("--path", "custom_path", help="Custom path prefix")
@click.option("--url", "access_url_prefix", help="Access URL prefix")
@click.option("--user", help="Username")
@click.option("--password", help="Password")
def storage_validate(stype, endpoint, region, bucket_name, account_id,
                     access_key_id, access_key_secret, custom_path,
                     access_url_prefix, user, password):
    """Validate storage connection parameters."""
    payload = {"type": stype}
    if endpoint:
        payload["endpoint"] = endpoint
    if region:
        payload["region"] = region
    if bucket_name:
        payload["bucketName"] = bucket_name
    if account_id:
        payload["accountId"] = account_id
    if access_key_id:
        payload["accessKeyId"] = access_key_id
    if access_key_secret:
        payload["accessKeySecret"] = access_key_secret
    if custom_path:
        payload["customPath"] = custom_path
    if access_url_prefix:
        payload["accessUrlPrefix"] = access_url_prefix
    if user:
        payload["user"] = user
    if password:
        payload["password"] = password

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
