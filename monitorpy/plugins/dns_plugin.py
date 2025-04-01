"""
DNS monitoring plugin for checking record availability, content, and propagation.
"""

import ipaddress
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Union

# Define DNS module placeholders in case import fails
dns = None

try:
    import dns.resolver
    import dns.exception
    import dns.rdatatype
    import dns.name
    import dns.message
    import dns.query
    import dns.flags

    DNSPYTHON_AVAILABLE = True
except ImportError:
    # Create a mock dns module with the necessary attributes for type checking
    class MockDNS:
        class Resolver:
            class Answer:
                pass

            class Resolver:
                pass

            class NXDOMAIN(Exception):
                pass

            class NoAnswer(Exception):
                pass

            class Timeout(Exception):
                pass

        class Rdatatype:
            class RdataType:
                __members__ = {}

        class Exception:
            pass

        class Name:
            pass

        class Message:
            pass

        class Query:
            pass

        class Flags:
            pass

    # Create module structure that matches dnspython
    class MockDNSModule:
        resolver = MockDNS.Resolver
        exception = MockDNS.Exception
        rdatatype = MockDNS.Rdatatype
        name = MockDNS.Name
        message = MockDNS.Message
        query = MockDNS.Query
        flags = MockDNS.Flags

    dns = MockDNSModule()
    DNSPYTHON_AVAILABLE = False

from monitorpy.core import MonitorPlugin, CheckResult, register_plugin
from monitorpy.utils import get_logger

# Configure logging
logger = get_logger("plugins.dns")

# List of common public DNS resolvers for propagation checking
DEFAULT_PUBLIC_RESOLVERS = [
    {"ip": "8.8.8.8", "name": "Google", "provider": "Google DNS"},
    {"ip": "8.8.4.4", "name": "Google", "provider": "Google DNS"},
    {"ip": "1.1.1.1", "name": "Cloudflare", "provider": "Cloudflare DNS"},
    {"ip": "1.0.0.1", "name": "Cloudflare", "provider": "Cloudflare DNS"},
    {"ip": "9.9.9.9", "name": "Quad9", "provider": "Quad9 DNS"},
    {"ip": "149.112.112.112", "name": "Quad9", "provider": "Quad9 DNS"},
    {"ip": "208.67.222.222", "name": "OpenDNS", "provider": "OpenDNS"},
    {"ip": "208.67.220.220", "name": "OpenDNS", "provider": "OpenDNS"},
]


