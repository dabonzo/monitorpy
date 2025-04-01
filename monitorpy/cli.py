"""
Command-line interface for the monitorpy package.
"""

import argparse
import json
import sys
import os
import logging
from typing import Optional, Dict, Any, List
import concurrent.futures

from monitorpy.core import registry, run_check, run_checks_in_parallel
from monitorpy.utils import setup_logging, format_result, get_logger
from monitorpy.config import load_config, save_sample_config, get_config

# Import to register all plugins
from monitorpy import plugins  # noqa: F401

logger = get_logger("cli")


def parse_header(header_str: str) -> Optional[tuple]:
    """
    Parse a header string in the format 'Name: Value'.

    Args:
        header_str: The header string to parse

    Returns:
        Optional[tuple]: Tuple of (name, value) or None if invalid
    """
    if not header_str or ":" not in header_str:
        return None

    name, value = header_str.split(":", 1)
    return name.strip(), value.strip()


def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Set up the command-line argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="MonitorPy - A plugin-based website and service monitoring tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=get_config("general", "log_level", "INFO"),
        help="Set logging level",
    )
    parser.add_argument(
        "--log-file",
        default=get_config("general", "log_file"),
        help="Log file path (if not specified, logs to stdout only)",
    )
    parser.add_argument("--config", help="Path to configuration file")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List plugins command
    subparsers.add_parser(
        "list",
        help="List available plugins",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    config_parser.add_argument("action", choices=["generate"], help="Action to perform")
    config_parser.add_argument(
        "--output",
        default="./monitorpy.yml",
        help="Output file path for generated config",
    )
    config_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="Output format"
    )

    # API server command
    api_parser = subparsers.add_parser(
        "api",
        help="Run the MonitorPy API server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    api_parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to"
    )
    api_parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    api_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    api_parser.add_argument(
        "--database", type=str, help="Database URL (defaults to SQLite)"
    )
    
    # User management command
    user_parser = subparsers.add_parser(
        "user",
        help="User management",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    user_subparsers = user_parser.add_subparsers(dest="user_action", help="User action")
    
    # Create user command
    create_user_parser = user_subparsers.add_parser("create", help="Create a new user")
    create_user_parser.add_argument("--username", required=True, help="Username for login")
    create_user_parser.add_argument("--email", required=True, help="User email address")
    create_user_parser.add_argument("--password", required=True, help="User password")
    create_user_parser.add_argument("--admin", action="store_true", help="Give admin privileges")
    
    # List users command
    list_users_parser = user_subparsers.add_parser("list", help="List all users")
    list_users_parser.add_argument("--show-keys", action="store_true", help="Show API keys")
    
    # Delete user command
    delete_user_parser = user_subparsers.add_parser("delete", help="Delete a user")
    delete_user_parser.add_argument("username", help="Username to delete")
    
    # Reset password command
    reset_pw_parser = user_subparsers.add_parser("reset-password", help="Reset user password")
    reset_pw_parser.add_argument("username", help="Username to reset password for")
    reset_pw_parser.add_argument("--password", required=True, help="New password")
    
    # Generate API key command
    gen_key_parser = user_subparsers.add_parser("generate-key", help="Generate new API key")
    gen_key_parser.add_argument("username", help="Username to generate key for")

    # Batch check command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Run multiple checks in parallel",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    batch_parser.add_argument(
        "checks_file", help="JSON file containing check configurations"
    )
    batch_parser.add_argument(
        "--output", help="Output file for results (default: stdout)"
    )
    batch_parser.add_argument(
        "--max-workers", type=int, help="Maximum number of parallel workers"
    )
    batch_parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing large numbers of checks",
    )
    batch_parser.add_argument(
        "--timeout", type=float, help="Timeout in seconds for each batch"
    )
    batch_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    batch_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )

    # Check website command
    website_parser = subparsers.add_parser(
        "website",
        help="Check website availability",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    website_parser.add_argument("url", help="URL to check", nargs="?")
    website_parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds"
    )
    website_parser.add_argument(
        "--status", type=int, default=200, help="Expected HTTP status code"
    )
    website_parser.add_argument(
        "--method", default="GET", help="HTTP method (GET, POST, etc.)"
    )
    website_parser.add_argument(
        "--header", action="append", help="HTTP header in format 'Name: Value'"
    )
    website_parser.add_argument("--body", help="Request body data")
    website_parser.add_argument(
        "--content", help="Content that should be present in the response"
    )
    website_parser.add_argument(
        "--no-content", help="Content that should NOT be present in the response"
    )
    website_parser.add_argument(
        "--auth-username", help="Username for basic authentication"
    )
    website_parser.add_argument(
        "--auth-password", help="Password for basic authentication"
    )
    website_parser.add_argument(
        "--no-verify", action="store_true", help="Disable SSL certificate verification"
    )
    website_parser.add_argument(
        "--no-redirect", action="store_true", help="Disable following redirects"
    )
    website_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    website_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    website_parser.add_argument(
        "--sites",
        help="File with list of URLs to check (one per line, will be checked in parallel with --parallel)",
    )
    website_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run multiple checks in parallel (when using --sites)",
    )
    website_parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers (default: CPU count + 4)",
    )

    # Check SSL certificate command
    ssl_parser = subparsers.add_parser(
        "ssl",
        help="Check SSL certificate",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ssl_parser.add_argument("hostname", help="Hostname or URL to check", nargs="?")
    ssl_parser.add_argument("--port", type=int, help="Port number (default: 443)")
    ssl_parser.add_argument(
        "--timeout", type=int, default=30, help="Connection timeout in seconds"
    )
    ssl_parser.add_argument(
        "--warning", type=int, default=30, help="Warning threshold in days"
    )
    ssl_parser.add_argument(
        "--critical", type=int, default=14, help="Critical threshold in days"
    )
    ssl_parser.add_argument(
        "--check-chain", action="store_true", help="Check certificate chain"
    )
    ssl_parser.add_argument(
        "--no-verify-hostname",
        action="store_true",
        help="Disable hostname verification",
    )
    ssl_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    ssl_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    ssl_parser.add_argument(
        "--hosts",
        help="File with list of hostnames to check (one per line, will be checked in parallel with --parallel)",
    )
    ssl_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run multiple checks in parallel (when using --hosts)",
    )
    ssl_parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers (default: CPU count + 4)",
    )

    # Mail server check command
    mail_parser = subparsers.add_parser(
        "mail",
        help="Check mail server connectivity and functionality",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    mail_parser.add_argument("hostname", help="Mail server hostname", nargs="?")
    mail_parser.add_argument(
        "--protocol",
        choices=["smtp", "imap", "pop3"],
        default="smtp",
        help="Mail protocol to check",
    )
    mail_parser.add_argument(
        "--port", type=int, help="Server port (defaults to standard port for protocol)"
    )
    mail_parser.add_argument("--username", help="Username for authentication")
    mail_parser.add_argument("--password", help="Password for authentication")
    mail_parser.add_argument("--ssl", action="store_true", help="Use SSL connection")
    mail_parser.add_argument(
        "--tls", action="store_true", help="Use TLS connection (SMTP only)"
    )
    mail_parser.add_argument(
        "--timeout", type=int, default=30, help="Connection timeout in seconds"
    )
    mail_parser.add_argument(
        "--send-test", action="store_true", help="Send test email (SMTP only)"
    )
    mail_parser.add_argument(
        "--from", dest="from_email", help="From email address (for test email)"
    )
    mail_parser.add_argument(
        "--to", dest="to_email", help="To email address (for test email)"
    )
    mail_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    mail_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    mail_parser.add_argument(
        "--basic-check",
        action="store_true",
        help="Perform basic connectivity check without authentication",
    )
    mail_parser.add_argument(
        "--no-resolve-mx",
        action="store_false",
        dest="resolve_mx",
        default=True,  # Make this the default behavior
        help="Don't resolve MX records for domain (resolve_mx is enabled by default)",
    )
    mail_parser.add_argument(
        "--servers",
        help="File with list of mail servers to check (one per line, will be checked in parallel with --parallel)",
    )
    mail_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run multiple checks in parallel (when using --servers)",
    )
    mail_parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers (default: CPU count + 4)",
    )

    dns_parser = subparsers.add_parser(
        "dns",
        help="Check DNS records and propagation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    dns_parser.add_argument("domain", help="Domain name to check", nargs="?")
    dns_parser.add_argument(
        "--type",
        default="A",
        dest="record_type",
        help="DNS record type (A, AAAA, MX, CNAME, TXT, NS, etc.)",
    )
    dns_parser.add_argument(
        "--value", dest="expected_value", help="Expected record value"
    )
    dns_parser.add_argument("--subdomain", help="Subdomain to check (e.g., 'www')")
    dns_parser.add_argument("--nameserver", help="Specific nameserver to query")
    dns_parser.add_argument(
        "--timeout", type=int, default=10, help="Query timeout in seconds"
    )
    dns_parser.add_argument(
        "--check-propagation",
        action="store_true",
        help="Check DNS propagation across multiple resolvers",
    )
    dns_parser.add_argument(
        "--resolvers",
        nargs="+",
        help="Custom DNS resolvers to check (space-separated list of IP addresses)",
    )
    dns_parser.add_argument(
        "--threshold",
        type=float,
        default=80,
        help="Propagation threshold percentage (0-100)",
    )
    dns_parser.add_argument(
        "--check-authoritative",
        action="store_true",
        help="Check if response is from an authoritative server",
    )
    dns_parser.add_argument(
        "--check-dnssec", action="store_true", help="Check DNSSEC validation"
    )
    dns_parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of concurrent workers for propagation checks",
    )
    dns_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    dns_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    dns_parser.add_argument(
        "--domains",
        help="File with list of domains to check (one per line, will be checked in parallel with --parallel)",
    )
    dns_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run multiple checks in parallel (when using --domains)",
    )
    dns_parser.add_argument(
        "--parallel-workers",
        type=int,
        help="Maximum number of parallel workers for domain checks (default: CPU count + 4)",
    )

    return parser


