"""
Tests for the website status plugin.
"""
import unittest
import requests  # Added missing import
from unittest.mock import patch, Mock

from monitorpy.plugins.website import WebsiteStatusPlugin
from monitorpy.core.result import CheckResult


class TestWebsiteStatusPlugin(unittest.TestCase):
    """Tests for the WebsiteStatusPlugin class."""

    def test_get_required_config(self):
        """Test get_required_config returns the expected values."""
        required = WebsiteStatusPlugin.get_required_config()
        self.assertIsInstance(required, list)
        self.assertIn("url", required)

    def test_get_optional_config(self):
        """Test get_optional_config returns the expected values."""
        optional = WebsiteStatusPlugin.get_optional_config()
        self.assertIsInstance(optional, list)
        self.assertIn("timeout", optional)
        self.assertIn("expected_status", optional)
        self.assertIn("method", optional)
        # Check a few more important ones
        self.assertIn("verify_ssl", optional)
        self.assertIn("expected_content", optional)

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        plugin = WebsiteStatusPlugin({"url": "https://example.com"})
        self.assertTrue(plugin.validate_config())

    def test_validate_config_missing_required(self):
        """Test validation with missing required parameters."""
        plugin = WebsiteStatusPlugin({})
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_url(self):
        """Test validation with invalid URL format."""
        plugin = WebsiteStatusPlugin({"url": "example.com"})  # Missing http:// or https://
        self.assertFalse(plugin.validate_config())

    @patch('requests.request')
    def test_run_check_success(self, mock_request):
        """Test successful website check."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Example content"
        mock_response.content = b"Example content"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "timeout": 5,
            "expected_status": 200
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("successful", result.message)
        self.assertIn("status_code", result.raw_data)
        self.assertEqual(result.raw_data["status_code"], 200)

        # Verify request was called with expected arguments
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://example.com")
        self.assertEqual(kwargs["timeout"], 5)

    @patch('requests.request')
    def test_run_check_wrong_status(self, mock_request):
        """Test website check with unexpected status code."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.content = b"Not Found"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "expected_status": 200
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("failed", result.message)
        self.assertIn("Expected status: 200", result.message)
        self.assertIn("actual: 404", result.message)

    @patch('requests.request')
    def test_run_check_content_match(self, mock_request):
        """Test website check with content matching."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Welcome to Example"
        mock_response.content = b"Welcome to Example"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "expected_content": "Welcome"
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("successful", result.message)

    @patch('requests.request')
    def test_run_check_content_mismatch(self, mock_request):
        """Test website check with content not matching."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Welcome to Example"
        mock_response.content = b"Welcome to Example"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "expected_content": "Missing Content"
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_WARNING)
        self.assertIn("content issues", result.message)
        self.assertTrue(result.raw_data["content_issues"])

    @patch('requests.request')
    def test_run_check_unexpected_content(self, mock_request):
        """Test website check with unexpected content present."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Error: Something went wrong"
        mock_response.content = b"Error: Something went wrong"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "unexpected_content": "Error"
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_WARNING)
        self.assertIn("content issues", result.message)
        self.assertTrue(result.raw_data["content_issues"])

    @patch('requests.request')
    def test_run_check_with_auth(self, mock_request):
        """Test website check with authentication."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Authenticated content"
        mock_response.content = b"Authenticated content"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.history = []

        mock_request.return_value = mock_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "auth_username": "user",
            "auth_password": "pass"
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)

        # Verify auth was passed correctly
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["auth"], ("user", "pass"))

    @patch('requests.request', side_effect=requests.exceptions.ConnectionError("Connection refused"))
    def test_run_check_connection_error(self, mock_request):
        """Test website check with connection error."""
        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com"
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Connection error", result.message)
        self.assertIn("error", result.raw_data)
        self.assertIn("error_type", result.raw_data)

    @patch('requests.request', side_effect=requests.exceptions.Timeout("Request timed out"))
    def test_run_check_timeout(self, mock_request):
        """Test website check with timeout."""
        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com",
            "timeout": 5
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Connection error", result.message)
        self.assertIn("timed out", result.raw_data["error"].lower())

    @patch('requests.request')
    def test_run_check_redirects(self, mock_request):
        """Test website check with redirects."""
        # Set up mock response with history
        redirect1 = Mock()
        redirect1.url = "https://example.com/redirect1"

        redirect2 = Mock()
        redirect2.url = "https://example.com/redirect2"

        final_response = Mock()
        final_response.status_code = 200
        final_response.text = "Final destination"
        final_response.content = b"Final destination"
        final_response.headers = {"Content-Type": "text/html"}
        final_response.history = [redirect1, redirect2]

        mock_request.return_value = final_response

        # Create plugin and run check
        plugin = WebsiteStatusPlugin({
            "url": "https://example.com/original",
            "follow_redirects": True
        })

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertEqual(len(result.raw_data["redirect_history"]), 2)
        self.assertEqual(result.raw_data["redirect_history"][0], "https://example.com/redirect1")

        # Verify request was called with follow_redirects=True
        args, kwargs = mock_request.call_args
        self.assertTrue(kwargs["allow_redirects"])


if __name__ == '__main__':
    unittest.main()
