"""Tests for FNS CLI - Note commands."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from fns_cli.commands.note import replace as replace_cmd
from fns_cli.commands.note import append as append_cmd
from fns_cli.config import _ctx


def _invoke_command(cmd, *args):
    """Invoke a Click command directly, capturing the result."""
    with patch("fns_cli.api.click.echo") as mock_echo:
        try:
            cmd.callback(*args)
        except SystemExit:
            pass
        return mock_echo.call_args_list


class TestReplaceMatchCount(unittest.TestCase):
    """Test that replace command correctly parses matchCount from API response."""

    def test_replace_matchCount_field(self):
        """Backend returns 'matchCount', not 'count'."""
        _ctx["json_output"] = False
        _ctx["quiet"] = False
        with patch("fns_cli.commands.note.curl_request") as mock_curl, \
             patch("fns_cli.commands.note.require_vault", return_value="test"), \
             patch("fns_cli.commands.note.compute_path_hash", return_value="123"):
            mock_curl.return_value = {
                "code": 1,
                "status": True,
                "data": {"matchCount": 5}
            }
            with patch("click.echo") as mock_echo:
                replace_cmd.callback("test.md", "old", "new")
                output = " ".join(str(c) for c in mock_echo.call_args_list)
                self.assertIn("5", output)
                self.assertNotIn("?", output)

    def test_replace_no_matchCount_defaults_to_unknown(self):
        """If matchCount not in response, show '?'."""
        _ctx["json_output"] = False
        _ctx["quiet"] = False
        with patch("fns_cli.commands.note.curl_request") as mock_curl, \
             patch("fns_cli.commands.note.require_vault", return_value="test"), \
             patch("fns_cli.commands.note.compute_path_hash", return_value="123"):
            mock_curl.return_value = {
                "code": 1,
                "status": True,
                "data": {}
            }
            with patch("click.echo") as mock_echo:
                replace_cmd.callback("test.md", "old", "new")
                output = " ".join(str(c) for c in mock_echo.call_args_list)
                self.assertIn("?", output)


class TestAppendOptimization(unittest.TestCase):
    """Test that append directly POSTs to /append without GET first."""

    def test_append_no_prior_get(self):
        """Should only make one POST, not GET + POST."""
        _ctx["json_output"] = False
        _ctx["quiet"] = False
        with patch("fns_cli.commands.note.curl_request") as mock_curl, \
             patch("fns_cli.commands.note.require_vault", return_value="test"), \
             patch("fns_cli.commands.note.compute_path_hash", return_value="123"):
            mock_curl.return_value = {"code": 1, "status": True}
            with patch("click.echo"):
                append_cmd.callback("test.md", "new content")
            self.assertEqual(mock_curl.call_count, 1)


if __name__ == "__main__":
    unittest.main()
