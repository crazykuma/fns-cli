"""Tests for FNS CLI - API layer."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from fns_cli.api import curl_request, handle_response
from fns_cli.config import _ctx


class TestCurlRequest(unittest.TestCase):
    """Test curl_request function."""

    def test_get_request(self):
        """Test GET request builds correct curl command."""
        _ctx["json_output"] = False
        with patch("fns_cli.api.subprocess.run") as mock_run, \
             patch("fns_cli.api.load_config", return_value={"base_url": "http://localhost/api"}), \
             patch("fns_cli.api.get_token", return_value="test-token"):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"code": 1, "status": True, "data": {"list": []}}),
                stderr=""
            )
            result = curl_request("GET", "/notes", params={"vault": "test"})
            self.assertEqual(result["code"], 1)
            call_args = mock_run.call_args[0][0]
            self.assertIn("curl", call_args)
            self.assertIn("GET", call_args)
            self.assertIn("Authorization: Bearer test-token", call_args)

    def test_post_request(self):
        """Test POST request with JSON body."""
        _ctx["json_output"] = False
        with patch("fns_cli.api.subprocess.run") as mock_run, \
             patch("fns_cli.api.load_config", return_value={"base_url": "http://localhost/api"}), \
             patch("fns_cli.api.get_token", return_value="test-token"):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"code": 1, "status": True}),
                stderr=""
            )
            curl_request("POST", "/note", json_data={"vault": "test", "path": "note.md"})
            call_args = mock_run.call_args[0][0]
            self.assertIn("POST", call_args)
            self.assertIn("Content-Type: application/json", call_args)

    def test_base_url_not_configured(self):
        """Test error when base URL is empty."""
        _ctx["json_output"] = True
        with patch("fns_cli.api.load_config", return_value={"base_url": ""}):
            with self.assertRaises(SystemExit):
                curl_request("GET", "/notes")


class TestHandleResponse(unittest.TestCase):
    """Test handle_response function."""

    def test_success_json_mode(self):
        """Test success in JSON mode returns data without exit."""
        _ctx["json_output"] = True
        data = {"code": 1, "status": True, "message": "OK"}
        with patch("click.echo") as mock_echo:
            result = handle_response(data, success_msg="Done!")
            self.assertEqual(result["code"], 1)
            mock_echo.assert_called_once()

    def test_success_text_mode(self):
        """Test success in text mode prints success message."""
        _ctx["json_output"] = False
        _ctx["quiet"] = False
        data = {"code": 1, "status": True, "message": "OK"}
        with patch("click.echo") as mock_echo:
            handle_response(data, success_msg="Done!")
            mock_echo.assert_called_once()

    def test_error_json_mode(self):
        """Test error in JSON mode returns data without exit."""
        _ctx["json_output"] = True
        data = {"code": 430, "status": False, "message": "Not found"}
        with patch("click.echo") as mock_echo:
            result = handle_response(data, error_prefix="Error")
            self.assertEqual(result["code"], 430)

    def test_error_text_mode(self):
        """Test error in text mode exits with message."""
        _ctx["json_output"] = False
        data = {"code": 0, "status": False, "message": "Error"}
        with self.assertRaises(SystemExit):
            handle_response(data, error_prefix="Error")


class TestConfig(unittest.TestCase):
    """Test config loading and saving."""

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()
        self._config_dir = os.path.join(self._temp_dir, "fns-cli")
        os.makedirs(self._config_dir, exist_ok=True)
        self._config_file = os.path.join(self._temp_dir, "config.json")

    def tearDown(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def test_save_and_load_config(self):
        cfg = {"base_url": "https://test.example.com/api", "vault": "TestVault"}
        with open(self._config_file, "w") as f:
            json.dump(cfg, f, indent=2)

        with open(self._config_file, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["base_url"], "https://test.example.com/api")
        self.assertEqual(loaded["vault"], "TestVault")


if __name__ == "__main__":
    unittest.main()
