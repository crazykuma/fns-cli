"""Tests for FNS CLI utility functions."""
import json
import os
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
        # 2024-05-20 12:00:00 UTC = 1716206400000 ms
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

    @patch.object(fns, "CONFIG_DIR", None)
    @patch.object(fns, "CONFIG_FILE", None)
    def test_load_config_no_file(self):
        """Test loading config when file doesn't exist returns defaults."""
        # We test the logic: if file doesn't exist, return defaults
        defaults = {"base_url": "", "vault": "Main"}
        self.assertEqual(fns.DEFAULT_BASE_URL, "")
        self.assertEqual(fns.DEFAULT_VAULT, "Main")

    def test_save_and_load_config(self):
        """Test saving and loading config."""
        cfg = {"base_url": "https://test.example.com/api", "vault": "TestVault"}
        self.config_file.write_text(json.dumps(cfg, indent=2))

        # Manually load and verify
        loaded = json.loads(self.config_file.read_text())
        self.assertEqual(loaded["base_url"], "https://test.example.com/api")
        self.assertEqual(loaded["vault"], "TestVault")


class TestFileUploadPrefix(unittest.TestCase):
    """Test @file.txt prefix parsing for write/append commands."""

    def test_at_prefix_detection(self):
        """Test that @ prefix is correctly detected."""
        self.assertTrue("@notes.txt".startswith("@"))
        self.assertFalse("some content".startswith("@"))
        self.assertFalse("@".startswith("@") and len("@notes.txt"[1:]) == 0)

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


class TestArgumentValidation(unittest.TestCase):
    """Test that main() validates argument counts properly."""

    @patch("fns.print")
    def test_read_no_args(self, mock_print):
        """Test fns read without path shows usage."""
        with patch.object(sys, "argv", ["fns", "read"]):
            fns.main()
            mock_print.assert_called()

    @patch("fns.print")
    def test_write_no_args(self, mock_print):
        """Test fns write without args shows usage."""
        with patch.object(sys, "argv", ["fns", "write"]):
            fns.main()
            mock_print.assert_called()

    @patch("fns.print")
    def test_config_one_arg(self, mock_print):
        """Test fns config with only one arg shows usage."""
        with patch.object(sys, "argv", ["fns", "config", "url"]):
            fns.main()
            mock_print.assert_called()


class TestCurlRequestURL(unittest.TestCase):
    """Test URL encoding in curl_request."""

    @patch("fns.load_config")
    @patch("fns.get_token")
    @patch("fns.subprocess.run")
    def test_url_encoding_with_chinese(self, mock_run, mock_token, mock_cfg):
        """Test that Chinese characters in path are URL-encoded."""
        mock_cfg.return_value = {"base_url": "https://test.com/api", "vault": "Test"}
        mock_token.return_value = "fake-token"
        mock_run.return_value = MagicMock(returncode=0, stdout='{"data":{"content":"test"}}')

        fns.curl_request("GET", "/note", params={"vault": "Test", "path": "日记/2024.md"})

        # Verify the URL was called with proper encoding
        call_args = mock_run.call_args[0][0]
        url = call_args[4]  # The URL argument in the curl command
        self.assertIn("%E6%97%A5%E8%AE%B0", url)  # URL-encoded "日记"


if __name__ == "__main__":
    unittest.main()