def handle_website_command(args):
    """Handle the website check command."""
    # Check if URL is provided when not using sites file
    if not args.url and not args.sites:
        logger.error("Either --url or --sites must be provided")
        print(
            "Error: Please provide either a URL to check or a sites file with --sites"
        )
        return None
    # Parse headers if provided
    headers = {}
    if args.header:
        for header_str in args.header:
            parsed = parse_header(header_str)
            if parsed:
                name, value = parsed
                headers[name] = value

    config = {
        "url": args.url,
        "timeout": args.timeout,
        "expected_status": args.status,
        "method": args.method,
        "headers": headers,
        "body": args.body,
        "auth_username": args.auth_username,
        "auth_password": args.auth_password,
        "verify_ssl": not args.no_verify,
        "follow_redirects": not args.no_redirect,
        "expected_content": args.content,
        "unexpected_content": args.no_content,
    }

    result = run_check("website_status", config)
    return result


def handle_parallel_websites(args):
    """Handle parallel website checks."""
    # Read URLs from file
    try:
        with open(args.sites, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading URLs file: {str(e)}")
        return None

    # Set up base configuration
    base_config = {
        "timeout": args.timeout,
        "expected_status": args.status,
        "method": args.method,
        "verify_ssl": not args.no_verify,
        "follow_redirects": not args.no_redirect,
        "expected_content": args.content,
        "unexpected_content": args.no_content,
    }

    # Parse headers if provided
    headers = {}
    if args.header:
        for header_str in args.header:
            parsed = parse_header(header_str)
            if parsed:
                name, value = parsed
                headers[name] = value

    if headers:
        base_config["headers"] = headers

    if args.auth_username and args.auth_password:
        base_config["auth_username"] = args.auth_username
        base_config["auth_password"] = args.auth_password

    # Create check configurations for each URL
    check_configs = []
    for i, url in enumerate(urls):
        config = base_config.copy()
        config["url"] = url
        check_configs.append(
            {"id": f"url{i+1}", "plugin_type": "website_status", "config": config}
        )

    # Run checks in parallel (use args.max_workers if specified, else None for default)
    max_workers = args.max_workers if hasattr(args, "max_workers") else None
    results = run_checks_in_parallel(check_configs, max_workers)

    # Print summary
    total = len(results)
    success = sum(1 for _, result in results if result.status == "success")
    warning = sum(1 for _, result in results if result.status == "warning")
    error = sum(1 for _, result in results if result.status == "error")

    output = []
    output.append(f"\nParallel Website Check Results ({success}/{total} successful):")
    output.append(f"  Success: {success}, Warning: {warning}, Error: {error}")
    output.append("")

    # Print detailed results if verbose
    if args.verbose:
        for check_config, result in results:
            url = check_config["config"]["url"]
            output.append(f"URL: {url}")
            output.append(f"  Status: {result.status}")
            output.append(f"  Message: {result.message}")
            output.append(f"  Response Time: {result.response_time:.3f}s")
            if result.raw_data and args.verbose:
                output.append("  Details:")
                for key, value in result.raw_data.items():
                    if key != "response_headers":  # Skip verbose headers
                        output.append(f"    {key}: {value}")
            output.append("")

    combined_result = "\n".join(output)
    return combined_result


def handle_ssl_command(args):
    """Handle the SSL certificate check command."""
    # Check if hostname is provided when not using hosts file
    if not args.hostname and not args.hosts:
        logger.error("Either hostname or --hosts must be provided")
        print(
            "Error: Please provide either a hostname to check or a hosts file with --hosts"
        )
        return None

    config = {
        "hostname": args.hostname,
        "port": args.port if args.port is not None else 443,  # Use default port 443 if not specified
        "timeout": args.timeout,
        "warning_days": args.warning,
        "critical_days": args.critical,
        "check_chain": args.check_chain,
        "verify_hostname": not args.no_verify_hostname,
    }

    result = run_check("ssl_certificate", config)
    return result


def handle_parallel_ssl(args):
    """Handle parallel SSL certificate checks."""
    # Read hostnames from file
    try:
        with open(args.hosts, "r") as f:
            hostnames = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading hosts file: {str(e)}")
        return None

    # Set up base configuration
    base_config = {
        "port": args.port if args.port is not None else 443,  # Use default port 443 if not specified
        "timeout": args.timeout,
        "warning_days": args.warning,
        "critical_days": args.critical,
        "check_chain": args.check_chain,
        "verify_hostname": not args.no_verify_hostname,
    }

    # Create check configurations for each hostname
    check_configs = []
    for i, hostname in enumerate(hostnames):
        config = base_config.copy()
        config["hostname"] = hostname
        check_configs.append(
            {"id": f"host{i+1}", "plugin_type": "ssl_certificate", "config": config}
        )

    # Run checks in parallel (use args.max_workers if specified, else None for default)
    max_workers = args.max_workers if hasattr(args, "max_workers") else None
    results = run_checks_in_parallel(check_configs, max_workers)

    # Print summary
    total = len(results)
    success = sum(1 for _, result in results if result.status == "success")
    warning = sum(1 for _, result in results if result.status == "warning")
    error = sum(1 for _, result in results if result.status == "error")

    output = []
    output.append(
        f"\nParallel SSL Certificate Check Results ({success}/{total} successful):"
    )
    output.append(f"  Success: {success}, Warning: {warning}, Error: {error}")
    output.append("")

    # Print detailed results if verbose
    if args.verbose:
        for check_config, result in results:
            hostname = check_config["config"]["hostname"]
            output.append(f"Host: {hostname}")
            output.append(f"  Status: {result.status}")
            output.append(f"  Message: {result.message}")
            output.append(f"  Response Time: {result.response_time:.3f}s")
            if result.raw_data and args.verbose:
                output.append("  Details:")
                for key, value in result.raw_data.items():
                    if key in [
                        "issuer",
                        "subject",
                        "valid_from",
                        "valid_until",
                        "days_remaining",
                    ]:
                        output.append(f"    {key}: {value}")
            output.append("")

    combined_result = "\n".join(output)
    return combined_result


def handle_mail_command(args):
    """Handle the mail server check command."""
    # Check if hostname is provided when not using servers file
    if not args.hostname and not args.servers:
        logger.error("Either hostname or --servers must be provided")
        print(
            "Error: Please provide either a mail server hostname to check or a servers file with --servers"
        )
        return None

    config = {
        "hostname": args.hostname,
        "protocol": args.protocol,
        "port": args.port,
        "username": args.username,
        "password": args.password,
        "use_ssl": args.ssl,
        "use_tls": args.tls,
        "timeout": args.timeout,
        "test_send": args.send_test,
        "from_email": args.from_email,
        "to_email": args.to_email,
        "resolve_mx": args.resolve_mx,
    }

    result = run_check("mail_server", config)
    return result


def handle_parallel_mail(args):
    """Handle parallel mail server checks."""
    # Read servers from file
    try:
        with open(args.servers, "r") as f:
            servers = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading servers file: {str(e)}")
        return None

    # Set up base configuration
    base_config = {
        "protocol": args.protocol,
        "port": args.port,
        "username": args.username,
        "password": args.password,
        "use_ssl": args.ssl,
        "use_tls": args.tls,
        "timeout": args.timeout,
        "test_send": args.send_test,
        "from_email": args.from_email,
        "to_email": args.to_email,
        "resolve_mx": args.resolve_mx,
    }

    # Create check configurations for each server
    check_configs = []
    for i, server in enumerate(servers):
        config = base_config.copy()
        config["hostname"] = server
        check_configs.append(
            {"id": f"server{i+1}", "plugin_type": "mail_server", "config": config}
        )

    # Run checks in parallel (use args.max_workers if specified, else None for default)
    max_workers = args.max_workers if hasattr(args, "max_workers") else None
    results = run_checks_in_parallel(check_configs, max_workers)

    # Print summary
    total = len(results)
    success = sum(1 for _, result in results if result.status == "success")
    warning = sum(1 for _, result in results if result.status == "warning")
    error = sum(1 for _, result in results if result.status == "error")

    output = []
    output.append(
        f"\nParallel Mail Server Check Results ({success}/{total} successful):"
    )
    output.append(f"  Success: {success}, Warning: {warning}, Error: {error}")
    output.append("")

    # Print detailed results if verbose
    if args.verbose:
        for check_config, result in results:
            server = check_config["config"]["hostname"]
            output.append(f"Server: {server}")
            output.append(f"  Status: {result.status}")
            output.append(f"  Message: {result.message}")
            output.append(f"  Response Time: {result.response_time:.3f}s")
            if result.raw_data and args.verbose:
                output.append("  Details:")
                for key, value in result.raw_data.items():
                    if key not in ["error_details"]:  # Skip verbose error details
                        output.append(f"    {key}: {value}")
            output.append("")

    combined_result = "\n".join(output)
    return combined_result


def handle_dns_command(args):
    """Handle the DNS check command."""
    # Check if domain is provided when not using domains file
    if not args.domain and not args.domains:
        logger.error("Either domain or --domains must be provided")
        print(
            "Error: Please provide either a domain to check or a domains file with --domains"
        )
        return None

    # Combine domain and subdomain if both are provided
    full_domain = args.domain
    if args.subdomain:
        full_domain = f"{args.subdomain}.{args.domain}"

    config = {
        "domain": args.domain,
        "subdomain": args.subdomain,
        "record_type": args.record_type,
        "expected_value": args.expected_value,
        "nameserver": args.nameserver,
        "timeout": args.timeout,
        "check_propagation": args.check_propagation,
        "propagation_threshold": args.threshold,
        "check_authoritative": args.check_authoritative,
        "check_dnssec": args.check_dnssec,
        "max_workers": args.max_workers,
    }
    
    # Only include resolvers if specified, and ensure it's in the right format
    if args.resolvers:
        # args.resolvers will be a list of IP addresses as strings
        config["resolvers"] = args.resolvers

    # Use "dns_record" which is the actual plugin name
    result = run_check("dns_record", config)
    return result


def handle_parallel_dns(args):
    """Handle parallel DNS checks."""
    # Read domains from file
    try:
        with open(args.domains, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading domains file: {str(e)}")
        return None

    # Set up base configuration
    base_config = {
        "record_type": args.record_type,
        "expected_value": args.expected_value,
        "nameserver": args.nameserver,
        "timeout": args.timeout,
        "check_propagation": args.check_propagation,
        "propagation_threshold": args.threshold,
        "check_authoritative": args.check_authoritative,
        "check_dnssec": args.check_dnssec,
        # Use the dns-specific max workers for propagation checks
        "max_workers": args.max_workers,
    }
    
    # Only include resolvers if specified, and ensure it's in the right format
    if args.resolvers:
        # args.resolvers will be a list of IP addresses as strings
        base_config["resolvers"] = args.resolvers

    # Create check configurations for each domain
    check_configs = []
    for i, domain in enumerate(domains):
        config = base_config.copy()
        # Check if the domain includes a subdomain part (e.g., www.example.com)
        parts = domain.split(".", 1)
        if len(parts) > 1 and len(parts[0].split(".")) == 1:
            config["domain"] = parts[1]
            config["subdomain"] = parts[0]
        else:
            config["domain"] = domain

        check_configs.append(
            {"id": f"domain{i+1}", "plugin_type": "dns_record", "config": config}
        )

    # Use parallel-workers for running the parallel checks (this is different from
    # the max_workers in the dns check config which is for propagation checks)
    max_workers = args.parallel_workers if hasattr(args, "parallel_workers") else None
    results = run_checks_in_parallel(check_configs, max_workers)

    # Print summary
    total = len(results)
    success = sum(1 for _, result in results if result.status == "success")
    warning = sum(1 for _, result in results if result.status == "warning")
    error = sum(1 for _, result in results if result.status == "error")

    output = []
    output.append(f"\nParallel DNS Check Results ({success}/{total} successful):")
    output.append(f"  Success: {success}, Warning: {warning}, Error: {error}")
    output.append("")

    # Print detailed results if verbose
    if args.verbose:
        for check_config, result in results:
            domain = check_config["config"]["domain"]
            subdomain = check_config["config"].get("subdomain")
            full_domain = f"{subdomain}.{domain}" if subdomain else domain
            output.append(f"Domain: {full_domain}")
            output.append(f"  Status: {result.status}")
            output.append(f"  Message: {result.message}")
            output.append(f"  Response Time: {result.response_time:.3f}s")
            if result.raw_data and args.verbose:
                output.append("  Details:")
                for key, value in result.raw_data.items():
                    if key not in [
                        "propagation_results"
                    ]:  # Skip verbose propagation details
                        output.append(f"    {key}: {value}")
            output.append("")

    combined_result = "\n".join(output)
    return combined_result


def handle_batch_command(args):
    """Handle the batch check command."""
    # Read check configurations from file
    try:
        with open(args.checks_file, "r") as f:
            checks_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading checks file: {str(e)}")
        return None

    # Validate the checks data
    if not isinstance(checks_data, list):
        logger.error(
            "Invalid checks file format. Expected a list of check configurations."
        )
        return None

    # Prepare check configurations
    check_configs = []
    for i, check in enumerate(checks_data):
        if "plugin_type" not in check:
            logger.error(f"Missing plugin_type in check at index {i}")
            continue
        if "config" not in check:
            logger.error(f"Missing config in check at index {i}")
            continue

        # Add ID if not present
        if "id" not in check:
            check["id"] = f"check{i+1}"

        check_configs.append(check)

    if not check_configs:
        logger.error("No valid check configurations found")
        return None

    # Run checks in batches
    max_workers = args.max_workers
    batch_size = args.batch_size
    timeout = args.timeout

    from monitorpy.core.batch_runner import run_check_batch

    results = run_check_batch(check_configs, batch_size, max_workers, timeout)

    # Process results
    processed_results = []
    for check_config, result in results:
        processed_results.append(
            {
                "id": check_config.get("id", "unknown"),
                "plugin_type": check_config.get("plugin_type"),
                "status": result.status,
                "message": result.message,
                "response_time": result.response_time,
                "raw_data": result.raw_data if args.verbose else None,
            }
        )

    # Calculate summary
    total = len(processed_results)
    success = sum(1 for r in processed_results if r["status"] == "success")
    warning = sum(1 for r in processed_results if r["status"] == "warning")
    error = sum(1 for r in processed_results if r["status"] == "error")

    summary = {
        "total": total,
        "success": success,
        "warning": warning,
        "error": error,
        "success_percentage": round(success / total * 100 if total > 0 else 0, 1),
    }

    # Output results
    output_data = {"summary": summary, "results": processed_results}

    if args.json:
        # JSON output
        output = json.dumps(output_data, indent=2)
    else:
        # Text output
        lines = []
        lines.append(
            f"\nBatch Check Results ({success}/{total} successful, {summary['success_percentage']}%):"
        )
        lines.append(f"  Success: {success}, Warning: {warning}, Error: {error}")
        lines.append("")

        if args.verbose:
            for result in processed_results:
                lines.append(f"Check: {result['id']} ({result['plugin_type']})")
                lines.append(f"  Status: {result['status']}")
                lines.append(f"  Message: {result['message']}")
                lines.append(f"  Response Time: {result['response_time']:.3f}s")
                if result["raw_data"]:
                    lines.append("  Details:")
                    for key, value in result["raw_data"].items():
                        # Limit the output of complex nested structures
                        if isinstance(value, (dict, list)) and not args.verbose:
                            lines.append(f"    {key}: [complex data]")
                        else:
                            lines.append(f"    {key}: {value}")
                lines.append("")

        output = "\n".join(lines)

    # Write to file if specified
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            logger.info(f"Results written to {args.output}")
            return f"Results written to {args.output}"
        except Exception as e:
            logger.error(f"Error writing results to file: {str(e)}")

    return output


def main():
    """Main entry point for the CLI."""
    parser = setup_cli_parser()
    args = parser.parse_args()

    # Set up logging
    setup_logging(level=args.log_level, log_file=args.log_file)

    # Load configuration if specified
    if args.config:
        load_config(args.config)

    # Handle commands
    if args.command == "list":
        print("Available plugins:")
        for plugin in sorted(registry.get_plugin_names()):
            print(f"  {plugin}")

        return 0

    elif args.command == "config":
        if args.action == "generate":
            save_sample_config(args.output, args.format)
            print(f"Sample configuration file saved to {args.output}")

        return 0

    elif args.command == "website":
        # Check if we're using a sites file
        if args.sites:
            if args.parallel:
                result = handle_parallel_websites(args)
            else:
                # Sites file provided but no parallel flag
                print(
                    "Using sites file without --parallel flag. Consider adding --parallel for better performance."
                )
                result = handle_parallel_websites(args)
        else:
            # Regular single website check
            result = handle_website_command(args)

    elif args.command == "ssl":
        # Check if we're using a hosts file
        if args.hosts:
            if args.parallel:
                result = handle_parallel_ssl(args)
            else:
                # Hosts file provided but no parallel flag
                print(
                    "Using hosts file without --parallel flag. Consider adding --parallel for better performance."
                )
                result = handle_parallel_ssl(args)
        else:
            result = handle_ssl_command(args)

    elif args.command == "mail":
        # Check if we're using a servers file
        if args.servers:
            if args.parallel:
                result = handle_parallel_mail(args)
            else:
                # Servers file provided but no parallel flag
                print(
                    "Using servers file without --parallel flag. Consider adding --parallel for better performance."
                )
                result = handle_parallel_mail(args)
        else:
            result = handle_mail_command(args)

    elif args.command == "dns":
        # Check if we're using a domains file
        if args.domains:
            if args.parallel:
                result = handle_parallel_dns(args)
            else:
                # Domains file provided but no parallel flag
                print(
                    "Using domains file without --parallel flag. Consider adding --parallel for better performance."
                )
                result = handle_parallel_dns(args)
        else:
            result = handle_dns_command(args)

    elif args.command == "api":
        try:
            from monitorpy.api import create_app, DevelopmentConfig, ProductionConfig
            from monitorpy.api.extensions import db
            from flask import Flask

            # Set database URL if provided
            if args.database:
                os.environ["DATABASE_URL"] = args.database

            # Set environment
            os.environ["FLASK_ENV"] = "development" if args.debug else "production"

            # Create and run application
            config_class = DevelopmentConfig if args.debug else ProductionConfig
            app = create_app(config_class)

            print(f"Starting MonitorPy API on {args.host}:{args.port}...")
            app.run(host=args.host, port=args.port, debug=args.debug)

            return 0

        except ImportError as e:
            print(f"Error: {str(e)}")
            print("Make sure the API dependencies are installed:")
            print("  pip install flask flask-sqlalchemy flask-migrate flask-cors")
            return 1
        except Exception as e:
            print(f"Error starting API: {str(e)}")
            return 1
            
    elif args.command == "user":
        try:
            from monitorpy.api import create_app
            from monitorpy.api.extensions import db
            from monitorpy.api.models.user import User
            from monitorpy.api.config import get_config

            # Create app context for database operations
            app = create_app(get_config())
            
            with app.app_context():
                # Handle user management commands
                if args.user_action == "create":
                    # Check if user already exists
                    if User.query.filter_by(username=args.username).first():
                        print(f"Error: Username {args.username} already exists")
                        return 1
                    
                    if User.query.filter_by(email=args.email).first():
                        print(f"Error: Email {args.email} already exists")
                        return 1
                        
                    # Create new user
                    user = User(
                        username=args.username, 
                        email=args.email, 
                        password=args.password, 
                        is_admin=args.admin
                    )
                    
                    # Generate API key
                    api_key = user.generate_api_key()
                    
                    # Save to database
                    db.session.add(user)
                    db.session.commit()
                    
                    is_admin_str = "with admin privileges" if args.admin else "without admin privileges"
                    print(f"User {args.username} ({args.email}) created successfully {is_admin_str}")
                    print(f"API Key: {api_key}")
                    
                elif args.user_action == "list":
                    users = User.query.all()
                    
                    if not users:
                        print("No users found")
                        return 0
                        
                    print(f"Found {len(users)} users:")
                    for user in users:
                        admin_status = " (admin)" if user.is_admin else ""
                        print(f"- {user.username} ({user.email}){admin_status}")
                        if args.show_keys and user.api_key:
                            print(f"  API Key: {user.api_key}")
                            
                elif args.user_action == "delete":
                    user = User.query.filter_by(username=args.username).first()
                    
                    if not user:
                        print(f"Error: User {args.username} not found")
                        return 1
                        
                    db.session.delete(user)
                    db.session.commit()
                    
                    print(f"User {args.username} deleted successfully")
                    
                elif args.user_action == "reset-password":
                    user = User.query.filter_by(username=args.username).first()
                    
                    if not user:
                        print(f"Error: User {args.username} not found")
                        return 1
                        
                    user.set_password(args.password)
                    db.session.commit()
                    
                    print(f"Password for user {args.username} reset successfully")
                    
                elif args.user_action == "generate-key":
                    user = User.query.filter_by(username=args.username).first()
                    
                    if not user:
                        print(f"Error: User {args.username} not found")
                        return 1
                        
                    api_key = user.generate_api_key()
                    db.session.commit()
                    
                    print(f"New API key for user {args.username} generated successfully")
                    print(f"API Key: {api_key}")
                    
                else:
                    print("Error: Unknown user action")
                    return 1
                    
            return 0
            
        except ImportError as e:
            print(f"Error: {str(e)}")
            print("Make sure the API dependencies are installed:")
            print("  pip install flask flask-sqlalchemy flask-migrate flask-cors")
            return 1
        except Exception as e:
            print(f"Error in user management: {str(e)}")
            return 1

    elif args.command == "batch":
        result = handle_batch_command(args)
        if result:
            print(result)
        return 0

    else:
        parser.print_help()
        return 1

    # If we get here, we have a check result to print
    if isinstance(result, str):
        print(result)
    elif args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_result(result, verbose=args.verbose))

    # Return exit code based on check status
    if result is None:
        return 1
    elif isinstance(result, str):
        # For parallel checks, we return 0 since we've already shown the summary
        return 0
    elif result.status == "success":
        return 0
    elif result.status == "warning":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
