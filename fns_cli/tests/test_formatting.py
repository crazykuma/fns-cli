"""Tests for FNS CLI - Formatting utilities."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from fns_cli.formatting import format_timestamp, format_size, echo
from fns_cli.config import _ctx


class TestFormatTimestamp(unittest.TestCase):
    """Test format_timestamp function."""

    def test_valid_timestamp(self):
        result = format_timestamp(1716206400000)
        self.assertRegex(result, r"2024-05-20 \d{2}:\d{2}:\d{2}")

    def test_empty_timestamp(self):
        self.assertEqual(format_timestamp(None), "")
        self.assertEqual(format_timestamp(0), "")
        self.assertEqual(format_timestamp(""), "")

    def test_invalid_timestamp(self):
        result = format_timestamp("not-a-number")
        self.assertEqual(result, "not-a-number")


class TestFormatSize(unittest.TestCase):
    """Test format_size function."""

    def test_zero_bytes(self):
        self.assertEqual(format_size(0), "0.0 B")

    def test_bytes(self):
        self.assertEqual(format_size(512), "512.0 B")

    def test_kilobytes(self):
        self.assertEqual(format_size(1024), "1.0 KB")

    def test_megabytes(self):
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")

    def test_none(self):
        self.assertEqual(format_size(None), "0 B")


class TestEcho(unittest.TestCase):
    """Test echo helper function."""

    def test_quiet_mode(self):
        _ctx["quiet"] = True
        with patch("click.echo") as mock_echo:
            echo("should not print")
            mock_echo.assert_not_called()
        _ctx.clear()

    def test_normal_mode(self):
        _ctx["quiet"] = False
        with patch("click.echo") as mock_echo:
            echo("hello")
            mock_echo.assert_called_once_with("hello")
        _ctx.clear()


if __name__ == "__main__":
    unittest.main()
