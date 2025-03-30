"""
Mail server monitoring plugin for checking SMTP, IMAP, and POP3 functionality.
"""
import time
import socket
import smtplib
import imaplib
import poplib
import ssl
from email.message import EmailMessage
from typing import Dict, Any, List, Optional, Tuple

from monitorpy.core import MonitorPlugin, CheckResult, register_plugin
from monitorpy.utils import get_logger

# Configure logging
logger = get_logger("plugins.mail_server")


@register_plugin("mail_server")
class MailServerPlugin(MonitorPlugin):
    """
    Plugin for checking mail server functionality.

    Verifies mail server connectivity, authentication, and optionally sends test emails.
    This plugin supports SMTP, IMAP, and POP3 protocols and can perform both basic
    connectivity checks and authenticated checks. It can also resolve MX records
    for a domain to find the actual mail servers.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """
        Get required configuration parameters.

        Returns:
            List[str]: List of required parameter names
        """
        return ["hostname", "protocol"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """
        Get optional configuration parameters.

        Returns:
            List[str]: List of optional parameter names
        """
        return [
            "port",
            "username",
            "password",
            "use_ssl",
            "use_tls",
            "timeout",
            "from_email",
            "to_email",
            "test_send",
            "subject",
            "message",
            "resolve_mx"
        ]

    def validate_config(self) -> bool:
        """
        Validate that the required configuration parameters are present and properly formatted.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check that all required keys are present
        if not all(key in self.config for key in self.get_required_config()):
            logger.error(f"Missing required configuration parameters: {self.get_required_config()}")
            return False

        # Validate protocol
        protocol = self.config.get("protocol", "").lower()
        valid_protocols = ["smtp", "imap", "pop3"]
        if protocol not in valid_protocols:
            logger.error(f"Invalid protocol: {protocol}. Must be one of: {', '.join(valid_protocols)}")
            return False

        # If test_send is enabled, validate email addresses
        if self.config.get("test_send", False):
            if "from_email" not in self.config or "to_email" not in self.config:
                logger.error("When test_send is enabled, from_email and to_email are required")
                return False

        # If username is provided, password should also be provided
        if "username" in self.config and "password" not in self.config:
            logger.error("Password is required when username is provided")
            return False

        return True

    def run_check(self) -> CheckResult:
        """
        Run the mail server check.

        Returns:
            CheckResult: The result of the check
        """
        hostname = self.config["hostname"]
        protocol = self.config["protocol"].lower()
        timeout = self.config.get("timeout", 30)
        username = self.config.get("username")
        password = self.config.get("password")

        try:
            logger.debug(f"Checking {protocol.upper()} server {hostname}")
            start_time = time.time()

            # Determine which check to perform
            if not username or not password:
                # If no credentials, perform basic check
                result = self._check_server_basic()
            elif protocol == "smtp":
                result = self._check_smtp()
            elif protocol == "imap":
                result = self._check_imap()
            elif protocol == "pop3":
                result = self._check_pop3()
            else:
                # This shouldn't happen due to validation, but just in case
                return CheckResult(
                    CheckResult.STATUS_ERROR,
                    f"Unsupported protocol: {protocol}",
                    0.0
                )

            end_time = time.time()
            result.response_time = end_time - start_time

            logger.info(f"Mail server check result: {result.status} - {result.message}")
            return result

        except Exception as e:
            logger.exception(f"Unexpected error checking mail server {hostname}")
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Unexpected error: {str(e)}",
                time.time() - start_time if 'start_time' in locals() else 0.0,
                {"error": str(e), "error_type": type(e).__name__}
            )

    def _check_server_basic(self) -> CheckResult:
        """
        Perform a basic check of mail server connectivity without authentication.
        Similar to an MXToolbox check - just tests if the server responds.

        Returns:
            CheckResult: The result of the check
        """
        hostname = self.config["hostname"]
        protocol = self.config["protocol"].lower()
        timeout = self.config.get("timeout", 30)
        port = self.config.get("port")  # We'll set defaults based on protocol
        use_ssl = self.config.get("use_ssl", False)

        # Default ports for different protocols if not specified
        if not port:
            if protocol == "smtp":
                port = 465 if use_ssl else 25
            elif protocol == "imap":
                port = 993 if use_ssl else 143
            elif protocol == "pop3":
                port = 995 if use_ssl else 110

        raw_data = {
            "hostname": hostname,
            "port": port,
            "protocol": protocol,
            "use_ssl": use_ssl,
            "mx_records": None
        }

        try:
            # Check for MX records if requested
            if self.config.get("resolve_mx", False) and "." in hostname and not hostname[0].isdigit():
                try:
                    import dns.resolver
                    mx_records = dns.resolver.resolve(hostname, 'MX')
                    mx_list = [(rec.preference, str(rec.exchange).rstrip('.')) for rec in mx_records]
                    mx_list.sort()  # Sort by preference

                    raw_data["mx_records"] = [mx[1] for mx in mx_list]

                    # Use the highest priority MX record
                    if raw_data["mx_records"]:
                        hostname = raw_data["mx_records"][0]
                        raw_data["hostname_used"] = hostname
                        logger.info(f"Using highest priority MX record: {hostname}")
                except ImportError:
                    logger.warning("dnspython library not installed. Cannot resolve MX records.")
                    raw_data["mx_error"] = "dnspython library not installed"
                except Exception as e:
                    logger.warning(f"Could not resolve MX records for {hostname}: {e}")
                    raw_data["mx_error"] = str(e)

            # SMTP basic check
            if protocol == "smtp":
                socket.setdefaulttimeout(timeout)
                if use_ssl:
                    server = smtplib.SMTP_SSL(hostname, port, timeout=timeout)
                else:
                    server = smtplib.SMTP(hostname, port, timeout=timeout)

                # Get initial connection info
                if hasattr(server, 'sock') and server.sock:
                    raw_data["local_address"] = server.sock.getsockname()[0]
                    raw_data["remote_address"] = server.sock.getpeername()[0]

                # Check if server accepts EHLO
                ehlo_code, ehlo_message = server.ehlo('monitorpy.local')
                raw_data["ehlo_code"] = ehlo_code
                raw_data["ehlo_message"] = ehlo_message.decode('utf-8') if isinstance(ehlo_message, bytes) else str(ehlo_message)

                # Check supported features
                raw_data["supports_tls"] = server.has_extn('STARTTLS')
                raw_data["extensions"] = {k.decode('utf-8') if isinstance(k, bytes) else k:
                                         v.decode('utf-8') if isinstance(v, bytes) else v
                                         for k, v in server.esmtp_features.items()}

                server.quit()

                # Create a user-friendly message
                if raw_data.get("hostname_used"):
                    message = f"SMTP server for {self.config['hostname']} (using {hostname}:{port}) is operational"
                else:
                    message = f"SMTP server {hostname}:{port} is operational"

                if raw_data["extensions"]:
                    message += f". Supports: {', '.join(raw_data['extensions'].keys())}"

                return CheckResult(
                    CheckResult.STATUS_SUCCESS,
                    message,
                    0.0,  # Will be updated in run_check
                    raw_data
                )

            # IMAP basic check
            elif protocol == "imap":
                socket.setdefaulttimeout(timeout)
                if use_ssl:
                    server = imaplib.IMAP4_SSL(hostname, port)
                else:
                    server = imaplib.IMAP4(hostname, port)

                # Get capabilities
                typ, capabilities_data = server.capability()
                capabilities_str = capabilities_data[0].decode('utf-8') if isinstance(capabilities_data[0], bytes) else str(capabilities_data[0])
                raw_data["capabilities"] = capabilities_str
                capabilities_list = capabilities_str.split()

                server.logout()

                # Create a user-friendly message
                if raw_data.get("hostname_used"):
                    message = f"IMAP server for {self.config['hostname']} (using {hostname}:{port}) is operational"
                else:
                    message = f"IMAP server {hostname}:{port} is operational"

                if capabilities_list:
                    # Show a few important capabilities
                    important_caps = [cap for cap in capabilities_list if any(x in cap for x in ["AUTH=", "STARTTLS", "IDLE", "UIDPLUS"])]
                    if important_caps:
                        message += f". Notable capabilities: {', '.join(important_caps)}"

                return CheckResult(
                    CheckResult.STATUS_SUCCESS,
                    message,
                    0.0,  # Will be updated in run_check
                    raw_data
                )

            # POP3 basic check
            elif protocol == "pop3":
                socket.setdefaulttimeout(timeout)
                if use_ssl:
                    server = poplib.POP3_SSL(hostname, port)
                else:
                    server = poplib.POP3(hostname, port)

                # Get welcome message
                welcome = server.getwelcome()
                raw_data["welcome_message"] = welcome

                # Get capabilities if available
                try:
                    capabilities_resp = server.capa()
                    if capabilities_resp[0].startswith(b"+OK") or capabilities_resp[0].startswith("+OK"):
                        capabilities_list = [cap.decode('utf-8') if isinstance(cap, bytes) else str(cap) for cap in capabilities_resp[1]]
                        raw_data["capabilities"] = capabilities_list
                except Exception as e:
                    raw_data["capabilities_error"] = str(e)
                    raw_data["capabilities"] = "Not supported or error"

                server.quit()

                # Create a user-friendly message
                if raw_data.get("hostname_used"):
                    message = f"POP3 server for {self.config['hostname']} (using {hostname}:{port}) is operational"
                else:
                    message = f"POP3 server {hostname}:{port} is operational"

                if welcome:
                    welcome_str = welcome if isinstance(welcome, str) else welcome.decode('utf-8')
                    if len(welcome_str) > 50:
                        welcome_str = welcome_str[:47] + "..."
                    message += f". Welcome: {welcome_str}"

                if raw_data.get("capabilities") and raw_data["capabilities"] != "Not supported or error":
                    message += f". Capabilities available."

                return CheckResult(
                    CheckResult.STATUS_SUCCESS,
                    message,
                    0.0,  # Will be updated in run_check
                    raw_data
                )

            else:
                return CheckResult(
                    CheckResult.STATUS_ERROR,
                    f"Unsupported protocol: {protocol}",
                    0.0,
                    raw_data
                )

        except (socket.gaierror, socket.timeout) as e:
            message = f"Connection error checking {protocol.upper()} server"
            if raw_data.get("hostname_used"):
                message += f" for {self.config['hostname']} (using {hostname}:{port})"
            else:
                message += f" {hostname}:{port}"
            message += f": {str(e)}"

            return CheckResult(
                CheckResult.STATUS_ERROR,
                message,
                0.0,
                raw_data
            )
        except Exception as e:
            message = f"Unexpected error checking {protocol.upper()} server"
            if raw_data.get("hostname_used"):
                message += f" for {self.config['hostname']} (using {hostname}:{port})"
            else:
                message += f" {hostname}:{port}"
            message += f": {str(e)}"

            return CheckResult(
                CheckResult.STATUS_ERROR,
                message,
                0.0,
                raw_data
            )

    def _check_smtp(self) -> CheckResult:
        """
        Check SMTP server connectivity and optionally send a test email.

        Returns:
            CheckResult: The result of the check
        """
        hostname = self.config["hostname"]
        port = self.config.get("port", 25)  # Default SMTP port
        use_ssl = self.config.get("use_ssl", False)
        use_tls = self.config.get("use_tls", False)
        username = self.config.get("username")
        password = self.config.get("password")
        timeout = self.config.get("timeout", 30)
        test_send = self.config.get("test_send", False)

        raw_data = {
            "hostname": hostname,
            "port": port,
            "protocol": "smtp",
            "use_ssl": use_ssl,
            "use_tls": use_tls,
            "authenticated": False,
            "test_send": test_send,
            "test_send_success": False
        }

        try:
            # Connect to the SMTP server
            if use_ssl:
                server = smtplib.SMTP_SSL(hostname, port, timeout=timeout)
            else:
                server = smtplib.SMTP(hostname, port, timeout=timeout)

            # Get the initial server response
            smtp_code, smtp_message = server.ehlo()
            raw_data["initial_response"] = f"{smtp_code} {smtp_message.decode('utf-8')}"

            if use_tls and not use_ssl:
                server.starttls()
                smtp_code, smtp_message = server.ehlo()
                raw_data["tls_response"] = f"{smtp_code} {smtp_message.decode('utf-8')}"

            # Authenticate if credentials are provided
            if username and password:
                server.login(username, password)
                raw_data["authenticated"] = True

            # Send a test email if requested
            if test_send:
                from_email = self.config["from_email"]
                to_email = self.config["to_email"]
                subject = self.config.get("subject", "MonitorPy Mail Server Test")
                message_text = self.config.get("message", "This is a test email from MonitorPy.")

                msg = EmailMessage()
                msg.set_content(message_text)
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = to_email

                server.send_message(msg)
                raw_data["test_send_success"] = True

            # Close the connection
            server.quit()

            # Determine the message based on what was tested
            if test_send:
                message = f"SMTP server check successful, test email sent from {self.config['from_email']} to {self.config['to_email']}"
            elif username and password:
                message = f"SMTP server check successful, authenticated as {username}"
            else:
                message = f"SMTP server check successful, connected to {hostname}:{port}"

            return CheckResult(
                CheckResult.STATUS_SUCCESS,
                message,
                0.0,  # Will be updated in run_check
                raw_data
            )

        except smtplib.SMTPAuthenticationError:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"SMTP authentication failed for user {username}",
                0.0,
                raw_data
            )
        except smtplib.SMTPException as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"SMTP error: {str(e)}",
                0.0,
                raw_data
            )
        except (socket.gaierror, socket.timeout) as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Connection error: {str(e)}",
                0.0,
                raw_data
            )
        except Exception as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Unexpected error: {str(e)}",
                0.0,
                raw_data
            )

    def _check_imap(self) -> CheckResult:
        """
        Check IMAP server connectivity and authentication.

        Returns:
            CheckResult: The result of the check
        """
        hostname = self.config["hostname"]
        port = self.config.get("port", 143)  # Default IMAP port
        use_ssl = self.config.get("use_ssl", False)
        username = self.config.get("username")
        password = self.config.get("password")
        timeout = self.config.get("timeout", 30)

        raw_data = {
            "hostname": hostname,
            "port": port,
            "protocol": "imap",
            "use_ssl": use_ssl,
            "authenticated": False
        }

        try:
            # Connect to the IMAP server
            socket.setdefaulttimeout(timeout)

            if use_ssl:
                server = imaplib.IMAP4_SSL(hostname, port)
            else:
                server = imaplib.IMAP4(hostname, port)

            # Authenticate if credentials are provided
            if username and password:
                server.login(username, password)
                raw_data["authenticated"] = True

                # Check mailbox status
                status, mailbox_data = server.select('INBOX', readonly=True)
                if status == 'OK':
                    raw_data["mailbox_status"] = "OK"
                    raw_data["mailbox_message_count"] = int(mailbox_data[0].decode('utf-8'))
                else:
                    raw_data["mailbox_status"] = "ERROR"

            # Close the connection
            server.logout()

            # Determine the message based on what was tested
            if username and password:
                message = f"IMAP server check successful, authenticated as {username}"
                if raw_data.get("mailbox_status") == "OK":
                    message += f", INBOX contains {raw_data['mailbox_message_count']} messages"
            else:
                message = f"IMAP server check successful, connected to {hostname}:{port}"

            return CheckResult(
                CheckResult.STATUS_SUCCESS,
                message,
                0.0,  # Will be updated in run_check
                raw_data
            )

        except imaplib.IMAP4.error as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"IMAP error: {str(e)}",
                0.0,
                raw_data
            )
        except (socket.gaierror, socket.timeout) as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Connection error: {str(e)}",
                0.0,
                raw_data
            )
        except Exception as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Unexpected error: {str(e)}",
                0.0,
                raw_data
            )

    def _check_pop3(self) -> CheckResult:
        """
        Check POP3 server connectivity and authentication.

        Returns:
            CheckResult: The result of the check
        """
        hostname = self.config["hostname"]
        port = self.config.get("port", 110)  # Default POP3 port
        use_ssl = self.config.get("use_ssl", False)
        username = self.config.get("username")
        password = self.config.get("password")
        timeout = self.config.get("timeout", 30)

        raw_data = {
            "hostname": hostname,
            "port": port,
            "protocol": "pop3",
            "use_ssl": use_ssl,
            "authenticated": False
        }

        try:
            # Connect to the POP3 server
            socket.setdefaulttimeout(timeout)

            if use_ssl:
                server = poplib.POP3_SSL(hostname, port)
            else:
                server = poplib.POP3(hostname, port)

            # Get server welcome message
            welcome = server.getwelcome()
            raw_data["welcome_message"] = welcome

            # Authenticate if credentials are provided
            if username and password:
                server.user(username)
                server.pass_(password)
                raw_data["authenticated"] = True

                # Get mailbox statistics
                message_count, mailbox_size = server.stat()
                raw_data["message_count"] = message_count
                raw_data["mailbox_size"] = mailbox_size

            # Close the connection
            server.quit()

            # Determine the message based on what was tested
            if username and password:
                message = f"POP3 server check successful, authenticated as {username}, {raw_data['message_count']} messages in mailbox"
            else:
                message = f"POP3 server check successful, connected to {hostname}:{port}"

            return CheckResult(
                CheckResult.STATUS_SUCCESS,
                message,
                0.0,  # Will be updated in run_check
                raw_data
            )

        except poplib.error_proto as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"POP3 protocol error: {str(e)}",
                0.0,
                raw_data
            )
        except (socket.gaierror, socket.timeout) as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Connection error: {str(e)}",
                0.0,
                raw_data
            )
        except Exception as e:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Unexpected error: {str(e)}",
                0.0,
                raw_data
            )