@register_plugin("dns_record")
class DNSRecordPlugin(MonitorPlugin):
    """
    Plugin for checking DNS records and propagation.

    This plugin verifies DNS record existence, content, and propagation across
    multiple DNS servers. It supports various record types (A, AAAA, MX, CNAME, TXT, etc.)
    and can check authoritative responses, DNSSEC validation, and response times.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """
        Get required configuration parameters.

        Returns:
            List[str]: List of required parameter names
        """
        return ["domain", "record_type"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """
        Get optional configuration parameters.

        Returns:
            List[str]: List of optional parameter names
        """
        return [
            "expected_value",
            "nameserver",
            "check_propagation",
            "resolvers",
            "propagation_threshold",
            "timeout",
            "check_authoritative",
            "check_dnssec",
            "subdomain",
            "max_workers",
        ]

    def validate_config(self) -> bool:
        """
        Validate that required configuration parameters are present and properly formatted.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check for dnspython availability
        if not DNSPYTHON_AVAILABLE:
            logger.error(
                "dnspython library is not installed. Please install it using 'pip install dnspython'"
            )
            return False

        # Check that all required keys are present
        if not all(key in self.config for key in self.get_required_config()):
            logger.error(
                f"Missing required configuration parameters: {self.get_required_config()}"
            )
            return False

        # Validate record type
        record_type = self.config.get("record_type", "").upper()
        valid_types = [t.upper() for t in dns.rdatatype.RdataType.__members__]
        if record_type not in valid_types:
            logger.error(
                f"Invalid record type: {record_type}. Must be one of: {', '.join(valid_types)}"
            )
            return False

        # If expected_value is required for certain record types
        if (
            record_type in ["A", "AAAA", "CNAME", "TXT"]
            and "expected_value" not in self.config
        ):
            # It's not a hard requirement, but log a warning
            logger.warning(
                f"No expected_value provided for {record_type} record. Will only check existence."
            )

        # Validate propagation threshold if check_propagation is enabled
        if self.config.get("check_propagation", False):
            threshold = self.config.get("propagation_threshold", 80)
            if (
                not isinstance(threshold, (int, float))
                or threshold < 0
                or threshold > 100
            ):
                logger.error(
                    "Propagation threshold must be a percentage between 0 and 100"
                )
                return False

        # Validate resolvers if explicitly provided
        if "resolvers" in self.config:
            resolvers = self.config["resolvers"]
            if not isinstance(resolvers, list):
                logger.error(
                    "Resolvers must be a list of IP addresses or resolver objects"
                )
                return False

            # Validate each resolver
            for resolver in resolvers:
                if isinstance(resolver, str):
                    try:
                        ipaddress.ip_address(resolver)
                    except ValueError:
                        logger.error(f"Invalid resolver IP address: {resolver}")
                        return False
                elif isinstance(resolver, dict):
                    if "ip" not in resolver:
                        logger.error(f"Missing 'ip' key in resolver object: {resolver}")
                        return False
                    try:
                        ipaddress.ip_address(resolver["ip"])
                    except ValueError:
                        logger.error(f"Invalid resolver IP address: {resolver['ip']}")
                        return False
                else:
                    logger.error(f"Invalid resolver format: {resolver}")
                    return False

        return True

    def run_check(self) -> CheckResult:
        """
        Run the DNS record check.

        Returns:
            CheckResult: The result of the check
        """
        domain = self.config["domain"]
        record_type = self.config["record_type"].upper()
        expected_value = self.config.get("expected_value")
        nameserver = self.config.get("nameserver")
        timeout = self.config.get("timeout", 10)
        check_propagation = self.config.get("check_propagation", False)
        check_authoritative = self.config.get("check_authoritative", False)
        check_dnssec = self.config.get("check_dnssec", False)
        subdomain = self.config.get("subdomain", "")
        max_workers = self.config.get("max_workers", 10)

        # Combine domain and subdomain if provided
        full_domain = f"{subdomain}.{domain}" if subdomain else domain

        try:
            logger.debug(f"Checking DNS {record_type} record for {full_domain}")
            start_time = time.time()

            # Create a resolver
            resolver = dns.resolver.Resolver()
            if nameserver:
                resolver.nameservers = (
                    [nameserver] if isinstance(nameserver, str) else nameserver
                )
            resolver.timeout = timeout

            # Basic query to check record existence
            try:
                answers = resolver.resolve(full_domain, record_type)
                record_exists = True
                answer_values = self._format_answers(answers, record_type)
                response_time = time.time() - start_time

                logger.debug(
                    f"Found {len(answer_values)} {record_type} records for {full_domain}"
                )
                logger.debug(f"Values: {answer_values}")

                # Check authoritative response if requested
                authoritative_result = None
                if check_authoritative:
                    authoritative_result = self._check_authoritative(
                        full_domain, record_type
                    )

                # Check DNSSEC if requested
                dnssec_result = None
                if check_dnssec:
                    dnssec_result = self._check_dnssec(full_domain, record_type)

                # Check propagation if requested
                propagation_result = None
                if check_propagation:
                    propagation_result = self._check_propagation(
                        full_domain, record_type, expected_value, max_workers
                    )

                # Validate against expected value if provided
                expected_value_match = True
                if expected_value:
                    # For most record types, just check if expected_value is in the answers
                    if isinstance(expected_value, list):
                        # If expected_value is a list, check that all values are present
                        expected_value_match = all(
                            val in answer_values for val in expected_value
                        )
                    else:
                        # If expected_value is a string, check if it's in the answers
                        expected_value_match = expected_value in answer_values

                # Prepare raw data
                raw_data = {
                    "domain": full_domain,
                    "record_type": record_type,
                    "records": answer_values,
                    "expected_value": expected_value,
                    "expected_value_match": expected_value_match,
                    "query_time": response_time,
                    "nameserver": nameserver or resolver.nameservers[0],
                }

                # Safely extract TTL values if available
                try:
                    # Some dnspython versions store TTL at the answer level rather than record level
                    if hasattr(answers, "ttl"):
                        raw_data["ttl"] = answers.ttl
                    # Try to get TTL from individual records
                    elif hasattr(answers[0], "ttl"):
                        raw_data["ttl"] = [ans.ttl for ans in answers]
                    # If answers.rrset is available and has ttl
                    elif hasattr(answers, "rrset") and hasattr(answers.rrset, "ttl"):
                        raw_data["ttl"] = answers.rrset.ttl
                    else:
                        raw_data["ttl"] = "unknown"
                except (AttributeError, IndexError):
                    raw_data["ttl"] = "unknown"

                # Add additional results if they were checked
                if authoritative_result:
                    raw_data["authoritative"] = authoritative_result

                if dnssec_result:
                    raw_data["dnssec"] = dnssec_result

                if propagation_result:
                    raw_data["propagation"] = propagation_result

                # Determine overall status
                status = CheckResult.STATUS_SUCCESS
                message_parts = []

                # Check expected value match
                if expected_value and not expected_value_match:
                    status = CheckResult.STATUS_ERROR
                    if isinstance(expected_value, list):
                        message_parts.append(
                            f"Expected values {expected_value} not all found"
                        )
                    else:
                        message_parts.append(
                            f"Expected value '{expected_value}' not found"
                        )

                # Check authoritative result if present
                if authoritative_result and not authoritative_result.get(
                    "is_authoritative", True
                ):
                    status = CheckResult.STATUS_WARNING
                    message_parts.append("Non-authoritative response")

                # Check DNSSEC result if present
                if dnssec_result and not dnssec_result.get("is_valid", True):
                    status = CheckResult.STATUS_ERROR
                    message_parts.append("DNSSEC validation failed")

                # Check propagation result if present
                if propagation_result:
                    prop_status = propagation_result.get("status")
                    if prop_status == CheckResult.STATUS_ERROR:
                        status = CheckResult.STATUS_ERROR
                        message_parts.append(
                            f"Poor propagation: {propagation_result.get('percentage', 0)}% "
                            f"({propagation_result.get('consistent_count', 0)}/{propagation_result.get('total_count', 0)} resolvers)"
                        )
                    elif prop_status == CheckResult.STATUS_WARNING:
                        if (
                            status != CheckResult.STATUS_ERROR
                        ):  # Don't downgrade from ERROR
                            status = CheckResult.STATUS_WARNING
                        message_parts.append(
                            f"Partial propagation: {propagation_result.get('percentage', 0)}% "
                            f"({propagation_result.get('consistent_count', 0)}/{propagation_result.get('total_count', 0)} resolvers)"
                        )

                # Build the message based on status
                if status == CheckResult.STATUS_SUCCESS:
                    if expected_value:
                        message = f"DNS {record_type} record for {full_domain} matches expected value"
                        if isinstance(expected_value, list):
                            message = f"DNS {record_type} records for {full_domain} contain all expected values"
                    else:
                        message = f"DNS {record_type} record found for {full_domain}"
                        if len(answer_values) > 1:
                            message = (
                                f"DNS {record_type} records found for {full_domain}"
                            )
                else:
                    if message_parts:
                        message = f"DNS {record_type} record check for {full_domain} has issues: {', '.join(message_parts)}"
                    else:
                        message = (
                            f"DNS {record_type} record check for {full_domain} failed"
                        )

                # Add record values to the message for better context
                if len(answer_values) <= 5:  # Don't overwhelm with too many values
                    message += f". Values: {', '.join(str(v) for v in answer_values)}"
                else:
                    message += f". Found {len(answer_values)} records"

                # Return the final result
                return CheckResult(
                    status=status,
                    message=message,
                    response_time=response_time,
                    raw_data=raw_data,
                )

            except dns.resolver.NXDOMAIN:
                # Domain does not exist
                response_time = time.time() - start_time
                return CheckResult(
                    status=CheckResult.STATUS_ERROR,
                    message=f"Domain {full_domain} does not exist",
                    response_time=response_time,
                    raw_data={
                        "domain": full_domain,
                        "record_type": record_type,
                        "error": "NXDOMAIN",
                        "query_time": response_time,
                    },
                )

            except dns.resolver.NoAnswer:
                # No records of the requested type
                response_time = time.time() - start_time
                return CheckResult(
                    status=CheckResult.STATUS_ERROR,
                    message=f"No {record_type} records found for {full_domain}",
                    response_time=response_time,
                    raw_data={
                        "domain": full_domain,
                        "record_type": record_type,
                        "error": "NoAnswer",
                        "query_time": response_time,
                    },
                )

            except dns.resolver.Timeout:
                # DNS query timed out
                response_time = timeout
                return CheckResult(
                    status=CheckResult.STATUS_ERROR,
                    message=f"Timeout resolving {record_type} records for {full_domain}",
                    response_time=response_time,
                    raw_data={
                        "domain": full_domain,
                        "record_type": record_type,
                        "error": "Timeout",
                        "query_time": response_time,
                    },
                )

        except Exception as e:
            # Catch any other exceptions
            logger.exception(f"Error checking DNS records for {full_domain}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Error checking DNS records: {str(e)}",
                response_time=(
                    time.time() - start_time if "start_time" in locals() else 0.0
                ),
                raw_data={
                    "domain": full_domain,
                    "record_type": record_type,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def _format_answers(
        self, answers: dns.resolver.Answer, record_type: str
    ) -> List[str]:
        """
        Format DNS answer objects into strings for comparison and display.

        Args:
            answers: DNS answer objects
            record_type: Type of record (A, AAAA, MX, etc.)

        Returns:
            List[str]: Formatted answer strings
        """
        result = []

        for rdata in answers:
            if record_type == "A" or record_type == "AAAA":
                # IP addresses
                result.append(str(rdata.address))
            elif record_type == "MX":
                # Mail servers with priority
                result.append(f"{rdata.preference} {rdata.exchange}")
            elif record_type == "CNAME" or record_type == "NS" or record_type == "PTR":
                # Name records
                result.append(str(rdata.target))
            elif record_type == "TXT":
                # TXT records (convert bytes to string)
                txt_data = rdata.strings
                txt_str = b"".join(txt_data).decode("utf-8", errors="replace")
                result.append(txt_str)
            elif record_type == "SOA":
                # SOA records
                result.append(
                    f"{rdata.mname} {rdata.rname} {rdata.serial} "
                    f"{rdata.refresh} {rdata.retry} {rdata.expire} {rdata.minimum}"
                )
            elif record_type == "SRV":
                # SRV records
                result.append(
                    f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
                )
            elif record_type == "CAA":
                # CAA records
                result.append(f'{rdata.flags} {rdata.tag} "{rdata.value}"')
            else:
                # Generic handling for other record types
                result.append(str(rdata))

        return result

    def _check_authoritative(self, domain: str, record_type: str) -> Dict[str, Any]:
        """
        Check if the response is authoritative.

        Args:
            domain: Domain name to check
            record_type: Type of DNS record

        Returns:
            Dict: Result of the authoritative check
        """
        try:
            # Create a specific query
            query = dns.message.make_query(domain, dns.rdatatype.from_text(record_type))

            # Find authoritative nameservers for this domain
            auth_ns = self._get_authoritative_nameservers(domain)

            if not auth_ns:
                return {
                    "is_authoritative": False,
                    "error": "Could not determine authoritative nameservers",
                }

            # Try each authoritative nameserver
            for ns in auth_ns:
                try:
                    # Make a direct query to the authoritative server
                    response = dns.query.udp(query, ns, timeout=5)

                    # Check if the response is authoritative
                    if response.flags & dns.flags.AA:
                        return {
                            "is_authoritative": True,
                            "nameserver": ns,
                            "flags": str(dns.flags.to_text(response.flags)),
                        }
                except Exception as e:
                    logger.debug(
                        f"Error querying authoritative nameserver {ns}: {str(e)}"
                    )
                    continue

            # If we get here, no authoritative response was received
            return {
                "is_authoritative": False,
                "attempted_nameservers": auth_ns,
                "error": "No authoritative response received from nameservers",
            }

        except Exception as e:
            logger.debug(f"Error checking authoritative response: {str(e)}")
            return {
                "is_authoritative": False,
                "error": f"Error checking authoritative response: {str(e)}",
            }

    def _get_authoritative_nameservers(self, domain: str) -> List[str]:
        """
        Get authoritative nameservers for a domain.

        Args:
            domain: Domain name

        Returns:
            List[str]: List of nameserver IP addresses
        """
        try:
            # Start with root and walk the DNS tree
            domain_parts = domain.split(".")

            # For efficiency, start with the TLD NS if possible
            current = ".".join(domain_parts[-2:]) if len(domain_parts) > 1 else domain

            ns_ips = []
            max_levels = len(domain_parts)

            # Recursively find authoritative nameservers
            for level in range(max_levels):
                try:
                    ns_records = dns.resolver.resolve(current, "NS")

                    # Get IP addresses for these nameservers
                    ns_ips = []
                    for record in ns_records:
                        ns_name = str(record.target).rstrip(".")
                        try:
                            # Get A records for this nameserver
                            ns_a_records = dns.resolver.resolve(ns_name, "A")
                            for a_record in ns_a_records:
                                ns_ips.append(str(a_record.address))
                        except Exception:
                            # If we can't resolve this NS, try the next one
                            continue

                    # If we found nameservers and this is the target domain, we're done
                    if ns_ips and current == domain:
                        return ns_ips

                    # Move up one level in the domain hierarchy if needed
                    if len(domain_parts) > level + 2:
                        current = ".".join(domain_parts[-(level + 3) :])
                    else:
                        # We've reached the highest level we can check
                        break

                except Exception as e:
                    logger.debug(f"Error resolving NS records for {current}: {str(e)}")
                    break

            return ns_ips

        except Exception as e:
            logger.debug(f"Error finding authoritative nameservers: {str(e)}")
            return []

    def _check_dnssec(self, domain: str, record_type: str) -> Dict[str, Any]:
        """
        Check DNSSEC validation for a domain.

        Args:
            domain: Domain name
            record_type: DNS record type

        Returns:
            Dict: DNSSEC validation results
        """
        try:
            # Create a resolver with DNSSEC validation enabled
            resolver = dns.resolver.Resolver()
            resolver.use_dnssec = True

            # Attempt to query with DNSSEC validation
            try:
                answers = resolver.resolve(
                    domain, record_type, raise_on_no_answer=False
                )

                # Check if we got DNSSEC information
                if answers.response.flags & dns.flags.AD:
                    return {
                        "is_valid": True,
                        "is_signed": True,
                        "flags": str(dns.flags.to_text(answers.response.flags)),
                    }
                else:
                    # AD flag not set, could mean unsigned or validation failed
                    return {
                        "is_valid": True,  # Still valid, just not signed or validated
                        "is_signed": False,
                        "flags": str(dns.flags.to_text(answers.response.flags)),
                    }

            except dns.resolver.DNSSECValidationError as e:
                # DNSSEC validation failed
                return {
                    "is_valid": False,
                    "is_signed": True,  # It's signed, but validation failed
                    "error": str(e),
                }

            except Exception as e:
                # Other errors
                return {"is_valid": False, "error": f"DNSSEC check failed: {str(e)}"}

        except Exception as e:
            logger.debug(f"Error checking DNSSEC: {str(e)}")
            return {"is_valid": False, "error": f"Error checking DNSSEC: {str(e)}"}

    def _check_propagation(
        self,
        domain: str,
        record_type: str,
        expected_value: Optional[Union[str, List[str]]] = None,
        max_workers: int = 10,
    ) -> Dict[str, Any]:
        """
        Check DNS propagation across multiple public resolvers.

        Args:
            domain: Domain name
            record_type: DNS record type
            expected_value: Expected record value(s)
            max_workers: Maximum number of concurrent workers for queries

        Returns:
            Dict: Propagation check results
        """
        # Get resolvers to check
        resolvers = self.config.get("resolvers", DEFAULT_PUBLIC_RESOLVERS)
        if isinstance(resolvers, list) and all(isinstance(r, str) for r in resolvers):
            # Convert list of IPs to resolver objects
            resolvers = [
                {"ip": ip, "name": ip, "provider": "Custom"} for ip in resolvers
            ]

        propagation_threshold = self.config.get("propagation_threshold", 80)
        timeout = self.config.get("timeout", 5)

        # Store results for each resolver
        results = []

        # Define the function to query a single resolver
        def query_resolver(resolver_info):
            resolver_ip = resolver_info["ip"]
            resolver_name = resolver_info.get("name", resolver_ip)
            provider = resolver_info.get("provider", "Unknown")

            try:
                # Create a resolver using this specific nameserver
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [resolver_ip]
                resolver.timeout = timeout

                start_time = time.time()

                try:
                    # Query the resolver
                    answers = resolver.resolve(domain, record_type)
                    response_time = time.time() - start_time

                    # Format answers
                    answer_values = self._format_answers(answers, record_type)

                    # Check if the answers match the expected value
                    match = True
                    if expected_value:
                        if isinstance(expected_value, list):
                            match = all(val in answer_values for val in expected_value)
                        else:
                            match = expected_value in answer_values

                    return {
                        "resolver": resolver_ip,
                        "name": resolver_name,
                        "provider": provider,
                        "status": "success",
                        "response_time": response_time,
                        "records": answer_values,
                        "match": match,
                    }

                except dns.resolver.NXDOMAIN:
                    # Domain not found
                    response_time = time.time() - start_time
                    return {
                        "resolver": resolver_ip,
                        "name": resolver_name,
                        "provider": provider,
                        "status": "error",
                        "error": "NXDOMAIN",
                        "response_time": response_time,
                        "match": False,
                    }

                except dns.resolver.NoAnswer:
                    # No records of the requested type
                    response_time = time.time() - start_time
                    return {
                        "resolver": resolver_ip,
                        "name": resolver_name,
                        "provider": provider,
                        "status": "error",
                        "error": "NoAnswer",
                        "response_time": response_time,
                        "match": False,
                    }

                except dns.resolver.Timeout:
                    # Query timed out
                    return {
                        "resolver": resolver_ip,
                        "name": resolver_name,
                        "provider": provider,
                        "status": "error",
                        "error": "Timeout",
                        "response_time": timeout,
                        "match": False,
                    }

            except Exception as e:
                logger.debug(f"Error querying resolver {resolver_ip}: {str(e)}")
                return {
                    "resolver": resolver_ip,
                    "name": resolver_name,
                    "provider": provider,
                    "status": "error",
                    "error": str(e),
                    "match": False,
                }

        # Query all resolvers in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_resolver = {
                executor.submit(query_resolver, resolver): resolver
                for resolver in resolvers
            }

            for future in as_completed(future_to_resolver):
                resolver = future_to_resolver[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.debug(
                        f"Error processing resolver {resolver['ip']}: {str(e)}"
                    )
                    results.append(
                        {
                            "resolver": resolver["ip"],
                            "name": resolver.get("name", resolver["ip"]),
                            "provider": resolver.get("provider", "Unknown"),
                            "status": "error",
                            "error": str(e),
                            "match": False,
                        }
                    )

        # Calculate propagation statistics
        total_resolvers = len(results)
        successful_resolvers = sum(1 for r in results if r["status"] == "success")
        consistent_resolvers = sum(1 for r in results if r.get("match", False))

        # Calculate percentage of consistent resolvers out of total
        percentage = (
            (consistent_resolvers / total_resolvers * 100) if total_resolvers > 0 else 0
        )

        # Determine status based on threshold
        if percentage >= propagation_threshold:
            status = CheckResult.STATUS_SUCCESS
        elif (
            percentage >= propagation_threshold * 0.7
        ):  # 70% of threshold as warning level
            status = CheckResult.STATUS_WARNING
        else:
            status = CheckResult.STATUS_ERROR

        # Return propagation results
        return {
            "status": status,
            "total_count": total_resolvers,
            "successful_count": successful_resolvers,
            "consistent_count": consistent_resolvers,
            "percentage": round(percentage, 1),
            "threshold": propagation_threshold,
            "resolvers": results,
        }
