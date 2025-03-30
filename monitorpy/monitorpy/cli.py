"""
Command-line interface for the monitorpy package.
"""
import argparse
import json
import sys
import logging
from typing import Dict, Any, List, Optional

from monitorpy.core import registry, run_check
from monitorpy.utils import setup_logging, format_result, get_logger
from monitorpy.utils.formatting import ColorFormatter
import monitorpy.plugins  # Import to register all plugins

logger = get_logger("cli")

def parse_header(header_str: str) -> Optional[tuple]:
    """
    Parse a header string in the format 'Name: Value'.

    Args:
        header_str: The header string to parse

    Returns:
        Optional[tuple]: Tuple of (name, value) or None if invalid
    """
    if not header_str or ':' not in header_str:
        return None

    name, value = header_str.split(':', 1)
    return name.strip(), value.strip()


def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Set up the command-line argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="MonitorPy - A plugin-based website and service monitoring tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path (if not specified, logs to stdout only)"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List plugins command
    list_parser = subparsers.add_parser(
        "list",
        help="List available plugins",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Check website command
    website_parser = subparsers.add_parser(
        "website",
        help="Check website availability",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    website_parser.add_argument("url", help="URL to check")
    website_parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    website_parser.add_argument("--status", type=int, default=200, help="Expected HTTP status code")
    website_parser.add_argument("--method", default="GET", help="HTTP method (GET, POST, etc.)")
    website_parser.add_argument("--header", action="append", help="HTTP header in format 'Name: Value'")
    website_parser.add_argument("--body", help="Request body data")
    website_parser.add_argument("--content", help="Content that should be present in the response")
    website_parser.add_argument("--no-content", help="Content that should NOT be present in the response")
    website_parser.add_argument("--auth-username", help="Username for basic authentication")
    website_parser.add_argument("--auth-password", help="Password for basic authentication")
    website_parser.add_argument("--no-verify", action="store_true", help="Disable SSL certificate verification")
    website_parser.add_argument("--no-redirect", action="store_true", help="Disable following redirects")
    website_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    website_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    # Check SSL certificate command
    ssl_parser = subparsers.add_parser(
        "ssl",
        help="Check SSL certificate",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ssl_parser.add_argument("hostname", help="Hostname or URL to check")
    ssl_parser.add_argument("--port", type=int, help="Port number (default: 443)")
    ssl_parser.add_argument("--timeout", type=int, default=30, help="Connection timeout in seconds")
    ssl_parser.add_argument("--warning", type=int, default=30, help="Warning threshold in days")
    ssl_parser.add_argument("--critical", type=int, default=14, help="Critical threshold in days")
    ssl_parser.add_argument("--check-chain", action="store_true", help="Check certificate chain")
    ssl_parser.add_argument("--no-verify-hostname", action="store_true", help="Disable hostname verification")
    ssl_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    ssl_parser.add_argument("--json", action="store_true", help="Output results as JSON")


        # Mail server check command
    mail_parser = subparsers.add_parser(
        "mail",
        help="Check mail server connectivity and functionality",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    mail_parser.add_argument("hostname", help="Mail server hostname")
    mail_parser.add_argument("--protocol", choices=["smtp", "imap", "pop3"], default="smtp", help="Mail protocol to check")
    mail_parser.add_argument("--port", type=int, help="Server port (defaults to standard port for protocol)")
    mail_parser.add_argument("--username", help="Username for authentication")
    mail_parser.add_argument("--password", help="Password for authentication")
    mail_parser.add_argument("--ssl", action="store_true", help="Use SSL connection")
    mail_parser.add_argument("--tls", action="store_true", help="Use TLS connection (SMTP only)")
    mail_parser.add_argument("--timeout", type=int, default=30, help="Connection timeout in seconds")
    mail_parser.add_argument("--send-test", action="store_true", help="Send test email (SMTP only)")
    mail_parser.add_argument("--from", dest="from_email", help="From email address (for test email)")
    mail_parser.add_argument("--to", dest="to_email", help="To email address (for test email)")
    mail_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    mail_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    mail_parser.add_argument("--basic-check", action="store_true",
                         help="Perform basic connectivity check without authentication")
    mail_parser.add_argument("--resolve-mx", action="store_true",
                         help="Resolve MX records for domain and check the highest priority server")

    return parser


def handle_list_command() -> int:
    """
    Handle the 'list' command to display available plugins.

    Returns:
        int: Exit code (0 for success)
    """
    print(ColorFormatter.highlight("Available plugins:"))
    for name, info in registry.get_all_plugins().items():
        print(f"\n{ColorFormatter.highlight(name)}:")
        print(f"  Description: {info['description']}")
        print(f"  Required config: {', '.join(info['required_config'])}")
        print(f"  Optional config: {', '.join(info['optional_config'])}")

    return 0


def handle_website_command(args) -> int:
    """
    Handle the 'website' command to check a website.

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    config = {
        "url": args.url,
        "timeout": args.timeout,
        "expected_status": args.status,
        "method": args.method,
        "verify_ssl": not args.no_verify,
        "follow_redirects": not args.no_redirect
    }

    # Parse headers if provided
    if args.header:
        headers = {}
        for header_str in args.header:
            header = parse_header(header_str)
            if header:
                headers[header[0]] = header[1]

        if headers:
            config["headers"] = headers

    # Add other optional configuration
    if args.body:
        config["body"] = args.body

    if args.content:
        config["expected_content"] = args.content

    if args.no_content:
        config["unexpected_content"] = args.no_content

    if args.auth_username:
        config["auth_username"] = args.auth_username

    if args.auth_password:
        config["auth_password"] = args.auth_password

    result = run_check("website_status", config)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_result(result, args.verbose))

    return 0 if result.is_success() else (1 if result.is_warning() else 2)


def handle_ssl_command(args) -> int:
    """
    Handle the 'ssl' command to check an SSL certificate.

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    config = {
        "hostname": args.hostname,
        "timeout": args.timeout,
        "warning_days": args.warning,
        "critical_days": args.critical,
        "check_chain": args.check_chain,
        "verify_hostname": not args.no_verify_hostname
    }

    if args.port:
        config["port"] = args.port

    result = run_check("ssl_certificate", config)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_result(result, args.verbose))

    return 0 if result.is_success() else (1 if result.is_warning() else 2)

def handle_mail_command(args) -> int:
    """
    Handle the 'mail' command to check a mail server.

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    config = {
        "hostname": args.hostname,
        "protocol": args.protocol,
        "timeout": args.timeout
    }

    # Add SSL/TLS configuration
    if args.ssl:
        config["use_ssl"] = True

    if args.protocol == "smtp" and args.tls:
        config["use_tls"] = True

    # Add custom port if specified
    if args.port:
        config["port"] = args.port

    # Handle MX resolution
    if args.resolve_mx:
        config["resolve_mx"] = True

        # Check if we need to install dnspython
        try:
            import dns.resolver
        except ImportError:
            print("Warning: The dnspython package is required for MX resolution.")
            print("Please install it with: pip install dnspython")
            return 2

    # Determine if we're doing a basic check or authenticated check
    if args.basic_check:
        # Basic check - don't include credentials
        logger.info(f"Performing basic {args.protocol.upper()} server check for {args.hostname}")
    else:
        # Include authentication if provided
        if args.username:
            config["username"] = args.username

        if args.password:
            config["password"] = args.password

        # Only include test email settings if doing SMTP with creds
        if args.protocol == "smtp" and args.send_test and args.username and args.password:
            config["test_send"] = True

            if args.from_email:
                config["from_email"] = args.from_email
            else:
                # Default from email if not provided
                config["from_email"] = args.username if "@" in args.username else f"{args.username}@example.com"

            if args.to_email:
                config["to_email"] = args.to_email
            else:
                # Default to same address if not provided
                config["to_email"] = config["from_email"]

            config["subject"] = "MonitorPy Mail Test"
            config["message"] = "This is a test email sent by MonitorPy to verify mail server functionality."

            logger.info(f"Will send test email from {config['from_email']} to {config['to_email']}")

    # Run the appropriate check
    result = run_check("mail_server", config)

    # Output the results
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_result(result, args.verbose))

    return 0 if result.is_success() else (1 if result.is_warning() else 2)


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        int: Exit code
    """
    parser = setup_cli_parser()
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file)

    # Handle commands
    if args.command == "list":
        return handle_list_command()
    elif args.command == "website":
        return handle_website_command(args)
    elif args.command == "ssl":
        return handle_ssl_command(args)
    elif args.command == "mail":
        return handle_mail_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
