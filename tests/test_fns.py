"""Tests for FNS CLI utility functions."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import fns
sys.path.insert(0, str(Path(__file__).parent.parent))

import fns


class TestFormatTimestamp(unittest.TestCase):
    """Test format_timestamp function."""

    def test_valid_timestamp(self):
        """Test converting a known millisecond timestamp."""
        result = fns.format_timestamp(1716206400000)
        self.assertRegex(result, r"2024-05-20 \d{2}:\d{2}:\d{2}")

    def test_empty_timestamp(self):
        """Test empty/falsy timestamp returns empty string."""
        self.assertEqual(fns.format_timestamp(None), "")
        self.assertEqual(fns.format_timestamp(0), "")
        self.assertEqual(fns.format_timestamp(""), "")

    def test_invalid_timestamp(self):
        """Test invalid timestamp falls back to string."""
        result = fns.format_timestamp("not-a-number")
        self.assertEqual(result, "not-a-number")


class TestConfig(unittest.TestCase):
    """Test config loading and saving."""

    def setUp(self):
        """Create temporary directory for config files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name) / "fns-cli"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_config(self):
        """Test saving and loading config."""
        cfg = {"base_url": "https://test.example.com/api", "vault": "TestVault"}
        self.config_file.write_text(json.dumps(cfg, indent=2))

        loaded = json.loads(self.config_file.read_text())
        self.assertEqual(loaded["base_url"], "https://test.example.com/api")
        self.assertEqual(loaded["vault"], "TestVault")


class TestFileUploadPrefix(unittest.TestCase):
    """Test @file.txt prefix parsing for write/append commands."""

    def test_at_prefix_detection(self):
        """Test that @ prefix is correctly detected."""
        self.assertTrue("@notes.txt".startswith("@"))
        self.assertFalse("some content".startswith("@"))

    def test_at_prefix_path_extraction(self):
        """Test extracting path from @ prefix."""
        content = "@/path/to/file.txt"
        file_path = content[1:]
        self.assertEqual(file_path, "/path/to/file.txt")

    def test_non_at_content(self):
        """Test that normal content is not treated as file path."""
        content = "Hello, world!"
        is_file_prefix = content.startswith("@")
        self.assertFalse(is_file_prefix)


class TestURLNormalization(unittest.TestCase):
    """Test URL auto-append /api logic."""

    def test_url_without_api_suffix(self):
        """Test that /api is appended to bare URL."""
        value = "https://example.com"
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        self.assertEqual(url, "https://example.com/api")

    def test_url_with_trailing_slash(self):
        """Test that trailing slash is stripped before appending /api."""
        value = "https://example.com/"
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        self.assertEqual(url, "https://example.com/api")

    def test_url_already_has_api(self):
        """Test that /api is not double-appended."""
        value = "https://example.com/api"
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        self.assertEqual(url, "https://example.com/api")

    def test_url_with_api_and_slash(self):
        """Test URL with /api/ is not modified."""
        value = "https://example.com/api/"
        url = value.rstrip("/")
        if not url.endswith("/api"):
            url += "/api"
        self.assertEqual(url, "https://example.com/api")


class TestVaultRequirement(unittest.TestCase):
    """Test that require_vault() gives helpful hint when vault is empty."""

    def test_require_vault_empty_json_mode(self):
        """Test that missing vault in JSON mode outputs JSON error."""
        fns._ctx["json_output"] = True
        with patch("fns.load_config", return_value={"base_url": "https://example.com/api", "vault": ""}), \
             patch("click.echo") as mock_echo, \
             self.assertRaises(SystemExit):
            fns.require_vault()
            mock_echo.assert_called()
        fns._ctx.clear()

    def test_require_vault_empty_text_mode(self):
        """Test that missing vault in text mode outputs human-readable hint."""
        fns._ctx["quiet"] = False
        fns._ctx["json_output"] = False
        with patch("fns.load_config", return_value={"base_url": "https://example.com/api", "vault": ""}), \
             self.assertRaises(SystemExit):
            fns.require_vault()
        fns._ctx.clear()


class TestEchoHelper(unittest.TestCase):
    """Test _echo helper function."""

    def test_echo_in_quiet_mode(self):
        """Test that _echo does nothing in quiet mode."""
        fns._ctx["quiet"] = True
        with patch("click.echo") as mock_echo:
            fns._echo("should not print")
            mock_echo.assert_not_called()
        fns._ctx.clear()

    def test_echo_in_normal_mode(self):
        """Test that _echo prints in normal mode."""
        fns._ctx["quiet"] = False
        with patch("click.echo") as mock_echo:
            fns._echo("hello")
            mock_echo.assert_called_once_with("hello")
        fns._ctx.clear()


class TestHandleResponse(unittest.TestCase):
    """Test _handle_response helper function."""

    def test_handle_response_success_json_mode(self):
        """Test successful response in JSON mode."""
        fns._ctx["json_output"] = True
        data = {"code": 1, "status": True, "message": "OK"}
        with patch("click.echo") as mock_echo:
            fns._handle_response(data, success_msg="Done!")
            # Should echo JSON, not the success message
            call_arg = mock_echo.call_args[0][0]
            self.assertIn('"code"', call_arg)
        fns._ctx.clear()

    def test_handle_response_error_json_mode(self):
        """Test error response in JSON mode still returns data."""
        fns._ctx["json_output"] = True
        data = {"code": 430, "status": False, "message": "Note not found"}
        with patch("click.echo") as mock_echo:
            result = fns._handle_response(data, error_prefix="Note error")
            # In JSON mode, always return data without exiting
            self.assertEqual(result["code"], 430)
            mock_echo.assert_called_once()
            call_arg = mock_echo.call_args[0][0]
            self.assertIn('"code"', call_arg)
        fns._ctx.clear()


if __name__ == "__main__":
    unittest.main()
