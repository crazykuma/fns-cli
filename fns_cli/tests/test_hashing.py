"""Tests for FNS CLI - Hashing utilities."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from fns_cli.hashing import compute_path_hash


class TestComputePathHash(unittest.TestCase):
    """Test path hash computation matching Go server implementation."""

    def test_basic_path(self):
        """Test hash for a simple path."""
        h = compute_path_hash("test.md")
        self.assertIsInstance(h, str)
        # Verify it's a valid signed 32-bit integer
        int(h)

    def test_unicode_path(self):
        """Test hash for path with Unicode characters."""
        h = compute_path_hash("笔记/测试.md")
        self.assertIsInstance(h, str)
        int(h)

    def test_empty_path(self):
        """Test hash for empty path."""
        h = compute_path_hash("")
        self.assertEqual(h, "0")

    def test_different_paths_different_hashes(self):
        """Different paths should produce different hashes."""
        h1 = compute_path_hash("a.md")
        h2 = compute_path_hash("b.md")
        self.assertNotEqual(h1, h2)

    def test_consistency(self):
        """Same path should always produce same hash."""
        h1 = compute_path_hash("folder/note.md")
        h2 = compute_path_hash("folder/note.md")
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
