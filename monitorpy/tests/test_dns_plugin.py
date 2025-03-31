"""
Tests for the DNS record plugin.
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import socket

from monitorpy.plugins.dns_plugin import DNSRecordPlugin, DNSPYTHON_AVAILABLE
from monitorpy.core.result import CheckResult


# Skip all tests if dnspython is not available
@unittest.skipIf(not DNSPYTHON_AVAILABLE, "dnspython library is not installed")
class TestDNSRecordPlugin(unittest.TestCase):
    """Tests for the DNSRecordPlugin class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_config = {
            "domain": "example.com",
            "record_type": "A",
            "timeout": 5
        }

    def test_get_required_config(self):
        """Test get_required_config returns the expected values."""
        required = DNSRecordPlugin.get_required_config()
        self.assertIsInstance(required, list)
        self.assertIn("domain", required)
        self.assertIn("record_type", required)

    def test_get_optional_config(self):
        """Test get_optional_config returns the expected values."""
        optional = DNSRecordPlugin.get_optional_config()
        self.assertIsInstance(optional, list)
        self.assertIn("expected_value", optional)
        self.assertIn("nameserver", optional)
        self.assertIn("check_propagation", optional)
        self.assertIn("check_authoritative", optional)
        self.assertIn("check_dnssec", optional)
        self.assertIn("timeout", optional)

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        plugin = DNSRecordPlugin(self.base_config)
        self.assertTrue(plugin.validate_config())

    def test_validate_config_missing_required(self):
        """Test validation with missing required parameters."""
        plugin = DNSRecordPlugin({"domain": "example.com"})  # Missing record_type
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_record_type(self):
        """Test validation with invalid record type."""
        plugin = DNSRecordPlugin({
            "domain": "example.com",
            "record_type": "INVALID"  # Not a valid DNS record type
        })
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_propagation_threshold(self):
        """Test validation with invalid propagation threshold."""
        plugin = DNSRecordPlugin({
            "domain": "example.com",
            "record_type": "A",
            "check_propagation": True,
            "propagation_threshold": 101  # Invalid: > 100%
        })
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_resolvers(self):
        """Test validation with invalid resolvers."""
        plugin = DNSRecordPlugin({
            "domain": "example.com",
            "record_type": "A",
            "check_propagation": True,
            "resolvers": ["not an IP address"]  # Invalid IP format
        })
        self.assertFalse(plugin.validate_config())

    @patch('dns.resolver.Resolver')
    def test_run_check_success(self, mock_resolver_class):
        """Test successful DNS record check."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Create plugin and run check
        plugin = DNSRecordPlugin(self.base_config)
        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("A record found for example.com", result.message)
        self.assertIn("192.0.2.1", result.message)
        self.assertIn("records", result.raw_data)
        self.assertEqual(result.raw_data["records"][0], "192.0.2.1")

        # Verify the resolve method was called with expected arguments
        mock_resolver.resolve.assert_called_once_with("example.com", "A")

    @patch('dns.resolver.Resolver')
    def test_run_check_expected_value_match(self, mock_resolver_class):
        """Test DNS record check with matching expected value."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Create plugin with expected value
        config = self.base_config.copy()
        config["expected_value"] = "192.0.2.1"
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("matches expected value", result.message)
        self.assertTrue(result.raw_data["expected_value_match"])

    @patch('dns.resolver.Resolver')
    def test_run_check_expected_value_mismatch(self, mock_resolver_class):
        """Test DNS record check with non-matching expected value."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Create plugin with expected value that won't match
        config = self.base_config.copy()
        config["expected_value"] = "192.0.2.2"  # Different IP
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Expected value", result.message)
        self.assertIn("not found", result.message)
        self.assertFalse(result.raw_data["expected_value_match"])

    @patch('dns.resolver.Resolver')
    def test_run_check_nxdomain(self, mock_resolver_class):
        """Test DNS record check for non-existent domain."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock NXDOMAIN exception
        import dns.resolver
        mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()

        # Create plugin and run check
        plugin = DNSRecordPlugin(self.base_config)
        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("does not exist", result.message)
        self.assertEqual(result.raw_data["error"], "NXDOMAIN")

    @patch('dns.resolver.Resolver')
    def test_run_check_no_answer(self, mock_resolver_class):
        """Test DNS record check with no answer for the requested type."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock NoAnswer exception
        import dns.resolver
        mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()

        # Create plugin and run check
        plugin = DNSRecordPlugin(self.base_config)
        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("No A records found", result.message)
        self.assertEqual(result.raw_data["error"], "NoAnswer")

    @patch('dns.resolver.Resolver')
    def test_run_check_timeout(self, mock_resolver_class):
        """Test DNS record check with timeout."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock Timeout exception
        import dns.resolver
        mock_resolver.resolve.side_effect = dns.resolver.Timeout()

        # Create plugin and run check
        plugin = DNSRecordPlugin(self.base_config)
        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Timeout", result.message)
        self.assertEqual(result.raw_data["error"], "Timeout")

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_propagation')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_propagation(self, mock_resolver_class, mock_check_propagation):
        """Test DNS record check with propagation checking."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock propagation check result
        mock_check_propagation.return_value = {
            "status": CheckResult.STATUS_SUCCESS,
            "total_count": 8,
            "successful_count": 8,
            "consistent_count": 8,
            "percentage": 100.0,
            "threshold": 80,
            "resolvers": []  # Would contain details about each resolver checked
        }

        # Create plugin with propagation checking enabled
        config = self.base_config.copy()
        config["check_propagation"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("propagation", result.raw_data)
        self.assertEqual(result.raw_data["propagation"]["percentage"], 100.0)

        # Verify propagation check was called
        mock_check_propagation.assert_called_once()

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_propagation')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_poor_propagation(self, mock_resolver_class, mock_check_propagation):
        """Test DNS record check with poor propagation."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock propagation check result with poor propagation
        mock_check_propagation.return_value = {
            "status": CheckResult.STATUS_ERROR,  # Poor propagation
            "total_count": 8,
            "successful_count": 8,
            "consistent_count": 4,  # Only 50% consistent
            "percentage": 50.0,
            "threshold": 80,
            "resolvers": []
        }

        # Create plugin with propagation checking enabled
        config = self.base_config.copy()
        config["check_propagation"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status,
                         CheckResult.STATUS_ERROR)  # Overall status should be ERROR due to poor propagation
        self.assertIn("Poor propagation", result.message)
        self.assertEqual(result.raw_data["propagation"]["percentage"], 50.0)

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_authoritative')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_authoritative(self, mock_resolver_class, mock_check_authoritative):
        """Test DNS record check with authoritative checking."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock authoritative check result
        mock_check_authoritative.return_value = {
            "is_authoritative": True,
            "nameserver": "ns1.example.com",
            "flags": "QR AA RD"
        }

        # Create plugin with authoritative checking enabled
        config = self.base_config.copy()
        config["check_authoritative"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("authoritative", result.raw_data)
        self.assertTrue(result.raw_data["authoritative"]["is_authoritative"])

        # Verify authoritative check was called
        mock_check_authoritative.assert_called_once()

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_authoritative')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_non_authoritative(self, mock_resolver_class, mock_check_authoritative):
        """Test DNS record check with non-authoritative response."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock authoritative check result indicating non-authoritative
        mock_check_authoritative.return_value = {
            "is_authoritative": False,
            "error": "Could not determine authoritative nameservers"
        }

        # Create plugin with authoritative checking enabled
        config = self.base_config.copy()
        config["check_authoritative"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_WARNING)  # Should be WARNING for non-authoritative
        self.assertIn("Non-authoritative response", result.message)
        self.assertFalse(result.raw_data["authoritative"]["is_authoritative"])

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_dnssec')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_dnssec(self, mock_resolver_class, mock_check_dnssec):
        """Test DNS record check with DNSSEC validation."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock DNSSEC check result
        mock_check_dnssec.return_value = {
            "is_valid": True,
            "is_signed": True,
            "flags": "QR RD RA AD"  # AD flag indicates DNSSEC validation
        }

        # Create plugin with DNSSEC checking enabled
        config = self.base_config.copy()
        config["check_dnssec"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("dnssec", result.raw_data)
        self.assertTrue(result.raw_data["dnssec"]["is_valid"])
        self.assertTrue(result.raw_data["dnssec"]["is_signed"])

        # Verify DNSSEC check was called
        mock_check_dnssec.assert_called_once()

    @patch('monitorpy.plugins.dns_plugin.DNSRecordPlugin._check_dnssec')
    @patch('dns.resolver.Resolver')
    def test_run_check_with_dnssec_failure(self, mock_resolver_class, mock_check_dnssec):
        """Test DNS record check with DNSSEC validation failure."""
        # Set up mock resolver
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver

        # Mock answers from the resolver
        mock_answer = MagicMock()
        mock_answer_item = MagicMock()
        mock_answer_item.address = "192.0.2.1"
        mock_answer_item.ttl = 3600

        mock_answer.__iter__.return_value = [mock_answer_item]
        mock_resolver.resolve.return_value = mock_answer

        # Mock DNSSEC check result with validation failure
        mock_check_dnssec.return_value = {
            "is_valid": False,
            "is_signed": True,
            "error": "DNSSEC validation failed"
        }

        # Create plugin with DNSSEC checking enabled
        config = self.base_config.copy()
        config["check_dnssec"] = True
        plugin = DNSRecordPlugin(config)

        result = plugin.run_check()

        # Verify result
        self.assertEqual(result.status, CheckResult.STATUS_ERROR)  # Should be ERROR for DNSSEC failure
        self.assertIn("DNSSEC validation failed", result.message)
        self.assertFalse(result.raw_data["dnssec"]["is_valid"])
        self.assertTrue(result.raw_data["dnssec"]["is_signed"])  # It's signed but validation failed


if __name__ == '__main__':
    unittest.main()