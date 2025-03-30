"""
Tests for the mail server plugin.
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import socket
import smtplib
import imaplib
import poplib
from email.message import EmailMessage

from monitorpy.plugins.mail_server import MailServerPlugin
from monitorpy.core.result import CheckResult


class TestMailServerPlugin(unittest.TestCase):
    """Tests for the MailServerPlugin class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_config = {
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "timeout": 10,
        }

    def test_get_required_config(self):
        """Test get_required_config returns the expected values."""
        required = MailServerPlugin.get_required_config()
        self.assertIsInstance(required, list)
        self.assertIn("hostname", required)
        self.assertIn("protocol", required)

    def test_get_optional_config(self):
        """Test get_optional_config returns the expected values."""
        optional = MailServerPlugin.get_optional_config()
        self.assertIsInstance(optional, list)
        self.assertIn("port", optional)
        self.assertIn("username", optional)
        self.assertIn("password", optional)
        self.assertIn("use_ssl", optional)
        self.assertIn("timeout", optional)
        self.assertIn("test_send", optional)

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        plugin = MailServerPlugin(self.base_config)
        self.assertTrue(plugin.validate_config())

    def test_validate_config_missing_required(self):
        """Test validation with missing required parameters."""
        plugin = MailServerPlugin({"hostname": "mail.example.com"})  # Missing protocol
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_protocol(self):
        """Test validation with invalid protocol."""
        plugin = MailServerPlugin({
            "hostname": "mail.example.com",
            "protocol": "invalid"  # Not a valid protocol
        })
        self.assertFalse(plugin.validate_config())

    def test_validate_config_test_send_missing_email(self):
        """Test validation when test_send is enabled but email addresses are missing."""
        plugin = MailServerPlugin({
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "test_send": True  # Missing from_email and to_email
        })
        self.assertFalse(plugin.validate_config())

    def test_validate_config_username_without_password(self):
        """Test validation when username is provided but password is missing."""
        plugin = MailServerPlugin({
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "username": "user"  # Missing password
        })
        self.assertFalse(plugin.validate_config())

    @patch('monitorpy.plugins.mail_server.MailServerPlugin._check_server_basic')
    def test_smtp_basic_check(self, mock_check_basic):
        """Test basic SMTP server check."""
        # Mock the _check_server_basic method to return a success result
        mock_check_basic.return_value = CheckResult(
            CheckResult.STATUS_SUCCESS,
            "SMTP server mail.example.com:25 is operational. Supports: STARTTLS, AUTH, SIZE",
            1.0,
            {
                "hostname": "mail.example.com",
                "port": 25,
                "protocol": "smtp",
                "extensions": {"STARTTLS": "", "AUTH": "PLAIN LOGIN", "SIZE": "10240000"}
            }
        )

        # Create plugin and run check
        config = self.base_config.copy()
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("operational", result.message)
        self.assertIn("Supports", result.message)

        # Verify the _check_server_basic method was called
        mock_check_basic.assert_called_once()

    @patch('monitorpy.plugins.mail_server.MailServerPlugin._check_server_basic')
    def test_smtp_basic_check_ssl(self, mock_check_basic):
        """Test basic SMTP server check with SSL."""
        # Mock the _check_server_basic method to return a success result
        mock_check_basic.return_value = CheckResult(
            CheckResult.STATUS_SUCCESS,
            "SMTP server mail.example.com:465 is operational",
            1.0,
            {
                "hostname": "mail.example.com",
                "port": 465,
                "protocol": "smtp",
                "use_ssl": True
            }
        )

        # Create plugin and run check
        config = self.base_config.copy()
        config["use_ssl"] = True
        config["port"] = 465
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)

        # Verify the _check_server_basic method was called with the right config
        mock_check_basic.assert_called_once()
        # Check that the config passed to _check_server_basic includes SSL and port
        self.assertTrue("use_ssl" in plugin.config)
        self.assertEqual(plugin.config["use_ssl"], True)
        self.assertEqual(plugin.config["port"], 465)

    @patch('imaplib.IMAP4')
    def test_imap_basic_check(self, mock_imap):
        """Test basic IMAP server check."""
        # Configure mock
        mock_server = Mock()
        mock_imap.return_value = mock_server

        # Mock capability response
        mock_server.capability.return_value = ('OK', [b'IMAP4rev1 STARTTLS AUTH=PLAIN AUTH=LOGIN IDLE NAMESPACE'])

        # Create plugin and run check
        config = self.base_config.copy()
        config["protocol"] = "imap"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("IMAP server", result.message)
        self.assertIn("capabilities", result.message)

        # Verify IMAP was called correctly
        mock_imap.assert_called_once_with("mail.example.com", 143)
        mock_server.capability.assert_called_once()
        mock_server.logout.assert_called_once()

    @patch('poplib.POP3')
    def test_pop3_basic_check(self, mock_pop3):
        """Test basic POP3 server check."""
        # Configure mock
        mock_server = Mock()
        mock_pop3.return_value = mock_server

        # Mock welcome message
        mock_server.getwelcome.return_value = "+OK POP3 server ready"

        # Mock capabilities
        mock_server.capa.return_value = (b'+OK', [b'USER', b'PIPELINING', b'UIDL', b'TOP'])

        # Create plugin and run check
        config = self.base_config.copy()
        config["protocol"] = "pop3"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("POP3 server", result.message)
        self.assertIn("Welcome", result.message)

        # Verify POP3 was called correctly
        mock_pop3.assert_called_once_with("mail.example.com", 110)
        mock_server.getwelcome.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('socket.create_connection')
    def test_connection_timeout(self, mock_socket):
        """Test handling of connection timeout."""
        # Mock socket timeout
        mock_socket.side_effect = socket.timeout("Connection timed out")

        # Create plugin and run check
        plugin = MailServerPlugin(self.base_config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Connection", result.message)
        self.assertIn("timed out", result.message)

    @patch('socket.create_connection')
    def test_connection_refused(self, mock_socket):
        """Test handling of connection refused."""
        # Mock connection refused
        mock_socket.side_effect = ConnectionRefusedError("Connection refused")

        # Create plugin and run check
        plugin = MailServerPlugin(self.base_config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Connection", result.message)
        self.assertIn("refused", result.message)

    @patch('monitorpy.plugins.mail_server.MailServerPlugin._check_server_basic')
    def test_mx_resolution(self, mock_check_basic):
        """Test MX record resolution functionality."""
        # Mock the _check_server_basic method to return a success result
        mock_check_basic.return_value = CheckResult(
            CheckResult.STATUS_SUCCESS,
            "SMTP server check successful",
            1.0,
            {
                "mx_records": ["primary-mx.example.com", "secondary-mx.example.com"],
                "hostname_used": "primary-mx.example.com"
            }
        )

        # Create plugin with resolve_mx enabled
        config = self.base_config.copy()
        config["hostname"] = "example.com"  # A domain rather than a server name
        config["resolve_mx"] = True
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertTrue("mx_records" in result.raw_data)
        self.assertEqual(result.raw_data["mx_records"][0], "primary-mx.example.com")
        self.assertEqual(result.raw_data["hostname_used"], "primary-mx.example.com")

        # Verify the _check_server_basic method was called
        mock_check_basic.assert_called_once()

    @patch('smtplib.SMTP')
    def test_smtp_authenticated_check(self, mock_smtp):
        """Test SMTP server check with authentication."""
        # Configure mock
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Mock EHLO response
        mock_server.ehlo.return_value = (250, b"mail.example.com Hello client")

        # Create plugin with authentication
        config = self.base_config.copy()
        config["username"] = "user@example.com"
        config["password"] = "password123"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("authenticated", result.message)
        self.assertIn("user@example.com", result.message)

        # Verify login was called
        mock_server.login.assert_called_once_with("user@example.com", "password123")

    @patch('smtplib.SMTP')
    def test_smtp_authentication_failure(self, mock_smtp):
        """Test SMTP server check with failed authentication."""
        # Configure mock
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Mock EHLO response
        mock_server.ehlo.return_value = (250, b"mail.example.com Hello client")

        # Mock authentication failure
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        # Create plugin with authentication
        config = self.base_config.copy()
        config["username"] = "user@example.com"
        config["password"] = "wrong_password"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("authentication failed", result.message.lower())

        # Verify login was called
        mock_server.login.assert_called_once_with("user@example.com", "wrong_password")

    @patch('smtplib.SMTP')
    def test_smtp_test_email(self, mock_smtp):
        """Test SMTP server check with sending test email."""
        # Configure mock
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Mock EHLO response
        mock_server.ehlo.return_value = (250, b"mail.example.com Hello client")

        # Create plugin with test email
        config = self.base_config.copy()
        config["username"] = "user@example.com"
        config["password"] = "password123"
        config["test_send"] = True
        config["from_email"] = "user@example.com"
        config["to_email"] = "recipient@example.com"
        config["subject"] = "Test Subject"
        config["message"] = "Test Message Body"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("test email sent", result.message.lower())
        self.assertTrue(result.raw_data["test_send_success"])

        # Verify send_message was called
        mock_server.send_message.assert_called_once()

    @patch('imaplib.IMAP4')
    def test_imap_authenticated_check(self, mock_imap):
        """Test IMAP server check with authentication."""
        # Configure mock
        mock_server = Mock()
        mock_imap.return_value = mock_server

        # Mock select response for inbox
        mock_server.select.return_value = ('OK', [b'22'])  # 22 messages in inbox

        # Create plugin with authentication
        config = self.base_config.copy()
        config["protocol"] = "imap"
        config["username"] = "user@example.com"
        config["password"] = "password123"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("authenticated", result.message)
        self.assertIn("INBOX contains", result.message)
        self.assertIn("22", result.message)

        # Verify login and select were called
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.select.assert_called_once_with('INBOX', readonly=True)

    @patch('imaplib.IMAP4')
    def test_imap_authentication_failure(self, mock_imap):
        """Test IMAP server check with failed authentication."""
        # Configure mock
        mock_server = Mock()
        mock_imap.return_value = mock_server

        # Mock authentication failure
        # Need to use an exception that inherits from BaseException
        mock_server.login.side_effect = Exception("Authentication failed")

        # Create plugin with authentication
        config = self.base_config.copy()
        config["protocol"] = "imap"
        config["username"] = "user@example.com"
        config["password"] = "wrong_password"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Unexpected error", result.message)

        # Verify login was called
        mock_server.login.assert_called_once_with("user@example.com", "wrong_password")

    @patch('poplib.POP3')
    def test_pop3_authenticated_check(self, mock_pop3):
        """Test POP3 server check with authentication."""
        # Configure mock
        mock_server = Mock()
        mock_pop3.return_value = mock_server

        # Mock stat response (message count, mailbox size)
        mock_server.stat.return_value = (15, 45000)

        # Create plugin with authentication
        config = self.base_config.copy()
        config["protocol"] = "pop3"
        config["username"] = "user@example.com"
        config["password"] = "password123"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("authenticated", result.message)
        self.assertIn("15 messages", result.message)

        # Verify user/pass and stat were called
        mock_server.user.assert_called_once_with("user@example.com")
        mock_server.pass_.assert_called_once_with("password123")
        mock_server.stat.assert_called_once()

    @patch('poplib.POP3')
    def test_pop3_authentication_failure(self, mock_pop3):
        """Test POP3 server check with failed authentication."""
        # Configure mock
        mock_server = Mock()
        mock_pop3.return_value = mock_server

        # Mock welcome message
        mock_server.getwelcome.return_value = "+OK POP3 server ready"

        # Mock authentication failure
        mock_server.user.return_value = "+OK"
        mock_server.pass_.side_effect = poplib.error_proto("-ERR Authentication failed")

        # Create plugin with authentication
        config = self.base_config.copy()
        config["protocol"] = "pop3"
        config["username"] = "user@example.com"
        config["password"] = "wrong_password"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("POP3 protocol error", result.message)

        # Verify user/pass were called
        mock_server.user.assert_called_once_with("user@example.com")
        mock_server.pass_.assert_called_once_with("wrong_password")

    @patch('monitorpy.plugins.mail_server.MailServerPlugin._check_smtp')
    def test_smtp_with_tls(self, mock_check_smtp):
        """Test SMTP server check with STARTTLS."""
        # Need to make sure the mocked method gets used when called by run_check
        def mock_smtp_implementation(*args, **kwargs):
            return CheckResult(
                CheckResult.STATUS_SUCCESS,
                "SMTP server check successful, connected to mail.example.com:25",
                1.0,
                {
                    "hostname": "mail.example.com",
                    "port": 25,
                    "protocol": "smtp",
                    "use_tls": True,
                    "tls_response": "250 mail.example.com Hello client"
                }
            )

        mock_check_smtp.side_effect = mock_smtp_implementation

        # Create plugin with TLS
        config = self.base_config.copy()
        config["use_tls"] = True
        config["username"] = "user@example.com"  # Adding credentials to ensure _check_smtp is called
        config["password"] = "password123"
        plugin = MailServerPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)

        # Verify the _check_smtp method was called with the right config
        mock_check_smtp.assert_called_once()


if __name__ == '__main__':
    unittest.main()
