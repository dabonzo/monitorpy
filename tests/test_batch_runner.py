"""
Tests for the batch runner module.
"""

import unittest
from unittest.mock import patch, MagicMock
import time

from monitorpy.core.result import CheckResult
from monitorpy.core.batch_runner import run_checks_in_parallel, run_check_batch


class TestBatchRunner(unittest.TestCase):
    """Tests for the batch runner functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_configs = [
            {
                "id": "test1",
                "plugin_type": "website_status",
                "config": {"url": "https://example.com"},
            },
            {
                "id": "test2",
                "plugin_type": "ssl_certificate",
                "config": {"hostname": "example.com"},
            },
            {
                "id": "test3",
                "plugin_type": "website_status",
                "config": {"url": "https://example.org"},
            },
        ]

    @patch("monitorpy.core.batch_runner._run_single_check")
    def test_run_checks_in_parallel_success(self, mock_run_check):
        """Test successful parallel execution of checks."""

        # Setup mock to return different results for different plugins
        def mock_run_impl(plugin_type, config):
            if plugin_type == "website_status":
                return CheckResult(
                    status=CheckResult.STATUS_SUCCESS,
                    message="Website check successful",
                    response_time=0.5,
                    raw_data={"url": config.get("url")},
                )
            else:
                return CheckResult(
                    status=CheckResult.STATUS_SUCCESS,
                    message="SSL check successful",
                    response_time=0.3,
                    raw_data={"hostname": config.get("hostname")},
                )

        mock_run_check.side_effect = mock_run_impl

        # Run parallel checks
        results = run_checks_in_parallel(self.test_configs)

        # Verify all checks were executed
        self.assertEqual(len(results), 3)
        mock_run_check.assert_called()
        self.assertEqual(mock_run_check.call_count, 3)

        # Verify results match the expected structure
        for check_config, result in results:
            self.assertIn(check_config["id"], ["test1", "test2", "test3"])
            self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)

    @patch("monitorpy.core.batch_runner._run_single_check")
    def test_run_checks_in_parallel_with_failure(self, mock_run_check):
        """Test parallel execution with some failures."""

        # Setup mock to fail for one check
        def mock_run_impl(plugin_type, config):
            if plugin_type == "ssl_certificate":
                return CheckResult(
                    status=CheckResult.STATUS_ERROR,
                    message="SSL check failed",
                    response_time=0.2,
                    raw_data={"error": "Connection refused"},
                )
            else:
                return CheckResult(
                    status=CheckResult.STATUS_SUCCESS,
                    message="Website check successful",
                    response_time=0.5,
                    raw_data={"url": config.get("url")},
                )

        mock_run_check.side_effect = mock_run_impl

        # Run parallel checks
        results = run_checks_in_parallel(self.test_configs)

        # Verify all checks were executed
        self.assertEqual(len(results), 3)

        # Count successes and failures
        successes = sum(
            1 for _, result in results if result.status == CheckResult.STATUS_SUCCESS
        )
        failures = sum(
            1 for _, result in results if result.status == CheckResult.STATUS_ERROR
        )

        self.assertEqual(successes, 2)
        self.assertEqual(failures, 1)

    @patch("monitorpy.core.batch_runner._run_single_check")
    def test_run_checks_with_exception(self, mock_run_check):
        """Test handling of exceptions during check execution."""

        # Setup mock to raise an exception for one check
        def mock_run_impl(plugin_type, config):
            if plugin_type == "ssl_certificate":
                raise Exception("Test exception")
            else:
                return CheckResult(
                    status=CheckResult.STATUS_SUCCESS,
                    message="Website check successful",
                    response_time=0.5,
                    raw_data={"url": config.get("url")},
                )

        mock_run_check.side_effect = mock_run_impl

        # Run parallel checks
        results = run_checks_in_parallel(self.test_configs)

        # Verify all checks were executed and exception was handled
        self.assertEqual(len(results), 3)

        # Check that the SSL check has an error result due to the exception
        ssl_result = next(
            (
                result
                for config, result in results
                if config["plugin_type"] == "ssl_certificate"
            ),
            None,
        )
        self.assertIsNotNone(ssl_result)
        self.assertEqual(ssl_result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Test exception", ssl_result.message)

    @patch("monitorpy.core.batch_runner.run_checks_in_parallel")
    def test_run_check_batch(self, mock_run_parallel):
        """Test running checks in batches."""
        # Create a mock return value for each batch
        def mock_run_parallel_impl(batch, *args, **kwargs):
            return [(config, CheckResult(CheckResult.STATUS_SUCCESS, f"Success for {config['id']}", 0.1, {})) 
                    for config in batch]
            
        mock_run_parallel.side_effect = mock_run_parallel_impl

        # Create a larger test set
        large_test_configs = self.test_configs * 3  # 9 configs total

        # Run batch with batch_size=2
        results = run_check_batch(large_test_configs, batch_size=2)

        # Verify run_checks_in_parallel was called multiple times
        self.assertEqual(
            mock_run_parallel.call_count, 5
        )  # 9 configs ÷ 2 = 5 batches (with rounding up)

    @patch("monitorpy.core.batch_runner._run_single_check")
    def test_with_timeout(self, mock_run_check):
        """Test parallel execution with timeout."""

        # Setup mock to simulate slow execution
        def slow_check(plugin_type, config):
            if plugin_type == "ssl_certificate":
                time.sleep(0.05)  # Simulate slow check, but not too slow for test
            return CheckResult(
                status=CheckResult.STATUS_SUCCESS,
                message="Check successful",
                response_time=0.1,
                raw_data={},
            )

        mock_run_check.side_effect = slow_check

        # Run with a timeout that's long enough to complete
        results = run_checks_in_parallel(self.test_configs, timeout=1.0)

        # Should get all results
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
