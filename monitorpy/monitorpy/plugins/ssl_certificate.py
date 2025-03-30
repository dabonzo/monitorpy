"""
SSL certificate monitoring plugin for checking certificate validity and expiration.
"""
import time
import socket
import ssl
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from monitorpy.core import MonitorPlugin, CheckResult, register_plugin
from monitorpy.utils import get_logger

# Configure logging
logger = get_logger("plugins.ssl")


@register_plugin("ssl_certificate")
class SSLCertificatePlugin(MonitorPlugin):
    """
    Plugin for checking SSL certificate validity and expiration.

    Verifies that a website's SSL certificate is valid and not expiring soon.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """
        Get required configuration parameters.

        Returns:
            List[str]: List of required parameter names
        """
        return ["hostname"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """
        Get optional configuration parameters.

        Returns:
            List[str]: List of optional parameter names
        """
        return [
            "port",
            "timeout",
            "warning_days",
            "critical_days",
            "check_chain",
            "verify_hostname"
        ]

    def validate_config(self) -> bool:
        """
        Validate that required configuration parameters are present and properly formatted.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check that all required keys are present
        if not all(key in self.config for key in self.get_required_config()):
            logger.error(f"Missing required configuration parameters: {self.get_required_config()}")
            return False

        # Extract hostname from URL if a full URL was provided
        hostname = self.config["hostname"]
        if hostname.startswith(("http://", "https://")):
            parsed_url = urllib.parse.urlparse(hostname)
            if not parsed_url.netloc:
                logger.error(f"Invalid URL format: {hostname}. Could not extract hostname.")
                return False

        return True

    def get_hostname_and_port(self) -> Tuple[str, int]:
        """
        Extract hostname and port from the configuration.

        Returns:
            Tuple[str, int]: Hostname and port
        """
        hostname = self.config["hostname"]
        port = self.config.get("port", 443)

        # Extract hostname from URL if a full URL was provided
        if hostname.startswith(("http://", "https://")):
            parsed_url = urllib.parse.urlparse(hostname)
            hostname = parsed_url.netloc

            # Extract port from URL if specified
            if ":" in hostname:
                hostname, port_str = hostname.split(":", 1)
                port = int(port_str)
            elif parsed_url.scheme == "http" and "port" not in self.config:
                port = 80

        return hostname, port

    def run_check(self) -> CheckResult:
        """
        Run the SSL certificate check.

        Returns:
            CheckResult: The result of the check
        """
        hostname, port = self.get_hostname_and_port()
        timeout = self.config.get("timeout", 30)
        warning_days = self.config.get("warning_days", 30)
        critical_days = self.config.get("critical_days", 14)
        check_chain = self.config.get("check_chain", False)
        verify_hostname = self.config.get("verify_hostname", True)

        try:
            logger.debug(f"Checking SSL certificate for {hostname}:{port} (timeout: {timeout}s)")
            start_time = time.time()

            # Create socket and get certificate
            context = ssl.create_default_context()
            if not verify_hostname:
                context.check_hostname = False

            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    # For checking the chain, we'd need to examine the entire chain
                    # This is a simplified implementation
                    if check_chain:
                        cipher = ssock.cipher()
                        protocol = ssock.version()

            end_time = time.time()
            response_time = end_time - start_time
            logger.debug(f"SSL check completed in {response_time:.4f}s")

            # Check certificate expiration
            expiration = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            now = datetime.now()
            days_until_expiration = (expiration - now).days

            # Check certificate validity period
            not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
            is_valid_period = not_before <= now <= expiration

            # Get certificate details
            subject = dict(item[0] for item in cert.get("subject", []))
            issuer = dict(item[0] for item in cert.get("issuer", []))

            # Determine certificate status
            if not is_valid_period:
                status = CheckResult.STATUS_ERROR
                if now < not_before:
                    message = f"Certificate not yet valid. Valid from {not_before.isoformat()}"
                else:
                    message = f"Certificate expired on {expiration.isoformat()}"
            elif days_until_expiration <= critical_days:
                status = CheckResult.STATUS_ERROR
                message = f"Certificate expires very soon: {days_until_expiration} days left (expires on {expiration.isoformat()})"
            elif days_until_expiration <= warning_days:
                status = CheckResult.STATUS_WARNING
                message = f"Certificate expiration approaching: {days_until_expiration} days left (expires on {expiration.isoformat()})"
            else:
                status = CheckResult.STATUS_SUCCESS
                message = f"Certificate valid until {expiration.isoformat()} ({days_until_expiration} days remaining)"

            # Prepare raw data
            raw_data = {
                "hostname": hostname,
                "port": port,
                "not_before": not_before.isoformat(),
                "not_after": expiration.isoformat(),
                "days_until_expiration": days_until_expiration,
                "subject": subject,
                "issuer": issuer,
                "version": cert.get("version"),
                "serial_number": cert.get("serialNumber"),
                "signature_algorithm": None,  # Not available in Python's ssl module
                "alternative_names": cert.get("subjectAltName", []),
            }

            # Add chain information if requested
            if check_chain:
                raw_data["cipher"] = cipher
                raw_data["protocol"] = protocol

            logger.info(f"SSL check result: {status} - {message}")
            return CheckResult(
                status=status,
                message=message,
                response_time=response_time,
                raw_data=raw_data
            )

        except ssl.SSLError as e:
            logger.exception(f"SSL error checking {hostname}:{port}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"SSL error: {str(e)}",
                response_time=0.0,
                raw_data={"error": str(e), "error_type": type(e).__name__}
            )
        except socket.timeout:
            logger.exception(f"Timeout connecting to {hostname}:{port}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Connection timed out after {timeout}s",
                response_time=timeout,
                raw_data={"error": "Connection timed out", "error_type": "socket.timeout"}
            )
        except socket.error as e:
            logger.exception(f"Socket error checking {hostname}:{port}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Connection error: {str(e)}",
                response_time=0.0,
                raw_data={"error": str(e), "error_type": type(e).__name__}
            )
        except Exception as e:
            logger.exception(f"Unexpected error checking SSL for {hostname}:{port}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Unexpected error: {str(e)}",
                response_time=0.0,
                raw_data={"error": str(e), "error_type": type(e).__name__}
            )
