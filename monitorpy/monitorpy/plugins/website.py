"""
Website monitoring plugin for checking website availability and content.
"""

import time
from typing import List

import requests
from requests.exceptions import RequestException

from monitorpy.core import MonitorPlugin, CheckResult, register_plugin
from monitorpy.utils import get_logger

# Configure logging
logger = get_logger("plugins.website")


@register_plugin("website_status")
class WebsiteStatusPlugin(MonitorPlugin):
    """
    Plugin for checking website availability and status codes.

    Verifies that a website is accessible and optionally checks for
    specific status codes and content.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """
        Get required configuration parameters.

        Returns:
            List[str]: List of required parameter names
        """
        return ["url"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """
        Get optional configuration parameters.

        Returns:
            List[str]: List of optional parameter names
        """
        return [
            "timeout",
            "expected_status",
            "method",
            "headers",
            "body",
            "auth_username",
            "auth_password",
            "verify_ssl",
            "follow_redirects",
            "expected_content",
            "unexpected_content",
        ]

    def validate_config(self) -> bool:
        """
        Validate that required configuration parameters are present and properly formatted.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check that all required keys are present
        if not all(key in self.config for key in self.get_required_config()):
            logger.error(
                f"Missing required configuration parameters: {self.get_required_config()}"
            )
            return False

        # Validate URL format
        url = self.config.get("url", "")
        if not url.startswith(("http://", "https://")):
            logger.error(
                f"Invalid URL format: {url}. Must start with http:// or https://"
            )
            return False

        return True

    def run_check(self) -> CheckResult:
        """
        Run the website status check.

        Returns:
            CheckResult: The result of the check
        """
        url = self.config["url"]
        timeout = self.config.get("timeout", 30)
        method = self.config.get("method", "GET")
        headers = self.config.get("headers", {})
        body = self.config.get("body", None)
        auth = None
        expected_status = self.config.get("expected_status", 200)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)
        expected_content = self.config.get("expected_content")
        unexpected_content = self.config.get("unexpected_content")

        # Set up authentication if provided
        if "auth_username" in self.config and "auth_password" in self.config:
            auth = (self.config["auth_username"], self.config["auth_password"])

        try:
            logger.debug(
                f"Checking website {url} (method: {method}, timeout: {timeout}s)"
            )
            start_time = time.time()

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                auth=auth,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=follow_redirects,
            )

            end_time = time.time()
            response_time = end_time - start_time
            logger.debug(
                f"Request completed in {response_time:.4f}s with status {response.status_code}"
            )

            # Check status code
            status_match = response.status_code == expected_status

            # Check content if specified
            content_match = True
            content_issues = []

            if expected_content and expected_content not in response.text:
                content_match = False
                content_issues.append(
                    f"Expected content '{expected_content}' not found"
                )
                logger.debug(
                    f"Expected content '{expected_content}' not found in response"
                )

            if unexpected_content and unexpected_content in response.text:
                content_match = False
                content_issues.append(
                    f"Unexpected content '{unexpected_content}' found"
                )
                logger.debug(
                    f"Unexpected content '{unexpected_content}' found in response"
                )

            # Determine overall status
            if status_match and content_match:
                status = CheckResult.STATUS_SUCCESS
                message = (
                    f"Website check successful. Status code: {response.status_code}"
                )
            elif status_match:
                status = CheckResult.STATUS_WARNING
                message = f"Website accessible but content issues detected: {', '.join(content_issues)}"
            else:
                status = CheckResult.STATUS_ERROR
                message = f"Website check failed. Expected status: {expected_status}, actual: {response.status_code}"

            # Prepare raw data
            raw_data = {
                "url": url,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "status_match": status_match,
                "content_match": content_match,
                "content_issues": content_issues,
                "response_headers": dict(response.headers),
                "response_size": len(response.content),
                "redirect_history": (
                    [h.url for h in response.history] if follow_redirects else None
                ),
            }

            logger.info(f"Website check result: {status} - {message}")
            return CheckResult(
                status=status,
                message=message,
                response_time=response_time,
                raw_data=raw_data,
            )

        except RequestException as e:
            logger.exception(f"Error checking website {url}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Connection error: {str(e)}",
                response_time=0.0,
                raw_data={"error": str(e), "error_type": type(e).__name__},
            )
        except Exception as e:
            logger.exception(f"Unexpected error checking website {url}")
            return CheckResult(
                status=CheckResult.STATUS_ERROR,
                message=f"Unexpected error: {str(e)}",
                response_time=0.0,
                raw_data={"error": str(e), "error_type": type(e).__name__},
            )
